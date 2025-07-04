#!/usr/bin/env python3
"""
Test script for the enhanced Insights functionality
"""

import requests
import json
from datetime import date, timedelta

# Configuration
BASE_URL = "http://localhost:8000"
COOKIES_FILE = "cookies.txt"

def load_cookies():
    """Load cookies from file"""
    cookies = {}
    try:
        with open(COOKIES_FILE, 'r') as f:
            for line in f:
                if '=' in line:
                    name, value = line.strip().split('=', 1)
                    cookies[name] = value
        return cookies
    except FileNotFoundError:
        print(f"Cookies file {COOKIES_FILE} not found. Please login first.")
        return None

def test_get_insights():
    """Test getting existing insights"""
    print("🔍 Testing GET insights...")
    
    cookies = load_cookies()
    if not cookies:
        return False
    
    periods = ['daily', 'weekly', 'monthly']
    
    for period in periods:
        try:
            response = requests.get(
                f"{BASE_URL}/insight/{period}",
                cookies=cookies,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {period.capitalize()} insight: {'Available' if data.get('insight_md') else 'Placeholder'}")
            else:
                print(f"❌ {period.capitalize()} insight: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ {period.capitalize()} insight: Error - {e}")
    
    return True

def test_generate_insight(period='daily'):
    """Test generating an insight"""
    print(f"\n🤖 Testing insight generation for {period}...")
    
    cookies = load_cookies()
    if not cookies:
        return False
    
    try:
        response = requests.post(
            f"{BASE_URL}/insight/{period}/generate",
            cookies=cookies,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {period.capitalize()} insight generation: {data.get('message', 'Success')}")
            print(f"   Regenerated: {data.get('regenerated', False)}")
            return True
        else:
            print(f"❌ {period.capitalize()} insight generation: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ {period.capitalize()} insight generation: Error - {e}")
        return False

def test_regenerate_insight(period='daily'):
    """Test regenerating an insight"""
    print(f"\n🔄 Testing insight regeneration for {period}...")
    
    cookies = load_cookies()
    if not cookies:
        return False
    
    try:
        response = requests.post(
            f"{BASE_URL}/insight/{period}/regenerate",
            cookies=cookies,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {period.capitalize()} insight regeneration: {data.get('message', 'Success')}")
            print(f"   Regenerated: {data.get('regenerated', False)}")
            return True
        else:
            print(f"❌ {period.capitalize()} insight regeneration: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ {period.capitalize()} insight regeneration: Error - {e}")
        return False

def main():
    """Run all tests"""
    print("🧠 Testing Enhanced Insights Functionality")
    print("=" * 50)
    
    # Test getting existing insights
    if not test_get_insights():
        return
    
    # Test generating daily insight
    if test_generate_insight('daily'):
        # Test regenerating daily insight
        test_regenerate_insight('daily')
    
    # Test generating weekly insight
    test_generate_insight('weekly')
    
    # Test generating monthly insight
    test_generate_insight('monthly')
    
    print("\n" + "=" * 50)
    print("🎉 Insight testing completed!")

if __name__ == "__main__":
    main() 