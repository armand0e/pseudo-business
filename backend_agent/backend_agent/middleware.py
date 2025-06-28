"""
Error handling middleware
"""
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Custom error handling middleware"""

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            # Log the exception here if needed
            return JSONResponse(
                status_code=500,
                content={"message": "Internal Server Error", "details": str(exc)},
            )

def add_error_handling_middleware(app):
    """Add error handling middleware to FastAPI app"""
    app.add_middleware(ErrorHandlingMiddleware)