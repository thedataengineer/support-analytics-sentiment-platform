from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime, timedelta
from storage.storage_manager import StorageManager
from services.elasticsearch_client import es_client
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/search")
async def search_tickets(
    q: Optional[str] = Query(None, description="Search query"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(20, description="Number of results to return"),
    offset: int = Query(0, description="Number of results to skip")
):
    """
    Search tickets with filters using DuckDB on Parquet data.
    Uses Elasticsearch when available, falls back to DuckDB.
    """
    # Try Elasticsearch first
    if es_client.enabled:
        logger.info(f"Using Elasticsearch for search: q={q}, sentiment={sentiment}")
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
            end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
            
            es_results = es_client.search_tickets(
                query=q,
                sentiment=sentiment,
                start_date=start,
                end_date=end,
                size=limit,
                offset=offset
            )

            formatted_results = [
                {
                    "id": hit["ticket_id"],
                    "text": (hit["summary"] + " " + hit["description"])[:200] + "...",
                    "sentiment": hit["sentiment"],
                    "confidence": hit["confidence"],
                    "created_at": hit["created_at"],
                    "score": hit.get("score", 0)
                }
                for hit in es_results["hits"]
            ]

            return {
                "total": es_results["total"],
                "results": formatted_results,
                "offset": offset,
                "limit": limit,
                "source": "elasticsearch"
            }
        except Exception as e:
            logger.warning(f"Elasticsearch search failed, falling back to DuckDB: {e}")

    # Fallback to DuckDB on Parquet
    logger.info("Using DuckDB for search (Elasticsearch not available)")
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
        
        # Count total results
        count_sql = f"SELECT COUNT(*) as total FROM sentiment_data WHERE {where_clause}"
        count_df = storage.execute_query(count_sql, {'sentiment_data': 'sentiment/data.parquet'})
        total = int(count_df.iloc[0]['total']) if not count_df.empty else 0
        
        # Get paginated results
        search_sql = f"""
        SELECT ticket_id, text, sentiment, confidence, timestamp, field_type
        FROM sentiment_data 
        WHERE {where_clause}
        ORDER BY timestamp DESC
        LIMIT {limit} OFFSET {offset}
        """
        
        results_df = storage.execute_query(search_sql, {'sentiment_data': 'sentiment/data.parquet'})
        
        formatted_results = [
            {
                "id": row['ticket_id'],
                "text": row['text'][:200] + "..." if len(str(row['text'])) > 200 else str(row['text']),
                "sentiment": row['sentiment'],
                "confidence": float(row['confidence']),
                "comment_timestamp": str(row['timestamp']),
                "field_type": row['field_type']
            }
            for _, row in results_df.iterrows()
        ]

        return {
            "total": total,
            "results": formatted_results,
            "offset": offset,
            "limit": limit,
            "source": "duckdb"
        }
        
    except Exception as e:
        logger.error(f"DuckDB search failed: {e}")
        return {
            "total": 0,
            "results": [],
            "offset": offset,
            "limit": limit,
            "source": "duckdb",
            "error": str(e)
        }


@router.get("/entities/top")
async def get_top_entities(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(20, le=100, description="Max number of entities to return")
):
    """
    Get top entities from tickets using DuckDB on Parquet data.
    Uses Elasticsearch aggregations when available, falls back to DuckDB.
    """
    # Try Elasticsearch first
    if es_client.enabled:
        logger.info("Using Elasticsearch for entity aggregation")
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
            end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
            
            entities = es_client.aggregate_entities(
                start_date=start,
                end_date=end,
                limit=limit
            )

            return {
                "entities": entities,
                "source": "elasticsearch"
            }
        except Exception as e:
            logger.warning(f"Elasticsearch aggregation failed, falling back to DuckDB: {e}")

    # Fallback to DuckDB
    logger.info("Using DuckDB for entity aggregation")
    storage = StorageManager()
    
    try:
        # Build WHERE clause for date filtering
        where_conditions = []
        if start_date:
            where_conditions.append(f"ticket_id IN (SELECT ticket_id FROM ticket_data WHERE created_date >= '{start_date}')")
        if end_date:
            where_conditions.append(f"ticket_id IN (SELECT ticket_id FROM ticket_data WHERE created_date <= '{end_date}')")
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        entities_sql = f"""
        SELECT 
            entity_type as label,
            entity_text as text,
            COUNT(*) as count
        FROM entity_data 
        WHERE {where_clause}
        GROUP BY entity_type, entity_text
        ORDER BY count DESC
        LIMIT {limit}
        """
        
        entities_df = storage.execute_query(entities_sql, {
            'entity_data': 'entity/data.parquet',
            'ticket_data': 'ticket/data.parquet'
        })
        
        entities = [
            {
                "label": row['label'],
                "text": row['text'],
                "count": int(row['count'])
            }
            for _, row in entities_df.iterrows()
        ]

        return {
            "entities": entities,
            "source": "duckdb"
        }
        
    except Exception as e:
        logger.error(f"DuckDB entity aggregation failed: {e}")
        return {
            "entities": [],
            "source": "duckdb",
            "error": str(e)
        }
