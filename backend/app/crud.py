from sqlalchemy.orm import Session
from . import models, schemas
from datetime import datetime, date, timedelta
from typing import List, Optional
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_user_by_email(db: Session, email: str):
    """Get user by email"""
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    """Create a new user"""
    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(email=user.email, password_hash=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_weight_log(db: Session, user_id, log: schemas.WeightLogCreate):
    db_log = models.WeightLog(user_id=user_id, kg=log.kg)
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

def get_weight_logs(db: Session, user_id):
    """Get all weight logs for a user"""
    return db.query(models.WeightLog).filter(models.WeightLog.user_id == user_id).order_by(models.WeightLog.logged_at.desc()).all()

def get_recent_weight_logs(db: Session, user_id, limit: int = 10):
    """Get recent weight logs for a user"""
    return db.query(models.WeightLog).filter(models.WeightLog.user_id == user_id).order_by(models.WeightLog.logged_at.desc()).limit(limit).all()

def create_food_log(db: Session, user_id, log: schemas.FoodLogCreate):
    """Create a comprehensive food log with all nutritional data"""
    # Convert schema to dict, excluding None values
    log_data = log.dict(exclude_unset=True)
    
    # Set default logged_at if not provided
    if 'logged_at' not in log_data:
        log_data['logged_at'] = datetime.utcnow()
    
    db_log = models.FoodLog(user_id=user_id, **log_data)
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

def get_food_logs(db: Session, user_id):
    """Get all food logs for a user"""
    return db.query(models.FoodLog).filter(models.FoodLog.user_id == user_id).order_by(models.FoodLog.logged_at.desc()).all()

def get_recent_food_logs(db: Session, user_id, limit: int = 10):
    """Get recent food logs for a user"""
    return db.query(models.FoodLog).filter(models.FoodLog.user_id == user_id).order_by(models.FoodLog.logged_at.desc()).limit(limit).all()

def get_food_logs_by_date_range(db: Session, user_id, start_date: date, end_date: date):
    """Get food logs within a date range"""
    return db.query(models.FoodLog).filter(
        models.FoodLog.user_id == user_id,
        models.FoodLog.logged_at >= start_date,
        models.FoodLog.logged_at < end_date + timedelta(days=1)
    ).order_by(models.FoodLog.logged_at.desc()).all()

def get_todays_food_logs(db: Session, user_id):
    """Get today's food logs for a user"""
    today = date.today()
    return get_food_logs_by_date_range(db, user_id, today, today)

def update_food_log(db: Session, food_log_id: int, user_id: str, updates: dict):
    """Update a food log"""
    db_log = db.query(models.FoodLog).filter(
        models.FoodLog.id == food_log_id,
        models.FoodLog.user_id == user_id
    ).first()
    
    if not db_log:
        return None
    
    # Update only provided fields
    for field, value in updates.items():
        if hasattr(db_log, field):
            setattr(db_log, field, value)
    
    db.commit()
    db.refresh(db_log)
    return db_log

def delete_food_log(db: Session, food_log_id: int, user_id: str):
    """Delete a food log"""
    db_log = db.query(models.FoodLog).filter(
        models.FoodLog.id == food_log_id,
        models.FoodLog.user_id == user_id
    ).first()
    
    if not db_log:
        return False
    
    db.delete(db_log)
    db.commit()
    return True

def get_food_parsing_session(db: Session, session_id: str, user_id: str):
    """Get a food parsing session"""
    return db.query(models.FoodParsingSession).filter(
        models.FoodParsingSession.session_id == session_id,
        models.FoodParsingSession.user_id == user_id
    ).first()

def get_user_food_parsing_sessions(db: Session, user_id: str, limit: int = 10):
    """Get recent food parsing sessions for a user"""
    return db.query(models.FoodParsingSession).filter(
        models.FoodParsingSession.user_id == user_id
    ).order_by(models.FoodParsingSession.created_at.desc()).limit(limit).all()

def get_nutrition_summary(db: Session, user_id: str, start_date: date, end_date: date):
    """Get nutrition summary for a date range"""
    food_logs = get_food_logs_by_date_range(db, user_id, start_date, end_date)
    
    summary = {
        'total_calories': 0,
        'total_protein_g': 0.0,
        'total_fat_g': 0.0,
        'total_carbs_g': 0.0,
        'total_fiber_g': 0.0,
        'total_sugar_g': 0.0,
        'vitamins': {},
        'minerals': {},
        'meal_counts': {'breakfast': 0, 'lunch': 0, 'dinner': 0, 'snack': 0},
        'total_meals': len(food_logs)
    }
    
    # Vitamin and mineral fields
    vitamin_fields = [
        'vitamin_a_mcg', 'vitamin_c_mg', 'vitamin_d_mcg', 'vitamin_e_mg', 'vitamin_k_mcg',
        'vitamin_b1_mg', 'vitamin_b2_mg', 'vitamin_b3_mg', 'vitamin_b5_mg', 'vitamin_b6_mg',
        'vitamin_b7_mcg', 'vitamin_b9_mcg', 'vitamin_b12_mcg'
    ]
    
    mineral_fields = [
        'calcium_mg', 'iron_mg', 'magnesium_mg', 'phosphorus_mg', 'potassium_mg',
        'sodium_mg', 'zinc_mg', 'copper_mg', 'manganese_mg', 'selenium_mcg',
        'chromium_mcg', 'molybdenum_mcg'
    ]
    
    for log in food_logs:
        # Macronutrients
        if log.calories:
            summary['total_calories'] += log.calories
        if log.protein_g:
            summary['total_protein_g'] += float(log.protein_g)
        if log.fat_g:
            summary['total_fat_g'] += float(log.fat_g)
        if log.carbs_g:
            summary['total_carbs_g'] += float(log.carbs_g)
        if log.fiber_g:
            summary['total_fiber_g'] += float(log.fiber_g)
        if log.sugar_g:
            summary['total_sugar_g'] += float(log.sugar_g)
        
        # Vitamins
        for field in vitamin_fields:
            value = getattr(log, field)
            if value:
                if field not in summary['vitamins']:
                    summary['vitamins'][field] = 0.0
                summary['vitamins'][field] += float(value)
        
        # Minerals
        for field in mineral_fields:
            value = getattr(log, field)
            if value:
                if field not in summary['minerals']:
                    summary['minerals'][field] = 0.0
                summary['minerals'][field] += float(value)
        
        # Meal counts
        if log.meal_type and log.meal_type in summary['meal_counts']:
            summary['meal_counts'][log.meal_type] += 1
    
    return summary

def create_hr_session(db: Session, user_id, session: schemas.HRSessionCreate):
    """Create a heart rate session"""
    db_session = models.HRSession(
        user_id=user_id,
        avg_hr=session.avg_hr,
        max_hr=session.max_hr,
        min_hr=session.min_hr,
        duration_minutes=session.duration_minutes,
        session_data=session.session_data
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def get_hr_sessions(db: Session, user_id):
    """Get all HR sessions for a user"""
    return db.query(models.HRSession).filter(models.HRSession.user_id == user_id).order_by(models.HRSession.logged_at.desc()).all()

def get_recent_hr_sessions(db: Session, user_id, limit: int = 10):
    """Get recent HR sessions for a user"""
    return db.query(models.HRSession).filter(models.HRSession.user_id == user_id).order_by(models.HRSession.logged_at.desc()).limit(limit).all()

def create_ai_insight(db: Session, user_id, period: str, period_start: date, insight_md: str):
    """Create an AI insight"""
    db_insight = models.AIInsight(
        user_id=user_id,
        period=period,
        period_start=period_start,
        insight_md=insight_md
    )
    db.add(db_insight)
    db.commit()
    db.refresh(db_insight)
    return db_insight

def get_ai_insight(db: Session, user_id, period: str, period_start: date):
    """Get an AI insight for a specific period"""
    return db.query(models.AIInsight).filter(
        models.AIInsight.user_id == user_id,
        models.AIInsight.period == period,
        models.AIInsight.period_start == period_start
    ).first()

def get_recent_ai_insights(db: Session, user_id, limit: int = 10):
    """Get recent AI insights for a user"""
    return db.query(models.AIInsight).filter(
        models.AIInsight.user_id == user_id
    ).order_by(models.AIInsight.created_at.desc()).limit(limit).all()

# Food Log Analysis CRUD functions
def create_food_log_analysis(db: Session, user_id: str, analysis: schemas.FoodLogAnalysisCreate):
    """Create a food log analysis"""
    db_analysis = models.FoodLogAnalysis(
        user_id=user_id,
        food_log_id=analysis.food_log_id,
        health_score=analysis.health_score,
        protein_adequacy=analysis.protein_adequacy,
        fiber_content=analysis.fiber_content,
        vitamin_balance=analysis.vitamin_balance,
        mineral_balance=analysis.mineral_balance,
        recommendations=analysis.recommendations,
        analysis_text=analysis.analysis_text,
        model_used=analysis.model_used,
        confidence_score=analysis.confidence_score
    )
    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)
    return db_analysis

def get_food_log_analysis(db: Session, food_log_id: int, user_id: str):
    """Get analysis for a specific food log"""
    return db.query(models.FoodLogAnalysis).filter(
        models.FoodLogAnalysis.food_log_id == food_log_id,
        models.FoodLogAnalysis.user_id == user_id
    ).first()

def update_food_log_analysis(db: Session, analysis_id: int, user_id: str, updates: dict):
    """Update a food log analysis"""
    db_analysis = db.query(models.FoodLogAnalysis).filter(
        models.FoodLogAnalysis.id == analysis_id,
        models.FoodLogAnalysis.user_id == user_id
    ).first()
    
    if not db_analysis:
        return None
    
    # Update only provided fields
    for field, value in updates.items():
        if hasattr(db_analysis, field):
            setattr(db_analysis, field, value)
    
    db.commit()
    db.refresh(db_analysis)
    return db_analysis

def get_food_log_with_analysis(db: Session, food_log_id: int, user_id: str):
    """Get a food log with its analysis"""
    food_log = db.query(models.FoodLog).filter(
        models.FoodLog.id == food_log_id,
        models.FoodLog.user_id == user_id
    ).first()
    
    if not food_log:
        return None
    
    analysis = get_food_log_analysis(db, food_log_id, user_id)
    
    return {
        'food_log': food_log,
        'analysis': analysis
    }

def get_food_logs_with_analysis(db: Session, user_id: str, limit: int = 10):
    """Get food logs with their analyses"""
    food_logs = get_recent_food_logs(db, user_id, limit)
    
    result = []
    for food_log in food_logs:
        analysis = get_food_log_analysis(db, food_log.id, user_id)
        result.append({
            'food_log': food_log,
            'analysis': analysis
        })
    
    return result
