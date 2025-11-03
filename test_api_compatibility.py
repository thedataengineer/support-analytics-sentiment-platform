#!/usr/bin/env python3
"""
Test script to verify API compatibility after Parquet migration.
Checks that all endpoints return expected response formats.
"""

import requests
import json
from datetime import datetime, timedelta

# Test configuration
BASE_URL = "http://localhost:8000"
START_DATE = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
END_DATE = datetime.now().strftime("%Y-%m-%d")

def test_endpoint(endpoint, expected_fields, params=None):
    """Test an API endpoint and verify response structure."""
    try:
        url = f"{BASE_URL}{endpoint}"
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ {endpoint}: HTTP {response.status_code}")
            return False
        
        data = response.json()
        
        # Check if all expected fields are present
        missing_fields = []
        for field in expected_fields:
            if field not in data:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ {endpoint}: Missing fields {missing_fields}")
            return False
        
        print(f"✅ {endpoint}: All expected fields present")
        return True
        
    except Exception as e:
        print(f"❌ {endpoint}: Error - {str(e)}")
        return False

def main():
    """Run API compatibility tests."""
    print("🧪 Testing API compatibility after Parquet migration...\n")
    
    tests = [
        {
            "endpoint": "/api/sentiment/overview",
            "params": {"start_date": START_DATE, "end_date": END_DATE},
            "expected_fields": ["sentiment_distribution", "sentiment_trend"]
        },
        {
            "endpoint": "/api/support/analytics", 
            "params": {"start_date": START_DATE, "end_date": END_DATE},
            "expected_fields": ["summary", "sentiment_distribution", "sentiment_trend", 
                              "field_type_distribution", "ticket_statuses", 
                              "tickets_by_comment_count", "confidence_distribution"]
        },
        {
            "endpoint": "/api/search",
            "params": {"q": "test", "limit": 5},
            "expected_fields": ["total", "results", "offset", "limit"]
        },
        {
            "endpoint": "/api/tickets",
            "params": {"limit": 5},
            "expected_fields": ["total", "results", "offset", "limit"]
        },
        {
            "endpoint": "/health",
            "params": None,
            "expected_fields": ["status", "storage", "timestamp"]
        }
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test_endpoint(test["endpoint"], test["expected_fields"], test["params"]):
            passed += 1
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All API endpoints are compatible!")
        return True
    else:
        print("⚠️  Some endpoints need attention")
        return False

if __name__ == "__main__":
    main()