import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from . import models, schemas
import re
from pydantic import BaseModel
from openai import OpenAI
import json

logger = logging.getLogger(__name__)

# Enhanced schemas for comprehensive nutrition data
class Nutrients(BaseModel):
    dish: str
    calories_kcal: float
    protein_g: float
    fat_g: float
    carbs_g: float
    fiber_g: Optional[float] = None
    sugar_g: Optional[float] = None
    sodium_mg: Optional[float] = None
    # Comprehensive vitamin and mineral data
    vitamin_a_mcg: Optional[float] = None
    vitamin_c_mg: Optional[float] = None
    vitamin_d_mcg: Optional[float] = None
    vitamin_e_mg: Optional[float] = None
    vitamin_k_mcg: Optional[float] = None
    vitamin_b1_mg: Optional[float] = None
    vitamin_b2_mg: Optional[float] = None
    vitamin_b3_mg: Optional[float] = None
    vitamin_b5_mg: Optional[float] = None
    vitamin_b6_mg: Optional[float] = None
    vitamin_b7_mcg: Optional[float] = None
    vitamin_b9_mcg: Optional[float] = None
    vitamin_b12_mcg: Optional[float] = None
    calcium_mg: Optional[float] = None
    iron_mg: Optional[float] = None
    magnesium_mg: Optional[float] = None
    phosphorus_mg: Optional[float] = None
    potassium_mg: Optional[float] = None
    zinc_mg: Optional[float] = None
    copper_mg: Optional[float] = None
    manganese_mg: Optional[float] = None
    selenium_mcg: Optional[float] = None
    chromium_mcg: Optional[float] = None
    molybdenum_mcg: Optional[float] = None
    cholesterol_mg: Optional[float] = None
    saturated_fat_g: Optional[float] = None
    trans_fat_g: Optional[float] = None
    polyunsaturated_fat_g: Optional[float] = None
    monounsaturated_fat_g: Optional[float] = None

class MealAnalysis(BaseModel):
    overall_health_score: float
    protein_adequacy: str
    fiber_content: str
    vitamin_balance: str
    mineral_balance: str
    recommendations: List[str]

