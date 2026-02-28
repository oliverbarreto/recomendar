"""
Authentication and security utilities
"""
import secrets
from typing import Optional
from fastapi import HTTPException, Security, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings


# API Key authentication
api_key_header = APIKeyHeader(
    name=settings.api_key_header,
    auto_error=False
)

# Shortcut API Key authentication
shortcut_api_key_header = APIKeyHeader(
    name=settings.shortcut_api_key_header,
    auto_error=False
)

# Bearer token authentication for future use
bearer_security = HTTPBearer(auto_error=False)


def generate_api_key() -> str:
    """Generate a secure API key"""
    return secrets.token_urlsafe(32)


def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> bool:
    """
    Verify API key authentication
    
    Args:
        api_key: API key from header
        
    Returns:
        bool: True if authentication is valid
        
    Raises:
        HTTPException: If authentication fails
    """
    # Skip authentication if disabled in settings
    if not settings.enable_api_key_auth:
        return True
    
    # Skip authentication if no API key is configured
    if not settings.api_key_secret:
        return True
    
    # Check if API key is provided
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={settings.api_key_header: "Required"},
        )
    
    # Verify API key
    if api_key != settings.api_key_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    
    return True


def get_current_user(
    api_key: Optional[str] = Security(api_key_header),
    bearer_token: Optional[HTTPAuthorizationCredentials] = Security(bearer_security)
) -> dict:
    """
    Get current authenticated user (placeholder for future user system)
    
    Args:
        api_key: API key from header
        bearer_token: Bearer token from header
        
    Returns:
        dict: User information
    """
    # For now, just verify API key
    verify_api_key(api_key)
    
    # Return a default user for now
    return {
        "id": "system",
        "username": "api_user",
        "permissions": ["read", "write"]
    }


def require_api_key(api_key: Optional[str] = Security(api_key_header)) -> bool:
    """
    Dependency that requires API key authentication
    """
    return verify_api_key(api_key)


async def get_current_user_jwt(
    bearer_token: Optional[HTTPAuthorizationCredentials] = Security(bearer_security)
) -> dict:
    """
    Get current authenticated user via JWT token

    Args:
        bearer_token: Bearer token from Authorization header

    Returns:
        dict: User information from JWT

    Raises:
        HTTPException: If authentication fails
    """
    from app.core.jwt import get_jwt_service
    from app.infrastructure.database.connection import get_async_db
    from app.infrastructure.repositories.user_repository import UserRepositoryImpl

    if not bearer_token or not bearer_token.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify JWT token
    jwt_service = get_jwt_service()
    payload = jwt_service.verify_token(bearer_token.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Blacklist current token on logout (if this is a logout request)
    # The token blacklisting is handled in the logout endpoint

    return {
        "user_id": int(user_id),  # Convert back to int for application use
        "email": payload.get("email"),
        "is_admin": payload.get("is_admin", False),
        "token": bearer_token.credentials
    }


def require_jwt_auth(current_user: dict = Depends(get_current_user_jwt)) -> dict:
    """
    Dependency that requires JWT authentication
    """
    return current_user


def require_admin(current_user: dict = Depends(get_current_user_jwt)) -> dict:
    """
    Dependency that requires admin privileges
    """
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


def verify_shortcut_key(shortcut_key: Optional[str] = Security(shortcut_api_key_header)) -> bool:
    """
    Verify iOS Shortcut API key authentication

    This is a separate authentication mechanism specifically for iOS Shortcuts,
    allowing users to add episodes via the Share Sheet without exposing the main API key.

    Args:
        shortcut_key: Shortcut API key from X-Shortcut-Key header

    Returns:
        bool: True if authentication is valid

    Raises:
        HTTPException: If authentication fails
    """
    # Check if shortcut API key is configured
    if not settings.shortcut_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Shortcut API is not configured",
        )

    # Check if shortcut key is provided
    if not shortcut_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Shortcut API key required",
            headers={settings.shortcut_api_key_header: "Required"},
        )

    # Verify shortcut API key
    if shortcut_key != settings.shortcut_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid shortcut API key",
        )

    return True


def require_shortcut_key(shortcut_key: Optional[str] = Security(shortcut_api_key_header)) -> bool:
    """
    Dependency that requires iOS Shortcut API key authentication
    """
    return verify_shortcut_key(shortcut_key)