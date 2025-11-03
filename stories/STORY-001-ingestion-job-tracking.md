# STORY-001 · Persist Ingestion Jobs & Status API

## Status
✅ Completed

## Overview
Every ingestion workflow (CSV upload, JSON batch, Jira Parquet) now records its lifecycle so the frontend can link to a live status page. Metadata is written as soon as a job is queued, progress is streamed while Celery workers run, and the final outcome is available for seven days.

## Delivered Capabilities
- `backend/jobs/job_status.py` maintains job metadata in Redis when available, with a deterministic in-memory fallback for local development. Each job captures source type, timestamps, record counters, and error details.
- All ingestion entry points (`upload_api`, `/api/data-ingest`, `/api/ingest/csv`, Jira parquet trigger) call `init_job`, `mark_job_running`, `increment_job_progress`, `mark_job_completed`, and `mark_job_failed` to emit state transitions.
- FastAPI routes `GET /api/job/{job_id}` and `GET /api/jobs` surface the cached payloads that the frontend uses for polling (`backend/api/ingest_csv.py`).
- Progress snapshots are keyed off `ingest_job:<id>` and expire after one week, matching the UX expectation that recent runs remain visible without hitting the relational database.

## Reference Implementation
- Job tracking helpers: `backend/jobs/job_status.py`
- Job status API: `backend/api/ingest_csv.py:get_job_status` & `list_job_statuses`
- Celery integration points: `backend/jobs/ingest_job.py`, `backend/jobs/parquet_ingest_job.py`
- Cache plumbing: `backend/cache.py` (Redis with local fallback)

## Verification
- `test_end_to_end.py` exercises ingestion flows and asserts job metadata updates.
- Frontend job pages (`client/src/pages/Jobs/JobStatusPage.js`, `JobListPage.js`) poll the endpoints and render state transitions based on the tracked payload.
