"""
Unit tests for Backend Agent authentication
"""
import pytest
from fastapi.testclient import TestClient

from ..main import app

client = TestClient(app)

def test_login_for_access_token():
    """Test obtaining a JWT token via login"""
    response = client.post(
        "/auth/token",
        data={"username": "johndoe", "password": "secret"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_for_access_token_invalid_password():
    """Test login with invalid password"""
    response = client.post(
        "/auth/token",
        data={"username": "johndoe", "password": "wrongpassword"},
    )
    assert response.status_code == 401