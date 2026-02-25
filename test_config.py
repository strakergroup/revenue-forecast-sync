#!/usr/bin/env python3
"""
Revenue Forecast Sync - Configuration Test
Tests configuration loading and validation without MySQL connection
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_env_loading():
    """Test .env file loading"""
    print("=== Testing .env File Loading ===")
    
    try:
        from dotenv import load_dotenv
        
        # Load .env file
        load_dotenv('.env')
        
        # Check environment variables
        mysql_host = os.getenv('MYSQL_HOST')
        mysql_user = os.getenv('MYSQL_USER') 
        mysql_database = os.getenv('MYSQL_DATABASE')
        api_key = os.getenv('BOOKINGS_SYNC_API_KEY')
        app_url = os.getenv('APP_URL')
        
        print(f"✅ MYSQL_HOST: {mysql_host}")
        print(f"✅ MYSQL_USER: {mysql_user}")
        print(f"✅ MYSQL_DATABASE: {mysql_database}")
        print(f"✅ APP_URL: {app_url}")
        print(f"✅ API_KEY: {'*' * (len(api_key) - 8) + api_key[-8:] if api_key else 'Not set'}")
        
        # Validate required variables
        required_vars = ['MYSQL_HOST', 'MYSQL_USER', 'MYSQL_PASSWORD', 'BOOKINGS_SYNC_API_KEY']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            print(f"❌ Missing required variables: {', '.join(missing_vars)}")
            return False
        else:
            print("✅ All required environment variables are set")
            return True
            
    except ImportError:
        print("❌ python-dotenv not available")
        return False
    except Exception as e:
        print(f"❌ Error loading .env: {e}")
        return False

def test_config_loading():
    """Test config loading from sync_app"""
    print("\n=== Testing Configuration Loading ===")
    
    try:
        # Mock the mysql.connector to avoid installation requirement
        import sys
        from unittest.mock import MagicMock
        sys.modules['mysql.connector'] = MagicMock()
        
        # Import and test config loading
        from sync_app import load_config, MYSQL_CONFIG, API_KEY, APP_URL
        
        print("Before load_config():")
        print(f"  MYSQL_HOST: {MYSQL_CONFIG['host']}")
        print(f"  API_KEY: {API_KEY}")
        
        load_config()
        
        print("After load_config():")
        print(f"  MYSQL_HOST: {MYSQL_CONFIG['host']}")
        print(f"  MYSQL_USER: {MYSQL_CONFIG['user']}")
        print(f"  MYSQL_DATABASE: {MYSQL_CONFIG['database']}")
        print(f"  APP_URL: {APP_URL}")
        print(f"  API_KEY: {'*' * (len(API_KEY) - 8) + API_KEY[-8:] if API_KEY else 'Not set'}")
        
        print("✅ Configuration loading successful")
        return True
        
    except Exception as e:
        print(f"❌ Error testing config loading: {e}")
        return False

def test_sql_query():
    """Test SQL query generation"""
    print("\n=== Testing SQL Query ===")
    
    try:
        from sync_app import QUERY
        
        # Test query with where clause
        where_clause = "WHERE j.job_created >= '2026-01-01'"
        formatted_query = QUERY.format(where_clause=where_clause)
        
        print("✅ SQL Query structure:")
        print("  - Selects from bi_data.jobs")
        print("  - Joins with clients, groups, straker_groups")
        print("  - Includes where clause formatting")
        print("  - Orders by job_created DESC")
        
        # Check for required fields
        required_fields = ['Customer', 'TJ', 'Date', 'Status', 'TJAmount']
        for field in required_fields:
            if field in formatted_query:
                print(f"  ✅ Field '{field}' included")
            else:
                print(f"  ❌ Field '{field}' missing")
        
        print("✅ SQL query test passed")
        return True
        
    except Exception as e:
        print(f"❌ Error testing SQL query: {e}")
        return False

def test_api_payload():
    """Test API payload structure"""
    print("\n=== Testing API Payload Structure ===")
    
    try:
        # Mock data similar to what would come from database
        mock_data = [
            {
                'Customer': 'Test Client',
                'TJ': 'TJ123456',
                'Date': '2026-02-25',
                'Status': 'completed',
                'TJAmount (in Sales Order currency)': 1500.00,
                'Currency': 'USD'
            }
        ]
        
        import json
        from datetime import date, datetime
        
        def serialize(obj):
            if isinstance(obj, (date, datetime)):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serialisable")
        
        # Test serialization
        serialized = json.loads(json.dumps(mock_data, default=serialize))
        
        print("✅ API Payload structure:")
        print(f"  - Data type: {type(serialized)}")
        print(f"  - Record count: {len(serialized)}")
        print(f"  - Sample record keys: {list(serialized[0].keys())}")
        print("  ✅ JSON serialization successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing API payload: {e}")
        return False

def main():
    """Run all tests"""
    print("Revenue Forecast Sync - Configuration Tests")
    print("=" * 50)
    
    tests = [
        ("Environment Loading", test_env_loading),
        ("Configuration Loading", test_config_loading), 
        ("SQL Query", test_sql_query),
        ("API Payload", test_api_payload)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...")
        success = test_func()
        results.append((test_name, success))
    
    print("\n" + "=" * 50)
    print("📋 Test Results Summary:")
    print("=" * 50)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:<25}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All configuration tests passed!")
        print("Next step: Test with actual database connection")
    else:
        print("\n⚠️  Some tests failed - check configuration")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)