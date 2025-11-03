from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import FileResponse
from datetime import datetime, time, timedelta
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
import logging
from services.report_summarizer import generate_pdf_report
from cache import cache, cached
from storage.storage_manager import StorageManager
from database import get_db
from models import User, UserReportPreference
from api.auth import require_role

logger = logging.getLogger(__name__)

router = APIRouter()


class ScheduleRequest(BaseModel):
    schedule_frequency: str = Field(..., pattern="^(daily|weekly)$")
    delivery_time: time = Field(default=time(8, 0))
    email: EmailStr


class ScheduleResponse(BaseModel):
    schedule_frequency: str
    delivery_time: time
    email: EmailStr
    last_sent_at: Optional[datetime] = None

@router.get("/sentiment/overview")
async def get_sentiment_overview(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    sentiment_type: Optional[str] = Query(None, description="Filter by sentiment type")
):
    """
    Get sentiment overview data for dashboard using DuckDB on Parquet data
    """
    # Default to last 30 days if no dates provided
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")

    storage = StorageManager()
    
    try:
        # Query sentiment distribution
        distribution_sql = f"""
        SELECT sentiment, COUNT(*) as count
        FROM sentiment_data 
        WHERE timestamp >= '{start_date}' AND timestamp <= '{end_date}'
        GROUP BY sentiment
        """
        
        distribution_df = storage.execute_query(distribution_sql, {'sentiment_data': 'sentiment/data.parquet'})
        
        # Build distribution dict with defaults
        sentiment_distribution = {"positive": 0, "negative": 0, "neutral": 0}
        for _, row in distribution_df.iterrows():
            sentiment_distribution[row['sentiment']] = int(row['count'])

        # Query sentiment trend by date
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
        
        # Build trend array
        trend_map = {}
        for _, row in trend_df.iterrows():
            date_str = str(row['date'])
            if date_str not in trend_map:
                trend_map[date_str] = {"date": date_str, "positive": 0, "negative": 0, "neutral": 0}
            trend_map[date_str][row['sentiment']] = int(row['count'])

        sentiment_trend = list(trend_map.values())

        logger.info(f"Retrieved sentiment data from Parquet for period {start_date} to {end_date}: {len(sentiment_trend)} days")
        return {
            "sentiment_distribution": sentiment_distribution,
            "sentiment_trend": sentiment_trend
        }
        
    except Exception as e:
        logger.error(f"Error retrieving sentiment overview from Parquet: {e}", exc_info=True)
        # Return empty data structure on error
        return {
            "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0},
            "sentiment_trend": []
        }


def _resolve_user(payload: dict, db: Session) -> User:
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(User).filter(User.email == email).one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/report/schedule", response_model=ScheduleResponse)
async def get_report_schedule(
    payload: dict = Depends(require_role("analyst", "admin")),
    db: Session = Depends(get_db),
):
    user = _resolve_user(payload, db)
    preference = (
        db.query(UserReportPreference)
        .filter(UserReportPreference.user_id == user.id)
        .one_or_none()
    )
    if not preference:
        raise HTTPException(status_code=404, detail="No schedule configured")

    return ScheduleResponse(
        schedule_frequency=preference.schedule_frequency,
        delivery_time=preference.delivery_time,
        email=preference.email,
        last_sent_at=preference.last_sent_at,
    )


@router.post("/report/schedule", response_model=ScheduleResponse)
async def upsert_report_schedule(
    request: ScheduleRequest,
    payload: dict = Depends(require_role("analyst", "admin")),
    db: Session = Depends(get_db),
):
    user = _resolve_user(payload, db)
    preference = (
        db.query(UserReportPreference)
        .filter(UserReportPreference.user_id == user.id)
        .one_or_none()
    )

    if preference:
        preference.schedule_frequency = request.schedule_frequency
        preference.delivery_time = request.delivery_time
        preference.email = request.email
    else:
        preference = UserReportPreference(
            user_id=user.id,
            schedule_frequency=request.schedule_frequency,
            delivery_time=request.delivery_time,
            email=request.email,
        )
        db.add(preference)

    db.commit()
    db.refresh(preference)

    return ScheduleResponse(
        schedule_frequency=preference.schedule_frequency,
        delivery_time=preference.delivery_time,
        email=preference.email,
        last_sent_at=preference.last_sent_at,
    )

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
