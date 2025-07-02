import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from google import genai
from google.genai import types
from pydantic import BaseModel
import re
from . import schemas

logger = logging.getLogger(__name__)

# Fallback chain for the food-logging agent (free-tier only, July 2025)
MODEL_PRIORITY = {
    0: {
        "name": "gemini-1.5-flash",
        "why": "Fast, versatile; primary choice.",
        "rpm": 15,
        "rpd": 1_500,
        "max_context_tokens": 1_000_000
    },
    1: {
        "name": "gemini-1.5-flash-8b",
        "why": "Lower quality but same free quotas.",
        "rpm": 15,
        "rpd": 1_500,
        "max_context_tokens": 1_000_000
    },
    2: {
        "name": "gemini-1.5-pro",
        "why": "Better reasoning; strict quotas.",
        "rpm": 2,
        "rpd": 50,
        "max_context_tokens": 2_000_000
    },
    3: {
        "name": "gemini-2.5-flash",
        "why": "‘Thinking traces’; upgrade path.",
        "rpm": 15,
        "rpd": 1_500,
        "max_context_tokens": 1_048_576
    },
    4: {
        "name": "gemini-2.5-pro",
        "why": "Top quality (CLI/Code-Assist key required for free tier).",
        "rpm": 60,  # via Code-Assist/CLI licence
        "rpd": 1_000,
        "max_context_tokens": 1_048_576
    }
}

class NutritionData(BaseModel):
    """Structured nutrition data model"""
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    fat_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fiber_g: Optional[float] = None
    sugar_g: Optional[float] = None
    
    # Vitamins
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
    
    # Minerals
    calcium_mg: Optional[float] = None
    iron_mg: Optional[float] = None
    magnesium_mg: Optional[float] = None
    phosphorus_mg: Optional[float] = None
    potassium_mg: Optional[float] = None
    sodium_mg: Optional[float] = None
    zinc_mg: Optional[float] = None
    copper_mg: Optional[float] = None
    manganese_mg: Optional[float] = None
    selenium_mcg: Optional[float] = None
    chromium_mcg: Optional[float] = None
    molybdenum_mcg: Optional[float] = None
    
    # Other nutrients
    cholesterol_mg: Optional[float] = None
    saturated_fat_g: Optional[float] = None
    trans_fat_g: Optional[float] = None
    polyunsaturated_fat_g: Optional[float] = None
    monounsaturated_fat_g: Optional[float] = None

class FoodItem(BaseModel):
    """Structured food item model"""
    description: str
    serving_size: Optional[str] = None
    meal_type: Optional[str] = None
    nutrition: NutritionData
    confidence_score: float = 0.8

class ParsingResult(BaseModel):
    """Structured parsing result model"""
    food_items: List[FoodItem]
    extracted_datetime: Optional[str] = None
    confidence_score: float = 0.7
    meal_type: Optional[str] = None
    meal_analysis: Optional[str] = None

