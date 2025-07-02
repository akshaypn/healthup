from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from . import schemas, models, database, deps
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
import os
import secrets

SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "20160"))  # 2 weeks (14 days * 24 * 60)
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))  # 30 days

# Cookie settings for production
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true").lower() == "true"  # Set to true in production
COOKIE_DOMAIN = os.getenv("COOKIE_DOMAIN", None)  # Set your domain in production
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax")  # lax, strict, or none

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter()

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str, token_type: str = "access"):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != token_type:
            raise JWTError("Invalid token type")
        return payload
    except JWTError:
        return None

def set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    """Set httpOnly cookies for authentication"""
    # Access token cookie (2 weeks)
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        domain=COOKIE_DOMAIN,
        path="/"
    )
    
    # Refresh token cookie (30 days)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,  # Convert to seconds
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        domain=COOKIE_DOMAIN,
        path="/"
    )

def clear_auth_cookies(response: Response):
    """Clear authentication cookies"""
    response.delete_cookie("access_token", path="/", domain=COOKIE_DOMAIN)
    response.delete_cookie("refresh_token", path="/", domain=COOKIE_DOMAIN)

@router.post("/auth/register", status_code=201)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = get_password_hash(user.password)
    db_user = models.User(email=user.email, password_hash=hashed)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"msg": "User registered successfully"}

@router.post("/auth/login", response_model=schemas.Token)
def login(user: schemas.UserLogin, response: Response, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create both access and refresh tokens
    access_token = create_access_token({"sub": str(db_user.id)})
    refresh_token = create_refresh_token({"sub": str(db_user.id)})
    
    # Set httpOnly cookies
    set_auth_cookies(response, access_token, refresh_token)
    
    return {
        "access_token": access_token,  # Still return for backward compatibility
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES,  # minutes
        "user": {
            "id": str(db_user.id),
            "email": db_user.email
        }
    }

@router.post("/auth/refresh", response_model=schemas.Token)
def refresh_token(request: Request, response: Response, db: Session = Depends(get_db)):
    # Get refresh token from Authorization header first, then fallback to cookie
    auth_header = request.headers.get("Authorization")
    refresh_token = None
    
    if auth_header and auth_header.startswith("Bearer "):
        refresh_token = auth_header.split(" ")[1]
    else:
        # Fallback to cookie for backward compatibility
        refresh_token = request.cookies.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token found")
    
    payload = verify_token(refresh_token, "refresh")
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    # Verify user still exists
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Create new tokens
    new_access_token = create_access_token({"sub": str(db_user.id)})
    new_refresh_token = create_refresh_token({"sub": str(db_user.id)})
    
    # Set new httpOnly cookies for backward compatibility
    set_auth_cookies(response, new_access_token, new_refresh_token)
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES,  # minutes
        "user": {
            "id": str(db_user.id),
            "email": db_user.email
        }
    }

@router.get("/auth/me", response_model=schemas.UserResponse)
def get_current_user_info(current_user: models.User = Depends(deps.get_current_user)):
    return current_user

@router.post("/auth/logout")
def logout(response: Response):
    # Clear authentication cookies
    clear_auth_cookies(response)
    return {"msg": "Logged out successfully"}
