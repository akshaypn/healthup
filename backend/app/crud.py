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
    """Get food logs with analysis for a user"""
    logs = db.query(models.FoodLog).filter(
        models.FoodLog.user_id == user_id
    ).order_by(models.FoodLog.logged_at.desc()).limit(limit).all()
    
    result = []
    for log in logs:
        analysis = get_food_log_analysis(db, log.id, user_id)
        result.append({
            'food_log': log,
            'analysis': analysis
        })
    
    return result

# Amazfit Integration CRUD Functions
def create_amazfit_credentials(db: Session, user_id: str, credentials: schemas.AmazfitCredentialsCreate):
    """Create or update Amazfit credentials for a user"""
    existing = db.query(models.AmazfitCredentials).filter(
        models.AmazfitCredentials.user_id == user_id
    ).first()
    
    if existing:
        # Update existing credentials
        existing.app_token = credentials.app_token
        existing.user_id_amazfit = credentials.user_id_amazfit
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new credentials
        db_credentials = models.AmazfitCredentials(
            user_id=user_id,
            app_token=credentials.app_token,
            user_id_amazfit=credentials.user_id_amazfit
        )
        db.add(db_credentials)
        db.commit()
        db.refresh(db_credentials)
        return db_credentials

def get_amazfit_credentials(db: Session, user_id: str):
    """Get Amazfit credentials for a user"""
    return db.query(models.AmazfitCredentials).filter(
        models.AmazfitCredentials.user_id == user_id
    ).first()

def delete_amazfit_credentials(db: Session, user_id: str):
    """Delete Amazfit credentials for a user"""
    credentials = db.query(models.AmazfitCredentials).filter(
        models.AmazfitCredentials.user_id == user_id
    ).first()
    
    if credentials:
        db.delete(credentials)
        db.commit()
        return True
    return False

def create_activity_data(db: Session, user_id: str, activity: schemas.ActivityDataCreate):
    """Create or update activity data"""
    existing = db.query(models.ActivityData).filter(
        models.ActivityData.user_id == user_id,
        models.ActivityData.date == activity.date
    ).first()
    
    if existing:
        # Update existing record
        for field, value in activity.dict(exclude_unset=True).items():
            setattr(existing, field, value)
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new record
        db_activity = models.ActivityData(
            user_id=user_id,
            **activity.dict()
        )
        db.add(db_activity)
        db.commit()
        db.refresh(db_activity)
        return db_activity

def get_activity_data(db: Session, user_id: str, start_date: date = None, end_date: date = None):
    """Get activity data for a user within date range"""
    query = db.query(models.ActivityData).filter(models.ActivityData.user_id == user_id)
    
    if start_date:
        query = query.filter(models.ActivityData.date >= start_date)
    if end_date:
        query = query.filter(models.ActivityData.date <= end_date)
    
    return query.order_by(models.ActivityData.date.desc()).all()

def get_recent_activity_data(db: Session, user_id: str, limit: int = 7):
    """Get recent activity data for a user"""
    return db.query(models.ActivityData).filter(
        models.ActivityData.user_id == user_id
    ).order_by(models.ActivityData.date.desc()).limit(limit).all()

def create_steps_data(db: Session, user_id: str, steps: schemas.StepsDataCreate):
    """Create or update steps data"""
    existing = db.query(models.StepsData).filter(
        models.StepsData.user_id == user_id,
        models.StepsData.date == steps.date
    ).first()
    
    if existing:
        # Update existing record
        for field, value in steps.dict(exclude_unset=True).items():
            setattr(existing, field, value)
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new record
        db_steps = models.StepsData(
            user_id=user_id,
            **steps.dict()
        )
        db.add(db_steps)
        db.commit()
        db.refresh(db_steps)
        return db_steps

def get_steps_data(db: Session, user_id: str, start_date: date = None, end_date: date = None):
    """Get steps data for a user within date range"""
    query = db.query(models.StepsData).filter(models.StepsData.user_id == user_id)
    
    if start_date:
        query = query.filter(models.StepsData.date >= start_date)
    if end_date:
        query = query.filter(models.StepsData.date <= end_date)
    
    return query.order_by(models.StepsData.date.desc()).all()

def get_recent_steps_data(db: Session, user_id: str, limit: int = 7):
    """Get recent steps data for a user"""
    return db.query(models.StepsData).filter(
        models.StepsData.user_id == user_id
    ).order_by(models.StepsData.date.desc()).limit(limit).all()

