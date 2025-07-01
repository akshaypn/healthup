from fastapi import FastAPI, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from . import models, database, schemas, crud, deps, worker
from .auth import router as auth_router

app = FastAPI(title="HealthUp API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "HealthUp API"}

app.include_router(auth_router)

@app.get("/auth/me")
def get_current_user(user=Depends(deps.get_current_user)):
    return {"id": str(user.id), "email": user.email}

@app.get("/dashboard")
def get_dashboard(user=Depends(deps.get_current_user), db=Depends(deps.get_db)):
    """Get dashboard data"""
    # Get recent logs
    recent_weight = crud.get_recent_weight_logs(db, user.id, limit=7)
    recent_food = crud.get_recent_food_logs(db, user.id, limit=10)
    recent_hr = crud.get_recent_hr_logs(db, user.id, limit=5)
    
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
    return crud.create_weight_log(db, user.id, log)

@app.get("/weight/history", response_model=schemas.WeightHistoryResponse)
def get_weight_history(user=Depends(deps.get_current_user), db=Depends(deps.get_db)):
    """Get weight history"""
    logs = crud.get_weight_logs(db, user.id)
    return {"logs": logs}

@app.post("/food")
def log_food(log: schemas.FoodLogCreate, user=Depends(deps.get_current_user), db=Depends(deps.get_db)):
    return crud.create_food_log(db, user.id, log)

@app.get("/food/history", response_model=schemas.FoodHistoryResponse)
def get_food_history(user=Depends(deps.get_current_user), db=Depends(deps.get_db)):
    """Get food history"""
    logs = crud.get_food_logs(db, user.id)
    return {"logs": logs}

@app.post("/hr")
def log_hr(log: schemas.HRLogCreate, user=Depends(deps.get_current_user), db=Depends(deps.get_db)):
    return crud.create_hr_log(db, user.id, log)

@app.get("/hr/history", response_model=schemas.HRHistoryResponse)
def get_hr_history(user=Depends(deps.get_current_user), db=Depends(deps.get_db)):
    """Get HR history"""
    logs = crud.get_hr_logs(db, user.id)
    return {"logs": logs}

@app.get("/insight/{period}", response_model=schemas.AIInsightResponse)
def get_insight(period: str, user=Depends(deps.get_current_user), db=Depends(deps.get_db)):
    insight = crud.get_ai_insight(db, user.id, period)
    if not insight:
        return {"period": period, "period_start": None, "insight_md": "", "created_at": None}
    return {
        "period": insight.period,
        "period_start": str(insight.period_start),
        "insight_md": insight.insight_md,
        "created_at": insight.created_at.isoformat(),
    }

@app.get("/coach/today")
def get_today_coach(user=Depends(deps.get_current_user), background_tasks: BackgroundTasks=BackgroundTasks()):
    """Get real-time coaching advice for today"""
    # Check cache first
    cache_key = f"coach_today:{user.id}"
    # For now, generate fresh advice
    # In production, you'd check Redis cache here
    
    # Generate coaching advice in background
    background_tasks.add_task(worker.generate_realtime_coach, str(user.id))
    
    return {
        "message": "Coaching advice is being generated",
        "tips": [
            "Stay hydrated throughout the day",
            "Take a 10-minute walk",
            "Log your next meal with accurate portions"
        ]
    }

@app.post("/coach/chat")
def chat_with_coach(message: dict, user=Depends(deps.get_current_user), background_tasks: BackgroundTasks=BackgroundTasks()):
    """Chat with AI coach"""
    background_tasks.add_task(worker.generate_realtime_coach, str(user.id))
    return {
        "message": "Your message has been sent to the coach",
        "response": "I'm analyzing your health data and will provide personalized advice shortly."
    }
