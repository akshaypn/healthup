import asyncio
import uuid
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from . import models, schemas
import re
from pydantic import BaseModel
from agents import Agent, Runner, trace
from agents.mcp import MCPServer, MCPServerStdio

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
    """Service for parsing natural language food input using OpenAI agents and MCP servers"""
    
    def __init__(self, mcp_config: schemas.MCPServerConfig):
        self.mcp_config = mcp_config
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
    
    async def parse_food_input(self, user_input: str, user_id: str, db: Session) -> schemas.FoodParsingResponse:
        """Parse natural language food input using OpenAI agents"""
        session_id = str(uuid.uuid4())
        
        # Create parsing session
        session = models.FoodParsingSession(
            user_id=user_id,
            session_id=session_id,
            user_input=user_input,
            status="pending"
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        
        try:
            # Step 1: Extract dishes using OpenAI agent
            dishes = await self._extract_dishes_with_agent(user_input)
            if not dishes:
                raise Exception("No dishes found in input")
            
            # Step 2: Batch search for nutrition data using agent
            nutrition_data = await self._batch_search_nutrition_with_agent(dishes)
            
            # Step 3: Extract datetime and meal type
            extracted_datetime = self._extract_datetime_from_text(user_input)
            meal_type = self._extract_meal_type(user_input)
            
            # Step 4: Create structured food items
            parsed_foods = []
            for dish_data in nutrition_data:
                parsed_food = schemas.ParsedFoodItem(
                    description=dish_data.dish,
                    serving_size=None,  # Will be extracted separately if needed
                    meal_type=meal_type,
                    confidence_score=0.9,  # High confidence with agent approach
                    nutritional_data=dish_data.dict(exclude={'dish'})
                )
                parsed_foods.append(parsed_food)
            
            # Step 5: Generate meal analysis using agent
            meal_analysis = await self._generate_meal_analysis_with_agent(nutrition_data)
            # Ensure meal_analysis is always a dict
            if meal_analysis is not None:
                if isinstance(meal_analysis, str):
                    meal_analysis = {"summary": meal_analysis}
                elif hasattr(meal_analysis, 'dict'):
                    meal_analysis = meal_analysis.dict()
            
            # Update session with results
            session.parsed_foods = [food.dict() for food in parsed_foods]
            session.extracted_datetime = extracted_datetime
            session.confidence_score = 0.9
            session.status = "completed"
            session.completed_at = datetime.utcnow()
            db.commit()
            
            return schemas.FoodParsingResponse(
                session_id=session_id,
                status="completed",
                parsed_foods=parsed_foods,
                extracted_datetime=extracted_datetime,
                confidence_score=0.9,
                meal_analysis=meal_analysis
            )
                
        except Exception as e:
            logger.error(f"Error parsing food input: {str(e)}")
            session.status = "failed"
            session.error_message = str(e)
            session.completed_at = datetime.utcnow()
            db.commit()
            
            return schemas.FoodParsingResponse(
                session_id=session_id,
                status="failed",
                parsed_foods=[],
                confidence_score=0.0,
                error_message=str(e)
            )
    
    async def _extract_dishes_with_agent(self, user_input: str) -> List[str]:
        """Step 1: Extract dish names using OpenAI agent"""
        agent = Agent(
            name="Food Dish Extractor",
            instructions="""You are an expert at extracting food dish names from natural language text. 
            Your task is to identify and extract only the food items/dishes mentioned in the user's text.
            Return the dishes as a JSON array of strings.""",
        )
        
        prompt = f"""
Extract only the food dish names mentioned below. Respond as a JSON object with a "dishes" array containing only the dish names.

User text: {user_input}

Examples:
- "I had 80 gms of protein oats with 250 ml milk and a small banana" → {{"dishes": ["protein oats", "milk", "banana"]}}
- "ate chicken breast and rice" → {{"dishes": ["chicken breast", "rice"]}}

Return only the JSON object with the dishes array.
"""
        
        with trace("Extract dishes"):
            result = await Runner.run(agent, prompt)
            
        try:
            import json
            # Try to parse the response as JSON
            response_text = result.final_output.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]  # Remove markdown code blocks
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]  # Remove markdown code blocks
            
            data = json.loads(response_text)
            return data.get("dishes", [])
        except Exception as e:
            logger.warning(f"Failed to parse agent response as JSON: {e}")
            # Fallback: use regex extraction
            return self._extract_dishes_regex(user_input)
    
    async def _batch_search_nutrition_with_agent(self, dishes: List[str]) -> List[Nutrients]:
        """Step 2: Batch search for nutrition data using OpenAI agent"""
        agent = Agent(
            name="Nutrition Data Provider",
            instructions="""You are an expert nutritionist with access to comprehensive food nutrition databases. 
            For each food item provided, return accurate nutritional information including calories, protein, fat, carbs, 
            and other essential nutrients. Use realistic values based on standard serving sizes.""",
        )
        
        dishes_text = ", ".join(dishes)
        prompt = f"""
For each of the following food items, provide nutritional information in JSON format:
{dishes_text}

Return a JSON array where each item has this structure:
{{
  "dish": "food name",
  "calories_kcal": float,
  "protein_g": float,
  "fat_g": float,
  "carbs_g": float,
  "fiber_g": float,
  "sugar_g": float,
  "sodium_mg": float
}}

Provide realistic nutritional values for standard serving sizes. If exact values aren't available, provide reasonable estimates.
"""
        
        with trace("Batch nutrition search"):
            result = await Runner.run(agent, prompt)
            
        try:
            import json
            response_text = result.final_output.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]
            
            data = json.loads(response_text)
            nutrition_items = []
            
            for item in data:
                nutrition_item = Nutrients(
                    dish=item.get("dish", ""),
                    calories_kcal=item.get("calories_kcal", 0.0),
                    protein_g=item.get("protein_g", 0.0),
                    fat_g=item.get("fat_g", 0.0),
                    carbs_g=item.get("carbs_g", 0.0),
                    fiber_g=item.get("fiber_g"),
                    sugar_g=item.get("sugar_g"),
                    sodium_mg=item.get("sodium_mg")
                )
                nutrition_items.append(nutrition_item)
            
            return nutrition_items
        except Exception as e:
            logger.warning(f"Failed to parse nutrition data: {e}")
            return self._generate_fallback_nutrition(dishes)
    
    async def _generate_meal_analysis_with_agent(self, nutrition_data: List[Nutrients]) -> Optional[MealAnalysis]:
        """Step 3: Generate meal analysis using OpenAI agent"""
        agent = Agent(
            name="Meal Analysis Expert",
            instructions="""You are a nutrition expert who analyzes meals and provides health insights. 
            Evaluate the nutritional content of meals and provide actionable recommendations for improvement.""",
        )
        
        # Calculate totals
        total_calories = sum(item.calories_kcal for item in nutrition_data)
        total_protein = sum(item.protein_g for item in nutrition_data)
        total_fat = sum(item.fat_g for item in nutrition_data)
        total_carbs = sum(item.carbs_g for item in nutrition_data)
        total_fiber = sum(item.fiber_g or 0 for item in nutrition_data)
        
        nutrition_summary = f"""
Meal Summary:
- Total Calories: {total_calories:.1f} kcal
- Total Protein: {total_protein:.1f}g
- Total Fat: {total_fat:.1f}g
- Total Carbs: {total_carbs:.1f}g
- Total Fiber: {total_fiber:.1f}g

Food Items: {[item.dish for item in nutrition_data]}
"""
        
        prompt = f"""
Analyze this meal and provide insights in JSON format:

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
        
        with trace("Meal analysis"):
            result = await Runner.run(agent, prompt)
            
        try:
            import json
            response_text = result.final_output.strip()
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
            return self._generate_fallback_analysis(nutrition_data)
    
    def _extract_dishes_regex(self, text: str) -> List[str]:
        """Fallback regex-based dish extraction"""
        dishes = []
        
        # Common patterns
        patterns = [
            r'(\d+)\s*(g|grams?|gm|gms?)\s+of\s+([^,\n]+)',
            r'(\d+)\s*(ml|milliliters?|cc)\s+of\s+([^,\n]+)',
            r'(\d+)\s*(oz|ounces?)\s+of\s+([^,\n]+)',
            r'a\s+(small|medium|large)\s+([^,\n]+)',
            r'(\d+)\s+([^,\n]+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match) == 2:
                    dishes.append(match[1].strip())
                elif len(match) == 3:
                    dishes.append(match[2].strip())
        
        # Also extract simple food words
        food_words = re.findall(r'\b(apple|banana|chicken|rice|bread|milk|eggs?|fish|beef|pork|vegetables?|fruits?|salad|soup|pasta|noodles?|pizza|burger|sandwich|taco|burrito|sushi|curry|stew|soup|yogurt|cheese|butter|oil|sugar|salt|pepper|herbs?|spices?)\b', text, re.IGNORECASE)
        dishes.extend(food_words)
        
        return list(set(dishes))  # Remove duplicates
    
    def _generate_fallback_nutrition(self, dishes: List[str]) -> List[Nutrients]:
        """Generate fallback nutrition data"""
        nutrition_items = []
        
        # Basic nutrition database
        nutrition_db = {
            "chicken breast": {"calories": 165, "protein": 31, "fat": 3.6, "carbs": 0},
            "rice": {"calories": 130, "protein": 2.7, "fat": 0.3, "carbs": 28},
            "milk": {"calories": 42, "protein": 3.4, "fat": 1.0, "carbs": 5.0},
            "banana": {"calories": 89, "protein": 1.1, "fat": 0.3, "carbs": 23},
            "apple": {"calories": 52, "protein": 0.3, "fat": 0.2, "carbs": 14},
            "eggs": {"calories": 155, "protein": 13, "fat": 11, "carbs": 1.1},
            "bread": {"calories": 79, "protein": 3.1, "fat": 1.0, "carbs": 15},
            "oats": {"calories": 68, "protein": 2.4, "fat": 1.4, "carbs": 12},
        }
        
        for dish in dishes:
            dish_lower = dish.lower()
            nutrition = nutrition_db.get(dish_lower, {"calories": 100, "protein": 5, "fat": 2, "carbs": 15})
            
            nutrition_item = Nutrients(
                dish=dish,
                calories_kcal=nutrition["calories"],
                protein_g=nutrition["protein"],
                fat_g=nutrition["fat"],
                carbs_g=nutrition["carbs"],
                fiber_g=2.0,
                sugar_g=5.0,
                sodium_mg=200.0
            )
            nutrition_items.append(nutrition_item)
        
        return nutrition_items
    
    def _generate_fallback_analysis(self, nutrition_data: List[Nutrients]) -> MealAnalysis:
        """Generate fallback meal analysis"""
        total_calories = sum(item.calories_kcal for item in nutrition_data)
        total_protein = sum(item.protein_g for item in nutrition_data)
        total_fat = sum(item.fat_g for item in nutrition_data)
        total_carbs = sum(item.carbs_g for item in nutrition_data)
        
        # Simple scoring
        protein_score = min(100, (total_protein / 50) * 100) if total_protein > 0 else 0
        calorie_score = min(100, (total_calories / 600) * 100) if total_calories > 0 else 0
        overall_score = (protein_score + calorie_score) / 2
        
        return MealAnalysis(
            overall_health_score=overall_score,
            protein_adequacy="Good" if total_protein >= 20 else "Could be improved",
            fiber_content="Moderate",
            vitamin_balance="Good",
            mineral_balance="Good",
            recommendations=["Consider adding more vegetables", "Stay hydrated"]
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

class FallbackFoodParser:
    """Simple fallback parser for basic food input"""
    
    @staticmethod
    def parse_simple_food_input(text: str) -> Dict[str, Any]:
        """Parse simple food input without AI"""
        return {
            "description": text,
            "calories": 100,
            "protein": 5,
            "fat": 2,
            "carbs": 15,
            "confidence_score": 0.3
        } 