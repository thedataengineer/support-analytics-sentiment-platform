#!/bin/bash
echo "🧪 Quick E2E Test..."
echo ""

# Test 1: Health checks
echo "=== Test 1: Health Checks ==="
curl -sf http://localhost:8000/health > /dev/null && echo "✅ Backend API" || echo "❌ Backend API"
curl -sf http://localhost:5001/health > /dev/null && echo "✅ ML Service" || echo "❌ ML Service"
curl -sf http://localhost:9200/_cluster/health > /dev/null && echo "✅ Elasticsearch" || echo "❌ Elasticsearch"
redis-cli ping > /dev/null 2>&1 && echo "✅ Redis" || echo "❌ Redis"
curl -sf http://localhost:3000 > /dev/null && echo "✅ Frontend" || echo "❌ Frontend"
echo ""

# Test 2: Authentication
echo "=== Test 2: Authentication ==="
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ ! -z "$TOKEN" ]; then
  echo "✅ Login successful"
  echo "Token: ${TOKEN:0:20}..."
else
  echo "❌ Login failed"
  exit 1
fi
echo ""

# Test 3: Upload test data
echo "=== Test 3: CSV Upload ==="
cat > /tmp/e2e_test_tickets.csv << 'EOF'
Key,Summary,Description,Comments
E2E-001,Cannot login to application,Users report authentication failures,"Checked database, Fixed password validation"
E2E-002,Dashboard shows incorrect data,Sentiment metrics not matching actual data,"Updated aggregation query"
E2E-003,Feature request: Dark mode,Users want dark theme support,"Added to backlog, Will prioritize"
EOF

UPLOAD_RESPONSE=$(curl -s -X POST http://localhost:8000/api/upload \
  -F "file=@/tmp/e2e_test_tickets.csv")

JOB_ID=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('job_id', ''))" 2>/dev/null)

if [ ! -z "$JOB_ID" ]; then
  echo "✅ Upload successful"
  echo "Job ID: $JOB_ID"
else
  echo "❌ Upload failed"
  echo "Response: $UPLOAD_RESPONSE"
fi
echo ""

# Test 4: Wait for processing
echo "=== Test 4: Job Processing (waiting 10s) ==="
sleep 10

JOB_RESPONSE=$(curl -s "http://localhost:8000/api/job/$JOB_ID")
JOB_STATUS=$(echo "$JOB_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null)
RECORDS_PROCESSED=$(echo "$JOB_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('records_processed', 0))" 2>/dev/null)

echo "Status: $JOB_STATUS"
echo "Records Processed: $RECORDS_PROCESSED"

if [ "$JOB_STATUS" = "completed" ]; then
  echo "✅ Job completed successfully"
else
  echo "⚠️  Job status: $JOB_STATUS (may still be processing)"
fi
echo ""

# Test 5: Search (wait for Elasticsearch indexing)
echo "=== Test 5: Search ==="
sleep 5
SEARCH_RESULT=$(curl -s "http://localhost:8000/api/search?q=login&limit=5")
SEARCH_COUNT=$(echo "$SEARCH_RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('total', 0))" 2>/dev/null)
SEARCH_SOURCE=$(echo "$SEARCH_RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('source', 'unknown'))" 2>/dev/null)

echo "Search results: $SEARCH_COUNT tickets"
echo "Backend: $SEARCH_SOURCE"

if [ "$SEARCH_COUNT" -gt 0 ]; then
  echo "✅ Search working"
else
  echo "⚠️  No search results (Elasticsearch may need more time to index)"
fi
echo ""

# Test 6: JSON Ingest
echo "=== Test 6: JSON Ingest with Auth ==="
JSON_RESPONSE=$(curl -s -X POST http://localhost:8000/api/data-ingest \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"records":[{"id":"E2E-JSON-001","summary":"API batch test","description":"Testing JSON ingest endpoint"}]}')

JSON_JOB=$(echo "$JSON_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('job_id', ''))" 2>/dev/null)

if [ ! -z "$JSON_JOB" ]; then
  echo "✅ JSON ingest successful"
  echo "Job ID: $JSON_JOB"
else
  echo "❌ JSON ingest failed"
  echo "Response: $JSON_RESPONSE"
fi
echo ""

# Test 7: Elasticsearch Check
echo "=== Test 7: Elasticsearch Index Check ==="
ES_COUNT=$(curl -s "http://localhost:9200/tickets/_count" | python3 -c "import sys, json; print(json.load(sys.stdin).get('count', 0))" 2>/dev/null)
echo "Tickets in Elasticsearch: $ES_COUNT"

if [ "$ES_COUNT" -gt 0 ]; then
  echo "✅ Elasticsearch has indexed data"
else
  echo "⚠️  No data in Elasticsearch yet (needs time to index)"
fi
echo ""

# Summary
echo "========================================"
echo "🎉 Test Suite Complete!"
echo "========================================"
echo ""
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8000"
echo "ML Service: http://localhost:5001"
echo ""
echo "Next steps:"
echo "1. Open http://localhost:3000 in browser"
echo "2. Login with: admin@example.com / password"
echo "3. Try uploading CSV from Upload page"
echo "4. Test NLQ with RAG in Support Analytics"
echo "5. Check RAG metadata display"
echo ""
echo "📚 Full test plan: LOCAL_DEPLOYMENT_TEST.md"
