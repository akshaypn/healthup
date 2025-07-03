import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from . import models, schemas
import re
from pydantic import BaseModel
from .mcp_server import get_mcp_client
import json

logger = logging.getLogger(__name__)

# New schemas for the agent-based approach
class DishList(BaseModel):
    dishes: List[str]

class Nutrients(BaseModel):
    dish: str
    calories_kcal: float
    protein_g: float
    fat_g: float
    carbs_g: float
    fiber_g: Optional[float] = None
    sugar_g: Optional[float] = None
    sodium_mg: Optional[float] = None
    # Add all other nutrients as optional
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

class NutritionReport(BaseModel):
    items: List[Nutrients]

class MealAnalysis(BaseModel):
    overall_health_score: float
    protein_adequacy: str
    fiber_content: str
    vitamin_balance: str
    mineral_balance: str
    recommendations: List[str]

class FoodParserService:
    """AI-powered food parsing service using OpenAI with web search grounding"""
    
    def __init__(self, mcp_config: schemas.MCPServerConfig):
        self.mcp_config = mcp_config
        self.mcp_client = get_mcp_client(mcp_config)

    async def parse_food_input(self, user_input: str, user_id: str, db: Session) -> schemas.FoodParsingResponse:
        """Parse natural language food input using AI with web search grounding"""
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
            dishes = await self._extract_dishes_with_agent(user_input)
            
            # Get nutrition data using AI with web search
            nutrition_data = await self._batch_search_nutrition_with_agent(dishes)
            
            # Generate meal analysis
            meal_analysis = await self._generate_meal_analysis_with_agent(nutrition_data)
            
            # Extract datetime and meal type
            extracted_datetime = self._extract_datetime_from_text(user_input)
            meal_type = self._extract_meal_type(user_input)
            
            # Prepare parsed foods
            parsed_foods = []
            for i, dish in enumerate(dishes):
                nutrition = nutrition_data[i] if i < len(nutrition_data) else None
                food_data = {
                    "description": dish,
                    "serving_size": "1 serving",
                    "meal_type": meal_type,
                    "confidence_score": 0.8,  # Add required field
                    "nutritional_data": {
                        "calories_kcal": nutrition.calories_kcal if nutrition else 0,
                        "protein_g": nutrition.protein_g if nutrition else 0,
                        "fat_g": nutrition.fat_g if nutrition else 0,
                        "carbs_g": nutrition.carbs_g if nutrition else 0,
                        "fiber_g": nutrition.fiber_g if nutrition else 0,
                        "sugar_g": nutrition.sugar_g if nutrition else 0,
                        "sodium_mg": nutrition.sodium_mg if nutrition else 0,
                    } if nutrition else {}
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
                meal_analysis=meal_analysis,
                extracted_datetime=extracted_datetime,
                confidence_score=0.8,  # Add required field
                meal_type=meal_type
            )
            
        except Exception as e:
            logger.error(f"Error parsing food input: {str(e)}")
            if session:
                session.status = "failed"
                session.error_message = str(e)
                db.commit()
            raise

    async def _extract_dishes_with_agent(self, user_input: str) -> List[str]:
        """Extract dishes from user input using AI"""
        prompt = f"""
        Extract food items from this text: "{user_input}"
        
        Return only the food items as a comma-separated list.
        Example: "banana, apple, oatmeal"
        """
        
        try:
            response = self.mcp_client.responses().create(
                model="gpt-4o",
                tools=[{"type": "web_search_preview"}],
                input=prompt
            )
            
            dishes_text = response.output_text.strip()
            dishes = [dish.strip() for dish in dishes_text.split(',') if dish.strip()]
            return dishes
            
        except Exception as e:
            logger.error(f"Error extracting dishes: {str(e)}")
            # Fallback: extract simple words that might be food
            words = user_input.lower().split()
            food_keywords = ['banana', 'apple', 'oatmeal', 'rice', 'chicken', 'bread', 'milk', 'egg', 'eggs']
            dishes = [word for word in words if word in food_keywords]
            return dishes if dishes else ['unknown food']

    async def _batch_search_nutrition_with_agent(self, dishes: List[str]) -> List[Nutrients]:
        """Search nutrition data for dishes using AI with web search grounding"""
        if not dishes:
            return []
        
        nutrition_items = []
        
        for dish in dishes:
            try:
                prompt = f"""
                Provide nutritional information for {dish} per serving.
                
                Return only the numbers in this format:
                calories: X
                protein: X
                fat: X
                carbs: X
                fiber: X
                sugar: X
                sodium: X
                """
                
                response = self.mcp_client.responses().create(
                    model="gpt-4o",
                    tools=[{"type": "web_search_preview"}],
                    input=prompt
                )
                
                response_text = response.output_text.strip()
                
                # Simple parsing of the response
                calories = self._extract_number(response_text, "calories", 100)
                protein = self._extract_number(response_text, "protein", 2)
                fat = self._extract_number(response_text, "fat", 1)
                carbs = self._extract_number(response_text, "carbs", 20)
                fiber = self._extract_number(response_text, "fiber", 2)
                sugar = self._extract_number(response_text, "sugar", 10)
                sodium = self._extract_number(response_text, "sodium", 5)
                
                nutrition = Nutrients(
                    dish=dish,
                    calories_kcal=calories,
                    protein_g=protein,
                    fat_g=fat,
                    carbs_g=carbs,
                    fiber_g=fiber,
                    sugar_g=sugar,
                    sodium_mg=sodium,
                )
                nutrition_items.append(nutrition)
                
            except Exception as e:
                logger.error(f"Error getting nutrition for {dish}: {str(e)}")
                # Fallback nutrition data
                nutrition = Nutrients(
                    dish=dish,
                    calories_kcal=100,
                    protein_g=2,
                    fat_g=1,
                    carbs_g=20,
                    fiber_g=2,
                    sugar_g=10,
                    sodium_mg=5,
                )
                nutrition_items.append(nutrition)
        
        return nutrition_items
    
    def _extract_number(self, text: str, field: str, default: float) -> float:
        """Extract a number from text for a specific field"""
        try:
            import re
            pattern = rf"{field}:\s*(\d+(?:\.\d+)?)"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1))
        except:
            pass
        return default

    async def _generate_meal_analysis_with_agent(self, nutrition_data: List[Nutrients]) -> Optional[MealAnalysis]:
        """Generate meal analysis using AI with web search grounding"""
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

        Return a JSON object with this structure:
        {{
          "overall_health_score": float (0-100),
          "protein_adequacy": "string description",
          "fiber_content": "string description", 
          "vitamin_balance": "string description",
          "mineral_balance": "string description",
          "recommendations": ["recommendation1", "recommendation2", ...]
        }}
        """
        
        try:
            response = self.mcp_client.responses().create(
                model="gpt-4o",
                tools=[{"type": "web_search_preview"}],
                input=prompt
            )
            
            response_text = response.output_text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]
            
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
            return None
    
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
        
        return None
    
    async def create_food_logs_from_session(self, session_id: str, user_id: str, db: Session) -> List[models.FoodLog]:
        """Create food logs from a completed parsing session"""
        session = db.query(models.FoodParsingSession).filter(
            models.FoodParsingSession.session_id == session_id,
            models.FoodParsingSession.user_id == user_id
        ).first()
        
        if not session or session.status != "completed":
            raise Exception("Session not found or not completed")
        
        food_logs = []
        for food_data in session.parsed_foods:
            food_log = models.FoodLog(
                user_id=user_id,
                description=food_data.get("description", ""),
                serving_size=food_data.get("serving_size"),
                meal_type=food_data.get("meal_type"),
                calories=food_data.get("nutritional_data", {}).get("calories_kcal", 0),
                protein=food_data.get("nutritional_data", {}).get("protein_g", 0),
                fat=food_data.get("nutritional_data", {}).get("fat_g", 0),
                carbs=food_data.get("nutritional_data", {}).get("carbs_g", 0),
                fiber=food_data.get("nutritional_data", {}).get("fiber_g", 0),
                sugar=food_data.get("nutritional_data", {}).get("sugar_g", 0),
                sodium=food_data.get("nutritional_data", {}).get("sodium_mg", 0),
                logged_at=session.extracted_datetime or datetime.utcnow()
            )
            db.add(food_log)
            food_logs.append(food_log)
        
        db.commit()
        return food_logs 