#!/usr/bin/env python3
"""
Complete Amazfit Integration Test
Use this script to test the full integration with fresh credentials
"""

import sys
import os
import requests
import json
from datetime import date, datetime
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

# Import the updated service
from amazfit_service import AmazfitService, AmazfitDataSync
from database import get_db
from models import AmazfitCredentials, ActivityData, StepsData, HRSession

# Configuration - UPDATE THESE WITH YOUR FRESH CREDENTIALS
FRESH_APP_TOKEN = "YOUR_FRESH_APP_TOKEN_HERE"
FRESH_USER_ID = "YOUR_FRESH_USER_ID_HERE"
TEST_USER_ID = "test-user-uuid"  # This will be your backend user ID
TEST_DATE = "2025-07-02"

def test_amazfit_service():
    """Test the Amazfit service with fresh credentials"""
    print("=== Testing Amazfit Service ===")
    print(f"App Token: {FRESH_APP_TOKEN[:20] if FRESH_APP_TOKEN != 'YOUR_FRESH_APP_TOKEN_HERE' else 'NOT_SET'}...")
    print(f"User ID: {FRESH_USER_ID}")
    print(f"Test Date: {TEST_DATE}")
    print()
    
    if FRESH_APP_TOKEN == "YOUR_FRESH_APP_TOKEN_HERE":
        print("⚠️  Please update FRESH_APP_TOKEN and FRESH_USER_ID with your actual credentials")
        return False
    
    # Initialize the service
    service = AmazfitService(app_token=FRESH_APP_TOKEN, user_id=FRESH_USER_ID)
    test_date = date.fromisoformat(TEST_DATE)
    
    try:
        # Test 1: Get band data
        print("1. Testing band data retrieval...")
        band_data = service.get_band_data(test_date)
        print(f"   ✓ Band data retrieved successfully")
        print(f"   - Data entries: {len(band_data.get('data', []))}")
        
        if band_data.get('data'):
            first_entry = band_data['data'][0]
            print(f"   - Has summary: {'summary' in first_entry}")
            print(f"   - Has HR data: {'data_hr' in first_entry}")
        
        # Test 2: Decode summary
        print("\n2. Testing summary decoding...")
        decoded_summary = service.decode_band_summary(band_data)
        print(f"   ✓ Summary decoded successfully")
        print(f"   - Summary keys: {list(decoded_summary.keys())}")
        
        # Test 3: Extract activity data
        if 'stp' in decoded_summary:
            stp = decoded_summary['stp']
            steps = stp.get('ttl', 0)
            calories = stp.get('cal', 0)
            print(f"   - Steps: {steps}")
            print(f"   - Calories: {calories}")
        
        # Test 4: Extract sleep data
        if 'slp' in decoded_summary:
            slp = decoded_summary['slp']
            print(f"   - Sleep keys: {list(slp.keys())}")
            if 'st' in slp and 'ed' in slp:
                sleep_duration = slp['ed'] - slp['st']
                print(f"   - Sleep duration: {sleep_duration} seconds ({sleep_duration//60} minutes)")
        
        # Test 5: Decode heart rate data
        print("\n3. Testing heart rate data decoding...")
        if band_data.get('data') and 'data_hr' in band_data['data'][0]:
            hr_blob = band_data['data'][0]['data_hr']
            hr_values = service.decode_hr_blob(hr_blob)
            print(f"   ✓ Heart rate data decoded successfully")
            print(f"   - Total readings: {len(hr_values)}")
            
            non_zero = [v for v in hr_values if v > 0]
            if non_zero:
                print(f"   - Sample HR values: {non_zero[:10]}")
                print(f"   - Valid readings: {len(non_zero)}")
                print(f"   - Average HR: {sum(non_zero) // len(non_zero)}")
                print(f"   - Max HR: {max(non_zero)}")
                print(f"   - Min HR: {min(non_zero)}")
            else:
                print("   - No valid heart rate data found")
        
        # Test 6: Get daily summary
        print("\n4. Testing daily summary...")
        daily_summary = service.get_daily_summary(test_date)
        print(f"   ✓ Daily summary retrieved successfully")
        print(f"   - Summary keys: {list(daily_summary.keys())}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_integration():
    """Test the database integration (requires database connection)"""
    print("\n=== Testing Database Integration ===")
    
    try:
        # Get database session
        db = next(get_db())
        
        # Test 1: Create Amazfit credentials
        print("1. Testing credentials creation...")
        credentials = AmazfitCredentials(
            user_id=TEST_USER_ID,
            app_token=FRESH_APP_TOKEN,
            user_id_amazfit=FRESH_USER_ID
        )
        db.add(credentials)
        db.commit()
        print("   ✓ Credentials created successfully")
        
        # Test 2: Test data sync
        print("\n2. Testing data sync...")
        sync_service = AmazfitDataSync(db, TEST_USER_ID)
        results = sync_service.sync_activity_data(days_back=1)
        print(f"   ✓ Data sync completed: {results} records synced")
        
        # Test 3: Check synced data
        print("\n3. Checking synced data...")
        activity_data = db.query(ActivityData).filter(
            ActivityData.user_id == TEST_USER_ID
        ).all()
        print(f"   - Activity records: {len(activity_data)}")
        
        steps_data = db.query(StepsData).filter(
            StepsData.user_id == TEST_USER_ID
        ).all()
        print(f"   - Steps records: {len(steps_data)}")
        
        hr_sessions = db.query(HRSession).filter(
            HRSession.user_id == TEST_USER_ID
        ).all()
        print(f"   - HR sessions: {len(hr_sessions)}")
        
        # Clean up test data
        print("\n4. Cleaning up test data...")
        db.query(AmazfitCredentials).filter(
            AmazfitCredentials.user_id == TEST_USER_ID
        ).delete()
        db.query(ActivityData).filter(
            ActivityData.user_id == TEST_USER_ID
        ).delete()
        db.query(StepsData).filter(
            StepsData.user_id == TEST_USER_ID
        ).delete()
        db.query(HRSession).filter(
            HRSession.user_id == TEST_USER_ID
        ).delete()
        db.commit()
        print("   ✓ Test data cleaned up")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoints():
    """Test the API endpoints (requires running backend)"""
    print("\n=== Testing API Endpoints ===")
    
    BASE_URL = "http://localhost:8000"
    TEST_EMAIL = "admin@admin.com"
    TEST_PASSWORD = "123456"
    
    try:
        # Test 1: Login
        print("1. Testing login...")
        response = requests.post(f"{BASE_URL}/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if response.status_code != 200:
            print(f"   ✗ Login failed: {response.status_code}")
            return False
        
        access_token = response.json()["access_token"]
        print("   ✓ Login successful")
        
        # Test 2: Setup credentials
        print("\n2. Testing credentials setup...")
        headers = {"Authorization": f"Bearer {access_token}"}
        credentials_data = {
            "app_token": FRESH_APP_TOKEN,
            "user_id_amazfit": FRESH_USER_ID
        }
        
        response = requests.post(f"{BASE_URL}/amazfit/credentials", 
                               json=credentials_data, headers=headers)
        
        if response.status_code == 200:
            print("   ✓ Credentials saved successfully")
        else:
            print(f"   ✗ Credentials setup failed: {response.status_code}")
            return False
        
        # Test 3: Sync data
        print("\n3. Testing data sync...")
        sync_data = {
            "sync_activity": True,
            "sync_steps": True,
            "sync_heart_rate": True,
            "sync_sleep": True,
            "days_back": 1
        }
        
        response = requests.post(f"{BASE_URL}/amazfit/sync", 
                               json=sync_data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print("   ✓ Sync completed successfully")
            print(f"   - Activity records: {result.get('activity_synced', 0)}")
            print(f"   - Steps records: {result.get('steps_synced', 0)}")
            print(f"   - Heart rate records: {result.get('heart_rate_synced', 0)}")
            print(f"   - Sleep records: {result.get('sleep_synced', 0)}")
        else:
            print(f"   ✗ Sync failed: {response.status_code}")
            return False
        
        # Test 4: Get activity data
        print("\n4. Testing activity data retrieval...")
        response = requests.get(f"{BASE_URL}/amazfit/activity?limit=7", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Retrieved {len(data)} activity records")
        else:
            print(f"   ✗ Activity retrieval failed: {response.status_code}")
            return False
        
        return True
        
    except Exception as e:
        print(f"\n✗ API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("=== Complete Amazfit Integration Test ===")
    print()
    
    # Test 1: Service functionality
    service_success = test_amazfit_service()
    
    if not service_success:
        print("\n⚠️  Service test failed. Please check your credentials.")
        return
    
    # Test 2: Database integration (optional)
    print("\n" + "="*50)
    db_success = test_database_integration()
    
    # Test 3: API endpoints (optional)
    print("\n" + "="*50)
    api_success = test_api_endpoints()
    
    # Summary
    print("\n" + "="*50)
    print("=== Test Summary ===")
    print(f"Service Test: {'✓ PASSED' if service_success else '✗ FAILED'}")
    print(f"Database Test: {'✓ PASSED' if db_success else '✗ FAILED'}")
    print(f"API Test: {'✓ PASSED' if api_success else '✗ FAILED'}")
    
    if service_success:
        print("\n🎉 Amazfit integration is working!")
        print("You can now use the API endpoints to sync and retrieve data.")
    else:
        print("\n❌ Please fix the issues above before proceeding.")

if __name__ == "__main__":
    main() 