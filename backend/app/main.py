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
from .food_parser import FoodParserService
from .mcp_server import get_mcp_client

load_dotenv()

app = FastAPI(title="HealthUp API", version="1.0.0")

# Configure CORS
# When credentials (cookies) are included in requests, the Access-Control-Allow-Origin header must
#    be the exact origin (not the wildcard "*").  To support both localhost development and
#    dynamic Tailscale IPs we allow any http/https origin on port 3000 using a regex.  Starlette's
#    CORSMiddleware will echo back the requesting origin when the regex matches, satisfying the
#    browser's security requirements while still letting cookies flow.
#
#    If you need to further restrict the allowed origins, set the environment variable
#    FRONTEND_ORIGINS (comma-separated) or FRONTEND_ORIGIN_REGEX.
#
frontend_origins = os.getenv("FRONTEND_ORIGINS")
frontend_origin_regex = os.getenv("FRONTEND_ORIGIN_REGEX")

if frontend_origins:
    origins_list = [o.strip() for o in frontend_origins.split(",") if o.strip()]
    cors_kwargs = {"allow_origins": origins_list}
else:
    # Default regex matches http://localhost:3000, http://127.0.0.1:3000 and any 100.x.x.x tailscale IPs on port 3000
    default_regex = frontend_origin_regex or r"https?://(?:localhost|127\.0\.0\.1|100(?:\.\d{1,3}){3})(?::\d+)?"
    cors_kwargs = {"allow_origin_regex": default_regex}

cors_kwargs.update({
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
})

app.add_middleware(CORSMiddleware, **cors_kwargs)

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
        # Return a placeholder response instead of 404
        return {
            "period": period,
            "period_start": period_start.isoformat(),
            "insight_md": f"# {period.capitalize()} Insights\n\nYour AI coach is analyzing your {period} data. Keep logging your health metrics to receive personalized insights!\n\n## What to expect:\n- Personalized health recommendations\n- Trend analysis and patterns\n- Actionable next steps\n- Motivational guidance",
            "created_at": datetime.utcnow().isoformat()
        }
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

# Food Log Analysis endpoints
@app.post("/food/{food_id}/analyze")
async def analyze_food_log(
    food_id: int,
    user=Depends(deps.get_current_user),
    db=Depends(deps.get_db)
):
    """Analyze a specific food log using AI"""
    try:
        # Get the food log
        food_log = db.query(models.FoodLog).filter(
            models.FoodLog.id == food_id,
            models.FoodLog.user_id == user.id
        ).first()
        
        if not food_log:
            raise HTTPException(status_code=404, detail="Food log not found")
        
        # Check if analysis already exists
        existing_analysis = crud.get_food_log_analysis(db, food_id, user.id)
        if existing_analysis:
            return existing_analysis
        
        # Create analysis using OpenAI agent
        from .food_parser import FoodParserService
        from . import schemas as food_schemas
        
        # Create a single food item for analysis
        nutrition_data = {
            "calories_kcal": food_log.calories or 0,
            "protein_g": food_log.protein_g or 0,
            "fat_g": food_log.fat_g or 0,
            "carbs_g": food_log.carbs_g or 0,
            "fiber_g": food_log.fiber_g or 0,
            "sugar_g": food_log.sugar_g or 0,
            "sodium_mg": food_log.sodium_mg or 0
        }
        
        # Create a Nutrients object for analysis
        from .food_parser import Nutrients
        nutrition_item = Nutrients(
            dish=food_log.description,
            calories_kcal=nutrition_data["calories_kcal"],
            protein_g=nutrition_data["protein_g"],
            fat_g=nutrition_data["fat_g"],
            carbs_g=nutrition_data["carbs_g"],
            fiber_g=nutrition_data["fiber_g"],
            sugar_g=nutrition_data["sugar_g"],
            sodium_mg=nutrition_data["sodium_mg"]
        )
        
        # Generate analysis using the food parser service
        mcp_config = food_schemas.MCPServerConfig(
            api_key=os.getenv("OPENAI_API_KEY"),
            timeout=int(os.getenv("MCP_TIMEOUT", "30"))
        )
        
        food_parser = FoodParserService(mcp_config)
        meal_analysis = await food_parser._generate_meal_analysis_with_agent([nutrition_item])
        
        if meal_analysis:
            # Create analysis record
            analysis_data = food_schemas.FoodLogAnalysisCreate(
                food_log_id=food_id,
                health_score=meal_analysis.overall_health_score,
                protein_adequacy=meal_analysis.protein_adequacy,
                fiber_content=meal_analysis.fiber_content,
                vitamin_balance=meal_analysis.vitamin_balance,
                mineral_balance=meal_analysis.mineral_balance,
                recommendations=meal_analysis.recommendations,
                analysis_text=f"AI analysis for {food_log.description}",
                model_used="OpenAI Agent",
                confidence_score=0.9
            )
            
            analysis = crud.create_food_log_analysis(db, user.id, analysis_data)
            return analysis
        else:
            raise HTTPException(status_code=500, detail="Failed to generate analysis")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze food log: {str(e)}")

@app.get("/food/{food_id}/analysis")
def get_food_log_analysis(
    food_id: int,
    user=Depends(deps.get_current_user),
    db=Depends(deps.get_db)
):
    """Get analysis for a specific food log"""
    analysis = crud.get_food_log_analysis(db, food_id, user.id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis

@app.get("/food/history/with-analysis")
def get_food_history_with_analysis(
    limit: int = 10,
    user=Depends(deps.get_current_user),
    db=Depends(deps.get_db)
):
    """Get food history with analysis"""
    food_logs_with_analysis = crud.get_food_logs_with_analysis(db, user.id, limit)
    return {"logs": food_logs_with_analysis}

@app.get("/food/{food_id}/with-analysis")
def get_food_log_with_analysis(
    food_id: int,
    user=Depends(deps.get_current_user),
    db=Depends(deps.get_db)
):
    """Get a food log with its analysis"""
    result = crud.get_food_log_with_analysis(db, food_id, user.id)
    if not result:
        raise HTTPException(status_code=404, detail="Food log not found")
    return result
