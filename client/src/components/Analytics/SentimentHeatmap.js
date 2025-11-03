import React from 'react';
import { Card, CardContent, Typography, Box } from '@mui/material';

function SentimentHeatmap({ data = [], onCellClick }) {
  const xValues = [...new Set(data.map(d => d.x))].sort();
  const yValues = [...new Set(data.map(d => d.y))].sort();
  
  const matrix = {};
  data.forEach(d => {
    if (!matrix[d.y]) matrix[d.y] = {};
    matrix[d.y][d.x] = d;
  });

  const getColor = (value) => {
    if (!value) return '#f5f5f5';
    const intensity = Math.abs(value);
    if (value > 0.5) return `rgba(76, 175, 80, ${intensity})`;
    if (value < -0.5) return `rgba(244, 67, 54, ${intensity})`;
    return `rgba(255, 193, 7, ${intensity})`;
  };

  const cellSize = 40;
  const margin = { top: 60, right: 60, bottom: 60, left: 100 };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" component="h2" gutterBottom>
          Sentiment Heatmap
        </Typography>
        <Box sx={{ overflowX: 'auto' }}>
          <svg 
            width={xValues.length * cellSize + margin.left + margin.right}
            height={yValues.length * cellSize + margin.top + margin.bottom}
          >
            {yValues.map((y, i) => (
              <text
                key={y}
                x={margin.left - 10}
                y={margin.top + i * cellSize + cellSize / 2}
                textAnchor="end"
                dominantBaseline="middle"
                fontSize="12"
                fill="#666"
              >
                {y}
              </text>
            ))}
            
            {xValues.map((x, i) => (
              <text
                key={x}
                x={margin.left + i * cellSize + cellSize / 2}
                y={margin.top - 10}
                textAnchor="middle"
                dominantBaseline="middle"
                fontSize="12"
                fill="#666"
                transform={`rotate(-45, ${margin.left + i * cellSize + cellSize / 2}, ${margin.top - 10})`}
              >
                {x}
              </text>
            ))}
            
            {yValues.map((y, i) => 
              xValues.map((x, j) => {
                const cellData = matrix[y]?.[x];
                const value = cellData?.value || 0;
                
                return (
                  <g key={`${x}-${y}`}>
                    <rect
                      x={margin.left + j * cellSize}
                      y={margin.top + i * cellSize}
                      width={cellSize}
                      height={cellSize}
                      fill={getColor(value)}
                      stroke="#fff"
                      strokeWidth="1"
                      style={{ cursor: onCellClick ? 'pointer' : 'default' }}
                      onClick={() => onCellClick && onCellClick(x, y, cellData)}
                    />
                    {cellData && (
                      <text
                        x={margin.left + j * cellSize + cellSize / 2}
                        y={margin.top + i * cellSize + cellSize / 2}
                        textAnchor="middle"
                        dominantBaseline="middle"
                        fontSize="10"
                        fill="#333"
                        fontWeight="bold"
                      >
                        {value.toFixed(1)}
                      </text>
                    )}
                  </g>
                );
              })
            )}
          </svg>
        </Box>
      </CardContent>
    </Card>
  );
}

export default SentimentHeatmap;