class MCPServerClient:
    """Production-ready MCP server client using Google GenAI with intelligent model fallback"""
    
    def __init__(self, api_key: str, timeout: int = 30):
        self.api_key = api_key
        self.timeout = timeout
        self.client = genai.Client(api_key=api_key)
        
        # Use the MODEL_PRIORITY fallback chain
        self.model_priority = MODEL_PRIORITY
        self.current_model_index = 0  # Start with the first model in the chain
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def _call_model_with_fallback(self, prompt: str, model: str = None, response_schema=None, tools=None, **kwargs) -> Dict[str, Any]:
        """Call model with intelligent fallback using the MODEL_PRIORITY chain."""
        last_error = None
        
        # Try models in priority order
        for priority, model_config in sorted(self.model_priority.items()):
            try_model = model_config["name"]
            try:
                logger.info(f"Attempting to call model: {try_model} (priority {priority})")
                
                # Prepare config with response_schema if provided
                config = {"temperature": 0.1}
                if response_schema and not tools:
                    # Only use structured output when not using tools
                    config["response_mime_type"] = "application/json"
                    config["response_schema"] = response_schema
                if tools:
                    # Convert tools to proper format for Google GenAI
                    formatted_tools = []
                    for tool in tools:
                        if "google_search" in tool:
                            formatted_tools.append(types.Tool(google_search=types.GoogleSearch()))
                    config["tools"] = formatted_tools
                config.update(kwargs)
                
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.models.generate_content,
                        model=try_model,
                        contents=prompt,
                        config=config
                    ),
                    timeout=self.timeout
                )
                if response.text:
                    logger.info(f"Successfully used model: {try_model}")
                    return {
                        "success": True, 
                        "text": response.text, 
                        "model": try_model, 
                        "model_priority": priority,
                        "model_info": model_config,
                        "parsed": getattr(response, "parsed", None)
                    }
                else:
                    raise Exception("Empty response from model")
            except Exception as e:
                last_error = e
                logger.warning(f"Model {try_model} (priority {priority}) failed: {str(e)}")
                continue
        
        # All models failed
        error_msg = f"All models in fallback chain failed. Last error: {str(last_error)}"
        logger.error(error_msg)
        raise Exception(error_msg)
    
    async def parse_food_input(self, user_input: str) -> Dict[str, Any]:
        """Parse natural language food input into structured data"""
        try:
            prompt = f"""
Parse the following food input into structured data. Extract all dishes, serving sizes, meal types, and timing information. For each dish, provide a detailed breakdown of macronutrients (calories, protein, fat, carbs, fiber, sugar), micronutrients (all vitamins and minerals), and a brief meal analysis. Use realistic values from common food databases. If exact values are not available, use reasonable estimates. Extract datetime if present (e.g., 'at 1 pm today').

User input: "{user_input}"

Return a JSON object with:
- food_items: list of dishes with description, serving_size, meal_type, nutrition (all macros/micros)
- extracted_datetime: ISO string or null
- confidence_score: 0-1
- meal_type: overall meal type
- meal_analysis: brief analysis of the meal
"""
            response = await self._call_model_with_fallback(
                prompt,
                response_schema=ParsingResult,
            )
            if not response["success"]:
                return {"error": "Failed to parse food input"}
            try:
                if response["parsed"] is not None:
                    result = response["parsed"]
                else:
                    parsed_data = json.loads(response["text"])
                    result = ParsingResult(**parsed_data)
                return {
                    "food_items": [item.dict() for item in result.food_items],
                    "extracted_datetime": result.extracted_datetime,
                    "confidence_score": result.confidence_score,
                    "meal_type": result.meal_type,
                    "meal_analysis": result.meal_analysis
                }
            except Exception as parse_error:
                logger.error(f"Failed to parse model response: {parse_error}")
                return await self._fallback_parse(user_input)
        except Exception as e:
            logger.error(f"Error parsing food input: {str(e)}")
            return {"error": str(e)}
    
    async def _fallback_parse(self, user_input: str) -> Dict[str, Any]:
        """Fallback parsing using regex patterns when AI parsing fails"""
        try:
            # Extract basic food information using regex
            food_items = []
            
            # Common food patterns
            food_patterns = [
                r'(\d+)\s*(g|grams?|gm|gms?)\s+of\s+([^,\n]+)',
                r'(\d+)\s*(ml|milliliters?|cc)\s+of\s+([^,\n]+)',
                r'(\d+)\s*(oz|ounces?)\s+of\s+([^,\n]+)',
                r'a\s+(small|medium|large)\s+([^,\n]+)',
                r'(\d+)\s+([^,\n]+)'
            ]
            
            for pattern in food_patterns:
                matches = re.finditer(pattern, user_input, re.IGNORECASE)
                for match in matches:
                    if len(match.groups()) >= 2:
                        serving_size = f"{match.group(1)} {match.group(2)}" if len(match.groups()) >= 3 else match.group(1)
                        description = match.group(3) if len(match.groups()) >= 3 else match.group(2)
                        
                        # Basic nutrition estimates
                        nutrition = NutritionData(
                            calories=100,  # Default estimate
                            protein_g=5,
                            fat_g=2,
                            carbs_g=15
                        )
                        
                        food_items.append({
                            "description": description.strip(),
                            "serving_size": serving_size,
                            "meal_type": self._extract_meal_type(user_input),
                            "nutrition": nutrition.dict()
                        })
            
            # Extract datetime
            datetime_str = self._extract_datetime(user_input)
            
            return {
                "food_items": food_items,
                "extracted_datetime": datetime_str,
                "confidence_score": 0.3,  # Low confidence for fallback
                "meal_type": self._extract_meal_type(user_input),
                "meal_analysis": "Basic parsing completed with limited accuracy"
            }
            
        except Exception as e:
            logger.error(f"Fallback parsing failed: {str(e)}")
            return {"error": f"All parsing methods failed: {str(e)}"}
    
    def _extract_datetime(self, text: str) -> Optional[str]:
        """Extract datetime from text using regex patterns"""
        now = datetime.utcnow()
        
        # Time patterns
        time_patterns = [
            r'at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?',
            r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)',
            r'(today|yesterday|tomorrow)',
            r'(morning|afternoon|evening|night)'
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if "today" in match.group(0).lower():
                    return now.isoformat()
                elif "yesterday" in match.group(0).lower():
                    yesterday = now - timedelta(days=1)
                    return yesterday.isoformat()
                elif "tomorrow" in match.group(0).lower():
                    tomorrow = now + timedelta(days=1)
                    return tomorrow.isoformat()
        
        return None
    
    def _extract_meal_type(self, text: str) -> Optional[str]:
        """Extract meal type from text"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['breakfast', 'morning']):
            return 'breakfast'
        elif any(word in text_lower for word in ['lunch', 'noon', 'midday']):
            return 'lunch'
        elif any(word in text_lower for word in ['dinner', 'evening', 'night']):
            return 'dinner'
        elif any(word in text_lower for word in ['snack', 'snacks']):
            return 'snack'
        
        return None
    
    async def search_nutrition(self, food_item: str, serving_size: Optional[str] = None) -> Dict[str, Any]:
        """Search for nutritional information using Google search grounding"""
        try:
            search_query = f"""
