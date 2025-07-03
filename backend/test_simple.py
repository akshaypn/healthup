#!/usr/bin/env python3
"""
Simple test script for HealthUp API endpoints
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_root_endpoint():
    """Test the root endpoint"""
    print("Testing root endpoint...")
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "HealthUp API"
    print("✅ Root endpoint working")

def test_health_endpoint():
    """Test the health endpoint"""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    print("✅ Health endpoint working")

def test_auth_flow():
    """Test authentication flow"""
    print("Testing authentication flow...")
    
    # Test registration
    user_data = {
        "email": "testuser@example.com",
        "password": "testpass123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    if response.status_code == 400 and "already registered" in response.json()["detail"]:
        print("ℹ️  User already exists, proceeding with login")
    else:
        assert response.status_code == 200
        print("✅ User registration working")
    
    # Test login
    response = requests.post(f"{BASE_URL}/auth/login", json=user_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    token = data["access_token"]
    print("✅ User login working")
    
    # Test authenticated endpoint
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    assert response.status_code == 200
    print("✅ Authentication working")
    
    return token

def test_food_logging(token):
    """Test food logging endpoints"""
    print("Testing food logging...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test creating food log
    food_data = {
        "description": "Test food item",
        "calories": 100,
        "protein_g": 10.0,
        "fat_g": 5.0,
        "carbs_g": 15.0
    }
    
    response = requests.post(f"{BASE_URL}/food", json=food_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == food_data["description"]
    food_id = data["id"]
    print("✅ Food log creation working")
    
    # Test getting food history
    response = requests.get(f"{BASE_URL}/food/history", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "logs" in data
    print("✅ Food history working")
    
    # Test updating food log
    update_data = {"description": "Updated test food"}
    response = requests.put(f"{BASE_URL}/food/{food_id}", json=update_data, headers=headers)
    assert response.status_code == 200
    print("✅ Food log update working")
    
    # Test deleting food log
    response = requests.delete(f"{BASE_URL}/food/{food_id}", headers=headers)
    assert response.status_code == 200
    print("✅ Food log deletion working")

def test_ai_food_parsing(token):
    """Test AI food parsing"""
    print("Testing AI food parsing...")
    headers = {"Authorization": f"Bearer {token}"}
    
    parse_data = {
        "user_input": "I had a grilled chicken breast with brown rice for lunch"
    }
    
    response = requests.post(f"{BASE_URL}/food/parse", json=parse_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "parsed_foods" in data
    assert len(data["parsed_foods"]) > 0
    print("✅ AI food parsing working")

def test_dashboard(token):
    """Test dashboard endpoint"""
    print("Testing dashboard...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/dashboard", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "recent_weight" in data
    assert "recent_food" in data
    assert "recent_hr" in data
    assert "stats" in data
    print("✅ Dashboard working")

def test_weight_logging(token):
    """Test weight logging"""
    print("Testing weight logging...")
    headers = {"Authorization": f"Bearer {token}"}
    
    weight_data = {"kg": 75.5}
    response = requests.post(f"{BASE_URL}/weight", json=weight_data, headers=headers)
    assert response.status_code == 200
    print("✅ Weight logging working")
    
    response = requests.get(f"{BASE_URL}/weight/history", headers=headers)
    assert response.status_code == 200
    print("✅ Weight history working")

def main():
    """Run all tests"""
    print("🚀 Starting HealthUp API tests...")
    print("=" * 50)
    
    try:
        test_root_endpoint()
        test_health_endpoint()
        token = test_auth_flow()
        test_food_logging(token)
        test_ai_food_parsing(token)
        test_dashboard(token)
        test_weight_logging(token)
        
        print("=" * 50)
        print("🎉 All tests passed! HealthUp API is working correctly.")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 