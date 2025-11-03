import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Box,
  useMediaQuery,
  useTheme,
  List,
  ListItem,
  ListItemText,
  Stack
} from '@mui/material';

function RecentTicketsTable({ tickets = [] }) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const getSentimentColor = (sentiment) => {
    switch (sentiment?.toLowerCase()) {
      case 'positive': return 'success';
      case 'negative': return 'error';
      case 'neutral': return 'warning';
      default: return 'default';
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority?.toLowerCase()) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" component="h2" gutterBottom>
          Recent Tickets
        </Typography>
        
        {isMobile ? (
          <List>
            {tickets.map((ticket) => (
              <ListItem key={ticket.ticket_id} divider>
                <ListItemText
                  primary={
                    <Stack direction="row" justifyContent="space-between" alignItems="center">
                      <Typography variant="subtitle2" fontWeight="medium">
                        {ticket.ticket_id}
                      </Typography>
                      <Chip
                        label={ticket.sentiment_label}
                        color={getSentimentColor(ticket.sentiment_label)}
                        size="small"
                      />
                    </Stack>
                  }
                  secondary={
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="body2" sx={{ mb: 1 }}>
                        {ticket.summary}
                      </Typography>
                      <Stack direction="row" spacing={1} flexWrap="wrap">
                        <Chip
                          label={ticket.priority || 'Unknown'}
                          color={getPriorityColor(ticket.priority)}
                          size="small"
                          variant="outlined"
                        />
                        <Typography variant="caption" color="text.secondary">
                          Score: {ticket.sentiment_score} • {formatDate(ticket.created_date)}
                        </Typography>
                      </Stack>
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        ) : (
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Ticket ID</TableCell>
                  <TableCell>Summary</TableCell>
                  <TableCell>Priority</TableCell>
                  <TableCell>Sentiment</TableCell>
                  <TableCell>Score</TableCell>
                  <TableCell>Created</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {tickets.map((ticket) => (
                  <TableRow key={ticket.ticket_id} hover>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        {ticket.ticket_id}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ maxWidth: 300 }}>
                        {ticket.summary}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={ticket.priority || 'Unknown'}
                        color={getPriorityColor(ticket.priority)}
                        size="small"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={ticket.sentiment_label}
                        color={getSentimentColor(ticket.sentiment_label)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {ticket.sentiment_score}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="textSecondary">
                        {formatDate(ticket.created_date)}
                      </Typography>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </CardContent>
    </Card>
  );
}

export default RecentTicketsTable;