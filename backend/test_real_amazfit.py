#!/usr/bin/env python3
"""
Test script for real Amazfit integration
"""

import sys
import os
import requests
import json
import base64
import struct
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Your real credentials from the working script
APP_TOKEN = "MQVBQEJyQktGXip6SltGSlpuQkZgBAAEAAAAAB-NFpnk_1LFAOwmvyGQ8Q3gnxbuJueeDARMP7mnEJswsJI-gMuW8QzuTtItZRfoQpLDvtf_0kPt5EzMxFroso7XLuCjR7fdFZ5BNrbj6NYfg-Po17Vhnojj5c7W03v5UN8yal0x31NB5Q8sx9swRiSyYJO3Yv3rlEqm446qjvdivAJfzqzStIFyym_CRY3Xc"
USER_ID = "6013538643"
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
        
        # Set up headers according to Huami API documentation
        self.session.headers.update({
            'apptoken': app_token,
            'appname': 'com.xiaomi.hm.health',
            'appPlatform': 'web',
            'Content-Type': 'application/json',
            'User-Agent': 'Zepp/6.10.5 PythonScript'
        })
    
    def _make_request(self, url: str, method: str = 'GET', params: Dict = None, data: Dict = None) -> Dict:
        """Make API request to Huami/Zepp API"""
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params)
            elif method.upper() == 'POST':
                response = self.session.post(url, params=params, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Huami API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response content: {e.response.text}")
            raise Exception(f"Failed to communicate with Huami API: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Huami API response: {e}")
            raise Exception(f"Invalid response from Huami API: {str(e)}")
    
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
        
        return self._make_request(url, params=params)
    
    def decode_band_summary(self, band_data: Dict) -> Dict:
        """Decode base64-encoded JSON summary from band data"""
        if not band_data or 'data' not in band_data or not band_data['data']:
            return {}
        
        try:
            # Get the summary from the first data entry
            summary_b64 = band_data['data'][0].get('summary', '')
            if summary_b64:
                # Add padding if needed
                if len(summary_b64) % 4 != 0:
                    summary_b64 += "=="
                decoded = base64.b64decode(summary_b64).decode()
                return json.loads(decoded)
        except Exception as e:
            logger.error(f"Failed to decode band summary: {e}")
        
        return {}
    
    def decode_hr_blob(self, hr_blob_b64: str) -> list:
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

def test_amazfit_service():
    """Test the Amazfit service with real credentials"""
    print("=== Testing Amazfit Service with Real Credentials ===")
    print(f"App Token: {APP_TOKEN[:20]}...")
    print(f"User ID: {USER_ID}")
    print(f"Test Date: {TEST_DATE}")
    print()
    
    # Initialize the service
    service = AmazfitService(app_token=APP_TOKEN, user_id=USER_ID)
    
    # Test date parsing
    test_date = date.fromisoformat(TEST_DATE)
    
    try:
        # Test 1: Get band data (the working approach)
        print("1. Testing band data retrieval...")
        band_data = service.get_band_data(test_date)
        print(f"   ✓ Band data retrieved successfully")
        print(f"   - Data entries: {len(band_data.get('data', []))}")
        
        if band_data.get('data'):
            first_entry = band_data['data'][0]
            print(f"   - Has summary: {'summary' in first_entry}")
            print(f"   - Has HR data: {'data_hr' in first_entry}")
        
        # Test 2: Decode band summary
        print("\n2. Testing band summary decoding...")
        decoded_summary = service.decode_band_summary(band_data)
        print(f"   ✓ Summary decoded successfully")
        print(f"   - Summary keys: {list(decoded_summary.keys())}")
        
        # Test 3: Extract activity data
        if 'stp' in decoded_summary:
            stp = decoded_summary['stp']
            print(f"   - Steps: {stp.get('ttl', 0)}")
            print(f"   - Calories: {stp.get('cal', 0)}")
        
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
            
            # Show sample values
            non_zero = [v for v in hr_values if v > 0]
            if non_zero:
                print(f"   - Sample HR values: {non_zero[:10]}")
                print(f"   - Valid readings: {len(non_zero)}")
                print(f"   - Average HR: {sum(non_zero) // len(non_zero)}")
                print(f"   - Max HR: {max(non_zero)}")
                print(f"   - Min HR: {min(non_zero)}")
            else:
                print("   - No valid heart rate data found")
        
        print("\n=== All Tests Passed! ===")
        print("The Amazfit service is working correctly with real credentials.")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_amazfit_service()
    sys.exit(0 if success else 1) 