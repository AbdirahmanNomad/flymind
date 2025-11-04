"""
Pytest test suite for FlyMind API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from api.api import app
from api.database import Base, engine, SessionLocal, init_db
from api.models import FlightSearchRequest, PriceAlertRequest
import os

# Set test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["REQUIRE_API_KEY"] = "false"
os.environ["RATE_LIMIT_ENABLED"] = "false"

# Create test database
TEST_DATABASE_URL = "sqlite:///./test_flymind.db"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Clean up test database
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client():
    """Create a test client."""
    # Initialize database
    init_db()
    return TestClient(app)


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "/docs" in data.get("docs", "")


def test_version_endpoint(client):
    """Test version endpoint."""
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "2.0.0"
    assert "name" in data
    assert "environment" in data


def test_search_endpoint_validation(client):
    """Test flight search endpoint validation."""
    # Test with missing required fields
    response = client.post("/search", json={})
    assert response.status_code == 422  # Validation error
    
    # Test with invalid trip type
    response = client.post("/search", json={
        "trip_type": "invalid",
        "origin": "JFK",
        "destination": "LAX",
        "depart_date": "2025-12-25"
    })
    assert response.status_code == 422


def test_price_alert_validation(client):
    """Test price alert validation."""
    # Test with invalid currency
    response = client.post("/alerts", json={
        "trip_type": "one-way",
        "origin": "JFK",
        "destination": "LAX",
        "depart_date": "2025-12-25",
        "target_price": 500.0,
        "currency": "INVALID",
        "email": "test@example.com"
    })
    assert response.status_code == 422
    
    # Test with negative price
    response = client.post("/alerts", json={
        "trip_type": "one-way",
        "origin": "JFK",
        "destination": "LAX",
        "depart_date": "2025-12-25",
        "target_price": -100.0,
        "currency": "USD",
        "email": "test@example.com"
    })
    assert response.status_code == 422


def test_webhook_endpoints(client):
    """Test webhook management endpoints."""
    # List webhooks (should be empty initially)
    response = client.get("/webhooks")
    assert response.status_code == 200
    assert "webhooks" in response.json()
    
    # Register webhook
    response = client.post("/webhooks", data={"webhook_url": "https://example.com/webhook"})
    assert response.status_code == 200
    
    # List webhooks again
    response = client.get("/webhooks")
    assert response.status_code == 200
    data = response.json()
    assert len(data["webhooks"]) == 1
    assert "https://example.com/webhook" in data["webhooks"]
    
    # Unregister webhook
    response = client.delete("/webhooks?webhook_url=https://example.com/webhook")
    assert response.status_code == 200


def test_alerts_endpoints(client):
    """Test price alert endpoints."""
    # List alerts (should be empty initially)
    response = client.get("/alerts")
    assert response.status_code == 200
    assert "alerts" in response.json()
    
    # Create alert
    alert_data = {
        "trip_type": "one-way",
        "origin": "JFK",
        "destination": "LAX",
        "depart_date": "2025-12-25",
        "target_price": 500.0,
        "currency": "USD",
        "email": "test@example.com",
        "notification_channels": ["email"]
    }
    response = client.post("/alerts", json=alert_data)
    assert response.status_code == 200
    data = response.json()
    assert "alert_id" in data
    alert_id = data["alert_id"]
    
    # List alerts
    response = client.get("/alerts")
    assert response.status_code == 200
    alerts = response.json()["alerts"]
    assert len(alerts) == 1
    
    # Delete alert
    response = client.delete(f"/alerts/{alert_id}")
    assert response.status_code == 200


def test_search_history_endpoint(client):
    """Test search history endpoint."""
    # Try to get non-existent search
    response = client.get("/search/nonexistent")
    assert response.status_code == 404


def test_cors_headers(client):
    """Test CORS headers are present."""
    response = client.options("/health")
    # CORS middleware should add headers
    assert response.status_code in [200, 204]


def test_error_handling(client):
    """Test error handling."""
    # Test 404
    response = client.get("/nonexistent")
    assert response.status_code == 404
    
    # Test invalid JSON
    response = client.post("/search", data="invalid json")
    assert response.status_code == 422


