#!/usr/bin/env python3
"""
Test script for the food parser functionality
"""

import asyncio
import sys
import os
sys.path.append('./backend')

from backend.app.food_parser import FoodParserService
from backend.app.schemas import MCPServerConfig
from backend.app.database import get_db

async def test_food_parser():
    """Test the food parser with a simple input"""
    
    # Create MCP config
    mcp_config = MCPServerConfig(
        server_url="http://localhost:8000",
        timeout=30
    )
    
    # Create food parser service
    parser = FoodParserService(mcp_config)
    
    # Test input
    user_input = "I had 1 banana for breakfast"
    user_id = "test-user-id"
    
    print(f"Testing food parser with input: '{user_input}'")
    print("=" * 50)
    
    try:
        # Get database session
        db = next(get_db())
        
        # Parse food input
        result = await parser.parse_food_input(user_input, user_id, db)
        
        print("✅ Food parsing successful!")
        print(f"Session ID: {result.session_id}")
        print(f"Status: {result.status}")
        print(f"Confidence Score: {result.confidence_score}")
        print(f"Meal Type: {result.meal_type}")
        print(f"Extracted DateTime: {result.extracted_datetime}")
        
        print("\n📋 Parsed Foods:")
        for i, food in enumerate(result.parsed_foods, 1):
            print(f"  {i}. {food['description']}")
            print(f"     Serving Size: {food['serving_size']}")
            print(f"     Meal Type: {food['meal_type']}")
            print(f"     Calories: {food['nutritional_data'].get('calories_kcal', 0)} kcal")
            print(f"     Protein: {food['nutritional_data'].get('protein_g', 0)}g")
            print(f"     Fat: {food['nutritional_data'].get('fat_g', 0)}g")
            print(f"     Carbs: {food['nutritional_data'].get('carbs_g', 0)}g")
            print(f"     Fiber: {food['nutritional_data'].get('fiber_g', 0)}g")
            print(f"     Sugar: {food['nutritional_data'].get('sugar_g', 0)}g")
            print(f"     Sodium: {food['nutritional_data'].get('sodium_mg', 0)}mg")
            
            # Show some vitamins and minerals
            print(f"     Vitamin C: {food['nutritional_data'].get('vitamin_c_mg', 0)}mg")
            print(f"     Calcium: {food['nutritional_data'].get('calcium_mg', 0)}mg")
            print(f"     Iron: {food['nutritional_data'].get('iron_mg', 0)}mg")
            print()
        
        if result.meal_analysis:
            print("🍽️ Meal Analysis:")
            print(f"  Health Score: {result.meal_analysis.overall_health_score}/100")
            print(f"  Protein Adequacy: {result.meal_analysis.protein_adequacy}")
            print(f"  Fiber Content: {result.meal_analysis.fiber_content}")
            print(f"  Vitamin Balance: {result.meal_analysis.vitamin_balance}")
            print(f"  Mineral Balance: {result.meal_analysis.mineral_balance}")
            print("  Recommendations:")
            for rec in result.meal_analysis.recommendations:
                print(f"    - {rec}")
        
        # Test creating food logs
        print("\n💾 Testing food log creation...")
        food_logs = await parser.create_food_logs_from_session(result.session_id, user_id, db)
        print(f"✅ Created {len(food_logs)} food logs")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing food parser: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Set environment variables for testing
    os.environ.setdefault("OPENAI_API_KEY", "sk-proj-your-openai-api-key-here")
    os.environ.setdefault("DATABASE_URL", "postgresql://healthup:healthup_secure_password_a2032334186a8000@localhost:5433/healthup")
    
    # Run the test
    success = asyncio.run(test_food_parser())
    
    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Tests failed!")
        sys.exit(1) 