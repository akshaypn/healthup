import os
import json
import logging
from datetime import datetime, timedelta, date
from typing import Dict, Any, Optional
from celery import Celery
from openai import OpenAI
from sqlalchemy.orm import Session
from . import models, database, crud
from .database import get_db

# Configure Celery
celery_app = Celery(
    "healthup_worker",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379")
)

# Initialize OpenAI client
client = OpenAI()

class TokenBucket:
    """Rate limiting for OpenAI API calls"""
    def __init__(self):
        self.redis_client = celery_app.backend.client
        
    def can_make_request(self, model: str, project: str = "default") -> bool:
        key = f"openai_rate_limit:{project}:{model}"
        next_allowed = self.redis_client.get(key)
        if next_allowed is None:
            return True
        return datetime.now().timestamp() > float(next_allowed)
    
    def set_next_allowed(self, model: str, delay_seconds: int, project: str = "default"):
        key = f"openai_rate_limit:{project}:{model}"
        next_time = datetime.now().timestamp() + delay_seconds
        self.redis_client.setex(key, delay_seconds + 10, next_time)

token_bucket = TokenBucket()

def build_daily_prompt(user_data: Dict[str, Any]) -> str:
    """Build prompt for daily insights"""
    prompt = f"""
    You are a personal health coach analyzing daily health data. Provide a concise, motivating summary and actionable next steps.
    
    User's daily data:
    - Weight: {user_data.get('weight', 'No data')} kg
    - Food entries: {len(user_data.get('food', []))} entries
    - Total calories: {sum(f.get('calories', 0) for f in user_data.get('food', []))} kcal
    - Protein: {sum(f.get('protein_g', 0) for f in user_data.get('food', []))}g
    - Fat: {sum(f.get('fat_g', 0) for f in user_data.get('food', []))}g
    - Carbs: {sum(f.get('carbs_g', 0) for f in user_data.get('food', []))}g
    - Heart rate sessions: {len(user_data.get('hr_sessions', []))} sessions
    
    Provide a markdown response with:
    1. Brief summary of the day
    2. 2-3 specific, actionable next steps
    3. Motivational note
    
    Keep it under 200 words and be encouraging.
    """
    return prompt

def build_weekly_prompt(user_data: Dict[str, Any]) -> str:
    """Build prompt for weekly insights"""
    prompt = f"""
    You are a personal health coach analyzing weekly health trends. Provide a comprehensive weekly report with insights and recommendations.
    
    User's weekly data:
    - Weight trend: {user_data.get('weight_trend', 'No data')}
    - Average daily calories: {user_data.get('avg_calories', 0)} kcal
    - Average daily protein: {user_data.get('avg_protein', 0)}g
    - Average daily fat: {user_data.get('avg_fat', 0)}g
    - Average daily carbs: {user_data.get('avg_carbs', 0)}g
    - Heart rate sessions: {len(user_data.get('hr_sessions', []))} sessions
    - Average HR: {user_data.get('avg_hr', 'No data')} bpm
    
    Provide a markdown response with:
    1. Weekly summary and trends
    2. Progress highlights
    3. Areas for improvement
    4. 3-5 specific recommendations for next week
    5. Motivational closing
    
    Keep it under 400 words and be encouraging.
    """
    return prompt

def build_monthly_prompt(user_data: Dict[str, Any]) -> str:
    """Build prompt for monthly insights"""
    prompt = f"""
    You are a personal health coach analyzing monthly health progress. Provide a comprehensive monthly report with deep insights and strategic recommendations.
    
    User's monthly data:
    - Weight progress: {user_data.get('weight_progress', 'No data')}
    - Average daily calories: {user_data.get('avg_calories', 0)} kcal
    - Average daily protein: {user_data.get('avg_protein', 0)}g
    - Average daily fat: {user_data.get('avg_fat', 0)}g
    - Average daily carbs: {user_data.get('avg_carbs', 0)}g
    - Heart rate sessions: {len(user_data.get('hr_sessions', []))} sessions
    - Average HR: {user_data.get('avg_hr', 'No data')} bpm
    - Consistency score: {user_data.get('consistency', 'No data')}%
    
    Provide a markdown response with:
    1. Monthly overview and major achievements
    2. Trend analysis and patterns
    3. Progress toward goals
    4. 5-7 strategic recommendations for next month
    5. Long-term health strategy suggestions
    6. Motivational closing
    
    Keep it under 600 words and be encouraging.
    """
    return prompt

