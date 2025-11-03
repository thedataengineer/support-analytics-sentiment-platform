from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date, case, text
import json
import httpx
import logging
from database import get_db
from storage.storage_manager import StorageManager
from services.elasticsearch_client import es_client
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

class NLQRequest(BaseModel):
    query: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None

def retrieve_relevant_tickets(query: str, start_date: datetime, end_date: datetime, limit: int = 10) -> List[Dict[str, Any]]:
    """
    RAG Retrieval: Use Elasticsearch to find relevant tickets for the query.

    Args:
        query: User's natural language query
        start_date: Start date filter
        end_date: End date filter
        limit: Maximum number of tickets to retrieve

    Returns:
        List of relevant ticket documents with context
    """
    if not es_client.enabled:
        logger.warning("Elasticsearch not available for RAG retrieval")
        return []

    try:
        # Search Elasticsearch with the user's query
        results = es_client.search_tickets(
            query=query,
            start_date=start_date,
            end_date=end_date,
            size=limit,
            offset=0
        )

        relevant_tickets = []
        for hit in results.get("hits", []):
            ticket = {
                "ticket_id": hit["ticket_id"],
                "summary": hit.get("summary", ""),
                "description": hit.get("description", "")[:500],  # Limit description length
                "sentiment": hit["sentiment"],
                "confidence": hit["confidence"],
                "score": hit.get("score", 0)
            }
            relevant_tickets.append(ticket)

        logger.info(f"Retrieved {len(relevant_tickets)} relevant tickets from Elasticsearch for RAG")
        return relevant_tickets

    except Exception as e:
        logger.error(f"Failed to retrieve tickets from Elasticsearch: {e}")
        return []


async def query_ollama(prompt: str, model: str = "llama2:70b") -> str:
    """
    Query Ollama API with the given prompt
    Falls back to llama2:7b if 70b is not available
    """
    ollama_endpoint = f"{settings.ollama_url}/api/generate"
    logger.info(f"Querying Ollama at: {ollama_endpoint}")

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:  # Increased timeout for 70B model
            response = await client.post(
                ollama_endpoint,
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_ctx": 4096  # Larger context window for RAG
                    }
                }
            )

            if response.status_code == 404 and "70b" in model:
                # Fallback to 7b model
                logger.warning("Llama 2 70B not available, falling back to 7B")
                response = await client.post(
                    ollama_endpoint,
                    json={
                        "model": "llama2:7b",
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "num_ctx": 4096
                        }
                    }
                )

            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                raise Exception(f"Ollama API error: {response.status_code}")
    except Exception as e:
        # Return fallback response if Ollama is not available
        logger.error(f"Ollama query failed: {e}", exc_info=True)
        return f"Ollama service unavailable. Error: {str(e)}"

def generate_sql_from_nlq(query: str, start_date: str, end_date: str) -> str:
    """
    Generate SQL query from natural language using LLM
    """
    schema_context = """
    Database Schema:
    Table: sentiment_results
    Columns:
    - id (INTEGER): Primary key
    - ticket_id (VARCHAR): Ticket identifier
    - text (TEXT): Comment text
    - sentiment (VARCHAR): 'positive', 'negative', or 'neutral'
    - confidence (FLOAT): Confidence score 0-1
    - field_type (VARCHAR): 'comment', 'description', or 'summary'
    - comment_number (INTEGER): Sequence number
    - comment_timestamp (DATETIME): When comment was made
    - author_id (VARCHAR): Author identifier
    - created_at (DATETIME): When record was created
    """

    prompt = f"""{schema_context}

Date Range: {start_date} to {end_date}

User Question: {query}

Generate a SQL query to answer this question. Return ONLY the SQL query, no explanation.
Use comment_timestamp for date filtering.
Format: SELECT ... FROM sentiment_results WHERE comment_timestamp >= '{start_date}' AND comment_timestamp <= '{end_date}' ...

SQL Query:"""

    return prompt

