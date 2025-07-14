"""
Database Session

Database session management for the Backend Agent.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# In a real application, this would come from a config file
SQLALCHEMY_DATABASE_URL = "sqlite:///./backend_agent.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    Database session dependency
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()