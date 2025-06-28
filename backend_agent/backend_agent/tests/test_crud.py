"""
Unit tests for Backend Agent CRUD operations
"""
import pytest
from sqlalchemy.orm import Session

from ..crud import (
    create_item,
    get_item,
    update_item,
    delete_item,
)
from ..models import ItemCreate, ItemUpdate
from database_agent.models import Base, Item as ItemModel

@pytest.fixture(scope="module")
def setup_database():
    """Setup the test database"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)
    yield TestingSessionLocal()
    Base.metadata.drop_all(bind=engine)

def test_create_item(setup_database):
    """Test creating an item"""
    db: Session = setup_database
    item_data = ItemCreate(name="Test Item", description="Test Description", price=10.0)
    item = create_item(db=db, item=item_data)
    assert item.id is not None
    assert item.name == item_data.name
    assert item.description == item_data.description
    assert item.price == item_data.price

def test_get_item(setup_database):
    """Test getting an item"""
    db: Session = setup_database
    # Create a test item first
    item_data = ItemCreate(name="Get Test Item", description="Get Description", price=20.0)
    created_item = create_item(db=db, item=item_data)

    # Now retrieve it
    retrieved_item = get_item(db=db, item_id=created_item.id)
    assert retrieved_item is not None
    assert retrieved_item.name == item_data.name

def test_update_item(setup_database):
    """Test updating an item"""
    db: Session = setup_database
    # Create a test item first
    item_data = ItemCreate(name="Update Test Item", description="Old Description", price=30.0)
    created_item = create_item(db=db, item=item_data)

    # Now update it
    updated_data = ItemUpdate(name="Updated Name", description="New Description", price=40.0)
    updated_item = update_item(db=db, item_id=created_item.id, item=updated_data)

    assert updated_item is not None
    assert updated_item.name == updated_data.name
    assert updated_item.description == updated_data.description
    assert updated_item.price == updated_data.price

def test_delete_item(setup_database):
    """Test deleting an item"""
    db: Session = setup_database
    # Create a test item first
    item_data = ItemCreate(name="Delete Test Item", description="Delete Description", price=50.0)
    created_item = create_item(db=db, item=item_data)

    # Now delete it
    success = delete_item(db=db, item_id=created_item.id)
    assert success is True

    # Verify it's gone
    deleted_item = get_item(db=db, item_id=created_item.id)
    assert deleted_item is None