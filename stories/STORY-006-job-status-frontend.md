# STORY-006 · Job Status Frontend Experience

## Overview
Deliver the UX promised in the upload story: users receive a link to a job status page that shows live progress, errors, and summaries for ingestion runs. The upload flow should navigate to this page after a successful submission.

## Acceptance Criteria
- New route `/jobs/:jobId` displays job metadata (status, timestamps, records processed, error message).
- Upload confirmation toast includes a “View status” button that routes to the job page.
- Job page polls `GET /api/job/{job_id}` every 10 seconds while `status` is `queued` or `running`, stops otherwise.
- Job list view `/jobs` (optional) pages through `GET /api/jobs`.
- Add unit tests using React Testing Library to check the polling logic and error handling.

## Routing Mockup
```jsx
// client/src/App.js
import JobStatusPage from './pages/Jobs/JobStatusPage';
import JobListPage from './pages/Jobs/JobListPage';

<Routes>
  {/* existing routes */}
  <Route path="/jobs" element={<JobListPage />} />
  <Route path="/jobs/:jobId" element={<JobStatusPage />} />
</Routes>
```

## Upload Hook Mockup
```jsx
// client/src/components/Upload/Upload.js
const navigate = useNavigate();

const handleSuccess = (file, result) => {
  enqueueSnackbar('File uploaded successfully! Processing...', {
    variant: 'success',
    action: (
      <Button color="inherit" size="small" onClick={() => navigate(`/jobs/${result.job_id}`)}>
        View status
      </Button>
    ),
  });
  setUploadedFiles(prev => [...prev, {
    name: file.name,
    size: file.size,
    jobId: result.job_id,
    status: 'queued',
  }]);
};
```

## Job Status Page Mockup
```jsx
// client/src/pages/Jobs/JobStatusPage.js
import React, { useEffect, useState, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { Card, CardContent, Typography, Chip, LinearProgress, Button } from '@mui/material';

function JobStatusPage() {
  const { jobId } = useParams();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchJob = useCallback(async () => {
    try {
      const res = await fetch(`/api/job/${jobId}`);
      if (!res.ok) throw new Error('Failed to fetch job status');
      const data = await res.json();
      setJob(data);
      setError(null);
      return data.status;
    } catch (err) {
      setError(err.message);
      return 'failed';
    } finally {
      setLoading(false);
    }
  }, [jobId]);

  useEffect(() => {
    let timer;
    const poll = async () => {
      const status = await fetchJob();
      if (status === 'queued' || status === 'running') {
        timer = setTimeout(poll, 10000);
      }
    };
    poll();
    return () => clearTimeout(timer);
  }, [fetchJob]);

  if (loading) return <LinearProgress />;
  if (error) return <Typography color="error">{error}</Typography>;

  return (
    <Card>
      <CardContent>
        <Typography variant="h5">Job {job.job_id}</Typography>
        <Chip label={job.status.toUpperCase()} color={statusColor(job.status)} />
        <Typography variant="body2">Submitted: {formatDate(job.submitted_at)}</Typography>
        {job.started_at && <Typography variant="body2">Started: {formatDate(job.started_at)}</Typography>}
        {job.completed_at && <Typography variant="body2">Completed: {formatDate(job.completed_at)}</Typography>}
        <Typography variant="body1" sx={{ mt: 2 }}>
          Records processed: {job.records_processed}
        </Typography>
        {job.error && (
          <Typography color="error" sx={{ mt: 2 }}>
            Error: {job.error}
          </Typography>
        )}
        <Button sx={{ mt: 3 }} href="/jobs" variant="outlined">
          View all jobs
        </Button>
      </CardContent>
    </Card>
  );
}
```

## Job List Mockup
```jsx
// client/src/pages/Jobs/JobListPage.js
const [jobs, setJobs] = useState([]);
const [page, setPage] = useState(0);

useEffect(() => {
  fetch(`/api/jobs?offset=${page * 20}&limit=20`)
    .then(res => res.json())
    .then(data => setJobs(data.results));
}, [page]);
```

## Styling & Testing Notes
- Reuse Material-UI components for consistent look.
- Provide status→color helper (`running` = info, `completed` = success, etc.).
- Add Jest tests mocking `fetch` to confirm polling stops after completion and errors display correctly.

