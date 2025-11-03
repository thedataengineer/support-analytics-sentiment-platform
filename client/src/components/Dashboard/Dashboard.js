import React, { useState, useEffect, useCallback } from 'react';
import { Container, Grid, Card, CardContent, Typography, Box, Button, Stack, Drawer, IconButton } from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { PieChart, Pie, Cell, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { enqueueSnackbar } from 'notistack';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import LogoutIcon from '@mui/icons-material/Logout';
import MenuIcon from '@mui/icons-material/Menu';
import MetricCard from './MetricCard';
import RecentTicketsTable from './RecentTicketsTable';
import { useResponsive, responsiveStyles } from '../../theme/responsive';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

function Dashboard() {
  const [sentimentData, setSentimentData] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [recentTickets, setRecentTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [startDate, setStartDate] = useState(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000));
  const [endDate, setEndDate] = useState(new Date());
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const navigate = useNavigate();
  const { isMobile, getChartHeight } = useResponsive();

  const handleLogout = () => {
    localStorage.removeItem('token');
    enqueueSnackbar('Logged out successfully', { variant: 'info' });
    navigate('/login');
  };

  const fetchDashboardData = useCallback(async () => {
    setLoading(true);
    try {
      const apiUrl = process.env.REACT_APP_API_URL || '';
      
      // Fetch sentiment data
      const sentimentResponse = await fetch(
        `${apiUrl}/api/sentiment/overview?start_date=${startDate.toISOString().split('T')[0]}&end_date=${endDate.toISOString().split('T')[0]}`
      );
      if (sentimentResponse.ok) {
        const sentimentData = await sentimentResponse.json();
        setSentimentData({
          sentiment_distribution: sentimentData?.sentiment_distribution ?? {},
          sentiment_trend: Array.isArray(sentimentData?.sentiment_trend) ? sentimentData.sentiment_trend : []
        });
      }
      
      // Fetch metrics
      const metricsResponse = await fetch(`${apiUrl}/api/dashboard/metrics`);
      if (metricsResponse.ok) {
        const metricsData = await metricsResponse.json();
        setMetrics(metricsData);
      }
      
      // Fetch recent tickets
      const ticketsResponse = await fetch(`${apiUrl}/api/dashboard/recent-tickets?limit=10`);
      if (ticketsResponse.ok) {
        const ticketsData = await ticketsResponse.json();
        setRecentTickets(ticketsData);
      }
      
    } catch (error) {
      enqueueSnackbar('Failed to fetch dashboard data', { variant: 'error' });
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate]);

  useEffect(() => {
    fetchDashboardData();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, [fetchDashboardData]);

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
          <Typography variant={isMobile ? 'h5' : 'h4'} component="h1">
            {isMobile ? 'Dashboard' : 'Sentiment Analysis Dashboard'}
          </Typography>
          {isMobile ? (
            <IconButton onClick={() => setMobileMenuOpen(true)}>
              <MenuIcon />
            </IconButton>
          ) : (
            <Stack direction="row" spacing={2}>
              <Button component={RouterLink} to="/support-analytics" variant="contained" color="secondary" startIcon={<AnalyticsIcon />}>
                Support Analytics
              </Button>
              <Button component={RouterLink} to="/ticket-trajectory" variant="contained" startIcon={<AnalyticsIcon />}>
                Ticket Trajectory
              </Button>
              <Button component={RouterLink} to="/sentiment-analysis" variant="outlined" startIcon={<AnalyticsIcon />}>
                Deep Dive
              </Button>
              <Button onClick={handleLogout} variant="outlined" color="error" startIcon={<LogoutIcon />}>
                Logout
              </Button>
            </Stack>
          )}
        </Stack>

        <Drawer anchor="right" open={mobileMenuOpen} onClose={() => setMobileMenuOpen(false)}>
          <Box sx={{ width: 250, p: 2 }}>
            <Stack spacing={2}>
              <Button fullWidth component={RouterLink} to="/support-analytics" variant="outlined" startIcon={<AnalyticsIcon />} onClick={() => setMobileMenuOpen(false)}>
                Support Analytics
              </Button>
              <Button fullWidth component={RouterLink} to="/ticket-trajectory" variant="outlined" startIcon={<AnalyticsIcon />} onClick={() => setMobileMenuOpen(false)}>
                Ticket Trajectory
              </Button>
              <Button fullWidth component={RouterLink} to="/sentiment-analysis" variant="outlined" startIcon={<AnalyticsIcon />} onClick={() => setMobileMenuOpen(false)}>
                Deep Dive
              </Button>
              <Button fullWidth onClick={() => { handleLogout(); setMobileMenuOpen(false); }} variant="outlined" color="error" startIcon={<LogoutIcon />}>
                Logout
              </Button>
            </Stack>
          </Box>
        </Drawer>

        {/* Filters */}
        <Box sx={{ mb: 3, ...responsiveStyles.mobileStack }}>
          <DatePicker
            label="Start Date"
            value={startDate}
            onChange={setStartDate}
            slotProps={{ textField: { size: 'small', fullWidth: isMobile } }}
          />
          <DatePicker
            label="End Date"
            value={endDate}
            onChange={setEndDate}
            slotProps={{ textField: { size: 'small', fullWidth: isMobile } }}
          />
          <Button variant="contained" onClick={fetchDashboardData} fullWidth={isMobile}>
            Refresh
          </Button>
        </Box>

        {loading ? (
          <Typography>Loading...</Typography>
        ) : (
          <Grid container spacing={3}>
            {/* Metric Cards */}
            {metrics && (
              <>
                <Grid item xs={12} md={4}>
                  <MetricCard 
                    title="Total Tickets" 
                    value={metrics.total_tickets} 
                    trend={metrics.ticket_trend}
                  />
                </Grid>
                <Grid item xs={12} md={4}>
                  <MetricCard 
                    title="Avg Sentiment" 
                    value={metrics.avg_sentiment} 
                    format="decimal"
                    trend={metrics.sentiment_trend}
                  />
                </Grid>
                <Grid item xs={12} md={4}>
                  <MetricCard 
                    title="Processing Jobs" 
                    value={metrics.processing_jobs}
                  />
                </Grid>
              </>
            )}
            
            {/* Charts */}
            {sentimentData && hasData && (
              <>
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" component="h2" gutterBottom>
                        Sentiment Distribution
                      </Typography>
                      <ResponsiveContainer width="100%" height={getChartHeight()}>
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

                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" component="h2" gutterBottom>
                        Sentiment Trend Over Time
                      </Typography>
                      <ResponsiveContainer width="100%" height={getChartHeight()}>
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
              </>
            )}
            
            {/* Recent Tickets Table */}
            <Grid item xs={12}>
              <RecentTicketsTable tickets={recentTickets} />
            </Grid>
          </Grid>
        )}
      </Container>
    </LocalizationProvider>
  );
}

export default Dashboard;
