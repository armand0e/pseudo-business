"""API Gateway Module

This module provides the API Gateway for handling HTTP requests, authentication,
routing, and load balancing for the Agentic AI Development Platform.
"""

from typing import Dict, List, Any, Optional, Callable
from fastapi import FastAPI, HTTPException, Depends, Request, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import time
import jwt
import hashlib
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio
from collections import defaultdict

from src.infrastructure.logging_system import LoggingSystem

_logging_system = LoggingSystem()
logger = _logging_system.get_logger()

# Pydantic models for API requests/responses
class ProjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)

class TaskCreateRequest(BaseModel):
    task_id: str = Field(..., min_length=1, max_length=255)
    project_id: int = Field(..., gt=0)
    description: str = Field(..., min_length=1)
    agent_type: str = Field(..., min_length=1)
    priority: int = Field(default=1, ge=1, le=10)

class AgentRegisterRequest(BaseModel):
    agent_id: str = Field(..., min_length=1, max_length=255)
    agent_type: str = Field(..., min_length=1)
    capabilities: List[str] = Field(default=[])

class AuthRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)

class APIResponse(BaseModel):
    success: bool
    data: Any = None
    message: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)

@dataclass
class RateLimitInfo:
    """Rate limiting information."""
    requests: int = 0
    window_start: float = 0.0
    blocked_until: float = 0.0

