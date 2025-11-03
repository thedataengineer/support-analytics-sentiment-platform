from fastapi import APIRouter, Query, Depends
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date, case
from ..database import get_db
from ..models.sentiment_result import SentimentResult

router = APIRouter()

@router.get("/support/analytics")
async def get_support_analytics(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive support analytics metrics
    """
    # Default to last 30 days
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")

    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    # 1. Overall sentiment distribution
    sentiment_dist = (
        db.query(
            SentimentResult.sentiment,
            func.count(SentimentResult.id).label("count")
        )
        .filter(SentimentResult.comment_timestamp >= start)
        .filter(SentimentResult.comment_timestamp <= end + timedelta(days=1))
        .group_by(SentimentResult.sentiment)
        .all()
    )

    sentiment_distribution = {
        "positive": 0,
        "negative": 0,
        "neutral": 0
    }
    for sentiment, count in sentiment_dist:
        sentiment_distribution[sentiment] = count

    # 2. Sentiment trend over time (daily)
    daily_trend = (
        db.query(
            cast(SentimentResult.comment_timestamp, Date).label("date"),
            SentimentResult.sentiment,
            func.count(SentimentResult.id).label("count")
        )
        .filter(SentimentResult.comment_timestamp >= start)
        .filter(SentimentResult.comment_timestamp <= end + timedelta(days=1))
        .group_by("date", SentimentResult.sentiment)
        .order_by("date")
        .all()
    )

    trend_data = {}
    for date, sentiment, count in daily_trend:
        date_str = date.isoformat()
        if date_str not in trend_data:
            trend_data[date_str] = {"date": date_str, "positive": 0, "negative": 0, "neutral": 0}
        trend_data[date_str][sentiment] = count

    # 3. Field type distribution (where sentiments come from)
    field_type_dist = (
        db.query(
            SentimentResult.field_type,
            SentimentResult.sentiment,
            func.count(SentimentResult.id).label("count")
        )
        .filter(SentimentResult.comment_timestamp >= start)
        .filter(SentimentResult.comment_timestamp <= end + timedelta(days=1))
        .group_by(SentimentResult.field_type, SentimentResult.sentiment)
        .all()
    )

    field_type_data = {}
    for field_type, sentiment, count in field_type_dist:
        ft = field_type or "unknown"
        if ft not in field_type_data:
            field_type_data[ft] = {"field_type": ft, "positive": 0, "negative": 0, "neutral": 0}
        field_type_data[ft][sentiment] = count

    # 4. Ticket-level metrics (aggregated by ticket)
    ticket_metrics = (
        db.query(
            SentimentResult.ticket_id,
            func.count(SentimentResult.id).label("comment_count"),
            func.sum(case((SentimentResult.sentiment == 'positive', 1), else_=0)).label("positive_count"),
            func.sum(case((SentimentResult.sentiment == 'negative', 1), else_=0)).label("negative_count"),
            func.sum(case((SentimentResult.sentiment == 'neutral', 1), else_=0)).label("neutral_count")
        )
        .filter(SentimentResult.comment_timestamp >= start)
        .filter(SentimentResult.comment_timestamp <= end + timedelta(days=1))
        .group_by(SentimentResult.ticket_id)
        .all()
    )

    # Calculate ticket statuses
    ticket_statuses = {
        "improving": 0,
        "declining": 0,
        "stable_positive": 0,
        "stable_negative": 0,
        "stable_neutral": 0,
        "mixed": 0
    }

    tickets_by_comment_count = {
        "1": 0,
        "2-5": 0,
        "6-10": 0,
        "11-20": 0,
        "20+": 0
    }

    for ticket_id, comment_count, pos, neg, neu in ticket_metrics:
        # Categorize by comment count
        if comment_count == 1:
            tickets_by_comment_count["1"] += 1
        elif 2 <= comment_count <= 5:
            tickets_by_comment_count["2-5"] += 1
        elif 6 <= comment_count <= 10:
            tickets_by_comment_count["6-10"] += 1
        elif 11 <= comment_count <= 20:
            tickets_by_comment_count["11-20"] += 1
        else:
            tickets_by_comment_count["20+"] += 1

        # Determine dominant sentiment
        if pos > neg and pos > neu:
            final_sentiment = "positive"
        elif neg > pos and neg > neu:
            final_sentiment = "negative"
        elif neu > pos and neu > neg:
            final_sentiment = "neutral"
        else:
            final_sentiment = "mixed"

        # Categorize status (simplified without timeline)
        if final_sentiment == "positive":
            ticket_statuses["stable_positive"] += 1
        elif final_sentiment == "negative":
            ticket_statuses["stable_negative"] += 1
        elif final_sentiment == "neutral":
            ticket_statuses["stable_neutral"] += 1
        else:
            ticket_statuses["mixed"] += 1

    # 5. Confidence distribution
    confidence_dist = (
        db.query(
            case(
                (SentimentResult.confidence >= 0.9, "high"),
                (SentimentResult.confidence >= 0.7, "medium"),
                else_="low"
            ).label("confidence_level"),
            func.count(SentimentResult.id).label("count")
        )
        .filter(SentimentResult.comment_timestamp >= start)
        .filter(SentimentResult.comment_timestamp <= end + timedelta(days=1))
        .group_by("confidence_level")
        .all()
    )

    confidence_data = {"high": 0, "medium": 0, "low": 0}
    for level, count in confidence_dist:
        confidence_data[level] = count

    # 6. Top authors by activity
    top_authors = (
        db.query(
            SentimentResult.author_id,
            func.count(SentimentResult.id).label("count")
        )
        .filter(SentimentResult.comment_timestamp >= start)
        .filter(SentimentResult.comment_timestamp <= end + timedelta(days=1))
        .filter(SentimentResult.author_id.isnot(None))
        .group_by(SentimentResult.author_id)
        .order_by(func.count(SentimentResult.id).desc())
        .limit(10)
        .all()
    )

    author_activity = [
        {"author_id": author_id or "Unknown", "count": count}
        for author_id, count in top_authors
    ]

    # 7. Summary stats
    total_tickets = len(set([t[0] for t in ticket_metrics]))
    total_comments = sum(sentiment_distribution.values())
    avg_comments_per_ticket = total_comments / total_tickets if total_tickets > 0 else 0

    return {
        "period": {
            "start_date": start_date,
            "end_date": end_date
        },
        "summary": {
            "total_tickets": total_tickets,
            "total_comments": total_comments,
            "avg_comments_per_ticket": round(avg_comments_per_ticket, 2)
        },
        "sentiment_distribution": sentiment_distribution,
        "sentiment_trend": list(trend_data.values()),
        "field_type_distribution": list(field_type_data.values()),
        "ticket_statuses": ticket_statuses,
        "tickets_by_comment_count": tickets_by_comment_count,
        "confidence_distribution": confidence_data,
        "top_authors": author_activity
    }
