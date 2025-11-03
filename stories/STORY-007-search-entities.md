# STORY-007 · Search & Entity Insights Backed by Data Stores

## Status
✅ Completed

## Overview
Analysts can now search ingested tickets and inspect the entities extracted by the NLP pipeline. The backend prefers Elasticsearch when available and seamlessly falls back to DuckDB queries over the Parquet snapshots, ensuring search remains functional in local environments.

## Delivered Capabilities
- `GET /api/search` orchestrates Elasticsearch full-text queries (summary, description, ticket ID) and gracefully downgrades to DuckDB `ILIKE` filters against `sentiment_data.parquet` when the cluster is unavailable (`backend/api/search_api.py`).
- `GET /api/entities/top` returns the most frequent entities for the requested window, using ES aggregations or DuckDB grouping over `entity_data.parquet` + `ticket_data.parquet`.
- Ingestion jobs push ticket summaries, descriptions, ultimate sentiment, and entity arrays into the Elasticsearch index via `backend/services/elasticsearch_client.py`, so search results are enriched with confidence scores and entity context.
- Frontend components (`client/src/components/Dashboard/RecentTicketsTable.js`, `client/src/components/EntitiesPanel/EntitiesPanel.js`) fetch the live APIs, render paginated results, and allow filtering by sentiment and date.

## Reference Implementation
- Backend API: `backend/api/search_api.py`
- Elasticsearch client & fallback logic: `backend/services/elasticsearch_client.py`
- Frontend integration: `client/src/components/EntitiesPanel/EntitiesPanel.js`, `client/src/components/Dashboard/RecentTicketsTable.js`
- Job indexing hook: `backend/jobs/ingest_job.py` and `backend/jobs/parquet_ingest_job.py` (ticket indexing + entity collection)

## Follow-ups
- Add automated tests that spin up DuckDB fixtures to validate fallback queries and verify entity aggregation limits.
- Consider exposing highlighted snippets in the search response when Elasticsearch is enabled to improve UX.
