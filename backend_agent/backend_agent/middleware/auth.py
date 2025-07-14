"""
Authentication Middleware

Handles authentication and authorization for Backend Agent endpoints.
Integrates with the API Gateway authentication system.
"""

import jwt
# import httpx
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import logging

# from ..config import settings

logger = logging.getLogger(__name__)
security = HTTPBearer()

class AuthenticationError(Exception):
    """Authentication error exception"""
    pass

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Verify JWT token.
    
    Args:
        credentials: HTTP bearer token credentials
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or verification fails
    """
    # This is a placeholder implementation. In a real application, you would
    # use a secret key from your configuration and potentially an external
    # authentication service.
    try:
        token = credentials.credentials
        # In a real app, use a secret from settings
        payload = jwt.decode(token, "your-secret-key", algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )

async def get_current_user(token_payload: Dict[str, Any] = Depends(verify_token)) -> Dict[str, Any]:
    """
    Get current user from token payload
    
    Args:
        token_payload: Decoded JWT payload
        
    Returns:
        User information
    """
    return {
        "user_id": token_payload.get("user_id"),
        "username": token_payload.get("username"),
        "email": token_payload.get("email"),
        "roles": token_payload.get("roles", [])
    }