import requests
import base64
import struct
from datetime import date, timedelta

# Fresh tokens from successful login
APP_TOKEN = "MQVBQFJyQktGHlp6QkpbRl5LRl5qek4uXAQABAAAAALPDyxf0sgQQloHie2_hcqJb2JN2vLzBVfnBTjYOsvTcXGpsf2jTVx6otebENdd5Vgz2EvYRBQ9YCOUecqHUJI_JorLTJKjqtzUyUmShQOOhHOFr9YU7JzhDU7yf-VXoABOCeJMdx8W1i52zHlQiTDhyHWqgBqkZeuA6Z05fFrgJYs-Sb0XE4MikpJy3OTVTeQ"
USER_ID = "6013538643"

# Try different header combinations
HEADERS_APPTOKEN = {
    "apptoken": APP_TOKEN,
    "appname": "com.xiaomi.hm.health",
    "appPlatform": "web",
    "User-Agent": "Zepp/6.10.5 PythonScript"
}

def print_json(label, data, maxlen=800):
    import json
    s = json.dumps(data, indent=2, default=str)
    print(f"\n--- {label} ---\n" + (s[:maxlen] + ("..." if len(s) > maxlen else "")))

def test_endpoint(url, params=None, label="Endpoint"):
    """Test an endpoint with apptoken auth"""
    print(f"\nTesting {label}...")
    print(f"URL: {url}")
    if params:
        print(f"Params: {params}")
    
    try:
        r = requests.get(url, headers=HEADERS_APPTOKEN, params=params)
        print(f"Status: {r.status_code}")
        
        if r.status_code == 200:
            print(f"✓ Success!")
            data = r.json()
            print_json(f"{label}", data)
            return data
        else:
            print(f"✗ Failed: {r.status_code}")
            print(f"Response: {r.text[:200]}")
            return None
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

def test_alternative_fitness_endpoints(user_id, day):
    """Test alternative fitness endpoints"""
    print(f"\n{'='*60}")
    print("TESTING ALTERNATIVE FITNESS ENDPOINTS")
    print(f"{'='*60}")
    
    # Try different fitness endpoints
    alternative_endpoints = [
        ("https://api-user.huami.com/v1/user/fitness/daily", {"userid": user_id, "date": day}, "Fitness Daily"),
        ("https://api-user.huami.com/v1/user/fitness/summary", {"userid": user_id, "date": day}, "Fitness Summary"),
        ("https://api-user.huami.com/v1/user/fitness/data", {"userid": user_id, "date": day}, "Fitness Data"),
        ("https://api-user.huami.com/v1/user/fitness/stats", {"userid": user_id, "date": day}, "Fitness Stats"),
        ("https://api-user.huami.com/v1/user/fitness/heart_rate_data", {"userid": user_id, "date": day}, "Heart Rate Data"),
        ("https://api-user.huami.com/v1/user/fitness/activity_data", {"userid": user_id, "date": day}, "Activity Data"),
        ("https://api-user.huami.com/v1/user/fitness/sleep_data", {"userid": user_id, "date": day}, "Sleep Data"),
    ]
    
    for url, params, label in alternative_endpoints:
        data = test_endpoint(url, params, label)
        if data:
            print(f"✓ Found working endpoint: {url}")
            break

def test_heart_rate(user_id, day):
    """Test heart rate endpoint"""
    url = "https://api-user.huami.com/v1/user/fitness/heart_rate"
    params = {"userid": user_id, "date": day}
    data = test_endpoint(url, params, f"Heart Rate ({day})")
    
    if data and "heartRate" in data:
        blob = base64.b64decode(data["heartRate"])
        hr_values = [struct.unpack('<H', blob[i:i+2])[0] for i in range(0, len(blob), 2)]
        print(f"  Heart rate values: {hr_values[:20]} ... Total: {len(hr_values)}")
        print(f"  Valid readings (non-zero): {len([h for h in hr_values if h > 0])}")
    
    return data

def test_activity(user_id, day):
    """Test activity endpoint"""
    url = "https://api-user.huami.com/v1/user/fitness/activity"
    params = {"userid": user_id, "date": day}
    return test_endpoint(url, params, f"Activity ({day})")

def test_sleep(user_id, day):
    """Test sleep endpoint"""
    url = "https://api-user.huami.com/v1/user/fitness/sleep"
    params = {"userid": user_id, "date": day}
    return test_endpoint(url, params, f"Sleep ({day})")

def test_workout_history():
    """Test workout history endpoint"""
    url = "https://api-mifit.huami.com/v1/sport/run/history.json"
    params = {"source": "run.mifit.huami.com"}
    data = test_endpoint(url, params, "Workout History")
    
    if data and data.get("data", {}).get("summary"):
        return data["data"]["summary"][0]["trackid"]
    return None

def test_workout_detail(trackid):
    """Test workout detail endpoint"""
    url = "https://api-mifit.huami.com/v1/sport/run/detail.json"
    params = {"trackid": trackid, "source": "run.mifit.huami.com"}
    return test_endpoint(url, params, f"Workout Detail ({trackid})")

def main():
    today = date.today().strftime("%Y-%m-%d")
    yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    print(f"Testing Amazfit API with fresh token")
    print(f"App Token: {APP_TOKEN[:50]}...")
    print(f"User ID: {USER_ID}")
    print(f"Testing dates: {today}, {yesterday}")
    
    # Test alternative fitness endpoints first
    test_alternative_fitness_endpoints(USER_ID, today)
    
    # Test original endpoints with today's date
    print(f"\n{'='*60}")
    print("TESTING ORIGINAL ENDPOINTS (TODAY)")
    print(f"{'='*60}")
    test_heart_rate(USER_ID, today)
    test_activity(USER_ID, today)
    test_sleep(USER_ID, today)
    
    # Test with yesterday's date
    print(f"\n{'='*60}")
    print("TESTING ORIGINAL ENDPOINTS (YESTERDAY)")
    print(f"{'='*60}")
    test_heart_rate(USER_ID, yesterday)
    test_activity(USER_ID, yesterday)
    test_sleep(USER_ID, yesterday)
    
    # Test workout endpoints
    print(f"\n{'='*60}")
    print("TESTING WORKOUT ENDPOINTS")
    print(f"{'='*60}")
    trackid = test_workout_history()
    if trackid:
        test_workout_detail(trackid)
    else:
        print("No workout history found.")

if __name__ == "__main__":
    main() 