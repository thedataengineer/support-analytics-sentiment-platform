import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Box,
  Chip,
  Stack,
  IconButton,
  Collapse
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import HourglassEmptyIcon from '@mui/icons-material/HourglassEmpty';

function ProgressTracker({ jobId, onComplete }) {
  const [jobStatus, setJobStatus] = useState(null);
  const [expanded, setExpanded] = useState(true);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!jobId) return;

    const checkStatus = async () => {
      try {
        setLoading(true);
        const apiUrl = process.env.REACT_APP_API_URL || '';
        const response = await fetch(`${apiUrl}/api/job/${jobId}`);
        const status = await response.json();
        setJobStatus(status);

        if (status.status === 'completed' || status.status === 'failed') {
          onComplete && onComplete(status);
        } else {
          // Continue polling
          setTimeout(checkStatus, 2000);
        }
      } catch (error) {
        console.error('Failed to check job status:', error);
      } finally {
        setLoading(false);
      }
    };

    checkStatus();
  }, [jobId, onComplete]);

  if (!jobId || !jobStatus) return null;

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <CheckCircleIcon color="success" />;
      case 'failed': return <ErrorIcon color="error" />;
      case 'running': return <HourglassEmptyIcon color="primary" />;
      default: return <HourglassEmptyIcon color="disabled" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'running': return 'primary';
      default: return 'default';
    }
  };

  const progress = jobStatus.total_rows > 0 
    ? (jobStatus.records_processed / jobStatus.total_rows) * 100 
    : 0;

  return (
    <Card sx={{ mt: 2 }}>
      <CardContent>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">
            Processing Status
          </Typography>
          <IconButton onClick={() => setExpanded(!expanded)} size="small">
            {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        </Stack>

        <Collapse in={expanded}>
          <Box sx={{ mt: 2 }}>
            <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 2 }}>
              {getStatusIcon(jobStatus.status)}
              <Chip 
                label={jobStatus.status.toUpperCase()} 
                color={getStatusColor(jobStatus.status)}
                size="small"
              />
              <Typography variant="body2" color="text.secondary">
                Job ID: {jobId}
              </Typography>
            </Stack>

            {jobStatus.status === 'running' && (
              <Box sx={{ mb: 2 }}>
                <LinearProgress 
                  variant="determinate" 
                  value={progress} 
                  sx={{ height: 8, borderRadius: 4 }}
                />
                <Typography variant="body2" sx={{ mt: 1 }}>
                  {jobStatus.records_processed?.toLocaleString() || 0} / {jobStatus.total_rows?.toLocaleString() || 0} records processed ({progress.toFixed(1)}%)
                </Typography>
              </Box>
            )}

            {jobStatus.status === 'completed' && (
              <Typography variant="body2" color="success.main">
                ✅ Successfully processed {jobStatus.records_processed?.toLocaleString()} records
              </Typography>
            )}

            {jobStatus.status === 'failed' && jobStatus.error && (
              <Typography variant="body2" color="error.main">
                ❌ {jobStatus.error}
              </Typography>
            )}

            {jobStatus.started_at && (
              <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                Started: {new Date(jobStatus.started_at).toLocaleString()}
              </Typography>
            )}

            {jobStatus.completed_at && (
              <Typography variant="caption" color="text.secondary" display="block">
                Completed: {new Date(jobStatus.completed_at).toLocaleString()}
              </Typography>
            )}
          </Box>
        </Collapse>
      </CardContent>
    </Card>
  );
}

export default ProgressTracker;