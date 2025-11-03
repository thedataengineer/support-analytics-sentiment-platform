import React, { useState, useEffect } from 'react';
import { Card, CardContent, Typography, List, ListItem, ListItemText, Chip, Box, TextField, Button } from '@mui/material';
import { enqueueSnackbar } from 'notistack';

function EntitiesPanel() {
  const [entities, setEntities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchEntities();
  }, []);

  const fetchEntities = async () => {
    setLoading(true);
    try {
      // Mock data for MVP - in production, fetch from API
      const mockEntities = [
        { text: 'iPhone', label: 'PRODUCT', count: 150 },
        { text: 'Google', label: 'ORGANIZATION', count: 120 },
        { text: 'New York', label: 'LOCATION', count: 95 },
        { text: 'John Smith', label: 'PERSON', count: 80 },
        { text: 'Support Team', label: 'ORGANIZATION', count: 65 },
      ];
      setEntities(mockEntities);
    } catch (error) {
      enqueueSnackbar('Failed to fetch entities', { variant: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const filteredEntities = entities.filter(entity =>
    entity.text.toLowerCase().includes(searchQuery.toLowerCase()) ||
    entity.label.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getLabelColor = (label) => {
    const colors = {
      'PRODUCT': 'primary',
      'ORGANIZATION': 'secondary',
      'LOCATION': 'success',
      'PERSON': 'warning',
      'MISC': 'default'
    };
    return colors[label] || 'default';
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" component="h2" gutterBottom>
          Top Entities
        </Typography>

        <Box sx={{ mb: 2 }}>
          <TextField
            fullWidth
            size="small"
            label="Search entities"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </Box>

        {loading ? (
          <Typography>Loading entities...</Typography>
        ) : (
          <List>
            {filteredEntities.map((entity, index) => (
              <ListItem key={index} divider>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="body1">{entity.text}</Typography>
                      <Chip
                        label={entity.label}
                        color={getLabelColor(entity.label)}
                        size="small"
                      />
                    </Box>
                  }
                  secondary={`Mentions: ${entity.count}`}
                />
              </ListItem>
            ))}
          </List>
        )}

        {filteredEntities.length === 0 && !loading && (
          <Typography variant="body2" color="text.secondary">
            No entities found
          </Typography>
        )}
      </CardContent>
    </Card>
  );
}

export default EntitiesPanel;
