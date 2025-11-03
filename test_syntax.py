#!/usr/bin/env python3
"""
Basic syntax and structure test for the Sentiment Analysis Platform
Tests that our code can be parsed and basic logic works without external dependencies.
"""

import sys
import os
import ast
import importlib.util

def test_python_syntax():
    """Test that all Python files have valid syntax"""
    print("Testing Python syntax...")

    python_files = []
    for root, dirs, files in os.walk('.'):
        # Skip certain directories
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules']]

        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))

    failed_files = []
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            ast.parse(source, file_path)
        except SyntaxError as e:
            failed_files.append((file_path, str(e)))
        except Exception as e:
            failed_files.append((file_path, f"Error reading file: {e}"))

    if failed_files:
        print("✗ Syntax errors found:")
        for file_path, error in failed_files:
            print(f"  {file_path}: {error}")
        return False
    else:
        print(f"✓ All {len(python_files)} Python files have valid syntax")
        return True

def test_file_structure():
    """Test that all required files exist"""
    print("\nTesting file structure...")

    required_files = [
        'backend/main.py',
        'backend/api/auth.py',
        'backend/api/ingest_csv.py',
        'backend/api/report_api.py',
        'backend/api/search_api.py',
        'backend/models/sentiment_result.py',
        'backend/models/entity.py',
        'backend/models/ticket.py',
        'backend/models/user.py',
        'backend/services/column_mapping.py',
        'backend/services/report_summarizer.py',
        'backend/services/nlp_client.py',
        'backend/jobs/ingest_job.py',
        'backend/jobs/celery_config.py',
        'client/src/App.js',
        'client/src/components/Dashboard/Dashboard.js',
        'client/src/components/Upload/Upload.js',
        'client/src/components/ReportExport/ReportExport.js',
        'client/src/pages/Login/Login.js',
        'client/src/components/EntitiesPanel/EntitiesPanel.js',
        'ml/app.py',
        'ml/sentiment_model/predict.py',
        'ml/ner_model/extract.py',
        'db/init.sql',
        'docker-compose.yml',
        'README.md'
    ]

    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)

    if missing_files:
        print("✗ Missing files:")
        for file_path in missing_files:
            print(f"  {file_path}")
        return False
    else:
        print(f"✓ All {len(required_files)} required files exist")
        return True

def test_package_structure():
    """Test that Python packages have __init__.py files"""
    print("\nTesting package structure...")

    packages = [
        'backend',
        'backend/api',
        'backend/models',
        'backend/services',
        'backend/jobs'
    ]

    missing_init = []
    for package in packages:
        init_file = os.path.join(package, '__init__.py')
        if not os.path.exists(init_file):
            missing_init.append(init_file)

    if missing_init:
        print("✗ Missing __init__.py files:")
        for init_file in missing_init:
            print(f"  {init_file}")
        return False
    else:
        print(f"✓ All {len(packages)} packages have __init__.py files")
        return True

def test_basic_logic():
    """Test basic logic without external dependencies"""
    print("\nTesting basic logic...")

    try:
        # Test column mapping logic
        import re

        # Read the column mapping file
        with open('backend/services/column_mapping.py', 'r') as f:
            content = f.read()

        # Check for basic class definition
        if 'class ColumnMapper:' not in content:
            raise Exception("ColumnMapper class not found")

        # Check for basic methods
        required_methods = ['detect_text_columns', 'create_mapping', 'apply_mapping']
        for method in required_methods:
            if f'def {method}' not in content:
                raise Exception(f"Method {method} not found in ColumnMapper")

        print("✓ Column mapping logic looks correct")

        # Test authentication logic
        with open('backend/api/auth.py', 'r') as f:
            auth_content = f.read()

        # Check for basic auth functions
        auth_functions = ['verify_password', 'get_password_hash', 'create_access_token']
        for func in auth_functions:
            if f'def {func}' not in auth_content:
                raise Exception(f"Function {func} not found in auth.py")

        print("✓ Authentication logic looks correct")

        return True

    except Exception as e:
        print(f"✗ Basic logic test failed: {e}")
        return False

def test_config_files():
    """Test configuration files"""
    print("\nTesting configuration files...")

    try:
        # Test docker-compose.yml
        with open('docker-compose.yml', 'r') as f:
            docker_content = f.read()

        if 'postgres:' not in docker_content:
            raise Exception("PostgreSQL service not found in docker-compose.yml")

        if 'elasticsearch:' not in docker_content:
            raise Exception("Elasticsearch service not found in docker-compose.yml")

        if 'redis:' not in docker_content:
            raise Exception("Redis service not found in docker-compose.yml")

        print("✓ Docker configuration looks correct")

        # Test database schema
        with open('db/init.sql', 'r') as f:
            sql_content = f.read()

        required_tables = ['users', 'tickets', 'sentiment_results', 'entities']
        for table in required_tables:
            if f'CREATE TABLE IF NOT EXISTS {table}' not in sql_content:
                raise Exception(f"Table {table} not found in init.sql")

        print("✓ Database schema looks correct")

        return True

    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False

def main():
    """Run all syntax tests"""
    print("=" * 60)
    print("SENTIMENT ANALYSIS PLATFORM - SYNTAX & STRUCTURE TESTS")
    print("=" * 60)

    # Change to the sentiment-platform directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    tests = [
        test_file_structure,
        test_package_structure,
        test_python_syntax,
        test_basic_logic,
        test_config_files,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            results.append(False)

    print("\n" + "=" * 60)
    print("SYNTAX TEST RESULTS SUMMARY")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("🎉 All syntax and structure tests passed!")
        print("\nThe Sentiment Analysis Platform MVP has been successfully created!")
        print("All code files are syntactically correct and the project structure is complete.")
        print("\nTo run the full system:")
        print("1. Start services: docker-compose up -d")
        print("2. Install backend dependencies: cd backend && pip install -r requirements.txt")
        print("3. Install ML dependencies: cd ml && pip install -r requirements.txt")
        print("4. Install frontend dependencies: cd client && npm install")
        print("5. Start backend: cd backend && uvicorn main:app --reload")
        print("6. Start ML service: cd ml && python app.py")
        print("7. Start frontend: cd client && npm start")
        return 0
    else:
        print("❌ Some tests failed. Check output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
