# STORY-008 · Scheduled Reporting & Data-Driven PDFs

## Status
✅ Completed

## Overview
Analysts can configure recurring email delivery for PDF sentiment reports. Preferences persist in Postgres, Celery Beat triggers daily/weekly jobs, PDFs are generated from DuckDB metrics, and messages are dispatched via configurable SMTP settings.

## Delivered Capabilities
- `backend/models/user_preferences.py` stores per-user schedule frequency, delivery time, recipient email, and last-sent timestamp (`backend/scripts/init_postgres.sql` updated accordingly).
- New API endpoints `/api/report/schedule` (GET/POST) let analysts view or update their schedule; responses are secured with `require_role("analyst", "admin")` and leverage the authenticated user context (`backend/api/report_api.py`).
- `backend/jobs/reporting_tasks.py` registers Celery Beat schedules (daily and weekly) and implements `send_scheduled_reports`, which generates PDFs, emails them via `EmailService`, updates `last_sent_at`, and cleans up temporary files.
- SMTP configuration and report timing are driven by environment variables exposed through `config.Settings`; emails fall back to logging when SMTP credentials are absent (`backend/services/email_service.py`).
- `test_end_to_end.py` now exercises the schedule API to confirm round-trip creation and retrieval.

## Notes
- Adjust `.env` with SMTP credentials (`SMTP_HOST`, `SMTP_PORT`, `REPORTS_FROM_EMAIL`, etc.) and run Celery beat alongside workers to enable automated delivery.*** End Patch
