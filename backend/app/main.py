from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from typing import List
import os
from dotenv import load_dotenv
from . import models, database, schemas, crud, deps, worker
from .auth import router as auth_router
from .food_parser import FoodParserService, FallbackFoodParser
from .mcp_server import get_mcp_client

load_dotenv()

app = FastAPI(title="HealthUp API", version="1.0.0")

# For development with Tailscale, allow all origins
# In production, you should specify exact origins
origins = os.getenv("CORS_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# MCP Server configuration
mcp_config = schemas.MCPServerConfig(
    api_key=os.getenv("OPENAI_API_KEY"),
    timeout=int(os.getenv("MCP_TIMEOUT", "30"))
)

# Initialize food parser service
food_parser_service = FoodParserService(mcp_config)

@app.get("/")
def root():
    return {"message": "HealthUp API"}

app.include_router(auth_router)

@app.get("/dashboard")
def get_dashboard(user=Depends(deps.get_current_user), db=Depends(deps.get_db)):
    """Get dashboard data"""
    # Get recent logs
    recent_weight = crud.get_recent_weight_logs(db, user.id, limit=7)
    recent_food = crud.get_recent_food_logs(db, user.id, limit=10)
    recent_hr = crud.get_recent_hr_sessions(db, user.id, limit=5)
    
    return {
        "recent_weight": recent_weight,
        "recent_food": recent_food,
        "recent_hr": recent_hr,
        "stats": {
            "total_weight_entries": len(recent_weight),
            "total_food_entries": len(recent_food),
            "total_hr_sessions": len(recent_hr)
        }
    }

@app.post("/weight")
def log_weight(log: schemas.WeightLogCreate, user=Depends(deps.get_current_user), db=Depends(deps.get_db)):
    """Log weight entry"""
    return crud.create_weight_log(db, user.id, log)

@app.get("/weight/history", response_model=schemas.WeightHistoryResponse)
def get_weight_history(user=Depends(deps.get_current_user), db=Depends(deps.get_db)):
    """Get weight history"""
    logs = crud.get_weight_logs(db, user.id)
    return {"logs": logs}

@app.post("/food")
def log_food(log: schemas.FoodLogCreate, user=Depends(deps.get_current_user), db=Depends(deps.get_db)):
    """Log food entry with comprehensive nutritional data"""
    return crud.create_food_log(db, user.id, log)

@app.get("/food/history", response_model=schemas.FoodHistoryResponse)
def get_food_history(user=Depends(deps.get_current_user), db=Depends(deps.get_db)):
    """Get food history"""
    logs = crud.get_food_logs(db, user.id)
    return {"logs": logs}

@app.get("/food/today", response_model=schemas.FoodHistoryResponse)
def get_todays_food(user=Depends(deps.get_current_user), db=Depends(deps.get_db)):
    """Get today's food logs"""
    logs = crud.get_todays_food_logs(db, user.id)
    return {"logs": logs}

@app.put("/food/{food_id}")
def update_food_log(food_id: int, updates: dict, user=Depends(deps.get_current_user), db=Depends(deps.get_db)):
    """Update a food log"""
    updated_log = crud.update_food_log(db, food_id, user.id, updates)
    if not updated_log:
        raise HTTPException(status_code=404, detail="Food log not found")
    return updated_log

@app.delete("/food/{food_id}")
def delete_food_log(food_id: int, user=Depends(deps.get_current_user), db=Depends(deps.get_db)):
    """Delete a food log"""
    success = crud.delete_food_log(db, food_id, user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Food log not found")
    return {"message": "Food log deleted successfully"}

@app.get("/food/nutrition-summary")
def get_nutrition_summary(
    start_date: date = None,
    end_date: date = None,
    user=Depends(deps.get_current_user),
    db=Depends(deps.get_db)
):
    """Get nutrition summary for a date range"""
    if not start_date:
        start_date = date.today()
    if not end_date:
        end_date = start_date
    
    summary = crud.get_nutrition_summary(db, user.id, start_date, end_date)
    return summary

@app.post("/food/parse", response_model=schemas.FoodParsingResponse)
async def parse_food_input(
    request: schemas.FoodParsingRequest,
    user=Depends(deps.get_current_user),
    db=Depends(deps.get_db)
):
    """Parse natural language food input using AI"""
    try:
        response = await food_parser_service.parse_food_input(
            request.user_input,
            user.id,
            db
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse food input: {str(e)}")

@app.post("/food/parse/{session_id}/create-logs")
async def create_food_logs_from_session(
    session_id: str,
    user=Depends(deps.get_current_user),
    db=Depends(deps.get_db)
):
    """Create food logs from a completed parsing session"""
    try:
        food_logs = await food_parser_service.create_food_logs_from_session(
            session_id,
            user.id,
            db
        )
        return {
            "message": f"Created {len(food_logs)} food logs",
            "food_logs": food_logs
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create food logs: {str(e)}")

@app.get("/food/parse/sessions", response_model=List[schemas.FoodParsingSessionResponse])
def get_parsing_sessions(user=Depends(deps.get_current_user), db=Depends(deps.get_db)):
    """Get user's food parsing sessions"""
    sessions = crud.get_user_food_parsing_sessions(db, user.id)
    return sessions

@app.get("/food/parse/sessions/{session_id}", response_model=schemas.FoodParsingSessionResponse)
def get_parsing_session(session_id: str, user=Depends(deps.get_current_user), db=Depends(deps.get_db)):
    """Get a specific food parsing session"""
    session = crud.get_food_parsing_session(db, session_id, user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Parsing session not found")
    return session

@app.post("/hr")
def log_hr_session(session: schemas.HRSessionCreate, user=Depends(deps.get_current_user), db=Depends(deps.get_db)):
    """Log heart rate session"""
    return crud.create_hr_session(db, user.id, session)

@app.get("/hr/history")
def get_hr_history(user=Depends(deps.get_current_user), db=Depends(deps.get_db)):
    """Get heart rate history"""
    sessions = crud.get_hr_sessions(db, user.id)
    return {"sessions": sessions}

@app.get("/insight/{period}")
def get_ai_insight(
    period: str,
    period_start: date = None,
    user=Depends(deps.get_current_user),
    db=Depends(deps.get_db)
):
    """Get AI insight for a specific period"""
    if not period_start:
        today = date.today()
        if period == 'daily':
            period_start = today
        elif period == 'weekly':
            period_start = today - timedelta(days=today.weekday())
        elif period == 'monthly':
            period_start = today.replace(day=1)
        else:
            raise HTTPException(status_code=400, detail="Invalid period")
    
    insight = crud.get_ai_insight(db, user.id, period, period_start)
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")
    return insight

@app.get("/coach/today")
def get_todays_coaching(user=Depends(deps.get_current_user), db=Depends(deps.get_db)):
    """Get real-time coaching advice for today"""
    # Get today's data
    todays_food = crud.get_todays_food_logs(db, user.id)
    recent_weight = crud.get_recent_weight_logs(db, user.id, 1)
    
    # Generate coaching advice
    tips = []
    message = "Here's your personalized health advice for today!"
    
    if not todays_food:
        tips.append("You haven't logged any food today. Consider tracking your meals for better insights.")
        message = "Let's start tracking your nutrition today!"
    else:
        tips.append(f"You've logged {len(todays_food)} meals today. Great job staying on track!")
        
        # Calculate total calories
        total_calories = sum(food.calories or 0 for food in todays_food)
        if total_calories > 0:
            tips.append(f"Total calories today: {total_calories} kcal")
        
        # Check protein intake
        total_protein = sum(food.protein_g or 0 for food in todays_food)
        if total_protein > 0:
            tips.append(f"Protein intake: {total_protein:.1f}g")
    
    if recent_weight:
        latest_weight = recent_weight[0]
        tips.append(f"Your latest weight: {latest_weight.kg} kg")
        
        # Check if there's a trend
        if len(recent_weight) > 1:
            previous_weight = recent_weight[1].kg
            change = latest_weight.kg - previous_weight
            if abs(change) > 0.1:  # Significant change
                if change > 0:
                    tips.append("You've gained some weight. Consider reviewing your nutrition and exercise routine.")
                else:
                    tips.append("You've lost some weight. Keep up the great work!")
    
    # Add general health tips
    tips.append("Stay hydrated! Aim for 8 glasses of water daily.")
    tips.append("Try to get at least 30 minutes of physical activity today.")
    
    return {
        "tips": tips,
        "message": message
    }

@app.post("/coach/chat")
def chat_with_coach(message: dict, user=Depends(deps.get_current_user), background_tasks: BackgroundTasks=BackgroundTasks()):
    """Chat with AI coach"""
    background_tasks.add_task(worker.generate_realtime_coach, str(user.id))
    return {
        "message": "Your message has been sent to the coach",
        "response": "I'm analyzing your health data and will provide personalized advice shortly."
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/test/food-parse")
async def test_food_parse(request: schemas.FoodParsingRequest):
    """Test endpoint for food parsing without authentication"""
    try:
        # Create a mock user ID for testing (valid UUID)
        test_user_id = "ccde30d4-5b22-4b4c-a2eb-5d7dbd72000a"
        
        # Get database session
        db = next(deps.get_db())
        
        response = await food_parser_service.parse_food_input(
            request.user_input,
            test_user_id,
            db
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse food input: {str(e)}")
