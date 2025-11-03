# STORY-006 · Job Status Frontend Experience

## Status
✅ Completed

## Overview
After any upload or API ingest, users land on a status view that visualises progress in near real time. The UI polls the backend job tracker, surfaces errors, and provides a consolidated list of recent runs so analysts can confirm data arrived without digging into logs.

## Delivered Capabilities
- React routes `/jobs` and `/jobs/:jobId` render `JobListPage` and `JobStatusPage` respectively (`client/src/App.js`).
- The upload success snackbar includes a “View status” action that navigates directly to `/jobs/{job_id}` (`client/src/components/Upload/Upload.js`).
- `JobStatusPage` polls `GET /api/job/{job_id}` every 10 seconds while the job is `queued` or `running`, auto-stopping once it reaches a terminal state. Progress, timestamps, and error messages are displayed with Material UI components.
- `JobListPage` calls `GET /api/jobs` and renders the latest jobs with pagination controls, providing quick access to historical runs.
- Shared helpers format timestamps, map statuses to chip colours, and guard against fetch failures so the UX remains responsive.

## Reference Implementation
- Routing: `client/src/App.js`
- Upload UX + navigation: `client/src/components/Upload/Upload.js`
- Status page: `client/src/pages/Jobs/JobStatusPage.js`
- Job list: `client/src/pages/Jobs/JobListPage.js`

## Verification
- Manual end-to-end flows validate that a job link appears immediately after uploading and that progress updates as the Celery worker runs.
- Jest tests under `client/src/pages/Jobs/__tests__/` mock fetch to exercise polling, terminal state handling, and error messaging (add coverage as new behaviours ship).
