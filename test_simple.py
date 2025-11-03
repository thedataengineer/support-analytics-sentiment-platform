#!/usr/bin/env python3
"""Simple test to verify core migration components work."""

import sys
import os
sys.path.append('backend')

def test_storage_imports():
    """Test that storage components can be imported."""
    try:
        from backend.storage.storage_manager import StorageManager
        from backend.storage.parquet_client import ParquetClient
        from backend.storage.duckdb_client import DuckDBClient
        from backend.storage.s3_client import S3Client
        print("✅ Storage imports successful")
        return True
    except Exception as e:
        print(f"❌ Storage imports failed: {e}")
        return False

def test_storage_manager():
    """Test StorageManager initialization."""
    try:
        from backend.storage.storage_manager import StorageManager
        storage = StorageManager()
        print("✅ StorageManager initialization successful")
        return True
    except Exception as e:
        print(f"❌ StorageManager failed: {e}")
        return False

def test_duckdb_connection():
    """Test DuckDB connection."""
    try:
        from backend.storage.duckdb_client import DuckDBClient
        client = DuckDBClient()
        # Simple test query
        result = client.conn.execute("SELECT 1 as test").fetchone()
        assert result[0] == 1
        print("✅ DuckDB connection successful")
        return True
    except Exception as e:
        print(f"❌ DuckDB connection failed: {e}")
        return False

def test_parquet_schemas():
    """Test Parquet schemas."""
    try:
        from backend.storage.schemas import sentiment_schema, ticket_schema, entity_schema
        assert sentiment_schema is not None
        assert ticket_schema is not None
        assert entity_schema is not None
        print("✅ Parquet schemas loaded")
        return True
    except Exception as e:
        print(f"❌ Parquet schemas failed: {e}")
        return False

def main():
    """Run simple tests."""
    print("🧪 Running Simple Migration Tests\n")
    
    tests = [
        ("Storage Imports", test_storage_imports),
        ("StorageManager", test_storage_manager),
        ("DuckDB Connection", test_duckdb_connection),
        ("Parquet Schemas", test_parquet_schemas)
    ]
    
    passed = 0
    for name, test_func in tests:
        print(f"Testing {name}...")
        if test_func():
            passed += 1
        print()
    
    print(f"📊 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 Core migration components working!")
        return True
    else:
        print("⚠️ Some components need attention")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)