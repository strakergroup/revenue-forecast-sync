#!/usr/bin/env python3
"""
Revenue Forecast Sync - Mock Test
Tests the application flow with mocked MySQL and API calls
"""

import os
import sys
import json
from datetime import datetime, date
from unittest.mock import MagicMock, patch

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def mock_mysql_data():
    """Generate mock data similar to actual database results"""
    return [
        {
            'Customer': 'Acme Corp',
            'Group': 'Enterprise',
            'Entity': 'Straker US',
            'TJ': 'TJ123456',
            'Date': datetime(2026, 2, 20),
            'TJAmount (in Sales Order currency)': 2500.50,
            'TJAmount nett (in Sales Order currency)': 2000.40,
            'Currency': 'USD',
            'Expected Due Date': datetime(2026, 3, 1),
            'Status': 'completed',
            'Completed Date': datetime(2026, 2, 22),
            'WIP % (i believe this is calculated at the last month end.)': 100.0,
            'Gross Margin': 25.5
        },
        {
            'Customer': 'Global Tech Ltd',
            'Group': 'SMB',
            'Entity': 'Straker APAC',
            'TJ': 'TJ123457',
            'Date': datetime(2026, 2, 21),
            'TJAmount (in Sales Order currency)': 1200.00,
            'TJAmount nett (in Sales Order currency)': 1000.00,
            'Currency': 'EUR',
            'Expected Due Date': datetime(2026, 3, 5),
            'Status': 'in_progress',
            'Completed Date': None,
            'WIP % (i believe this is calculated at the last month end.)': 65.0,
            'Gross Margin': 20.0
        },
        {
            'Customer': 'StartupXYZ',
            'Group': 'Startup',
            'Entity': 'Straker EU',
            'TJ': 'TJ123458',
            'Date': datetime(2026, 2, 22),
            'TJAmount (in Sales Order currency)': 750.00,
            'TJAmount nett (in Sales Order currency)': 650.00,
            'Currency': 'GBP',
            'Expected Due Date': datetime(2026, 3, 10),
            'Status': 'quoted',
            'Completed Date': None,
            'WIP % (i believe this is calculated at the last month end.)': 0.0,
            'Gross Margin': 15.5
        }
    ]

def test_full_workflow():
    """Test the complete sync workflow with mocks"""
    print("=== Full Workflow Test (Mocked) ===")
    
    try:
        # Mock MySQL connector
        mock_mysql = MagicMock()
        mock_connector = MagicMock()
        mock_cursor = MagicMock()
        
        # Set up mock responses
        mock_data = mock_mysql_data()
        mock_cursor.fetchall.return_value = mock_data
        mock_connector.cursor.return_value = mock_cursor
        mock_mysql.connect.return_value = mock_connector
        
        # Mock requests for API calls
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "inserted": 3,
            "updated": 0,
            "message": "Data processed successfully"
        }
        
        with patch('mysql.connector', mock_mysql), \
             patch('requests.post', return_value=mock_response) as mock_post:
            
            # Import after patching
            from sync_app import run, load_config
            
            print("🔧 Setting up test environment...")
            load_config()
            
            print("📊 Running sync with mock data...")
            
            # Test dry run first
            print("\n--- DRY RUN TEST ---")
            success_dry = run(full_refresh=True, dry_run=True)
            print(f"Dry run result: {'✅ SUCCESS' if success_dry else '❌ FAILED'}")
            
            # Test actual run (still mocked)
            print("\n--- ACTUAL RUN TEST (MOCKED) ---") 
            success_real = run(full_refresh=True, dry_run=False)
            print(f"Actual run result: {'✅ SUCCESS' if success_real else '❌ FAILED'}")
            
            # Verify MySQL connection was attempted
            mysql_connect_called = mock_mysql.connect.called
            print(f"MySQL connection attempted: {'✅ YES' if mysql_connect_called else '❌ NO'}")
            
            # Verify query execution
            query_executed = mock_cursor.execute.called
            print(f"Query executed: {'✅ YES' if query_executed else '❌ NO'}")
            
            # Verify API call (only in non-dry run)
            api_called = mock_post.called
            print(f"API call made: {'✅ YES' if api_called else '❌ NO'}")
            
            if api_called:
                # Check API call details
                call_args = mock_post.call_args
                url = call_args[1]['json']['data'] if call_args else None
                print(f"API payload records: {len(url) if url else 0}")
            
            return success_dry and success_real and mysql_connect_called and query_executed
            
    except Exception as e:
        print(f"❌ Error in workflow test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_scenarios():
    """Test error handling scenarios"""
    print("\n=== Error Scenario Tests ===")
    
    results = []
    
    # Test 1: MySQL connection failure
    try:
        with patch('mysql.connector.connect', side_effect=Exception("Connection failed")):
            from sync_app import run
            success = run(full_refresh=True, dry_run=True)
            results.append(("MySQL Connection Error", not success))  # Should fail gracefully
    except SystemExit:
        results.append(("MySQL Connection Error", True))  # Expected to exit
    except Exception as e:
        results.append(("MySQL Connection Error", False))
    
    # Test 2: API authentication failure
    try:
        mock_mysql = MagicMock()
        mock_connector = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = mock_mysql_data()
        mock_connector.cursor.return_value = mock_cursor
        mock_mysql.connect.return_value = mock_connector
        
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = Exception("Authentication failed")
        
        with patch('mysql.connector', mock_mysql), \
             patch('requests.post', return_value=mock_response):
            
            from sync_app import run
            success = run(full_refresh=True, dry_run=False)
            results.append(("API Auth Error", not success))  # Should handle gracefully
    except SystemExit:
        results.append(("API Auth Error", True))  # Expected to exit on auth failure
    except Exception as e:
        results.append(("API Auth Error", False))
    
    return results

def main():
    """Run all mock tests"""
    print("Revenue Forecast Sync - Mock Integration Tests")
    print("=" * 55)
    
    # Test full workflow
    workflow_success = test_full_workflow()
    
    # Test error scenarios  
    error_results = test_error_scenarios()
    
    print("\n" + "=" * 55)
    print("📋 Test Results Summary:")
    print("=" * 55)
    
    print(f"Full Workflow Test: {'✅ PASS' if workflow_success else '❌ FAIL'}")
    
    for test_name, success in error_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:<20}: {status}")
    
    all_passed = workflow_success and all(result[1] for result in error_results)
    
    if all_passed:
        print("\n🎉 All mock tests passed!")
        print("✅ Application logic works correctly")
        print("✅ Error handling is functional")
        print("\nNext steps:")
        print("- Test with real database (requires mysql-connector-python)")
        print("- Deploy to Kubernetes for production testing")
    else:
        print("\n⚠️  Some tests failed - check application logic")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)