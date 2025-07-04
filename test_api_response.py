#!/usr/bin/env python3
"""
Test the actual API response to see what data is being returned
"""

import requests
import json
from datetime import date

BASE_URL = "http://100.123.199.100:8000"

def test_api_response():
    """Test the actual API response"""
    print("Testing API response...")
    
    # Load cookies from the existing session
    try:
        with open('cookies.txt', 'r') as f:
            cookies = {}
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    cookies[key] = value
    except FileNotFoundError:
        print("No cookies.txt found. Please log in first.")
        return
    
    # Test with today's date
    today = date.today().strftime("%Y-%m-%d")
    
    try:
        response = requests.get(
            f"{BASE_URL}/amazfit/day?date_str={today}",
            cookies=cookies
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✓ API Response:")
            print(json.dumps(data, indent=2))
            
            # Analyze the data
            print("\n📊 Data Analysis:")
            print(f"Date: {data.get('date')}")
            print(f"Heart rate array length: {len(data.get('heart_rate', []))}")
            print(f"Steps: {data.get('steps')}")
            print(f"Calories: {data.get('calories')}")
            print(f"Sleep duration: {data.get('sleep_duration')}")
            
            # Check heart rate data
            hr_data = data.get('heart_rate', [])
            if hr_data:
                non_zero_hr = [hr for hr in hr_data if hr > 0]
                print(f"Non-zero HR values: {len(non_zero_hr)}")
                if non_zero_hr:
                    print(f"HR range: {min(non_zero_hr)} - {max(non_zero_hr)} BPM")
                    print(f"Sample HR values: {non_zero_hr[:10]}")
                else:
                    print("⚠ No valid heart rate data found")
            else:
                print("⚠ No heart rate data array")
                
        elif response.status_code == 401:
            print("⚠ Authentication failed - cookies may be expired")
        else:
            print(f"✗ Unexpected status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    test_api_response() 