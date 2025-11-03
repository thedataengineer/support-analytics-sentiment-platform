import React, { useEffect, useState } from 'react';
import {
  Container,
  Card,
  CardContent,
  Typography,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Chip,
  Stack,
  TextField,
  MenuItem,
  Button,
  LinearProgress,
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

const STATUS_OPTIONS = [
  { label: 'All', value: '' },
  { label: 'Queued', value: 'queued' },
  { label: 'Running', value: 'running' },
  { label: 'Completed', value: 'completed' },
  { label: 'Failed', value: 'failed' },
];

const STATUS_COLOR_MAP = {
  queued: 'default',
  running: 'info',
  completed: 'success',
  failed: 'error',
};

const formatDate = (value) => (value ? new Date(value).toLocaleString() : '—');

function JobListPage() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState('');

  useEffect(() => {
    const fetchJobs = async () => {
      setLoading(true);
      try {
        const apiUrl = process.env.REACT_APP_API_URL || '';
        const params = new URLSearchParams();
        if (statusFilter) {
          params.append('status', statusFilter);
        }
        const response = await fetch(`${apiUrl}/api/jobs?${params.toString()}`);
        if (!response.ok) {
          throw new Error('Failed to load jobs');
        }
        const data = await response.json();
        setJobs(data.results || []);
        setError(null);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchJobs();
  }, [statusFilter]);

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 6 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
        <Typography variant="h4">Ingestion Jobs</Typography>
        <Button component={RouterLink} to="/upload" variant="contained">
          New Upload
        </Button>
      </Stack>

      <Card>
        {loading && <LinearProgress />}
        <CardContent>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} sx={{ mb: 2 }}>
            <TextField
              select
              label="Status"
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value)}
              size="small"
              sx={{ width: 200 }}
            >
              {STATUS_OPTIONS.map((option) => (
                <MenuItem key={option.value || 'all'} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </TextField>
            {error && (
              <Typography color="error" variant="body2">
                {error}
              </Typography>
            )}
          </Stack>

          {jobs.length === 0 && !loading ? (
            <Typography variant="body2" color="text.secondary">
              No jobs to display.
            </Typography>
          ) : (
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Job ID</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell align="right">Records Processed</TableCell>
                  <TableCell align="right">Sentiment Records</TableCell>
                  <TableCell>Submitted</TableCell>
                  <TableCell>Completed</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {jobs.map((job) => (
                  <TableRow key={job.job_id} hover>
                    <TableCell sx={{ maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {job.job_id}
                    </TableCell>
                    <TableCell>
                      <Chip
                        size="small"
                        label={job.status?.toUpperCase() ?? 'UNKNOWN'}
                        color={STATUS_COLOR_MAP[job.status] || 'default'}
                      />
                    </TableCell>
                    <TableCell align="right">
                      {(job.records_processed ?? 0).toLocaleString()}
                    </TableCell>
                    <TableCell align="right">
                      {(job.sentiment_records ?? 0).toLocaleString()}
                    </TableCell>
                    <TableCell>{formatDate(job.submitted_at)}</TableCell>
                    <TableCell>{formatDate(job.completed_at)}</TableCell>
                    <TableCell align="right">
                      <Button
                        component={RouterLink}
                        to={`/jobs/${job.job_id}`}
                        size="small"
                        variant="text"
                      >
                        View
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </Container>
  );
}

export default JobListPage;
