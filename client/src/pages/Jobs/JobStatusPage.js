import React, { useEffect, useState } from 'react';
import { useParams, Link as RouterLink } from 'react-router-dom';
import {
  Container,
  Card,
  CardContent,
  Typography,
  Chip,
  LinearProgress,
  Stack,
  Button,
  Divider,
} from '@mui/material';

const STATUS_COLOR_MAP = {
  queued: 'default',
  running: 'info',
  completed: 'success',
  failed: 'error',
};

const formatDate = (value) => (value ? new Date(value).toLocaleString() : '—');

function JobStatusPage() {
  const { jobId } = useParams();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isActive = true;
    let timer;

    const fetchJob = async () => {
      try {
        const response = await fetch(`/api/job/${jobId}`);
        if (!response.ok) {
          throw new Error('Failed to load job status');
        }
        const data = await response.json();
        if (!isActive) {
          return;
        }
        setJob(data);
        setError(null);
        setLoading(false);

        if (['queued', 'running'].includes(data.status)) {
          timer = setTimeout(fetchJob, 5000);
        }
      } catch (err) {
        if (!isActive) {
          return;
        }
        setError(err.message);
        setLoading(false);
      }
    };

    fetchJob();

    return () => {
      isActive = false;
      if (timer) {
        clearTimeout(timer);
      }
    };
  }, [jobId]);

  const renderProgress = () => {
    if (!job) return null;
    const total = job.total_rows ?? 0;
    const processed = job.records_processed ?? 0;
    if (!total || total <= 0) return null;
    const percent = Math.round((processed / total) * 100);
    return (
      <Stack spacing={1}>
        <Typography variant="body2" color="text.secondary">
          Processed {processed.toLocaleString()} / {total.toLocaleString()}
        </Typography>
        <LinearProgress variant="determinate" value={percent} />
      </Stack>
    );
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 6 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
        <Typography variant="h4">Ingestion Job</Typography>
        <Button component={RouterLink} to="/jobs" variant="outlined">
          Back to Jobs
        </Button>
      </Stack>

      <Card>
        <CardContent>
          {loading && <LinearProgress sx={{ mb: 2 }} />}
          {error && (
            <Typography color="error" sx={{ mb: 2 }}>
              {error}
            </Typography>
          )}
          {job && (
            <Stack spacing={2}>
              <Stack direction="row" spacing={2} alignItems="center">
                <Typography variant="h5">{job.job_id}</Typography>
                <Chip
                  label={job.status?.toUpperCase() ?? 'UNKNOWN'}
                  color={STATUS_COLOR_MAP[job.status] || 'default'}
                />
              </Stack>

              <Divider />

              <Stack spacing={1}>
                <Typography variant="body1">
                  <strong>Source:</strong> {job.source ?? '—'}
                </Typography>
                <Typography variant="body1">
                  <strong>File:</strong> {job.file_name ?? '—'}
                </Typography>
                <Typography variant="body1">
                  <strong>Submitted:</strong> {formatDate(job.submitted_at)}
                </Typography>
                <Typography variant="body1">
                  <strong>Started:</strong> {formatDate(job.started_at)}
                </Typography>
                <Typography variant="body1">
                  <strong>Completed:</strong> {formatDate(job.completed_at)}
                </Typography>
                <Typography variant="body1">
                  <strong>Duration:</strong>{' '}
                  {job.duration ? `${job.duration.toFixed(2)}s` : '—'}
                </Typography>
              </Stack>

              {renderProgress()}

              <Stack direction="row" spacing={4}>
                <Typography variant="body2" color="text.secondary">
                  Sentiment rows: {(job.sentiment_records ?? 0).toLocaleString()}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Entity rows: {(job.entity_records ?? 0).toLocaleString()}
                </Typography>
              </Stack>

              {job.error && (
                <Card variant="outlined" sx={{ borderColor: 'error.main', backgroundColor: 'error.light', p: 2 }}>
                  <Typography variant="subtitle2" color="error">
                    Error details
                  </Typography>
                  <Typography variant="body2" color="error.main">
                    {job.error}
                  </Typography>
                </Card>
              )}
            </Stack>
          )}
        </CardContent>
      </Card>
    </Container>
  );
}

export default JobStatusPage;
