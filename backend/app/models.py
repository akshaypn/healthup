from sqlalchemy import Column, String, Integer, Numeric, ForeignKey, DateTime, Text, BigInteger, JSON, Date, UniqueConstraint, CheckConstraint
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
    calories = Column(Integer)
    protein_g = Column(Integer)
    fat_g = Column(Integer)
    carbs_g = Column(Integer)
    logged_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    user = relationship('User', back_populates='food_logs')

class HRSession(Base):
    __tablename__ = 'hr_sessions'
    id = Column(BigInteger, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'))
    avg_bpm = Column(Integer)
    min_bpm = Column(Integer)
    max_bpm = Column(Integer)
    raw_json = Column(JSON)
    started_at = Column(DateTime(timezone=True))
    ended_at = Column(DateTime(timezone=True))
    user = relationship('User', back_populates='hr_sessions')

class AIInsight(Base):
    __tablename__ = 'ai_insights'
    id = Column(BigInteger, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'))
    period = Column(String, CheckConstraint("period in ('daily','weekly','monthly')"))
    period_start = Column(Date)
    insight_md = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    user = relationship('User', back_populates='ai_insights')
    __table_args__ = (
        UniqueConstraint('user_id', 'period', 'period_start', name='uq_user_period_start'),
    )
