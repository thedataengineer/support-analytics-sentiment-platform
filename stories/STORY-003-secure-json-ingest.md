# STORY-003 · Secure JSON Batch Ingest API

## Status
✅ Completed

## Overview
External systems can now submit structured feedback in bulk. The `/api/data-ingest` endpoint validates payload shape, enforces role-based access control, and reuses the shared Celery pipeline so JSON batches land in the same sentiment/entity tables as CSV uploads.

## Delivered Capabilities
- `backend/api/ingest_csv.py:ingest_data` exposes `POST /api/data-ingest`, requiring an `Authorization: Bearer` token with `analyst` or `admin` role via `require_role`.
- Pydantic models (`IngestRecord`, `IngestRequest`) cap batches at 1,000 items, require at least one text field, and normalise comment arrays before dispatch.
- Jobs are registered with `init_job` using source `json_api`, and Celery task `backend.jobs.parquet_ingest_job.process_json_ingest_parquet_task` drives ingest, emitting progress to Redis and populating tickets, sentiment results, and entities.
- API responses mirror the CSV flow, returning `job_id`, `status_url`, and a short metadata summary for the frontend.

## Reference Implementation
- Endpoint & validation: `backend/api/ingest_csv.py:229`
- Celery task: `backend/jobs/parquet_ingest_job.py:326`
- Job tracking: `backend/jobs/job_status.py`
- Auth utilities: `backend/api/auth.py` (`require_role`, JWT handling)

## Verification
- Manual smoke tests via `test_end_to_end.py` cover JSON ingestion.
- React upload workflow surfaces the returned `job_id`, enabling operators to monitor JSON imports alongside other job types.
