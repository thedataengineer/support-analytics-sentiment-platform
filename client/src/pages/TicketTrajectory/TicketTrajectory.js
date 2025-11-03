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
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Stack,
  IconButton,
  Tooltip,
  TablePagination,
  LinearProgress,
  Divider,
  List,
  ListItem,
  ListItemText,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import SearchIcon from '@mui/icons-material/Search';
import RefreshIcon from '@mui/icons-material/Refresh';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import TrendingFlatIcon from '@mui/icons-material/TrendingFlat';
import CommentIcon from '@mui/icons-material/Comment';
import { enqueueSnackbar } from 'notistack';
import { Link as RouterLink } from 'react-router-dom';

function TicketTrajectory() {
  const [searchQuery, setSearchQuery] = useState('');
  const [sentimentFilter, setSentimentFilter] = useState('');
  const [startDate, setStartDate] = useState(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000));
  const [endDate, setEndDate] = useState(new Date());
  const [tickets, setTickets] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const fetchTickets = useCallback(async () => {
    setLoading(true);
    try {
      const apiUrl = process.env.REACT_APP_API_URL || '';
      const params = new URLSearchParams({
        limit: rowsPerPage,
        offset: page * rowsPerPage,
      });

      if (searchQuery) params.append('q', searchQuery);
      if (sentimentFilter) params.append('sentiment', sentimentFilter);
      if (startDate) params.append('start_date', startDate.toISOString().split('T')[0]);
      if (endDate) params.append('end_date', endDate.toISOString().split('T')[0]);

      const response = await fetch(`${apiUrl}/api/tickets?${params.toString()}`);
      if (!response.ok) throw new Error('Failed to fetch tickets');

      const data = await response.json();
      setTickets(data.results || []);
      setTotal(data.total || 0);
    } catch (error) {
      enqueueSnackbar('Failed to fetch ticket data', { variant: 'error' });
      setTickets([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [searchQuery, sentimentFilter, startDate, endDate, page, rowsPerPage]);

  useEffect(() => {
    fetchTickets();
  }, [fetchTickets]);

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleSearch = () => {
    setPage(0);
    fetchTickets();
  };

  const handleReset = () => {
    setSearchQuery('');
    setSentimentFilter('');
    setStartDate(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000));
    setEndDate(new Date());
    setPage(0);
  };

  const handleAccordionChange = (panel) => (event, isExpanded) => {
    setExpanded(isExpanded ? panel : false);
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

  const getStatusIcon = (status) => {
    if (status?.includes('improving')) return <TrendingUpIcon color="success" />;
    if (status?.includes('declining')) return <TrendingDownIcon color="error" />;
    return <TrendingFlatIcon color="action" />;
  };

  const getStatusColor = (status) => {
    if (status?.includes('improving')) return 'success';
    if (status?.includes('declining')) return 'error';
    if (status?.includes('stable_positive')) return 'success';
    if (status?.includes('stable_negative')) return 'error';
    if (status?.includes('stable_neutral')) return 'warning';
    return 'default';
  };

  const getStatusLabel = (status) => {
    if (!status) return 'Unknown';
    return status.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  };

  const getFieldTypeIcon = (fieldType) => {
    return <CommentIcon fontSize="small" />;
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
          <Typography variant="h4" component="h1">
            Ticket Sentiment Trajectory
          </Typography>
          <Button component={RouterLink} to="/support-analytics" variant="outlined">
            Back to Dashboard
          </Button>
        </Stack>

        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          View sentiment analysis by ticket showing the complete journey from initial comment to resolution
        </Typography>

        {/* Filters */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Grid container spacing={2}>
              <Grid item xs={12} md={3}>
                <TextField
                  fullWidth
                  label="Search Ticket ID or Text"
                  placeholder="Search..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                />
              </Grid>
              <Grid item xs={12} md={2}>
                <TextField
                  fullWidth
                  select
                  label="Final Sentiment"
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
              <Grid item xs={12} md={3}>
                <Stack direction="row" spacing={1} sx={{ height: '100%' }}>
                  <Button
                    variant="contained"
                    onClick={handleSearch}
                    fullWidth
                    startIcon={<SearchIcon />}
                    sx={{ height: '56px' }}
                  >
                    Search
                  </Button>
                  <Tooltip title="Reset Filters">
                    <IconButton onClick={handleReset} color="default" sx={{ height: '56px' }}>
                      <RefreshIcon />
                    </IconButton>
                  </Tooltip>
                </Stack>
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        {/* Results Summary */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="h6">
            {total.toLocaleString()} Tickets Found
          </Typography>
        </Box>

        {loading && <LinearProgress sx={{ mb: 2 }} />}

        {/* Ticket List */}
        {tickets.length === 0 && !loading ? (
          <Card>
            <CardContent>
              <Typography variant="body1" align="center" color="text.secondary">
                No tickets found. Try adjusting your filters.
              </Typography>
            </CardContent>
          </Card>
        ) : (
          <>
            {tickets.map((ticket, index) => (
              <Accordion
                key={ticket.ticket_id}
                expanded={expanded === ticket.ticket_id}
                onChange={handleAccordionChange(ticket.ticket_id)}
                sx={{ mb: 2 }}
              >
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', gap: 2 }}>
                    <Chip
                      label={ticket.ticket_id}
                      color="primary"
                      variant="outlined"
                      size="small"
                    />
                    <Box sx={{ flexGrow: 1 }}>
                      <Stack direction="row" spacing={1} alignItems="center">
                        <Typography variant="subtitle1">
                          {ticket.total_comments} Comment{ticket.total_comments !== 1 ? 's' : ''}
                        </Typography>
                        <Chip
                          icon={getStatusIcon(ticket.status)}
                          label={getStatusLabel(ticket.status)}
                          color={getStatusColor(ticket.status)}
                          size="small"
                        />
                      </Stack>
                    </Box>
                    <Stack direction="row" spacing={1}>
                      <Chip
                        label={`Final: ${ticket.final_sentiment}`}
                        color={getSentimentColor(ticket.final_sentiment)}
                        size="small"
                      />
                      <Chip
                        label={`+ ${ticket.sentiment_distribution.positive}`}
                        color="success"
                        size="small"
                        variant="outlined"
                      />
                      <Chip
                        label={`- ${ticket.sentiment_distribution.negative}`}
                        color="error"
                        size="small"
                        variant="outlined"
                      />
                      <Chip
                        label={`~ ${ticket.sentiment_distribution.neutral}`}
                        color="warning"
                        size="small"
                        variant="outlined"
                      />
                    </Stack>
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Box>
                    {/* Show Negative Entities First if any exist */}
                    {ticket.negative_entities && ticket.negative_entities.length > 0 && (
                      <Box sx={{ mb: 3, p: 2, bgcolor: '#ffebee', borderRadius: 1, border: '1px solid #ef5350' }}>
                        <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 2 }}>
                          <Typography variant="subtitle2" color="error.main" sx={{ fontWeight: 'bold' }}>
                            ⚠️ Negative Sentiments Detected ({ticket.negative_count})
                          </Typography>
                        </Stack>
                        <List dense>
                          {ticket.negative_entities.slice(0, 5).map((entity, idx) => (
                            <ListItem key={idx} sx={{ py: 0.5 }}>
                              <ListItemText
                                primary={
                                  <Stack direction="row" spacing={1} alignItems="center">
                                    <Chip label={entity.field_type} size="small" variant="outlined" color="error" />
                                    <Typography variant="caption" color="text.secondary">
                                      {entity.timestamp ? new Date(entity.timestamp).toLocaleDateString() : 'N/A'}
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary">
                                      ({(entity.confidence * 100).toFixed(0)}% confidence)
                                    </Typography>
                                  </Stack>
                                }
                                secondary={
                                  <Typography variant="body2" color="error.dark" sx={{ mt: 0.5 }}>
                                    "{entity.text_snippet}"
                                  </Typography>
                                }
                              />
                            </ListItem>
                          ))}
                          {ticket.negative_entities.length > 5 && (
                            <Typography variant="caption" color="text.secondary" sx={{ pl: 2, display: 'block', mt: 1 }}>
                              ... and {ticket.negative_entities.length - 5} more negative items
                            </Typography>
                          )}
                        </List>
                      </Box>
                    )}

                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      Complete Sentiment Timeline
                    </Typography>
                    <Divider sx={{ mb: 2 }} />

                    <List>
                      {ticket.comments?.map((comment, idx) => (
                        <ListItem
                          key={idx}
                          sx={{
                            flexDirection: 'column',
                            alignItems: 'flex-start',
                            border: '1px solid #e0e0e0',
                            borderRadius: 1,
                            mb: 1,
                            bgcolor: '#fafafa',
                          }}
                        >
                          <Stack direction="row" spacing={2} alignItems="center" sx={{ width: '100%', mb: 1 }}>
                            <Chip
                              icon={getFieldTypeIcon(comment.field_type)}
                              label={comment.field_type || 'Unknown'}
                              size="small"
                              variant="outlined"
                            />
                            <Chip
                              label={comment.sentiment}
                              color={getSentimentColor(comment.sentiment)}
                              size="small"
                            />
                            <Box sx={{ flexGrow: 1 }}>
                              <Typography variant="caption" color="text.secondary">
                                Confidence: {((comment.confidence || 0) * 100).toFixed(1)}%
                              </Typography>
                            </Box>
                            {comment.comment_timestamp && (
                              <Typography variant="caption" color="text.secondary">
                                {new Date(comment.comment_timestamp).toLocaleString()}
                              </Typography>
                            )}
                            {comment.author_id && (
                              <Chip label={comment.author_id} size="small" variant="outlined" />
                            )}
                          </Stack>
                          <Typography variant="body2" sx={{ pl: 1 }}>
                            {comment.text}
                          </Typography>
                        </ListItem>
                      ))}
                    </List>

                    <Divider sx={{ my: 2 }} />

                    <Stack direction="row" spacing={2} alignItems="center">
                      <Typography variant="subtitle2">Final Assessment:</Typography>
                      <Chip
                        label={`${ticket.final_sentiment} sentiment`}
                        color={getSentimentColor(ticket.final_sentiment)}
                      />
                      <Chip
                        icon={getStatusIcon(ticket.status)}
                        label={getStatusLabel(ticket.status)}
                        color={getStatusColor(ticket.status)}
                      />
                    </Stack>
                  </Box>
                </AccordionDetails>
              </Accordion>
            ))}

            <Card>
              <TablePagination
                component="div"
                count={total}
                page={page}
                onPageChange={handleChangePage}
                rowsPerPage={rowsPerPage}
                onRowsPerPageChange={handleChangeRowsPerPage}
                rowsPerPageOptions={[5, 10, 25, 50]}
              />
            </Card>
          </>
        )}
      </Container>
    </LocalizationProvider>
  );
}

export default TicketTrajectory;
