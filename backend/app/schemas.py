from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserRegister(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class WeightLogCreate(BaseModel):
    kg: float

class WeightLogResponse(BaseModel):
    id: int
    kg: float
    logged_at: datetime

    class Config:
        from_attributes = True

class WeightHistoryResponse(BaseModel):
    logs: List[WeightLogResponse]

class FoodLogCreate(BaseModel):
    description: str
    calories: int
    protein_g: int
    fat_g: int
    carbs_g: int

class FoodLogResponse(BaseModel):
    id: int
    description: str
    calories: int
    protein_g: int
    fat_g: int
    carbs_g: int
    logged_at: datetime

    class Config:
        from_attributes = True

class FoodHistoryResponse(BaseModel):
    logs: List[FoodLogResponse]

class HRLogCreate(BaseModel):
    avg_bpm: int
    min_bpm: int
    max_bpm: int
    raw: dict

class HRLogResponse(BaseModel):
    id: int
    avg_bpm: int
    min_bpm: int
    max_bpm: int
    started_at: datetime
    ended_at: datetime

    class Config:
        from_attributes = True

class HRHistoryResponse(BaseModel):
    logs: List[HRLogResponse]

class AIInsightResponse(BaseModel):
    period: str
    period_start: str
    insight_md: str
    created_at: str
