from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from storage.storage_manager import StorageManager

router = APIRouter()

@router.get("/tickets")
async def get_tickets_with_sentiment(
    q: Optional[str] = Query(None, description="Search query"),
    sentiment: Optional[str] = Query(None, description="Filter by final sentiment"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(20, description="Number of tickets to return"),
    offset: int = Query(0, description="Number of tickets to skip")
):
    """
    Get tickets with their sentiment data using DuckDB on Parquet
    """
    storage = StorageManager()
    
    try:
        # Build WHERE clause
        where_conditions = []
        if q:
            where_conditions.append(f"(text ILIKE '%{q}%' OR ticket_id ILIKE '%{q}%')")
        if sentiment:
            where_conditions.append(f"sentiment = '{sentiment}'")
        if start_date:
            where_conditions.append(f"timestamp >= '{start_date}'")
        if end_date:
            where_conditions.append(f"timestamp <= '{end_date}'")
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # Get ticket summary with sentiment aggregation
        tickets_sql = f"""
        SELECT 
            ticket_id,
            COUNT(*) as total_comments,
            SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) as positive_count,
            SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) as negative_count,
            SUM(CASE WHEN sentiment = 'neutral' THEN 1 ELSE 0 END) as neutral_count,
            MIN(timestamp) as first_comment_date,
            MAX(timestamp) as last_comment_date
        FROM sentiment_data 
        WHERE {where_clause}
        GROUP BY ticket_id
        ORDER BY ticket_id
        LIMIT {limit} OFFSET {offset}
        """
        
        tickets_df = storage.execute_query(tickets_sql, {'sentiment_data': 'sentiment/data.parquet'})
        
        results = []
        for _, row in tickets_df.iterrows():
            pos, neg, neu = int(row['positive_count']), int(row['negative_count']), int(row['neutral_count'])
            
            # Determine final sentiment
            if pos > neg and pos > neu:
                final_sentiment = "positive"
            elif neg > pos and neg > neu:
                final_sentiment = "negative"
            else:
                final_sentiment = "neutral"
            
            ticket_data = {
                "ticket_id": row['ticket_id'],
                "total_comments": int(row['total_comments']),
                "sentiment_distribution": {"positive": pos, "negative": neg, "neutral": neu},
                "final_sentiment": final_sentiment,
                "status": f"stable_{final_sentiment}",
                "first_comment_date": str(row['first_comment_date']),
                "last_comment_date": str(row['last_comment_date'])
            }
            results.append(ticket_data)
        
        # Get total count
        count_sql = f"SELECT COUNT(DISTINCT ticket_id) as total FROM sentiment_data WHERE {where_clause}"
        count_df = storage.execute_query(count_sql, {'sentiment_data': 'sentiment/data.parquet'})
        total = int(count_df.iloc[0]['total']) if not count_df.empty else 0

        return {
            "total": total,
            "results": results,
            "offset": offset,
            "limit": limit
        }
        
    except Exception as e:
        return {
            "total": 0,
            "results": [],
            "offset": offset,
            "limit": limit,
            "error": str(e)
        }


@router.get("/tickets/{ticket_id}")
async def get_ticket_detail(ticket_id: str):
    """
    Get detailed sentiment trajectory for a specific ticket using DuckDB
    """
    storage = StorageManager()
    
    try:
        # Get all sentiment data for this ticket
        detail_sql = f"""
        SELECT ticket_id, text, sentiment, confidence, field_type, timestamp
        FROM sentiment_data 
        WHERE ticket_id = '{ticket_id}'
        ORDER BY timestamp ASC
        """
        
        sentiments_df = storage.execute_query(detail_sql, {'sentiment_data': 'sentiment/data.parquet'})
        
        if sentiments_df.empty:
            raise HTTPException(status_code=404, detail="Ticket not found")

        # Build detailed comments
        comments = []
        sentiment_scores = {'positive': 0, 'negative': 0, 'neutral': 0}

        for _, row in sentiments_df.iterrows():
            comment_data = {
                "field_type": row['field_type'] or "unknown",
                "text": row['text'],
                "sentiment": row['sentiment'],
                "confidence": float(row['confidence']),
                "comment_timestamp": str(row['timestamp'])
            }
            comments.append(comment_data)
            sentiment_scores[row['sentiment']] += 1

        # Calculate final sentiment
        final_sentiment = max(sentiment_scores, key=sentiment_scores.get)
        total_comments = sum(sentiment_scores.values())

        # Calculate trajectory
        if len(comments) >= 2:
            first_sentiment = comments[0]['sentiment']
            last_sentiment = comments[-1]['sentiment']

            if first_sentiment == 'negative' and last_sentiment == 'positive':
                status = 'improving'
            elif first_sentiment == 'positive' and last_sentiment == 'negative':
                status = 'declining'
            elif first_sentiment == last_sentiment:
                status = f'stable_{first_sentiment}'
            else:
                status = 'mixed'
        else:
            status = f'single_{comments[0]["sentiment"]}' if comments else 'unknown'

        return {
            "ticket_id": ticket_id,
            "total_comments": total_comments,
            "sentiment_distribution": sentiment_scores,
            "final_sentiment": final_sentiment,
            "status": status,
            "comments": comments,
            "first_comment_date": comments[0]['comment_timestamp'] if comments else None,
            "last_comment_date": comments[-1]['comment_timestamp'] if comments else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving ticket details: {str(e)}")
