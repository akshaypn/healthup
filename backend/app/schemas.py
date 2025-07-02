from pydantic import BaseModel, EmailStr, field_validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date
import uuid

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True
        
    @classmethod
    def from_orm(cls, obj):
        # Convert UUID to string for the id field
        if hasattr(obj, 'id') and obj.id is not None:
            obj.id = str(obj.id)
        return super().from_orm(obj)
    
    @field_validator('id', mode='before')
    @classmethod
    def validate_id(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: Dict[str, Any]

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class TokenData(BaseModel):
    email: Optional[str] = None

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

# Comprehensive Food Logging Schemas
class FoodLogCreate(BaseModel):
    description: str
    calories: Optional[int] = None
    protein_g: Optional[float] = None
    fat_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fiber_g: Optional[float] = None
    sugar_g: Optional[float] = None
    
    # Vitamins
    vitamin_a_mcg: Optional[float] = None
    vitamin_c_mg: Optional[float] = None
    vitamin_d_mcg: Optional[float] = None
    vitamin_e_mg: Optional[float] = None
    vitamin_k_mcg: Optional[float] = None
    vitamin_b1_mg: Optional[float] = None
    vitamin_b2_mg: Optional[float] = None
    vitamin_b3_mg: Optional[float] = None
    vitamin_b5_mg: Optional[float] = None
    vitamin_b6_mg: Optional[float] = None
    vitamin_b7_mcg: Optional[float] = None
    vitamin_b9_mcg: Optional[float] = None
    vitamin_b12_mcg: Optional[float] = None
    
    # Minerals
    calcium_mg: Optional[float] = None
    iron_mg: Optional[float] = None
    magnesium_mg: Optional[float] = None
    phosphorus_mg: Optional[float] = None
    potassium_mg: Optional[float] = None
    sodium_mg: Optional[float] = None
    zinc_mg: Optional[float] = None
    copper_mg: Optional[float] = None
    manganese_mg: Optional[float] = None
    selenium_mcg: Optional[float] = None
    chromium_mcg: Optional[float] = None
    molybdenum_mcg: Optional[float] = None
    
    # Other nutrients
    cholesterol_mg: Optional[float] = None
    saturated_fat_g: Optional[float] = None
    trans_fat_g: Optional[float] = None
    polyunsaturated_fat_g: Optional[float] = None
    monounsaturated_fat_g: Optional[float] = None
    
    # Metadata
    serving_size: Optional[str] = None
    meal_type: Optional[str] = None
    confidence_score: Optional[float] = None
    source: Optional[str] = "manual"
    search_queries: Optional[Dict[str, Any]] = None
    logged_at: Optional[datetime] = None

class FoodLogResponse(BaseModel):
    id: int
    description: str
    calories: Optional[int] = None
    protein_g: Optional[float] = None
    fat_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fiber_g: Optional[float] = None
    sugar_g: Optional[float] = None
    
    # Vitamins
    vitamin_a_mcg: Optional[float] = None
    vitamin_c_mg: Optional[float] = None
    vitamin_d_mcg: Optional[float] = None
    vitamin_e_mg: Optional[float] = None
    vitamin_k_mcg: Optional[float] = None
    vitamin_b1_mg: Optional[float] = None
    vitamin_b2_mg: Optional[float] = None
    vitamin_b3_mg: Optional[float] = None
    vitamin_b5_mg: Optional[float] = None
    vitamin_b6_mg: Optional[float] = None
    vitamin_b7_mcg: Optional[float] = None
    vitamin_b9_mcg: Optional[float] = None
    vitamin_b12_mcg: Optional[float] = None
    
    # Minerals
    calcium_mg: Optional[float] = None
    iron_mg: Optional[float] = None
    magnesium_mg: Optional[float] = None
    phosphorus_mg: Optional[float] = None
    potassium_mg: Optional[float] = None
    sodium_mg: Optional[float] = None
    zinc_mg: Optional[float] = None
    copper_mg: Optional[float] = None
    manganese_mg: Optional[float] = None
    selenium_mcg: Optional[float] = None
    chromium_mcg: Optional[float] = None
    molybdenum_mcg: Optional[float] = None
    
    # Other nutrients
    cholesterol_mg: Optional[float] = None
    saturated_fat_g: Optional[float] = None
    trans_fat_g: Optional[float] = None
    polyunsaturated_fat_g: Optional[float] = None
    monounsaturated_fat_g: Optional[float] = None
    
    # Metadata
    serving_size: Optional[str] = None
    meal_type: Optional[str] = None
    confidence_score: Optional[float] = None
    source: Optional[str] = None
    search_queries: Optional[Dict[str, Any]] = None
    logged_at: datetime

    class Config:
        from_attributes = True

class FoodHistoryResponse(BaseModel):
    logs: List[FoodLogResponse]

# AI Food Parsing Schemas
class ParsedFoodItem(BaseModel):
    description: str
    serving_size: Optional[str] = None
    meal_type: Optional[str] = None
    confidence_score: float
    nutritional_data: Dict[str, Any]

class FoodParsingRequest(BaseModel):
    user_input: str
    extract_datetime: bool = True

class FoodParsingResponse(BaseModel):
    session_id: str
    status: str
    parsed_foods: List[ParsedFoodItem]
    extracted_datetime: Optional[datetime] = None
    confidence_score: float
    error_message: Optional[str] = None
    meal_analysis: Optional[Dict[str, Any]] = None

class FoodParsingSessionResponse(BaseModel):
    id: int
    session_id: str
    user_input: str
    parsed_foods: List[ParsedFoodItem]
    extracted_datetime: Optional[datetime] = None
    confidence_score: float
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# MCP Server Schemas
class MCPServerConfig(BaseModel):
    api_key: str
    timeout: int = 30

class HRSessionCreate(BaseModel):
    avg_hr: int
    max_hr: int
    min_hr: int
    duration_minutes: int
    session_data: Optional[Dict[str, Any]] = None

class HRSessionResponse(BaseModel):
    id: int
    avg_hr: int
    max_hr: int
    min_hr: int
    duration_minutes: int
    session_data: Optional[Dict[str, Any]] = None
    logged_at: datetime

    class Config:
        from_attributes = True

class AIInsightResponse(BaseModel):
    id: int
    period: str
    period_start: date
    insight_md: str
    created_at: datetime

    class Config:
        from_attributes = True
