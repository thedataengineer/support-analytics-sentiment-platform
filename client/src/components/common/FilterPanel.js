import React from 'react';
import {
  Card,
  CardContent,
  Stack,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Button,
  Box
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import RefreshIcon from '@mui/icons-material/Refresh';

function FilterPanel({ 
  filters = [], 
  values = {}, 
  onChange, 
  onRefresh,
  orientation = 'horizontal' 
}) {
  const handleFilterChange = (filterKey, value) => {
    onChange && onChange({ ...values, [filterKey]: value });
  };

  const renderFilter = (filter) => {
    const value = values[filter.key] || filter.defaultValue || '';

    switch (filter.type) {
      case 'select':
        return (
          <FormControl key={filter.key} size="small" sx={{ minWidth: 120 }}>
            <InputLabel>{filter.label}</InputLabel>
            <Select
              value={value}
              onChange={(e) => handleFilterChange(filter.key, e.target.value)}
              label={filter.label}
            >
              {filter.options?.map(option => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        );

      case 'text':
        return (
          <TextField
            key={filter.key}
            label={filter.label}
            value={value}
            onChange={(e) => handleFilterChange(filter.key, e.target.value)}
            size="small"
            placeholder={filter.placeholder}
          />
        );

      case 'date':
        return (
          <DatePicker
            key={filter.key}
            label={filter.label}
            value={value}
            onChange={(newValue) => handleFilterChange(filter.key, newValue)}
            slotProps={{ textField: { size: 'small' } }}
          />
        );

      case 'dateRange':
        return (
          <Stack key={filter.key} direction="row" spacing={1}>
            <DatePicker
              label="Start Date"
              value={value?.start}
              onChange={(newValue) => handleFilterChange(filter.key, { ...value, start: newValue })}
              slotProps={{ textField: { size: 'small' } }}
            />
            <DatePicker
              label="End Date"
              value={value?.end}
              onChange={(newValue) => handleFilterChange(filter.key, { ...value, end: newValue })}
              slotProps={{ textField: { size: 'small' } }}
            />
          </Stack>
        );

      default:
        return null;
    }
  };

  return (
    <Card>
      <CardContent>
        <Stack 
          direction={orientation === 'horizontal' ? 'row' : 'column'}
          spacing={2}
          alignItems={orientation === 'horizontal' ? 'center' : 'stretch'}
          flexWrap="wrap"
        >
          {filters.map(renderFilter)}
          
          {onRefresh && (
            <Button
              variant="contained"
              onClick={onRefresh}
              startIcon={<RefreshIcon />}
              size="small"
            >
              Refresh
            </Button>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
}

export default FilterPanel;