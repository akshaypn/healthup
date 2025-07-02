import asyncio
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from . import models, schemas, mcp_server
import re
from pydantic import BaseModel

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
    """Service for parsing natural language food input using AI and MCP servers"""
    
    def __init__(self, mcp_config: schemas.MCPServerConfig):
        self.mcp_config = mcp_config
    
    async def parse_food_input(self, user_input: str, user_id: str, db: Session) -> schemas.FoodParsingResponse:
        """Parse natural language food input using the new agent-based approach"""
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
            # Step 1: Extract dishes using structured data
            dishes = await self._extract_dishes(user_input)
            if not dishes:
                raise Exception("No dishes found in input")
            
            # Step 2: Batch search for nutrition data
            nutrition_data = await self._batch_search_nutrition(dishes)
            
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
                    confidence_score=0.9,  # High confidence with structured approach
                    nutritional_data=dish_data.dict(exclude={'dish'})
                )
                parsed_foods.append(parsed_food)
            
            # Step 5: Generate meal analysis
            meal_analysis = await self._generate_meal_analysis(nutrition_data)
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
    
    async def _extract_dishes(self, user_input: str) -> List[str]:
        """Step 1: Extract dish names using structured data"""
        async with mcp_server.get_mcp_client(self.mcp_config) as mcp_client:
            prompt = f"""
Extract only the food dish names mentioned below. Respond as a JSON object with a "dishes" array containing only the dish names.

User text: {user_input}

Examples:
- "I had 80 gms of protein oats with 250 ml milk and a small banana" → {{"dishes": ["protein oats", "milk", "banana"]}}
- "ate chicken breast and rice" → {{"dishes": ["chicken breast", "rice"]}}

Return only the JSON object with the dishes array.
"""
            
            response = await mcp_client._call_model_with_fallback(
                prompt,
                response_schema=DishList
            )
            
            if response["success"] and response["parsed"]:
                return response["parsed"].dishes
            elif response["success"]:
                # Fallback: try to parse the text response
                try:
                    import json
                    data = json.loads(response["text"])
                    return data.get("dishes", [])
                except:
                    pass
            
            # Final fallback: use regex extraction
            return self._extract_dishes_regex(user_input)
    
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
                if len(match) == 2:  # a small/medium/large pattern
                    dishes.append(match[1].strip())
                elif len(match) == 3:  # quantity unit pattern
                    dishes.append(match[2].strip())
        
        # Remove duplicates and clean up
        dishes = list(set([dish.strip() for dish in dishes if dish.strip()]))
        return dishes
    
    async def _batch_search_nutrition(self, dishes: List[str]) -> List[Nutrients]:
        """Step 2: Batch search for nutrition data using Google search"""
        if not dishes:
            return []
        
        # Limit to 30 dishes per batch as per README
        if len(dishes) > 30:
            dishes = dishes[:30]
        
        async with mcp_server.get_mcp_client(self.mcp_config) as mcp_client:
            # Create batched query
            dishes_str = " OR ".join([f'"{dish}"' for dish in dishes])
            search_query = f"nutrition facts ({dishes_str}) serving size 100g calories protein fat carbs fiber sugar sodium vitamins minerals"
            
            # Use Google search tool
            tools = [{
                "google_search": {
                    "query": search_query
                }
            }]
            
            prompt = f"""
You are given Google search snippets about food nutrition. For each dish in the list below, extract the nutritional information and return a structured JSON response.

Dishes to analyze: {dishes}

Search results will be provided via Google search. For each dish, extract:
- calories_kcal (convert to kcal if needed)
- protein_g (grams)
- fat_g (grams) 
- carbs_g (grams)
- fiber_g (grams, optional)
- sugar_g (grams, optional)
- sodium_mg (milligrams, optional)
- All vitamins and minerals if available

Use realistic values from the search results. If exact values are not found, use reasonable estimates based on similar foods.

Return a JSON object with an "items" array containing one Nutrients object per dish.
"""
            
            response = await mcp_client._call_model_with_fallback(
                prompt,
                tools=tools
                # Note: Cannot use response_schema with tools, so we'll parse manually
            )
            
            if response["success"]:
                # Parse the text response manually since tools don't support structured output
                try:
                    import json
                    import re
                    
                    # Look for JSON in the response text
                    text = response["text"]
                    json_match = re.search(r'\{.*\}', text, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                        data = json.loads(json_str)
                        if "items" in data:
                            return [Nutrients(**item) for item in data["items"]]
                        else:
                            # Try to parse as direct array
                            return [Nutrients(**item) for item in data]
                    else:
                        # Try to parse the entire response as JSON
                        data = json.loads(text)
                        if "items" in data:
                            return [Nutrients(**item) for item in data["items"]]
                        else:
                            return [Nutrients(**item) for item in data]
                except Exception as parse_error:
                    logger.warning(f"Failed to parse nutrition response: {parse_error}")
                    logger.debug(f"Response text: {response['text']}")
                    pass
            
            # Final fallback: return basic nutrition data
            return self._generate_fallback_nutrition(dishes)
    
    def _generate_fallback_nutrition(self, dishes: List[str]) -> List[Nutrients]:
        """Generate fallback nutrition data when search fails"""
        fallback_data = []
        
        # Basic nutrition estimates for common foods
        nutrition_estimates = {
            "oats": {"calories": 389, "protein": 16.9, "fat": 6.9, "carbs": 66.3, "fiber": 10.6},
            "milk": {"calories": 42, "protein": 3.4, "fat": 1.0, "carbs": 5.0, "fiber": 0.0},
            "banana": {"calories": 89, "protein": 1.1, "fat": 0.3, "carbs": 22.8, "fiber": 2.6},
            "chicken": {"calories": 165, "protein": 31.0, "fat": 3.6, "carbs": 0.0, "fiber": 0.0},
            "rice": {"calories": 130, "protein": 2.7, "fat": 0.3, "carbs": 28.0, "fiber": 0.4},
        }
        
        for dish in dishes:
            dish_lower = dish.lower()
            nutrition = nutrition_estimates.get(dish_lower, {
                "calories": 100, "protein": 5.0, "fat": 2.0, "carbs": 15.0, "fiber": 2.0
            })
            
            fallback_data.append(Nutrients(
                dish=dish,
                calories_kcal=nutrition["calories"],
                protein_g=nutrition["protein"],
                fat_g=nutrition["fat"],
                carbs_g=nutrition["carbs"],
                fiber_g=nutrition.get("fiber", 2.0)
            ))
        
        return fallback_data
    
    async def _generate_meal_analysis(self, nutrition_data: List[Nutrients]) -> Optional[MealAnalysis]:
        """Step 3: Generate meal analysis"""
        if not nutrition_data:
            return None
        
        async with mcp_server.get_mcp_client(self.mcp_config) as mcp_client:
            # Calculate totals
            total_calories = sum(item.calories_kcal for item in nutrition_data)
            total_protein = sum(item.protein_g for item in nutrition_data)
            total_fat = sum(item.fat_g for item in nutrition_data)
            total_carbs = sum(item.carbs_g for item in nutrition_data)
            total_fiber = sum(item.fiber_g or 0 for item in nutrition_data)
            
            prompt = f"""
Analyze this meal based on the nutritional data:

Total calories: {total_calories} kcal
Total protein: {total_protein}g
Total fat: {total_fat}g
Total carbs: {total_carbs}g
Total fiber: {total_fiber}g

Dishes: {[item.dish for item in nutrition_data]}

Provide a structured analysis with:
- overall_health_score (0-10 scale)
- protein_adequacy (assessment of protein content)
- fiber_content (assessment of fiber content)
- vitamin_balance (assessment of vitamin variety)
- mineral_balance (assessment of mineral content)
- recommendations (list of suggestions for improvement)

Return as a JSON object matching the MealAnalysis schema.
"""
            
            response = await mcp_client._call_model_with_fallback(
                prompt,
                response_schema=MealAnalysis
            )
            
            if response["success"]:
                try:
                    import json
                    import re
                    # Look for JSON in the response text
                    text = response["text"]
                    json_match = re.search(r'\{.*\}', text, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                        data = json.loads(json_str)
                        return data
                    else:
                        # Try to parse the entire response as JSON
                        data = json.loads(text)
                        return data
                except Exception as parse_error:
                    logger.warning(f"Failed to parse meal analysis response: {parse_error}")
                    logger.debug(f"Response text: {response['text']}")
                    # Fallback: wrap as dict
                    return {"summary": response["text"]}
            # Fallback analysis
            return self._generate_fallback_analysis(nutrition_data).dict()
    
    def _generate_fallback_analysis(self, nutrition_data: List[Nutrients]) -> MealAnalysis:
        """Generate fallback meal analysis"""
        total_calories = sum(item.calories_kcal for item in nutrition_data)
        total_protein = sum(item.protein_g for item in nutrition_data)
        total_fat = sum(item.fat_g for item in nutrition_data)
        total_carbs = sum(item.carbs_g for item in nutrition_data)
        total_fiber = sum(item.fiber_g or 0 for item in nutrition_data)
        
        # Simple scoring
        health_score = 7.0  # Default score
        if total_protein >= 20:
            health_score += 1
        if total_fiber >= 5:
            health_score += 1
        if total_fat <= 30:
            health_score += 1
        
        return MealAnalysis(
            overall_health_score=min(health_score, 10.0),
            protein_adequacy="Good" if total_protein >= 20 else "Could be improved",
            fiber_content="Good" if total_fiber >= 5 else "Low",
            vitamin_balance="Varied selection",
            mineral_balance="Basic coverage",
            recommendations=["Consider adding more vegetables", "Include a variety of protein sources"]
        )
    
    def _extract_datetime_from_text(self, text: str) -> Optional[datetime]:
        """Extract datetime information from text using regex patterns"""
        now = datetime.utcnow()
        
        # Patterns for time extraction
        time_patterns = [
            r'at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm|AM|PM)?',
            r'(\d{1,2}):(\d{2})\s*(am|pm|AM|PM)?',
            r'(today|yesterday|tomorrow)',
            r'(\d{1,2})\s*(am|pm|AM|PM)'
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if 'today' in match.group().lower():
                    return now.replace(hour=12, minute=0, second=0, microsecond=0)
                elif 'yesterday' in match.group().lower():
                    return (now - timedelta(days=1)).replace(hour=12, minute=0, second=0, microsecond=0)
                elif 'tomorrow' in match.group().lower():
                    return (now + timedelta(days=1)).replace(hour=12, minute=0, second=0, microsecond=0)
                else:
                    # Extract hour and minute
                    hour = int(match.group(1))
                    minute = int(match.group(2)) if match.group(2) else 0
                    
                    # Handle AM/PM
                    if match.group(3):
                        if match.group(3).lower() == 'pm' and hour != 12:
                            hour += 12
                        elif match.group(3).lower() == 'am' and hour == 12:
                            hour = 0
                    
                    return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        return None
    
    def _extract_meal_type(self, text: str) -> Optional[str]:
        """Extract meal type from text"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['breakfast', 'morning', 'am']):
            return "Breakfast"
        elif any(word in text_lower for word in ['lunch', 'noon', 'midday']):
            return "Lunch"
        elif any(word in text_lower for word in ['dinner', 'evening', 'night', 'pm']):
            return "Dinner"
        elif any(word in text_lower for word in ['snack', 'between']):
            return "Snack"
        
        return None

    async def create_food_logs_from_session(self, session_id: str, user_id: str, db: Session) -> List[models.FoodLog]:
        """Create food logs from a completed parsing session"""
        session = db.query(models.FoodParsingSession).filter(
            models.FoodParsingSession.session_id == session_id,
            models.FoodParsingSession.user_id == user_id
        ).first()
        
        if not session:
            raise ValueError("Parsing session not found")
        
        if session.status != "completed":
            raise ValueError(f"Session is not completed (status: {session.status})")
        
        food_logs = []
        for food_item in session.parsed_foods:
            nutritional_data = food_item.get("nutritional_data", {})
            
            # Create food log with comprehensive nutritional data
            food_log = models.FoodLog(
                user_id=user_id,
                description=food_item["description"],
                serving_size=food_item.get("serving_size"),
                meal_type=food_item.get("meal_type"),
                confidence_score=food_item.get("confidence_score", 0.5),
                source="ai_parsed",
                search_queries={"session_id": session_id},
                logged_at=session.extracted_datetime or datetime.utcnow(),
                
                # Macronutrients
                calories=nutritional_data.get("calories_kcal"),
                protein_g=nutritional_data.get("protein_g"),
                fat_g=nutritional_data.get("fat_g"),
                carbs_g=nutritional_data.get("carbs_g"),
                fiber_g=nutritional_data.get("fiber_g"),
                sugar_g=nutritional_data.get("sugar_g"),
                
                # Vitamins
                vitamin_a_mcg=nutritional_data.get("vitamin_a_mcg"),
                vitamin_c_mg=nutritional_data.get("vitamin_c_mg"),
                vitamin_d_mcg=nutritional_data.get("vitamin_d_mcg"),
                vitamin_e_mg=nutritional_data.get("vitamin_e_mg"),
                vitamin_k_mcg=nutritional_data.get("vitamin_k_mcg"),
                vitamin_b1_mg=nutritional_data.get("vitamin_b1_mg"),
                vitamin_b2_mg=nutritional_data.get("vitamin_b2_mg"),
                vitamin_b3_mg=nutritional_data.get("vitamin_b3_mg"),
                vitamin_b5_mg=nutritional_data.get("vitamin_b5_mg"),
                vitamin_b6_mg=nutritional_data.get("vitamin_b6_mg"),
                vitamin_b7_mcg=nutritional_data.get("vitamin_b7_mcg"),
                vitamin_b9_mcg=nutritional_data.get("vitamin_b9_mcg"),
                vitamin_b12_mcg=nutritional_data.get("vitamin_b12_mcg"),
                
                # Minerals
                calcium_mg=nutritional_data.get("calcium_mg"),
                iron_mg=nutritional_data.get("iron_mg"),
                magnesium_mg=nutritional_data.get("magnesium_mg"),
                phosphorus_mg=nutritional_data.get("phosphorus_mg"),
                potassium_mg=nutritional_data.get("potassium_mg"),
                sodium_mg=nutritional_data.get("sodium_mg"),
                zinc_mg=nutritional_data.get("zinc_mg"),
                copper_mg=nutritional_data.get("copper_mg"),
                manganese_mg=nutritional_data.get("manganese_mg"),
                selenium_mcg=nutritional_data.get("selenium_mcg"),
                chromium_mcg=nutritional_data.get("chromium_mcg"),
                molybdenum_mcg=nutritional_data.get("molybdenum_mcg"),
                
                # Other nutrients
                cholesterol_mg=nutritional_data.get("cholesterol_mg"),
                saturated_fat_g=nutritional_data.get("saturated_fat_g"),
                trans_fat_g=nutritional_data.get("trans_fat_g"),
                polyunsaturated_fat_g=nutritional_data.get("polyunsaturated_fat_g"),
                monounsaturated_fat_g=nutritional_data.get("monounsaturated_fat_g")
            )
            
            db.add(food_log)
            food_logs.append(food_log)
        
        db.commit()
        
        # Refresh all food logs to get their IDs
        for food_log in food_logs:
            db.refresh(food_log)
        
        return food_logs

class FallbackFoodParser:
    """Fallback parser for when AI parsing fails"""
    
    @staticmethod
    def parse_simple_food_input(text: str) -> Dict[str, Any]:
        """Simple regex-based food parsing as fallback"""
        # Basic implementation for fallback
        return {
            "food_items": [],
            "extracted_datetime": None,
            "confidence_score": 0.1,
            "meal_type": None,
            "meal_analysis": None
        } 