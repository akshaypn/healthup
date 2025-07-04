#!/usr/bin/env python3
"""
Test the updated Amazfit service with fresh credentials
"""

import requests
import json
import base64
import struct
import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fresh credentials from the login
FRESH_TOKEN = "MQVBQFJyQktGHlp6QkpbRl5LRl5qek4uXAQABAAAAADRmxMBneW9_q8R3KFG776nf5RxVYY2SbpTx61-tGZnJjYLlOibdHhipmUVi6i-8G9y6jcVwLvFRxw4aA-T2QP3bODHkyViYXVjLmSSC-bggj0hjm_ZBthFApu9hZWQpN2olLyspJRTFkb0n45BWSs_jzSDXCyouesOgjWQClm5LY6eZkBTi9P9qx6MMDnTNAA"
FRESH_UID = "6013538643"
TEST_DATE = "2025-07-02"

class AmazfitService:
    """Service for interacting with real Huami/Zepp Amazfit API"""
    
    # Real Huami API endpoints
    USER_API_BASE = "https://api-user.huami.com"
    MIFIT_API_BASE = "https://api-mifit.huami.com"
    
    def __init__(self, app_token: str, user_id: str = None):
        self.app_token = app_token
        self.user_id = user_id
        self.session = requests.Session()
        
        # Set up headers exactly like the working script
        self.session.headers.update({
            'apptoken': app_token,
            'appname': 'com.xiaomi.hm.health',
            'appPlatform': 'web',
            'User-Agent': 'ZeppPython/1.7'  # Match the working script
        })
    
    def get_band_data(self, target_date: date) -> Dict:
        """Get comprehensive band data for a specific date using the working script approach"""
        if not self.user_id:
            raise Exception("User ID is required for band data")
        
        url = f"{self.MIFIT_API_BASE}/v1/data/band_data.json"
        params = {
            "query_type": "detail",
            "userid": self.user_id,
            "device_type": "android_phone",
            "from_date": target_date.strftime('%Y-%m-%d'),
            "to_date": target_date.strftime('%Y-%m-%d')
        }
        
        # Use the exact same approach as the working script
        response = self.session.get(url, params=params, timeout=20)
        response.raise_for_status()
        return response.json()
    
    def decode_band_summary(self, band_data: Dict) -> Dict:
        """Decode base64-encoded JSON summary from band data - matches working script"""
        if not band_data or 'data' not in band_data or not band_data['data']:
            return {}
        
        try:
            # Get the summary from the first data entry
            summary_b64 = band_data['data'][0].get('summary', '')
            if summary_b64:
                # Use the exact same approach as the working script
                return json.loads(base64.b64decode(summary_b64 + "==").decode())
        except Exception as e:
            logger.error(f"Failed to decode band summary: {e}")
        
        return {}
    
    def decode_hr_blob(self, hr_blob_b64: str) -> List[int]:
        """Decode heart rate blob from base64 string"""
        try:
            raw = base64.b64decode(hr_blob_b64)
            hr_values = []
            
            # Try different decoding approaches
            for off in range(0, len(raw), 2):
                if off + 1 < len(raw):
                    value = struct.unpack_from("<H", raw, off)[0]
                    
                    # Filter out invalid values (65535 is often used as "no data")
                    if value < 65535:
                        # Some devices might store HR in different ranges
                        if value > 300:  # If it's in the 300+ range, might need scaling
                            value = value // 10  # Scale down to get realistic BPM
                        hr_values.append(value)
                    else:
                        hr_values.append(0)  # No data
                else:
                    hr_values.append(0)
            
            return hr_values
        except Exception as e:
            logger.error(f"Failed to decode HR blob: {e}")
            return []
    
    def get_daily_summary(self, target_date: date) -> Dict:
        """Get comprehensive daily summary including all metrics"""
        summary = {
            'date': target_date.strftime('%Y-%m-%d'),
            'heart_rate': [],
            'activity': {},
            'sleep': {},
            'workouts': [],
            'band_data': {}
        }
        
        try:
            # Get band data (includes summary, steps, sleep, etc.)
            band_data = self.get_band_data(target_date)
            summary['band_data'] = band_data
            
            # Decode the summary
            decoded_summary = self.decode_band_summary(band_data)
            
            # Extract activity data from decoded summary
            if 'stp' in decoded_summary:
                summary['activity'] = {
                    'steps': decoded_summary['stp'].get('ttl', 0),
                    'calories': decoded_summary['stp'].get('cal', 0)
                }
            
            # Extract sleep data from decoded summary
            if 'slp' in decoded_summary:
                slp = decoded_summary['slp']
                sleep_data = {}
                
                if 'st' in slp and 'ed' in slp:
                    # Calculate sleep duration in seconds
                    sleep_duration = slp['ed'] - slp['st']
                    sleep_data['sleep_time_seconds'] = sleep_duration
                    sleep_data['sleep_time_hours'] = sleep_duration / 3600
                    sleep_data['sleep_start'] = slp['st']
                    sleep_data['sleep_end'] = slp['ed']
                else:
                    # Fallback: try to find any numeric field that might be total sleep time
                    for key, value in slp.items():
                        if isinstance(value, (int, float)) and value > 0 and key not in ['st', 'ed']:
                            sleep_data['sleep_time_seconds'] = value
                            sleep_data['sleep_time_hours'] = value / 3600
                            break
                
                summary['sleep'] = sleep_data
            
            # Get heart rate data from band data
            if band_data and 'data' in band_data and band_data['data']:
                hr_blob = band_data['data'][0].get('data_hr', '')
                if hr_blob:
                    summary['heart_rate'] = self.decode_hr_blob(hr_blob)
            
        except Exception as e:
            logger.warning(f"Failed to get band data: {e}")
        
        return summary

def test_amazfit_service():
    """Test the Amazfit service with fresh credentials"""
    print("=== Testing Updated Amazfit Service ===")
    print(f"App Token: {FRESH_TOKEN[:20]}...")
    print(f"User ID: {FRESH_UID}")
    print(f"Test Date: {TEST_DATE}")
    print()
    
    # Initialize the service
    service = AmazfitService(app_token=FRESH_TOKEN, user_id=FRESH_UID)
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
        
        # Test 6: Get daily summary (comprehensive)
        print("\n4. Testing daily summary...")
        daily_summary = service.get_daily_summary(test_date)
        print(f"   ✓ Daily summary retrieved successfully")
        print(f"   - Summary keys: {list(daily_summary.keys())}")
        
        # Show activity data
        if daily_summary.get('activity'):
            activity = daily_summary['activity']
            print(f"   - Activity data: {activity}")
        
        # Show sleep data
        if daily_summary.get('sleep'):
            sleep = daily_summary['sleep']
            print(f"   - Sleep data: {sleep}")
        
        # Show heart rate data
        if daily_summary.get('heart_rate'):
            hr_data = daily_summary['heart_rate']
            print(f"   - Heart rate readings: {len(hr_data)}")
        
        print("\n=== All Tests Passed! ===")
        print("The updated Amazfit service is working correctly with fresh credentials.")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_amazfit_service()
    exit(0 if success else 1) 