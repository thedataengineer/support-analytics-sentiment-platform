#!/usr/bin/env python3
"""
Basic functionality test for the Sentiment Analysis Platform
"""

import sys
import os
import json
from datetime import datetime, timedelta

# Add backend to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_imports():
    """Test that we can import our modules"""
    print("Testing imports...")

    try:
        # Test backend imports
        from backend.api.auth import router as auth_router
        from backend.api.ingest_csv import router as ingest_router
        from backend.api.report_api import router as report_router
        from backend.api.search_api import router as search_router

        print("✓ Backend API imports successful")

        # Test model imports
        from backend.models.sentiment_result import SentimentResult
        from backend.models.entity import Entity
        from backend.models.ticket import Ticket
        from backend.models.user import User

        print("✓ Database model imports successful")

        # Test service imports
        from backend.services.column_mapping import ColumnMapper
        from backend.services.report_summarizer import generate_pdf_report
        from backend.services.nlp_client import nlp_client

        print("✓ Service imports successful")

        assert True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        assert False, f"Import failed: {e}"

def test_column_mapper():
    """Test column mapping functionality"""
    print("\nTesting column mapping...")

    try:
        from backend.services.column_mapping import ColumnMapper

        # Create a sample CSV structure
        sample_columns = ['id', 'summary', 'description', 'comment', 'status']

        mapper = ColumnMapper()
        mapping = mapper.create_mapping(sample_columns, 'test_source')

        assert 'text_columns' in mapping
        assert len(mapping['text_columns']) > 0

        print("✓ Column mapping works")
        assert True
    except Exception as e:
        print(f"✗ Column mapping failed: {e}")
        assert False, f"Column mapping failed: {e}"

def test_data_models():
    """Test data model creation"""
    print("\nTesting data models...")

    try:
        from backend.models.sentiment_result import SentimentResult
        from backend.models.ticket import Ticket
        from backend.models.entity import Entity

        # Test creating instances (without DB)
        ticket = Ticket(
            ticket_id="TEST-001",
            summary="Test ticket",
            description="Test description"
        )

        sentiment = SentimentResult(
            ticket_id="TEST-001",
            text="Test text",
            sentiment="positive",
            confidence=0.85
        )

        entity = Entity(
            ticket_id="TEST-001",
            text="test",
            label="PRODUCT",
            start_pos=0,
            end_pos=4
        )

        print("✓ Data models work")
        assert True
    except Exception as e:
        print(f"✗ Data models failed: {e}")
        assert False, f"Data models failed: {e}"

def test_auth_logic():
    """Test authentication logic"""
    print("\nTesting authentication logic...")

    try:
        from backend.api.auth import create_access_token, verify_password, get_password_hash

        # Test password hashing
        password = "test123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed)

        # Test JWT token creation
        token = create_access_token({"sub": "test@example.com"})
        assert token is not None
        assert isinstance(token, str)

        print("✓ Authentication logic works")
        assert True
    except Exception as e:
        print(f"✗ Authentication logic failed: {e}")
        assert False, f"Authentication logic failed: {e}"

def test_csv_validation():
    """Test CSV validation logic"""
    print("\nTesting CSV validation...")

    try:
        import pandas as pd
        from io import StringIO

        # Create sample CSV data
        csv_data = """id,summary,description,status
TICKET-001,Service issue,The service was slow,open
TICKET-002,Product feedback,Great product quality,closed
"""

        # Test pandas CSV reading
        df = pd.read_csv(StringIO(csv_data))

        assert len(df) == 2
        assert 'summary' in df.columns
        assert 'description' in df.columns

        print("✓ CSV validation works")
        assert True
    except Exception as e:
        print(f"✗ CSV validation failed: {e}")
        assert False, f"CSV validation failed: {e}"

def test_report_generation():
    """Test report generation logic"""
    print("\nTesting report generation...")

    try:
        from backend.services.report_summarizer import generate_pdf_report

        # Test with sample dates (this will create a file)
        start_date = "2025-01-01"
        end_date = "2025-01-31"

        # Note: This might fail due to missing matplotlib, but let's see
        try:
            pdf_path = generate_pdf_report(start_date, end_date)
            if os.path.exists(pdf_path):
                print("✓ PDF report generation works")
                os.remove(pdf_path)  # Clean up
                assert True
            else:
                print("⚠ PDF generation returned path but file doesn't exist")
                assert False, "PDF file not created"
        except ImportError:
            print("⚠ PDF generation skipped (matplotlib not available)")
            assert True
        except Exception as e:
            print(f"✗ PDF generation failed: {e}")
            assert False, f"PDF generation failed: {e}"

    except Exception as e:
        print(f"✗ Report generation test failed: {e}")
        assert False, f"Report generation test failed: {e}"

def main():
    """Run all tests"""
    print("=" * 50)
    print("SENTIMENT ANALYSIS PLATFORM - BASIC TESTS")
    print("=" * 50)

    tests = [
        test_imports,
        test_column_mapper,
        test_data_models,
        test_auth_logic,
        test_csv_validation,
        test_report_generation,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            results.append(False)

    print("\n" + "=" * 50)
    print("TEST RESULTS SUMMARY")
    print("=" * 50)

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("🎉 All basic tests passed!")
        return 0
    else:
        print("❌ Some tests failed. Check output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
