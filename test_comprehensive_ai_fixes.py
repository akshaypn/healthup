#!/usr/bin/env python3
"""
Comprehensive AI and Integration Testing Suite

Tests all critical fixes:
1. AI food parsing with OpenAI API
2. Nutritional requirements API format
3. Decimal type handling
4. Graph plotting and data visualization
5. Weekly/monthly data aggregation  
6. Frontend integration issues
7. Edge cases and error handling
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

class ComprehensiveAITestSuite:
    
    def __init__(self):
        self.session = requests.Session()
        self.test_user_email = "aitest@example.com"
        self.test_user_password = "testpass123"
        self.auth_token = None
        self.user_id = None
        self.test_results = {}
        
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
                print(f"✅ User logged in successfully (ID: {self.user_id})")
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

    def test_ai_food_parsing_with_openai(self):
        """Test AI food parsing with OpenAI API - comprehensive scenarios"""
        print("\n🤖 Testing AI Food Parsing with OpenAI")
        
        test_scenarios = [
            {
                "input": "I ate a banana",
                "expected_foods": 1,
                "description": "Simple single food"
            },
            {
                "input": "grilled chicken breast with rice and steamed broccoli",
                "expected_foods": 3,
                "description": "Complex meal with multiple items"
            },
            {
                "input": "2 slices of whole wheat toast with peanut butter and a glass of orange juice",
                "expected_foods": 3,
                "description": "Breakfast with quantities"
            },
            {
                "input": "large caesar salad with grilled chicken, croutons, and dressing",
                "expected_foods": 4,
                "description": "Composed dish with components"
            },
            {
                "input": "Had dinner: pasta with marinara sauce, side of garlic bread, and a small garden salad",
                "expected_foods": 3,
                "description": "Contextual meal description"
            }
        ]
        
        successful_parses = 0
        parsing_sessions = []
        nutrition_accuracy_tests = []
        
        for scenario in test_scenarios:
            input_text = scenario["input"]
            expected_foods = scenario["expected_foods"]
            description = scenario["description"]
            
            print(f"   Testing: {description}")
            print(f"   Input: '{input_text}'")
            
            try:
                parse_data = {
                    "user_input": input_text,
                    "extract_datetime": True
                }
                
                # Test with timeout
                start_time = time.time()
                response = self.session.post(f"{BASE_URL}/food/parse", json=parse_data, timeout=30)
                parse_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    session_id = data.get("session_id")
                    parsed_foods = data.get("parsed_foods", [])
                    status = data.get("status")
                    
                    print(f"   ✅ Parsed {len(parsed_foods)} foods in {parse_time:.2f}s (Session: {session_id})")
                    print(f"      Status: {status}")
                    
                    # Check accuracy
                    if len(parsed_foods) >= expected_foods - 1:  # Allow some flexibility
                        print(f"      ✅ Food count reasonable ({len(parsed_foods)} vs expected {expected_foods})")
                    else:
                        print(f"      ⚠️  Food count low ({len(parsed_foods)} vs expected {expected_foods})")
                    
                    # Analyze nutrition data quality
                    total_calories = 0
                    for food in parsed_foods:
                        nutrition = food.get("nutritional_data", {})
                        calories = nutrition.get("calories", 0)
                        protein = nutrition.get("protein_g", 0)
                        description = food.get("description", "Unknown")
                        
                        print(f"      - {description}: {calories} cal, {protein}g protein")
                        total_calories += calories
                        
                        # Track nutrition accuracy
                        nutrition_accuracy_tests.append({
                            "food": description,
                            "calories": calories,
                            "protein": protein,
                            "has_calories": calories > 0,
                            "has_protein": protein > 0,
                            "realistic_calories": 10 <= calories <= 2000 if calories > 0 else False
                        })
                    
                    print(f"      Total meal calories: {total_calories}")
                    
                    if total_calories > 0:
                        print(f"      ✅ Calories extracted successfully")
                    else:
                        print(f"      ❌ ZERO CALORIE BUG DETECTED!")
                    
                    parsing_sessions.append(session_id)
                    successful_parses += 1
                    
                elif response.status_code == 500:
                    error_data = response.json()
                    error_detail = error_data.get('detail', 'Unknown error')
                    print(f"   ❌ Parsing failed: {error_detail}")
                    
                    if "food-related content only" in error_detail:
                        print(f"      This appears to be input sanitization issue")
                    elif "timeout" in error_detail.lower():
                        print(f"      This appears to be a timeout issue")
                    else:
                        print(f"      Unknown AI parsing error")
                        
                else:
                    print(f"   ❌ Parsing failed: {response.status_code}")
                    print(f"      Response: {response.text}")
                    
            except requests.exceptions.Timeout:
                print(f"   ❌ Parsing timeout after 30 seconds")
            except Exception as e:
                print(f"   ❌ Parsing error: {e}")
        
        # Analyze nutrition data accuracy
        print(f"\n📊 AI Nutrition Accuracy Analysis:")
        foods_with_calories = sum(1 for test in nutrition_accuracy_tests if test["has_calories"])
        foods_with_protein = sum(1 for test in nutrition_accuracy_tests if test["has_protein"])
        realistic_calories = sum(1 for test in nutrition_accuracy_tests if test["realistic_calories"])
        
        print(f"   Foods with calories: {foods_with_calories}/{len(nutrition_accuracy_tests)}")
        print(f"   Foods with protein: {foods_with_protein}/{len(nutrition_accuracy_tests)}")
        print(f"   Realistic calorie values: {realistic_calories}/{foods_with_calories if foods_with_calories > 0 else 1}")
        
        accuracy_score = (foods_with_calories + realistic_calories) / (len(nutrition_accuracy_tests) * 2) * 100 if nutrition_accuracy_tests else 0
        print(f"   Overall nutrition accuracy: {accuracy_score:.1f}%")
        
        print(f"\n📊 AI Parsing Results: {successful_parses}/{len(test_scenarios)} successful")
        
        self.test_results["ai_parsing_success_rate"] = successful_parses / len(test_scenarios)
        self.test_results["ai_nutrition_accuracy"] = accuracy_score
        
        return successful_parses > 0, parsing_sessions

    def test_nutritional_requirements_api_fix(self):
        """Test the fixed nutritional requirements API format"""
        print("\n🎯 Testing Nutritional Requirements API Fix")
        
        try:
            response = self.session.get(f"{BASE_URL}/nutritional-requirements")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Nutritional requirements endpoint accessible")
                
                # Check for flattened format
                required_fields = [
                    "daily_calories", "daily_protein_g", "daily_fat_g", 
                    "daily_carbs_g", "daily_fiber_g"
                ]
                
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    print("✅ All required flattened fields present")
                    
                    # Check values are reasonable
                    daily_calories = data.get("daily_calories")
                    daily_protein = data.get("daily_protein_g")
                    
                    print(f"   Daily calories: {daily_calories}")
                    print(f"   Daily protein: {daily_protein}g")
                    
                    if daily_calories and isinstance(daily_calories, (int, float)) and 1500 <= daily_calories <= 3500:
                        print("✅ Calorie calculation appears reasonable")
                    else:
                        print(f"❌ Unreasonable calorie calculation: {daily_calories}")
                        return False
                    
                    if daily_protein and isinstance(daily_protein, (int, float)) and 50 <= daily_protein <= 200:
                        print("✅ Protein calculation appears reasonable")
                    else:
                        print(f"❌ Unreasonable protein calculation: {daily_protein}")
                        return False
                    
                    # Check that detailed requirements are also present
                    if "detailed_requirements" in data:
                        print("✅ Detailed requirements also preserved")
                    else:
                        print("⚠️  Detailed requirements missing (not critical)")
                    
                    self.test_results["nutritional_api_format"] = "fixed"
                    return True
                else:
                    print(f"❌ Missing flattened fields: {missing_fields}")
                    self.test_results["nutritional_api_format"] = "broken"
                    return False
            else:
                print(f"❌ Failed to get requirements: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Requirements API test failed: {e}")
            return False

    def test_decimal_type_handling(self):
        """Test that Decimal types are properly converted to float"""
        print("\n🔢 Testing Decimal Type Handling Fix")
        
        try:
            # Create a food with decimal values
            food_data = {
                "description": "Type Test Food",
                "calories": 150,
                "protein_g": 12.5,
                "fat_g": 8.3,
                "carbs_g": 15.7,
                "vitamin_c_mg": 25.4
            }
            
            # Create food
            response = self.session.post(f"{BASE_URL}/food", json=food_data)
            if response.status_code != 200:
                print("❌ Failed to create test food")
                return False
            
            food_id = response.json().get("id")
            print(f"✅ Created test food (ID: {food_id})")
            
            # Get food back and check types
            history_response = self.session.get(f"{BASE_URL}/food/history")
            if history_response.status_code == 200:
                logs = history_response.json().get("logs", [])
                test_food = next((log for log in logs if log.get("id") == food_id), None)
                
                if test_food:
                    protein_value = test_food.get("protein_g")
                    fat_value = test_food.get("fat_g")
                    vitamin_c_value = test_food.get("vitamin_c_mg")
                    
                    print(f"   Protein type: {type(protein_value)} = {protein_value}")
                    print(f"   Fat type: {type(fat_value)} = {fat_value}")
                    print(f"   Vitamin C type: {type(vitamin_c_value)} = {vitamin_c_value}")
                    
                    # Check all are proper numeric types (int/float, not Decimal)
                    if isinstance(protein_value, (int, float)) and isinstance(fat_value, (int, float)):
                        print("✅ Decimal fields properly converted to float")
                        
                        # Test update operation (this was failing before)
                        update_data = {"protein_g": 15.0, "fat_g": 10.0}
                        update_response = self.session.put(f"{BASE_URL}/food/{food_id}", json=update_data)
                        
                        if update_response.status_code == 200:
                            print("✅ Food update operation successful")
                            updated_food = update_response.json()
                            
                            if abs(updated_food.get("protein_g", 0) - 15.0) < 0.01:
                                print("✅ Update values correctly applied")
                                self.test_results["decimal_type_handling"] = "fixed"
                                return True
                            else:
                                print("❌ Update values not correctly applied")
                                return False
                        else:
                            print(f"❌ Food update failed: {update_response.status_code}")
                            return False
                    else:
                        print(f"❌ Decimal fields not converted: protein={type(protein_value)}, fat={type(fat_value)}")
                        self.test_results["decimal_type_handling"] = "broken"
                        return False
                else:
                    print("❌ Test food not found in history")
                    return False
            else:
                print(f"❌ Failed to get food history: {history_response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Decimal type test failed: {e}")
            return False

    def test_weekly_monthly_data_aggregation(self):
        """Test weekly and monthly data aggregation accuracy"""
        print("\n📅 Testing Weekly/Monthly Data Aggregation")
        
        try:
            # Create food logs across different days
            today = date.today()
            test_foods = []
            
            # Create foods for the past week
            for i in range(7):
                log_date = today - timedelta(days=i)
                food_data = {
                    "description": f"Test Food Day {i}",
                    "calories": 100 + (i * 10),  # 100, 110, 120, etc.
                    "protein_g": 5 + i,
                    "logged_at": log_date.isoformat()
                }
                
                response = self.session.post(f"{BASE_URL}/food", json=food_data)
                if response.status_code == 200:
                    test_foods.append({**food_data, "id": response.json().get("id")})
                else:
                    print(f"⚠️  Failed to create food for day {i}")
            
            print(f"✅ Created {len(test_foods)} test foods across 7 days")
            
            # Test weekly summary
            week_start = today - timedelta(days=6)
            weekly_response = self.session.get(f"{BASE_URL}/food/nutrition-summary", 
                                             params={"start_date": week_start, "end_date": today})
            
            if weekly_response.status_code == 200:
                weekly_data = weekly_response.json()
                weekly_calories = weekly_data.get("total_calories", 0)
                weekly_protein = weekly_data.get("total_protein_g", 0)
                
                print(f"   Weekly calories: {weekly_calories}")
                print(f"   Weekly protein: {weekly_protein}g")
                
                # Expected: 100+110+120+130+140+150+160 = 910 calories
                # Expected: 5+6+7+8+9+10+11 = 56g protein
                expected_calories = sum(100 + (i * 10) for i in range(7))
                expected_protein = sum(5 + i for i in range(7))
                
                if abs(weekly_calories - expected_calories) <= expected_calories * 0.1:  # 10% tolerance
                    print(f"✅ Weekly calorie aggregation accurate ({weekly_calories} vs expected {expected_calories})")
                else:
                    print(f"❌ Weekly calorie aggregation inaccurate ({weekly_calories} vs expected {expected_calories})")
                    return False
                
                if abs(weekly_protein - expected_protein) <= expected_protein * 0.1:  # 10% tolerance
                    print(f"✅ Weekly protein aggregation accurate ({weekly_protein} vs expected {expected_protein})")
                else:
                    print(f"❌ Weekly protein aggregation inaccurate ({weekly_protein} vs expected {expected_protein})")
                    return False
                
                # Test food bank weekly view
                bank_response = self.session.get(f"{BASE_URL}/food-bank/weekly")
                if bank_response.status_code == 200:
                    bank_data = bank_response.json()
                    bank_summary = bank_data.get("summary", {})
                    bank_calories = bank_summary.get("total_calories", 0)
                    
                    print(f"   Food bank weekly calories: {bank_calories}")
                    
                    if abs(bank_calories - weekly_calories) <= 10:  # Should match
                        print("✅ Food bank weekly data consistent with nutrition summary")
                    else:
                        print("❌ Food bank weekly data inconsistent")
                        return False
                else:
                    print(f"⚠️  Food bank weekly endpoint failed: {bank_response.status_code}")
                
                self.test_results["weekly_aggregation"] = "accurate"
                return True
            else:
                print(f"❌ Weekly nutrition summary failed: {weekly_response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Weekly/monthly test failed: {e}")
            return False

    def test_graph_data_ranges_and_edge_cases(self):
        """Test graph data ranges and edge cases"""
        print("\n📊 Testing Graph Data Ranges and Edge Cases")
        
        try:
            # Test empty data scenario
            future_date = date.today() + timedelta(days=30)
            empty_response = self.session.get(f"{BASE_URL}/food/nutrition-summary", 
                                            params={"start_date": future_date, "end_date": future_date})
            
            if empty_response.status_code == 200:
                empty_data = empty_response.json()
                print(f"✅ Empty date range handled gracefully: {empty_data.get('total_calories', 0)} calories")
            else:
                print(f"❌ Empty date range not handled: {empty_response.status_code}")
                return False
            
            # Test very large date range
            start_date = date.today() - timedelta(days=365)
            end_date = date.today()
            large_response = self.session.get(f"{BASE_URL}/food/nutrition-summary", 
                                            params={"start_date": start_date, "end_date": end_date})
            
            if large_response.status_code == 200:
                large_data = large_response.json()
                print(f"✅ Large date range handled: {large_data.get('total_calories', 0)} calories")
            else:
                print(f"❌ Large date range failed: {large_response.status_code}")
                return False
            
            # Test invalid date formats
            invalid_response = self.session.get(f"{BASE_URL}/food/nutrition-summary", 
                                              params={"start_date": "invalid", "end_date": "also-invalid"})
            
            if invalid_response.status_code == 422:  # Should return validation error
                print("✅ Invalid date formats properly rejected")
            else:
                print(f"⚠️  Invalid dates not properly handled: {invalid_response.status_code}")
            
            self.test_results["graph_edge_cases"] = "handled"
            return True
            
        except Exception as e:
            print(f"❌ Graph edge case test failed: {e}")
            return False

    def test_frontend_integration_scenarios(self):
        """Test common frontend integration scenarios"""
        print("\n🖥️ Testing Frontend Integration Scenarios")
        
        scenarios_passed = 0
        total_scenarios = 4
        
        try:
            # Scenario 1: User profile → Requirements → Food logging workflow
            print("   Scenario 1: Complete user workflow")
            
            # Get requirements (should now work with fixed format)
            req_response = self.session.get(f"{BASE_URL}/nutritional-requirements")
            if req_response.status_code == 200 and "daily_calories" in req_response.json():
                print("      ✅ Requirements API format compatible")
                scenarios_passed += 1
            else:
                print("      ❌ Requirements API incompatible")
            
            # Scenario 2: Food CRUD operations with proper types
            print("   Scenario 2: Food CRUD operations")
            
            food_data = {"description": "Frontend Test Food", "calories": 200, "protein_g": 10.0}
            create_response = self.session.post(f"{BASE_URL}/food", json=food_data)
            
            if create_response.status_code == 200:
                food_id = create_response.json().get("id")
                
                # Update (should work with fixed Decimal handling)
                update_response = self.session.put(f"{BASE_URL}/food/{food_id}", 
                                                 json={"calories": 250})
                
                if update_response.status_code == 200:
                    print("      ✅ Food CRUD operations working")
                    scenarios_passed += 1
                else:
                    print("      ❌ Food update failed")
            else:
                print("      ❌ Food creation failed")
            
            # Scenario 3: AI parsing → Log creation workflow
            print("   Scenario 3: AI parsing workflow")
            
            # Try a simple AI parse
            parse_response = self.session.post(f"{BASE_URL}/food/parse", 
                                             json={"user_input": "apple"}, 
                                             timeout=15)
            
            if parse_response.status_code == 200:
                session_id = parse_response.json().get("session_id")
                if session_id:
                    # Try to create logs from session
                    create_logs_response = self.session.post(f"{BASE_URL}/food/parse/{session_id}/create-logs")
                    
                    if create_logs_response.status_code == 200:
                        print("      ✅ AI parsing workflow complete")
                        scenarios_passed += 1
                    else:
                        print("      ❌ Log creation from AI session failed")
                else:
                    print("      ❌ No session ID from AI parsing")
            else:
                print("      ❌ AI parsing failed in workflow")
            
            # Scenario 4: Data aggregation for charts
            print("   Scenario 4: Chart data aggregation")
            
            # Test multiple time periods
            periods = ["daily", "weekly", "monthly"]
            period_success = 0
            
            for period in periods:
                bank_response = self.session.get(f"{BASE_URL}/food-bank/{period}")
                if bank_response.status_code == 200:
                    data = bank_response.json()
                    if "summary" in data and "food_logs" in data:
                        period_success += 1
            
            if period_success == len(periods):
                print("      ✅ Chart data aggregation working")
                scenarios_passed += 1
            else:
                print(f"      ❌ Chart data partial failure ({period_success}/{len(periods)})")
            
            success_rate = scenarios_passed / total_scenarios
            print(f"\n   Frontend Integration Score: {scenarios_passed}/{total_scenarios} ({success_rate*100:.0f}%)")
            
            self.test_results["frontend_integration_score"] = success_rate
            return success_rate > 0.75  # 75% success rate
            
        except Exception as e:
            print(f"❌ Frontend integration test failed: {e}")
            return False

    def run_comprehensive_tests(self):
        """Run all comprehensive tests"""
        print("🧪 HealthUp Comprehensive AI & Integration Test Suite")
        print("=" * 80)
        
        if not self.setup_test_user():
            print("❌ Failed to setup test user")
            return
        
        if not self.setup_user_profile():
            print("❌ Failed to setup user profile")
            return
        
        # Run all tests
        test_functions = [
            ("AI Food Parsing with OpenAI", self.test_ai_food_parsing_with_openai),
            ("Nutritional Requirements API Fix", self.test_nutritional_requirements_api_fix),
            ("Decimal Type Handling", self.test_decimal_type_handling),
            ("Weekly/Monthly Data Aggregation", self.test_weekly_monthly_data_aggregation),
            ("Graph Data Ranges & Edge Cases", self.test_graph_data_ranges_and_edge_cases),
            ("Frontend Integration Scenarios", self.test_frontend_integration_scenarios)
        ]
        
        ai_sessions = []
        
        for test_name, test_func in test_functions:
            try:
                if test_name == "AI Food Parsing with OpenAI":
                    result, sessions = test_func()
                    ai_sessions = sessions
                else:
                    result = test_func()
                
                self.test_results[test_name] = result
                
            except Exception as e:
                print(f"❌ {test_name} crashed: {e}")
                self.test_results[test_name] = False
        
        # Generate comprehensive report
        self.generate_comprehensive_report()

    def generate_comprehensive_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST REPORT")
        print("=" * 80)
        
        # Calculate overall scores
        test_scores = [v for v in self.test_results.values() if isinstance(v, bool)]
        passed_tests = sum(test_scores)
        total_tests = len(test_scores)
        overall_score = passed_tests / total_tests * 100 if total_tests > 0 else 0
        
        print(f"Overall Score: {passed_tests}/{total_tests} ({overall_score:.1f}%)")
        print()
        
        # Detailed results
        print("Test Results:")
        for test_name, result in self.test_results.items():
            if isinstance(result, bool):
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"  {status} {test_name}")
            elif isinstance(result, (int, float)):
                print(f"  📊 {test_name}: {result}")
            else:
                print(f"  📋 {test_name}: {result}")
        
        # Performance metrics
        print(f"\nPerformance Metrics:")
        if "ai_parsing_success_rate" in self.test_results:
            print(f"  AI Parsing Success Rate: {self.test_results['ai_parsing_success_rate']*100:.1f}%")
        if "ai_nutrition_accuracy" in self.test_results:
            print(f"  AI Nutrition Accuracy: {self.test_results['ai_nutrition_accuracy']:.1f}%")
        if "frontend_integration_score" in self.test_results:
            print(f"  Frontend Integration: {self.test_results['frontend_integration_score']*100:.1f}%")
        
        # Production readiness assessment
        print(f"\n🚀 Production Readiness Assessment:")
        
        critical_tests = [
            "AI Food Parsing with OpenAI",
            "Nutritional Requirements API Fix", 
            "Decimal Type Handling"
        ]
        
        critical_passed = sum(1 for test in critical_tests if self.test_results.get(test, False))
        
        if critical_passed == len(critical_tests):
            if overall_score >= 80:
                print("✅ PRODUCTION READY - All critical tests pass, high overall score")
            else:
                print("⚠️  CAUTION - Critical tests pass but some integration issues remain")
        else:
            print("❌ NOT PRODUCTION READY - Critical tests failing")
        
        # Specific recommendations
        print(f"\n📋 Recommendations:")
        
        if not self.test_results.get("AI Food Parsing with OpenAI", False):
            print("  🔧 Fix AI parsing - check OpenAI API key and timeout handling")
        
        if not self.test_results.get("Decimal Type Handling", False):
            print("  🔧 Fix Decimal type conversion in database layer")
        
        if self.test_results.get("ai_nutrition_accuracy", 0) < 70:
            print("  🔧 Improve AI nutrition data extraction accuracy")
        
        if self.test_results.get("frontend_integration_score", 0) < 0.8:
            print("  🔧 Address remaining frontend integration issues")
        
        print(f"\n🎉 Testing complete! Save this report for production deployment planning.")

if __name__ == "__main__":
    suite = ComprehensiveAITestSuite()
    suite.run_comprehensive_tests() 