@_logging_system.error_handler
class APIGateway:
    """API Gateway for handling HTTP requests and routing."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the API Gateway.

        Args:
            config (Dict[str, Any]): Configuration for the API Gateway.
        """
        logger.info("Initializing API Gateway")
        self.config = config
        self.app = FastAPI(
            title="Agentic AI Development Platform API",
            description="API Gateway for the Agentic AI Development Platform",
            version="1.0.0"
        )
        
        # Security configuration
        self.security = HTTPBearer()
        self.jwt_secret = config.get('jwt_secret', 'default-secret-key')
        self.jwt_algorithm = config.get('jwt_algorithm', 'HS256')
        self.jwt_expiry_hours = config.get('jwt_expiry_hours', 24)
        
        # Rate limiting
        self.rate_limits = defaultdict(RateLimitInfo)
        self.rate_limit_config = config.get('rate_limiting', {})
        self.max_requests_per_minute = self.rate_limit_config.get('max_requests_per_minute', 100)
        
        # CORS configuration
        self.cors_config = config.get('cors', {})
        
        # Initialize middleware and routes
        self._setup_middleware()
        self._setup_routes()
        
        # Backend services (to be injected)
        self.database_agent = None
        self.master_orchestrator = None

    def set_dependencies(self, database_agent=None, master_orchestrator=None):
        """
        Set dependencies for the API Gateway.

        Args:
            database_agent: Database agent instance.
            master_orchestrator: Master orchestrator instance.
        """
        logger.info("Setting API Gateway dependencies")
        self.database_agent = database_agent
        self.master_orchestrator = master_orchestrator

    def _setup_middleware(self):
        """Setup middleware for the FastAPI application."""
        logger.info("Setting up API Gateway middleware")
        
        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.cors_config.get('allowed_origins', ["*"]),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Trusted host middleware
        allowed_hosts = self.config.get('allowed_hosts', ["*"])
        if allowed_hosts != ["*"]:
            self.app.add_middleware(
                TrustedHostMiddleware,
                allowed_hosts=allowed_hosts
            )
        
        # Custom middleware
        @self.app.middleware("http")
        async def rate_limiting_middleware(request: Request, call_next):
            # Get client IP
            client_ip = request.client.host
            
            # Check rate limiting
            if not self._check_rate_limit(client_ip):
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Rate limit exceeded"}
                )
            
            # Process request
            start_time = time.time()
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Add custom headers
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-API-Version"] = "1.0.0"
            
            logger.debug(f"Request to {request.url.path} took {process_time:.3f}s")
            return response

    def _check_rate_limit(self, client_ip: str) -> bool:
        """
        Check if client has exceeded rate limit.

        Args:
            client_ip (str): Client IP address.

        Returns:
            bool: True if within rate limit, False otherwise.
        """
        current_time = time.time()
        rate_info = self.rate_limits[client_ip]
        
        # Check if still blocked
        if current_time < rate_info.blocked_until:
            return False
        
        # Reset window if needed
        window_duration = 60  # 1 minute
        if current_time - rate_info.window_start > window_duration:
            rate_info.requests = 0
            rate_info.window_start = current_time
        
        # Check rate limit
        rate_info.requests += 1
        if rate_info.requests > self.max_requests_per_minute:
            rate_info.blocked_until = current_time + window_duration
            return False
        
        return True

    def _setup_routes(self):
        """Setup API routes."""
        logger.info("Setting up API Gateway routes")
        
        # Health check
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            health_status = {
                "api_gateway": "healthy",
                "database": "unknown",
                "master_orchestrator": "unknown"
            }
            
            if self.database_agent:
                health_status["database"] = "healthy" if self.database_agent.health_check() else "unhealthy"
            
            return APIResponse(
                success=True,
                data=health_status,
                message="Health check completed"
            )

        # Authentication endpoints
        @self.app.post("/auth/login")
        async def login(auth_request: AuthRequest):
            """User authentication endpoint."""
            logger.info(f"Login attempt for user: {auth_request.username}")
            
            # Simple authentication (in production, use proper user management)
            if self._authenticate_user(auth_request.username, auth_request.password):
                token = self._generate_jwt_token(auth_request.username)
                logger.info(f"Login successful for user: {auth_request.username}")
                
                return APIResponse(
                    success=True,
                    data={"token": token, "expires_in": self.jwt_expiry_hours * 3600},
                    message="Login successful"
                )
            else:
                logger.warning(f"Login failed for user: {auth_request.username}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )

        @self.app.post("/auth/refresh")
        async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(self.security)):
            """Refresh JWT token."""
            try:
                payload = jwt.decode(credentials.credentials, self.jwt_secret, algorithms=[self.jwt_algorithm])
                username = payload.get("sub")
                
                new_token = self._generate_jwt_token(username)
                logger.info(f"Token refreshed for user: {username}")
                
                return APIResponse(
                    success=True,
                    data={"token": new_token, "expires_in": self.jwt_expiry_hours * 3600},
                    message="Token refreshed"
                )
            except jwt.ExpiredSignatureError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expired"
                )
            except jwt.JWTError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )

        # Project management endpoints
        @self.app.post("/projects")
        async def create_project(
            project_request: ProjectCreateRequest,
            current_user: dict = Depends(self._get_current_user)
        ):
            """Create a new project."""
            logger.info(f"Creating project: {project_request.name}")
            
            if not self.database_agent:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Database service unavailable"
                )
            
            result = self.database_agent.create_project(
                name=project_request.name,
                description=project_request.description
            )
            
            if result.success:
                logger.info(f"Project created successfully: {project_request.name}")
                return APIResponse(
                    success=True,
                    data=result.data,
                    message="Project created successfully"
                )
            else:
                logger.error(f"Failed to create project: {result.error}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )

        @self.app.get("/projects")
        async def list_projects(current_user: dict = Depends(self._get_current_user)):
            """List all projects."""
            logger.debug("Listing projects")
            
            if not self.database_agent:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Database service unavailable"
                )
            
            # This would need to be implemented in the database agent
            return APIResponse(
                success=True,
                data=[],
                message="Projects retrieved successfully"
            )

        # Task management endpoints
        @self.app.post("/tasks")
        async def create_task(
            task_request: TaskCreateRequest,
            current_user: dict = Depends(self._get_current_user)
        ):
            """Create a new task."""
            logger.info(f"Creating task: {task_request.task_id}")
            
            if not self.database_agent:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Database service unavailable"
                )
            
            result = self.database_agent.create_task(
                task_id=task_request.task_id,
                project_id=task_request.project_id,
                description=task_request.description,
                agent_type=task_request.agent_type,
                priority=task_request.priority
            )
            
            if result.success:
                logger.info(f"Task created successfully: {task_request.task_id}")
                return APIResponse(
                    success=True,
                    data=result.data,
                    message="Task created successfully"
                )
            else:
                logger.error(f"Failed to create task: {result.error}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )

        @self.app.get("/tasks")
        async def list_tasks(
            agent_type: Optional[str] = None,
            current_user: dict = Depends(self._get_current_user)
        ):
            """List pending tasks."""
            logger.debug(f"Listing tasks for agent type: {agent_type}")
            
            if not self.database_agent:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Database service unavailable"
                )
            
            result = self.database_agent.get_pending_tasks(agent_type=agent_type)
            
            if result.success:
                return APIResponse(
                    success=True,
                    data=result.data,
                    message="Tasks retrieved successfully"
                )
            else:
                logger.error(f"Failed to retrieve tasks: {result.error}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )

        # Agent management endpoints
        @self.app.post("/agents")
        async def register_agent(
            agent_request: AgentRegisterRequest,
            current_user: dict = Depends(self._get_current_user)
        ):
            """Register a new agent."""
            logger.info(f"Registering agent: {agent_request.agent_id}")
            
            if not self.database_agent:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Database service unavailable"
                )
            
            result = self.database_agent.register_agent(
                agent_id=agent_request.agent_id,
                agent_type=agent_request.agent_type,
                capabilities=agent_request.capabilities
            )
            
            if result.success:
                logger.info(f"Agent registered successfully: {agent_request.agent_id}")
                return APIResponse(
                    success=True,
                    data=result.data,
                    message="Agent registered successfully"
                )
            else:
                logger.error(f"Failed to register agent: {result.error}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )

        @self.app.get("/agents/{agent_id}/status")
        async def get_agent_status(
            agent_id: str,
            current_user: dict = Depends(self._get_current_user)
        ):
            """Get agent status."""
            logger.debug(f"Getting status for agent: {agent_id}")
            
            if self.master_orchestrator:
                status_info = self.master_orchestrator.get_agent_status(agent_id)
                return APIResponse(
                    success=True,
                    data=status_info,
                    message="Agent status retrieved"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Master orchestrator unavailable"
                )

    def _authenticate_user(self, username: str, password: str) -> bool:
        """
        Authenticate a user (simplified implementation).

        Args:
            username (str): Username.
            password (str): Password.

        Returns:
            bool: True if authentication successful.
        """
        # In production, this should use proper password hashing and user database
        default_users = self.config.get('default_users', {
            'admin': 'admin123',
            'developer': 'dev123'
        })
        
        return username in default_users and default_users[username] == password

    def _generate_jwt_token(self, username: str) -> str:
        """
        Generate JWT token for authenticated user.

        Args:
            username (str): Username.

        Returns:
            str: JWT token.
        """
        payload = {
            "sub": username,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=self.jwt_expiry_hours)
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    async def _get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
        """
        Get current authenticated user from JWT token.

        Args:
            credentials: HTTP authorization credentials.

        Returns:
            dict: User information.
        """
        try:
            payload = jwt.decode(credentials.credentials, self.jwt_secret, algorithms=[self.jwt_algorithm])
            username = payload.get("sub")
            
            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
            
            return {"username": username}
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

    def get_app(self) -> FastAPI:
        """Get the FastAPI application instance."""
        return self.app

    async def startup(self):
        """Startup tasks for the API Gateway."""
        logger.info("API Gateway starting up")
        # Any initialization tasks

    async def shutdown(self):
        """Shutdown tasks for the API Gateway."""
        logger.info("API Gateway shutting down")
        # Any cleanup tasks