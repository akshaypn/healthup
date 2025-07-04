import requests

# Test basic connectivity and authentication
def test_basic_auth():
    print("Testing basic Amazfit API connectivity...")
    
    # Test a simple endpoint that might exist
    test_urls = [
        "https://api-user.huami.com/",
        "https://api-user.huami.com/v1/",
        "https://api-user.huami.com/v1/user",
        "https://api-mifit.huami.com/",
        "https://api-mifit.huami.com/v1/",
    ]
    
    headers = {
        "User-Agent": "Zepp/6.10.5 PythonScript"
    }
    
    for url in test_urls:
        try:
            print(f"Testing {url}")
            r = requests.get(url, headers=headers)
            print(f"  Status: {r.status_code}")
            if r.status_code != 404:
                print(f"  Response: {r.text[:200]}")
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    test_basic_auth() 