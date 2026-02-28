"""
Authentication API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.infrastructure.database.connection import get_async_db
from app.infrastructure.repositories.user_repository import UserRepositoryImpl
from app.core.jwt import get_jwt_service, verify_password, validate_password_strength
from app.application.services.event_service import EventService
from app.domain.entities.event import EventSeverity
from app.presentation.schemas.auth_schemas import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    LogoutRequest,
    UserProfileResponse,
    ChangePasswordRequest,
    UpdateProfileRequest,
    AuthErrorResponse,
    TokenValidationResponse
)
from app.core.auth import get_current_user_jwt

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/login",
    response_model=LoginResponse,
    responses={
        401: {"model": AuthErrorResponse, "description": "Invalid credentials"},
        422: {"model": AuthErrorResponse, "description": "Validation error"}
    }
)
async def login(
    credentials: LoginRequest,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_async_db)]
) -> LoginResponse:
    """
    Authenticate user and return JWT tokens

    Args:
        credentials: User login credentials
        session: Database session

    Returns:
        JWT tokens and user profile

    Raises:
        HTTPException: If authentication fails
    """
    user_repo = UserRepositoryImpl(session)

    # Find user by email
    user = await user_repo.find_by_email(credentials.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Verify password
    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Create token pair
    additional_claims = {
        "email": user.email,
        "is_admin": user.is_admin
    }

    # Extend refresh token expiration for "remember me"
    if credentials.remember_me:
        additional_claims["remember_me"] = True

    jwt_service = get_jwt_service()
    tokens = jwt_service.create_token_pair(user.id, additional_claims, remember_me=credentials.remember_me)

    # Log successful login event
    try:
        event_service = EventService(session)

        # Get client information
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        await event_service.log_user_action(
            channel_id=1,  # Default channel for now
            user_id=user.id,
            action="login",
            resource_type="auth",
            resource_id=None,
            message=f"User {user.email} logged in successfully",
            details={
                "remember_me": credentials.remember_me,
                "user_email": user.email,
                "is_admin": user.is_admin,
                "token_type": tokens["token_type"]
            },
            severity=EventSeverity.INFO,
            ip_address=client_ip,
            user_agent=user_agent
        )
    except Exception as e:
        # Don't fail login if event logging fails
        pass

    # Return response
    return LoginResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        expires_in=tokens["expires_in"],
        user=UserProfileResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            is_admin=user.is_admin,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    )


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    responses={
        401: {"model": AuthErrorResponse, "description": "Invalid refresh token"},
        422: {"model": AuthErrorResponse, "description": "Validation error"}
    }
)
async def refresh_token(
    request: RefreshTokenRequest
) -> RefreshTokenResponse:
    """
    Refresh access token using refresh token

    Args:
        request: Refresh token request

    Returns:
        New access token

    Raises:
        HTTPException: If refresh token is invalid
    """
    # Verify refresh token
    jwt_service = get_jwt_service()
    payload = jwt_service.verify_token(request.refresh_token, token_type="refresh")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    # Extract claims from refresh token for token rotation
    additional_claims = {
        "email": payload.get("email"),
        "is_admin": payload.get("is_admin", False)
    }
    
    # Preserve remember_me claim if present
    remember_me = payload.get("remember_me", False)
    if remember_me:
        additional_claims["remember_me"] = True

    from datetime import datetime, timezone, timedelta
    from app.core.config import settings

    # Create sliding access token for better UX
    access_token = jwt_service.create_sliding_token({
        "sub": str(user_id),  # JWT 'sub' claim must be a string
        "jti": f"{user_id}_{datetime.now(timezone.utc).timestamp()}",
        **additional_claims
    })

    # Create new refresh token with same claims (token rotation)
    # This extends the refresh token expiration with each refresh
    base_claims = {
        "sub": str(user_id),
        **additional_claims
    }
    
    # Use extended expiration if remember_me is True
    if remember_me:
        refresh_expire_delta = timedelta(days=settings.jwt_refresh_token_extended_expire_days)
        new_refresh_token = jwt_service.create_refresh_token(base_claims, expires_delta=refresh_expire_delta)
    else:
        new_refresh_token = jwt_service.create_refresh_token(base_claims)

    return RefreshTokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=jwt_service.access_token_expire_minutes * 60
    )


@router.post(
    "/refresh-sliding",
    response_model=RefreshTokenResponse,
    responses={
        401: {"model": AuthErrorResponse, "description": "Invalid or non-sliding token"},
        422: {"model": AuthErrorResponse, "description": "Validation error"}
    }
)
async def refresh_sliding_token(
    current_user: Annotated[dict, Depends(get_current_user_jwt)]
) -> RefreshTokenResponse:
    """
    Refresh sliding token based on activity
    
    This endpoint extends the token expiration for active users,
    providing seamless session continuation without re-authentication.

    Args:
        current_user: Current authenticated user (validates existing token)

    Returns:
        New access token with extended expiration

    Raises:
        HTTPException: If token is invalid or not a sliding token
    """
    jwt_service = get_jwt_service()
    
    # Get the current token from the request
    current_token = current_user.get("token")
    if not current_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No token provided"
        )
    
    # Refresh the sliding token
    new_token = jwt_service.refresh_sliding_token(current_token)
    if not new_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is not a sliding token or is invalid"
        )
    
    return RefreshTokenResponse(
        access_token=new_token,
        token_type="bearer",
        expires_in=jwt_service.access_token_expire_minutes * 60
    )


@router.post(
    "/logout",
    responses={
        200: {"description": "Successfully logged out"},
        401: {"model": AuthErrorResponse, "description": "Invalid token"}
    }
)
async def logout(
    logout_request: LogoutRequest,
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user_jwt)],
    session: Annotated[AsyncSession, Depends(get_async_db)]
) -> dict:
    """
    Logout user by blacklisting tokens

    Args:
        request: Logout request with optional refresh token
        current_user: Current authenticated user

    Returns:
        Success message
    """
    # The access token is automatically blacklisted by the dependency
    success_count = 1

    # Also blacklist refresh token if provided
    if logout_request.refresh_token:
        jwt_service = get_jwt_service()
        if jwt_service.blacklist_token(logout_request.refresh_token):
            success_count += 1

    # Log successful logout event
    try:
        event_service = EventService(session)

        # Get client information
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        await event_service.log_user_action(
            channel_id=1,  # Default channel for now
            user_id=current_user["user_id"],
            action="logout",
            resource_type="auth",
            resource_id=None,
            message=f"User {current_user.get('email', 'unknown')} logged out successfully",
            details={
                "tokens_invalidated": success_count,
                "user_email": current_user.get("email"),
                "is_admin": current_user.get("is_admin", False)
            },
            severity=EventSeverity.INFO,
            ip_address=client_ip,
            user_agent=user_agent
        )
    except Exception as e:
        # Don't fail logout if event logging fails
        pass

    return {
        "message": "Successfully logged out",
        "tokens_invalidated": success_count
    }


@router.get(
    "/me",
    response_model=UserProfileResponse,
    responses={
        401: {"model": AuthErrorResponse, "description": "Authentication required"}
    }
)
async def get_current_user_profile(
    current_user: Annotated[dict, Depends(get_current_user_jwt)],
    session: Annotated[AsyncSession, Depends(get_async_db)]
) -> UserProfileResponse:
    """
    Get current user profile

    Args:
        current_user: Current authenticated user
        session: Database session

    Returns:
        User profile information
    """
    user_repo = UserRepositoryImpl(session)
    user = await user_repo.get_by_id(current_user["user_id"])

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserProfileResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        is_admin=user.is_admin,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@router.post(
    "/validate-token",
    response_model=TokenValidationResponse,
    responses={
        200: {"description": "Token validation result"}
    }
)
async def validate_token(
    token: str
) -> TokenValidationResponse:
    """
    Validate JWT token (utility endpoint)

    Args:
        token: JWT token to validate

    Returns:
        Token validation result
    """
    jwt_service = get_jwt_service()
    payload = jwt_service.verify_token(token)

    if payload:
        from datetime import datetime, timezone
        expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

        return TokenValidationResponse(
            valid=True,
            user_id=payload.get("sub"),
            expires_at=expires_at
        )
    else:
        return TokenValidationResponse(
            valid=False,
            user_id=None,
            expires_at=None
        )


@router.get(
    "/debug-jwt",
    responses={
        200: {"description": "JWT service debug information"}
    }
)
async def debug_jwt_service() -> dict:
    """
    Debug endpoint to verify JWT service configuration
    """
    import hashlib
    from datetime import datetime, timezone
    jwt_service = get_jwt_service()

    # Get secret key hash for debugging
    secret_hash = hashlib.md5(jwt_service.secret_key.encode()).hexdigest()[:10]
    instance_id = hex(id(jwt_service))

    return {
        "instance_id": instance_id,
        "secret_key_hash": secret_hash,
        "secret_key_length": len(jwt_service.secret_key),
        "algorithm": jwt_service.algorithm,
        "access_token_expire_minutes": jwt_service.access_token_expire_minutes,
        "refresh_token_expire_days": jwt_service.refresh_token_expire_days,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }