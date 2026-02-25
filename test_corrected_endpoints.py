#!/usr/bin/env python3
"""
Test Correct API Endpoints
"""

import os
import json
import requests
from dotenv import load_dotenv

def test_corrected_endpoints():
    """Test the corrected API endpoints"""
    load_dotenv('.env')
    
    app_url = os.getenv('APP_URL', 'https://optiqo.straker.co')
    api_key = os.getenv('BOOKINGS_SYNC_API_KEY')
    
    print(f"Testing corrected endpoints for: {app_url}")
    
    # Test the corrected endpoints based on previous message
    test_endpoints = [
        "/api/sync",           # Recommended in previous message
        "/api/sync/bookings",  # Current (problematic)
        "/webhook",            # Alternative webhook endpoint
        "/api/webhook"         # Alternative API webhook
    ]
    
    test_payload = {
        "data": [
            {
                "Customer": "API_TEST_CLIENT", 
                "TJ": "TJ_API_TEST_001",
                "Date": "2026-02-25T12:00:00",
                "Status": "test"
            }
        ]
    }
    
    for endpoint in test_endpoints:
        url = f"{app_url.rstrip('/')}{endpoint}"
        print(f"\n📤 Testing POST: {url}")
        
        try:
            response = requests.post(
                url,
                json=test_payload,
                headers={
                    "X-API-KEY": api_key,  # Try both header formats
                    "X-Api-Key": api_key,
                    "Content-Type": "application/json",
                },
                timeout=30,
            )
            
            print(f"  Status: {response.status_code} - {response.reason}")
            
            if response.status_code == 200:
                print(f"  ✅ SUCCESS: {response.text[:200]}")
                return endpoint  # Return successful endpoint
            elif response.status_code == 404:
                print(f"  📍 Not Found - Endpoint doesn't exist")
            elif response.status_code == 401:
                print(f"  🔑 Auth issue - Check API key format")
            elif response.status_code == 504:
                print(f"  ⏰ Gateway Timeout - Same as before")
            elif response.status_code == 503:
                print(f"  🔧 Service Unavailable")
            else:
                print(f"  Response: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            print(f"  ⏰ Timeout")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    return None

if __name__ == "__main__":
    successful_endpoint = test_corrected_endpoints()
    if successful_endpoint:
        print(f"\n🎉 Found working endpoint: {successful_endpoint}")
    else:
        print(f"\n⚠️  No working endpoint found")