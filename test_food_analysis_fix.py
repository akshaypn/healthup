#!/usr/bin/env python3
"""
Test script to verify food analysis endpoint fix
"""

import requests
import json
import os
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword123"

def test_food_analysis():
    """Test the food analysis endpoint"""
    print("🧪 Testing Food Analysis Endpoint Fix")
    print("=" * 50)
    
    # First, try to login
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    try:
        # Login
        print("🔐 Attempting login...")
        login_response = requests.post(
            f"{BASE_URL}/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return False
        
        print("✅ Login successful")
        
        # Get cookies for authenticated requests
        cookies = login_response.cookies
        
        # First, create a food log to analyze
        print("\n🍽️ Creating a test food log...")
        food_log_data = {
            "description": "Test banana",
            "calories": 105,
            "protein_g": 1.3,
            "fat_g": 0.4,
            "carbs_g": 27,
            "fiber_g": 3.1,
            "sugar_g": 14,
            "sodium_mg": 1,
            "meal_type": "snack"
        }
        
        food_response = requests.post(
            f"{BASE_URL}/food",
            json=food_log_data,
            cookies=cookies,
            headers={"Content-Type": "application/json"}
        )
        
        if food_response.status_code != 200:
            print(f"❌ Failed to create food log: {food_response.status_code}")
            print(f"Response: {food_response.text}")
            return False
        
        food_log = food_response.json()
        food_id = food_log["id"]
        print(f"✅ Created food log with ID: {food_id}")
        
        # Now test the analysis endpoint
        print(f"\n🔍 Testing analysis for food log {food_id}...")
        analysis_response = requests.post(
            f"{BASE_URL}/food/{food_id}/analyze",
            cookies=cookies,
            headers={"Content-Type": "application/json"}
        )
        
        if analysis_response.status_code == 200:
            analysis = analysis_response.json()
            print("✅ Food analysis successful!")
            print(f"   Health Score: {analysis.get('health_score', 'N/A')}")
            print(f"   Protein Adequacy: {analysis.get('protein_adequacy', 'N/A')}")
            print(f"   Fiber Content: {analysis.get('fiber_content', 'N/A')}")
            print(f"   Recommendations: {analysis.get('recommendations', [])}")
            return True
        else:
            print(f"❌ Food analysis failed: {analysis_response.status_code}")
            print(f"Response: {analysis_response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the server. Make sure the backend is running.")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_food_analysis()
    if success:
        print("\n🎉 All tests passed! Food analysis is working correctly.")
    else:
        print("\n💥 Tests failed. Food analysis still has issues.") 