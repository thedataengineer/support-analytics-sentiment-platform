from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from ..database import get_db
from ..models.sentiment_result import SentimentResult

router = APIRouter()

@router.get("/tickets")
async def get_tickets_with_sentiment(
    q: Optional[str] = Query(None, description="Search query"),
    sentiment: Optional[str] = Query(None, description="Filter by final sentiment"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(20, description="Number of tickets to return"),
    offset: int = Query(0, description="Number of tickets to skip"),
    db: Session = Depends(get_db)
):
    """
    Get tickets with their full sentiment trajectory
    Returns tickets grouped with all their comments and sentiment analysis
    """

    # Build base query for ticket IDs
    ticket_query = db.query(SentimentResult.ticket_id).distinct()

    # Apply filters
    if q:
        ticket_query = ticket_query.filter(
            or_(
                SentimentResult.text.ilike(f"%{q}%"),
                SentimentResult.ticket_id.ilike(f"%{q}%")
            )
        )

    if start_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        ticket_query = ticket_query.filter(SentimentResult.comment_timestamp >= start)

    if end_date:
        end = datetime.strptime(end_date, "%Y-%m-%d")
        ticket_query = ticket_query.filter(SentimentResult.comment_timestamp <= end + timedelta(days=1))

    # Get total count of tickets
    total_tickets = ticket_query.count()

    # Get paginated ticket IDs
    ticket_ids = [
        row[0] for row in ticket_query
        .order_by(SentimentResult.ticket_id)
        .offset(offset)
        .limit(limit)
        .all()
    ]

    # Get all sentiment results for these tickets
    results = []
    for ticket_id in ticket_ids:
        # Get all sentiment records for this ticket, removing duplicates by keeping latest created_at
        sentiments_subquery = (
            db.query(
                SentimentResult.id,
                func.row_number().over(
                    partition_by=[
                        SentimentResult.ticket_id,
                        SentimentResult.field_type,
                        SentimentResult.comment_number,
                        SentimentResult.text
                    ],
                    order_by=SentimentResult.created_at.desc()
                ).label('rn')
            )
            .filter(SentimentResult.ticket_id == ticket_id)
            .subquery()
        )

        # Get unique sentiment records
        sentiments = (
            db.query(SentimentResult)
            .join(sentiments_subquery, SentimentResult.id == sentiments_subquery.c.id)
            .filter(sentiments_subquery.c.rn == 1)
            .order_by(
                SentimentResult.comment_timestamp.asc().nullslast(),
                SentimentResult.comment_number.asc().nullslast()
            )
            .all()
        )

        if not sentiments:
            continue

        # Build comments list
        comments = []
        sentiment_scores = {'positive': 0, 'negative': 0, 'neutral': 0}
        negative_entities = []  # Track negative sentiment items

        for sent in sentiments:
            comment_data = {
                "field_type": sent.field_type or "unknown",
                "text": sent.text[:200] + "..." if len(sent.text) > 200 else sent.text,
                "full_text": sent.text,
                "sentiment": sent.sentiment,
                "confidence": sent.confidence,
                "comment_timestamp": sent.comment_timestamp.isoformat() if sent.comment_timestamp else None,
                "comment_number": sent.comment_number,
                "author_id": sent.author_id,
                "created_at": sent.created_at.isoformat() if sent.created_at else None
            }
            comments.append(comment_data)

            # Count sentiments for final aggregation
            if sent.sentiment in sentiment_scores:
                sentiment_scores[sent.sentiment] += 1

            # Track negative entities with their context
            if sent.sentiment == 'negative':
                negative_entities.append({
                    "field_type": sent.field_type or "unknown",
                    "text_snippet": sent.text[:150] + "..." if len(sent.text) > 150 else sent.text,
                    "confidence": sent.confidence,
                    "timestamp": sent.comment_timestamp.isoformat() if sent.comment_timestamp else None
                })

        # Calculate final sentiment (most common)
        final_sentiment = max(sentiment_scores, key=sentiment_scores.get)
        total_comments = sum(sentiment_scores.values())

        # Calculate sentiment trajectory status
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

        # Apply sentiment filter if specified
        if sentiment and final_sentiment != sentiment:
            continue

        # Build ticket object
        ticket_data = {
            "ticket_id": ticket_id,
            "total_comments": total_comments,
            "sentiment_distribution": sentiment_scores,
            "final_sentiment": final_sentiment,
            "status": status,
            "comments": comments,
            "negative_entities": negative_entities,
            "negative_count": len(negative_entities),
            "first_comment_date": comments[0]['comment_timestamp'] if comments else None,
            "last_comment_date": comments[-1]['comment_timestamp'] if comments else None
        }

        results.append(ticket_data)

    return {
        "total": total_tickets,
        "results": results,
        "offset": offset,
        "limit": limit
    }


@router.get("/tickets/{ticket_id}")
async def get_ticket_detail(
    ticket_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed sentiment trajectory for a specific ticket
    """
    sentiments = (
        db.query(SentimentResult)
        .filter(SentimentResult.ticket_id == ticket_id)
        .order_by(
            SentimentResult.comment_timestamp.asc().nullslast(),
            SentimentResult.comment_number.asc().nullslast()
        )
        .all()
    )

    if not sentiments:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Build detailed comments
    comments = []
    sentiment_scores = {'positive': 0, 'negative': 0, 'neutral': 0}

    for sent in sentiments:
        comment_data = {
            "id": sent.id,
            "field_type": sent.field_type or "unknown",
            "text": sent.text,
            "sentiment": sent.sentiment,
            "confidence": sent.confidence,
            "comment_timestamp": sent.comment_timestamp.isoformat() if sent.comment_timestamp else None,
            "comment_number": sent.comment_number,
            "author_id": sent.author_id,
            "created_at": sent.created_at.isoformat() if sent.created_at else None
        }
        comments.append(comment_data)

        if sent.sentiment in sentiment_scores:
            sentiment_scores[sent.sentiment] += 1

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
