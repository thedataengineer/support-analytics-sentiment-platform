import React from 'react';
import { Card, CardContent, Typography, Box } from '@mui/material';
import { ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, BarChart, Bar } from 'recharts';
import { useResponsive } from '../../theme/responsive';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];

function ResponsiveChart({ 
  type, 
  data = [], 
  title,
  config = {},
  height: customHeight 
}) {
  const { getChartHeight } = useResponsive();
  const height = customHeight || getChartHeight();

  const renderChart = () => {
    switch (type) {
      case 'pie':
        return (
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={config.showLabels ? ({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%` : false}
              outerRadius={Math.min(height / 3, 80)}
              fill="#8884d8"
              dataKey={config.dataKey || 'value'}
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        );

      case 'line':
        return (
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={config.xKey || 'x'} />
            <YAxis />
            <Tooltip />
            <Legend />
            {config.lines?.map((line, index) => (
              <Line
                key={line.key}
                type="monotone"
                dataKey={line.key}
                stroke={line.color || COLORS[index % COLORS.length]}
                name={line.name}
              />
            ))}
          </LineChart>
        );

      case 'bar':
        return (
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={config.xKey || 'x'} />
            <YAxis />
            <Tooltip />
            <Legend />
            {config.bars?.map((bar, index) => (
              <Bar
                key={bar.key}
                dataKey={bar.key}
                fill={bar.color || COLORS[index % COLORS.length]}
                name={bar.name}
              />
            ))}
          </BarChart>
        );

      default:
        return <Typography>Unsupported chart type: {type}</Typography>;
    }
  };

  return (
    <Card>
      <CardContent>
        {title && (
          <Typography variant="h6" component="h2" gutterBottom>
            {title}
          </Typography>
        )}
        <ResponsiveContainer width="100%" height={height}>
          {renderChart()}
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

export default ResponsiveChart;