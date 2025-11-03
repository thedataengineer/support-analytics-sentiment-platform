# Local Deployment Test Plan

## ✅ **Services Status Check**

Run this first to verify all services:

```bash
# Check infrastructure
docker-compose ps

# Test each service
curl http://localhost:9200/_cluster/health  # Elasticsearch
curl http://localhost:8000/health           # Backend API
curl http://localhost:5001/health           # ML Service
redis-cli ping                              # Redis
curl http://localhost:3000                  # Frontend (should return HTML)
```

**Expected Status:**
- ✅ **Elasticsearch**: Green cluster health
- ✅ **PostgreSQL**: Running on port 5432
- ✅ **Redis**: PONG response
- ✅ **Backend API**: `{"status":"healthy"}`
- ✅ **ML Service**: `{"status":"healthy"}`
- ✅ **Frontend**: React app on http://localhost:3000

---

## 🧪 **End-to-End Test Scenarios**

### **Test 1: Authentication Flow**

1. **Open Browser:** http://localhost:3000
   - Should redirect to `/login`

2. **Login:**
   - Email: `admin@example.com`
   - Password: `password`
   - Click "Sign In"
   - ✅ Should see success notification
   - ✅ Should redirect to Dashboard

3. **Check Token:**
   - Open DevTools → Application → Local Storage
   - ✅ Should see `token` with JWT value

4. **Test Logout:**
   - Click red "Logout" button in top-right
   - ✅ Should see "Logged out successfully" notification
   - ✅ Should redirect to `/login`
   - ✅ Token should be removed from localStorage

---

### **Test 2: CSV Upload with Async Processing**

**Create Test CSV:**
```bash
cat > /tmp/test_tickets.csv << 'EOF'
Key,Summary,Description,Comments
TICKET-001,Login issue,User cannot access dashboard,"Checked logs, Issue resolved"
TICKET-002,Performance slow,Dashboard loading takes too long,"Optimized queries"
TICKET-003,Feature request,Need dark mode support,"Added to roadmap, Will implement"
EOF
```

**Test Upload:**
1. Login again (admin@example.com / password)
2. Click "Upload" in navigation or go to http://localhost:3000/upload
3. **CSV Upload Tab:**
   - Drag & drop `/tmp/test_tickets.csv` OR click to browse
   - ✅ Should see file validation
   - ✅ Should show "File uploaded successfully! Processing..."
   - ✅ Should display job_id
   - ✅ Should appear in "Upload History" section
   - ✅ Watch status change: queued → running → completed

4. **Check Job Status:**
   - Click "View" button next to uploaded file
   - ✅ Should show progress: X/3 rows processed
   - ✅ Should show sentiment_records and entity_records counts
   - ✅ Wait for status: "completed"

**Verify Backend Processing:**
```bash
# Check job status via API
curl http://localhost:8000/api/job/YOUR_JOB_ID | python3 -m json.tool

# Expected response:
{
  "job_id": "...",
  "status": "completed",
  "records_processed": 3,
  "sentiment_records": 6-9,
  "entity_records": 5-10,
  "total_rows": 3
}
```

---

### **Test 3: Search with Elasticsearch**

1. Go to http://localhost:3000/sentiment-analysis

2. **Wait for data to appear** (may take 10-20 seconds for Elasticsearch indexing)

3. **Test Search:**
   - Search box: Type "login"
   - ✅ Should find TICKET-001
   - ✅ Results should show sentiment chip (positive/negative/neutral)
   - ✅ Confidence bar should be displayed

4. **Test Filters:**
   - Select "Negative" sentiment filter
   - ✅ Should filter results
   - Try date range filters
   - ✅ Should update results

5. **Check Elasticsearch is Being Used:**
   - Look for badge or check browser Network tab
   - API call to `/api/search` should return `"source": "elasticsearch"`

**Verify Elasticsearch Index:**
```bash
# Check if tickets are indexed
curl http://localhost:9200/tickets/_search?size=1 | python3 -m json.tool

# Should show indexed tickets with sentiment and entities
```

---

### **Test 4: JSON Batch Ingest**

1. Go to http://localhost:3000/upload

2. **Click "JSON Batch Ingest" tab**

3. **Paste Test JSON:**
```json
{
  "records": [
    {
      "id": "API-001",
      "summary": "API rate limit exceeded",
      "description": "Customer hitting 429 errors on /api/users endpoint",
      "comments": ["Increased rate limit", "Monitoring traffic"]
    },
    {
      "id": "API-002",
      "summary": "Database timeout",
      "description": "Query taking more than 30 seconds to execute"
    }
  ]
}
```

4. **Click "Submit JSON Batch"**
   - ✅ Should validate JSON format
   - ✅ Should check for required fields
   - ✅ If you're logged in as admin, should succeed
   - ✅ If not logged in or wrong role, should show 403 error
   - ✅ Should show job_id notification
   - ✅ Should add to upload history

