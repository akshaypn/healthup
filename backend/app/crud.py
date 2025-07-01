from sqlalchemy.orm import Session
from . import models, schemas
from datetime import datetime, date, timedelta

def create_weight_log(db: Session, user_id, log: schemas.WeightLogCreate):
    db_log = models.WeightLog(user_id=user_id, kg=log.kg)
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

def get_weight_logs(db: Session, user_id):
    """Get all weight logs for a user"""
    return db.query(models.WeightLog).filter(models.WeightLog.user_id == user_id).order_by(models.WeightLog.logged_at.desc()).all()

def get_recent_weight_logs(db: Session, user_id, limit: int = 7):
    """Get recent weight logs for a user"""
    return db.query(models.WeightLog).filter(models.WeightLog.user_id == user_id).order_by(models.WeightLog.logged_at.desc()).limit(limit).all()

def create_food_log(db: Session, user_id, log: schemas.FoodLogCreate):
    db_log = models.FoodLog(user_id=user_id, **log.dict())
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

def create_hr_log(db: Session, user_id, log: schemas.HRLogCreate):
    db_log = models.HRSession(user_id=user_id, avg_bpm=log.avg_bpm, min_bpm=log.min_bpm, max_bpm=log.max_bpm, raw_json=log.raw, started_at=datetime.utcnow(), ended_at=datetime.utcnow())
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

def get_hr_logs(db: Session, user_id):
    """Get all HR logs for a user"""
    return db.query(models.HRSession).filter(models.HRSession.user_id == user_id).order_by(models.HRSession.started_at.desc()).all()

def get_recent_hr_logs(db: Session, user_id, limit: int = 5):
    """Get recent HR logs for a user"""
    return db.query(models.HRSession).filter(models.HRSession.user_id == user_id).order_by(models.HRSession.started_at.desc()).limit(limit).all()

def get_ai_insight(db: Session, user_id, period: str, period_start: date = None):
    if period_start is None:
        today = date.today()
        if period == 'daily':
            period_start = today
        elif period == 'weekly':
            period_start = today - timedelta(days=today.weekday())
        elif period == 'monthly':
            period_start = today.replace(day=1)
        else:
            return None
    return db.query(models.AIInsight).filter_by(user_id=user_id, period=period, period_start=period_start).first()

def create_ai_insight(db: Session, user_id, period: str, period_start: date, insight_md: str):
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