def call_openai_with_grounding(prompt: str, agent_name: str = "Health Coach") -> str:
    """Call OpenAI with web search grounding for health coaching"""
    try:
        # Check if OpenAI API key is available
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise Exception("OPENAI_API_KEY not found")
        
        # Check rate limiting
        if not token_bucket.can_make_request("gpt-4o", "health_coaching"):
            raise Exception("Rate limit exceeded")
        
        # Create response with web search grounding
        response = client.responses.create(
            model="gpt-4o",
            tools=[{"type": "web_search_preview"}],
            input=f"""You are a knowledgeable health and nutrition coach named {agent_name}. 
            Provide helpful, accurate, and motivating advice based on the user's health data. 
            Be encouraging but realistic in your recommendations.
            
            User request: {prompt}"""
        )
        
        # Set rate limit
        token_bucket.set_next_allowed("gpt-4o", 1, "health_coaching")
        
        return response.output_text if response.output_text else "No response generated"
        
    except Exception as e:
        logging.error(f"Error calling OpenAI with grounding: {str(e)}")
        return f"Error generating response: {str(e)}"

def get_user_data_for_period(db: Session, user_id: str, period: str, period_start: date) -> Dict[str, Any]:
    """Get user data for the specified period"""
    if period == "daily":
        period_end = period_start + timedelta(days=1)
    elif period == "weekly":
        period_end = period_start + timedelta(weeks=1)
    else:  # monthly
        period_end = period_start + timedelta(days=30)
    
    # Get weight data
    weight_logs = db.query(models.WeightLog).filter(
        models.WeightLog.user_id == user_id,
        models.WeightLog.logged_at >= period_start,
        models.WeightLog.logged_at < period_end
    ).all()
    
    # Get food data
    food_logs = db.query(models.FoodLog).filter(
        models.FoodLog.user_id == user_id,
        models.FoodLog.logged_at >= period_start,
        models.FoodLog.logged_at < period_end
    ).all()
    
    # Get HR data
    hr_sessions = db.query(models.HRSession).filter(
        models.HRSession.user_id == user_id,
        models.HRSession.started_at >= period_start,
        models.HRSession.started_at < period_end
    ).all()
    
    # Process data
    food_data = [
        {
            "calories": f.calories or 0,
            "protein_g": f.protein_g or 0,
            "fat_g": f.fat_g or 0,
            "carbs_g": f.carbs_g or 0
        } for f in food_logs
    ]
    
    hr_data = [
        {
            "avg_bpm": h.avg_bpm or 0,
            "min_bpm": h.min_bpm or 0,
            "max_bpm": h.max_bpm or 0
        } for h in hr_sessions
    ]
    
    return {
        "weight": weight_logs[-1].kg if weight_logs else None,
        "weight_trend": [w.kg for w in weight_logs] if weight_logs else [],
        "food": food_data,
        "hr_sessions": hr_data,
        "avg_calories": sum(f["calories"] for f in food_data) / len(food_data) if food_data else 0,
        "avg_protein": sum(f["protein_g"] for f in food_data) / len(food_data) if food_data else 0,
        "avg_fat": sum(f["fat_g"] for f in food_data) / len(food_data) if food_data else 0,
        "avg_carbs": sum(f["carbs_g"] for f in food_data) / len(food_data) if food_data else 0,
        "avg_hr": sum(h["avg_bpm"] for h in hr_data) / len(hr_data) if hr_data else None,
    }

@celery_app.task
def generate_daily_insight(user_id: str, target_date: str):
    """Generate daily insight for a user"""
    db = next(get_db())
    try:
        target_date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
        existing = crud.get_ai_insight(db, user_id, "daily", target_date_obj)
        if existing:
            return {"status": "already_exists"}
        user_data = get_user_data_for_period(db, user_id, "daily", target_date_obj)
        prompt = build_daily_prompt(user_data)
        insight_md = call_openai_with_grounding(prompt, "Daily Health Coach")
        crud.create_ai_insight(db, user_id, "daily", target_date_obj, insight_md)
        return {"status": "success", "insight": insight_md}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@celery_app.task
