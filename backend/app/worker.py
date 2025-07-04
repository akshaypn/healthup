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
    """Build comprehensive prompt for daily insights"""
    prompt = f"""
    You are a personal health coach analyzing daily health data. Provide a concise, motivating summary and actionable next steps.
    
    **DAILY HEALTH SUMMARY FOR {user_data.get('period_start', 'Today')}**
    
    **Weight & Body Metrics:**
    - Current Weight: {user_data.get('weight', 'No data')} kg
    - Weight Change: {user_data.get('weight_change', 0):.1f} kg
    - Weight Entries: {user_data.get('weight_entries', 0)} logged today
    
    **Nutrition & Food:**
    - Total Calories: {user_data.get('total_calories', 0):.0f} kcal
    - Protein: {user_data.get('total_protein', 0):.1f}g
    - Fat: {user_data.get('total_fat', 0):.1f}g
    - Carbs: {user_data.get('total_carbs', 0):.1f}g
    - Fiber: {user_data.get('total_fiber', 0):.1f}g
    - Food Entries: {user_data.get('food_entries', 0)} meals logged
    - Average Meal Health Score: {user_data.get('avg_health_score', 0):.1f}/100
    - Meal Distribution: {user_data.get('meal_types', {})}
    
    **Activity & Fitness:**
    - Steps: {user_data.get('total_steps', 0):,} steps
    - Calories Burned: {user_data.get('total_calories_burned', 0):.0f} kcal
    - Active Minutes: {user_data.get('total_active_minutes', 0)} minutes
    - Distance: {user_data.get('total_distance', 0):.1f} km
    
    **Heart Rate:**
    - Average HR: {user_data.get('avg_hr', 0):.0f} bpm
    - HR Range: {user_data.get('min_hr', 0):.0f} - {user_data.get('max_hr', 0):.0f} bpm
    - HR Sessions: {user_data.get('hr_entries', 0)} logged
    
    **Sleep:**
    - Sleep Hours: {user_data.get('avg_sleep_hours', 0):.1f} hours
    - Sleep Entries: {user_data.get('sleep_entries', 0)} days with data
    
    **Consistency Score: {user_data.get('overall_consistency', 0):.1f}%**
    
    **TASK:** Provide a markdown response with:
    1. **Daily Summary** - Brief overview of the day's health metrics
    2. **Key Highlights** - What went well today
    3. **Areas for Improvement** - What could be better
    4. **Tomorrow's Action Plan** - 2-3 specific, actionable next steps
    5. **Motivational Note** - Encouraging message
    
    Keep it under 300 words, be encouraging but realistic, and provide specific, actionable advice.
    Focus on the most important metrics and trends for daily insights.
    """
    return prompt

def build_weekly_prompt(user_data: Dict[str, Any]) -> str:
    """Build comprehensive prompt for weekly insights"""
    prompt = f"""
    You are a personal health coach analyzing weekly health trends. Provide a comprehensive weekly report with insights and recommendations.
    
    **WEEKLY HEALTH SUMMARY ({user_data.get('period_days', 7)} days)**
    
    **Weight Trends:**
    - Starting Weight: {user_data.get('weight_trend', [])[0] if user_data.get('weight_trend') else 'No data'} kg
    - Ending Weight: {user_data.get('weight', 'No data')} kg
    - Weekly Change: {user_data.get('weight_change', 0):.1f} kg
    - Weight Entries: {user_data.get('weight_entries', 0)} logged this week
    
    **Nutrition Trends:**
    - Average Daily Calories: {user_data.get('avg_daily_calories', 0):.0f} kcal
    - Average Daily Protein: {user_data.get('avg_daily_protein', 0):.1f}g
    - Average Daily Fat: {user_data.get('avg_daily_fat', 0):.1f}g
    - Average Daily Carbs: {user_data.get('avg_daily_carbs', 0):.1f}g
    - Average Daily Fiber: {user_data.get('avg_daily_fiber', 0):.1f}g
    - Total Food Entries: {user_data.get('food_entries', 0)} meals logged
    - Average Meal Health Score: {user_data.get('avg_health_score', 0):.1f}/100
    - Meal Distribution: {user_data.get('meal_types', {})}
    
    **Activity & Fitness Trends:**
    - Average Daily Steps: {user_data.get('avg_daily_steps', 0):.0f} steps
    - Total Weekly Steps: {user_data.get('total_steps', 0):,} steps
    - Average Daily Calories Burned: {user_data.get('avg_daily_calories_burned', 0):.0f} kcal
    - Average Daily Active Minutes: {user_data.get('avg_daily_active_minutes', 0):.0f} minutes
    - Total Distance: {user_data.get('total_distance', 0):.1f} km
    
    **Heart Rate Trends:**
    - Average HR: {user_data.get('avg_hr', 0):.0f} bpm
    - HR Range: {user_data.get('min_hr', 0):.0f} - {user_data.get('max_hr', 0):.0f} bpm
    - HR Sessions: {user_data.get('hr_entries', 0)} logged this week
    
    **Sleep Trends:**
    - Average Sleep: {user_data.get('avg_sleep_hours', 0):.1f} hours per night
    - Sleep Consistency: {user_data.get('sleep_entries', 0)} days with sleep data
    
    **Consistency Metrics:**
    - Food Logging: {user_data.get('food_consistency', 0):.1f}%
    - Weight Tracking: {user_data.get('weight_consistency', 0):.1f}%
    - Activity Tracking: {user_data.get('activity_consistency', 0):.1f}%
    - Overall Consistency: {user_data.get('overall_consistency', 0):.1f}%
    
    **TASK:** Provide a markdown response with:
    1. **Weekly Overview** - Summary of the week's health journey
    2. **Progress Highlights** - What went well this week
    3. **Trend Analysis** - Patterns and insights from the data
    4. **Areas for Improvement** - What could be better next week
    5. **Next Week's Goals** - 3-5 specific, actionable recommendations
    6. **Motivational Closing** - Encouraging message for the week ahead
    
    Keep it under 500 words, be encouraging but realistic, and provide specific, actionable advice.
    Focus on trends, patterns, and weekly progress rather than daily details.
    """
    return prompt

