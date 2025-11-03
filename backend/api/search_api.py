from fastapi import APIRouter, Query, Depends
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from ..database import get_db
from ..models.sentiment_result import SentimentResult
from ..models.entity import Entity
from ..services.elasticsearch_client import es_client
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
    offset: int = Query(0, description="Number of results to skip"),
    db: Session = Depends(get_db)
):
    """
    Search tickets with filters.
    Uses Elasticsearch when available, falls back to PostgreSQL.
    """
    # Parse dates
    start = None
    end = None
    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            pass

    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            pass

    # Try Elasticsearch first
    if es_client.enabled:
        logger.info(f"Using Elasticsearch for search: q={q}, sentiment={sentiment}")
        try:
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
            logger.warning(f"Elasticsearch search failed, falling back to PostgreSQL: {e}")

    # Fallback to PostgreSQL
    logger.info("Using PostgreSQL for search (Elasticsearch not available)")
    query = db.query(SentimentResult)

    # Apply text search filter
    if q:
        query = query.filter(
            or_(
                SentimentResult.text.ilike(f"%{q}%"),
                SentimentResult.ticket_id.ilike(f"%{q}%")
            )
        )

    # Apply sentiment filter
    if sentiment:
        query = query.filter(SentimentResult.sentiment == sentiment)

    # Apply date range filter
    if start:
        query = query.filter(SentimentResult.comment_timestamp >= start)

    if end:
        query = query.filter(SentimentResult.comment_timestamp <= end + timedelta(days=1))

    # Get total count before pagination
    total = query.count()

    # Apply pagination and ordering
    results = (
        query.order_by(SentimentResult.comment_timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    # Format results
    formatted_results = [
        {
            "id": result.ticket_id,
            "text": result.text[:200] + "..." if len(result.text) > 200 else result.text,
            "sentiment": result.sentiment,
            "confidence": result.confidence,
            "comment_timestamp": result.comment_timestamp.isoformat() if result.comment_timestamp else None,
            "field_type": result.field_type,
            "author_id": result.author_id
        }
        for result in results
    ]

    return {
        "total": total,
        "results": formatted_results,
        "offset": offset,
        "limit": limit,
        "source": "postgresql"
    }


@router.get("/entities/top")
async def get_top_entities(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(20, le=100, description="Max number of entities to return"),
    db: Session = Depends(get_db)
):
    """
    Get top entities from tickets.
    Uses Elasticsearch aggregations when available, falls back to PostgreSQL.
    """
    # Parse dates
    start = None
    end = None
    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            pass

    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            pass

    # Try Elasticsearch first
    if es_client.enabled:
        logger.info("Using Elasticsearch for entity aggregation")
        try:
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
            logger.warning(f"Elasticsearch aggregation failed, falling back to PostgreSQL: {e}")

    # Fallback to PostgreSQL
    logger.info("Using PostgreSQL for entity aggregation")
    from ..models.ticket import Ticket

    query = (
        db.query(
            Entity.label,
            Entity.text,
            func.count(Entity.id).label("count")
        )
        .join(Ticket, Ticket.ticket_id == Entity.ticket_id)
    )

    # Apply date filters
    if start:
        query = query.filter(Ticket.created_at >= start)

    if end:
        query = query.filter(Ticket.created_at <= end + timedelta(days=1))

    # Group and order
    results = (
        query.group_by(Entity.label, Entity.text)
        .order_by(func.count(Entity.id).desc())
        .limit(limit)
        .all()
    )

    entities = [
        {
            "label": label,
            "text": text,
            "count": count
        }
        for label, text, count in results
    ]

    return {
        "entities": entities,
        "source": "postgresql"
    }