def get_today_activity_summary(db: Session, user_id: str):
    """Get today's activity summary for dashboard"""
    today = date.today()
    
    # Get today's activity data
    activity = db.query(models.ActivityData).filter(
        models.ActivityData.user_id == user_id,
        models.ActivityData.date == today
    ).first()
    
    # Get today's steps data
    steps = db.query(models.StepsData).filter(
        models.StepsData.user_id == user_id,
        models.StepsData.date == today
    ).first()
    
    return {
        'activity': activity,
        'steps': steps,
        'total_calories_burned': (activity.calories_burned if activity else 0) + (steps.calories_burned if steps else 0),
        'total_steps': steps.total_steps if steps else 0,
        'active_minutes': activity.active_minutes if activity else 0,
        'sleep_hours': activity.sleep_hours if activity else 0
    }

# User Profile CRUD
def create_user_profile(db: Session, user_id: str, profile_data: dict):
    """Create or update user profile"""
    existing_profile = db.query(models.UserProfile).filter(
        models.UserProfile.user_id == user_id
    ).first()
    
    if existing_profile:
        # Update existing profile
        for key, value in profile_data.items():
            setattr(existing_profile, key, value)
        existing_profile.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing_profile)
        return existing_profile
    else:
        # Create new profile
        db_profile = models.UserProfile(user_id=user_id, **profile_data)
        db.add(db_profile)
        db.commit()
        db.refresh(db_profile)
        return db_profile

def get_user_profile(db: Session, user_id: str):
    """Get user profile"""
    return db.query(models.UserProfile).filter(
        models.UserProfile.user_id == user_id
    ).first()

def calculate_nutritional_requirements(profile: models.UserProfile):
    """Calculate daily nutritional requirements based on user profile"""
    # Convert decimal values to float for calculations
    weight_kg = float(profile.weight_kg)
    height_cm = float(profile.height_cm)
    age = int(profile.age)
    
    # Basic BMR calculation using Mifflin-St Jeor Equation
    if profile.gender.lower() == 'male':
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    
    # Activity multipliers
    activity_multipliers = {
        'sedentary': 1.2,
        'lightly_active': 1.375,
        'moderately_active': 1.55,
        'very_active': 1.725,
        'extremely_active': 1.9
    }
    
    tdee = bmr * activity_multipliers.get(profile.activity_level, 1.2)
    
    # Goal adjustments
    if profile.goal == 'lose_weight':
        tdee *= 0.85  # 15% deficit
    elif profile.goal == 'gain_weight':
        tdee *= 1.15  # 15% surplus
    
    # Macronutrient distribution
    protein_g = weight_kg * 2.2  # 2.2g per kg body weight
    fat_g = (tdee * 0.25) / 9  # 25% of calories from fat
    carbs_g = (tdee - (protein_g * 4) - (fat_g * 9)) / 4  # Remaining calories from carbs
    
    # Micronutrient requirements (simplified)
    requirements = {
        'calories': {'target': tdee, 'unit': 'kcal'},
        'protein_g': {'target': protein_g, 'unit': 'g'},
        'fat_g': {'target': fat_g, 'unit': 'g'},
        'carbs_g': {'target': carbs_g, 'unit': 'g'},
        'fiber_g': {'target': 25, 'unit': 'g'},
        'sugar_g': {'target': 50, 'unit': 'g'},
        'sodium_mg': {'target': 2300, 'unit': 'mg'},
        'vitamin_a_mcg': {'target': 900 if profile.gender.lower() == 'male' else 700, 'unit': 'μg'},
        'vitamin_c_mg': {'target': 90 if profile.gender.lower() == 'male' else 75, 'unit': 'mg'},
        'vitamin_d_mcg': {'target': 15, 'unit': 'μg'},
        'vitamin_e_mg': {'target': 15, 'unit': 'mg'},
        'vitamin_k_mcg': {'target': 120 if profile.gender.lower() == 'male' else 90, 'unit': 'μg'},
        'vitamin_b1_mg': {'target': 1.2 if profile.gender.lower() == 'male' else 1.1, 'unit': 'mg'},
        'vitamin_b2_mg': {'target': 1.3 if profile.gender.lower() == 'male' else 1.1, 'unit': 'mg'},
        'vitamin_b3_mg': {'target': 16 if profile.gender.lower() == 'male' else 14, 'unit': 'mg'},
        'vitamin_b5_mg': {'target': 5, 'unit': 'mg'},
        'vitamin_b6_mg': {'target': 1.3 if profile.gender.lower() == 'male' else 1.3, 'unit': 'mg'},
        'vitamin_b7_mcg': {'target': 30, 'unit': 'μg'},
        'vitamin_b9_mcg': {'target': 400, 'unit': 'μg'},
        'vitamin_b12_mcg': {'target': 2.4, 'unit': 'μg'},
        'calcium_mg': {'target': 1000, 'unit': 'mg'},
        'iron_mg': {'target': 8 if profile.gender.lower() == 'male' else 18, 'unit': 'mg'},
        'magnesium_mg': {'target': 400 if profile.gender.lower() == 'male' else 310, 'unit': 'mg'},
        'phosphorus_mg': {'target': 700, 'unit': 'mg'},
        'potassium_mg': {'target': 3400 if profile.gender.lower() == 'male' else 2600, 'unit': 'mg'},
        'zinc_mg': {'target': 11 if profile.gender.lower() == 'male' else 8, 'unit': 'mg'},
        'copper_mg': {'target': 0.9, 'unit': 'mg'},
        'manganese_mg': {'target': 2.3 if profile.gender.lower() == 'male' else 1.8, 'unit': 'mg'},
        'selenium_mcg': {'target': 55, 'unit': 'μg'},
        'chromium_mcg': {'target': 35 if profile.gender.lower() == 'male' else 25, 'unit': 'μg'},
        'molybdenum_mcg': {'target': 45, 'unit': 'μg'},
    }
    
    return requirements

