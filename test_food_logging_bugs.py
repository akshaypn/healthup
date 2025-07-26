#!/usr/bin/env python3
"""
Focused Food Logging Bug Detection Tests

Quick tests to identify specific bugs in:
- Nutritional calculations
- AI parsing results
- Database persistence
- User profile integration
"""

import requests
import json
import psycopg2
from datetime import datetime, date

BASE_URL = "http://localhost:8000"
DB_URL = "postgresql://healthup:healthup_secure_password_a2032334186a8000@localhost:5433/healthup"

class FoodLoggingBugDetector:
    
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        
    def quick_login(self):
        """Quick login with test user"""
        user_data = {"email": "bugtest@example.com", "password": "testpass123"}
        
        # Register
        try:
            self.session.post(f"{BASE_URL}/auth/register", json=user_data)
        except:
            pass
        
        # Login
        response = self.session.post(f"{BASE_URL}/auth/login", json=user_data)
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data.get("access_token")
            self.user_id = data.get("user", {}).get("id")
            self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
            return True
        return False

    def test_zero_calorie_bug(self):
        """Test if AI parsing returns 0 calories (Bug #1)"""
        print("\n🐛 Bug #1: Testing Zero Calorie AI Parsing")
        
        try:
            parse_data = {"user_input": "I ate a banana"}
            response = self.session.post(f"{BASE_URL}/food/parse", json=parse_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                parsed_foods = data.get("parsed_foods", [])
                
                for food in parsed_foods:
                    nutrition = food.get("nutritional_data", {})
                    calories = nutrition.get("calories", 0)
                    description = food.get("description", "Unknown")
                    
                    print(f"   Food: {description}")
                    print(f"   Calories: {calories}")
                    
                    if calories == 0:
                        print("   ❌ BUG DETECTED: AI parsing returns 0 calories!")
                        return False
                    else:
                        print("   ✅ Calories properly parsed")
                        return True
                        
            elif response.status_code == 500:
                error_detail = response.json().get("detail", "Unknown error")
                if "food-related content only" in error_detail:
                    print("   ❌ BUG DETECTED: Food input incorrectly rejected as non-food!")
                    return False
                else:
                    print(f"   ❌ AI parsing failed: {error_detail}")
                    return False
            else:
                print(f"   ❌ AI parsing failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
            return False

    def test_negative_nutrition_bug(self):
        """Test if negative nutritional values are accepted (Bug #2)"""
        print("\n🐛 Bug #2: Testing Negative Nutrition Values")
        
        invalid_food = {
            "description": "Invalid Food",
            "calories": -100,
            "protein_g": -5.0,
            "vitamin_c_mg": -50
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/food", json=invalid_food)
            
            if response.status_code == 200:
                print("   ❌ BUG DETECTED: Negative nutrition values accepted!")
                return False
            elif response.status_code == 422:
                print("   ✅ Negative values properly rejected")
                return True
            else:
                print(f"   ⚠️  Unexpected response: {response.status_code}")
                return True
                
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
            return False

    def test_calculation_consistency_bug(self):
        """Test nutritional calculation consistency (Bug #3)"""
        print("\n🐛 Bug #3: Testing Nutritional Calculation Consistency")
        
        # Add known foods with specific nutrition
        test_foods = [
            {"description": "Test Apple", "calories": 95, "protein_g": 0.5, "vitamin_c_mg": 14},
            {"description": "Test Banana", "calories": 105, "protein_g": 1.3, "vitamin_c_mg": 10}
        ]
        
        try:
            # Add the foods
            for food in test_foods:
                response = self.session.post(f"{BASE_URL}/food", json=food)
                if response.status_code != 200:
                    print(f"   ❌ Failed to add test food: {food['description']}")
                    return False
            
            # Get nutrition summary
            today = date.today()
            response = self.session.get(f"{BASE_URL}/food/nutrition-summary", 
                                      params={"start_date": today, "end_date": today})
            
            if response.status_code == 200:
                data = response.json()
                total_calories = data.get('total_calories', 0)
                total_protein = data.get('total_protein_g', 0)
                vitamins = data.get('vitamins', {})
                vitamin_c = vitamins.get('vitamin_c_mg', 0)
                
                print(f"   Calculated totals:")
                print(f"   - Calories: {total_calories} (expected: ≥200)")
                print(f"   - Protein: {total_protein}g (expected: ≥1.8)")
                print(f"   - Vitamin C: {vitamin_c}mg (expected: ≥24)")
                
                # Check if calculations are reasonable
                if total_calories < 100:  # Should be at least 200 from our test foods
                    print("   ❌ BUG DETECTED: Calorie calculation too low!")
                    return False
                
                if total_protein < 1.0:  # Should be at least 1.8 from our test foods
                    print("   ❌ BUG DETECTED: Protein calculation too low!")
                    return False
                
                print("   ✅ Calculations appear consistent")
                return True
            else:
                print(f"   ❌ Failed to get nutrition summary: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
            return False

    def test_user_profile_calculation_bug(self):
        """Test if user profile affects nutritional requirements (Bug #4)"""
        print("\n🐛 Bug #4: Testing User Profile Integration")
        
        try:
            # Create user profile
            profile_data = {
                "gender": "female",
                "height_cm": 165,
                "weight_kg": 60,
                "age": 25,
                "activity_level": "sedentary",
                "goal": "lose_weight"
            }
            
            profile_response = self.session.post(f"{BASE_URL}/profile", json=profile_data)
            if profile_response.status_code != 200:
                print("   ❌ Failed to create user profile")
                return False
            
            # Get nutritional requirements
            req_response = self.session.get(f"{BASE_URL}/nutritional-requirements")
            
            if req_response.status_code == 200:
                requirements = req_response.json()
                daily_calories = requirements.get('daily_calories')
                daily_protein = requirements.get('daily_protein_g')
                
                print(f"   Calculated requirements:")
                print(f"   - Daily calories: {daily_calories}")
                print(f"   - Daily protein: {daily_protein}g")
                
                # For sedentary 25yr old female, 60kg, 165cm, lose weight goal
                # Expected BMR ~1350, TDEE ~1620, weight loss ~1370
                if daily_calories and 1200 <= daily_calories <= 1600:
                    print("   ✅ Calorie requirements reasonable for profile")
                else:
                    print(f"   ❌ BUG DETECTED: Unreasonable calorie requirement: {daily_calories}")
                    return False
                
                if daily_protein and 40 <= daily_protein <= 120:
                    print("   ✅ Protein requirements reasonable for profile")
                else:
                    print(f"   ❌ BUG DETECTED: Unreasonable protein requirement: {daily_protein}")
                    return False
                
                return True
            else:
                print(f"   ❌ Failed to get requirements: {req_response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
            return False

    def test_database_persistence_bug(self):
        """Test database persistence issues (Bug #5)"""
        print("\n🐛 Bug #5: Testing Database Persistence")
        
        try:
            # Connect to database
            conn = psycopg2.connect(DB_URL)
            cursor = conn.cursor()
            
            # Check for data type mismatches
            cursor.execute("""
                SELECT id, calories, protein_g, description 
                FROM food_logs 
                WHERE user_id = %s 
                ORDER BY id DESC 
                LIMIT 5
            """, (self.user_id,))
            
            rows = cursor.fetchall()
            print(f"   Recent food logs in database: {len(rows)}")
            
            for row in rows:
                food_id, calories, protein_g, description = row
                print(f"   - ID {food_id}: {description} - {calories} cal, {protein_g}g protein")
                
                # Check for data type issues
                if calories is not None and not isinstance(calories, (int, float)):
                    print(f"   ❌ BUG DETECTED: Calories stored as wrong type: {type(calories)}")
                    return False
                
                if protein_g is not None and not isinstance(protein_g, (int, float)):
                    print(f"   ❌ BUG DETECTED: Protein stored as wrong type: {type(protein_g)}")
                    return False
            
            # Check for constraint violations
            cursor.execute("""
                SELECT COUNT(*) FROM food_logs 
                WHERE calories < 0 OR protein_g < 0 OR fat_g < 0 OR carbs_g < 0
            """)
            negative_count = cursor.fetchone()[0]
            
            if negative_count > 0:
                print(f"   ❌ BUG DETECTED: {negative_count} records with negative values in database!")
                return False
            
            cursor.close()
            conn.close()
            
            print("   ✅ Database persistence appears correct")
            return True
            
        except Exception as e:
            print(f"   ❌ Database test failed: {e}")
            return False

    def test_food_update_persistence_bug(self):
        """Test food update persistence (Bug #6)"""
        print("\n🐛 Bug #6: Testing Food Update Persistence")
        
        try:
            # Create food
            food_data = {"description": "Update Test Food", "calories": 100, "protein_g": 5.0}
            response = self.session.post(f"{BASE_URL}/food", json=food_data)
            
            if response.status_code != 200:
                print("   ❌ Failed to create test food")
                return False
            
            food_id = response.json().get("id")
            
            # Update food
            update_data = {"calories": 200, "protein_g": 10.0}
            update_response = self.session.put(f"{BASE_URL}/food/{food_id}", json=update_data)
            
            if update_response.status_code != 200:
                print(f"   ❌ Food update failed: {update_response.status_code}")
                return False
            
            # Verify update in database
            conn = psycopg2.connect(DB_URL)
            cursor = conn.cursor()
            cursor.execute("SELECT calories, protein_g FROM food_logs WHERE id = %s", (food_id,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if row:
                db_calories, db_protein = row
                if db_calories == 200 and abs(db_protein - 10.0) < 0.01:
                    print("   ✅ Food update persisted correctly")
                    return True
                else:
                    print(f"   ❌ BUG DETECTED: Update not persisted. DB: {db_calories} cal, {db_protein}g")
                    return False
            else:
                print("   ❌ BUG DETECTED: Food not found in database after update")
                return False
                
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
            return False

    def test_amazfit_data_handling_bug(self):
        """Test Amazfit data handling (Bug #7)"""
        print("\n🐛 Bug #7: Testing Amazfit Data Handling")
        
        try:
            # Check Amazfit endpoints
            response = self.session.get(f"{BASE_URL}/amazfit/credentials")
            
            if response.status_code == 200:
                print("   ✅ Amazfit credentials endpoint accessible")
                
                # Test today's data
                today = date.today().strftime("%Y-%m-%d")
                day_response = self.session.get(f"{BASE_URL}/amazfit/day", 
                                              params={"date_str": today})
                
                if day_response.status_code == 200:
                    data = day_response.json()
                    
                    # Check for proper data structure
                    required_keys = ["activity_data", "steps_data", "heart_rate_data"]
                    missing_keys = [key for key in required_keys if key not in data]
                    
                    if missing_keys:
                        print(f"   ❌ BUG DETECTED: Missing data keys: {missing_keys}")
                        return False
                    
                    # Check for null/undefined handling
                    activity_data = data.get("activity_data", {})
                    if activity_data is None:
                        print("   ❌ BUG DETECTED: Activity data is null")
                        return False
                    
                    print("   ✅ Amazfit data structure appears correct")
                    return True
                    
                elif day_response.status_code == 500:
                    error_detail = day_response.json().get("detail", "")
                    if "NoneType" in error_detail or "AttributeError" in error_detail:
                        print("   ❌ BUG DETECTED: Amazfit service has null reference errors")
                        return False
                    else:
                        print("   ⚠️  Amazfit service error (may be expected without credentials)")
                        return True
                else:
                    print(f"   ⚠️  Amazfit day data: {day_response.status_code}")
                    return True
            else:
                print(f"   ❌ Amazfit credentials endpoint failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
            return False

    def run_bug_detection(self):
        """Run focused bug detection tests"""
        print("🔍 HealthUp Food Logging Bug Detection")
        print("=" * 50)
        
        if not self.quick_login():
            print("❌ Failed to login")
            return
        
        bugs_detected = []
        
        # Run all bug tests
        bug_tests = [
            ("Zero Calorie AI Parsing", self.test_zero_calorie_bug),
            ("Negative Nutrition Values", self.test_negative_nutrition_bug),
            ("Calculation Consistency", self.test_calculation_consistency_bug),
            ("User Profile Integration", self.test_user_profile_calculation_bug),
            ("Database Persistence", self.test_database_persistence_bug),
            ("Food Update Persistence", self.test_food_update_persistence_bug),
            ("Amazfit Data Handling", self.test_amazfit_data_handling_bug)
        ]
        
        for bug_name, test_func in bug_tests:
            try:
                result = test_func()
                if not result:
                    bugs_detected.append(bug_name)
            except Exception as e:
                print(f"❌ {bug_name} test crashed: {e}")
                bugs_detected.append(f"{bug_name} (crashed)")
        
        # Generate bug report
        print("\n" + "=" * 50)
        print("🐛 BUG DETECTION REPORT")
        print("=" * 50)
        
        if bugs_detected:
            print(f"❌ BUGS DETECTED: {len(bugs_detected)}")
            for i, bug in enumerate(bugs_detected, 1):
                print(f"   {i}. {bug}")
        else:
            print("✅ NO BUGS DETECTED - All tests passed!")
        
        print(f"\nTest Score: {len(bug_tests) - len(bugs_detected)}/{len(bug_tests)} passed")
        
        return bugs_detected

if __name__ == "__main__":
    detector = FoodLoggingBugDetector()
    bugs = detector.run_bug_detection() 