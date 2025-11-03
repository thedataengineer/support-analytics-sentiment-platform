# STORY-004 · Database-Backed Sentiment Overview

## Overview
Replace the mocked sentiment metrics used by the dashboard with real aggregations from PostgreSQL so product managers can visualize actual customer feedback trends across configurable date ranges.

## Acceptance Criteria
- `/api/sentiment/overview` accepts `start_date`, `end_date`, `sentiment_type` query params, validates them, and queries PostgreSQL via SQLAlchemy.
- Response structure matches the spec (`sentiment_distribution`, `sentiment_trend` array).
- Results cached in Redis for ~5 minutes keyed by the normalized query parameters.
- Include unit tests covering empty datasets and filter combinations.

## Query Mockup
```python
# backend/api/report_api.py
from sqlalchemy import func, cast, Date
from models.sentiment_result import SentimentResult

def _parse_date(param: str, default: datetime) -> date:
    try:
        return datetime.fromisoformat(param).date()
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid date: {param}")

@router.get("/sentiment/overview")
@cached(ttl=300, key_builder=make_overview_cache_key)
def get_sentiment_overview(
    start_date: str | None = None,
    end_date: str | None = None,
    sentiment_type: str | None = Query(None, regex="^(positive|negative|neutral)$"),
    db: Session = Depends(get_db),
):
    start = _parse_date(start_date, datetime.utcnow() - timedelta(days=30))
    end = _parse_date(end_date, datetime.utcnow())

    base_query = db.query(SentimentResult).filter(
        SentimentResult.created_at >= start,
        SentimentResult.created_at <= end + timedelta(days=1),
    )
    if sentiment_type:
        base_query = base_query.filter(SentimentResult.sentiment == sentiment_type)

    distribution = (
        db.query(
            SentimentResult.sentiment,
            func.count(SentimentResult.id).label("count"),
        )
        .filter(SentimentResult.created_at.between(start, end + timedelta(days=1)))
        .group_by(SentimentResult.sentiment)
        .all()
    )

    trend = (
        db.query(
            cast(SentimentResult.created_at, Date).label("bucket"),
            SentimentResult.sentiment,
            func.count(SentimentResult.id).label("count"),
        )
        .filter(SentimentResult.created_at.between(start, end + timedelta(days=1)))
        .group_by("bucket", SentimentResult.sentiment)
        .order_by("bucket")
        .all()
    )

    sentiment_distribution = {sentiment: 0 for sentiment in ["positive", "negative", "neutral"]}
    for sentiment, count in distribution:
        sentiment_distribution[sentiment] = count

    trend_map: dict[date, dict[str, int]] = {}
    for bucket, sentiment, count in trend:
        trend_map.setdefault(bucket.isoformat(), {"positive": 0, "negative": 0, "neutral": 0})
        trend_map[bucket.isoformat()][sentiment] = count

    sentiment_trend = [
        {"date": day, **counts}
        for day, counts in sorted(trend_map.items())
    ]

    return {
        "sentiment_distribution": sentiment_distribution,
        "sentiment_trend": sentiment_trend,
    }
```

## Testing Notes
- Use SQLAlchemy session fixtures with in-memory SQLite to seed sample `SentimentResult` rows.
- Add tests ensuring invalid date formats return 400 and that filters reduce counts appropriately.
- Extend frontend dashboard tests to assert the API data is rendered (mock fetch).

