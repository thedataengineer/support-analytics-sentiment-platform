import React from 'react';
import { Card, CardContent, Typography, Box } from '@mui/material';

function CorrelationMatrix({ correlations = [], features = [] }) {
  const getColor = (value) => {
    const intensity = Math.abs(value);
    if (value > 0) return `rgba(76, 175, 80, ${intensity})`;
    return `rgba(244, 67, 54, ${intensity})`;
  };

  const cellSize = 60;
  const margin = { top: 80, right: 40, bottom: 40, left: 80 };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" component="h2" gutterBottom>
          Feature Correlation Matrix
        </Typography>
        <Box sx={{ overflowX: 'auto' }}>
          <svg 
            width={features.length * cellSize + margin.left + margin.right}
            height={features.length * cellSize + margin.top + margin.bottom}
          >
            {/* Y-axis labels */}
            {features.map((feature, i) => (
              <text
                key={`y-${feature}`}
                x={margin.left - 10}
                y={margin.top + i * cellSize + cellSize / 2}
                textAnchor="end"
                dominantBaseline="middle"
                fontSize="12"
                fill="#666"
              >
                {feature}
              </text>
            ))}
            
            {/* X-axis labels */}
            {features.map((feature, i) => (
              <text
                key={`x-${feature}`}
                x={margin.left + i * cellSize + cellSize / 2}
                y={margin.top - 10}
                textAnchor="middle"
                dominantBaseline="middle"
                fontSize="12"
                fill="#666"
                transform={`rotate(-45, ${margin.left + i * cellSize + cellSize / 2}, ${margin.top - 10})`}
              >
                {feature}
              </text>
            ))}
            
            {/* Correlation cells */}
            {features.map((yFeature, i) => 
              features.map((xFeature, j) => {
                const correlation = correlations.find(c => c.x === xFeature && c.y === yFeature);
                const value = correlation?.value || (i === j ? 1 : 0);
                
                return (
                  <g key={`${xFeature}-${yFeature}`}>
                    <rect
                      x={margin.left + j * cellSize}
                      y={margin.top + i * cellSize}
                      width={cellSize}
                      height={cellSize}
                      fill={getColor(value)}
                      stroke="#fff"
                      strokeWidth="1"
                    />
                    <text
                      x={margin.left + j * cellSize + cellSize / 2}
                      y={margin.top + i * cellSize + cellSize / 2}
                      textAnchor="middle"
                      dominantBaseline="middle"
                      fontSize="11"
                      fill="#fff"
                      fontWeight="bold"
                    >
                      {value.toFixed(2)}
                    </text>
                  </g>
                );
              })
            )}
          </svg>
        </Box>
        
        <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="caption">Correlation:</Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box sx={{ width: 16, height: 16, bgcolor: 'rgba(244, 67, 54, 0.8)' }} />
            <Typography variant="caption">Negative</Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box sx={{ width: 16, height: 16, bgcolor: 'rgba(76, 175, 80, 0.8)' }} />
            <Typography variant="caption">Positive</Typography>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}

export default CorrelationMatrix;