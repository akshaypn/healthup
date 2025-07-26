#!/usr/bin/env python3
"""
Test Amazfit integration with real credentials
This script tests the actual Amazfit login and data fetching.
"""

import sys
import os
sys.path.append('backend')

from backend.amazfit_login import get_amazfit_token
from backend.amazfit_service import AmazfitService
from datetime import date

def test_amazfit_login():
    """Test the Amazfit login functionality"""
    print("Testing Amazfit Login...")
    
    # You need to replace these with actual credentials
    email = input("Enter your Amazfit email: ")
    password = input("Enter your Amazfit password: ")
    
    try:
        # Test the login
        app_token, user_id = get_amazfit_token(email, password)
        print(f"✓ Login successful!")
        print(f"  App Token: {app_token[:20]}...")
        print(f"  User ID: {user_id}")
        
        # Test the service
        service = AmazfitService(app_token, user_id)
        print(f"✓ Service created successfully")
        
        # Test getting today's data
        today = date.today()
        print(f"\nFetching data for {today}...")
        
        # Get heart rate data
        heart_rate = service.get_heart_rate_data(today)
        print(f"✓ Heart rate data: {len(heart_rate)} samples")
        if heart_rate:
            non_zero = [hr for hr in heart_rate if hr > 0]
            print(f"  Non-zero values: {len(non_zero)}")
            if non_zero:
                print(f"  Sample values: {non_zero[:5]}")
        
        # Get activity data
        activity = service.get_activity_data(today)
        print(f"✓ Activity data retrieved")
        
        # Get sleep data
        sleep = service.get_sleep_data(today)
        print(f"✓ Sleep data retrieved")
        
        # Get band data
        band_data = service.get_band_data(today)
        summary = service.decode_band_summary(band_data)
        print(f"✓ Band data retrieved")
        
        if summary:
            steps = summary.get("stp", {}).get("ttl", 0)
            calories = summary.get("stp", {}).get("cal", 0)
            print(f"  Steps: {steps}")
            print(f"  Calories: {calories}")
        
        print("\n✓ All Amazfit integration tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

def main():
    print("Amazfit Integration Test with Real Credentials")
    print("=" * 50)
    
    success = test_amazfit_login()
    
    if success:
        print("\n" + "=" * 50)
        print("INTEGRATION VERIFIED!")
        print("\nThe backend Amazfit integration is working correctly.")
        print("You can now use the frontend to connect your Amazfit account.")
    else:
        print("\n" + "=" * 50)
        print("INTEGRATION FAILED!")
        print("Please check your credentials and try again.")

if __name__ == "__main__":
    main() 