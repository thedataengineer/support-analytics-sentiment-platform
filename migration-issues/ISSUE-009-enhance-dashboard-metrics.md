# ISSUE-009: Enhance Dashboard Metrics

## Problem
Current dashboard lacks key metrics shown in mockups. Missing metric cards, recent tickets table, and advanced visualizations.

## Current vs Mockup Gaps

### Missing Components
1. **Metric Cards**: Total tickets, avg sentiment, processing jobs
2. **Recent Tickets Table**: Live ticket feed with sentiment scores
3. **Enhanced Filters**: Department, priority, status filters
4. **Auto-refresh**: Real-time data updates
5. **Drill-down**: Click charts to filter data

### Current Implementation
```javascript
// Only has basic pie chart and line chart
<Grid container spacing={3}>
  <Grid item xs={12} md={6}>
    <SentimentPieChart />
  </Grid>
  <Grid item xs={12} md={6}>
    <SentimentTrendChart />
  </Grid>
</Grid>
```

### Target Implementation
```javascript
// Metric cards + charts + recent tickets
<Grid container spacing={3}>
  <Grid item xs={12} md={4}>
    <MetricCard title="Total Tickets" value={12847} trend={5.2} />
  </Grid>
  <Grid item xs={12} md={4}>
    <MetricCard title="Avg Sentiment" value={0.72} trend={0.05} />
  </Grid>
  <Grid item xs={12} md={4}>
    <MetricCard title="Processing Jobs" value={3} />
  </Grid>
  <Grid item xs={12}>
    <RecentTicketsTable />
  </Grid>
</Grid>
```

## Files to Create/Modify
- `client/src/components/Dashboard/MetricCard.js` - NEW
- `client/src/components/Dashboard/RecentTicketsTable.js` - NEW
- `client/src/components/Dashboard/Dashboard.js` - MODIFY
- `backend/api/dashboard_api.py` - NEW

## API Endpoints Needed
- `GET /api/dashboard/metrics` - Summary metrics
- `GET /api/dashboard/recent-tickets` - Recent tickets with sentiment

## Success Criteria
- Dashboard matches mockup layout
- Real-time metrics display
- Recent tickets table functional
- Auto-refresh every 30s