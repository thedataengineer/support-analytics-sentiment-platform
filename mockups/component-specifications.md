# Component Specifications

## Component Props & APIs

### MetricCard Component
```javascript
// components/Dashboard/MetricCard.js
<MetricCard
  title="Total Tickets"
  value={12847}
  trend={{ value: 5.2, period: "7d", direction: "up" }}
  icon="ticket"
  color="primary"
/>
```

### SentimentPieChart Component
```javascript
// components/Dashboard/SentimentPieChart.js
<SentimentPieChart
  data={[
    { name: "Positive", value: 45, color: "#4caf50" },
    { name: "Neutral", value: 35, color: "#ff9800" },
    { name: "Negative", value: 20, color: "#f44336" }
  ]}
  onSegmentClick={(segment) => filterBySentiment(segment)}
/>
```

### DragDropZone Component
```javascript
// components/Upload/DragDropZone.js
<DragDropZone
  acceptedTypes={[".csv", ".json"]}
  maxSize={500 * 1024 * 1024} // 500MB
  onFileDrop={(files) => handleFiles(files)}
  onError={(error) => showError(error)}
/>
```

### SentimentHeatmap Component
```javascript
// components/Analytics/SentimentHeatmap.js
<SentimentHeatmap
  data={heatmapData}
  xAxis="department"
  yAxis="week"
  colorScale="RdYlGn"
  onCellClick={(x, y, value) => drillDown(x, y)}
/>
```

## State Management Structure

### Dashboard State
```javascript
const dashboardState = {
  metrics: {
    totalTickets: 12847,
    avgSentiment: 0.72,
    processingJobs: 3
  },
  sentimentDistribution: [...],
  sentimentTrends: [...],
  recentTickets: [...],
  filters: {
    dateRange: "7d",
    department: "all",
    sentiment: "all"
  },
  loading: false,
  error: null
}
```

### Upload State
```javascript
const uploadState = {
  files: [],
  configuration: {
    textColumn: "description",
    idColumn: "ticket_id",
    dateColumn: "created_date",
    skipHeader: true,
    enableNER: true,
    backgroundProcess: false
  },
  uploadProgress: {
    current: 0,
    total: 0,
    status: "idle" // idle, uploading, processing, complete, error
  },
  recentUploads: [...]
}
```

## API Integration Points

### Dashboard APIs
- `GET /api/dashboard/metrics` - Metric cards data
- `GET /api/dashboard/sentiment-distribution` - Pie chart data
- `GET /api/dashboard/sentiment-trends` - Timeline data
- `GET /api/dashboard/recent-tickets` - Recent tickets table

### Upload APIs
- `POST /api/upload/file` - File upload endpoint
- `GET /api/upload/progress/{job_id}` - Upload progress
- `GET /api/upload/history` - Recent uploads
- `POST /api/upload/validate` - File validation

### Analytics APIs
- `POST /api/analytics/nlq` - Natural language query
- `GET /api/analytics/heatmap` - Sentiment heatmap data
- `GET /api/analytics/entities` - Entity analysis
- `GET /api/analytics/correlations` - Correlation matrix

## Responsive Breakpoints

```css
/* Mobile First Approach */
.component {
  /* Mobile: < 480px */
  width: 100%;
  padding: 8px;
}

@media (min-width: 480px) {
  /* Tablet: 480px - 768px */
  .component {
    width: 50%;
    padding: 12px;
  }
}

@media (min-width: 768px) {
  /* Desktop: > 768px */
  .component {
    width: 33.33%;
    padding: 16px;
  }
}
```

## Performance Considerations

### Lazy Loading
```javascript
// Lazy load heavy components
const SentimentHeatmap = lazy(() => import('./SentimentHeatmap'));
const EntityWordCloud = lazy(() => import('./EntityWordCloud'));
```

### Memoization
```javascript
// Memoize expensive calculations
const processedData = useMemo(() => {
  return processChartData(rawData);
}, [rawData]);
```

### Virtual Scrolling
```javascript
// For large ticket lists
<VirtualizedTable
  rowCount={tickets.length}
  rowHeight={60}
  rowRenderer={({ index, key, style }) => (
    <TicketRow key={key} style={style} ticket={tickets[index]} />
  )}
/>
```