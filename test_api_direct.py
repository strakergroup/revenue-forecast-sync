#!/usr/bin/env python3
"""
OptiQo API Test - Direct API call test
Tests the /api/sync/bookings endpoint directly
"""

import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

def test_api_connection():
    """Test direct API connection to OptiQo"""
    load_dotenv('.env')
    
    app_url = os.getenv('APP_URL', 'https://optiqo.straker.co')
    api_key = os.getenv('BOOKINGS_SYNC_API_KEY')
    
    if not api_key:
        print("❌ API key not found")
        return False
    
    # Sample test data
    test_data = [
        {
            'Customer': 'API Test Client',
            'Group': 'Test Group',
            'Entity': 'Test Entity',
            'TJ': 'TJ_TEST_001',
            'Date': '2026-02-25T10:00:00',
            'TJAmount (in Sales Order currency)': 100.00,
            'TJAmount nett (in Sales Order currency)': 90.00,
            'Currency': 'USD',
            'Expected Due Date': '2026-03-01T00:00:00',
            'Status': 'test',
            'Completed Date': None,
            'WIP % (i believe this is calculated at the last month end.)': 0.0,
            'Gross Margin': 10.0
        }
    ]
    
    url = f"{app_url.rstrip('/')}/api/sync/bookings"
    payload = {"data": test_data}
    
    print(f"🔍 Testing API endpoint: {url}")
    print(f"🔑 API Key: {api_key[:8]}...{api_key[-4:]}")
    print(f"📦 Test records: {len(test_data)}")
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers={
                "X-Api-Key": api_key,
                "Content-Type": "application/json",
            },
            timeout=30,
        )
        
        print(f"📡 Response Status: {response.status_code}")
        print(f"📄 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ API call successful!")
            print(f"📊 Response: {json.dumps(result, indent=2)}")
            return True
        elif response.status_code == 401:
            print("❌ Authentication failed - check API key")
            print(f"Response: {response.text}")
            return False
        elif response.status_code == 503:
            print("❌ Service unavailable - API key not configured on server")
            print(f"Response: {response.text}")
            return False
        else:
            print(f"❌ API call failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - server unreachable")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timeout")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("OptiQo API Direct Test")
    print("=" * 30)
    success = test_api_connection()
    print("\n" + "=" * 30)
    if success:
        print("🎉 API test successful!")
    else:
        print("⚠️  API test failed")