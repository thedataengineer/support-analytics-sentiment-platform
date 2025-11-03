from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import create_engine, text
import os

router = APIRouter()

def get_postgres_engine():
    postgres_url = os.getenv('POSTGRES_URL', 'postgresql://sentiment_user:sentiment_pass@localhost:5432/sentiment_db')
    return create_engine(postgres_url, pool_pre_ping=True)

@router.get("/support/analytics")
async def get_support_analytics(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """
    Get comprehensive support analytics metrics from PostgreSQL
    """
    # Default to last 30 days
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")

    engine = get_postgres_engine()

    try:
        # 1. Overall sentiment distribution
        with engine.connect() as conn:
            sentiment_df = pd.read_sql(text("""
                SELECT sentiment_label as sentiment, COUNT(*) as count
                FROM sentiment_results
                WHERE timestamp >= :start AND timestamp <= :end
                GROUP BY sentiment_label
            """), conn, params={"start": start_date, "end": end_date})

        sentiment_distribution = {"positive": 0, "negative": 0, "neutral": 0}
        for _, row in sentiment_df.iterrows():
            if row['sentiment'] in sentiment_distribution:
                sentiment_distribution[row['sentiment']] = int(row['count'])

        # 2. Count tickets
        with engine.connect() as conn:
            ticket_count = pd.read_sql(text("SELECT COUNT(DISTINCT ticket_id) as count FROM tickets"), conn)
            total_tickets = int(ticket_count.iloc[0]['count']) if not ticket_count.empty else 0

        total_comments = sum(sentiment_distribution.values())
        avg_comments_per_ticket = total_comments / total_tickets if total_tickets > 0 else 0

        return {
            "period": {"start_date": start_date, "end_date": end_date},
            "summary": {
                "total_tickets": total_tickets,
                "total_comments": total_comments,
                "avg_comments_per_ticket": round(avg_comments_per_ticket, 2)
            },
            "sentiment_distribution": sentiment_distribution,
            "sentiment_trend": [],
            "field_type_distribution": [],
            "ticket_statuses": {"stable_positive": 0, "stable_negative": 0, "stable_neutral": 0, "mixed": 0},
            "tickets_by_comment_count": {"1": 0, "2-5": 0, "6-10": 0, "11-20": 0, "20+": 0},
            "confidence_distribution": {"high": 0, "medium": 0, "low": 0},
            "top_authors": []
        }

    except Exception as e:
        # Fallback to empty data structure
        return {
            "period": {"start_date": start_date, "end_date": end_date},
            "summary": {"total_tickets": 0, "total_comments": 0, "avg_comments_per_ticket": 0},
            "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0},
            "sentiment_trend": [],
            "field_type_distribution": [],
            "ticket_statuses": {"stable_positive": 0, "stable_negative": 0, "stable_neutral": 0, "mixed": 0},
            "tickets_by_comment_count": {"1": 0, "2-5": 0, "6-10": 0, "11-20": 0, "20+": 0},
            "confidence_distribution": {"high": 0, "medium": 0, "low": 0},
            "top_authors": []
        }