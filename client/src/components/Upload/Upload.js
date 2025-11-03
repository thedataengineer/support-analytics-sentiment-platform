import React, { useState, useCallback } from 'react';
import {
  Container,
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  LinearProgress,
  Stack,
  Tabs,
  Tab,
  TextField,
  Alert,
} from '@mui/material';
import { enqueueSnackbar } from 'notistack';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import DataObjectIcon from '@mui/icons-material/DataObject';
import { useNavigate, Link as RouterLink } from 'react-router-dom';
import DragDropZone from './DragDropZone';
import UploadConfiguration from './UploadConfiguration';
import ProgressTracker from './ProgressTracker';
import RecentUploads from './RecentUploads';

function Upload() {
  const [tabValue, setTabValue] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [jsonInput, setJsonInput] = useState('');
  const [jsonError, setJsonError] = useState('');
  const [currentJobId, setCurrentJobId] = useState(null);
  const [uploadConfig, setUploadConfig] = useState({
    idColumn: 'ticket_id',
    textColumn: 'description',
    dateColumn: 'created_date',
    enableSentiment: true,
    enableNER: false,
    backgroundProcessing: true,
    skipDuplicates: false
  });
  const [dragError, setDragError] = useState(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const navigate = useNavigate();

  const checkJobStatus = useCallback(async (jobId) => {
    const checkStatus = async () => {
      try {
        const apiUrl = process.env.REACT_APP_API_URL || '';
        const response = await fetch(`${apiUrl}/api/job/${jobId}`);
        const status = await response.json();

        setUploadedFiles(prev => prev.map(file => {
          if (file.jobId !== jobId) return file;
          const totalRows = status.total_rows ?? file.totalRows;
          const recordsProcessed = status.records_processed ?? file.recordsProcessed;
          return {
            ...file,
            status: status.status,
            totalRows,
            recordsProcessed,
            error: status.error ?? null,
            completedAt: status.completed_at ?? file.completedAt,
          };
        }));

        if (status.status === 'completed') {
          enqueueSnackbar('Processing completed!', { variant: 'success' });
        } else if (status.status === 'failed') {
          enqueueSnackbar('Processing failed', { variant: 'error' });
        } else {
          // Continue checking
          setTimeout(checkStatus, 2000);
        }
      } catch (error) {
        console.error('Status check failed:', error);
      }
    };

    checkStatus();
  }, []);

  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setDragError(null);
    setUploadSuccess(false);

    // Validate file type
    if (!file.name.endsWith('.csv')) {
      setDragError('Please upload a CSV file');
      return;
    }

    // Validate file size (500MB limit)
    if (file.size > 500 * 1024 * 1024) {
      setDragError('File size must be less than 500MB');
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    try {
      const apiUrl = process.env.REACT_APP_API_URL || '';
      const formData = new FormData();
      formData.append('file', file);
      
      // Add configuration
      formData.append('config', JSON.stringify(uploadConfig));

      const response = await fetch(`${apiUrl}/api/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      const result = await response.json();
      setCurrentJobId(result.job_id);
      setUploadSuccess(true);

      enqueueSnackbar('File uploaded successfully! Processing...', { variant: 'success' });
      
      setUploadedFiles(prev => [...prev, {
        name: file.name,
        size: file.size,
        jobId: result.job_id,
        status: 'queued',
        totalRows: result.file_info?.rows ?? null,
        recordsProcessed: 0,
        error: null,
        submittedAt: new Date().toISOString()
      }]);

      // Check job status periodically
      checkJobStatus(result.job_id);

    } catch (error) {
      setDragError('Upload failed: ' + error.message);
    } finally {
      setUploading(false);
      setUploadProgress(100);
    }
  }, [checkJobStatus, uploadConfig]);



  const handleJsonSubmit = async () => {
    setJsonError('');

    // Validate JSON
    let parsedData;
    try {
      parsedData = JSON.parse(jsonInput);
    } catch (error) {
      setJsonError('Invalid JSON format. Please check your input.');
      return;
    }

    // Validate structure
    if (!parsedData.records || !Array.isArray(parsedData.records)) {
      setJsonError('JSON must have a "records" array field');
      return;
    }

    if (parsedData.records.length === 0) {
      setJsonError('Records array cannot be empty');
      return;
    }

    if (parsedData.records.length > 1000) {
      setJsonError('Maximum 1000 records allowed per batch');
      return;
    }

    // Validate each record has required fields
    for (let i = 0; i < parsedData.records.length; i++) {
      const record = parsedData.records[i];
      if (!record.id) {
        setJsonError(`Record ${i + 1} is missing required "id" field`);
        return;
      }
      if (!record.summary && !record.description) {
        setJsonError(`Record ${i + 1} must have at least "summary" or "description" field`);
        return;
      }
    }

    setUploading(true);
    setUploadProgress(0);

    try {
      const apiUrl = process.env.REACT_APP_API_URL || '';
      const token = localStorage.getItem('token');
      const response = await fetch(`${apiUrl}/api/data-ingest`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(parsedData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Ingestion failed');
      }

      const result = await response.json();

      enqueueSnackbar(`Successfully queued ${parsedData.records.length} records for processing!`, {
        variant: 'success',
        action: () => (
          <Button
            color="inherit"
            size="small"
            onClick={() => navigate(`/jobs/${result.job_id}`)}
          >
            View status
          </Button>
        ),
      });

      setUploadedFiles(prev => [...prev, {
        name: `JSON Batch (${parsedData.records.length} records)`,
        size: new Blob([jsonInput]).size,
        jobId: result.job_id,
        status: 'queued',
        totalRows: parsedData.records.length,
        recordsProcessed: 0,
        error: null,
        submittedAt: new Date().toISOString()
      }]);

      // Check job status periodically
      checkJobStatus(result.job_id);

      // Clear input on success
      setJsonInput('');

    } catch (error) {
      enqueueSnackbar('Ingestion failed: ' + error.message, { variant: 'error' });
    } finally {
      setUploading(false);
      setUploadProgress(100);
    }
  };



  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
        <Typography variant="h4" component="h1">
          Upload Data
        </Typography>
        <Button component={RouterLink} to="/jobs" variant="outlined">
          View Jobs
        </Button>
      </Stack>

      {/* Tabs for CSV vs JSON */}
      <Card sx={{ mb: 3 }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
            <Tab icon={<CloudUploadIcon />} label="CSV Upload" iconPosition="start" />
            <Tab icon={<DataObjectIcon />} label="JSON Batch Ingest" iconPosition="start" />
          </Tabs>
        </Box>

        {/* CSV Upload Tab */}
        {tabValue === 0 && (
          <CardContent>
            <DragDropZone
              onFileDrop={onDrop}
              acceptedTypes={['.csv']}
              maxSize={500 * 1024 * 1024}
              disabled={uploading}
              error={dragError}
              success={uploadSuccess}
            />

            <UploadConfiguration
              config={uploadConfig}
              onChange={setUploadConfig}
              availableColumns={['ticket_id', 'summary', 'description', 'created_date', 'priority', 'status', 'department']}
            />

            {uploading && tabValue === 0 && (
              <Box sx={{ mt: 2 }}>
                <LinearProgress variant="determinate" value={uploadProgress} />
                <Typography variant="body2" sx={{ mt: 1 }}>
                  Uploading... {uploadProgress}%
                </Typography>
              </Box>
            )}

            {currentJobId && (
              <ProgressTracker
                jobId={currentJobId}
                onComplete={(status) => {
                  if (status.status === 'completed') {
                    enqueueSnackbar('Processing completed successfully!', { variant: 'success' });
                  } else if (status.status === 'failed') {
                    enqueueSnackbar('Processing failed', { variant: 'error' });
                  }
                  setCurrentJobId(null);
                }}
              />
            )}
          </CardContent>
        )}

        {/* JSON Batch Ingest Tab */}
        {tabValue === 1 && (
          <CardContent>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Submit a JSON payload with ticket records for batch processing.
              Requires analyst or admin role.
            </Typography>

            <TextField
              fullWidth
              multiline
              rows={15}
              placeholder={`{\n  "records": [\n    {\n      "id": "TICKET-001",\n      "summary": "Cannot login to dashboard",\n      "description": "User reports authentication error",\n      "comments": ["Checked logs", "Issue resolved"]\n    }\n  ]\n}`}
              value={jsonInput}
              onChange={(e) => setJsonInput(e.target.value)}
              sx={{ mt: 2, fontFamily: 'monospace', fontSize: '0.9rem' }}
              disabled={uploading}
            />

            {jsonError && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {jsonError}
              </Alert>
            )}

            <Box sx={{ mt: 2 }}>
              <Typography variant="caption" color="text.secondary">
                Format requirements:
              </Typography>
              <ul style={{ margin: '8px 0', paddingLeft: '20px', fontSize: '0.875rem' }}>
                <li>Must have a "records" array (1-1000 records)</li>
                <li>Each record needs an "id" field</li>
                <li>Each record must have "summary" or "description" (or both)</li>
                <li>Optional: "comments" array for comment texts</li>
              </ul>
            </Box>

            <Button
              variant="contained"
              onClick={handleJsonSubmit}
              disabled={uploading || !jsonInput.trim()}
              fullWidth
              sx={{ mt: 2 }}
            >
              {uploading ? 'Processing...' : 'Submit JSON Batch'}
            </Button>

            {uploading && tabValue === 1 && (
              <Box sx={{ mt: 2 }}>
                <LinearProgress />
                <Typography variant="body2" sx={{ mt: 1 }} align="center">
                  Processing batch...
                </Typography>
              </Box>
            )}
          </CardContent>
        )}
      </Card>

      <RecentUploads uploads={uploadedFiles} />
    </Container>
  );
}

export default Upload;
