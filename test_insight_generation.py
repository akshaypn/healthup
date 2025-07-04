#!/usr/bin/env python3
"""
Test script for insight generation with authentication
"""

import requests
import json
import os

# Configuration
BASE_URL = "http://localhost:8000"
LOGIN_DATA = {
    "email": "admin@admin.com",
    "password": "123456"
}

def login_and_get_cookies():
    """Login and get session cookies"""
    print("🔐 Logging in...")
    
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json=LOGIN_DATA,
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code == 200:
        print("✅ Login successful")
        return response.cookies
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(response.text)
        return None

def test_insight_generation(cookies):
    """Test insight generation"""
    print("\n🤖 Testing insight generation...")
    
    # Test daily insight generation
    response = requests.post(
        f"{BASE_URL}/insight/daily/regenerate",
        cookies=cookies,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Insight generation successful!")
        print(f"Message: {data.get('message')}")
        print(f"Regenerated: {data.get('regenerated')}")
        
        # Show a preview of the insight
        insight = data.get('insight', {})
        if insight and insight.get('insight_md'):
            preview = insight['insight_md'][:200] + "..." if len(insight['insight_md']) > 200 else insight['insight_md']
            print(f"Insight preview: {preview}")
    else:
        print(f"❌ Insight generation failed: {response.status_code}")
        try:
            error_data = response.json()
            print(f"Error: {error_data.get('detail', 'Unknown error')}")
        except:
            print(f"Error: {response.text}")

def test_get_insights(cookies):
    """Test getting existing insights"""
    print("\n📊 Testing GET insights...")
    
    periods = ['daily', 'weekly', 'monthly']
    
    for period in periods:
        response = requests.get(
            f"{BASE_URL}/insight/{period}",
            cookies=cookies,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            status = "Available" if data.get('insight_md') and not data.get('insight_md', '').startswith('# Daily Insights') else "Placeholder"
            print(f"✅ {period.capitalize()} insight: {status}")
        else:
            print(f"❌ {period.capitalize()} insight: HTTP {response.status_code}")

def main():
    """Run all tests"""
    print("🧠 Testing Insight Generation with Authentication")
    print("=" * 60)
    
    # Login and get cookies
    cookies = login_and_get_cookies()
    if not cookies:
        print("❌ Cannot proceed without authentication")
        return
    
    # Test getting existing insights
    test_get_insights(cookies)
    
    # Test insight generation
    test_insight_generation(cookies)
    
    print("\n" + "=" * 60)
    print("🎉 Testing completed!")

if __name__ == "__main__":
    main() 