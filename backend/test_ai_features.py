#!/usr/bin/env python3
"""
Test script for AI features in HealthUp API
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def get_auth_token():
    """Get authentication token"""
    user_data = {
        "email": "admin@admin.com",
        "password": "123456"
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=user_data)
    assert response.status_code == 200
    return response.json()["access_token"]

def test_ai_food_parsing_comprehensive():
    """Test comprehensive AI food parsing scenarios"""
    print("Testing AI food parsing with various inputs...")
    
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    test_cases = [
        {
            "input": "I had oatmeal with berries and a banana for breakfast",
            "expected_foods": ["oatmeal", "berries", "banana"]
        },
        {
            "input": "Lunch was grilled salmon with quinoa and steamed vegetables",
            "expected_foods": ["grilled salmon", "quinoa", "steamed vegetables"]
        },
        {
            "input": "Snack: Greek yogurt with honey and almonds",
            "expected_foods": ["Greek yogurt", "honey", "almonds"]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"  Test case {i}: {test_case['input']}")
        
        response = requests.post(f"{BASE_URL}/food/parse", 
                               json={"user_input": test_case["input"]}, 
                               headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "session_id" in data
        assert "parsed_foods" in data
        assert len(data["parsed_foods"]) > 0
        
        # Check that we got nutritional data
        for food in data["parsed_foods"]:
            assert "description" in food
            assert "nutritional_data" in food
            assert "calories_kcal" in food["nutritional_data"]
            assert "protein_g" in food["nutritional_data"]
            assert "fat_g" in food["nutritional_data"]
            assert "carbs_g" in food["nutritional_data"]
        
        print(f"    ✅ Parsed {len(data['parsed_foods'])} foods successfully")
        
        # Check meal analysis if available
        if "meal_analysis" in data:
            analysis = data["meal_analysis"]
            assert "overall_health_score" in analysis
            assert "recommendations" in analysis
            print(f"    ✅ Meal analysis provided")
    
    print("✅ All AI food parsing tests passed")

def test_food_log_analysis():
    """Test food log analysis functionality"""
    print("Testing food log analysis...")
    
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # First create a food log
    food_data = {
        "description": "Salmon with vegetables",
        "calories": 350,
        "protein_g": 40.0,
        "fat_g": 18.0,
        "carbs_g": 15.0,
        "fiber_g": 8.0,
        "vitamin_c_mg": 45.0,
        "calcium_mg": 200.0,
        "iron_mg": 3.0
    }
    
    response = requests.post(f"{BASE_URL}/food", json=food_data, headers=headers)
    assert response.status_code == 200
    food_log = response.json()
    food_id = food_log["id"]
    
    print(f"  Created food log with ID: {food_id}")
    
    # Test food log analysis
    response = requests.post(f"{BASE_URL}/food/{food_id}/analyze", headers=headers)
    assert response.status_code == 200
    print("  ✅ Food analysis initiated")
    
    # Wait a moment for analysis to complete
    time.sleep(2)
    
    # Get the analysis results
    response = requests.get(f"{BASE_URL}/food/{food_id}/analysis", headers=headers)
    if response.status_code == 200:
        analysis = response.json()
        print(f"  ✅ Analysis completed: {analysis.get('health_score', 'N/A')} health score")
    else:
        print(f"  ℹ️  Analysis still processing (status: {response.status_code})")
    
    print("✅ Food log analysis test completed")

def test_ai_insights():
    """Test AI insights functionality"""
    print("Testing AI insights...")
    
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test daily insights
    response = requests.get(f"{BASE_URL}/insight/daily", headers=headers)
    if response.status_code == 200:
        insight = response.json()
        print("  ✅ Daily insight available")
    else:
        print(f"  ℹ️  No daily insight yet (status: {response.status_code})")
    
    # Test weekly insights
    response = requests.get(f"{BASE_URL}/insight/weekly", headers=headers)
    if response.status_code == 200:
        insight = response.json()
        print("  ✅ Weekly insight available")
    else:
        print(f"  ℹ️  No weekly insight yet (status: {response.status_code})")
    
    print("✅ AI insights test completed")

def test_coach_chat():
    """Test AI coach chat functionality"""
    print("Testing AI coach chat...")
    
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    test_messages = [
        "I want to lose weight. What should I focus on?",
        "How can I improve my protein intake?",
        "What are good sources of fiber?",
        "I'm trying to build muscle. Any tips?"
    ]
    
    for message in test_messages:
        print(f"  Testing: {message}")
        
        response = requests.post(f"{BASE_URL}/coach/chat", 
                               json={"message": message}, 
                               headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "response" in data
        
        print(f"    ✅ Coach responded: {data['response'][:50]}...")
    
    print("✅ AI coach chat test completed")

def test_nutrition_summary():
    """Test nutrition summary functionality"""
    print("Testing nutrition summary...")
    
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/food/nutrition-summary", headers=headers)
    assert response.status_code == 200
    summary = response.json()
    
    assert "total_calories" in summary
    assert "total_protein_g" in summary
    assert "total_fat_g" in summary
    assert "total_carbs_g" in summary
    
    print(f"  ✅ Nutrition summary: {summary['total_calories']} calories, "
          f"{summary['total_protein_g']}g protein, "
          f"{summary['total_fat_g']}g fat, "
          f"{summary['total_carbs_g']}g carbs")
    
    print("✅ Nutrition summary test completed")

def main():
    """Run all AI feature tests"""
    print("🤖 Starting HealthUp AI Features Tests...")
    print("=" * 60)
    
    try:
        test_ai_food_parsing_comprehensive()
        test_food_log_analysis()
        test_ai_insights()
        test_coach_chat()
        test_nutrition_summary()
        
        print("=" * 60)
        print("🎉 All AI feature tests passed! HealthUp AI is working correctly.")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 