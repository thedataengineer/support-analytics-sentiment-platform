# MVP Story Matrix

| Story | Title | Status | Notes | Spec |
|-------|-------|--------|-------|------|
| STORY-001 | Persist ingestion jobs & status API | ✅ Completed | Redis-backed tracker, `/api/job/{id}` & `/api/jobs` now live; used by parquet pipeline. | [stories/STORY-001-ingestion-job-tracking.md](../stories/STORY-001-ingestion-job-tracking.md) |
| STORY-002 | Asynchronous CSV processing with Celery | ⚠️ In progress | CSV endpoint still executes synchronously; needs Celery task wiring and status updates similar to parquet job. | [stories/STORY-002-csv-celery-processing.md](../stories/STORY-002-csv-celery-processing.md) |
| STORY-003 | Secure JSON batch ingest API | ⛔ Not started | `/api/data-ingest` remains a stub with no auth/job tracking. | [stories/STORY-003-secure-json-ingest.md](../stories/STORY-003-secure-json-ingest.md) |
| STORY-004 | Database-backed sentiment overview | ⛔ Not started | Dashboard still uses mocked data; requires SQL aggregation + caching. | [stories/STORY-004-sentiment-overview.md](../stories/STORY-004-sentiment-overview.md) |
| STORY-005 | Authentication & role-based access control | ⛔ Not started | Auth endpoints still hard-coded; no persisted users or role guards. | [stories/STORY-005-auth-rbac.md](../stories/STORY-005-auth-rbac.md) |
| STORY-006 | Job status frontend experience | ⛔ Not started | Upload UI lacks status page/route; needs polling UI against new APIs. | [stories/STORY-006-job-status-frontend.md](../stories/STORY-006-job-status-frontend.md) |
| STORY-007 | Search & entity insights | ⛔ Not started | Search/Entities endpoints serve mock data; no PostgreSQL/Elasticsearch wiring. | [stories/STORY-007-search-entities.md](../stories/STORY-007-search-entities.md) |
| STORY-008 | Scheduled reporting & PDF data sourcing | ⛔ Not started | PDF uses mock data; no Celery Beat or email service yet. | [stories/STORY-008-scheduled-reporting.md](../stories/STORY-008-scheduled-reporting.md) |
| STORY-009 | Parquet ingestion pipeline | ✅ Completed | Parquet jobs now stream via Celery, update job tracker, and regenerate column mappings dynamically. | [stories/STORY-009-parquet-ingest.md](../stories/STORY-009-parquet-ingest.md) |

Legend: ✅ Completed · ⚠️ In progress · ⛔ Not started
