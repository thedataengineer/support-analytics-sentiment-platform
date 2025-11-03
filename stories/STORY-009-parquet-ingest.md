# STORY-009 · Parquet Ingestion Pipeline

## Overview
Support direct ingestion of the Jira profiler export stored at `/Users/karteek/dev/work/accionlabs/jira-profiler/Jira.parquet`. The file contains 10,000 rows × 1,667 columns (confirmed via `pyarrow` in the `support` pyenv), so the ingestion pipeline must stream data efficiently, reuse the shared column mapping, and feed the NLP processors without materializing the entire dataset in memory.

### Current State
- `backend/api/jira_ingest.py` loads the entire Parquet file synchronously and calls `process_parquet_data`.
- `backend/jobs/ingest_job.py::process_parquet_data` iterates the in-memory DataFrame and reuses NLP calls, but:
  - it assumes the DataFrame is already loaded (no chunking/streaming),
  - it bypasses Celery and `IngestJob` status updates,
  - it does not populate Elasticsearch or job progress caches.
- Tests (`test_jira_ingest.py`) exercise this synchronous path.

### Gaps
1. Need an asynchronous ingestion path mirroring CSV/JSON jobs to avoid blocking requests.
2. Must update shared job tracking so Parquet ingestion reports progress and errors.
3. Should avoid loading all 1,667 columns × 10,000 rows into memory when running in production.

## Acceptance Criteria
- Backend exposes a task or endpoint that accepts a Parquet source path (initially the local default above, later configurable).
- Pipeline reads Parquet in chunks (via `pyarrow.dataset` or `pandas.read_parquet` with `pyarrow`), mapping columns onto the unified schema (`ticket_id`, `summary`, `description`, comments, etc.).
- Resulting records flow through the same processing helpers as CSV/JSON, updating `IngestJob` progress and persisting tickets, sentiments, entities, and search indices.
- Automation confirms schema width (1,667 columns) and logs mapped/unmapped columns for traceability.

## Implementation Sketch
```python
# backend/jobs/parquet_ingest.py
from pyarrow import dataset as ds
from jobs.ingest_job import process_record
from models.ingest_job import IngestJob

def process_parquet_source(job_id: str, parquet_path: str):
    dset = ds.dataset(parquet_path, format="parquet")
    column_names = dset.schema.names
    logger.info("Parquet schema: %s columns", len(column_names))

    mapper = ColumnMapper()
    mapping = mapper.create_mapping(column_names, source_name="jira_parquet")

    with get_db_context() as db:
        update_job(db, job_id, status="running", started_at=datetime.utcnow(), total_columns=len(column_names))

    record_count = 0
    for batch in dset.to_batches(max_chunksize=500):
        df = batch.to_pandas()
        filtered = mapper.apply_mapping(df, mapping)
        for _, row in filtered.iterrows():
            process_record(row, job_id)
            record_count += 1
            if record_count % 100 == 0:
                cache.set(f"ingest_progress:{job_id}", {"records_processed": record_count}, ttl=30)

    with get_db_context() as db:
        update_job(db, job_id, status="completed", completed_at=datetime.utcnow(), records_processed=record_count)
```

## Trigger Path
```python
# backend/api/upload_api.py
@router.post("/upload/parquet", dependencies=[Depends(require_role("analyst", "admin"))])
def trigger_parquet_ingest(request: ParquetIngestRequest, db: Session = Depends(get_db)):
    job_id = str(uuid.uuid4())
    job = IngestJob(
        job_id=job_id,
        source_type="parquet",
        status="queued",
        file_name=os.path.basename(request.parquet_path),
    )
    db.add(job)
    db.commit()

    celery_app.send_task(
        "backend.jobs.parquet_ingest.process_parquet_task",
        args=[job_id, request.parquet_path],
    )

    return {"job_id": job_id, "status_url": f"/api/job/{job_id}"}
```

## Validation Notes
- Include smoke test that asserts `pf.metadata.num_columns == 1667` so regressions get flagged if schema changes.
- Log unmapped columns to help refine `column_mappings.json`.
- Update ingestion tests to cover parquet path with mocked dataset (e.g., using `pyarrow.Table.from_pandas`).

## Current Implementation Touchpoints
- `backend/api/jira_ingest.py` schedules the Celery task and seeds the job tracker.
- `backend/jobs/ingest_job.py::process_parquet_job` performs chunked ingestion with status updates.
- `backend/jobs/job_status.py` stores progress snapshots in Redis (or in-memory fallback).