5. **Verify with API:**
```bash
# Test JSON ingest with token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

curl -X POST http://localhost:8000/api/data-ingest \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "records": [
      {"id": "TEST-001", "summary": "Test ticket", "description": "Testing JSON API"}
    ]
  }' | python3 -m json.tool

# Expected: {"job_id": "...", "status_url": "/api/job/...", ...}
```

---

### **Test 5: NLQ with RAG**

**Prerequisites:**
- Make sure you have data ingested (from Test 2 or 3)
- Ollama must be running: `ollama serve` (optional, will fail gracefully if not available)

1. Go to http://localhost:3000/support-analytics

2. **Click "Natural Language Query (NLQ)" tab**

3. **Ask Questions:**
   - "What percentage of tickets have negative sentiment?"
   - "Show me the sentiment trend over time"
   - "What are the main issues customers are facing?"

4. **Check Response:**
   - ✅ Should show AI answer in text format
   - ✅ If Ollama is running, should get intelligent responses
   - ✅ If Ollama is not running, should show fallback message

5. **Check RAG Metadata (NEW!):**
   - Below the AI response, look for blue panel:
   - ✅ Should show "📚 Context Sources (Powered by Elasticsearch)"
   - ✅ Should display number of retrieved tickets
   - ✅ Should show ticket IDs as chips (e.g., TICKET-001, TICKET-002)
   - ✅ Should indicate if Elasticsearch is enabled

6. **Try Chart Generation:**
   - Ask: "Show me the sentiment distribution"
   - ✅ Should display chart below the text answer

**Verify RAG Retrieval:**
```bash
# Check if tickets are being retrieved for RAG
# (Look at backend logs or test NLQ API directly)
curl -X POST http://localhost:8000/api/support/nlq \
  -H "Content-Type: application/json" \
  -d '{"query": "What are customers complaining about?"}' \
  | python3 -m json.tool

# Response should include:
{
  "query": "...",
  "answer": "...",
  "rag_metadata": {
    "retrieved_tickets": 10,
    "elasticsearch_enabled": true,
    "ticket_ids": ["TICKET-001", "TICKET-002", ...]
  }
}
```

---

### **Test 6: Pre-built Analytics Dashboard**

1. Go to http://localhost:3000/support-analytics

2. **Click "Pre-built Dashboards" tab**

3. **Verify Charts Display:**
   - ✅ Summary cards: Total Tickets, Total Comments, Avg Comments/Ticket
   - ✅ Sentiment Distribution pie chart
   - ✅ Confidence Distribution bar chart
   - ✅ Sentiment Trend Over Time line chart
   - ✅ Sentiment by Field Type stacked bar
   - ✅ Tickets by Comment Count
   - ✅ Ticket Status Distribution
   - ✅ Top 10 Most Active Authors

4. **Test Date Filters:**
   - Change start/end dates
   - Click "Refresh"
   - ✅ All charts should update with new data

---

### **Test 7: Job Tracking**

1. Go to http://localhost:3000/jobs

2. **View Job List:**
   - ✅ Should see all previously uploaded jobs
   - ✅ Status: queued, running, completed, or failed
   - ✅ Click on any job to see details

3. **Job Detail Page:**
   - ✅ Progress bar
   - ✅ Records processed count
   - ✅ Sentiment records count
   - ✅ Entity records count
   - ✅ Errors (if any)
   - ✅ Duration

---

## 🔍 **Backend API Testing**

Test backend endpoints directly:

```bash
# Health check
curl http://localhost:8000/health

# Sentiment overview
curl "http://localhost:8000/api/sentiment/overview?start_date=2024-01-01&end_date=2024-12-31"

# Search tickets
curl "http://localhost:8000/api/search?q=login&limit=5"

# Entity aggregation (Elasticsearch)
curl "http://localhost:8000/api/entities/top?limit=10"

# Support analytics
curl "http://localhost:8000/api/support/analytics?start_date=2024-01-01&end_date=2024-12-31"
```

---

## 📊 **Performance Checks**

### Elasticsearch Performance:
```bash
# Should be < 500ms for search
time curl -s "http://localhost:9200/tickets/_search?q=login&size=10" > /dev/null

# Check index stats
curl http://localhost:9200/tickets/_stats
```

### Backend Response Times:
```bash
# Should be < 2 seconds
time curl -s "http://localhost:8000/api/sentiment/overview?start_date=2024-01-01&end_date=2024-12-31" > /dev/null

# Search should be < 1 second
time curl -s "http://localhost:8000/api/search?q=test&limit=20" > /dev/null
```

---

## 🐛 **Common Issues & Fixes**

### Issue: Frontend won't load
```bash
# Check if running
lsof -i :3000

# Restart if needed
cd client && npm start
```

### Issue: "401 Unauthorized" on API calls
- Make sure you're logged in
- Check token in localStorage
- Token may have expired (default 30 min) - re-login

### Issue: Elasticsearch not indexing
```bash
# Check Elasticsearch health
curl http://localhost:9200/_cluster/health

# Restart if needed
docker-compose restart elasticsearch

# Wait 30 seconds, then check indices
curl http://localhost:9200/_cat/indices
```

