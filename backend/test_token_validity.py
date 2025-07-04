#!/usr/bin/env python3
"""
Test token validity with different endpoints
"""

import requests
import json

# Your real credentials
TOKEN = "MQVBQEJyQktGXip6SltGSlpuQkZgBAAEAAAAAB-NFpnk_1LFAOwmvyGQ8Q3gnxbuJueeDARMP7mnEJswsJI-gMuW8QzuTtItZRfoQpLDvtf_0kPt5EzMxFroso7XLuCjR7fdFZ5BNrbj6NYfg-Po17Vhnojj5c7W03v5UN8yal0x31NB5Q8sx9swRiSyYJO3Yv3rlEqm446qjvdivAJfzqzStIFyym_CRY3Xc"
UID = "6013538643"

# Different header combinations to try
HEADERS_TO_TEST = [
    {
        "apptoken": TOKEN,
        "appname": "com.xiaomi.hm.health",
        "appPlatform": "web",
        "User-Agent": "Zepp/6.10.5 PythonScript"
    },
    {
        "apptoken": TOKEN,
        "appname": "com.xiaomi.hm.health",
        "appPlatform": "web",
        "User-Agent": "ZeppPython/1.7"
    },
    {
        "apptoken": TOKEN,
        "appname": "com.xiaomi.hm.health",
        "appPlatform": "web",
        "Content-Type": "application/json",
        "User-Agent": "Zepp/6.10.5 PythonScript"
    }
]

# Different endpoints to test
ENDPOINTS_TO_TEST = [
    {
        "name": "User Profile",
        "url": "https://api-user.huami.com/v1/user/profile",
        "params": {}
    },
    {
        "name": "Heart Rate",
        "url": "https://api-user.huami.com/v1/user/fitness/heart_rate",
        "params": {"userid": UID, "date": "2025-07-02"}
    },
    {
        "name": "Activity",
        "url": "https://api-user.huami.com/v1/user/fitness/activity",
        "params": {"userid": UID, "date": "2025-07-02"}
    },
    {
        "name": "Band Data",
        "url": "https://api-mifit.huami.com/v1/data/band_data.json",
        "params": {
            "query_type": "detail",
            "userid": UID,
            "device_type": "android_phone",
            "from_date": "2025-07-02",
            "to_date": "2025-07-02"
        }
    }
]

def test_endpoint(name, url, params, headers):
    """Test a single endpoint"""
    try:
        print(f"Testing {name}...")
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            print(f"  ✓ SUCCESS: {name}")
            data = response.json()
            print(f"  - Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            return True
        else:
            print(f"  ✗ FAILED: {name} - Status: {response.status_code}")
            print(f"  - Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"  ✗ ERROR: {name} - {e}")
        return False

def main():
    print("=== Testing Amazfit Token Validity ===")
    print(f"Token: {TOKEN[:20]}...")
    print(f"UID: {UID}")
    print()
    
    success_count = 0
    total_tests = 0
    
    for i, headers in enumerate(HEADERS_TO_TEST):
        print(f"\n--- Testing Header Set {i+1} ---")
        print(f"Headers: {headers}")
        
        for endpoint in ENDPOINTS_TO_TEST:
            total_tests += 1
            if test_endpoint(endpoint["name"], endpoint["url"], endpoint["params"], headers):
                success_count += 1
            print()
    
    print(f"\n=== Summary ===")
    print(f"Successful tests: {success_count}/{total_tests}")
    
    if success_count > 0:
        print("✓ Token appears to be valid for some endpoints")
    else:
        print("✗ Token appears to be invalid or expired")
        print("You may need to refresh your token")

if __name__ == "__main__":
    main() 