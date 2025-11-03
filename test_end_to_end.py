#!/usr/bin/env python3
"""End-to-end test for Parquet migration."""

import requests
import json
import time
import sys
import os

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["storage"] == "parquet"
        print("✅ Health check passed")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_auth():
    """Test authentication."""
    try:
        # Bootstrap admin user
        requests.post(f"{BASE_URL}/api/auth/bootstrap", timeout=5)
        
        # Login
        response = requests.post(f"{BASE_URL}/api/auth/login", 
                               json={"email": "admin@example.com", "password": "password"},
                               timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        print("✅ Authentication passed")
        return data["access_token"]
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return None

def test_ingestion(token):
    """Test CSV ingestion."""
    try:
        # Create test CSV
        csv_content = "ticket_id,summary,description\nTEST-1,Test ticket,Test description\nTEST-2,Another ticket,Another description"
        
        files = {'file': ('test.csv', csv_content, 'text/csv')}
        headers = {'Authorization': f'Bearer {token}'} if token else {}
        
        response = requests.post(f"{BASE_URL}/api/upload", files=files, headers=headers, timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        print("✅ CSV ingestion passed")
        return data["job_id"]
    except Exception as e:
        print(f"❌ CSV ingestion failed: {e}")
        return None

def test_analytics():
    """Test analytics endpoints."""
    try:
        # Test sentiment overview
        response = requests.get(f"{BASE_URL}/api/sentiment/overview", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "sentiment_distribution" in data
        assert "sentiment_trend" in data
        
        # Test support analytics
        response = requests.get(f"{BASE_URL}/api/support/analytics", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        
        print("✅ Analytics endpoints passed")
        return True
    except Exception as e:
        print(f"❌ Analytics failed: {e}")
        return False

def test_search():
    """Test search functionality."""
    try:
        response = requests.get(f"{BASE_URL}/api/search?q=test&limit=5", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "results" in data
        print("✅ Search passed")
        return True
    except Exception as e:
        print(f"❌ Search failed: {e}")
        return False

def test_report_schedule(token: str) -> bool:
    """Test scheduled report configuration endpoints."""
    try:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        payload = {
            "schedule_frequency": "daily",
            "delivery_time": "08:00",
            "email": "reports@example.com",
        }
        response = requests.post(
            f"{BASE_URL}/api/report/schedule",
            json=payload,
            headers=headers,
            timeout=10,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["schedule_frequency"] == "daily"
        assert data["email"] == "reports@example.com"

        response = requests.get(
            f"{BASE_URL}/api/report/schedule",
            headers=headers,
            timeout=10,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["schedule_frequency"] == "daily"
        print("✅ Report schedule endpoints passed")
        return True
    except Exception as e:
        print(f"❌ Report schedule failed: {e}")
        return False

def main():
    """Run end-to-end test."""
    print("🧪 Starting End-to-End Test for Parquet Migration\n")
    
    tests = [
        ("Health Check", test_health),
        ("Authentication", test_auth),
        ("Report Schedule", None),
        ("Analytics", test_analytics),
        ("Search", test_search)
    ]
    
    passed = 0
    token = None
    
    for name, test_func in tests:
        print(f"Running {name}...")
        if name == "Authentication":
            result = test_func()
            if result:
                token = result
                passed += 1
        elif name == "Report Schedule":
            if token and test_report_schedule(token):
                passed += 1
        else:
            if test_func():
                passed += 1
    
    print(f"\n📊 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! Migration successful!")
        return True
    else:
        print("⚠️ Some tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