def get_food_logs_by_period(db: Session, user_id: str, period: str, start_date: datetime, end_date: datetime):
    """Get food logs for a specific period"""
    return db.query(models.FoodLog).filter(
        models.FoodLog.user_id == user_id,
        models.FoodLog.logged_at >= start_date,
        models.FoodLog.logged_at <= end_date
    ).order_by(models.FoodLog.logged_at.desc()).all()

def calculate_nutritional_summary(db: Session, user_id: str, period: str, start_date: datetime, end_date: datetime):
    """Calculate nutritional summary for a period"""
    profile = get_user_profile(db, user_id)
    if not profile:
        return None
    
    requirements = calculate_nutritional_requirements(profile)
    food_logs = get_food_logs_by_period(db, user_id, period, start_date, end_date)
    
    # Calculate consumed nutrients
    consumed = {
        'calories': 0,
        'protein_g': 0,
        'fat_g': 0,
        'carbs_g': 0,
        'fiber_g': 0,
        'sugar_g': 0,
        'sodium_mg': 0,
        'vitamin_a_mcg': 0,
        'vitamin_c_mg': 0,
        'vitamin_d_mcg': 0,
        'vitamin_e_mg': 0,
        'vitamin_k_mcg': 0,
        'vitamin_b1_mg': 0,
        'vitamin_b2_mg': 0,
        'vitamin_b3_mg': 0,
        'vitamin_b5_mg': 0,
        'vitamin_b6_mg': 0,
        'vitamin_b7_mcg': 0,
        'vitamin_b9_mcg': 0,
        'vitamin_b12_mcg': 0,
        'calcium_mg': 0,
        'iron_mg': 0,
        'magnesium_mg': 0,
        'phosphorus_mg': 0,
        'potassium_mg': 0,
        'zinc_mg': 0,
        'copper_mg': 0,
        'manganese_mg': 0,
        'selenium_mcg': 0,
        'chromium_mcg': 0,
        'molybdenum_mcg': 0,
    }
    
    for log in food_logs:
        for nutrient in consumed:
            if hasattr(log, nutrient) and getattr(log, nutrient) is not None:
                consumed[nutrient] += float(getattr(log, nutrient))
    
    # Calculate requirements and status
    nutritional_requirements = []
    for nutrient, data in requirements.items():
        target = data['target']
        consumed_val = consumed.get(nutrient, 0)
        remaining = target - consumed_val
        percentage = (consumed_val / target * 100) if target > 0 else 0
        
        # Determine status
        if percentage < 80:
            status = 'under'
        elif percentage > 120:
            status = 'over'
        else:
            status = 'adequate'
        
        nutritional_requirements.append(schemas.NutritionalRequirement(
            nutrient=nutrient,
            daily_target=target,
            unit=data['unit'],
            consumed=consumed_val,
            remaining=remaining,
            percentage=percentage,
            status=status
        ))
    
    # Calculate period multiplier for requirements
    period_multipliers = {'daily': 1, 'weekly': 7, 'monthly': 30}
    multiplier = period_multipliers.get(period, 1)
    
    # Adjust targets for period
    for req in nutritional_requirements:
        req.daily_target *= multiplier
    
    return schemas.NutritionalSummary(
        period=period,
        period_start=start_date.isoformat(),
        period_end=end_date.isoformat(),
        total_calories=consumed['calories'],
        total_protein=consumed['protein_g'],
        total_fat=consumed['fat_g'],
        total_carbs=consumed['carbs_g'],
        requirements=nutritional_requirements,
        summary={
            'total_food_items': len(food_logs),
            'average_calories_per_day': consumed['calories'] / multiplier if multiplier > 0 else 0,
            'completion_rate': sum(1 for r in nutritional_requirements if r.status == 'adequate') / len(nutritional_requirements) * 100
        }
    )