Search for nutritional information for {food_item}.
{f"Serving size: {serving_size}" if serving_size else ""}

Please provide the following nutritional data in JSON format:
- calories (number)
- protein_g (number)
- fat_g (number)
- carbs_g (number)
- fiber_g (number)
- sugar_g (number)

Return only the JSON data, no additional text.
"""
            grounding_tool = types.Tool(google_search=types.GoogleSearch())
            response = await self._call_model_with_fallback(
                search_query,
                tools=[grounding_tool],
                # Don't use structured output with tools - parse JSON manually
            )
            if response["success"]:
                try:
                    # Try to extract JSON from the response
                    text = response["text"]
                    # Look for JSON in the response
                    import re
                    json_match = re.search(r'\{.*\}', text, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                        nutrition_data = json.loads(json_str)
                        return nutrition_data
                    else:
                        # Fallback: create basic nutrition data
                        return {
                            "calories": 100,
                            "protein_g": 5.0,
                            "fat_g": 2.0,
                            "carbs_g": 15.0,
                            "fiber_g": 2.0,
                            "sugar_g": 10.0
                        }
                except Exception as parse_error:
                    logger.error(f"Failed to parse nutrition data: {parse_error}")
                    # Return basic nutrition data as fallback
                    return {
                        "calories": 100,
                        "protein_g": 5.0,
                        "fat_g": 2.0,
                        "carbs_g": 15.0,
                        "fiber_g": 2.0,
                        "sugar_g": 10.0
                    }
            else:
                return {"error": "Failed to extract nutrition data"}
        except Exception as e:
            logger.error(f"Error searching nutrition for {food_item}: {str(e)}")
            return {"error": str(e)}

def get_mcp_client(config: schemas.MCPServerConfig) -> MCPServerClient:
    """Factory function to create MCP client"""
    if not config.api_key:
        raise ValueError("Google GenAI API key is required")
    
    return MCPServerClient(api_key=config.api_key, timeout=config.timeout) 