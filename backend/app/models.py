from sqlalchemy import Column, String, Integer, Numeric, ForeignKey, DateTime, Text, BigInteger, JSON, Date, UniqueConstraint, CheckConstraint, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
import sqlalchemy as sa
import uuid
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    gemini_api_key = Column(String)  # AES-GCM encrypted at rest
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    weight_logs = relationship('WeightLog', back_populates='user', cascade="all, delete-orphan")
    food_logs = relationship('FoodLog', back_populates='user', cascade="all, delete-orphan")
    hr_sessions = relationship('HRSession', back_populates='user', cascade="all, delete-orphan")
    ai_insights = relationship('AIInsight', back_populates='user', cascade="all, delete-orphan")
    food_parsing_sessions = relationship('FoodParsingSession', back_populates='user', cascade="all, delete-orphan")
    food_log_analyses = relationship('FoodLogAnalysis', back_populates='user', cascade="all, delete-orphan")
    profile = relationship('UserProfile', back_populates='user', cascade="all, delete-orphan", uselist=False)
    amazfit_credentials = relationship('AmazfitCredentials', back_populates='user', cascade="all, delete-orphan", uselist=False)
    activity_data = relationship('ActivityData', back_populates='user', cascade="all, delete-orphan")
    steps_data = relationship('StepsData', back_populates='user', cascade="all, delete-orphan")

class UserProfile(Base):
    __tablename__ = 'user_profiles'
    id = Column(BigInteger, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), unique=True)
    gender = Column(String)  # male, female, other
    height_cm = Column(Numeric(5,2))  # height in centimeters
    weight_kg = Column(Numeric(5,2))  # weight in kilograms
    age = Column(Integer)
    activity_level = Column(String)  # sedentary, lightly_active, moderately_active, very_active, extremely_active
    goal = Column(String)  # lose_weight, maintain_weight, gain_weight
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship('User', back_populates='profile')