def build_monthly_prompt(user_data: Dict[str, Any]) -> str:
    """Build comprehensive prompt for monthly insights"""
    prompt = f"""
    You are a personal health coach analyzing monthly health progress. Provide a comprehensive monthly report with deep insights and strategic recommendations.
    
    **MONTHLY HEALTH SUMMARY ({user_data.get('period_days', 30)} days)**
    
    **Weight Progress:**
    - Starting Weight: {user_data.get('weight_trend', [])[0] if user_data.get('weight_trend') else 'No data'} kg
    - Current Weight: {user_data.get('weight', 'No data')} kg
    - Monthly Change: {user_data.get('weight_change', 0):.1f} kg
    - Weight Entries: {user_data.get('weight_entries', 0)} logged this month
    
    **Nutrition Analysis:**
    - Average Daily Calories: {user_data.get('avg_daily_calories', 0):.0f} kcal
    - Average Daily Protein: {user_data.get('avg_daily_protein', 0):.1f}g
    - Average Daily Fat: {user_data.get('avg_daily_fat', 0):.1f}g
    - Average Daily Carbs: {user_data.get('avg_daily_carbs', 0):.1f}g
    - Average Daily Fiber: {user_data.get('avg_daily_fiber', 0):.1f}g
    - Total Food Entries: {user_data.get('food_entries', 0)} meals logged
    - Average Meal Health Score: {user_data.get('avg_health_score', 0):.1f}/100
    - Meal Distribution: {user_data.get('meal_types', {})}
    
    **Activity & Fitness Progress:**
    - Average Daily Steps: {user_data.get('avg_daily_steps', 0):.0f} steps
    - Total Monthly Steps: {user_data.get('total_steps', 0):,} steps
    - Average Daily Calories Burned: {user_data.get('avg_daily_calories_burned', 0):.0f} kcal
    - Average Daily Active Minutes: {user_data.get('avg_daily_active_minutes', 0):.0f} minutes
    - Total Monthly Distance: {user_data.get('total_distance', 0):.1f} km
    
    **Heart Rate Analysis:**
    - Average HR: {user_data.get('avg_hr', 0):.0f} bpm
    - HR Range: {user_data.get('min_hr', 0):.0f} - {user_data.get('max_hr', 0):.0f} bpm
    - HR Sessions: {user_data.get('hr_entries', 0)} logged this month
    
    **Sleep Analysis:**
    - Average Sleep: {user_data.get('avg_sleep_hours', 0):.1f} hours per night
    - Sleep Consistency: {user_data.get('sleep_entries', 0)} days with sleep data
    
    **Consistency & Habits:**
    - Food Logging Consistency: {user_data.get('food_consistency', 0):.1f}%
    - Weight Tracking Consistency: {user_data.get('weight_consistency', 0):.1f}%
    - Activity Tracking Consistency: {user_data.get('activity_consistency', 0):.1f}%
    - Overall Consistency: {user_data.get('overall_consistency', 0):.1f}%
    
    **TASK:** Provide a markdown response with:
    1. **Monthly Overview** - Comprehensive summary of the month's health journey
    2. **Major Achievements** - Key accomplishments and milestones
    3. **Trend Analysis** - Deep insights into patterns and behaviors
    4. **Progress Toward Goals** - How well the month aligned with health objectives
    5. **Strategic Recommendations** - 5-7 specific recommendations for next month
    6. **Long-term Health Strategy** - Suggestions for sustainable health habits
    7. **Motivational Closing** - Encouraging message for continued progress
    
    Keep it under 700 words, be encouraging but realistic, and provide strategic, actionable advice.
    Focus on long-term trends, habit formation, and sustainable health improvements.
    """
    return prompt

