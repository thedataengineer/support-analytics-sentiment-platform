# STORY-002 · Asynchronous CSV Processing with Celery

## Overview
Move the CSV ingestion pipeline off the FastAPI thread and into Celery workers so large Jira exports run asynchronously while streaming progress back through the job tracker introduced in STORY-001.

## Acceptance Criteria
- `/api/upload` stores the file, records a `queued` job, and immediately enqueues a Celery task instead of running `process_csv_upload` synchronously.
- Celery worker updates job state transitions (`running`, `completed`, `failed`) and increments `records_processed`.
- Progress snapshots stored in Redis (e.g., `ingest_progress:{job_id}`) so the status API can read without hitting the DB on every poll.
- Temporary files are cleaned up by the worker after processing.

## Queue Wiring Mockup
```python
# backend/api/upload_api.py
from fastapi import APIRouter, UploadFile, File, BackgroundTasks
from jobs.celery_config import celery_app
from models.ingest_job import IngestJob

@router.post("/upload")
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    job_id = str(uuid.uuid4())
    persisted_path = _persist_temp_file(file, job_id)

    job = IngestJob(
        job_id=job_id,
        source_type="csv_upload",
        file_name=file.filename,
        status="queued",
    )
    db.add(job)
    db.commit()

    celery_app.send_task(
        "backend.jobs.ingest_job.process_csv_upload_task",
        args=[persisted_path, job_id],
    )

    return {"job_id": job_id, "status_url": f"/api/job/{job_id}"}
```

## Celery Task Mockup
```python
# backend/jobs/ingest_job.py
from jobs.celery_config import celery_app
from models.ingest_job import IngestJob
from sqlalchemy.orm import Session

def _update_status(db: Session, job_id: str, **kwargs):
    job = db.get(IngestJob, job_id)
    for key, value in kwargs.items():
        setattr(job, key, value)
    db.commit()

@celery_app.task(name="backend.jobs.ingest_job.process_csv_upload_task", bind=True)
def process_csv_upload_task(self, file_path: str, job_id: str):
    with get_db_context() as db:
        _update_status(db, job_id, status="running", started_at=datetime.utcnow())

    try:
        stats = process_csv_upload(file_path, job_id, on_progress=_emit_progress)
        with get_db_context() as db:
            _update_status(
                db,
                job_id,
                status="completed",
                completed_at=datetime.utcnow(),
                records_processed=stats["processed_rows"],
            )
    except Exception as exc:
        with get_db_context() as db:
            _update_status(
                db,
                job_id,
                status="failed",
                completed_at=datetime.utcnow(),
                error=str(exc),
            )
        raise
```

```python
# backend/jobs/ingest_job.py (process_csv_upload signature)
def process_csv_upload(file_path: str, job_id: str, on_progress: Callable[[int], None]) -> Dict[str, Any]:
    ...
    for chunk in chunks:
        # existing processing
        processed += len(chunk)
        cache.set(f"ingest_progress:{job_id}", {"records_processed": processed}, ttl=30)
        on_progress(processed)
```

## Worker Ops Notes
- Ensure `celery -A backend.jobs.celery_config worker` is the official command in docs.
- Add retry/backoff policy on transient errors (e.g., DB connection resets) using Celery’s retry utilities.
- Update deployment docs so Celery workers run as separate services in `docker-compose`.

