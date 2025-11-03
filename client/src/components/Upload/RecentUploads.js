import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Box,
  LinearProgress
} from '@mui/material';
import VisibilityIcon from '@mui/icons-material/Visibility';
import { useNavigate } from 'react-router-dom';

function RecentUploads({ uploads = [] }) {
  const navigate = useNavigate();

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'running': return 'primary';
      case 'queued': return 'warning';
      default: return 'default';
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getProgress = (upload) => {
    if (!upload.totalRows || upload.totalRows === 0) return 0;
    return (upload.recordsProcessed / upload.totalRows) * 100;
  };

  if (uploads.length === 0) {
    return (
      <Card sx={{ mt: 2 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Recent Uploads
          </Typography>
          <Typography variant="body2" color="text.secondary">
            No recent uploads found
          </Typography>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card sx={{ mt: 2 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Recent Uploads
        </Typography>
        
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>File Name</TableCell>
                <TableCell>Size</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Progress</TableCell>
                <TableCell>Uploaded</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {uploads.map((upload, index) => (
                <TableRow key={upload.jobId || index} hover>
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">
                      {upload.name}
                    </Typography>
                  </TableCell>
                  
                  <TableCell>
                    <Typography variant="body2">
                      {formatFileSize(upload.size)}
                    </Typography>
                  </TableCell>
                  
                  <TableCell>
                    <Chip
                      label={upload.status}
                      color={getStatusColor(upload.status)}
                      size="small"
                      variant="outlined"
                    />
                  </TableCell>
                  
                  <TableCell>
                    <Box sx={{ minWidth: 120 }}>
                      {upload.status === 'running' ? (
                        <>
                          <LinearProgress 
                            variant="determinate" 
                            value={getProgress(upload)} 
                            size="small"
                            sx={{ mb: 0.5 }}
                          />
                          <Typography variant="caption">
                            {upload.recordsProcessed?.toLocaleString() || 0} / {upload.totalRows?.toLocaleString() || 0}
                          </Typography>
                        </>
                      ) : upload.status === 'completed' ? (
                        <Typography variant="caption" color="success.main">
                          {upload.recordsProcessed?.toLocaleString() || 0} records
                        </Typography>
                      ) : upload.status === 'failed' ? (
                        <Typography variant="caption" color="error.main">
                          Failed
                        </Typography>
                      ) : (
                        <Typography variant="caption" color="text.secondary">
                          Queued
                        </Typography>
                      )}
                    </Box>
                  </TableCell>
                  
                  <TableCell>
                    <Typography variant="caption" color="text.secondary">
                      {formatDate(upload.submittedAt)}
                    </Typography>
                  </TableCell>
                  
                  <TableCell>
                    <IconButton
                      size="small"
                      onClick={() => navigate(`/jobs/${upload.jobId}`)}
                      disabled={!upload.jobId}
                    >
                      <VisibilityIcon fontSize="small" />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </CardContent>
    </Card>
  );
}

export default RecentUploads;