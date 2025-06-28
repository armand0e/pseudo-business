"""
Database dependencies for dependency injection
"""
from sqlalchemy.orm import Session

def get_db_session():
    """Dependency to get a database session"""
    # In a real application, this would be connected to the actual database
    # For now, we'll use a mock session
    from database_agent.models import SessionLocal

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()