class WeightLog(Base):
    __tablename__ = 'weight_logs'
    id = Column(BigInteger, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'))
    kg = Column(Numeric(5,2), nullable=False)
    logged_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    user = relationship('User', back_populates='weight_logs')

class FoodLog(Base):
    __tablename__ = 'food_logs'
    id = Column(BigInteger, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'))
    description = Column(Text)
    
    # Macronutrients
    calories = Column(Integer)
    protein_g = Column(Numeric(6,2))
    fat_g = Column(Numeric(6,2))
    carbs_g = Column(Numeric(6,2))
    fiber_g = Column(Numeric(6,2))
    sugar_g = Column(Numeric(6,2))
    
    # Micronutrients - Vitamins
    vitamin_a_mcg = Column(Numeric(8,2))  # Retinol Activity Equivalents
    vitamin_c_mg = Column(Numeric(8,2))
    vitamin_d_mcg = Column(Numeric(8,2))
    vitamin_e_mg = Column(Numeric(8,2))
    vitamin_k_mcg = Column(Numeric(8,2))
    vitamin_b1_mg = Column(Numeric(8,2))  # Thiamin
    vitamin_b2_mg = Column(Numeric(8,2))  # Riboflavin
    vitamin_b3_mg = Column(Numeric(8,2))  # Niacin
    vitamin_b5_mg = Column(Numeric(8,2))  # Pantothenic Acid
    vitamin_b6_mg = Column(Numeric(8,2))
    vitamin_b7_mcg = Column(Numeric(8,2))  # Biotin
    vitamin_b9_mcg = Column(Numeric(8,2))  # Folate
    vitamin_b12_mcg = Column(Numeric(8,2))
    
    # Micronutrients - Minerals
    calcium_mg = Column(Numeric(8,2))
    iron_mg = Column(Numeric(8,2))
    magnesium_mg = Column(Numeric(8,2))
    phosphorus_mg = Column(Numeric(8,2))
    potassium_mg = Column(Numeric(8,2))
    sodium_mg = Column(Numeric(8,2))
    zinc_mg = Column(Numeric(8,2))
    copper_mg = Column(Numeric(8,2))
    manganese_mg = Column(Numeric(8,2))
    selenium_mcg = Column(Numeric(8,2))
    chromium_mcg = Column(Numeric(8,2))
    molybdenum_mcg = Column(Numeric(8,2))
    
    # Other nutrients
    cholesterol_mg = Column(Numeric(8,2))
    saturated_fat_g = Column(Numeric(6,2))
    trans_fat_g = Column(Numeric(6,2))
    polyunsaturated_fat_g = Column(Numeric(6,2))
    monounsaturated_fat_g = Column(Numeric(6,2))
    
    # Metadata
    serving_size = Column(String)
    meal_type = Column(String)  # breakfast, lunch, dinner, snack
    confidence_score = Column(Numeric(3,2))  # AI confidence in nutritional data
    source = Column(String)  # manual, ai_parsed, mcp_server
    search_queries = Column(JSON)  # Store search queries used for grounding
    logged_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    user = relationship('User', back_populates='food_logs')

class FoodParsingSession(Base):
    __tablename__ = 'food_parsing_sessions'
    id = Column(BigInteger, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'))
    session_id = Column(String, unique=True, nullable=False)
    user_input = Column(Text, nullable=False)
    parsed_foods = Column(JSON)  # Array of parsed food items
    extracted_datetime = Column(DateTime(timezone=True))
    confidence_score = Column(Numeric(3,2))
    status = Column(String)  # pending, completed, failed
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True))
    
    user = relationship('User', back_populates='food_parsing_sessions')

class HRSession(Base):
    __tablename__ = 'hr_sessions'
    id = Column(BigInteger, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'))
    avg_hr = Column(Integer)
    max_hr = Column(Integer)
    min_hr = Column(Integer)
    duration_minutes = Column(Integer)
    session_data = Column(JSON)  # Raw HR data points
    logged_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    user = relationship('User', back_populates='hr_sessions')

class AIInsight(Base):
    __tablename__ = 'ai_insights'
    id = Column(BigInteger, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'))
    period = Column(String)  # daily, weekly, monthly
    period_start = Column(Date)
    insight_md = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    user = relationship('User', back_populates='ai_insights')
    
    __table_args__ = (
        UniqueConstraint('user_id', 'period', 'period_start', name='uq_user_period_start'),
    )

class FoodLogAnalysis(Base):
    __tablename__ = 'food_log_analyses'
    id = Column(BigInteger, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'))
    food_log_id = Column(BigInteger, ForeignKey('food_logs.id', ondelete='CASCADE'))
    health_score = Column(Numeric(5,2))  # 0-100 health score (increased precision)
    protein_adequacy = Column(String)  # low, adequate, high
    fiber_content = Column(String)  # low, adequate, high
    vitamin_balance = Column(String)  # poor, fair, good, excellent
    mineral_balance = Column(String)  # poor, fair, good, excellent
    recommendations = Column(JSON)  # Array of recommendation strings
    analysis_text = Column(Text)  # Detailed analysis text
    model_used = Column(String)  # Which AI model was used
    confidence_score = Column(Numeric(3,2))  # AI confidence in analysis
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship('User', back_populates='food_log_analyses')
    food_log = relationship('FoodLog')
    
    __table_args__ = (
        UniqueConstraint('user_id', 'food_log_id', name='uq_user_food_log_analysis'),
    )

class AmazfitCredentials(Base):
    __tablename__ = 'amazfit_credentials'
    id = Column(BigInteger, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), unique=True)
    app_token = Column(Text, nullable=False)
    user_id_amazfit = Column(String)  # Amazfit user ID
    email = Column(String)  # Amazfit email (encrypted)
    password = Column(String)  # Amazfit password (encrypted)
    last_sync = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship('User', back_populates='amazfit_credentials')

class ActivityData(Base):
    __tablename__ = 'activity_data'
    id = Column(BigInteger, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'))
    date = Column(Date, nullable=False)
    calories_burned = Column(Integer)
    active_minutes = Column(Integer)
    distance_km = Column(Numeric(6,2))
    steps = Column(Integer)
    sleep_hours = Column(Numeric(4,2))
    deep_sleep_hours = Column(Numeric(4,2))
    light_sleep_hours = Column(Numeric(4,2))
    rem_sleep_hours = Column(Numeric(4,2))
    awake_hours = Column(Numeric(4,2))
    sleep_score = Column(Integer)
    activity_score = Column(Integer)
    raw_data = Column(JSON)  # Store raw API response
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship('User', back_populates='activity_data')
    
    __table_args__ = (
        UniqueConstraint('user_id', 'date', name='uq_user_activity_date'),
    )

class StepsData(Base):
    __tablename__ = 'steps_data'
    id = Column(BigInteger, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'))
    date = Column(Date, nullable=False)
    total_steps = Column(Integer)
    hourly_steps = Column(JSON)  # Array of hourly step counts
    goal_steps = Column(Integer, default=10000)
    calories_burned = Column(Integer)
    distance_km = Column(Numeric(6,2))
    active_minutes = Column(Integer)
    raw_data = Column(JSON)  # Store raw API response
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship('User', back_populates='steps_data')
    
    __table_args__ = (
        UniqueConstraint('user_id', 'date', name='uq_user_steps_date'),
    )
