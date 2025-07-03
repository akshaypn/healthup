import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import get_db, Base
from app.main import app
from app.auth import get_password_hash
from app.models import User
import uuid

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(test_db):
    return TestClient(app)

@pytest.fixture
def test_user():
    return {
        "email": "test@example.com",
        "password": "testpassword123"
    }

def test_register_user(client, test_user):
    """Test user registration"""
    response = client.post("/auth/register", json=test_user)
    assert response.status_code == 200
    data = response.json()
    assert "User registered successfully" in data["message"]
    assert data["user"]["email"] == test_user["email"]

def test_register_duplicate_user(client, test_user):
    """Test registering a duplicate user"""
    # Register first user
    client.post("/auth/register", json=test_user)
    
    # Try to register same user again
    response = client.post("/auth/register", json=test_user)
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]

def test_login_user(client, test_user):
    """Test user login"""
    # Register user first
    client.post("/auth/register", json=test_user)
    
    # Login
    response = client.post("/auth/login", json=test_user)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == test_user["email"]

def test_login_invalid_credentials(client, test_user):
    """Test login with invalid credentials"""
    # Register user first
    client.post("/auth/register", json=test_user)
    
    # Try to login with wrong password
    invalid_credentials = {
        "email": test_user["email"],
        "password": "wrongpassword"
    }
    response = client.post("/auth/login", json=invalid_credentials)
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]

def test_login_nonexistent_user(client):
    """Test login with non-existent user"""
    response = client.post("/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "password123"
    })
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]

def test_get_current_user(client, test_user):
    """Test getting current user with valid token"""
    # Register and login user
    client.post("/auth/register", json=test_user)
    login_response = client.post("/auth/login", json=test_user)
    token = login_response.json()["access_token"]
    
    # Get current user
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user["email"]

def test_get_current_user_invalid_token(client):
    """Test getting current user with invalid token"""
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 401

def test_refresh_token(client, test_user):
    """Test token refresh"""
    # Register and login user
    client.post("/auth/register", json=test_user)
    login_response = client.post("/auth/login", json=test_user)
    refresh_token = login_response.json()["refresh_token"]
    
    # Refresh token
  