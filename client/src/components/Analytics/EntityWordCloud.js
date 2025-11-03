import React from 'react';
import { Card, CardContent, Typography, Box, Chip } from '@mui/material';

function EntityWordCloud({ entities = [], onEntityClick }) {
  const getSentimentColor = (sentiment) => {
    if (sentiment > 0.5) return 'success';
    if (sentiment < -0.5) return 'error';
    return 'warning';
  };

  const getTypeColor = (type) => {
    const colors = {
      'PERSON': 'primary',
      'ORG': 'secondary', 
      'PRODUCT': 'info',
      'GPE': 'warning'
    };
    return colors[type] || 'default';
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" component="h2" gutterBottom>
          Entity Analysis
        </Typography>
        <Box sx={{ 
          display: 'flex', 
          flexWrap: 'wrap', 
          gap: 1,
          minHeight: 200,
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          {entities.map((entity, index) => (
            <Chip
              key={`${entity.text}-${index}`}
              label={`${entity.text} (${entity.frequency})`}
              color={getTypeColor(entity.type)}
              variant={entity.sentiment > 0 ? 'filled' : 'outlined'}
              size={entity.frequency > 10 ? 'medium' : 'small'}
              onClick={() => onEntityClick && onEntityClick(entity)}
              sx={{
                fontSize: `${Math.max(0.7, Math.min(1.2, entity.frequency / 10))}rem`,
                cursor: onEntityClick ? 'pointer' : 'default',
                '&:hover': onEntityClick ? {
                  transform: 'scale(1.1)',
                  transition: 'transform 0.2s'
                } : {}
              }}
            />
          ))}
        </Box>
        
        <Box sx={{ mt: 2, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <Typography variant="caption">Entity Types:</Typography>
          <Chip label="Person" color="primary" size="small" />
          <Chip label="Organization" color="secondary" size="small" />
          <Chip label="Product" color="info" size="small" />
          <Chip label="Location" color="warning" size="small" />
        </Box>
      </CardContent>
    </Card>
  );
}

export default EntityWordCloud;