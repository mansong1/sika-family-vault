import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import get_db
from app.models.models import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_create_circle():
    response = client.post("/api/v1/circles", json={
        "name": "Test Susu",
        "description": "A test circle",
        "contribution_amount": "100.00",
        "cycle_days": 30,
        "max_members": 5
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Susu"
    assert data["status"] == "pending"

def test_list_circles():
    response = client.get("/api/v1/circles")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_activate_circle():
    create_resp = client.post("/api/v1/circles", json={
        "name": "Activate Test",
        "contribution_amount": "50.00",
        "cycle_days": 14,
        "max_members": 3
    })
    circle_id = create_resp.json()["id"]
    response = client.patch(f"/api/v1/circles/{circle_id}/activate")
    assert response.status_code == 200
    assert response.json()["status"] == "active"
