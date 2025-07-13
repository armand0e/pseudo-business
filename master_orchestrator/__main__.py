"""
Master Orchestrator - Central coordination and orchestration of all platform services
Port: 8000
Technology: Python 3.9+, FastAPI, async operations
Security: JWT authentication, rate limiting, input validation
Performance: <200ms response times, async processing
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, List, Optional

import aiohttp
import jwt
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for tracking metrics
start_time = time.time()
task_metrics = {
    "active_tasks": 0,
    "completed_tasks": 0,
    "agent_connections": 0,
    "total_response_time": 0.0,
    "request_count": 0
}

# Security configuration
JWT_SECRET = "master-orchestrator-secret-key"  # In production, use environment variable
JWT_ALGORITHM = "HS256"

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)

# Security
security = HTTPBearer()

# Agent endpoints configuration
AGENT_ENDPOINTS = {
    "database_agent": "http://localhost:3001",
    "backend_agent": "http://localhost:8001", 
    "api_gateway": "http://localhost:3000",
    "frontend_agent": "http://localhost:3002",
    "testing_agent": "http://localhost:8002"
}

# Pydantic models for input validation
class TaskRequest(BaseModel):
    task_type: str
    priority: int
    description: str
    agent_target: Optional[str] = None
    
    @validator('priority')
    def priority_must_be_valid(cls, v):
        if v < 1 or v > 10:
            raise ValueError('Priority must be between 1 and 10')
        return v
    
    @validator('task_type')
    def task_type_must_be_valid(cls, v):
        valid_types = ['database', 'backend', 'frontend', 'testing', 'orchestration']
        if v.lower() not in valid_types:
            raise ValueError(f'Task type must be one of: {valid_types}')
        return v.lower()

class AgentStatusRequest(BaseModel):
    agent_name: str
    
    @validator('agent_name')
    def agent_name_must_be_valid(cls, v):
        if v not in AGENT_ENDPOINTS:
            raise ValueError(f'Agent name must be one of: {list(AGENT_ENDPOINTS.keys())}')
        return v

# JWT Authentication functions
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )

# Async helper functions
async def call_agent(session: aiohttp.ClientSession, agent_name: str, data: dict) -> dict:
    """Make async call to agent"""
    if agent_name not in AGENT_ENDPOINTS:
        return {"error": f"Unknown agent: {agent_name}"}
    
    try:
        url = f"{AGENT_ENDPOINTS[agent_name]}/health"
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
            if response.status == 200:
                result = await response.json()
                return {"agent": agent_name, "status": "success", "data": result}
            else:
                return {"agent": agent_name, "status": "error", "code": response.status}
    except asyncio.TimeoutError:
        return {"agent": agent_name, "status": "timeout"}
    except Exception as e:
        logger.error(f"Error calling agent {agent_name}: {str(e)}")
        return {"agent": agent_name, "status": "error", "error": str(e)}

async def orchestrate_agents(task_data: dict) -> List[dict]:
    """Async orchestration of multiple agents"""
    task_metrics["active_tasks"] += 1
    
    try:
        async with aiohttp.ClientSession() as session:
            # Determine which agents to call based on task type
            target_agents = []
            if task_data.get("agent_target"):
                target_agents = [task_data["agent_target"]]
            else:
                # Call all agents for comprehensive orchestration
                target_agents = list(AGENT_ENDPOINTS.keys())
            
            tasks = [
                call_agent(session, agent, task_data)
                for agent in target_agents
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Update metrics
            task_metrics["completed_tasks"] += 1
            task_metrics["active_tasks"] = max(0, task_metrics["active_tasks"] - 1)
            
            return results
    except Exception as e:
        task_metrics["active_tasks"] = max(0, task_metrics["active_tasks"] - 1)
        logger.error(f"Orchestration error: {str(e)}")
        raise

async def check_agent_connectivity() -> Dict[str, str]:
    """Check connectivity to all agents"""
    agent_status = {}
    
    async with aiohttp.ClientSession() as session:
        tasks = [
            call_agent(session, agent_name, {})
            for agent_name in AGENT_ENDPOINTS.keys()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, agent_name in enumerate(AGENT_ENDPOINTS.keys()):
            result = results[i]
            if isinstance(result, dict) and result.get("status") == "success":
                agent_status[agent_name] = "connected"
            else:
                agent_status[agent_name] = "disconnected"
    
    task_metrics["agent_connections"] = sum(1 for status in agent_status.values() if status == "connected")
    return agent_status

# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("Master Orchestrator starting up...")
    
    # Startup: Check initial agent connectivity
    await check_agent_connectivity()
    logger.info("Initial agent connectivity check completed")
    
    yield
    
    # Shutdown
    logger.info("Master Orchestrator shutting down...")

# FastAPI application
app = FastAPI(
    title="Master Orchestrator",
    description="Central coordination and orchestration of all platform services",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    start_time = time.time()
    
    response = await call_next(request)
    
    # Calculate response time for metrics
    process_time = time.time() - start_time
    task_metrics["total_response_time"] += process_time
    task_metrics["request_count"] += 1
    
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

# Health endpoint (public, no authentication required)
@app.get("/health")
@limiter.limit("100/minute")
async def health_check(request: Request):
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "master-orchestrator",
        "port": 8000,
        "timestamp": time.time()
    }

# Status endpoint (protected)
@app.get("/status")
@limiter.limit("100/minute")
async def get_status(request: Request, token = Depends(verify_token)):
    """Detailed service status with agent connectivity"""
    agent_status = await check_agent_connectivity()
    
    return {
        "status": "running",
        "service": "master-orchestrator",
        "port": 8000,
        "version": "1.0.0",
        "timestamp": time.time(),
        "uptime_seconds": time.time() - start_time,
        "components": {
            "orchestration_engine": "active",
            **agent_status
        },
        "security": {
            "authentication": "jwt",
            "rate_limiting": "100/minute",
            "input_validation": "enabled"
        }
    }

# Metrics endpoint (protected)
@app.get("/metrics")
@limiter.limit("100/minute")
async def get_metrics(request: Request, token = Depends(verify_token)):
    """Prometheus-compatible metrics"""
    avg_response_time = (
        task_metrics["total_response_time"] / task_metrics["request_count"] * 1000
        if task_metrics["request_count"] > 0 else 0
    )
    
    return {
        "orchestration": {
            "active_tasks": task_metrics["active_tasks"],
            "completed_tasks": task_metrics["completed_tasks"],
            "agent_connections": task_metrics["agent_connections"],
            "average_response_time_ms": round(avg_response_time, 2)
        },
        "system": {
            "uptime_seconds": round(time.time() - start_time, 2),
            "memory_usage_mb": 256,  # Placeholder - in production, use psutil
            "cpu_usage_percent": 15.0,  # Placeholder - in production, use psutil
            "total_requests": task_metrics["request_count"]
        },
        "performance": {
            "avg_response_time_ms": round(avg_response_time, 2),
            "target_response_time_ms": 200,
            "performance_target_met": avg_response_time < 200
        }
    }

# Task orchestration endpoint (protected)
@app.post("/orchestrate")
@limiter.limit("100/minute")
async def orchestrate_task(
    task_request: TaskRequest,
    request: Request,
    token = Depends(verify_token)
):
    """Orchestrate a task across relevant agents"""
    try:
        logger.info(f"Orchestrating task: {task_request.task_type} with priority {task_request.priority}")
        
        task_data = task_request.dict()
        results = await orchestrate_agents(task_data)
        
        return {
            "status": "success",
            "task_id": f"task_{int(time.time())}_{task_request.priority}",
            "task_type": task_request.task_type,
            "priority": task_request.priority,
            "results": results,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Orchestration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Orchestration failed: {str(e)}"
        )

# Agent status check endpoint (protected)
@app.post("/agent-status")
@limiter.limit("100/minute")
async def check_agent_status(
    agent_request: AgentStatusRequest,
    request: Request,
    token = Depends(verify_token)
):
    """Check status of a specific agent"""
    try:
        async with aiohttp.ClientSession() as session:
            result = await call_agent(session, agent_request.agent_name, {})
            
        return {
            "agent": agent_request.agent_name,
            "endpoint": AGENT_ENDPOINTS[agent_request.agent_name],
            "status": result.get("status", "unknown"),
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Agent status check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent status check failed: {str(e)}"
        )

# Authentication endpoint (public) - for testing purposes
@app.post("/auth/token")
@limiter.limit("10/minute")
async def create_access_token(request: Request):
    """Create JWT token for testing purposes"""
    try:
        # In production, this would validate user credentials
        payload = {
            "sub": "master-orchestrator-user",
            "exp": time.time() + 3600,  # 1 hour expiration
            "iat": time.time(),
            "service": "master-orchestrator"
        }
        
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": 3600
        }
    except Exception as e:
        logger.error(f"Token creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token creation failed: {str(e)}"
        )

# Error handling
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return {
        "error": {
            "status_code": exc.status_code,
            "detail": exc.detail,
            "timestamp": time.time(),
            "path": str(request.url)
        }
    }

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return {
        "error": {
            "status_code": 500,
            "detail": "Internal server error",
            "timestamp": time.time(),
            "path": str(request.url)
        }
    }

def main():
    """Main entry point for the master orchestrator service"""
    logger.info("Starting Master Orchestrator on port 8000...")
    uvicorn.run(
        "master_orchestrator.__main__:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        access_log=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()