#!/usr/bin/env python3
"""
Test the authenticated /amazfit/day endpoint
"""

import requests
import json
from datetime import date

BASE_URL = "http://100.123.199.100:8000"

def test_authenticated_amazfit():
    """Test the /amazfit/day endpoint with authentication"""
    print("Testing authenticated /amazfit/day endpoint...")
    
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
                # Show some sample heart rate data
                hr_data = data.get('heart_rate', [])
                non_zero_hr = [hr for hr in hr_data if hr > 0]
                if non_zero_hr:
                    print(f"Sample heart rate values: {non_zero_hr[:10]}")
            else:
                print("⚠ No activity data for today (this is normal if no activity)")
                
        elif response.status_code == 401:
            print("⚠ Authentication failed - cookies may be expired")
        elif response.status_code == 404:
            print("⚠ Amazfit account not connected")
        else:
            print(f"✗ Unexpected status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    test_authenticated_amazfit() 