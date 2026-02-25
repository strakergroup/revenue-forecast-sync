#!/usr/bin/env python3
"""
API Endpoint Test - OptiQo API direct test
"""

import os
import json
import requests
from dotenv import load_dotenv

def test_api_endpoints():
    """Test various API endpoints to identify the issue"""
    load_dotenv('.env')
    
    app_url = os.getenv('APP_URL', 'https://optiqo.straker.co')
    api_key = os.getenv('BOOKINGS_SYNC_API_KEY')
    
    print(f"Testing API endpoints for: {app_url}")
    print(f"API Key: {api_key[:8]}...{api_key[-4:]}")
    
    # Test endpoints to try
    test_endpoints = [
        "/",
        "/health",
        "/api/health", 
        "/api/sync/bookings",
        "/api/v1/revenue-forecast"
    ]
    
    for endpoint in test_endpoints:
        url = f"{app_url.rstrip('/')}{endpoint}"
        print(f"\n🔍 Testing: {url}")
        
        try:
            # Try GET first
            response = requests.get(url, timeout=10, headers={"X-Api-Key": api_key})
            print(f"  GET {response.status_code}: {response.reason}")
            if response.status_code < 500:
                print(f"  Response: {response.text[:200]}")
            
        except requests.exceptions.Timeout:
            print(f"  GET: ⏰ Timeout")
        except requests.exceptions.ConnectionError as e:
            print(f"  GET: 🔌 Connection Error - {e}")
        except Exception as e:
            print(f"  GET: ❌ Error - {e}")
    
    # Test POST to /api/sync/bookings specifically
    url = f"{app_url.rstrip('/')}/api/sync/bookings"
    print(f"\n📤 Testing POST: {url}")
    
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
    
    try:
        response = requests.post(
            url,
            json=test_payload,
            headers={
                "X-Api-Key": api_key,
                "Content-Type": "application/json",
            },
            timeout=30,
        )
        
        print(f"  POST {response.status_code}: {response.reason}")
        print(f"  Headers: {dict(response.headers)}")
        
        if response.status_code == 504:
            print("  ⚠️  Gateway Timeout - API server may be down or overwhelmed")
        elif response.status_code == 503:
            print("  ⚠️  Service Unavailable")
        elif response.status_code == 401:
            print("  🔑 Authentication issue")
        elif response.status_code == 404:
            print("  📍 Endpoint not found")
        else:
            print(f"  Response: {response.text[:500]}")
            
    except requests.exceptions.Timeout:
        print(f"  POST: ⏰ Timeout after 30s")
    except Exception as e:
        print(f"  POST: ❌ Error - {e}")

if __name__ == "__main__":
    test_api_endpoints()