"""
Backend Agent FastAPI Application

Main FastAPI application for the Backend Agent, providing RESTful APIs
for task management, project coordination, and business logic.
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
import logging
from typing import Optional
from datetime import datetime

from .routers import tasks, projects, agents, health
from .middleware.error_handler import setup_error_handlers

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Backend Agent API",
    description="Core business logic API for the Agentic AI Development Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# In a real application, you would configure CORS properly.
# For now, we'll allow all origins for simplicity.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup error handlers
setup_error_handlers(app)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Backend Agent starting up...")
    # Initialize database connections, caches, etc.

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("Backend Agent shutting down...")
    # Cleanup resources

@app.get("/health", tags=["system"])
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}

@app.get("/", tags=["system"])
async def root():
    """Root endpoint providing API information"""
    return {
        "service": "Backend Agent API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "api": "/api/v1"
        }
    }

@app.post("/", tags=["system"])
async def test_data_flow(request_data: dict):
    """Test endpoint for data flow validation"""
    return {
        "service": "Backend Agent API",
        "status": "data_received",
        "received_data": request_data,
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(
        "backend_agent.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )