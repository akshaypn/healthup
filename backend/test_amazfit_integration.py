#!/usr/bin/env python3
"""
Test script for Amazfit integration endpoints
"""

import requests
import json
from datetime import datetime, date

# Configuration
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "your-test-email@example.com"  # Replace with actual test credentials
TEST_PASSWORD = "your-test-password"

def test_amazfit_connect():
    """Test connecting Amazfit account"""
    print("Testing Amazfit account connection...")
    
    url = f"{BASE_URL}/amazfit/connect"
    data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_get_day_data():
    """Test getting day data"""
    print("\nTesting get day data...")
    
    today = date.today().strftime("%Y-%m-%d")
    url = f"{BASE_URL}/amazfit/day?date_str={today}"
    
    try:
        response = requests.get(url)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Steps: {data.get('steps', 0)}")
            print(f"Calories: {data.get('calories', 0)}")
            print(f"Sleep duration: {data.get('sleep_duration', 0)} seconds")
            print(f"Heart rate samples: {len(data.get('heart_rate', []))}")
        else:
            print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_refresh_token():
    """Test token refresh"""
    print("\nTesting token refresh...")
    
    url = f"{BASE_URL}/amazfit/refresh-token"
    
    try:
        response = requests.post(url)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("Amazfit Integration Test")
    print("=" * 50)
    
    # Test connection
    connect_success = test_amazfit_connect()
    
    if connect_success:
        # Test getting day data
        test_get_day_data()
        
        # Test token refresh
        test_refresh_token()
    else:
        print("Connection failed, skipping other tests")
    
    print("\nTest completed!")

if __name__ == "__main__":
    main() 