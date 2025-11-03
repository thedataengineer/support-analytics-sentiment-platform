# STORY-002 · Asynchronous CSV Processing with Celery

## Status
✅ Completed

## Overview
CSV uploads now hand off heavy lifting to Celery workers. The FastAPI layer persists the file to disk, registers a queued job, and returns immediately with a tracking link while the worker streams progress updates through the job status helpers established in STORY-001.

## Delivered Capabilities
- `POST /api/upload/file` (see `backend/api/upload_api.py`) stores the uploaded CSV under the local `uploads/` tree via `UploadService`, seeds job metadata with `init_job`, and enqueues `backend.jobs.ingest_job.process_csv_upload_task`.
- Workers call `mark_job_running`, `increment_job_progress`, `mark_job_completed`, and `mark_job_failed` so the status endpoint reflects record counts, sentiment/entity totals, and any processing errors.
- Temporary files are removed after successful processing, and job metadata captures total rows, column count, and detected text columns for visibility in the UI.
- Progress information is cached in Redis (or the in-memory fallback) which the frontend polls every few seconds.

## Reference Implementation
- Upload entry point: `backend/api/upload_api.py:16`
- Celery wiring and processing: `backend/jobs/ingest_job.py` (`process_csv_upload_task`, `process_chunk`)
- Job tracking utilities: `backend/jobs/job_status.py`
- Frontend UX: `client/src/components/Upload/Upload.js` and `client/src/pages/Jobs/JobStatusPage.js`

## Verification
- `test_end_to_end.py` triggers CSV ingestion and asserts job transitions.
- Manual testing via the React upload flow confirms navigation to `/jobs/:jobId` and real-time progress updates.
