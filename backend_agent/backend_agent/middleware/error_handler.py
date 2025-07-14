"""
Error Handler Middleware

Global error handling for Backend Agent endpoints.
"""

import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import traceback
from datetime import datetime

from ..models import ErrorResponse

logger = logging.getLogger(__name__)

def setup_error_handlers(app: FastAPI):
    """
    Setup global error handlers for the FastAPI application
    
    Args:
        app: FastAPI application instance
    """
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions"""
        logger.warning(f"HTTP {exc.status_code}: {exc.detail}")
        
        error_response = ErrorResponse(
            error_code=f"HTTP_{exc.status_code}",
            message=exc.detail,
            details={"status_code": exc.status_code}
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.dict()
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle Starlette HTTP exceptions"""
        logger.warning(f"Starlette HTTP {exc.status_code}: {exc.detail}")
        
        error_response = ErrorResponse(
            error_code=f"HTTP_{exc.status_code}",
            message=str(exc.detail),
            details={"status_code": exc.status_code}
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.dict()
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle request validation errors"""
        logger.warning(f"Validation error: {exc.errors()}")
        
        error_response = ErrorResponse(
            error_code="VALIDATION_ERROR",
            message="Request validation failed",
            details={
                "errors": exc.errors(),
                "body": str(exc.body) if hasattr(exc, 'body') else None
            }
        )
        
        return JSONResponse(
            status_code=422,
            content=error_response.dict()
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle general exceptions"""
        logger.error(f"Unhandled exception: {exc}")
        logger.error(traceback.format_exc())
        
        error_response = ErrorResponse(
            error_code="INTERNAL_ERROR",
            message="An internal error occurred",
            details={
                "type": type(exc).__name__,
                "trace_id": str(hash(str(exc) + str(datetime.utcnow())))
            }
        )
        
        return JSONResponse(
            status_code=500,
            content=error_response.dict()
        )

class BackendAgentException(Exception):
    """Base exception for Backend Agent"""
    def __init__(self, message: str, error_code: str = "BACKEND_ERROR", details: dict = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class TaskNotFoundError(BackendAgentException):
    """Task not found error"""
    def __init__(self, task_id: int):
        super().__init__(
            message=f"Task with ID {task_id} not found",
            error_code="TASK_NOT_FOUND",
            details={"task_id": task_id}
        )

class ProjectNotFoundError(BackendAgentException):
    """Project not found error"""
    def __init__(self, project_id: int):
        super().__init__(
            message=f"Project with ID {project_id} not found",
            error_code="PROJECT_NOT_FOUND",
            details={"project_id": project_id}
        )

class AgentUnavailableError(BackendAgentException):
    """Agent unavailable error"""
    def __init__(self, agent_type: str):
        super().__init__(
            message=f"Agent {agent_type} is currently unavailable",
            error_code="AGENT_UNAVAILABLE",
            details={"agent_type": agent_type}
        )

class TaskAssignmentError(BackendAgentException):
    """Task assignment error"""
    def __init__(self, message: str):
        super().__init__(
            message=message,
            error_code="TASK_ASSIGNMENT_ERROR"
        )