@router.post("/support/nlq")
async def process_nlq(request: NLQRequest):
    """
    Process natural language query about support data using Ollama LLM with RAG.
    Uses Elasticsearch to retrieve relevant tickets as context.
    """
    try:
        # Default dates
        start_date = request.start_date or (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = request.end_date or datetime.now().strftime("%Y-%m-%d")

        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        # Get aggregate statistics using DuckDB
        storage = StorageManager()
        sentiment_sql = f"""
        SELECT sentiment, COUNT(*) as count
        FROM sentiment_data 
        WHERE timestamp >= '{start_date}' AND timestamp <= '{end_date}'
        GROUP BY sentiment
        """
        
        sentiment_df = storage.execute_query(sentiment_sql, {'sentiment_data': 'sentiment/data.parquet'})
        
        sentiment_data = {"positive": 0, "negative": 0, "neutral": 0}
        for _, row in sentiment_df.iterrows():
            sentiment_data[row['sentiment']] = int(row['count'])

        total = sum(sentiment_data.values())

        # RAG: Retrieve relevant tickets from Elasticsearch
        relevant_tickets = retrieve_relevant_tickets(request.query, start, end, limit=10)

        # Build RAG context with retrieved tickets
        tickets_context = ""
        if relevant_tickets:
            tickets_context = "\n\nRelevant Ticket Examples (retrieved from knowledge base):\n"
            for idx, ticket in enumerate(relevant_tickets[:5], 1):  # Use top 5 for context
                score_str = f"{ticket['score']:.2f}" if ticket.get('score') is not None else "N/A"
                tickets_context += f"""
Ticket #{idx} (ID: {ticket['ticket_id']}, Sentiment: {ticket['sentiment']}, Relevance Score: {score_str})
Summary: {ticket['summary']}
Description: {ticket['description']}
---"""

        # Build enhanced context for LLM with RAG
        context = f"""You are an expert support analytics AI assistant analyzing customer support ticket data.

Date Range: {start_date} to {end_date}

Aggregate Statistics:
- Total Comments: {total:,}
- Positive: {sentiment_data['positive']:,} ({sentiment_data['positive']/total*100:.1f}% if total > 0 else 0)%
- Negative: {sentiment_data['negative']:,} ({sentiment_data['negative']/total*100:.1f}% if total > 0 else 0)%
- Neutral: {sentiment_data['neutral']:,} ({sentiment_data['neutral']/total*100:.1f}% if total > 0 else 0)%
{tickets_context}

User Question: {request.query}

Instructions:
1. Use the aggregate statistics to provide quantitative insights
2. Reference specific ticket examples when relevant to illustrate your points
3. Provide actionable insights and recommendations
4. If asked about trends, patterns, or specific issues, cite ticket examples
5. Be concise but thorough
6. If the data doesn't support a conclusion, say so

Answer:"""

        # Query Ollama with RAG-enhanced context
        logger.info(f"Querying Llama 2 70B with RAG context ({len(relevant_tickets)} tickets retrieved)")
        llm_response = await query_ollama(context)

        # Determine if visualization is needed
        chart_data = None
        visualization_keywords = ['show', 'chart', 'graph', 'plot', 'visualize', 'trend', 'distribution']

        if any(keyword in request.query.lower() for keyword in visualization_keywords):
            # Create appropriate chart based on query
            if 'trend' in request.query.lower() or 'over time' in request.query.lower():
                # Get trend data using DuckDB
                trend_sql = f"""
                SELECT 
                    DATE(timestamp) as date,
                    sentiment,
                    COUNT(*) as count
                FROM sentiment_data 
                WHERE timestamp >= '{start_date}' AND timestamp <= '{end_date}'
                GROUP BY DATE(timestamp), sentiment
                ORDER BY date
                """
                
                trend_df = storage.execute_query(trend_sql, {'sentiment_data': 'sentiment/data.parquet'})
                
                trend_map = {}
                for _, row in trend_df.iterrows():
                    date_str = str(row['date'])
                    if date_str not in trend_map:
                        trend_map[date_str] = {"date": date_str, "positive": 0, "negative": 0, "neutral": 0}
                    trend_map[date_str][row['sentiment']] = int(row['count'])

                trend_data = list(trend_map.values())

                chart_data = {
                    "data": [
                        {
                            "x": [d['date'] for d in trend_data],
                            "y": [d['positive'] for d in trend_data],
                            "name": "Positive",
                            "type": "scatter",
                            "mode": "lines+markers",
                            "line": {"color": "#4CAF50"}
                        },
                        {
                            "x": [d['date'] for d in trend_data],
                            "y": [d['negative'] for d in trend_data],
                            "name": "Negative",
                            "type": "scatter",
                            "mode": "lines+markers",
                            "line": {"color": "#F44336"}
                        },
                        {
                            "x": [d['date'] for d in trend_data],
                            "y": [d['neutral'] for d in trend_data],
                            "name": "Neutral",
                            "type": "scatter",
                            "mode": "lines+markers",
                            "line": {"color": "#FFC107"}
                        }
                    ],
                    "layout": {
                        "title": "Sentiment Trend Over Time",
                        "xaxis": {"title": "Date"},
                        "yaxis": {"title": "Count"},
                        "height": 400
                    }
                }
            else:
                # Default to distribution chart
                chart_data = {
                    "data": [{
                        "values": list(sentiment_data.values()),
                        "labels": list(sentiment_data.keys()),
                        "type": "pie",
                        "marker": {"colors": ["#4CAF50", "#F44336", "#FFC107"]}
                    }],
                    "layout": {
                        "title": "Sentiment Distribution",
                        "height": 400
                    }
                }

        return {
            "query": request.query,
            "answer": llm_response or "Unable to generate response. Please check if Ollama is running.",
            "chart_data": chart_data,
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "statistics": sentiment_data,
            "rag_metadata": {
                "retrieved_tickets": len(relevant_tickets),
                "elasticsearch_enabled": es_client.enabled,
                "ticket_ids": [t["ticket_id"] for t in relevant_tickets[:5]]
            }
        }

    except Exception as e:
        logger.error(f"NLQ processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")
