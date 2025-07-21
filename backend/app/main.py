from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from typing import List, Optional
import os
from dotenv import load_dotenv
from . import models, database, schemas, crud, deps, worker
from .auth import router as auth_router
from .food_parser import FoodParserService
from .mcp_server import get_mcp_client
from cryptography.fernet import Fernet

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
cors_origins = os.getenv("CORS_ORIGINS")  # Also check for CORS_ORIGINS

if frontend_origins:
    origins_list = [o.strip() for o in frontend_origins.split(",") if o.strip()]
    cors_kwargs = {"allow_origins": origins_list}
elif cors_origins:
    origins_list = [o.strip() for o in cors_origins.split(",") if o.strip()]
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

@app.post("/insight/{period}/generate")
def generate_insight(
    period: str,
    period_start: date = None,
    user=Depends(deps.get_current_user),
    db=Depends(deps.get_db)
):
    """Generate AI insight for a specific period on-demand"""
    if period not in ['daily', 'weekly', 'monthly']:
        raise HTTPException(status_code=400, detail="Invalid period. Must be daily, weekly, or monthly")
    
    if not period_start:
        today = date.today()
        if period == 'daily':
            period_start = today
        elif period == 'weekly':
            period_start = today - timedelta(days=today.weekday())
        elif period == 'monthly':
            period_start = today.replace(day=1)
    
    # Check if insight already exists
    existing_insight = crud.get_ai_insight(db, user.id, period, period_start)
    if existing_insight:
        return {
            "message": f"{period.capitalize()} insight already exists for this period",
            "insight": existing_insight,
            "regenerated": False
        }
    
    try:
        # Import worker functions
        from .worker import get_user_data_for_period, build_daily_prompt, build_weekly_prompt, build_monthly_prompt, call_openai_with_grounding
        
        # Get comprehensive user data
        user_data = get_user_data_for_period(db, user.id, period, period_start)
        
        # Build appropriate prompt
        if period == 'daily':
            prompt = build_daily_prompt(user_data)
            agent_name = "Daily Health Coach"
        elif period == 'weekly':
            prompt = build_weekly_prompt(user_data)
            agent_name = "Weekly Health Coach"
        else:  # monthly
            prompt = build_monthly_prompt(user_data)
            agent_name = "Monthly Health Coach"
        
        # Generate insight using OpenAI
        insight_md = call_openai_with_grounding(prompt, agent_name)
        
        # Save to database
        insight = crud.create_ai_insight(db, user.id, period, period_start, insight_md)
        
        return {
            "message": f"{period.capitalize()} insight generated successfully",
            "insight": insight,
            "regenerated": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate insight: {str(e)}")

@app.post("/insight/{period}/regenerate")
def regenerate_insight(
    period: str,
    period_start: date = None,
    user=Depends(deps.get_current_user),
    db=Depends(deps.get_db)
):
    """Regenerate AI insight for a specific period (overwrites existing)"""
    if period not in ['daily', 'weekly', 'monthly']:
        raise HTTPException(status_code=400, detail="Invalid period. Must be daily, weekly, or monthly")
    
    if not period_start:
        today = date.today()
        if period == 'daily':
            period_start = today
        elif period == 'weekly':
            period_start = today - timedelta(days=today.weekday())
        elif period == 'monthly':
            period_start = today.replace(day=1)
    
    try:
        print(f"Starting insight regeneration for user {user.id}, period {period}, start {period_start}")
        
        # Import worker functions
        from .worker import get_user_data_for_period, build_daily_prompt, build_weekly_prompt, build_monthly_prompt, call_openai_with_grounding
        
        # Get comprehensive user data
        print("Getting user data for period...")
        user_data = get_user_data_for_period(db, user.id, period, period_start)
        print(f"User data retrieved: {len(user_data)} keys")
        
        # Build appropriate prompt
        print("Building prompt...")
        if period == 'daily':
            prompt = build_daily_prompt(user_data)
            agent_name = "Daily Health Coach"
        elif period == 'weekly':
            prompt = build_weekly_prompt(user_data)
            agent_name = "Weekly Health Coach"
        else:  # monthly
            prompt = build_monthly_prompt(user_data)
            agent_name = "Monthly Health Coach"
        
        print(f"Prompt built, length: {len(prompt)} characters")
        
        # Generate insight using OpenAI
        print("Calling OpenAI...")
        insight_md = call_openai_with_grounding(prompt, agent_name)
        print(f"OpenAI response received, length: {len(insight_md)} characters")
        
        # Delete existing insight if it exists
        existing_insight = crud.get_ai_insight(db, user.id, period, period_start)
        if existing_insight:
            print("Deleting existing insight...")
            db.delete(existing_insight)
            db.commit()
        
        # Save new insight to database
        print("Saving new insight to database...")
        insight = crud.create_ai_insight(db, user.id, period, period_start, insight_md)
        print("Insight saved successfully")
        
        return {
            "message": f"{period.capitalize()} insight regenerated successfully",
            "insight": insight,
            "regenerated": True
        }
        
    except Exception as e:
        print(f"Error in regenerate_insight: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to regenerate insight: {str(e)}")

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
        # Get database session
        db = next(deps.get_db())
        
        # Get the first user from the database
        user = db.query(models.User).first()
        if not user:
            raise HTTPException(status_code=404, detail="No users found in database")
        
        response = await food_parser_service.parse_food_input(
            request.user_input,
            str(user.id),
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
            sodium_mg=nutrition_data["sodium_mg"],
            vitamin_a_mcg=food_log.vitamin_a_mcg,
            vitamin_c_mg=food_log.vitamin_c_mg,
            vitamin_d_mcg=food_log.vitamin_d_mcg,
            vitamin_e_mg=food_log.vitamin_e_mg,
            vitamin_k_mcg=food_log.vitamin_k_mcg,
            vitamin_b1_mg=food_log.vitamin_b1_mg,
            vitamin_b2_mg=food_log.vitamin_b2_mg,
            vitamin_b3_mg=food_log.vitamin_b3_mg,
            vitamin_b5_mg=food_log.vitamin_b5_mg,
            vitamin_b6_mg=food_log.vitamin_b6_mg,
            vitamin_b7_mcg=food_log.vitamin_b7_mcg,
            vitamin_b9_mcg=food_log.vitamin_b9_mcg,
            vitamin_b12_mcg=food_log.vitamin_b12_mcg,
            calcium_mg=food_log.calcium_mg,
            iron_mg=food_log.iron_mg,
            magnesium_mg=food_log.magnesium_mg,
            phosphorus_mg=food_log.phosphorus_mg,
            potassium_mg=food_log.potassium_mg,
            zinc_mg=food_log.zinc_mg,
            copper_mg=food_log.copper_mg,
            manganese_mg=food_log.manganese_mg,
            selenium_mcg=food_log.selenium_mcg,
            chromium_mcg=food_log.chromium_mcg,
            molybdenum_mcg=food_log.molybdenum_mcg,
            cholesterol_mg=food_log.cholesterol_mg,
            saturated_fat_g=food_log.saturated_fat_g,
            trans_fat_g=food_log.trans_fat_g,
            polyunsaturated_fat_g=food_log.polyunsaturated_fat_g,
            monounsaturated_fat_g=food_log.monounsaturated_fat_g
        )
        
        # Generate analysis using the food parser service
        mcp_config = food_schemas.MCPServerConfig(
            api_key=os.getenv("OPENAI_API_KEY"),
            timeout=int(os.getenv("MCP_TIMEOUT", "30"))
        )
        
        food_parser = FoodParserService(mcp_config)
        meal_analysis = await food_parser._generate_meal_analysis([nutrition_item])
        
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

# Amazfit Integration Endpoints
@app.post("/amazfit/credentials", response_model=schemas.AmazfitCredentialsResponse)
def create_amazfit_credentials(
    credentials: schemas.AmazfitCredentialsCreate,
    current_user=Depends(deps.get_current_user),
    db=Depends(deps.get_db)
):
    """Create or update Amazfit credentials for the current user"""
    try:
        db_credentials = crud.create_amazfit_credentials(db, str(current_user.id), credentials)
        return db_credentials
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to save credentials: {str(e)}")

@app.get("/amazfit/credentials", response_model=schemas.AmazfitCredentialsResponse)
def get_amazfit_credentials(
    current_user=Depends(deps.get_current_user),
    db=Depends(deps.get_db)
):
    """Get Amazfit credentials for the current user"""
    credentials = crud.get_amazfit_credentials(db, str(current_user.id))
    if not credentials:
        raise HTTPException(status_code=404, detail="No Amazfit credentials found")
    return credentials

@app.delete("/amazfit/credentials")
def delete_amazfit_credentials(
    current_user=Depends(deps.get_current_user),
    db=Depends(deps.get_db)
):
    """Delete Amazfit credentials for the current user"""
    success = crud.delete_amazfit_credentials(db, str(current_user.id))
    if not success:
        raise HTTPException(status_code=404, detail="No Amazfit credentials found")
    return {"message": "Credentials deleted successfully"}

@app.post("/amazfit/sync", response_model=schemas.AmazfitSyncResponse)
def sync_amazfit_data(
    sync_request: schemas.AmazfitSyncRequest = schemas.AmazfitSyncRequest(),
    current_user=Depends(deps.get_current_user),
    db=Depends(deps.get_db)
):
    """Sync data from Amazfit"""
    try:
        from .amazfit_service import AmazfitDataSync
        
        sync_service = AmazfitDataSync(db, str(current_user.id))
        results = sync_service.sync_all_data(sync_request.days_back)
        
        return schemas.AmazfitSyncResponse(
            success=True,
            message="Data synced successfully",
            activity_synced=results['activity_synced'],
            steps_synced=results['steps_synced'],
            heart_rate_synced=results['heart_rate_synced'],
            sleep_synced=results['sleep_synced']
        )
        
    except Exception as e:
        # Assuming logger is available, otherwise replace with print or similar
        # logger.error(f"Failed to sync Amazfit data: {e}") 
        print(f"Failed to sync Amazfit data: {e}") # Placeholder for logger
        return schemas.AmazfitSyncResponse(
            success=False,
            message=f"Failed to sync data: {str(e)}",
            errors=[str(e)]
        )

@app.get("/amazfit/activity", response_model=List[schemas.ActivityDataResponse])
def get_activity_data(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 7,
    current_user=Depends(deps.get_current_user),
    db=Depends(deps.get_db)
):
    """Get activity data for the current user"""
    if start_date and end_date:
        activity_data = crud.get_activity_data(db, str(current_user.id), start_date, end_date)
    else:
        activity_data = crud.get_recent_activity_data(db, str(current_user.id), limit)
    
    return activity_data

@app.get("/amazfit/steps", response_model=List[schemas.StepsDataResponse])
def get_steps_data(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 7,
    current_user=Depends(deps.get_current_user),
    db=Depends(deps.get_db)
):
    """Get steps data for the current user"""
    if start_date and end_date:
        steps_data = crud.get_steps_data(db, str(current_user.id), start_date, end_date)
    else:
        steps_data = crud.get_recent_steps_data(db, str(current_user.id), limit)
    
    return steps_data

@app.get("/amazfit/today")
def get_today_summary(
    current_user=Depends(deps.get_current_user),
    db=Depends(deps.get_db)
):
    """Get today's activity summary for dashboard"""
    summary = crud.get_today_activity_summary(db, str(current_user.id))
    return summary

# New endpoints for frontend integration
@app.post("/amazfit/connect")
def connect_amazfit_account(
    credentials: schemas.AmazfitCredentialsCreate,
    current_user=Depends(deps.get_current_user),
    db=Depends(deps.get_db)
):
    """Connect Amazfit account using email/password"""
    try:
        # Get encryption key from environment
        encryption_key = os.getenv("AMAZFIT_ENCRYPTION_KEY")
        if not encryption_key:
            # Generate a new key if not set
            encryption_key = Fernet.generate_key().decode()
            print(f"WARNING: Generated new encryption key. Set AMAZFIT_ENCRYPTION_KEY={encryption_key}")
        
        # Test the credentials by getting a token
        from .amazfit_service import AmazfitService
        service = AmazfitService.from_credentials(credentials.email, credentials.password)
        
        # Encrypt credentials
        f = Fernet(encryption_key.encode())
        encrypted_email = f.encrypt(credentials.email.encode()).decode()
        encrypted_password = f.encrypt(credentials.password.encode()).decode()
        
        # Save to database
        db_credentials = models.AmazfitCredentials(
            user_id=current_user.id,
            app_token=service.app_token,
            user_id_amazfit=service.user_id,
            email=encrypted_email,
            password=encrypted_password
        )
        
        # Update existing or create new
        existing = db.query(models.AmazfitCredentials).filter(
            models.AmazfitCredentials.user_id == current_user.id
        ).first()
        
        if existing:
            existing.app_token = service.app_token
            existing.user_id_amazfit = service.user_id
            existing.email = encrypted_email
            existing.password = encrypted_password
            existing.updated_at = datetime.utcnow()
        else:
            db.add(db_credentials)
        
        db.commit()
        
        return {
            "message": "Amazfit account connected successfully",
            "user_id": service.user_id
        }
        
    except Exception as e:
        db.rollback()
        print(f"Error in connect_amazfit_account: {str(e)}")
        # Provide more specific error messages
        if "Login failed" in str(e) or "Login error" in str(e):
            raise HTTPException(status_code=400, detail="Invalid email or password. Please check your Amazfit credentials.")
        elif "Failed to communicate with Huami API" in str(e):
            raise HTTPException(status_code=400, detail="Unable to connect to Amazfit servers. Please try again later.")
        else:
            raise HTTPException(status_code=400, detail=f"Failed to connect Amazfit account: {str(e)}")

@app.get("/amazfit/day")
def get_amazfit_day_data(
    date_str: str,  # YYYY-MM-DD format
    adjust_date: bool = False,  # Add option to adjust date for timezone issues
    current_user=Depends(deps.get_current_user),
    db=Depends(deps.get_db)
):
    """Get Amazfit data for a specific day with caching"""
    try:
        # Parse date and convert to IST (UTC+5:30)
        # Amazfit API returns data in UTC, but we need to display in IST
        from datetime import timezone, timedelta
        
        # Parse the input date as UTC
        parsed_datetime = datetime.strptime(date_str, "%Y-%m-%d")
        utc_date = parsed_datetime.replace(tzinfo=timezone.utc)
        
        # Convert to IST (UTC+5:30)
        ist_offset = timedelta(hours=5, minutes=30)
        ist_date = utc_date + ist_offset
        
        # Use the IST date for API requests
        target_date = ist_date.date()
        
        print(f"DEBUG: Input date: {date_str}")
        print(f"DEBUG: UTC date: {utc_date.date()}")
        print(f"DEBUG: IST date: {target_date}")
        print(f"DEBUG: Requesting data for IST date: {target_date}")
        
        # First, check if we have cached data in the database
        cached_activity = db.query(models.ActivityData).filter(
            models.ActivityData.user_id == current_user.id,
            models.ActivityData.date == target_date
        ).first()
        
        cached_hr = db.query(models.HRSession).filter(
            models.HRSession.user_id == current_user.id,
            models.HRSession.logged_at >= target_date,
            models.HRSession.logged_at < target_date + timedelta(days=1)
        ).first()
        
        # If we have cached data, return it
        if cached_activity and cached_activity.raw_data:
            raw_data = cached_activity.raw_data
            
            # Extract heart rate data from cached HR session
            hr_data = []
            if cached_hr and cached_hr.session_data:
                hr_data = cached_hr.session_data.get('hr_values', [])
            
            return {
                "date": date_str,
                "heart_rate": hr_data,
                "steps": cached_activity.steps or 0,
                "calories": cached_activity.calories_burned or 0,
                "sleep_duration": int((cached_activity.sleep_hours or 0) * 3600),  # Convert hours to seconds
                "activity": {
                    "steps": cached_activity.steps,
                    "calories": cached_activity.calories_burned,
                    "distance": float(cached_activity.distance_km or 0),
                    "active_minutes": cached_activity.active_minutes
                },
                "sleep": {
                    "sleep_time_hours": float(cached_activity.sleep_hours or 0),
                    "deep_sleep_hours": float(cached_activity.deep_sleep_hours or 0),
                    "light_sleep_hours": float(cached_activity.light_sleep_hours or 0),
                    "rem_sleep_hours": float(cached_activity.rem_sleep_hours or 0),
                    "awake_hours": float(cached_activity.awake_hours or 0),
                    "sleep_time_seconds": int((cached_activity.sleep_hours or 0) * 3600)
                },
                "summary": raw_data.get('summary', {}),
                "workouts": raw_data.get('workouts', []),
                "events": raw_data.get('events', []),
                "hrv": raw_data.get('hrv', 0),
                "hr_stats": raw_data.get('hr_stats', {}),
                "cached": True
            }
        
        # If no cached data, fetch from API
        credentials = db.query(models.AmazfitCredentials).filter(
            models.AmazfitCredentials.user_id == current_user.id
        ).first()
        
        if not credentials:
            raise HTTPException(status_code=404, detail="Amazfit account not connected")
        
        # Check if we have the required fields
        if not credentials.app_token or not credentials.user_id_amazfit:
            raise HTTPException(status_code=400, detail="Amazfit credentials incomplete. Please reconnect your account.")
        
        # Use stored app_token and user_id directly instead of decrypting email/password
        from .amazfit_service import AmazfitService
        service = AmazfitService(credentials.app_token, credentials.user_id_amazfit)
        
        try:
            # Use the working approach: get_daily_summary which uses band_data
            daily_summary = service.get_daily_summary(target_date)
            
            # Extract data from the summary
            heart_rate = daily_summary.get('heart_rate', [])
            activity = daily_summary.get('activity', {})
            sleep = daily_summary.get('sleep', {})
            band_data = daily_summary.get('band_data', {})
            summary = service.decode_band_summary(band_data)
            
            # Cache the data in the database
            try:
                # Save activity data
                if cached_activity:
                    # Update existing record
                    cached_activity.steps = activity.get('steps', 0)
                    cached_activity.calories_burned = activity.get('calories', 0)
                    cached_activity.distance_km = activity.get('distance', 0) / 1000  # Convert meters to km
                    cached_activity.active_minutes = activity.get('active_minutes', 0)
                    cached_activity.sleep_hours = sleep.get('sleep_time_hours', 0)
                    cached_activity.deep_sleep_hours = sleep.get('deep_sleep_hours', 0)
                    cached_activity.light_sleep_hours = sleep.get('light_sleep_hours', 0)
                    cached_activity.rem_sleep_hours = sleep.get('rem_sleep_hours', 0)
                    cached_activity.awake_hours = sleep.get('awake_hours', 0)
                    cached_activity.raw_data = daily_summary
                    cached_activity.updated_at = datetime.utcnow()
                else:
                    # Create new record
                    new_activity = models.ActivityData(
                        user_id=current_user.id,
                        date=target_date,
                        steps=activity.get('steps', 0),
                        calories_burned=activity.get('calories', 0),
                        distance_km=activity.get('distance', 0) / 1000,  # Convert meters to km
                        active_minutes=activity.get('active_minutes', 0),
                        sleep_hours=sleep.get('sleep_time_hours', 0),
                        deep_sleep_hours=sleep.get('deep_sleep_hours', 0),
                        light_sleep_hours=sleep.get('light_sleep_hours', 0),
                        rem_sleep_hours=sleep.get('rem_sleep_hours', 0),
                        awake_hours=sleep.get('awake_hours', 0),
                        raw_data=daily_summary
                    )
                    db.add(new_activity)
                
                # Save heart rate data if available
                if heart_rate and len(heart_rate) > 0:
                    # Calculate HR statistics
                    valid_hr = [hr for hr in heart_rate if hr > 0]
                    if valid_hr:
                        hr_stats = {
                            'avg_hr': sum(valid_hr) // len(valid_hr),
                            'max_hr': max(valid_hr),
                            'min_hr': min(valid_hr),
                            'duration_minutes': len(valid_hr),
                            'total_readings': len(heart_rate),
                            'valid_readings': len(valid_hr)
                        }
                        
                        if cached_hr:
                            # Update existing HR session
                            cached_hr.avg_hr = hr_stats['avg_hr']
                            cached_hr.max_hr = hr_stats['max_hr']
                            cached_hr.min_hr = hr_stats['min_hr']
                            cached_hr.duration_minutes = hr_stats['duration_minutes']
                            cached_hr.session_data = {
                                'hr_values': heart_rate,
                                'stats': hr_stats
                            }
                        else:
                            # Create new HR session
                            new_hr = models.HRSession(
                                user_id=current_user.id,
                                avg_hr=hr_stats['avg_hr'],
                                max_hr=hr_stats['max_hr'],
                                min_hr=hr_stats['min_hr'],
                                duration_minutes=hr_stats['duration_minutes'],
                                session_data={
                                    'hr_values': heart_rate,
                                    'stats': hr_stats
                                },
                                logged_at=datetime.combine(target_date, datetime.min.time())
                            )
                            db.add(new_hr)
                
                db.commit()
                
            except Exception as cache_error:
                # Log cache error but don't fail the request
                print(f"Failed to cache data: {cache_error}")
                db.rollback()
            
        except Exception as e:
            # If Huami API returns 404 (no data), return empty/default response
            if "404" in str(e) or "Not Found" in str(e):
                return {
                    "date": date_str,
                    "heart_rate": [],
                    "steps": 0,
                    "calories": 0,
                    "sleep_duration": 0,
                    "activity": {},
                    "sleep": {},
                    "summary": {},
                    "cached": False
                }
            else:
                print(f"Error in get_amazfit_day_data: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Failed to get day data: {str(e)}")
        
        # Process the data from the summary
        steps = activity.get('steps', 0)
        calories = activity.get('calories', 0)
        sleep_duration = sleep.get('sleep_time_seconds', 0)
        
        return {
            "date": date_str,
            "heart_rate": heart_rate,
            "steps": steps,
            "calories": calories,
            "sleep_duration": sleep_duration,  # in seconds
            "activity": activity,
            "sleep": sleep,
            "summary": summary,
            "workouts": daily_summary.get('workouts', []),
            "events": daily_summary.get('events', []),
            "hrv": daily_summary.get('hrv', 0),
            "hr_stats": daily_summary.get('hr_stats', {}),
            "cached": False
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        print(f"Error in get_amazfit_day_data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get day data: {str(e)}")

@app.post("/amazfit/refresh-token")
def refresh_amazfit_token(
    current_user=Depends(deps.get_current_user),
    db=Depends(deps.get_db)
):
    """Refresh Amazfit token using stored credentials"""
    try:
        # Get credentials
        credentials = db.query(models.AmazfitCredentials).filter(
            models.AmazfitCredentials.user_id == current_user.id
        ).first()
        
        if not credentials:
            raise HTTPException(status_code=404, detail="Amazfit account not connected")
        
        # Decrypt credentials
        encryption_key = os.getenv("AMAZFIT_ENCRYPTION_KEY")
        if not encryption_key:
            raise HTTPException(status_code=500, detail="Encryption key not configured")
        
        f = Fernet(encryption_key.encode())
        email = f.decrypt(credentials.email.encode()).decode()
        password = f.decrypt(credentials.password.encode()).decode()
        
        # Get fresh token
        from .amazfit_service import AmazfitService
        service = AmazfitService.from_credentials(email, password)
        
        # Update database
        credentials.app_token = service.app_token
        credentials.user_id_amazfit = service.user_id
        credentials.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "message": "Token refreshed successfully",
            "user_id": service.user_id
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to refresh token: {str(e)}")

# User Profile endpoints
@app.post("/profile", response_model=schemas.UserProfileResponse)
def create_or_update_profile(profile: schemas.UserProfileCreate, user=Depends(deps.get_current_user), db=Depends(deps.get_db)):
    """Create or update user profile"""
    profile_data = profile.dict()
    db_profile = crud.create_user_profile(db, user.id, profile_data)
    return db_profile

@app.get("/profile", response_model=schemas.UserProfileResponse)
def get_profile(user=Depends(deps.get_current_user), db=Depends(deps.get_db)):
    """Get user profile"""
    profile = crud.get_user_profile(db, user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@app.put("/profile", response_model=schemas.UserProfileResponse)
def update_profile(profile: schemas.UserProfileUpdate, user=Depends(deps.get_current_user), db=Depends(deps.get_db)):
    """Update user profile"""
    existing_profile = crud.get_user_profile(db, user.id)
    if not existing_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    profile_data = profile.dict(exclude_unset=True)
    db_profile = crud.create_user_profile(db, user.id, profile_data)
    return db_profile

# Food Bank endpoints
@app.get("/food-bank/{period}", response_model=schemas.FoodBankResponse)
def get_food_bank(period: str, user=Depends(deps.get_current_user), db=Depends(deps.get_db)):
    """Get food bank data for a period (daily, weekly, monthly)"""
    if period not in ['daily', 'weekly', 'monthly']:
        raise HTTPException(status_code=400, detail="Period must be daily, weekly, or monthly")
    
    # Calculate date range
    now = datetime.utcnow()
    if period == 'daily':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif period == 'weekly':
        start_date = now - timedelta(days=now.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=6)
        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    else:  # monthly
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month == 12:
            end_date = now.replace(year=now.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = now.replace(month=now.month + 1, day=1) - timedelta(days=1)
        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    summary = crud.calculate_nutritional_summary(db, user.id, period, start_date, end_date)
    if not summary:
        raise HTTPException(status_code=404, detail="User profile not found. Please create a profile first.")
    
    food_logs = crud.get_food_logs_by_period(db, user.id, period, start_date, end_date)
    
    return schemas.FoodBankResponse(
        summary=summary,
        food_logs=food_logs
    )

@app.get("/nutritional-requirements")
def get_nutritional_requirements(user=Depends(deps.get_current_user), db=Depends(deps.get_db)):
    """Get user's daily nutritional requirements"""
    profile = crud.get_user_profile(db, user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    requirements = crud.calculate_nutritional_requirements(profile)
    return {"requirements": requirements}
