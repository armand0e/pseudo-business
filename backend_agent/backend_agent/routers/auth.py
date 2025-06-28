"""
Authentication router
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..models import Token, TokenData
from ..auth import create_access_token
from ..dependencies import get_db_session

# Fake user database for demonstration purposes
fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbhgJQO3LxRrzM2lQK65g6No6YeW45SgaHE1e",  # bcrypt hash of "secret"
        "disabled": False,
    }
}

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

def verify_password(plain_password, hashed_password):
    """Verify a password against its hash"""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.verify(plain_password, hashed_password)

def get_user(db, username: str):
    """Get a user by username"""
    # In a real application, this would query the database
    if username in fake_users_db:
        user_dict = fake_users_db[username]
        return TokenData(**user_dict)
    return None

def authenticate_user(db: Session, username: str, password: str):
    """Authenticate a user"""
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, fake_users_db[username]["hashed_password"]):
        return False
    return user

@router.post("/token", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db_session)
):
    """Login endpoint to obtain a JWT token"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}