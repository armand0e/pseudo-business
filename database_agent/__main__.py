"""Main FastAPI application for the Database Agent."""
import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any

import structlog
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import (
    get_current_active_user,
    get_current_admin_user,
    create_access_token,
    authenticate_user,
    UserResponse,
)
from .config import settings
from .crud import (
    user_crud,
    project_crud,
    task_crud,
    agent_crud,
    create_audit_log,
    PaginationParams,
    FilterParams,
    UserCreate,
    UserUpdate,
    ProjectCreate,
    ProjectUpdate,
    TaskCreate,
    TaskUpdate,
    AgentCreate,
    AgentUpdate,
)
from .database import db_manager, get_db_session
from .models import User, Project, Task, Agent

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
DB_OPERATIONS = Counter('database_operations_total', 'Total database operations', ['operation', 'table'])

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Database Agent service")
    await db_manager.initialize()
    logger.info("Database Agent service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Database Agent service")
    await db_manager.close()
    logger.info("Database Agent service stopped")


# Create FastAPI application
app = FastAPI(
    title="Database Agent",
    description="Centralized database operations and data management service",
    version=settings.app.version,
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.security.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure as needed for production
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Middleware for metrics and logging
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add request processing time and metrics."""
    start_time = time.time()
    
    # Log request
    logger.info(
        "HTTP request started",
        method=request.method,
        url=str(request.url),
        remote_addr=request.client.host if request.client else None,
    )
    
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Update metrics
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    REQUEST_DURATION.observe(process_time)
    
    # Log response
    logger.info(
        "HTTP request completed",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        process_time=process_time,
    )
    
    return response


# Pydantic models for API
class LoginRequest(BaseModel):
    """Login request model."""
    email: str
    password: str


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str = "bearer"


class HealthResponse(BaseModel):
    """Health response model."""
    status: str
    timestamp: str
    version: str
    database: Dict[str, Any]


class StatusResponse(BaseModel):
    """Status response model."""
    service: str
    version: str
    status: str
    uptime: float
    database: Dict[str, Any]
    metrics: Dict[str, Any]


class MetricsResponse(BaseModel):
    """Metrics response model."""
    requests_total: int
    database_connections: Dict[str, Any]
    active_users: int
    active_projects: int
    active_tasks: int


# Health check endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    db_health = await db_manager.health_check()
    
    return HealthResponse(
        status="healthy" if db_health["status"] == "healthy" else "unhealthy",
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        version=settings.app.version,
        database=db_health,
    )


@app.get("/status", response_model=StatusResponse)
async def status_check():
    """Detailed status endpoint."""
    db_health = await db_manager.health_check()
    
    return StatusResponse(
        service=settings.app.service_name,
        version=settings.app.version,
        status="healthy" if db_health["status"] == "healthy" else "unhealthy",
        uptime=time.time(),  # This would be actual uptime in production
        database=db_health,
        metrics={
            "total_requests": 0,  # Would be actual metrics
            "active_connections": db_health.get("pool_checked_out", 0),
        },
    )


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Authentication endpoints
@app.post("/auth/login", response_model=TokenResponse)
@limiter.limit(f"{settings.security.rate_limit_requests}/minute")
async def login(
    request: Request,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Authenticate user and return access token."""
    user = await authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": str(user.id)})
    
    logger.info("User logged in", user_id=str(user.id), email=user.email)
    
    return TokenResponse(access_token=access_token)


# User endpoints
@app.get("/users", response_model=List[UserResponse])
@limiter.limit(f"{settings.security.rate_limit_requests}/minute")
async def list_users(
    request: Request,
    pagination: PaginationParams = Depends(),
    filters: FilterParams = Depends(),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_admin_user),
):
    """List users with pagination and filtering."""
    users = await user_crud.get_multi(db, pagination, filters)
    DB_OPERATIONS.labels(operation="read", table="users").inc()
    
    return [
        UserResponse(
            id=str(user.id),
            email=user.email,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
            is_admin=user.is_admin,
            created_at=user.created_at,
            last_login=user.last_login,
        )
        for user in users
    ]


@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(f"{settings.security.rate_limit_requests}/minute")
async def create_user(
    request: Request,
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_admin_user),
):
    """Create a new user."""
    # Check if user already exists
    existing_user = await user_crud.get_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    existing_username = await user_crud.get_by_username(db, user_data.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )
    
    user = await user_crud.create(db, user_data)
    DB_OPERATIONS.labels(operation="create", table="users").inc()
    
    # Create audit log
    await create_audit_log(
        db,
        entity_type="user",
        entity_id=user.id,
        action="create",
        user_id=current_user.id,
    )
    
    logger.info("User created", user_id=str(user.id), email=user.email)
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        is_admin=user.is_admin,
        created_at=user.created_at,
        last_login=user.last_login,
    )


@app.get("/users/{user_id}", response_model=UserResponse)
@limiter.limit(f"{settings.security.rate_limit_requests}/minute")
async def get_user(
    request: Request,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
):
    """Get user by ID."""
    user = await user_crud.get(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Users can only view their own profile unless they're admin
    if user.id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    DB_OPERATIONS.labels(operation="read", table="users").inc()
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        is_admin=user.is_admin,
        created_at=user.created_at,
        last_login=user.last_login,
    )


