#!/usr/bin/env python3
"""End-to-end test suite for sentiment analysis platform"""

import requests
import json
import time
import sys
from pathlib import Path

# Test configuration
API_BASE = "http://localhost:8000"
FRONTEND_BASE = "http://localhost:3000"

class E2ETestSuite:
    def __init__(self):
        self.token = None
        self.test_results = []
        
    def log_test(self, name, success, message=""):
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {name}")
        if message:
            print(f"   {message}")
        self.test_results.append({"name": name, "success": success, "message": message})
        
    def test_backend_health(self):
        """Test backend health endpoint"""
        try:
            response = requests.get(f"{API_BASE}/health", timeout=5)
            success = response.status_code == 200
            data = response.json() if success else {}
            self.log_test("Backend Health Check", success, 
                         f"Status: {data.get('status', 'unknown')}")
            return success
        except Exception as e:
            self.log_test("Backend Health Check", False, str(e))
            return False
            
    def test_auth_flow(self):
        """Test authentication flow"""
        try:
            # Test login
            login_data = {
                "username": "admin@example.com",
                "password": "password"
            }
            response = requests.post(f"{API_BASE}/api/auth/login", 
                                   data=login_data, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.log_test("Authentication Login", True, "Token received")
                return True
            else:
                self.log_test("Authentication Login", False, 
                             f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Authentication Login", False, str(e))
            return False
            
    def test_dashboard_apis(self):
        """Test dashboard API endpoints"""
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        
        # Test dashboard metrics
        try:
            response = requests.get(f"{API_BASE}/api/dashboard/metrics", 
                                  headers=headers, timeout=5)
            success = response.status_code == 200
            if success:
                data = response.json()
                has_metrics = all(key in data for key in 
                                ["total_tickets", "avg_sentiment", "processing_jobs"])
                self.log_test("Dashboard Metrics API", has_metrics,
                             f"Metrics: {list(data.keys())}")
            else:
                self.log_test("Dashboard Metrics API", False, 
                             f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Dashboard Metrics API", False, str(e))
            
        # Test recent tickets
        try:
            response = requests.get(f"{API_BASE}/api/dashboard/recent-tickets", 
                                  headers=headers, timeout=5)
            success = response.status_code == 200
            if success:
                data = response.json()
                self.log_test("Recent Tickets API", True, 
                             f"Found {len(data)} tickets")
            else:
                self.log_test("Recent Tickets API", False, 
                             f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Recent Tickets API", False, str(e))
            
    def test_analytics_apis(self):
        """Test advanced analytics API endpoints"""
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        
        endpoints = [
            ("Heatmap API", "/api/analytics/heatmap"),
            ("Entities API", "/api/analytics/entities"),
            ("Correlations API", "/api/analytics/correlations"),
            ("Anomalies API", "/api/analytics/anomalies")
        ]
        
        for name, endpoint in endpoints:
            try:
                response = requests.get(f"{API_BASE}{endpoint}", 
                                      headers=headers, timeout=5)
                success = response.status_code == 200
                if success:
                    data = response.json()
                    self.log_test(name, True, f"Data keys: {list(data.keys())}")
                else:
                    self.log_test(name, False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test(name, False, str(e))
                
    def test_storage_system(self):
        """Test Parquet storage system"""
        try:
            # Test DuckDB connection
            from backend.storage.duckdb_client import DuckDBClient
            client = DuckDBClient()
            conn = client.conn
            
            # Test basic query
            result = conn.execute("SELECT 1 as test").fetchone()
            success = result[0] == 1
            self.log_test("DuckDB Connection", success, "Basic query executed")
            
            # Test table existence
            tables = conn.execute("SHOW TABLES").fetchall()
            table_names = [table[0] for table in tables]
            expected_tables = ["tickets", "sentiment_results", "entities"]
            
            for table in expected_tables:
                exists = table in table_names
                self.log_test(f"Table: {table}", exists, 
                             f"Found in: {table_names}")
                             
        except Exception as e:
            self.log_test("Storage System", False, str(e))
            
    def test_frontend_accessibility(self):
        """Test frontend is accessible"""
        try:
            response = requests.get(FRONTEND_BASE, timeout=5)
            success = response.status_code == 200
            self.log_test("Frontend Accessibility", success, 
                         f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Frontend Accessibility", False, str(e))
            return False
            
    def run_all_tests(self):
        """Run complete test suite"""
        print("🚀 Starting End-to-End Test Suite")
        print("=" * 50)
        
        # Core system tests
        backend_ok = self.test_backend_health()
        if not backend_ok:
            print("❌ Backend not available - skipping API tests")
        else:
            self.test_auth_flow()
            self.test_dashboard_apis()
            self.test_analytics_apis()
            
        # Storage tests
        self.test_storage_system()
        
        # Frontend tests
        self.test_frontend_accessibility()
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 Test Results Summary")
        print("=" * 50)
        
        passed = sum(1 for test in self.test_results if test["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED!")
            return True
        else:
            print(f"\n⚠️  {total - passed} TESTS FAILED")
            return False

if __name__ == "__main__":
    suite = E2ETestSuite()
    success = suite.run_all_tests()
    sys.exit(0 if success else 1)