class FoodParserService:
    """AI-powered food parsing service using OpenAI with comprehensive nutrition data"""
    
    def __init__(self, mcp_config: schemas.MCPServerConfig):
        self.mcp_config = mcp_config
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def parse_food_input(self, user_input: str, user_id: str, db: Session) -> schemas.FoodParsingResponse:
        """Parse natural language food input using AI with comprehensive nutrition data"""
        session = None
        try:
            # Create parsing session
            session = models.FoodParsingSession(
                session_id=f"session_{user_id}_{datetime.utcnow().timestamp()}",
                user_id=user_id,
                user_input=user_input,
                status="processing",
                created_at=datetime.utcnow()
            )
            db.add(session)
            db.commit()
            
            # Extract dishes using AI
            dishes = await self._extract_dishes_with_ai(user_input)
            
            # Get comprehensive nutrition data using AI
            nutrition_data = await self._get_comprehensive_nutrition_data(dishes)
            
            # Generate meal analysis
            meal_analysis = await self._generate_meal_analysis(nutrition_data)
            
            # Extract datetime and meal type
            extracted_datetime = self._extract_datetime_from_text(user_input)
            meal_type = self._extract_meal_type(user_input)
            
            # Prepare parsed foods with comprehensive nutrition data
            parsed_foods = []
            for i, dish in enumerate(dishes):
                nutrition = nutrition_data[i] if i < len(nutrition_data) else None
                food_data = {
                    "description": dish,
                    "serving_size": "1 serving",
                    "meal_type": meal_type,
                    "confidence_score": 0.9,
                    "nutritional_data": nutrition.dict() if nutrition else {
                        "calories_kcal": 0,
                        "protein_g": 0,
                        "fat_g": 0,
                        "carbs_g": 0,
                        "fiber_g": 0,
                        "sugar_g": 0,
                        "sodium_mg": 0,
                    }
                }
                parsed_foods.append(food_data)
            
            # Update session
            session.status = "completed"
            session.parsed_foods = parsed_foods
            session.extracted_datetime = extracted_datetime
            session.meal_analysis = meal_analysis.dict() if meal_analysis else None
            db.commit()
            
            return schemas.FoodParsingResponse(
                session_id=session.session_id,
                status="completed",
                parsed_foods=parsed_foods,
                meal_analysis=meal_analysis.dict() if meal_analysis else None,
                extracted_datetime=extracted_datetime,
                confidence_score=0.9,
                meal_type=meal_type
            )
            
        except Exception as e:
            logger.error(f"Error parsing food input: {str(e)}")
            if session:
                session.status = "failed"
                session.error_message = str(e)
                db.commit()
            raise

    async def _extract_dishes_with_ai(self, user_input: str) -> List[str]:
        """Extract dishes from user input using AI"""
        prompt = f"""
        You are a food logging assistant. Extract ONLY the food items from this text: "{user_input}"
        
        Return ONLY a comma-separated list of food items. Do not include any other text.
        
        Examples:
        Input: "I had 1 banana in the morning for breakfast"
        Output: "banana"
        
        Input: "I ate chicken rice and vegetables for lunch"
        Output: "chicken, rice, vegetables"
        
        Input: "Drank coffee with milk and sugar"
        Output: "coffee, milk, sugar"
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a food extraction assistant. Extract only food items from text."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            dishes_text = response.choices[0].message.content.strip()
            # Clean up the response and split by comma
            dishes = [dish.strip().lower() for dish in dishes_text.split(',') if dish.strip()]
            return dishes
            
        except Exception as e:
            logger.error(f"Error extracting dishes: {str(e)}")
            # Fallback: extract simple words that might be food
            words = user_input.lower().split()
            food_keywords = ['banana', 'apple', 'oatmeal', 'rice', 'chicken', 'bread', 'milk', 'egg', 'eggs', 'coffee', 'tea', 'vegetables', 'salad', 'pasta', 'pizza', 'burger', 'sandwich', 'soup', 'yogurt', 'cheese', 'meat', 'fish', 'beef', 'pork', 'lamb', 'turkey', 'duck', 'shrimp', 'salmon', 'tuna', 'cod', 'tilapia', 'tofu', 'beans', 'lentils', 'chickpeas', 'quinoa', 'couscous', 'potato', 'sweet potato', 'carrot', 'broccoli', 'spinach', 'kale', 'lettuce', 'tomato', 'onion', 'garlic', 'ginger', 'pepper', 'salt', 'oil', 'butter', 'cream', 'sugar', 'honey', 'syrup', 'jam', 'jelly', 'peanut butter', 'almond butter', 'nuts', 'almonds', 'walnuts', 'cashews', 'peanuts', 'seeds', 'chia', 'flax', 'sunflower', 'pumpkin']
            dishes = [word for word in words if word in food_keywords]
            return dishes if dishes else ['unknown food']

    async def _get_comprehensive_nutrition_data(self, dishes: List[str]) -> List[Nutrients]:
        """Get comprehensive nutrition data for dishes using AI"""
        if not dishes:
            return []
        
        nutrition_items = []
        
        for dish in dishes:
            try:
                prompt = f"""
                Provide comprehensive nutritional information for {dish} per serving (1 serving).
                
                Return ONLY a JSON object with this exact structure:
                {{
                    "calories_kcal": number,
                    "protein_g": number,
                    "fat_g": number,
                    "carbs_g": number,
                    "fiber_g": number,
                    "sugar_g": number,
                    "sodium_mg": number,
                    "vitamin_a_mcg": number,
                    "vitamin_c_mg": number,
                    "vitamin_d_mcg": number,
                    "vitamin_e_mg": number,
                    "vitamin_k_mcg": number,
                    "vitamin_b1_mg": number,
                    "vitamin_b2_mg": number,
                    "vitamin_b3_mg": number,
                    "vitamin_b5_mg": number,
                    "vitamin_b6_mg": number,
                    "vitamin_b7_mcg": number,
                    "vitamin_b9_mcg": number,
                    "vitamin_b12_mcg": number,
                    "calcium_mg": number,
                    "iron_mg": number,
                    "magnesium_mg": number,
                    "phosphorus_mg": number,
                    "potassium_mg": number,
                    "zinc_mg": number,
                    "copper_mg": number,
                    "manganese_mg": number,
                    "selenium_mcg": number,
                    "chromium_mcg": number,
                    "molybdenum_mcg": number,
                    "cholesterol_mg": number,
                    "saturated_fat_g": number,
                    "trans_fat_g": number,
                    "polyunsaturated_fat_g": number,
                    "monounsaturated_fat_g": number
                }}
                
                Use realistic nutritional values based on standard serving sizes. If a nutrient is not present or negligible, use 0.
                """
                
                response = self.openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a nutrition expert. Provide accurate nutritional data in JSON format."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1000,
                    temperature=0.1
                )
                
                response_text = response.choices[0].message.content.strip()
                
                # Clean up JSON response
                if response_text.startswith('```json'):
                    response_text = response_text[7:-3]
                elif response_text.startswith('```'):
                    response_text = response_text[3:-3]
                
                # Parse JSON
                nutrition_dict = json.loads(response_text)
                
                nutrition = Nutrients(
                    dish=dish,
                    calories_kcal=nutrition_dict.get("calories_kcal", 0),
                    protein_g=nutrition_dict.get("protein_g", 0),
                    fat_g=nutrition_dict.get("fat_g", 0),
                    carbs_g=nutrition_dict.get("carbs_g", 0),
                    fiber_g=nutrition_dict.get("fiber_g", 0),
                    sugar_g=nutrition_dict.get("sugar_g", 0),
                    sodium_mg=nutrition_dict.get("sodium_mg", 0),
                    vitamin_a_mcg=nutrition_dict.get("vitamin_a_mcg", 0),
                    vitamin_c_mg=nutrition_dict.get("vitamin_c_mg", 0),
                    vitamin_d_mcg=nutrition_dict.get("vitamin_d_mcg", 0),
                    vitamin_e_mg=nutrition_dict.get("vitamin_e_mg", 0),
                    vitamin_k_mcg=nutrition_dict.get("vitamin_k_mcg", 0),
                    vitamin_b1_mg=nutrition_dict.get("vitamin_b1_mg", 0),
                    vitamin_b2_mg=nutrition_dict.get("vitamin_b2_mg", 0),
                    vitamin_b3_mg=nutrition_dict.get("vitamin_b3_mg", 0),
                    vitamin_b5_mg=nutrition_dict.get("vitamin_b5_mg", 0),
                    vitamin_b6_mg=nutrition_dict.get("vitamin_b6_mg", 0),
                    vitamin_b7_mcg=nutrition_dict.get("vitamin_b7_mcg", 0),
                    vitamin_b9_mcg=nutrition_dict.get("vitamin_b9_mcg", 0),
                    vitamin_b12_mcg=nutrition_dict.get("vitamin_b12_mcg", 0),
                    calcium_mg=nutrition_dict.get("calcium_mg", 0),
                    iron_mg=nutrition_dict.get("iron_mg", 0),
                    magnesium_mg=nutrition_dict.get("magnesium_mg", 0),
                    phosphorus_mg=nutrition_dict.get("phosphorus_mg", 0),
                    potassium_mg=nutrition_dict.get("potassium_mg", 0),
                    zinc_mg=nutrition_dict.get("zinc_mg", 0),
                    copper_mg=nutrition_dict.get("copper_mg", 0),
                    manganese_mg=nutrition_dict.get("manganese_mg", 0),
                    selenium_mcg=nutrition_dict.get("selenium_mcg", 0),
                    chromium_mcg=nutrition_dict.get("chromium_mcg", 0),
                    molybdenum_mcg=nutrition_dict.get("molybdenum_mcg", 0),
                    cholesterol_mg=nutrition_dict.get("cholesterol_mg", 0),
                    saturated_fat_g=nutrition_dict.get("saturated_fat_g", 0),
                    trans_fat_g=nutrition_dict.get("trans_fat_g", 0),
                    polyunsaturated_fat_g=nutrition_dict.get("polyunsaturated_fat_g", 0),
                    monounsaturated_fat_g=nutrition_dict.get("monounsaturated_fat_g", 0),
                )
                nutrition_items.append(nutrition)
                
            except Exception as e:
                logger.error(f"Error getting nutrition for {dish}: {str(e)}")
                # Fallback nutrition data with more comprehensive values
                nutrition = Nutrients(
                    dish=dish,
                    calories_kcal=150,
                    protein_g=5,
                    fat_g=3,
                    carbs_g=25,
                    fiber_g=3,
                    sugar_g=8,
                    sodium_mg=50,
                    # Add some basic vitamin and mineral values
                    vitamin_a_mcg=50,
                    vitamin_c_mg=10,
                    vitamin_d_mcg=1,
                    vitamin_e_mg=2,
                    vitamin_k_mcg=10,
                    vitamin_b1_mg=0.1,
                    vitamin_b2_mg=0.1,
                    vitamin_b3_mg=2,
                    vitamin_b5_mg=0.5,
                    vitamin_b6_mg=0.1,
                    vitamin_b7_mcg=5,
                    vitamin_b9_mcg=20,
                    vitamin_b12_mcg=0.5,
                    calcium_mg=50,
                    iron_mg=1,
                    magnesium_mg=25,
                    phosphorus_mg=50,
                    potassium_mg=200,
                    zinc_mg=0.5,
                    copper_mg=0.1,
                    manganese_mg=0.5,
                    selenium_mcg=5,
                    chromium_mcg=1,
                    molybdenum_mcg=1,
                    cholesterol_mg=10,
                    saturated_fat_g=1,
                    trans_fat_g=0,
                    polyunsaturated_fat_g=1,
                    monounsaturated_fat_g=1,
                )
                nutrition_items.append(nutrition)
        
        return nutrition_items

    async def _generate_meal_analysis(self, nutrition_data: List[Nutrients]) -> Optional[MealAnalysis]:
        """Generate meal analysis using AI"""
        if not nutrition_data:
            return None
        
        total_calories = sum(item.calories_kcal for item in nutrition_data)
        total_protein = sum(item.protein_g for item in nutrition_data)
        total_fat = sum(item.fat_g for item in nutrition_data)
        total_carbs = sum(item.carbs_g for item in nutrition_data)
        total_fiber = sum(item.fiber_g or 0 for item in nutrition_data)
        
        nutrition_summary = f"""
        Total calories: {total_calories} kcal
        Total protein: {total_protein}g
        Total fat: {total_fat}g
        Total carbs: {total_carbs}g
        Total fiber: {total_fiber}g
        """
        
        prompt = f"""
        Analyze this meal's nutritional profile and provide health insights and recommendations.
        
        {nutrition_summary}

        Return ONLY a JSON object with this exact structure:
        {{
          "overall_health_score": 75.0,
          "protein_adequacy": "Adequate protein content",
          "fiber_content": "Good fiber content", 
          "vitamin_balance": "Good vitamin balance",
          "mineral_balance": "Good mineral balance",
          "recommendations": ["Consider adding more vegetables", "Stay hydrated"]
        }}
        
        Do not include any other text, only the JSON object.
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a nutrition expert. Analyze meals and provide health insights. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Clean up the response
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]
            
            # Remove any leading/trailing whitespace
            response_text = response_text.strip()
            
            # Check if response is empty or invalid
            if not response_text:
                logger.warning("Empty response from AI for meal analysis")
                return self._generate_fallback_meal_analysis(nutrition_data)
            
            data = json.loads(response_text)
            return MealAnalysis(
                overall_health_score=data.get("overall_health_score", 70.0),
                protein_adequacy=data.get("protein_adequacy", "Adequate"),
                fiber_content=data.get("fiber_content", "Moderate"),
                vitamin_balance=data.get("vitamin_balance", "Good"),
                mineral_balance=data.get("mineral_balance", "Good"),
                recommendations=data.get("recommendations", [])
            )
        except Exception as e:
            logger.warning(f"Failed to parse meal analysis: {e}")
            return self._generate_fallback_meal_analysis(nutrition_data)
    
    def _generate_fallback_meal_analysis(self, nutrition_data: List[Nutrients]) -> MealAnalysis:
        """Generate fallback meal analysis when AI fails"""
        total_calories = sum(item.calories_kcal for item in nutrition_data)
        total_protein = sum(item.protein_g for item in nutrition_data)
        total_fat = sum(item.fat_g for item in nutrition_data)
        total_carbs = sum(item.carbs_g for item in nutrition_data)
        total_fiber = sum(item.fiber_g or 0 for item in nutrition_data)
        
        # Calculate basic health score
        health_score = 70.0
        if total_protein >= 20:
            health_score += 10
        if total_fiber >= 5:
            health_score += 10
        if total_calories >= 300 and total_calories <= 800:
            health_score += 10
        
        # Determine adequacy levels
        protein_adequacy = "High" if total_protein >= 25 else "Adequate" if total_protein >= 15 else "Low"
        fiber_content = "High" if total_fiber >= 8 else "Adequate" if total_fiber >= 5 else "Low"
        
        # Generate basic recommendations
        recommendations = []
        if total_protein < 20:
            recommendations.append("Consider adding more protein-rich foods")
        if total_fiber < 5:
            recommendations.append("Add more fiber-rich foods like vegetables and whole grains")
        if total_calories < 300:
            recommendations.append("This seems like a light meal - consider adding more food")
        if total_calories > 800:
            recommendations.append("This is a large meal - consider portion control")
        
        if not recommendations:
            recommendations = ["Good meal composition", "Stay hydrated", "Consider adding vegetables"]
        
        return MealAnalysis(
            overall_health_score=health_score,
            protein_adequacy=protein_adequacy,
            fiber_content=fiber_content,
            vitamin_balance="Good",
            mineral_balance="Good",
            recommendations=recommendations
        )
    
    def _extract_datetime_from_text(self, text: str) -> Optional[datetime]:
        """Extract datetime from text"""
        now = datetime.now()
        
        # Common time patterns
        time_patterns = [
            (r'today', lambda: now.replace(hour=12, minute=0, second=0, microsecond=0)),
            (r'yesterday', lambda: (now - timedelta(days=1)).replace(hour=12, minute=0, second=0, microsecond=0)),
            (r'this morning', lambda: now.replace(hour=8, minute=0, second=0, microsecond=0)),
            (r'this afternoon', lambda: now.replace(hour=14, minute=0, second=0, microsecond=0)),
            (r'this evening', lambda: now.replace(hour=18, minute=0, second=0, microsecond=0)),
            (r'last night', lambda: (now - timedelta(days=1)).replace(hour=20, minute=0, second=0, microsecond=0)),
        ]
        
        for pattern, time_func in time_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return time_func()
        
        return None
    
    def _extract_meal_type(self, text: str) -> Optional[str]:
        """Extract meal type from text"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['breakfast', 'morning', 'coffee']):
            return "breakfast"
        elif any(word in text_lower for word in ['lunch', 'noon', 'midday']):
            return "lunch"
        elif any(word in text_lower for word in ['dinner', 'evening', 'night', 'supper']):
            return "dinner"
        elif any(word in text_lower for word in ['snack', 'snacks']):
            return "snack"
        
        return "meal"

    async def create_food_logs_from_session(self, session_id: str, user_id: str, db: Session) -> List[models.FoodLog]:
        """Create food logs from a parsing session"""
        try:
            # Get the session
            session = db.query(models.FoodParsingSession).filter(
                models.FoodParsingSession.session_id == session_id,
                models.FoodParsingSession.user_id == user_id
            ).first()
            
            if not session or not session.parsed_foods:
                return []
            
            food_logs = []
            for food_data in session.parsed_foods:
                # Create food log entry
                food_log = models.FoodLog(
                    user_id=user_id,
                    description=food_data["description"],
                    serving_size=food_data["serving_size"],
                    meal_type=food_data["meal_type"],
                    calories=food_data["nutritional_data"].get("calories_kcal", 0),
                    protein_g=food_data["nutritional_data"].get("protein_g", 0),
                    fat_g=food_data["nutritional_data"].get("fat_g", 0),
                    carbs_g=food_data["nutritional_data"].get("carbs_g", 0),
                    fiber_g=food_data["nutritional_data"].get("fiber_g", 0),
                    sugar_g=food_data["nutritional_data"].get("sugar_g", 0),
                    sodium_mg=food_data["nutritional_data"].get("sodium_mg", 0),
                    # Add all vitamins and minerals
                    vitamin_a_mcg=food_data["nutritional_data"].get("vitamin_a_mcg", 0),
                    vitamin_c_mg=food_data["nutritional_data"].get("vitamin_c_mg", 0),
                    vitamin_d_mcg=food_data["nutritional_data"].get("vitamin_d_mcg", 0),
                    vitamin_e_mg=food_data["nutritional_data"].get("vitamin_e_mg", 0),
                    vitamin_k_mcg=food_data["nutritional_data"].get("vitamin_k_mcg", 0),
                    vitamin_b1_mg=food_data["nutritional_data"].get("vitamin_b1_mg", 0),
                    vitamin_b2_mg=food_data["nutritional_data"].get("vitamin_b2_mg", 0),
                    vitamin_b3_mg=food_data["nutritional_data"].get("vitamin_b3_mg", 0),
                    vitamin_b5_mg=food_data["nutritional_data"].get("vitamin_b5_mg", 0),
                    vitamin_b6_mg=food_data["nutritional_data"].get("vitamin_b6_mg", 0),
                    vitamin_b7_mcg=food_data["nutritional_data"].get("vitamin_b7_mcg", 0),
                    vitamin_b9_mcg=food_data["nutritional_data"].get("vitamin_b9_mcg", 0),
                    vitamin_b12_mcg=food_data["nutritional_data"].get("vitamin_b12_mcg", 0),
                    calcium_mg=food_data["nutritional_data"].get("calcium_mg", 0),
                    iron_mg=food_data["nutritional_data"].get("iron_mg", 0),
                    magnesium_mg=food_data["nutritional_data"].get("magnesium_mg", 0),
                    phosphorus_mg=food_data["nutritional_data"].get("phosphorus_mg", 0),
                    potassium_mg=food_data["nutritional_data"].get("potassium_mg", 0),
                    zinc_mg=food_data["nutritional_data"].get("zinc_mg", 0),
                    copper_mg=food_data["nutritional_data"].get("copper_mg", 0),
                    manganese_mg=food_data["nutritional_data"].get("manganese_mg", 0),
                    selenium_mcg=food_data["nutritional_data"].get("selenium_mcg", 0),
                    chromium_mcg=food_data["nutritional_data"].get("chromium_mcg", 0),
                    molybdenum_mcg=food_data["nutritional_data"].get("molybdenum_mcg", 0),
                    cholesterol_mg=food_data["nutritional_data"].get("cholesterol_mg", 0),
                    saturated_fat_g=food_data["nutritional_data"].get("saturated_fat_g", 0),
                    trans_fat_g=food_data["nutritional_data"].get("trans_fat_g", 0),
                    polyunsaturated_fat_g=food_data["nutritional_data"].get("polyunsaturated_fat_g", 0),
                    monounsaturated_fat_g=food_data["nutritional_data"].get("monounsaturated_fat_g", 0),
                    confidence_score=food_data.get("confidence_score", 0.9),
                    source="ai_parsed",
                    logged_at=session.extracted_datetime or datetime.utcnow()
                )
                
                db.add(food_log)
                food_logs.append(food_log)
            
            db.commit()
            return food_logs
            
        except Exception as e:
            logger.error(f"Error creating food logs from session: {str(e)}")
            db.rollback()
            return [] 