"""
CRUD operations for item management
"""
from typing import List
from sqlalchemy.orm import Session
from .models import ItemCreate, ItemUpdate
from database_agent.models import Item as ItemModel

def get_item(db: Session, item_id: int) -> ItemModel:
    """Get an item by ID"""
    return db.query(ItemModel).filter(ItemModel.id == item_id).first()

def get_items(db: Session, skip: int = 0, limit: int = 10) -> List[ItemModel]:
    """Get a list of items with pagination"""
    return db.query(ItemModel).offset(skip).limit(limit).all()

def create_item(db: Session, item: ItemCreate) -> ItemModel:
    """Create a new item"""
    db_item = ItemModel(
        name=item.name,
        description=item.description,
        price=item.price
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def update_item(db: Session, item_id: int, item: ItemUpdate) -> ItemModel:
    """Update an existing item"""
    db_item = db.query(ItemModel).filter(ItemModel.id == item_id).first()
    if db_item:
        db_item.name = item.name
        db_item.description = item.description
        db_item.price = item.price
        db.commit()
        db.refresh(db_item)
    return db_item

def delete_item(db: Session, item_id: int) -> bool:
    """Delete an item by ID"""
    db_item = db.query(ItemModel).filter(ItemModel.id == item_id).first()
    if db_item:
        db.delete(db_item)
        db.commit()
        return True
    return False