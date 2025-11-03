# STORY-003 · Secure JSON Batch Ingest API

## Overview
Provide the authenticated JSON ingestion endpoint described in the MVP so CRM or upstream systems can batch-submit structured feedback, reuse the shared job tracking, and trigger the same NLP pipeline used for CSV uploads.

## Acceptance Criteria
- Endpoint lives in `backend/api/data_ingest.py` with route `POST /api/data-ingest`.
- Requests must include a valid JWT (preferred) or API key header before work is accepted.
- Payload validation enforces array length ≤ 1,000 and required fields (`id`, `summary` and/or `description`).
- Enqueues Celery task `process_json_ingest` that reuses the same processing logic as CSV (`process_records` helper).
- Job status response mirrors CSV upload (`job_id`, `status_url`).

## FastAPI Mockup
```python
# backend/api/data_ingest.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, validator
from typing import List
from services.auth import get_current_user  # wrapper around auth.verify_token
from jobs.celery_config import celery_app
from models.ingest_job import IngestJob

router = APIRouter(prefix="/api", tags=["ingestion"])

class IngestRecord(BaseModel):
    id: str = Field(..., max_length=100)
    summary: str | None = None
    description: str | None = None
    comments: List[str] | None = None

    @validator("summary", "description", pre=True, always=True)
    def at_least_one_text(cls, v, values):
        if not (v or values.get("description")):
            raise ValueError("summary or description required")
        return v

class IngestRequest(BaseModel):
    records: List[IngestRecord]

    @validator("records")
    def cap_batch_size(cls, records):
        if len(records) == 0:
            raise ValueError("records cannot be empty")
        if len(records) > 1000:
            raise ValueError("records exceeds batch limit of 1000")
        return records

@router.post("/data-ingest")
def ingest_records(payload: IngestRequest, user=Depends(get_current_user), db: Session = Depends(get_db)):
    job_id = str(uuid.uuid4())
    job = IngestJob(
        job_id=job_id,
        source_type="json_api",
        status="queued",
        file_name=f"{len(payload.records)}-records.json",
    )
    db.add(job)
    db.commit()

    celery_app.send_task(
        "backend.jobs.ingest_job.process_json_ingest_task",
        args=[job_id, payload.dict()],
    )

    return {
        "job_id": job_id,
        "status_url": f"/api/job/{job_id}"
    }
```

## Worker Mockup
```python
# backend/jobs/ingest_job.py
@celery_app.task(name="backend.jobs.ingest_job.process_json_ingest_task", bind=True)
def process_json_ingest_task(self, job_id: str, payload: dict):
    records = payload["records"]
    with get_db_context() as db:
        _update_status(db, job_id, status="running", started_at=datetime.utcnow())

        for idx, record in enumerate(records, start=1):
            process_record(record, db)  # shared helper with CSV path
            cache.set(f"ingest_progress:{job_id}", {"records_processed": idx}, ttl=30)

        _update_status(
            db,
            job_id,
            status="completed",
            completed_at=datetime.utcnow(),
            records_processed=len(records),
        )
```

## Auth Notes
- Reuse JWT utilities from STORY-005 once implemented (`@require_role(["analyst", "admin"])`).
- Optionally support static API keys via environment variable and dependency.
- Add tests covering missing/invalid token and oversize batch rejection.

