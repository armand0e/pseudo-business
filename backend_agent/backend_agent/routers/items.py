"""
Item router for CRUD operations
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..models import ItemCreate, ItemUpdate, ItemResponse
from ..crud import (
    get_item as crud_get_item,
    get_items as crud_get_items,
    create_item as crud_create_item,
    update_item as crud_update_item,
    delete_item as crud_delete_item
)
from ..dependencies import get_db_session
from ..auth import authenticate_token

router = APIRouter(
    prefix="/items",
    tags=["items"],
    dependencies=[Depends(authenticate_token)]
)

@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(item: ItemCreate, db: Session = Depends(get_db_session)):
    """Create a new item"""
    return crud_create_item(db=db, item=item)

@router.get("/", response_model=List[ItemResponse])
def read_items(skip: int = 0, limit: int = 10, db: Session = Depends(get_db_session)):
    """Get a list of items with pagination"""
    items = crud_get_items(db=db, skip=skip, limit=limit)
    return items

@router.get("/{item_id}", response_model=ItemResponse)
def read_item(item_id: int, db: Session = Depends(get_db_session)):
    """Get an item by ID"""
    db_item = crud_get_item(db=db, item_id=item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

@router.put("/{item_id}", response_model=ItemResponse)
def update_item(item_id: int, item: ItemUpdate, db: Session = Depends(get_db_session)):
    """Update an existing item"""
    db_item = crud_update_item(db=db, item_id=item_id, item=item)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

@router.delete("/{item_id}", response_model=ItemResponse)
def delete_item(item_id: int, db: Session = Depends(get_db_session)):
    """Delete an item by ID"""
    db_item = crud_get_item(db=db, item_id=item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    success = crud_delete_item(db=db, item_id=item_id)
    if not success:
        raise HTTPException(status_code=500, detail="Could not delete item")

    return db_item