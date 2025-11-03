import React from 'react';
import { Card, CardContent, Typography, Box, Chip } from '@mui/material';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';

function MetricCard({ title, value, trend, format = 'number' }) {
  const formatValue = (val) => {
    if (format === 'percentage') return `${val}%`;
    if (format === 'decimal') return val.toFixed(2);
    return val.toLocaleString();
  };

  const getTrendColor = (trendValue) => {
    if (trendValue > 0) return 'success';
    if (trendValue < 0) return 'error';
    return 'default';
  };

  const getTrendIcon = (trendValue) => {
    if (trendValue > 0) return <TrendingUpIcon fontSize="small" />;
    if (trendValue < 0) return <TrendingDownIcon fontSize="small" />;
    return null;
  };

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography color="textSecondary" gutterBottom variant="overline">
          {title}
        </Typography>
        <Typography variant="h4" component="div" sx={{ mb: 1 }}>
          {formatValue(value)}
        </Typography>
        {trend !== undefined && trend !== 0 && (
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Chip
              icon={getTrendIcon(trend)}
              label={`${trend > 0 ? '+' : ''}${trend}%`}
              color={getTrendColor(trend)}
              size="small"
              variant="outlined"
            />
          </Box>
        )}
      </CardContent>
    </Card>
  );
}

export default MetricCard;