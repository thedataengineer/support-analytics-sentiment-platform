from fastapi import APIRouter, Query, HTTPException, Depends
from fastapi.responses import FileResponse
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import func, cast, Date
from sqlalchemy.orm import Session
import os
import logging
from ..services.report_summarizer import generate_pdf_report
from ..cache import cache, cached
from ..database import get_db
from ..models.sentiment_result import SentimentResult

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/sentiment/overview")
async def get_sentiment_overview(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    sentiment_type: Optional[str] = Query(None, description="Filter by sentiment type"),
    db: Session = Depends(get_db)
):
    """
    Get sentiment overview data for dashboard - queries real database
    """
    # Default to last 30 days if no dates provided
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")

    try:
        # Parse dates
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        # Query sentiment distribution
        distribution = (
            db.query(
                SentimentResult.sentiment,
                func.count(SentimentResult.id).label("count"),
            )
            .filter(SentimentResult.comment_timestamp >= start)
            .filter(SentimentResult.comment_timestamp <= end + timedelta(days=1))
            .group_by(SentimentResult.sentiment)
            .all()
        )

        # Build distribution dict with defaults
        sentiment_distribution = {"positive": 0, "negative": 0, "neutral": 0}
        for sentiment, count in distribution:
            sentiment_distribution[sentiment] = count

        # Query sentiment trend by date (using comment timestamp, not created_at)
        trend = (
            db.query(
                cast(SentimentResult.comment_timestamp, Date).label("bucket"),
                SentimentResult.sentiment,
                func.count(SentimentResult.id).label("count"),
            )
            .filter(SentimentResult.comment_timestamp >= start)
            .filter(SentimentResult.comment_timestamp <= end + timedelta(days=1))
            .group_by("bucket", SentimentResult.sentiment)
            .order_by("bucket")
            .all()
        )

        # Build trend array
        trend_map = {}
        for bucket, sentiment, count in trend:
            date_str = bucket.isoformat()
            if date_str not in trend_map:
                trend_map[date_str] = {"date": date_str, "positive": 0, "negative": 0, "neutral": 0}
            trend_map[date_str][sentiment] = count

        sentiment_trend = list(trend_map.values())

        logger.info(f"Retrieved real sentiment data for period {start_date} to {end_date}: {len(sentiment_trend)} days")
        return {
            "sentiment_distribution": sentiment_distribution,
            "sentiment_trend": sentiment_trend
        }
    except Exception as e:
        logger.error(f"Error retrieving sentiment overview: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve sentiment overview")

@router.get("/report/pdf")
async def download_pdf_report(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """
    Generate and download PDF report
    """
    if not start_date:
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")

    try:
        pdf_path = generate_pdf_report(start_date, end_date)

        return FileResponse(
            path=pdf_path,
            filename=f"sentiment_report_{start_date}_to_{end_date}.pdf",
            media_type="application/pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")
