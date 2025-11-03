# STORY-001 · Persist Ingestion Jobs & Status API

## Overview
Implement the persistence and API layer required by the MVP so that every ingestion run (CSV or JSON) is tracked with durable metadata and exposed via REST for the frontend. This enables the status URL returned from uploads to surface live state transitions (`queued`, `running`, `completed`, `failed`) along with timestamps and progress counters.

## Acceptance Criteria
- `IngestJob` table (or ORM model) stores `job_id`, `source_type`, `file_name`, `status`, `submitted_at`, `started_at`, `completed_at`, `records_processed`, and `error`.
- FastAPI exposes:
  - `GET /api/job/{job_id}` → current status payload.
  - `GET /api/jobs` → paginated list with optional `status` filter.
- Upload and JSON ingest endpoints write an initial `queued` record before dispatching async work.
- Job status APIs hit Redis cache first (if available) and fall back to PostgreSQL.

## Data Model Mockup
```python
# backend/models/ingest_job.py
from sqlalchemy import Column, String, DateTime, Enum, Integer, Text
from sqlalchemy.sql import func
from database import Base

class IngestJob(Base):
    __tablename__ = "ingest_jobs"

    job_id = Column(String(36), primary_key=True)
    source_type = Column(String(20), nullable=False)  # csv_upload, json_api, jira_ingest, etc.
    file_name = Column(String(255))
    status = Column(Enum("queued", "running", "completed", "failed", name="ingest_job_status"), nullable=False)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    records_processed = Column(Integer, default=0)
    error = Column(Text)
```

```sql
-- db/init.sql
CREATE TYPE ingest_job_status AS ENUM ('queued', 'running', 'completed', 'failed');

CREATE TABLE IF NOT EXISTS ingest_jobs (
    job_id UUID PRIMARY KEY,
    source_type VARCHAR(20) NOT NULL,
    file_name VARCHAR(255),
    status ingest_job_status NOT NULL,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    records_processed INTEGER NOT NULL DEFAULT 0,
    error TEXT
);

CREATE INDEX IF NOT EXISTS idx_ingest_jobs_status_submitted_at
    ON ingest_jobs (status, submitted_at DESC);
```

## API Mockup
```python
# backend/api/job_status.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from models.ingest_job import IngestJob
from cache import cache

router = APIRouter(prefix="/api", tags=["ingestion"])

@router.get("/job/{job_id}")
def get_job(job_id: str, db: Session = Depends(get_db)):
    cache_key = f"ingest_job:{job_id}"
    if cached := cache.get(cache_key):
        return cached

    job = db.get(IngestJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    payload = {
        "job_id": job.job_id,
        "status": job.status,
        "submitted_at": job.submitted_at,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
        "records_processed": job.records_processed,
        "error": job.error,
    }

    cache.set(cache_key, payload, ttl=30)
    return payload

@router.get("/jobs")
def list_jobs(
    status: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(IngestJob).order_by(IngestJob.submitted_at.desc())
    if status:
        query = query.filter(IngestJob.status == status)
    jobs = query.offset(offset).limit(limit).all()
    return {
        "results": [
            {
                "job_id": job.job_id,
                "status": job.status,
                "submitted_at": job.submitted_at,
                "completed_at": job.completed_at,
                "records_processed": job.records_processed,
            }
            for job in jobs
        ],
        "offset": offset,
        "limit": limit,
    }
```

## Integration Notes
- Update existing upload handlers to insert an `IngestJob` record before scheduling work.
- Encapsulate status updates in a helper (e.g., `jobs/ingest_tracking.py`) so Celery tasks can call `mark_running`, `increment_progress`, `mark_completed`, `mark_failed`.
- Remember to register the new router inside `backend/main.py`.

