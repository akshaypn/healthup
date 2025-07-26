#!/usr/bin/env python3
"""
Comprehensive Food Logging Integration Tests

Tests the complete food logging workflow including:
- Frontend-Backend integration
- Database persistence
- AI API integration
- Nutritional calculations
- User profile/goals integration
- Amazfit API integration
- Data handling and display
"""

import requests
import json
import time
import psycopg2
from datetime import datetime, date, timedelta
from typing import Dict, List, Any
import uuid

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
DB_URL = "postgresql://healthup:healthup_secure_password_a2032334186a8000@localhost:5433/healthup"

class FoodLoggingIntegrationTests:
    
    def __init__(self):
        self.session = requests.Session()
        self.test_user_email = "foodtest@example.com"
        self.test_user_password = "testpass123"
        self.auth_token = None
        self.user_id = None
        
    def setup_test_user(self):
        """Create and login test user"""
        print("🔧 Setting up test user...")
        
        user_data = {
            "email": self.test_user_email,
            "password": self.test_user_password
        }
        
        # Register user
        try:
            response = self.session.post(f"{BASE_URL}/auth/register", json=user_data)
            if response.status_code == 201:
                print(f"✅ User registered successfully")
            elif response.status_code == 400:
                print(f"⚠️  User already exists")
        except Exception as e:
            print(f"❌ Registration failed: {e}")
            return False
        
        # Login
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", json=user_data)
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.user_id = data.get("user", {}).get("id")
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                print(f"✅ User logged in successfully")
                return True
        except Exception as e:
            print(f"❌ Login failed: {e}")
            return False
        
        return False
    
    def setup_user_profile(self):
        """Create user profile for nutritional calculations"""
        print("🔧 Setting up user profile...")
        
        profile_data = {
            "gender": "male",
            "height_cm": 180,
            "weight_kg": 75,
            "age": 30,
            "activity_level": "moderately_active",
            "goal": "maintain_weight"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/profile", json=profile_data)
            if response.status_code == 200:
                print("✅ User profile created successfully")
                return True
            else:
                print(f"❌ Profile creation failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Profile setup failed: {e}")
            return False

    def test_basic_food_logging(self):
        """Test basic food logging functionality"""
        print("\n🍎 Testing Basic Food Logging")
        
        food_data = {
            "description": "Test Apple",
            "calories": 95,
            "protein_g": 0.5,
            "fat_g": 0.3,
            "carbs_g": 25,
            "fiber_g": 4.4,
            "sugar_g": 19,
            "vitamin_c_mg": 14,
            "potassium_mg": 195,
            "meal_type": "snack",
            "serving_size": "1 medium apple"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/food", json=food_data)
            if response.status_code == 200:
                data = response.json()
                food_id = data.get("id")
                print(f"✅ Food logged successfully (ID: {food_id})")
                
                # Verify data persistence
                history_response = self.session.get(f"{BASE_URL}/food/history")
                if history_response.status_code == 200:
                    logs = history_response.json().get("logs", [])
                    if any(log.get("id") == food_id for log in logs):
                        print("✅ Food data persisted correctly")
                        return True, food_id
                    else:
                        print("❌ Food data not found in history")
                        return False, None
                else:
                    print(f"❌ Failed to retrieve food history: {history_response.status_code}")
                    return False, None
            else:
                print(f"❌ Food logging failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False, None
        except Exception as e:
            print(f"❌ Food logging error: {e}")
            return False, None

    def test_ai_food_parsing(self):
        """Test AI food parsing integration"""
        print("\n🤖 Testing AI Food Parsing")
        
        test_inputs = [
            "I ate a grilled chicken breast with rice and broccoli for lunch",
            "Had 2 slices of whole wheat toast with peanut butter for breakfast",
            "Drank a large coffee with milk and sugar",
            "Ate a caesar salad with croutons and dressing"
        ]
        
        successful_parses = 0
        parsing_sessions = []
        
        for input_text in test_inputs:
            print(f"   Testing: '{input_text[:50]}...'")
            
            try:
                parse_data = {
                    "user_input": input_text,
                    "extract_datetime": True
                }
                
                response = self.session.post(f"{BASE_URL}/food/parse", json=parse_data)
                
                if response.status_code == 200:
                    data = response.json()
                    session_id = data.get("session_id")
                    parsed_foods = data.get("parsed_foods", [])
                    status = data.get("status")
                    
                    print(f"   ✅ Parsed {len(parsed_foods)} foods (Session: {session_id})")
                    print(f"      Status: {status}")
                    
                    if parsed_foods:
                        for food in parsed_foods:
                            nutrition = food.get("nutritional_data", {})
                            calories = nutrition.get("calories", 0)
                            protein = nutrition.get("protein_g", 0)
                            print(f"      - {food.get('description')}: {calories} cal, {protein}g protein")
                    
                    parsing_sessions.append(session_id)
                    successful_parses += 1
                    
                elif response.status_code == 500:
                    error_data = response.json()
                    print(f"   ❌ Parsing failed: {error_data.get('detail', 'Unknown error')}")
                else:
                    print(f"   ❌ Parsing failed: {response.status_code}")
                    print(f"      Response: {response.text}")
                    
            except Exception as e:
                print(f"   ❌ Parsing error: {e}")
        
        print(f"\n📊 AI Parsing Results: {successful_parses}/{len(test_inputs)} successful")
        return successful_parses > 0, parsing_sessions

    def test_food_log_creation_from_ai(self, session_ids):
        """Test creating food logs from AI parsing sessions"""
        print("\n📝 Testing Food Log Creation from AI Sessions")
        
        created_logs = 0
        
        for session_id in session_ids:
            if not session_id:
                continue
                
            print(f"   Creating logs from session: {session_id}")
            
            try:
                response = self.session.post(f"{BASE_URL}/food/parse/{session_id}/create-logs")
                
                if response.status_code == 200:
                    data = response.json()
                    food_logs = data.get("food_logs", [])
                    print(f"   ✅ Created {len(food_logs)} food logs")
                    created_logs += len(food_logs)
                    
                    # Verify each log has proper nutritional data
                    for log in food_logs:
                        calories = log.get("calories")
                        protein = log.get("protein_g")
                        if calories is not None and protein is not None:
                            print(f"      - {log.get('description')}: {calories} cal, {protein}g protein")
                        else:
                            print(f"      ⚠️  Missing nutritional data in: {log.get('description')}")
                            
                else:
                    print(f"   ❌ Log creation failed: {response.status_code}")
                    print(f"      Response: {response.text}")
                    
            except Exception as e:
                print(f"   ❌ Log creation error: {e}")
        
        print(f"\n📊 Created {created_logs} food logs from AI sessions")
        return created_logs > 0

    def test_nutritional_calculations(self):
        """Test nutritional summary calculations"""
        print("\n🧮 Testing Nutritional Calculations")
        
        # Get today's nutrition summary
        today = date.today()
        
        try:
            response = self.session.get(f"{BASE_URL}/food/nutrition-summary", 
                                      params={"start_date": today, "end_date": today})
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Nutritional summary retrieved")
                print(f"   Total calories: {data.get('total_calories', 0)}")
                print(f"   Total protein: {data.get('total_protein_g', 0)}g")
                print(f"   Total fat: {data.get('total_fat_g', 0)}g")
                print(f"   Total carbs: {data.get('total_carbs_g', 0)}g")
                
                # Check for calculation consistency
                vitamins = data.get('vitamins', {})
                minerals = data.get('minerals', {})
                
                print(f"   Vitamins tracked: {len(vitamins)}")
                print(f"   Minerals tracked: {len(minerals)}")
                
                # Test specific nutrient calculations
                if vitamins.get('vitamin_c_mg', 0) < 0:
                    print("   ❌ Negative vitamin C value detected")
                    return False
                
                if data.get('total_calories', 0) < 0:
                    print("   ❌ Negative total calories detected")
                    return False
                
                print("✅ Nutritional calculations appear consistent")
                return True
                
            else:
                print(f"❌ Failed to get nutrition summary: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Nutritional calculation error: {e}")
            return False

    def test_user_goals_integration(self):
        """Test integration with user profile and goals"""
        print("\n🎯 Testing User Goals Integration")
        
        try:
            # Get nutritional requirements based on user profile
            response = self.session.get(f"{BASE_URL}/nutritional-requirements")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Nutritional requirements retrieved")
                
                # Check if requirements are calculated based on user profile
                daily_calories = data.get('daily_calories')
                daily_protein = data.get('daily_protein_g')
                
                if daily_calories and daily_protein:
                    print(f"   Daily calorie target: {daily_calories}")
                    print(f"   Daily protein target: {daily_protein}g")
                    
                    # Verify calculations are reasonable for test profile
                    # (30-year-old, 75kg, 180cm male, moderately active)
                    if 1800 <= daily_calories <= 3000:  # Reasonable range
                        print("✅ Calorie calculation appears reasonable")
                    else:
                        print(f"❌ Unreasonable calorie calculation: {daily_calories}")
                        return False
                    
                    if 50 <= daily_protein <= 200:  # Reasonable range
                        print("✅ Protein calculation appears reasonable")
                    else:
                        print(f"❌ Unreasonable protein calculation: {daily_protein}")
                        return False
                    
                    return True
                else:
                    print("❌ Missing calculated requirements")
                    return False
            else:
                print(f"❌ Failed to get requirements: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Goals integration error: {e}")
            return False

    def test_food_bank_functionality(self):
        """Test food bank nutritional summaries"""
        print("\n🏦 Testing Food Bank Functionality")
        
        periods = ["daily", "weekly", "monthly"]
        
        for period in periods:
            print(f"   Testing {period} summary...")
            
            try:
                response = self.session.get(f"{BASE_URL}/food-bank/{period}")
                
                if response.status_code == 200:
                    data = response.json()
                    summary = data.get("summary", {})
                    food_logs = data.get("food_logs", [])
                    
                    print(f"   ✅ {period.capitalize()} summary: {len(food_logs)} logs")
                    print(f"      Total calories: {summary.get('total_calories', 0)}")
                    
                    # Check requirements comparison
                    requirements = summary.get("requirements", [])
                    if requirements:
                        over_consumed = sum(1 for req in requirements if req.get("status") == "over")
                        under_consumed = sum(1 for req in requirements if req.get("status") == "under")
                        adequate = sum(1 for req in requirements if req.get("status") == "adequate")
                        
                        print(f"      Nutrients: {adequate} adequate, {under_consumed} under, {over_consumed} over")
                    
                else:
                    print(f"   ❌ {period.capitalize()} summary failed: {response.status_code}")
                    return False
                    
            except Exception as e:
                print(f"   ❌ {period.capitalize()} summary error: {e}")
                return False
        
        print("✅ Food bank functionality working")
        return True

    def test_amazfit_integration(self):
        """Test Amazfit API integration"""
        print("\n⌚ Testing Amazfit Integration")
        
        try:
            # Check if user has Amazfit credentials
            response = self.session.get(f"{BASE_URL}/amazfit/credentials")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Amazfit credentials endpoint accessible")
                
                if data.get("user_id_amazfit"):
                    print(f"   User has Amazfit credentials")
                    
                    # Test data retrieval
                    today = date.today().strftime("%Y-%m-%d")
                    day_response = self.session.get(f"{BASE_URL}/amazfit/day", 
                                                  params={"date_str": today})
                    
                    if day_response.status_code == 200:
                        day_data = day_response.json()
                        print("✅ Amazfit day data retrieved")
                        
                        # Check data structure
                        activity_data = day_data.get("activity_data", {})
                        steps_data = day_data.get("steps_data", {})
                        hr_data = day_data.get("heart_rate_data", [])
                        
                        print(f"   Steps: {steps_data.get('total_steps', 'N/A')}")
                        print(f"   Calories burned: {activity_data.get('calories_burned', 'N/A')}")
                        print(f"   Heart rate entries: {len(hr_data)}")
                        
                        return True
                    else:
                        print(f"❌ Amazfit day data failed: {day_response.status_code}")
                        return False
                else:
                    print("⚠️  No Amazfit credentials configured")
                    
                    # Test credentials creation (will fail without real credentials)
                    test_creds = {
                        "email": "test@example.com",
                        "password": "testpass"
                    }
                    
                    creds_response = self.session.post(f"{BASE_URL}/amazfit/credentials", 
                                                     json=test_creds)
                    if creds_response.status_code != 200:
                        print("⚠️  Amazfit credential creation failed (expected with test data)")
                    
                    return True
            else:
                print(f"❌ Amazfit credentials check failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Amazfit integration error: {e}")
            return False

    def test_database_consistency(self):
        """Test database consistency and data integrity"""
        print("\n🗄️ Testing Database Consistency")
        
        try:
            # Connect to database directly
            conn = psycopg2.connect(DB_URL)
            cursor = conn.cursor()
            
            # Check food logs count
            cursor.execute("SELECT COUNT(*) FROM food_logs WHERE user_id = %s", (self.user_id,))
            food_count = cursor.fetchone()[0]
            
            # Check user profile existence
            cursor.execute("SELECT COUNT(*) FROM user_profiles WHERE user_id = %s", (self.user_id,))
            profile_count = cursor.fetchone()[0]
            
            # Check for orphaned records
            cursor.execute("""
                SELECT COUNT(*) FROM food_logs 
                WHERE user_id NOT IN (SELECT id FROM users)
            """)
            orphaned_foods = cursor.fetchone()[0]
            
            print(f"✅ Database consistency check:")
            print(f"   User food logs: {food_count}")
            print(f"   User profiles: {profile_count}")
            print(f"   Orphaned food logs: {orphaned_foods}")
            
            if orphaned_foods > 0:
                print("❌ Found orphaned food logs!")
                return False
            
            # Check data types and constraints
            cursor.execute("""
                SELECT COUNT(*) FROM food_logs 
                WHERE calories < 0 OR protein_g < 0 OR fat_g < 0 OR carbs_g < 0
            """)
            invalid_nutrition = cursor.fetchone()[0]
            
            if invalid_nutrition > 0:
                print(f"❌ Found {invalid_nutrition} records with negative nutrition values!")
                return False
            
            cursor.close()
            conn.close()
            
            print("✅ Database consistency verified")
            return True
            
        except Exception as e:
            print(f"❌ Database consistency check failed: {e}")
            return False

    def test_food_update_and_delete(self):
        """Test food log update and delete functionality"""
        print("\n✏️ Testing Food Update and Delete")
        
        # First create a food log
        food_data = {
            "description": "Test Food for Update",
            "calories": 100,
            "protein_g": 5.0
        }
        
        try:
            # Create
            response = self.session.post(f"{BASE_URL}/food", json=food_data)
            if response.status_code != 200:
                print("❌ Failed to create test food for update")
                return False
            
            food_id = response.json().get("id")
            print(f"✅ Created test food (ID: {food_id})")
            
            # Update
            update_data = {
                "description": "Updated Test Food",
                "calories": 150,
                "protein_g": 8.0
            }
            
            update_response = self.session.put(f"{BASE_URL}/food/{food_id}", json=update_data)
            if update_response.status_code == 200:
                updated_food = update_response.json()
                if updated_food.get("calories") == 150:
                    print("✅ Food update successful")
                else:
                    print("❌ Food update data inconsistent")
                    return False
            else:
                print(f"❌ Food update failed: {update_response.status_code}")
                return False
            
            # Delete
            delete_response = self.session.delete(f"{BASE_URL}/food/{food_id}")
            if delete_response.status_code == 200:
                print("✅ Food delete successful")
                
                # Verify deletion
                history_response = self.session.get(f"{BASE_URL}/food/history")
                if history_response.status_code == 200:
                    logs = history_response.json().get("logs", [])
                    if not any(log.get("id") == food_id for log in logs):
                        print("✅ Food deletion verified")
                        return True
                    else:
                        print("❌ Food still exists after deletion")
                        return False
            else:
                print(f"❌ Food delete failed: {delete_response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Food update/delete error: {e}")
            return False

    def run_comprehensive_tests(self):
        """Run all food logging integration tests"""
        print("🧪 HealthUp Food Logging Integration Test Suite")
        print("=" * 60)
        
        if not self.setup_test_user():
            print("❌ Failed to setup test user")
            return
        
        if not self.setup_user_profile():
            print("❌ Failed to setup user profile")
            return
        
        test_results = {}
        
        # Run all tests
        tests = [
            ("Basic Food Logging", self.test_basic_food_logging),
            ("AI Food Parsing", self.test_ai_food_parsing),
            ("Nutritional Calculations", self.test_nutritional_calculations),
            ("User Goals Integration", self.test_user_goals_integration),
            ("Food Bank Functionality", self.test_food_bank_functionality),
            ("Amazfit Integration", self.test_amazfit_integration),
            ("Database Consistency", self.test_database_consistency),
            ("Food Update/Delete", self.test_food_update_and_delete)
        ]
        
        ai_sessions = []
        
        for test_name, test_func in tests:
            try:
                if test_name == "Basic Food Logging":
                    result, food_id = test_func()
                    test_results[test_name] = result
                elif test_name == "AI Food Parsing":
                    result, sessions = test_func()
                    test_results[test_name] = result
                    ai_sessions = sessions
                else:
                    test_results[test_name] = test_func()
            except Exception as e:
                print(f"❌ {test_name} crashed: {e}")
                test_results[test_name] = False
        
        # Test AI session conversion if we have sessions
        if ai_sessions:
            try:
                result = self.test_food_log_creation_from_ai(ai_sessions)
                test_results["AI Session Conversion"] = result
            except Exception as e:
                print(f"❌ AI Session Conversion crashed: {e}")
                test_results["AI Session Conversion"] = False
        
        # Generate report
        self.generate_integration_report(test_results)

    def generate_integration_report(self, results):
        """Generate comprehensive integration test report"""
        print("\n" + "=" * 60)
        print("📊 INTEGRATION TEST REPORT")
        print("=" * 60)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        print(f"Tests Passed: {passed}/{total} ({passed/total*100:.1f}%)")
        print()
        
        print("Detailed Results:")
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status} {test_name}")
        
        # Identify critical issues
        critical_failures = []
        if not results.get("Basic Food Logging", True):
            critical_failures.append("Basic food logging not working")
        if not results.get("Database Consistency", True):
            critical_failures.append("Database integrity issues")
        if not results.get("Nutritional Calculations", True):
            critical_failures.append("Nutritional calculations failing")
        
        if critical_failures:
            print(f"\n🚨 CRITICAL ISSUES:")
            for issue in critical_failures:
                print(f"  - {issue}")
        
        # Overall assessment
        if passed == total:
            print(f"\n🎉 ALL TESTS PASSED - System integration excellent!")
        elif passed >= total * 0.8:
            print(f"\n✅ GOOD - Most functionality working, minor issues to address")
        elif passed >= total * 0.6:
            print(f"\n⚠️  FAIR - Several integration issues need attention")
        else:
            print(f"\n❌ POOR - Major integration problems detected")
        
        return results

if __name__ == "__main__":
    tester = FoodLoggingIntegrationTests()
    tester.run_comprehensive_tests() 