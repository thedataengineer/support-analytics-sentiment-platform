import React from 'react';
import { Card, CardContent, Typography, Box, Alert, Chip, Stack } from '@mui/material';
import WarningIcon from '@mui/icons-material/Warning';
import ErrorIcon from '@mui/icons-material/Error';
import InfoIcon from '@mui/icons-material/Info';

function AnomalyAlerts({ anomalies = [], onAlertClick }) {
  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'high': return <ErrorIcon />;
      case 'medium': return <WarningIcon />;
      default: return <InfoIcon />;
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      default: return 'info';
    }
  };

  const getTypeLabel = (type) => {
    switch (type) {
      case 'sentiment_spike': return 'Sentiment Spike';
      case 'sentiment_drop': return 'Sentiment Drop';
      default: return 'Anomaly';
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" component="h2" gutterBottom>
          Anomaly Detection
        </Typography>
        
        {anomalies.length === 0 ? (
          <Alert severity="success" icon={<InfoIcon />}>
            No anomalies detected in recent data
          </Alert>
        ) : (
          <Stack spacing={2}>
            {anomalies.map((anomaly, index) => (
              <Alert
                key={index}
                severity={getSeverityColor(anomaly.severity)}
                icon={getSeverityIcon(anomaly.severity)}
                action={
                  <Chip
                    label={`${anomaly.deviation} deviation`}
                    color={getSeverityColor(anomaly.severity)}
                    size="small"
                    variant="outlined"
                  />
                }
                onClick={() => onAlertClick && onAlertClick(anomaly)}
                sx={{ cursor: onAlertClick ? 'pointer' : 'default' }}
              >
                <Box>
                  <Typography variant="subtitle2" component="div">
                    {getTypeLabel(anomaly.type)} - {formatDate(anomaly.date)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Sentiment: {anomaly.value} (expected: {anomaly.expected})
                    • {anomaly.ticket_count} tickets
                  </Typography>
                </Box>
              </Alert>
            ))}
          </Stack>
        )}
        
        <Box sx={{ mt: 2 }}>
          <Typography variant="caption" color="text.secondary">
            Anomalies are detected when sentiment deviates significantly from recent trends
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
}

export default AnomalyAlerts;