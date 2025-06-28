"""
Unit tests for Backend Agent routers
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..main import app
from ..dependencies import get_db_session
from database_agent.models import Base, Item as ItemModel

# Create a new database session for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db_session dependency
@app.dependency_overrides[get_db_session]
def override_get_db_session():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_database():
    """Setup the test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_create_item(setup_database):
    """Test creating an item via API"""
    response = client.post(
        "/items/",
        json={"name": "API Test Item", "description": "API Description", "price": 15.0},
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == "API Test Item"

def test_read_items(setup_database):
    """Test reading items via API"""
    # First create an item
    client.post(
        "/items/",
        json={"name": "List Test Item", "description": "List Description", "price": 25.0},
    )

    # Now read the list
    response = client.get("/items/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

def test_read_item(setup_database):
    """Test reading a specific item via API"""
    # First create an item
    post_response = client.post(
        "/items/",
        json={"name": "Get Test Item", "description": "Get Description", "price": 35.0},
    )
    item_id = post_response.json()["id"]

    # Now read it
    response = client.get(f"/items/{item_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Get Test Item"

def test_update_item(setup_database):
    """Test updating an item via API"""
    # First create an item
    post_response = client.post(
        "/items/",
        json={"name": "Update Test Item", "description": "Old Description", "price": 45.0},
    )
    item_id = post_response.json()["id"]

    # Now update it
    response = client.put(
        f"/items/{item_id}",
        json={"name": "Updated Name", "description": "New Description", "price": 55.0},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"

def test_delete_item(setup_database):
    """Test deleting an item via API"""
    # First create an item
    post_response = client.post(
        "/items/",
        json={"name": "Delete Test Item", "description": "Delete Description", "price": 65.0},
    )
    item_id = post_response.json()["id"]

    # Now delete it
    response = client.delete(f"/items/{item_id}")
    assert response.status_code == 200

    # Verify it's gone
    get_response = client.get(f"/items/{item_id}")
    assert get_response.status_code == 404