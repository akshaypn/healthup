#!/usr/bin/env python3
"""
Test the /amazfit/day endpoint to verify it's working correctly
"""

import requests
import json
from datetime import date

BASE_URL = "http://100.123.199.100:8000"

def test_amazfit_day_endpoint():
    """Test the /amazfit/day endpoint"""
    print("Testing /amazfit/day endpoint...")
    
    # Test with today's date
    today = date.today().strftime("%Y-%m-%d")
    
    try:
        response = requests.get(f"{BASE_URL}/amazfit/day?date_str={today}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✓ Endpoint working!")
            print(f"Date: {data.get('date')}")
            print(f"Heart rate samples: {len(data.get('heart_rate', []))}")
            print(f"Steps: {data.get('steps', 0)}")
            print(f"Calories: {data.get('calories', 0)}")
            print(f"Sleep duration: {data.get('sleep_duration', 0)} seconds")
            
            # Check if we have meaningful data
            has_data = (len(data.get('heart_rate', [])) > 0 or 
                       data.get('steps', 0) > 0 or 
                       data.get('calories', 0) > 0)
            
            if has_data:
                print("✓ Data found!")
            else:
                print("⚠ No activity data for today (this is normal if no activity)")
                
        elif response.status_code == 401:
            print("⚠ Requires authentication (expected)")
        elif response.status_code == 404:
            print("⚠ Amazfit account not connected")
        else:
            print(f"✗ Unexpected status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    test_amazfit_day_endpoint() 