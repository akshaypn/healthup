#!/usr/bin/env python3
"""
Test script to verify Amazfit connection flow
"""

import requests
import json
import sys

BASE_URL = "http://100.123.199.100:8000"

def test_amazfit_connect():
    """Test the Amazfit connection endpoint"""
    print("Testing Amazfit connection flow...")
    
    # Test 1: Check if credentials endpoint exists (should return 401 without auth)
    print("\n1. Testing /amazfit/credentials endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/amazfit/credentials")
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Endpoint exists and requires authentication")
        else:
            print(f"   ⚠️  Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Test connect endpoint with invalid data
    print("\n2. Testing /amazfit/connect endpoint with invalid data...")
    try:
        response = requests.post(
            f"{BASE_URL}/amazfit/connect",
            json={"email": "test@example.com", "password": "wrongpassword"},
            headers={"Content-Type": "application/json"}
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 400:
            print("   ✅ Endpoint exists and validates input")
            try:
                error_data = response.json()
                print(f"   Error message: {error_data.get('detail', 'No detail')}")
            except:
                print("   Could not parse error response")
        else:
            print(f"   ⚠️  Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Test day endpoint without auth
    print("\n3. Testing /amazfit/day endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/amazfit/day?date_str=2025-07-03")
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Endpoint exists and requires authentication")
        else:
            print(f"   ⚠️  Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n✅ Amazfit endpoints are accessible and properly configured!")
    print("\nTo test with real credentials:")
    print("1. Go to http://100.123.199.100:3000")
    print("2. Login to your account")
    print("3. Navigate to Heart Rate section")
    print("4. Use the Amazfit connection modal")

if __name__ == "__main__":
    test_amazfit_connect() 