### Issue: ML Service errors
```bash
# Check ML service logs
cd ml && tail -f app.log

# Restart ML service
cd ml && pyenv shell sentiment-ml && python app.py
```

### Issue: Celery not processing jobs
```bash
# Check Celery logs
docker-compose logs celery

# Restart Celery
docker-compose restart celery
```

### Issue: "No tickets retrieved" in RAG
- Make sure you've ingested data first
- Wait 10-20 seconds for Elasticsearch indexing
- Check: `curl http://localhost:9200/tickets/_count`

---

## ✅ **Success Criteria Checklist**

- [ ] All 5 Docker services running (postgres, redis, elasticsearch, backend, celery)
- [ ] ML service responding on port 5001
- [ ] Frontend running on port 3000
- [ ] Can login and logout successfully
- [ ] Can upload CSV file
- [ ] Job status updates from queued → completed
- [ ] Search finds uploaded tickets
- [ ] Elasticsearch is being used (check API response)
- [ ] JSON ingest tab works
- [ ] NLQ responds with answers
- [ ] RAG metadata shows retrieved tickets
- [ ] Pre-built dashboards display charts
- [ ] Date filters update data
- [ ] Logout button works

---

## 🎯 **Full Test Run Script**

Run all tests automatically:

```bash
#!/bin/bash
echo "🧪 Starting E2E Tests..."

# Test 1: Health checks
echo "Test 1: Health Checks"
curl -sf http://localhost:8000/health && echo "✅ Backend" || echo "❌ Backend"
curl -sf http://localhost:5001/health && echo "✅ ML Service" || echo "❌ ML Service"
curl -sf http://localhost:9200/_cluster/health && echo "✅ Elasticsearch" || echo "❌ Elasticsearch"
redis-cli ping > /dev/null && echo "✅ Redis" || echo "❌ Redis"

# Test 2: Authentication
echo -e "\nTest 2: Authentication"
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ ! -z "$TOKEN" ]; then
  echo "✅ Login successful"
else
  echo "❌ Login failed"
  exit 1
fi

# Test 3: Upload test data
echo -e "\nTest 3: CSV Upload"
cat > /tmp/test_tickets.csv << 'EOF'
Key,Summary,Description
TEST-001,Login issue,User cannot access dashboard
TEST-002,Performance slow,Dashboard loading takes too long
EOF

UPLOAD_RESPONSE=$(curl -s -X POST http://localhost:8000/api/upload \
  -F "file=@/tmp/test_tickets.csv")

JOB_ID=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('job_id', ''))" 2>/dev/null)

if [ ! -z "$JOB_ID" ]; then
  echo "✅ Upload successful, job_id: $JOB_ID"
else
  echo "❌ Upload failed"
fi

# Test 4: Wait for processing
echo -e "\nTest 4: Job Processing"
sleep 5
JOB_STATUS=$(curl -s "http://localhost:8000/api/job/$JOB_ID" \
  | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', ''))" 2>/dev/null)

echo "Job status: $JOB_STATUS"

# Test 5: Search
echo -e "\nTest 5: Search"
SEARCH_RESULT=$(curl -s "http://localhost:8000/api/search?q=login&limit=5")
SEARCH_COUNT=$(echo "$SEARCH_RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('total', 0))" 2>/dev/null)

if [ "$SEARCH_COUNT" -gt 0 ]; then
  echo "✅ Search found $SEARCH_COUNT tickets"
else
  echo "⚠️  Search found no tickets (may need to wait for indexing)"
fi

# Test 6: JSON Ingest
echo -e "\nTest 6: JSON Ingest"
JSON_RESPONSE=$(curl -s -X POST http://localhost:8000/api/data-ingest \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"records":[{"id":"API-TEST-001","summary":"Test via API","description":"Automated test"}]}')

JSON_JOB=$(echo "$JSON_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('job_id', ''))" 2>/dev/null)

if [ ! -z "$JSON_JOB" ]; then
  echo "✅ JSON ingest successful"
else
  echo "❌ JSON ingest failed"
fi

echo -e "\n🎉 Test run complete!"
echo "Open http://localhost:3000 to test frontend features"
```

Save as `test_deployment.sh` and run:
```bash
chmod +x test_deployment.sh
./test_deployment.sh
```

---

## 📱 **Frontend URLs**

- **Dashboard:** http://localhost:3000/
- **Upload:** http://localhost:3000/upload
- **Search:** http://localhost:3000/sentiment-analysis
- **Analytics:** http://localhost:3000/support-analytics
- **Jobs:** http://localhost:3000/jobs
- **Login:** http://localhost:3000/login

---

## 🎉 **Expected Results**

If everything works:
- ✅ All services respond to health checks
- ✅ Login redirects to dashboard
- ✅ CSV upload creates job and processes
- ✅ Search returns results with Elasticsearch
- ✅ JSON ingest requires auth and works
- ✅ NLQ shows RAG metadata
- ✅ Dashboards display charts
- ✅ Logout clears session

**Your sentiment analysis platform with RAG is fully operational!** 🚀
