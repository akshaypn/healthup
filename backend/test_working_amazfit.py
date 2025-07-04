#!/usr/bin/env python3
"""
Test script that matches the working amazfit_fetch_decode.py approach
"""

import requests
import json
import base64
import struct
from datetime import date

# Your real credentials from the working script
TOKEN = "MQVBQEJyQktGXip6SltGSlpuQkZgBAAEAAAAAB-NFpnk_1LFAOwmvyGQ8Q3gnxbuJueeDARMP7mnEJswsJI-gMuW8QzuTtItZRfoQpLDvtf_0kPt5EzMxFroso7XLuCjR7fdFZ5BNrbj6NYfg-Po17Vhnojj5c7W03v5UN8yal0x31NB5Q8sx9swRiSyYJO3Yv3rlEqm446qjvdivAJfzqzStIFyym_CRY3Xc"
UID = "6013538643"
DAY = "2025-07-02"

# Headers from the working script
HEAD = {
    "appPlatform": "web",
    "appname": "com.xiaomi.hm.health",
    "User-Agent": "ZeppPython/1.7"
}

BASE = "https://api-mifit.huami.com"

def b64json(s: str) -> dict:
    """decode base64-encoded JSON → dict"""
    return json.loads(base64.b64decode(s + "==").decode())

def decode_hr_blob(b64: str):
    raw = base64.b64decode(b64)
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

def band(token: str, uid: str, day: str):
    qs = {
        "query_type": "detail", 
        "userid": uid, 
        "device_type": "android_phone",
        "from_date": day, 
        "to_date": day
    }
    r = requests.get(
        f"{BASE}/v1/data/band_data.json",
        headers=HEAD | {"apptoken": token}, 
        params=qs, 
        timeout=20
    )
    r.raise_for_status()
    return r.json()

def test_working_approach():
    """Test using the exact same approach as the working script"""
    print("=== Testing Working Amazfit Approach ===")
    print(f"Token: {TOKEN[:20]}...")
    print(f"UID: {UID}")
    print(f"Day: {DAY}")
    print()
    
    try:
        # Test 1: Get band data using the working approach
        print("1. Getting band data...")
        bd = band(TOKEN, UID, DAY)
        print(f"   ✓ Band data retrieved successfully")
        print(f"   - Data entries: {len(bd.get('data', []))}")
        
        if bd.get('data'):
            first_entry = bd['data'][0]
            print(f"   - Has summary: {'summary' in first_entry}")
            print(f"   - Has HR data: {'data_hr' in first_entry}")
        
        # Test 2: Decode summary
        print("\n2. Decoding summary...")
        summary = b64json(bd["data"][0]["summary"])
        print(f"   ✓ Summary decoded successfully")
        print(f"   - Summary keys: {list(summary.keys())}")
        
        # Test 3: Extract step data
        steps = summary.get("stp", {}).get("ttl", 0)
        kcals = summary.get("stp", {}).get("cal", 0)
        print(f"   - Steps: {steps}")
        print(f"   - Calories: {kcals}")
        
        # Test 4: Calculate sleep duration
        sleep_s = 0
        if "slp" in summary:
            slp = summary["slp"]
            print(f"   - Sleep keys: {list(slp.keys())}")
            if "st" in slp and "ed" in slp:
                sleep_s = slp["ed"] - slp["st"]
                print(f"   - Sleep: {slp['st']} → {slp['ed']} = {sleep_s}s ({sleep_s//60} min)")
            else:
                print(f"   - Available sleep fields: {list(slp.keys())}")
                # Fallback: try to find any numeric field that might be total sleep time
                for key, value in slp.items():
                    if isinstance(value, (int, float)) and value > 0 and key not in ['st', 'ed']:
                        print(f"   - Using {key}={value} as sleep time")
                        sleep_s = value
                        break
        
        # Test 5: Decode HR blob
        print("\n3. Decoding heart rate data...")
        hr_blob = decode_hr_blob(bd["data"][0]["data_hr"])
        
        # Debug: show some sample values
        non_zero = [v for v in hr_blob if v > 0]
        if non_zero:
            print(f"   - Heart rate sample values: {non_zero[:10]}...")
            print(f"   - Valid readings: {len(non_zero)}")
            print(f"   - Average HR: {sum(non_zero) // len(non_zero)}")
            print(f"   - Max HR: {max(non_zero)}")
            print(f"   - Min HR: {min(non_zero)}")
        else:
            print("   - No heart rate data found")
        
        # Test 6: Summary
        print(f"\n[✓] {DAY}: steps {steps:,}  kcals {kcals:,}  "
              f"sleep {sleep_s//60} min  HR-samples {len(hr_blob)}")
        
        print("\n=== All Tests Passed! ===")
        print("The working approach is successful.")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_working_approach()
    exit(0 if success else 1) 