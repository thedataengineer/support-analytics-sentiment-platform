#!/usr/bin/env python3
"""Component-level tests for backend services"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_storage_components():
    """Test storage layer components"""
    print("🔧 Testing Storage Components")
    print("-" * 30)
    
    try:
        from backend.storage.duckdb_client import DuckDBClient
        client = DuckDBClient()
        conn = client.conn
        
        # Test connection
        result = conn.execute("SELECT 'Storage OK' as status").fetchone()
        print(f"✅ DuckDB Connection: {result[0]}")
        
        # Test table creation
        conn.execute("""
            CREATE TABLE IF NOT EXISTS test_table (
                id INTEGER,
                name VARCHAR
            )
        """)
        print("✅ Table Creation: OK")
        
        # Test data operations
        conn.execute("INSERT INTO test_table VALUES (1, 'test')")
        result = conn.execute("SELECT * FROM test_table WHERE id = 1").fetchone()
        print(f"✅ Data Operations: {result}")
        
        # Cleanup
        conn.execute("DROP TABLE test_table")
        print("✅ Cleanup: OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Storage Test Failed: {e}")
        return False

def test_api_imports():
    """Test API module imports"""
    print("\n🔧 Testing API Imports")
    print("-" * 30)
    
    modules = [
        ("dashboard_api", "backend.api.dashboard_api"),
        ("advanced_analytics_api", "backend.api.advanced_analytics_api"),
        ("support_analytics_api", "backend.api.support_analytics_api")
    ]
    
    success_count = 0
    for name, module_path in modules:
        try:
            __import__(module_path)
            print(f"✅ {name}: Import OK")
            success_count += 1
        except Exception as e:
            print(f"❌ {name}: Import Failed - {e}")
    
    return success_count == len(modules)

def test_data_flow():
    """Test basic data flow"""
    print("\n🔧 Testing Data Flow")
    print("-" * 30)
    
    try:
        from backend.storage.duckdb_client import DuckDBClient
        client = DuckDBClient()
        conn = client.conn
        
        # Check if we have any data
        tables = conn.execute("SHOW TABLES").fetchall()
        print(f"✅ Available Tables: {[t[0] for t in tables]}")
        
        # Test sample queries
        if any('tickets' in str(table) for table in tables):
            count = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
            print(f"✅ Tickets Count: {count}")
        
        if any('sentiment' in str(table) for table in tables):
            count = conn.execute("SELECT COUNT(*) FROM sentiment_results").fetchone()[0]
            print(f"✅ Sentiment Results Count: {count}")
            
        return True
        
    except Exception as e:
        print(f"❌ Data Flow Test Failed: {e}")
        return False

def main():
    """Run all component tests"""
    print("🧪 Component Test Suite")
    print("=" * 40)
    
    tests = [
        test_storage_components,
        test_api_imports,
        test_data_flow
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 40)
    print("📊 Component Test Summary")
    print("=" * 40)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 All component tests passed!")
        return True
    else:
        print("⚠️  Some component tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)