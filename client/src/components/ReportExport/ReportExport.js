import React, { useState } from 'react';
import { Container, Card, CardContent, Typography, Box, Button } from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { enqueueSnackbar } from 'notistack';
import FileDownloadIcon from '@mui/icons-material/FileDownload';

function ReportExport() {
  const [startDate, setStartDate] = useState(new Date(Date.now() - 7 * 24 * 60 * 60 * 1000));
  const [endDate, setEndDate] = useState(new Date());
  const [generating, setGenerating] = useState(false);

  const handleDownloadReport = async () => {
    setGenerating(true);

    try {
      const startDateStr = startDate.toISOString().split('T')[0];
      const endDateStr = endDate.toISOString().split('T')[0];

      const response = await fetch(`/api/report/pdf?start_date=${startDateStr}&end_date=${endDateStr}`);

      if (!response.ok) {
        throw new Error('Failed to generate report');
      }

      // Create blob and download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `sentiment_report_${startDateStr}_to_${endDateStr}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      enqueueSnackbar('Report downloaded successfully!', { variant: 'success' });

    } catch (error) {
      enqueueSnackbar('Failed to generate report: ' + error.message, { variant: 'error' });
    } finally {
      setGenerating(false);
    }
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Export Sentiment Reports
        </Typography>

        <Card>
          <CardContent>
            <Typography variant="h6" component="h2" gutterBottom>
              Generate PDF Report
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Download a comprehensive PDF report of sentiment analysis results for the selected date range.
            </Typography>

            <Box sx={{ display: 'flex', gap: 2, mb: 3, alignItems: 'center' }}>
              <DatePicker
                label="Start Date"
                value={startDate}
                onChange={setStartDate}
                slotProps={{
                  textField: { size: 'small' }
                }}
              />
              <DatePicker
                label="End Date"
                value={endDate}
                onChange={setEndDate}
                slotProps={{
                  textField: { size: 'small' }
                }}
              />
            </Box>

            <Button
              variant="contained"
              startIcon={<FileDownloadIcon />}
              onClick={handleDownloadReport}
              disabled={generating}
              size="large"
            >
              {generating ? 'Generating Report...' : 'Download PDF Report'}
            </Button>
          </CardContent>
        </Card>
      </Container>
    </LocalizationProvider>
  );
}

export default ReportExport;
