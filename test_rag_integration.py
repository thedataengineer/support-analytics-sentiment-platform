#!/usr/bin/env python3
"""
Test script for RAG integration with Elasticsearch
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

print("=" * 60)
print("RAG Integration Test Suite")
print("=" * 60)

# Test 1: Elasticsearch Client
print("\n[TEST 1] Testing Elasticsearch Client...")
try:
    from backend.services.elasticsearch_client import es_client

    if es_client.enabled:
        print("✅ Elasticsearch connected successfully")
        print(f"   URL: {es_client.es_url}")

        # Test index creation
        es_client._ensure_indices()
        print("✅ Indices created/verified")
    else:
        print("⚠️  Elasticsearch not available (will use PostgreSQL fallback)")
except Exception as e:
    print(f"❌ Elasticsearch client failed: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Index a sample ticket
print("\n[TEST 2] Testing Ticket Indexing...")
try:
    sample_ticket = {
        "ticket_id": "TEST-001",
        "summary": "Cannot login to the application",
        "description": "User is experiencing authentication issues when trying to access the dashboard",
        "ultimate_sentiment": "negative",
        "ultimate_confidence": 0.85,
        "sentiment_trend": "declining",
        "created_at": "2024-11-01T10:00:00Z",
        "issue_type": "bug",
        "comment_count": 3,
        "entities": [
            {"text": "authentication", "label": "ISSUE"},
            {"text": "dashboard", "label": "PRODUCT"}
        ]
    }

    if es_client.enabled:
        success = es_client.index_ticket(sample_ticket)
        if success:
            print("✅ Sample ticket indexed successfully")
            es_client.refresh_index()
            print("✅ Index refreshed")
        else:
            print("⚠️  Indexing returned False")
    else:
        print("⚠️  Skipping (Elasticsearch not available)")
except Exception as e:
    print(f"❌ Indexing failed: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Search/Retrieval
print("\n[TEST 3] Testing RAG Retrieval...")
try:
    from datetime import datetime, timedelta
    from backend.api.nlq_api import retrieve_relevant_tickets

    start = datetime.now() - timedelta(days=30)
    end = datetime.now()

    results = retrieve_relevant_tickets(
        query="login authentication issues",
        start_date=start,
        end_date=end,
        limit=5
    )

    if results:
        print(f"✅ Retrieved {len(results)} relevant tickets")
        for idx, ticket in enumerate(results[:3], 1):
            print(f"   {idx}. {ticket['ticket_id']}: {ticket['summary'][:50]}...")
    elif es_client.enabled:
        print("⚠️  No tickets retrieved (index may be empty)")
    else:
        print("⚠️  Skipping (Elasticsearch not available)")

except Exception as e:
    print(f"❌ Retrieval failed: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Ollama Connection
print("\n[TEST 4] Testing Ollama Connection...")
try:
    import httpx
    import asyncio

    async def test_ollama():
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "llama2:70b",
                        "prompt": "Say 'Hello' in one word.",
                        "stream": False
                    }
                )
                if response.status_code == 200:
                    result = response.json()
                    print("✅ Ollama llama2:70b is available")
                    print(f"   Response: {result.get('response', '')[:50]}...")
                    return True
                elif response.status_code == 404:
                    print("⚠️  llama2:70b not found, trying 7b...")
                    response = await client.post(
                        "http://localhost:11434/api/generate",
                        json={
                            "model": "llama2:7b",
                            "prompt": "Say 'Hello' in one word.",
                            "stream": False
                        }
                    )
                    if response.status_code == 200:
                        print("✅ Ollama llama2:7b is available (70b not found)")
                        return True
                return False
        except Exception as e:
            print(f"❌ Ollama not available: {e}")
            return False

    ollama_ok = asyncio.run(test_ollama())

except Exception as e:
    print(f"❌ Ollama test failed: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Full RAG Pipeline
print("\n[TEST 5] Testing Full RAG Pipeline...")
try:
    if es_client.enabled and 'ollama_ok' in locals() and ollama_ok:
        print("✅ All components ready for RAG")
        print("   • Elasticsearch: Connected")
        print("   • Ollama: Available")
        print("   • RAG Pipeline: Ready")
        print("\n   Test query: POST /api/support/nlq")
        print('   Body: {"query": "What are customers complaining about?"}')
    else:
        missing = []
        if not es_client.enabled:
            missing.append("Elasticsearch")
        if 'ollama_ok' not in locals() or not ollama_ok:
            missing.append("Ollama")
        print(f"⚠️  Missing components: {', '.join(missing)}")
        print("   RAG will fall back to PostgreSQL + statistics only")
except Exception as e:
    print(f"❌ Pipeline check failed: {e}")

# Summary
print("\n" + "=" * 60)
print("Test Summary")
print("=" * 60)
print("✅ = Working")
print("⚠️  = Warning/Fallback available")
print("❌ = Error")
print("\nTo test the API endpoint:")
print("  1. Start backend: cd backend && uvicorn main:app --reload")
print("  2. Start ML service: cd ml && python app.py")
print("  3. Test NLQ:")
print('     curl -X POST http://localhost:8000/api/support/nlq \\')
print('       -H "Content-Type: application/json" \\')
print('       -d \'{"query": "What issues are customers facing?"}\'')
print("=" * 60)
