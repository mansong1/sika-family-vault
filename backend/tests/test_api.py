from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_create_circle():
    # Register first
    reg = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "phone_number": "+233501234567",
        "full_name": "Test User",
        "password": "password123",
        "bvn": "12345678901"
    })
    token = reg.json()["token"]
    
    response = client.post("/api/v1/circles", json={
        "name": "Family Susu",
        "description": "Monthly family savings",
        "contribution_amount": 100.0,
        "cycle_length_days": 30,
        "max_members": 5,
        "penalty_for_late": 0.05
    })
    assert response.status_code == 200
    assert response.json()["status"] == "pending"

def test_dashboard():
    response = client.get("/api/v1/dashboard")
    assert response.status_code == 200
    assert "credit_score" in response.json()

def test_credit_score():
    response = client.get("/api/v1/credit-score")
    assert response.status_code == 200
    assert response.json()["score"] >= 300
