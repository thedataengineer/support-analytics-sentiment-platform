import React from 'react';
import { Box, Typography, Paper } from '@mui/material';
import { useDropzone } from 'react-dropzone';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';

function DragDropZone({ 
  onFileDrop, 
  acceptedTypes = ['.csv'], 
  maxSize = 500 * 1024 * 1024,
  disabled = false,
  error = null,
  success = false
}) {
  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop: onFileDrop,
    accept: {
      'text/csv': acceptedTypes
    },
    multiple: false,
    disabled,
    maxSize
  });

  const getZoneColor = () => {
    if (error) return '#ffebee';
    if (success) return '#e8f5e9';
    if (isDragReject) return '#ffebee';
    if (isDragActive) return '#e3f2fd';
    return 'transparent';
  };

  const getBorderColor = () => {
    if (error) return '#f44336';
    if (success) return '#4caf50';
    if (isDragReject) return '#f44336';
    if (isDragActive) return '#2196f3';
    return '#ccc';
  };

  const getIcon = () => {
    if (error) return <ErrorIcon sx={{ fontSize: 48, color: 'error.main', mb: 2 }} />;
    if (success) return <CheckCircleIcon sx={{ fontSize: 48, color: 'success.main', mb: 2 }} />;
    return <CloudUploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />;
  };

  const getMessage = () => {
    if (error) return error;
    if (success) return 'File uploaded successfully!';
    if (isDragReject) return 'File type not supported';
    if (isDragActive) return 'Drop the file here';
    return 'Drag & drop a file here, or click to select';
  };

  return (
    <Paper
      {...getRootProps()}
      elevation={0}
      sx={{
        border: `2px dashed ${getBorderColor()}`,
        borderRadius: 2,
        p: 4,
        textAlign: 'center',
        cursor: disabled ? 'not-allowed' : 'pointer',
        bgcolor: getZoneColor(),
        transition: 'all 0.2s ease',
        '&:hover': !disabled ? {
          bgcolor: '#f5f5f5',
          borderColor: 'primary.main'
        } : {}
      }}
    >
      <input {...getInputProps()} />
      {getIcon()}
      <Typography variant="h6" gutterBottom>
        {getMessage()}
      </Typography>
      <Typography variant="body2" color="text.secondary">
        Supports {acceptedTypes.join(', ')} files up to {Math.round(maxSize / (1024 * 1024))}MB
      </Typography>
    </Paper>
  );
}

export default DragDropZone;