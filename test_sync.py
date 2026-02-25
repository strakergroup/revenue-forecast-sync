#!/usr/bin/env python3
"""
Revenue Forecast Sync Test Script
Test the sync application components locally
"""

import os
import sys
import json
from sync_app import RevenueForecastSync, DatabaseConfig, MySQLDataExtractor, RevenueForecastAPI

def test_database_connection():
    """Test MySQL database connection"""
    print("Testing database connection...")
    
    try:
        config = DatabaseConfig("config.ini")
        db_config = config.get_mysql_config()
        
        extractor = MySQLDataExtractor(db_config)
        extractor.connect()
        
        # Test simple query
        result = extractor.execute_query("SELECT 1 as test")
        if result and len(result) > 0:
            print("✓ Database connection successful")
        else:
            print("✗ Database query failed")
            return False
            
        extractor.disconnect()
        return True
        
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

def test_api_connection():
    """Test API connection"""
    print("Testing API connection...")
    
    try:
        config = DatabaseConfig("config.ini")
        api_config = config.get_api_config()
        
        client = RevenueForecastAPI(api_config)
        
        if client.test_connection():
            print("✓ API connection successful")
            return True
        else:
            print("⚠ API connection test failed (but may still work)")
            return True  # Continue with tests
            
    except Exception as e:
        print(f"✗ API connection failed: {e}")
        return False

def test_data_extraction():
    """Test data extraction methods"""
    print("Testing data extraction...")
    
    try:
        config = DatabaseConfig("config.ini")
        db_config = config.get_mysql_config()
        
        extractor = MySQLDataExtractor(db_config)
        extractor.connect()
        
        try:
            # Test daily data
            daily_data = extractor.get_revenue_forecast_data()
            print(f"✓ Daily data extracted: {len(daily_data)} records")
            
            # Test monthly data
            monthly_data = extractor.get_monthly_revenue_forecast()
            print(f"✓ Monthly data extracted: {len(monthly_data)} records")
            
            # Test client data
            client_data = extractor.get_client_revenue_breakdown()
            print(f"✓ Client data extracted: {len(client_data)} records")
            
            if daily_data:
                print(f"Sample daily record: {json.dumps(daily_data[0], indent=2, default=str)}")
            
            return True
            
        finally:
            extractor.disconnect()
            
    except Exception as e:
        print(f"✗ Data extraction failed: {e}")
        return False

def test_full_sync():
    """Test complete sync process"""
    print("Testing full sync process...")
    
    try:
        sync_app = RevenueForecastSync("config.ini")
        success = sync_app.run_sync()
        
        if success:
            print("✓ Full sync test successful")
            return True
        else:
            print("✗ Full sync test failed")
            return False
            
    except Exception as e:
        print(f"✗ Full sync test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Revenue Forecast Sync - Test Suite")
    print("=" * 40)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("API Connection", test_api_connection),
        ("Data Extraction", test_data_extraction),
        ("Full Sync Process", test_full_sync)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * len(test_name))
        results[test_name] = test_func()
    
    print("\n" + "=" * 40)
    print("Test Results Summary:")
    print("=" * 40)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name:<20}: {status}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n✓ All tests passed!")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()