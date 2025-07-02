#!/usr/bin/env python3
"""
Simple MCP Server Example for HealthUp Food Parsing

This is a basic implementation of an MCP server that provides tools for:
- Google search (mock)
- Nutrition extraction
- Food input parsing

To run this server:
python mcp_server_example.py

The server will start on http://localhost:8001
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="HealthUp MCP Server", version="1.0.0")

class ToolCall(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]

class ToolResponse(BaseModel):
    success: bool
    data: Dict[str, Any] = {}
    error: str = None

# Mock nutrition database
NUTRITION_DB = {
    "oatmeal": {
        "calories": 150,
        "protein_g": 5.0,
        "fat_g": 3.0,
        "carbs_g": 27.0,
        "fiber_g": 4.0,
        "sugar_g": 1.0,
        "vitamin_c_mg": 0.0,
        "calcium_mg": 20.0,
        "iron_mg": 1.5,
        "confidence_score": 0.9
    },
    "banana": {
        "calories": 105,
        "protein_g": 1.3,
        "fat_g": 0.4,
        "carbs_g": 27.0,
        "fiber_g": 3.1,
        "sugar_g": 14.0,
        "vitamin_c_mg": 10.3,
        "calcium_mg": 6.0,
        "iron_mg": 0.3,
        "confidence_score": 0.95
    },
    "honey": {
        "calories": 64,
        "protein_g": 0.1,
        "fat_g": 0.0,
        "carbs_g": 17.0,
        "fiber_g": 0.0,
        "sugar_g": 17.0,
        "vitamin_c_mg": 0.1,
        "calcium_mg": 1.0,
        "iron_mg": 0.1,
        "confidence_score": 0.9
    },
    "chicken breast": {
        "calories": 165,
        "protein_g": 31.0,
        "fat_g": 3.6,
        "carbs_g": 0.0,
        "fiber_g": 0.0,
        "sugar_g": 0.0,
        "vitamin_c_mg": 0.0,
        "calcium_mg": 15.0,
        "iron_mg": 1.0,
        "confidence_score": 0.95
    },
    "rice": {
        "calories": 130,
        "protein_g": 2.7,
        "fat_g": 0.3,
        "carbs_g": 28.0,
        "fiber_g": 0.4,
        "sugar_g": 0.1,
        "vitamin_c_mg": 0.0,
        "calcium_mg": 10.0,
        "iron_mg": 0.2,
        "confidence_score": 0.9
    },
    "apple": {
        "calories": 95,
        "protein_g": 0.5,
        "fat_g": 0.3,
        "carbs_g": 25.0,
        "fiber_g": 4.4,
        "sugar_g": 19.0,
        "vitamin_c_mg": 8.4,
        "calcium_mg": 11.0,
        "iron_mg": 0.2,
        "confidence_score": 0.95
    }
}

def extract_food_items(text: str) -> List[Dict[str, Any]]:
    """Extract food items from natural language text"""
    text_lower = text.lower()
    food_items = []
    
    # Simple keyword matching (in a real implementation, this would use NLP)
    for food_name, nutrition in NUTRITION_DB.items():
        if food_name in text_lower:
            # Extract serving size if mentioned
            serving_size = None
            if "cup" in text_lower and food_name in text_lower:
                serving_size = "1 cup"
            elif "tbsp" in text_lower or "tablespoon" in text_lower:
                serving_size = "1 tbsp"
            elif "banana" in text_lower:
                serving_size = "1 medium"
            elif "apple" in text_lower:
                serving_size = "1 medium"
            
            food_items.append({
                "description": food_name.title(),
                "serving_size": serving_size,
                "nutritional_data": nutrition.copy()
            })
    
    return food_items

def extract_datetime(text: str) -> str:
    """Extract datetime information from text"""
    text_lower = text.lower()
    now = datetime.now()
    
    # Simple time extraction
    if "breakfast" in text_lower or "morning" in text_lower:
        return now.replace(hour=8, minute=0, second=0, microsecond=0).isoformat()
    elif "lunch" in text_lower or "noon" in text_lower:
        return now.replace(hour=12, minute=0, second=0, microsecond=0).isoformat()
    elif "dinner" in text_lower or "evening" in text_lower:
        return now.replace(hour=18, minute=0, second=0, microsecond=0).isoformat()
    elif "snack" in text_lower:
        return now.replace(hour=15, minute=0, second=0, microsecond=0).isoformat()
    
    return now.isoformat()

def extract_meal_type(text: str) -> str:
    """Extract meal type from text"""
    text_lower = text.lower()
    
    if "breakfast" in text_lower or "morning" in text_lower:
        return "breakfast"
    elif "lunch" in text_lower or "noon" in text_lower:
        return "lunch"
    elif "dinner" in text_lower or "evening" in text_lower:
        return "dinner"
    elif "snack" in text_lower:
        return "snack"
    
    return "meal"

@app.post("/tools/google_search")
async def google_search(tool_call: ToolCall) -> ToolResponse:
    """Mock Google search tool"""
    try:
        query = tool_call.parameters.get("query", "")
        num_results = tool_call.parameters.get("num_results", 5)
        
        logger.info(f"Mock Google search for: {query}")
        
        # Return mock search results
        results = [
            {
                "title": f"Nutrition facts for {query}",
                "snippet": f"Comprehensive nutritional information for {query} including calories, protein, fat, carbs, vitamins, and minerals.",
                "url": f"https://example.com/nutrition/{query.replace(' ', '-')}"
            }
        ] * min(num_results, 3)
        
        return ToolResponse(
            success=True,
            data={"results": results}
        )
    except Exception as e:
        logger.error(f"Error in google_search: {e}")
        return ToolResponse(
            success=False,
            error=str(e)
        )

@app.post("/tools/extract_nutrition")
async def extract_nutrition(tool_call: ToolCall) -> ToolResponse:
    """Extract nutritional data from search results"""
    try:
        food_item = tool_call.parameters.get("food_item", "").lower()
        serving_size = tool_call.parameters.get("serving_size")
        
        logger.info(f"Extracting nutrition for: {food_item}")
        
        # Find the best match in our nutrition database
        best_match = None
        best_score = 0
        
        for food_name, nutrition in NUTRITION_DB.items():
            if food_name in food_item or food_item in food_name:
                score = len(set(food_name.split()) & set(food_item.split()))
                if score > best_score:
                    best_score = score
                    best_match = nutrition
        
        if best_match:
            return ToolResponse(
                success=True,
                data=best_match
            )
        else:
            # Return default nutrition data
            return ToolResponse(
                success=True,
                data={
                    "calories": 100,
                    "protein_g": 5.0,
                    "fat_g": 3.0,
                    "carbs_g": 15.0,
                    "fiber_g": 2.0,
                    "sugar_g": 5.0,
                    "vitamin_c_mg": 10.0,
                    "calcium_mg": 50.0,
                    "iron_mg": 1.0,
                    "confidence_score": 0.5
                }
            )
    except Exception as e:
        logger.error(f"Error in extract_nutrition: {e}")
        return ToolResponse(
            success=False,
            error=str(e)
        )

@app.post("/tools/parse_food_input")
async def parse_food_input(tool_call: ToolCall) -> ToolResponse:
    """Parse natural language food input"""
    try:
        user_input = tool_call.parameters.get("user_input", "")
        extract_datetime_flag = tool_call.parameters.get("extract_datetime", True)
        extract_serving_sizes = tool_call.parameters.get("extract_serving_sizes", True)
        extract_meal_types = tool_call.parameters.get("extract_meal_types", True)
        
        logger.info(f"Parsing food input: {user_input}")
        
        # Extract food items
        food_items = extract_food_items(user_input)
        
        # Extract datetime if requested
        extracted_datetime = None
        if extract_datetime_flag:
            extracted_datetime = extract_datetime(user_input)
        
        # Extract meal type
        meal_type = None
        if extract_meal_types:
            meal_type = extract_meal_type(user_input)
        
        # Calculate overall confidence
        confidence_score = 0.8 if food_items else 0.3
        
        return ToolResponse(
            success=True,
            data={
                "food_items": food_items,
                "extracted_datetime": extracted_datetime,
                "confidence_score": confidence_score,
                "meal_type": meal_type
            }
        )
    except Exception as e:
        logger.error(f"Error in parse_food_input: {e}")
        return ToolResponse(
            success=False,
            error=str(e)
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "available_tools": ["google_search", "extract_nutrition", "parse_food_input"]
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "HealthUp MCP Server",
        "version": "1.0.0",
        "tools": [
            {
                "name": "google_search",
                "description": "Mock Google search for nutrition information",
                "endpoint": "/tools/google_search"
            },
            {
                "name": "extract_nutrition",
                "description": "Extract nutritional data from search results",
                "endpoint": "/tools/extract_nutrition"
            },
            {
                "name": "parse_food_input",
                "description": "Parse natural language food input",
                "endpoint": "/tools/parse_food_input"
            }
        ]
    }

if __name__ == "__main__":
    logger.info("Starting HealthUp MCP Server on http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001) 