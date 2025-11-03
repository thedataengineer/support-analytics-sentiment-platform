import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  Grid,
  Divider,
  Box
} from '@mui/material';

function UploadConfiguration({ 
  config, 
  onChange, 
  availableColumns = [] 
}) {
  const handleChange = (field, value) => {
    onChange({ ...config, [field]: value });
  };

  return (
    <Card sx={{ mt: 2 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Upload Configuration
        </Typography>
        
        <Grid container spacing={3}>
          {/* Column Mapping */}
          <Grid item xs={12}>
            <Typography variant="subtitle2" gutterBottom>
              Column Mapping
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={4}>
                <FormControl fullWidth size="small">
                  <InputLabel>ID Column</InputLabel>
                  <Select
                    value={config.idColumn || ''}
                    onChange={(e) => handleChange('idColumn', e.target.value)}
                    label="ID Column"
                  >
                    {availableColumns.map(col => (
                      <MenuItem key={col} value={col}>{col}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12} md={4}>
                <FormControl fullWidth size="small">
                  <InputLabel>Text Column</InputLabel>
                  <Select
                    value={config.textColumn || ''}
                    onChange={(e) => handleChange('textColumn', e.target.value)}
                    label="Text Column"
                  >
                    {availableColumns.map(col => (
                      <MenuItem key={col} value={col}>{col}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12} md={4}>
                <FormControl fullWidth size="small">
                  <InputLabel>Date Column</InputLabel>
                  <Select
                    value={config.dateColumn || ''}
                    onChange={(e) => handleChange('dateColumn', e.target.value)}
                    label="Date Column"
                  >
                    <MenuItem value="">None</MenuItem>
                    {availableColumns.map(col => (
                      <MenuItem key={col} value={col}>{col}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </Grid>

          <Grid item xs={12}>
            <Divider />
          </Grid>

          {/* Processing Options */}
          <Grid item xs={12}>
            <Typography variant="subtitle2" gutterBottom>
              Processing Options
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={config.enableSentiment || true}
                    onChange={(e) => handleChange('enableSentiment', e.target.checked)}
                  />
                }
                label="Enable Sentiment Analysis"
              />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={config.enableNER || false}
                    onChange={(e) => handleChange('enableNER', e.target.checked)}
                  />
                }
                label="Enable Named Entity Recognition"
              />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={config.backgroundProcessing || true}
                    onChange={(e) => handleChange('backgroundProcessing', e.target.checked)}
                  />
                }
                label="Background Processing"
              />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={config.skipDuplicates || false}
                    onChange={(e) => handleChange('skipDuplicates', e.target.checked)}
                  />
                }
                label="Skip Duplicate Records"
              />
            </Box>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
}

export default UploadConfiguration;