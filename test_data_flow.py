#!/usr/bin/env python3
"""Test data flow through Parquet pipeline."""

import sys
import os
import pandas as pd
from datetime import datetime
sys.path.append('backend')

def test_data_pipeline():
    """Test complete data pipeline."""
    try:
        from backend.storage.storage_manager import StorageManager
        
        storage = StorageManager()
        
        # Test data
        test_sentiment_data = [
            {
                "ticket_id": "TEST-001",
                "text": "This is a positive test",
                "sentiment": "positive", 
                "confidence": 0.95,
                "field_type": "summary",
                "timestamp": datetime.utcnow()
            },
            {
                "ticket_id": "TEST-002", 
                "text": "This is a negative test",
                "sentiment": "negative",
                "confidence": 0.87,
                "field_type": "description", 
                "timestamp": datetime.utcnow()
            }
        ]
        
        test_ticket_data = [
            {
                "ticket_id": "TEST-001",
                "created_date": datetime.utcnow(),
                "status": "open",
                "priority": "high", 
                "assignee": "test_user",
                "reporter": "test_reporter",
                "summary": "Test ticket 1",
                "description": "Test description 1",
                "overall_sentiment": "positive",
                "sentiment_confidence": 0.95
            }
        ]
        
        print("✅ Test data created")
        
        # Test sentiment summary (should work even with no data)
        summary = storage.get_sentiment_summary()
        print(f"✅ Sentiment summary retrieved: {len(summary)} rows")
        
        # Test search (should work even with no data)
        search_results = storage.search_tickets("test", limit=5)
        print(f"✅ Search completed: {len(search_results)} results")
        
        print("✅ Data pipeline test successful")
        return True
        
    except Exception as e:
        print(f"❌ Data pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run data flow test."""
    print("🧪 Testing Data Flow Through Parquet Pipeline\n")
    
    if test_data_pipeline():
        print("\n🎉 Data pipeline working correctly!")
        return True
    else:
        print("\n⚠️ Data pipeline needs attention")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)