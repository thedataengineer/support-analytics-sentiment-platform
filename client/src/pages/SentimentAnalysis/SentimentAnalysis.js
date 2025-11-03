import React, { useState, useEffect, useCallback } from 'react';
import {
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  TextField,
  MenuItem,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Paper,
  Chip,
  Stack,
  IconButton,
  Tooltip,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import SearchIcon from '@mui/icons-material/Search';
import FilterListIcon from '@mui/icons-material/FilterList';
import RefreshIcon from '@mui/icons-material/Refresh';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer } from 'recharts';
import { enqueueSnackbar } from 'notistack';
import { Link as RouterLink } from 'react-router-dom';

function SentimentAnalysis() {
  const [searchQuery, setSearchQuery] = useState('');
  const [sentimentFilter, setSentimentFilter] = useState('');
  const [startDate, setStartDate] = useState(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000));
  const [endDate, setEndDate] = useState(new Date());
  const [results, setResults] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);

  const fetchResults = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        limit: rowsPerPage,
        offset: page * rowsPerPage,
      });

      if (searchQuery) params.append('q', searchQuery);
      if (sentimentFilter) params.append('sentiment', sentimentFilter);
      if (startDate) params.append('start_date', startDate.toISOString().split('T')[0]);
      if (endDate) params.append('end_date', endDate.toISOString().split('T')[0]);

      const response = await fetch(`/api/search?${params.toString()}`);
      if (!response.ok) throw new Error('Failed to fetch results');

      const data = await response.json();
      setResults(data.results || []);
      setTotal(data.total || 0);
    } catch (error) {
      enqueueSnackbar('Failed to fetch sentiment data', { variant: 'error' });
      setResults([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [searchQuery, sentimentFilter, startDate, endDate, page, rowsPerPage]);

  const fetchStats = useCallback(async () => {
    try {
      const response = await fetch(
        `/api/sentiment/overview?start_date=${startDate.toISOString().split('T')[0]}&end_date=${endDate.toISOString().split('T')[0]}`
      );
      if (!response.ok) throw new Error('Failed to fetch stats');

      const data = await response.json();
      setStats(data.sentiment_distribution || {});
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  }, [startDate, endDate]);

  useEffect(() => {
    fetchResults();
    fetchStats();
  }, [fetchResults, fetchStats]);

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleSearch = () => {
    setPage(0);
    fetchResults();
  };

  const handleReset = () => {
    setSearchQuery('');
    setSentimentFilter('');
    setStartDate(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000));
    setEndDate(new Date());
    setPage(0);
  };

  const getSentimentColor = (sentiment) => {
    switch (sentiment?.toLowerCase()) {
      case 'positive':
        return 'success';
      case 'negative':
        return 'error';
      case 'neutral':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.9) return '#4CAF50';
    if (confidence >= 0.7) return '#FFC107';
    return '#FF9800';
  };

  const statsData = stats
    ? [
        { name: 'Positive', count: stats.positive || 0, color: '#4CAF50' },
        { name: 'Negative', count: stats.negative || 0, color: '#F44336' },
        { name: 'Neutral', count: stats.neutral || 0, color: '#FFC107' },
      ]
    : [];

  const totalCount = statsData.reduce((sum, item) => sum + item.count, 0);

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
          <Typography variant="h4" component="h1">
            Sentiment Analysis Deep Dive
          </Typography>
          <Button component={RouterLink} to="/" variant="outlined">
            Back to Dashboard
          </Button>
        </Stack>

        {/* Statistics Overview */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Sentiment Distribution
                </Typography>
                {totalCount > 0 ? (
                  <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={statsData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <RechartsTooltip />
                      <Bar dataKey="count" fill="#8884d8">
                        {statsData.map((entry, index) => (
                          <Bar key={`bar-${index}`} dataKey="count" fill={entry.color} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No data available for the selected period
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={4}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Summary
                </Typography>
                <Stack spacing={2}>
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Total Records
                    </Typography>
                    <Typography variant="h4">{totalCount.toLocaleString()}</Typography>
                  </Box>
                  {statsData.map((item) => (
                    <Box key={item.name}>
                      <Typography variant="body2" color="text.secondary">
                        {item.name}
                      </Typography>
                      <Stack direction="row" spacing={2} alignItems="center">
                        <Typography variant="h6">{item.count.toLocaleString()}</Typography>
                        <Typography variant="body2" color="text.secondary">
                          ({totalCount > 0 ? ((item.count / totalCount) * 100).toFixed(1) : 0}%)
                        </Typography>
                      </Stack>
                    </Box>
                  ))}
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Filters */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
              <FilterListIcon sx={{ mr: 1 }} />
              Filters
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Search"
                  placeholder="Search text or ticket ID..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  InputProps={{
                    endAdornment: (
                      <IconButton onClick={handleSearch} size="small">
                        <SearchIcon />
                      </IconButton>
                    ),
                  }}
                />
              </Grid>
              <Grid item xs={12} md={2}>
                <TextField
                  fullWidth
                  select
                  label="Sentiment"
                  value={sentimentFilter}
                  onChange={(e) => setSentimentFilter(e.target.value)}
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="positive">Positive</MenuItem>
                  <MenuItem value="negative">Negative</MenuItem>
                  <MenuItem value="neutral">Neutral</MenuItem>
                </TextField>
              </Grid>
              <Grid item xs={12} md={2}>
                <DatePicker
                  label="Start Date"
                  value={startDate}
                  onChange={setStartDate}
                  slotProps={{ textField: { fullWidth: true } }}
                />
              </Grid>
              <Grid item xs={12} md={2}>
                <DatePicker
                  label="End Date"
                  value={endDate}
                  onChange={setEndDate}
                  slotProps={{ textField: { fullWidth: true } }}
                />
              </Grid>
              <Grid item xs={12} md={2}>
                <Stack direction="row" spacing={1}>
                  <Button variant="contained" onClick={handleSearch} fullWidth startIcon={<SearchIcon />}>
                    Search
                  </Button>
                  <Tooltip title="Reset Filters">
                    <IconButton onClick={handleReset} color="default">
                      <RefreshIcon />
                    </IconButton>
                  </Tooltip>
                </Stack>
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        {/* Results Table */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Results ({total.toLocaleString()})
            </Typography>
            <TableContainer component={Paper} sx={{ maxHeight: 600 }}>
              <Table stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell>Ticket ID</TableCell>
                    <TableCell>Text</TableCell>
                    <TableCell>Sentiment</TableCell>
                    <TableCell>Confidence</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Date</TableCell>
                    <TableCell>Author</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {loading ? (
                    <TableRow>
                      <TableCell colSpan={7} align="center">
                        Loading...
                      </TableCell>
                    </TableRow>
                  ) : results.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} align="center">
                        No results found
                      </TableCell>
                    </TableRow>
                  ) : (
                    results.map((row, index) => (
                      <TableRow key={`${row.id}-${index}`} hover>
                        <TableCell>
                          <Chip label={row.id} size="small" variant="outlined" />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ maxWidth: 400, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                            {row.text}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip label={row.sentiment} color={getSentimentColor(row.sentiment)} size="small" />
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Box
                              sx={{
                                width: 60,
                                height: 8,
                                bgcolor: '#e0e0e0',
                                borderRadius: 1,
                                overflow: 'hidden',
                              }}
                            >
                              <Box
                                sx={{
                                  width: `${(row.confidence || 0) * 100}%`,
                                  height: '100%',
                                  bgcolor: getConfidenceColor(row.confidence),
                                  transition: 'width 0.3s',
                                }}
                              />
                            </Box>
                            <Typography variant="caption">{((row.confidence || 0) * 100).toFixed(0)}%</Typography>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Chip label={row.field_type || 'N/A'} size="small" variant="outlined" />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {row.comment_timestamp ? new Date(row.comment_timestamp).toLocaleDateString() : 'N/A'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">{row.author_id || 'Unknown'}</Typography>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </TableContainer>
            <TablePagination
              component="div"
              count={total}
              page={page}
              onPageChange={handleChangePage}
              rowsPerPage={rowsPerPage}
              onRowsPerPageChange={handleChangeRowsPerPage}
              rowsPerPageOptions={[10, 25, 50, 100]}
            />
          </CardContent>
        </Card>
      </Container>
    </LocalizationProvider>
  );
}

export default SentimentAnalysis;
