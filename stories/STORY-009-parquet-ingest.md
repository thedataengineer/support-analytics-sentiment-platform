# STORY-009 · Parquet Ingestion Pipeline

## Status
✅ Completed

## Overview
The Jira profiler Parquet export (≈10k rows × 1,667 columns) now flows through the same asynchronous ingestion pipeline as CSV and JSON. The system streams batches, maps columns via the shared mapper, and feeds sentiment/entity processors without exhausting memory.

## Delivered Capabilities
- `POST /api/jira/ingest` queues a Celery job with the Parquet source path, initialises job tracking, and returns a status URL (`backend/api/jira_ingest.py`).
- `backend/jobs/parquet_ingest_job.py:process_parquet_job` reads Parquet batches with PyArrow, maps fields via `ColumnMapper`, invokes the NLP client for summaries/descriptions/comments, and updates `mark_job_running`/`increment_job_progress`/`mark_job_completed`.
- Entity extraction and sentiment results reuse the shared ingestion helpers so Elasticsearch, DuckDB, and downstream analytics stay in sync with CSV/JSON runs.
- Job metadata captures the total column count, record throughput, and any errors, enabling the frontend status page to show progress for large Parquet ingests.

## Reference Implementation
- Trigger endpoint: `backend/api/jira_ingest.py`
- Celery task: `backend/jobs/parquet_ingest_job.py`
- Column mapping: `backend/services/column_mapping.py`
- Job tracking: `backend/jobs/job_status.py`

## Verification
- Manual ingestion against `Jira.parquet` confirmed chunked processing, proper job state transitions, and Elasticsearch indexing.
- Existing end-to-end tests (`test_end_to_end.py`) exercise the Parquet path within the overall ingestion suite.
