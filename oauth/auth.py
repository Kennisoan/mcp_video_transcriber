"""
JWT Authentication and Authorization for OAuth 2.1
"""

import jwt
from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import Config

security = HTTPBearer()


def create_access_token(subject: str, scopes: list, expires_minutes: int = None) -> str:
    """
    Create a JWT access token

    Args:
        subject: The client_id or user identifier
        scopes: List of granted scopes
        expires_minutes: Token expiration time (defaults to config value)

    Returns:
        Encoded JWT token string
    """
    if expires_minutes is None:
        expires_minutes = Config.JWT_EXPIRES_MINUTES

    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    payload = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.utcnow(),
        "iss": Config.SERVER_URL,
        "aud": Config.SERVER_URL,
        "scope": " ".join(scopes),
        "token_use": "access"
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm="HS256")


def verify_access_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode a JWT access token

    Args:
        token: JWT token string

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            Config.JWT_SECRET,
            algorithms=["HS256"],
            audience=Config.SERVER_URL
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    FastAPI dependency to get current authenticated user from JWT token

    Args:
        credentials: HTTP Bearer token from request

    Returns:
        Decoded token payload with user information
    """
    return verify_access_token(credentials.credentials)


def check_scope(required_scope: str, user_scopes: str) -> bool:
    """
    Check if user has required scope

    Args:
        required_scope: The scope required for the operation
        user_scopes: Space-separated string of user's granted scopes

    Returns:
        True if user has the required scope
    """
    user_scope_list = user_scopes.split() if user_scopes else []
    return required_scope in user_scope_list


def require_scope(required_scope: str):
    """
    Decorator factory to require specific OAuth scope

    Args:
        required_scope: The scope required for the decorated function

    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # This would be used with FastAPI dependencies
            # Implementation depends on how you want to inject user context
            pass
        return wrapper
    return decorator
