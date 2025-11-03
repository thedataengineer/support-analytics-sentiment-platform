import React, { useState, useEffect, useCallback } from 'react';
import {
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  Tabs,
  Tab,
  Stack,
  Chip,
  TextField,
  InputAdornment,
  IconButton,
  CircularProgress,
  Paper,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import Plot from 'react-plotly.js';
import RefreshIcon from '@mui/icons-material/Refresh';
import SendIcon from '@mui/icons-material/Send';
import DashboardIcon from '@mui/icons-material/Dashboard';
import ChatIcon from '@mui/icons-material/Chat';
import LogoutIcon from '@mui/icons-material/Logout';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import { enqueueSnackbar } from 'notistack';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import SentimentHeatmap from '../../components/Analytics/SentimentHeatmap';
import EntityWordCloud from '../../components/Analytics/EntityWordCloud';
import CorrelationMatrix from '../../components/Analytics/CorrelationMatrix';
import AnomalyAlerts from '../../components/Analytics/AnomalyAlerts';

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

function SupportAnalytics() {
  const [tabValue, setTabValue] = useState(0);
  const [startDate, setStartDate] = useState(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000));
  const [endDate, setEndDate] = useState(new Date());
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // NLQ state
  const [nlqQuery, setNlqQuery] = useState('');
  const [nlqResponse, setNlqResponse] = useState(null);
  const [nlqLoading, setNlqLoading] = useState(false);

  // Advanced analytics state
  const [heatmapData, setHeatmapData] = useState([]);
  const [entityData, setEntityData] = useState([]);
  const [correlationData, setCorrelationData] = useState({ correlations: [], features: [] });
  const [anomalyData, setAnomalyData] = useState([]);

  const fetchAnalytics = useCallback(async () => {
    setLoading(true);
    try {
      const apiUrl = process.env.REACT_APP_API_URL || '';
      const params = new URLSearchParams({
        start_date: startDate.toISOString().split('T')[0],
        end_date: endDate.toISOString().split('T')[0],
      });

      // Fetch basic analytics
      const response = await fetch(`${apiUrl}/api/support/analytics?${params.toString()}`);
      if (!response.ok) throw new Error('Failed to fetch analytics');
      const data = await response.json();
      setAnalytics(data);

      // Fetch advanced analytics
      const [heatmapRes, entityRes, correlationRes, anomalyRes] = await Promise.all([
        fetch(`${apiUrl}/api/analytics/heatmap`),
        fetch(`${apiUrl}/api/analytics/entities`),
        fetch(`${apiUrl}/api/analytics/correlations`),
        fetch(`${apiUrl}/api/analytics/anomalies`)
      ]);

      if (heatmapRes.ok) {
        const heatmapData = await heatmapRes.json();
        setHeatmapData(heatmapData.data || []);
      }

      if (entityRes.ok) {
        const entityData = await entityRes.json();
        setEntityData(entityData.entities || []);
      }

      if (correlationRes.ok) {
        const correlationData = await correlationRes.json();
        setCorrelationData(correlationData);
      }

      if (anomalyRes.ok) {
        const anomalyData = await anomalyRes.json();
        setAnomalyData(anomalyData.anomalies || []);
      }

    } catch (error) {
      enqueueSnackbar('Failed to fetch analytics data', { variant: 'error' });
      setAnalytics(null);
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    enqueueSnackbar('Logged out successfully', { variant: 'info' });
    navigate('/login');
  };

  const handleNLQSubmit = async () => {
    if (!nlqQuery.trim()) return;

    setNlqLoading(true);
    try {
      const apiUrl = process.env.REACT_APP_API_URL || '';
      const response = await fetch(`${apiUrl}/api/support/nlq`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: nlqQuery,
          start_date: startDate.toISOString().split('T')[0],
          end_date: endDate.toISOString().split('T')[0],
        }),
      });

      if (!response.ok) throw new Error('Failed to process query');

      const data = await response.json();
      setNlqResponse(data);
    } catch (error) {
      enqueueSnackbar('Failed to process natural language query', { variant: 'error' });
    } finally {
      setNlqLoading(false);
    }
  };

  if (!analytics && loading) {
    return (
      <Container maxWidth="xl" sx={{ mt: 4, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <CircularProgress />
      </Container>
    );
  }

  const { summary, sentiment_distribution, sentiment_trend, field_type_distribution, ticket_statuses, tickets_by_comment_count, confidence_distribution, top_authors } = analytics || {};

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
          <Typography variant="h4" component="h1">
            Ticket Analytics Dashboard
          </Typography>
          <Stack direction="row" spacing={2}>
            <Button
              component={RouterLink}
              to="/upload"
              variant="outlined"
              startIcon={<AnalyticsIcon />}
            >
              Upload Data
            </Button>
            <Button
              component={RouterLink}
              to="/sentiment-analysis"
              variant="outlined"
              startIcon={<AnalyticsIcon />}
            >
              Sentiment Deep Dive
            </Button>
            <Button
              component={RouterLink}
              to="/ticket-trajectory"
              variant="outlined"
              startIcon={<AnalyticsIcon />}
            >
              Ticket Trajectory
            </Button>
            <Button
              component={RouterLink}
              to="/jobs"
              variant="outlined"
              startIcon={<AnalyticsIcon />}
            >
              Job Status
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

        {/* Date Filters */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Stack direction="row" spacing={2} alignItems="center">
              <DatePicker
                label="Start Date"
                value={startDate}
                onChange={setStartDate}
                slotProps={{ textField: { size: 'small' } }}
              />
              <DatePicker
                label="End Date"
                value={endDate}
                onChange={setEndDate}
                slotProps={{ textField: { size: 'small' } }}
              />
              <Button
                variant="contained"
                onClick={fetchAnalytics}
                startIcon={<RefreshIcon />}
              >
                Refresh
              </Button>
            </Stack>
          </CardContent>
        </Card>

        {/* Tabs for Dashboards vs NLQ */}
        <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
          <Tabs value={tabValue} onChange={handleTabChange}>
            <Tab icon={<DashboardIcon />} label="Pre-built Dashboards" iconPosition="start" />
            <Tab icon={<TrendingUpIcon />} label="Advanced Analytics" iconPosition="start" />
            <Tab icon={<ChatIcon />} label="Natural Language Query (NLQ)" iconPosition="start" />
          </Tabs>
        </Box>

        {/* Tab 1: Pre-built Dashboards */}
        <TabPanel value={tabValue} index={0}>
          {analytics && (
            <>
              {/* Summary Cards */}
              <Grid container spacing={3} sx={{ mb: 3 }}>
                <Grid item xs={12} md={4}>
                  <Card sx={{ bgcolor: '#e3f2fd' }}>
                    <CardContent>
                      <Typography variant="h6" color="primary">Total Tickets</Typography>
                      <Typography variant="h3">{summary?.total_tickets?.toLocaleString()}</Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Card sx={{ bgcolor: '#f3e5f5' }}>
                    <CardContent>
                      <Typography variant="h6" color="secondary">Total Comments</Typography>
                      <Typography variant="h3">{summary?.total_comments?.toLocaleString()}</Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Card sx={{ bgcolor: '#e8f5e9' }}>
                    <CardContent>
                      <Typography variant="h6" color="success.main">Avg Comments/Ticket</Typography>
                      <Typography variant="h3">{summary?.avg_comments_per_ticket?.toFixed(1)}</Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>

              {/* Charts Row 1 */}
              <Grid container spacing={3} sx={{ mb: 3 }}>
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>Sentiment Distribution</Typography>
                      <Plot
                        data={[{
                          values: [sentiment_distribution?.positive || 0, sentiment_distribution?.negative || 0, sentiment_distribution?.neutral || 0],
                          labels: ['Positive', 'Negative', 'Neutral'],
                          type: 'pie',
                          marker: {
                            colors: ['#4CAF50', '#F44336', '#FFC107']
                          },
                          textinfo: 'label+percent',
                          hoverinfo: 'label+value+percent'
                        }]}
                        layout={{
                          height: isMobile ? 250 : 350,
                          margin: { t: 20, b: 20, l: 20, r: 20 },
                          showlegend: true,
                          legend: { orientation: 'h', y: -0.1 }
                        }}
                        config={{ responsive: true, displayModeBar: true }}
                        style={{ width: '100%' }}
                      />
                    </CardContent>
                  </Card>
                </Grid>

                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>Confidence Distribution</Typography>
                      <Plot
                        data={[{
                          x: ['High (90%+)', 'Medium (70-90%)', 'Low (<70%)'],
                          y: [confidence_distribution?.high || 0, confidence_distribution?.medium || 0, confidence_distribution?.low || 0],
                          type: 'bar',
                          marker: {
                            color: ['#4CAF50', '#FFC107', '#F44336']
                          }
                        }]}
                        layout={{
                          height: 350,
                          margin: { t: 20, b: 60, l: 60, r: 20 },
                          yaxis: { title: 'Count' }
                        }}
                        config={{ responsive: true, displayModeBar: true }}
                        style={{ width: '100%' }}
                      />
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>

              {/* Charts Row 2 */}
              <Grid container spacing={3} sx={{ mb: 3 }}>
                <Grid item xs={12}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>Sentiment Trend Over Time</Typography>
                      <Plot
                        data={[
                          {
                            x: sentiment_trend?.map(d => d.date) || [],
                            y: sentiment_trend?.map(d => d.positive) || [],
                            name: 'Positive',
                            type: 'scatter',
                            mode: 'lines+markers',
                            line: { color: '#4CAF50', width: 2 },
                            marker: { size: 6 }
                          },
                          {
                            x: sentiment_trend?.map(d => d.date) || [],
                            y: sentiment_trend?.map(d => d.negative) || [],
                            name: 'Negative',
                            type: 'scatter',
                            mode: 'lines+markers',
                            line: { color: '#F44336', width: 2 },
                            marker: { size: 6 }
                          },
                          {
                            x: sentiment_trend?.map(d => d.date) || [],
                            y: sentiment_trend?.map(d => d.neutral) || [],
                            name: 'Neutral',
                            type: 'scatter',
                            mode: 'lines+markers',
                            line: { color: '#FFC107', width: 2 },
                            marker: { size: 6 }
                          }
                        ]}
                        layout={{
                          height: 400,
                          margin: { t: 20, b: 60, l: 60, r: 20 },
                          xaxis: { title: 'Date' },
                          yaxis: { title: 'Count' },
                          legend: { orientation: 'h', y: -0.2 },
                          hovermode: 'x unified'
                        }}
                        config={{ responsive: true, displayModeBar: true }}
                        style={{ width: '100%' }}
                      />
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>

              {/* Charts Row 3 */}
              <Grid container spacing={3} sx={{ mb: 3 }}>
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>Sentiment by Field Type</Typography>
                      <Plot
                        data={[
                          {
                            x: field_type_distribution?.map(d => d.field_type) || [],
                            y: field_type_distribution?.map(d => d.positive) || [],
                            name: 'Positive',
                            type: 'bar',
                            marker: { color: '#4CAF50' }
                          },
                          {
                            x: field_type_distribution?.map(d => d.field_type) || [],
                            y: field_type_distribution?.map(d => d.negative) || [],
                            name: 'Negative',
                            type: 'bar',
                            marker: { color: '#F44336' }
                          },
                          {
                            x: field_type_distribution?.map(d => d.field_type) || [],
                            y: field_type_distribution?.map(d => d.neutral) || [],
                            name: 'Neutral',
                            type: 'bar',
                            marker: { color: '#FFC107' }
                          }
                        ]}
                        layout={{
                          height: 350,
                          margin: { t: 20, b: 60, l: 60, r: 20 },
                          barmode: 'stack',
                          xaxis: { title: 'Field Type' },
                          yaxis: { title: 'Count' }
                        }}
                        config={{ responsive: true, displayModeBar: true }}
                        style={{ width: '100%' }}
                      />
                    </CardContent>
                  </Card>
                </Grid>

                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>Tickets by Comment Count</Typography>
                      <Plot
                        data={[{
                          x: Object.keys(tickets_by_comment_count || {}),
                          y: Object.values(tickets_by_comment_count || {}),
                          type: 'bar',
                          marker: {
                            color: ['#2196F3', '#03A9F4', '#00BCD4', '#009688', '#4CAF50']
                          }
                        }]}
                        layout={{
                          height: 350,
                          margin: { t: 20, b: 60, l: 60, r: 20 },
                          xaxis: { title: 'Comments Range' },
                          yaxis: { title: 'Ticket Count' }
                        }}
                        config={{ responsive: true, displayModeBar: true }}
                        style={{ width: '100%' }}
                      />
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>

              {/* Charts Row 4 */}
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>Ticket Status Distribution</Typography>
                      <Plot
                        data={[{
                          values: Object.values(ticket_statuses || {}),
                          labels: Object.keys(ticket_statuses || {}).map(k => k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())),
                          type: 'pie',
                          marker: {
                            colors: ['#4CAF50', '#F44336', '#81C784', '#E57373', '#FFD54F', '#9E9E9E']
                          },
                          textinfo: 'label+percent',
                          hoverinfo: 'label+value+percent'
                        }]}
                        layout={{
                          height: 350,
                          margin: { t: 20, b: 20, l: 20, r: 20 },
                          showlegend: true,
                          legend: { orientation: 'v', x: 1.1, y: 0.5 }
                        }}
                        config={{ responsive: true, displayModeBar: true }}
                        style={{ width: '100%' }}
                      />
                    </CardContent>
                  </Card>
                </Grid>

                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>Top 10 Most Active Authors</Typography>
                      <Plot
                        data={[{
                          y: top_authors?.map(a => a.author_id.substring(0, 20)) || [],
                          x: top_authors?.map(a => a.count) || [],
                          type: 'bar',
                          orientation: 'h',
                          marker: { color: '#2196F3' }
                        }]}
                        layout={{
                          height: 350,
                          margin: { t: 20, b: 40, l: 150, r: 20 },
                          xaxis: { title: 'Activity Count' },
                          yaxis: { automargin: true }
                        }}
                        config={{ responsive: true, displayModeBar: true }}
                        style={{ width: '100%' }}
                      />
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </>
          )}
        </TabPanel>

        {/* Tab 2: Advanced Analytics */}
        <TabPanel value={tabValue} index={1}>
          <Grid container spacing={3}>
            {/* Anomaly Alerts */}
            <Grid item xs={12}>
              <AnomalyAlerts 
                anomalies={anomalyData}
                onAlertClick={(alert) => {
                  enqueueSnackbar(`Investigating ${alert.type} on ${alert.date}`, { variant: 'info' });
                }}
              />
            </Grid>
            
            {/* Sentiment Heatmap */}
            <Grid item xs={12} lg={8}>
              <SentimentHeatmap 
                data={heatmapData}
                onCellClick={(x, y, data) => {
                  enqueueSnackbar(`Drilling down: ${x} - ${y}`, { variant: 'info' });
                }}
              />
            </Grid>
            
            {/* Entity Word Cloud */}
            <Grid item xs={12} lg={4}>
              <EntityWordCloud 
                entities={entityData}
                onEntityClick={(entity) => {
                  enqueueSnackbar(`Filtering by entity: ${entity.text}`, { variant: 'info' });
                }}
              />
            </Grid>
            
            {/* Correlation Matrix */}
            <Grid item xs={12}>
              <CorrelationMatrix 
                correlations={correlationData.correlations}
                features={correlationData.features}
              />
            </Grid>
          </Grid>
        </TabPanel>

        {/* Tab 3: Natural Language Query */}
        <TabPanel value={tabValue} index={2}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Ask Questions About Your Support Data
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Ask natural language questions like "What's the average sentiment trend?" or "Show me tickets with declining sentiment"
              </Typography>

              <Stack direction="row" spacing={2} sx={{ mb: 3 }}>
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  placeholder="Type your question here... (e.g., 'What percentage of tickets have negative sentiment?')"
                  value={nlqQuery}
                  onChange={(e) => setNlqQuery(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleNLQSubmit();
                    }
                  }}
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          onClick={handleNLQSubmit}
                          disabled={nlqLoading || !nlqQuery.trim()}
                          color="primary"
                        >
                          {nlqLoading ? <CircularProgress size={24} /> : <SendIcon />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                />
              </Stack>

              {nlqResponse && (
                <>
                  <Paper sx={{ p: 3, bgcolor: '#f5f5f5' }}>
                    <Typography variant="subtitle2" color="primary" gutterBottom>
                      AI Response:
                    </Typography>
                    <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                      {nlqResponse.answer}
                    </Typography>

                    {nlqResponse.chart_data && (
                      <Box sx={{ mt: 3 }}>
                        <Plot
                          data={nlqResponse.chart_data.data}
                          layout={nlqResponse.chart_data.layout}
                          config={{ responsive: true, displayModeBar: true }}
                          style={{ width: '100%' }}
                        />
                      </Box>
                    )}

                    {nlqResponse.sql_query && (
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="caption" color="text.secondary">
                          SQL Query: {nlqResponse.sql_query}
                        </Typography>
                      </Box>
                    )}
                  </Paper>

                  {/* RAG Metadata Display */}
                  {nlqResponse.rag_metadata && (
                    <Paper sx={{ p: 2, mt: 2, bgcolor: '#e3f2fd', border: '1px solid #2196F3' }}>
                      <Stack spacing={1}>
                        <Typography variant="subtitle2" color="primary">
                          📚 Context Sources {nlqResponse.rag_metadata.elasticsearch_enabled && '(Powered by Elasticsearch)'}
                        </Typography>
                        {nlqResponse.rag_metadata.retrieved_tickets > 0 ? (
                          <>
                            <Typography variant="body2" color="text.secondary">
                              Answer generated from {nlqResponse.rag_metadata.retrieved_tickets} relevant tickets in the knowledge base
                            </Typography>
                            {nlqResponse.rag_metadata.ticket_ids && nlqResponse.rag_metadata.ticket_ids.length > 0 && (
                              <Box>
                                <Typography variant="caption" color="text.secondary" gutterBottom>
                                  Referenced tickets:
                                </Typography>
                                <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ gap: 0.5, mt: 0.5 }}>
                                  {nlqResponse.rag_metadata.ticket_ids.map(id => (
                                    <Chip
                                      key={id}
                                      label={id}
                                      size="small"
                                      variant="outlined"
                                      color="primary"
                                    />
                                  ))}
                                </Stack>
                              </Box>
                            )}
                          </>
                        ) : (
                          <Typography variant="body2" color="text.secondary">
                            Answer based on aggregate statistics (no specific tickets retrieved)
                          </Typography>
                        )}
                      </Stack>
                    </Paper>
                  )}
                </>
              )}

              <Box sx={{ mt: 3 }}>
                <Typography variant="subtitle2" gutterBottom>Example Questions:</Typography>
                <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ gap: 1 }}>
                  <Chip label="What's the sentiment breakdown?" onClick={() => setNlqQuery("What's the sentiment breakdown?")} />
                  <Chip label="Show me the trend over time" onClick={() => setNlqQuery("Show me the trend over time")} />
                  <Chip label="Which field type has most negative sentiment?" onClick={() => setNlqQuery("Which field type has most negative sentiment?")} />
                  <Chip label="How many tickets are improving?" onClick={() => setNlqQuery("How many tickets are improving?")} />
                </Stack>
              </Box>
            </CardContent>
          </Card>
        </TabPanel>
      </Container>
    </LocalizationProvider>
  );
}

export default SupportAnalytics;