@app.put("/users/{user_id}", response_model=UserResponse)
@limiter.limit(f"{settings.security.rate_limit_requests}/minute")
async def update_user(
    request: Request,
    user_id: uuid.UUID,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
):
    """Update user by ID."""
    user = await user_crud.get(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Users can only update their own profile unless they're admin
    if user.id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Non-admin users cannot change admin status
    if not current_user.is_admin and user_data.is_admin is not None:
        user_data.is_admin = None
    
    user = await user_crud.update(db, user, user_data)
    DB_OPERATIONS.labels(operation="update", table="users").inc()
    
    # Create audit log
    await create_audit_log(
        db,
        entity_type="user",
        entity_id=user.id,
        action="update",
        user_id=current_user.id,
        changes=user_data.model_dump(exclude_unset=True),
    )
    
    logger.info("User updated", user_id=str(user.id), email=user.email)
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        is_admin=user.is_admin,
        created_at=user.created_at,
        last_login=user.last_login,
    )


@app.delete("/users/{user_id}")
@limiter.limit(f"{settings.security.rate_limit_requests}/minute")
async def delete_user(
    request: Request,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_admin_user),
):
    """Delete user by ID."""
    user = await user_crud.get(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Cannot delete self
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )
    
    success = await user_crud.delete(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete user",
        )
    
    DB_OPERATIONS.labels(operation="delete", table="users").inc()
    
    # Create audit log
    await create_audit_log(
        db,
        entity_type="user",
        entity_id=user.id,
        action="delete",
        user_id=current_user.id,
    )
    
    logger.info("User deleted", user_id=str(user.id), email=user.email)
    
    return {"message": "User deleted successfully"}


# Project endpoints
@app.get("/projects")
@limiter.limit(f"{settings.security.rate_limit_requests}/minute")
async def list_projects(
    request: Request,
    pagination: PaginationParams = Depends(),
    filters: FilterParams = Depends(),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
):
    """List projects with pagination and filtering."""
    projects = await project_crud.get_multi(db, pagination, filters)
    DB_OPERATIONS.labels(operation="read", table="projects").inc()
    
    return projects


@app.post("/projects", status_code=status.HTTP_201_CREATED)
@limiter.limit(f"{settings.security.rate_limit_requests}/minute")
async def create_project(
    request: Request,
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new project."""
    project = await project_crud.create(db, project_data, owner_id=current_user.id)
    DB_OPERATIONS.labels(operation="create", table="projects").inc()
    
    # Create audit log
    await create_audit_log(
        db,
        entity_type="project",
        entity_id=project.id,
        action="create",
        user_id=current_user.id,
    )
    
    logger.info("Project created", project_id=str(project.id), name=project.name)
    
    return project


@app.get("/projects/{project_id}")
@limiter.limit(f"{settings.security.rate_limit_requests}/minute")
async def get_project(
    request: Request,
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
):
    """Get project by ID."""
    project = await project_crud.get_with_tasks(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    DB_OPERATIONS.labels(operation="read", table="projects").inc()
    
    return project


# Task endpoints  
@app.get("/tasks")
@limiter.limit(f"{settings.security.rate_limit_requests}/minute")
async def list_tasks(
    request: Request,
    pagination: PaginationParams = Depends(),
    filters: FilterParams = Depends(),
    project_id: Optional[uuid.UUID] = None,
    assignee_id: Optional[uuid.UUID] = None,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
):
    """List tasks with filtering options."""
    if project_id:
        tasks = await task_crud.get_by_project(db, project_id)
    elif assignee_id:
        tasks = await task_crud.get_by_assignee(db, assignee_id)
    elif status_filter:
        tasks = await task_crud.get_by_status(db, status_filter)
    else:
        tasks = await task_crud.get_multi(db, pagination, filters)
    
    DB_OPERATIONS.labels(operation="read", table="tasks").inc()
    
    return tasks


@app.post("/tasks", status_code=status.HTTP_201_CREATED)
@limiter.limit(f"{settings.security.rate_limit_requests}/minute")
async def create_task(
    request: Request,
    task_data: TaskCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new task."""
    # Verify project exists and user has access
    project = await project_crud.get(db, task_data.project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    task = await task_crud.create(db, task_data)
    DB_OPERATIONS.labels(operation="create", table="tasks").inc()
    
    # Create audit log
    await create_audit_log(
        db,
        entity_type="task",
        entity_id=task.id,
        action="create",
        user_id=current_user.id,
    )
    
    logger.info("Task created", task_id=str(task.id), title=task.title)
    
    return task


# Agent endpoints
@app.get("/agents")
@limiter.limit(f"{settings.security.rate_limit_requests}/minute")
async def list_agents(
    request: Request,
    pagination: PaginationParams = Depends(),
    agent_type: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
):
    """List agents with filtering options."""
    if agent_type:
        agents = await agent_crud.get_by_type(db, agent_type)
    elif status_filter == "available":
        agents = await agent_crud.get_available(db)
    else:
        agents = await agent_crud.get_multi(db, pagination)
    
    DB_OPERATIONS.labels(operation="read", table="agents").inc()
    
    return agents


@app.post("/agents", status_code=status.HTTP_201_CREATED)
@limiter.limit(f"{settings.security.rate_limit_requests}/minute")
async def create_agent(
    request: Request,
    agent_data: AgentCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_admin_user),
):
    """Create a new agent."""
    agent = await agent_crud.create(db, agent_data)
    DB_OPERATIONS.labels(operation="create", table="agents").inc()
    
    # Create audit log
    await create_audit_log(
        db,
        entity_type="agent",
        entity_id=agent.id,
        action="create",
        user_id=current_user.id,
    )
    
    logger.info("Agent created", agent_id=str(agent.id), name=agent.name, type=agent.type)
    
    return agent


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.app.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    # Run the application
    uvicorn.run(
        "database_agent.__main__:app",
        host=settings.app.host,
        port=settings.app.port,
        log_level=settings.app.log_level.lower(),
        reload=settings.app.debug,
    )