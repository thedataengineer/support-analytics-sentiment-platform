import React, { useState, useEffect, useCallback } from 'react';
import { Container, Grid, Card, CardContent, Typography, Box, Button, Stack } from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { PieChart, Pie, Cell, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { enqueueSnackbar } from 'notistack';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import LogoutIcon from '@mui/icons-material/Logout';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

function Dashboard() {
  const [sentimentData, setSentimentData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [startDate, setStartDate] = useState(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000));
  const [endDate, setEndDate] = useState(new Date());
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('token');
    enqueueSnackbar('Logged out successfully', { variant: 'info' });
    navigate('/login');
  };

  const fetchSentimentData = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `/api/sentiment/overview?start_date=${startDate.toISOString().split('T')[0]}&end_date=${endDate.toISOString().split('T')[0]}`
      );
      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }
      const data = await response.json();
      const normalizedData = {
        sentiment_distribution: data?.sentiment_distribution ?? {},
        sentiment_trend: Array.isArray(data?.sentiment_trend) ? data.sentiment_trend : []
      };
      setSentimentData(normalizedData);
    } catch (error) {
      enqueueSnackbar('Failed to fetch sentiment data', { variant: 'error' });
      setSentimentData(null);
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate]);

  useEffect(() => {
    fetchSentimentData();
  }, [fetchSentimentData]);

  const pieData = Object.entries(sentimentData?.sentiment_distribution ?? {}).map(([key, value]) => ({
    name: key.charAt(0).toUpperCase() + key.slice(1),
    value
  }));
  const trendData = sentimentData?.sentiment_trend ?? [];
  const hasData = pieData.length > 0 || trendData.length > 0;

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
          <Typography variant="h4" component="h1">
            Sentiment Analysis Dashboard
          </Typography>
          <Stack direction="row" spacing={2}>
            <Button
              component={RouterLink}
              to="/support-analytics"
              variant="contained"
              color="secondary"
              startIcon={<AnalyticsIcon />}
            >
              Support Analytics
            </Button>
            <Button
              component={RouterLink}
              to="/ticket-trajectory"
              variant="contained"
              startIcon={<AnalyticsIcon />}
            >
              Ticket Trajectory
            </Button>
            <Button
              component={RouterLink}
              to="/sentiment-analysis"
              variant="outlined"
              startIcon={<AnalyticsIcon />}
            >
              Deep Dive
            </Button>
            <Button
              onClick={handleLogout}
              variant="outlined"
              color="error"
              startIcon={<LogoutIcon />}
            >
              Logout
            </Button>
          </Stack>
        </Stack>

        {/* Filters */}
        <Box sx={{ mb: 3, display: 'flex', gap: 2, alignItems: 'center' }}>
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
          <Button variant="contained" onClick={fetchSentimentData}>
            Refresh
          </Button>
        </Box>

        {loading ? (
          <Typography>Loading...</Typography>
        ) : sentimentData && hasData ? (
          <Grid container spacing={3}>
            {/* Sentiment Distribution Pie Chart */}
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" component="h2" gutterBottom>
                    Sentiment Distribution
                  </Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={pieData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {pieData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>

            {/* Sentiment Trend Line Chart */}
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" component="h2" gutterBottom>
                    Sentiment Trend Over Time
                  </Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={trendData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Line type="monotone" dataKey="positive" stroke="#4CAF50" name="Positive" />
                      <Line type="monotone" dataKey="negative" stroke="#F44336" name="Negative" />
                      <Line type="monotone" dataKey="neutral" stroke="#FFC107" name="Neutral" />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        ) : (
          <Typography>No data available</Typography>
        )}
      </Container>
    </LocalizationProvider>
  );
}

export default Dashboard;
