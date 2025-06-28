"""
Pydantic models for request and response validation
"""
from typing import Optional, List
from pydantic import BaseModel

class ItemBase(BaseModel):
    """Base model for item data"""
    name: str
    description: Optional[str] = None
    price: float

class ItemCreate(ItemBase):
    """Model for creating a new item"""

class ItemUpdate(ItemBase):
    """Model for updating an existing item"""

class ItemResponse(ItemBase):
    """Model for returning item data with ID"""
    id: int

    class Config:
        orm_mode = True

class Token(BaseModel):
    """Model for JWT token response"""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Model for token data payload"""
    username: Optional[str] = None