def call_openai_with_grounding(prompt: str, agent_name: str = "Health Coach") -> str:
    """Call OpenAI with web search grounding for health coaching"""
    try:
        print(f"Starting OpenAI call for {agent_name}")
        
        # Check if OpenAI API key is available
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise Exception("OPENAI_API_KEY not found")
        
        print(f"OpenAI API key found: {api_key[:10]}...")
        
        # Check rate limiting
        if not token_bucket.can_make_request("gpt-4o", "health_coaching"):
            raise Exception("Rate limit exceeded")
        
        print("Rate limit check passed")
        
        # Create response with web search grounding
        print("Making OpenAI API call...")
        response = client.responses.create(
            model="gpt-4o",
            tools=[{"type": "web_search_preview"}],
            input=f"""You are a knowledgeable health and nutrition coach named {agent_name}. 
            Provide helpful, accurate, and motivating advice based on the user's health data. 
            Be encouraging but realistic in your recommendations.
            
            User request: {prompt}"""
        )
        
        print("OpenAI API call completed")
        
        # Set rate limit
        token_bucket.set_next_allowed("gpt-4o", 1, "health_coaching")
        
        result = response.output_text if response.output_text else "No response generated"
        print(f"OpenAI response length: {len(result)} characters")
        
        return result
        
    except Exception as e:
        print(f"Error calling OpenAI with grounding: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"Error generating response: {str(e)}"

def get_user_data_for_period(db: Session, user_id: str, period: str, period_start: date) -> Dict[str, Any]:
    """Get comprehensive user data for the specified period"""
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
    ).order_by(models.WeightLog.logged_at).all()
    
    # Get food data with analysis
    food_logs = db.query(models.FoodLog).filter(
        models.FoodLog.user_id == user_id,
        models.FoodLog.logged_at >= period_start,
        models.FoodLog.logged_at < period_end
    ).order_by(models.FoodLog.logged_at).all()
    
    # Get food analysis data
    food_analyses = db.query(models.FoodLogAnalysis).join(models.FoodLog).filter(
        models.FoodLog.user_id == user_id,
        models.FoodLog.logged_at >= period_start,
        models.FoodLog.logged_at < period_end
    ).all()
    
    # Get HR data
    hr_sessions = db.query(models.HRSession).filter(
        models.HRSession.user_id == user_id,
        models.HRSession.logged_at >= period_start,
        models.HRSession.logged_at < period_end
    ).order_by(models.HRSession.logged_at).all()
    
    # Get activity data (steps, sleep, etc.)
    activity_data = db.query(models.ActivityData).filter(
        models.ActivityData.user_id == user_id,
        models.ActivityData.date >= period_start,
        models.ActivityData.date < period_end
    ).order_by(models.ActivityData.date).all()
    
    # Get steps data
    steps_data = db.query(models.StepsData).filter(
        models.StepsData.user_id == user_id,
        models.StepsData.date >= period_start,
        models.StepsData.date < period_end
    ).order_by(models.StepsData.date).all()
    
    # Process weight data
    weight_trend = [w.kg for w in weight_logs] if weight_logs else []
    latest_weight = weight_logs[-1].kg if weight_logs else None
    weight_change = weight_logs[-1].kg - weight_logs[0].kg if len(weight_logs) > 1 else 0
    
    # Process food data
    food_data = []
    total_calories = 0
    total_protein = 0
    total_fat = 0
    total_carbs = 0
    total_fiber = 0
    meal_types = {}
    
    for f in food_logs:
        calories = f.calories or 0
        protein = f.protein_g or 0
        fat = f.fat_g or 0
        carbs = f.carbs_g or 0
        fiber = f.fiber_g or 0
        
        total_calories += calories
        total_protein += protein
        total_fat += fat
        total_carbs += carbs
        total_fiber += fiber
        
        meal_type = f.meal_type or 'snack'
        meal_types[meal_type] = meal_types.get(meal_type, 0) + 1
        
        food_data.append({
            "description": f.description,
            "calories": calories,
            "protein_g": protein,
            "fat_g": fat,
            "carbs_g": carbs,
            "fiber_g": fiber,
            "meal_type": meal_type,
            "logged_at": f.logged_at
        })
    
    # Process food analysis
    avg_health_score = 0
    if food_analyses:
        avg_health_score = sum(a.health_score or 0 for a in food_analyses) / len(food_analyses)
    
    # Process HR data
    hr_data = []
    avg_hr = 0
    min_hr = 0
    max_hr = 0
    
    if hr_sessions:
        for h in hr_sessions:
            hr_data.append({
                "avg_bpm": h.avg_hr or 0,
                "min_bpm": h.min_hr or 0,
                "max_bpm": h.max_hr or 0,
                "duration_minutes": h.duration_minutes or 0,
                "logged_at": h.logged_at
            })
        
        avg_hr = sum(h["avg_bpm"] for h in hr_data) / len(hr_data)
        min_hr = min(h["min_bpm"] for h in hr_data)
        max_hr = max(h["max_bpm"] for h in hr_data)
    
    # Process activity data
    total_steps = 0
    total_calories_burned = 0
    total_active_minutes = 0
    total_distance = 0
    sleep_data = []
    
    for a in activity_data:
        total_steps += a.steps or 0
        total_calories_burned += a.calories_burned or 0
        total_active_minutes += a.active_minutes or 0
        total_distance += a.distance_km or 0
        
        if a.sleep_hours:
            sleep_data.append({
                "date": a.date,
                "total_hours": a.sleep_hours,
                "deep_hours": a.deep_sleep_hours or 0,
                "light_hours": a.light_sleep_hours or 0,
                "rem_hours": a.rem_sleep_hours or 0,
                "awake_hours": a.awake_hours or 0,
                "sleep_score": a.sleep_score
            })
    
    # Calculate averages
    days_in_period = (period_end - period_start).days
    avg_daily_calories = total_calories / days_in_period if days_in_period > 0 else 0
    avg_daily_protein = total_protein / days_in_period if days_in_period > 0 else 0
    avg_daily_fat = total_fat / days_in_period if days_in_period > 0 else 0
    avg_daily_carbs = total_carbs / days_in_period if days_in_period > 0 else 0
    avg_daily_fiber = total_fiber / days_in_period if days_in_period > 0 else 0
    avg_daily_steps = total_steps / days_in_period if days_in_period > 0 else 0
    avg_daily_calories_burned = total_calories_burned / days_in_period if days_in_period > 0 else 0
    avg_daily_active_minutes = total_active_minutes / days_in_period if days_in_period > 0 else 0
    avg_sleep_hours = sum(s["total_hours"] for s in sleep_data) / len(sleep_data) if sleep_data else 0
    
    # Calculate consistency metrics
    days_with_food = len(set(f.logged_at.date() for f in food_logs))
    days_with_weight = len(set(w.logged_at.date() for w in weight_logs))
    days_with_activity = len(activity_data)
    food_consistency = (days_with_food / days_in_period * 100) if days_in_period > 0 else 0
    weight_consistency = (days_with_weight / days_in_period * 100) if days_in_period > 0 else 0
    activity_consistency = (days_with_activity / days_in_period * 100) if days_in_period > 0 else 0
    
    return {
        # Weight data
        "weight": latest_weight,
        "weight_trend": weight_trend,
        "weight_change": weight_change,
        "weight_entries": len(weight_logs),
        
        # Food data
        "food": food_data,
        "food_entries": len(food_logs),
        "total_calories": total_calories,
        "total_protein": total_protein,
        "total_fat": total_fat,
        "total_carbs": total_carbs,
        "total_fiber": total_fiber,
        "avg_daily_calories": avg_daily_calories,
        "avg_daily_protein": avg_daily_protein,
        "avg_daily_fat": avg_daily_fat,
        "avg_daily_carbs": avg_daily_carbs,
        "avg_daily_fiber": avg_daily_fiber,
        "meal_types": meal_types,
        "avg_health_score": avg_health_score,
        
        # Heart rate data
        "hr_sessions": hr_data,
        "hr_entries": len(hr_sessions),
        "avg_hr": avg_hr,
        "min_hr": min_hr,
        "max_hr": max_hr,
        
        # Activity data
        "activity_data": activity_data,
        "steps_data": steps_data,
        "total_steps": total_steps,
        "total_calories_burned": total_calories_burned,
        "total_active_minutes": total_active_minutes,
        "total_distance": total_distance,
        "avg_daily_steps": avg_daily_steps,
        "avg_daily_calories_burned": avg_daily_calories_burned,
        "avg_daily_active_minutes": avg_daily_active_minutes,
        
        # Sleep data
        "sleep_data": sleep_data,
        "avg_sleep_hours": avg_sleep_hours,
        "sleep_entries": len(sleep_data),
        
        # Consistency metrics
        "food_consistency": food_consistency,
        "weight_consistency": weight_consistency,
        "activity_consistency": activity_consistency,
        "overall_consistency": (food_consistency + weight_consistency + activity_consistency) / 3,
        
        # Period info
        "period_days": days_in_period,
        "period_start": period_start,
        "period_end": period_end
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