def generate_weekly_insight(user_id: str, week_start: str):
    """Generate weekly insight for a user"""
    db = next(get_db())
    try:
        week_start_obj = datetime.strptime(week_start, "%Y-%m-%d").date()
        existing = crud.get_ai_insight(db, user_id, "weekly", week_start_obj)
        if existing:
            return {"status": "already_exists"}
        user_data = get_user_data_for_period(db, user_id, "weekly", week_start_obj)
        prompt = build_weekly_prompt(user_data)
        insight_md = call_openai_with_grounding(prompt, "Weekly Health Coach")
        crud.create_ai_insight(db, user_id, "weekly", week_start_obj, insight_md)
        return {"status": "success", "insight": insight_md}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@celery_app.task
def generate_monthly_insight(user_id: str, month_start: str):
    """Generate monthly insight for a user"""
    db = next(get_db())
    try:
        month_start_obj = datetime.strptime(month_start, "%Y-%m-%d").date()
        existing = crud.get_ai_insight(db, user_id, "monthly", month_start_obj)
        if existing:
            return {"status": "already_exists"}
        user_data = get_user_data_for_period(db, user_id, "monthly", month_start_obj)
        prompt = build_monthly_prompt(user_data)
        insight_md = call_openai_with_grounding(prompt, "Monthly Health Coach")
        crud.create_ai_insight(db, user_id, "monthly", month_start_obj, insight_md)
        return {"status": "success", "insight": insight_md}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@celery_app.task
def generate_realtime_coach(user_id: str) -> str:
    """Generate real-time coaching advice"""
    db = next(get_db())
    try:
        today = date.today()
        user_data = get_user_data_for_period(db, user_id, "daily", today)
        prompt = f"""
        You are a real-time health coach. Based on today's data so far, provide 2-3 quick, actionable tips.
        Today's data:
        - Weight: {user_data.get('weight', 'No data')} kg
        - Calories so far: {user_data.get('avg_calories', 0)} kcal
        - Protein: {user_data.get('avg_protein', 0)}g
        - HR sessions: {len(user_data.get('hr_sessions', []))}
        Provide 2-3 specific, actionable tips for the rest of the day. Keep it under 100 words.
        """
        return call_openai_with_grounding(prompt, "Real-time Health Coach")
    except Exception as e:
        return f"Unable to generate coaching advice: {str(e)}"
    finally:
        db.close()

# Scheduled tasks
@celery_app.task
def nightly_daily_insights():
    """Generate daily insights for all active users at 00:05"""
    db = next(get_db())
    try:
        yesterday = date.today() - timedelta(days=1)
        active_users = db.query(models.User).all()
        
        for user in active_users:
            generate_daily_insight.delay(str(user.id), yesterday.strftime("%Y-%m-%d"))
        
        return {"status": "scheduled", "users": len(active_users)}
    finally:
        db.close()

@celery_app.task
def weekly_insights():
    """Generate weekly insights every Monday at 01:00"""
    db = next(get_db())
    try:
        # Get last Monday
        today = date.today()
        days_since_monday = today.weekday()
        last_monday = today - timedelta(days=days_since_monday)
        
        active_users = db.query(models.User).all()
        
        for user in active_users:
            generate_weekly_insight.delay(str(user.id), last_monday.strftime("%Y-%m-%d"))
        
        return {"status": "scheduled", "users": len(active_users)}
    finally:
        db.close()

@celery_app.task
def monthly_insights():
    """Generate monthly insights on the 1st of each month at 02:00"""
    db = next(get_db())
    try:
        # Get first day of current month
        today = date.today()
        first_of_month = today.replace(day=1)
        
        active_users = db.query(models.User).all()
        
        for user in active_users:
            generate_monthly_insight.delay(str(user.id), first_of_month.strftime("%Y-%m-%d"))
        
        return {"status": "scheduled", "users": len(active_users)}
    finally:
        db.close()
