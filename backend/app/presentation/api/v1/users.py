"""
User management API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.infrastructure.database.connection import get_async_db
from app.infrastructure.repositories.user_repository import UserRepositoryImpl
from app.core.jwt import verify_password, get_password_hash, validate_password_strength
from app.core.auth import get_current_user_jwt
from app.core.dependencies import UserSettingsServiceDep
from app.application.services.user_settings_service import UserSettingsService
from app.domain.entities.followed_channel import SubscriptionCheckFrequency
from app.presentation.schemas.auth_schemas import (
    UserProfileResponse,
    ChangePasswordRequest,
    UpdateProfileRequest,
    AuthErrorResponse
)
from app.presentation.schemas.user_settings_schemas import (
    UserSettingsResponse,
    UserSettingsUpdateRequest,
    SubscriptionCheckFrequencyEnum,
)
from zoneinfo import available_timezones

router = APIRouter(prefix="/users", tags=["user-management"])


@router.get(
    "/profile",
    response_model=UserProfileResponse,
    responses={
        401: {"model": AuthErrorResponse, "description": "Authentication required"},
        404: {"model": AuthErrorResponse, "description": "User not found"}
    }
)
async def get_user_profile(
    current_user: Annotated[dict, Depends(get_current_user_jwt)],
    session: Annotated[AsyncSession, Depends(get_async_db)]
) -> UserProfileResponse:
    """
    Get current user's profile information

    Args:
        current_user: Current authenticated user
        session: Database session

    Returns:
        User profile information

    Raises:
        HTTPException: If user not found
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


@router.put(
    "/profile",
    response_model=UserProfileResponse,
    responses={
        401: {"model": AuthErrorResponse, "description": "Authentication required"},
        404: {"model": AuthErrorResponse, "description": "User not found"},
        409: {"model": AuthErrorResponse, "description": "Email already exists"},
        422: {"model": AuthErrorResponse, "description": "Validation error"}
    }
)
async def update_user_profile(
    profile_update: UpdateProfileRequest,
    current_user: Annotated[dict, Depends(get_current_user_jwt)],
    session: Annotated[AsyncSession, Depends(get_async_db)]
) -> UserProfileResponse:
    """
    Update current user's profile information

    Args:
        profile_update: Profile update data
        current_user: Current authenticated user
        session: Database session

    Returns:
        Updated user profile

    Raises:
        HTTPException: If validation fails or user not found
    """
    user_repo = UserRepositoryImpl(session)
    user = await user_repo.get_by_id(current_user["user_id"])

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if email is being changed and is available
    if profile_update.email and profile_update.email != user.email:
        if await user_repo.email_exists(profile_update.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email address is already registered"
            )

    # Update user profile
    try:
        user.update_profile(
            name=profile_update.name,
            email=profile_update.email
        )

        updated_user = await user_repo.update(user)
        await session.commit()

        return UserProfileResponse(
            id=updated_user.id,
            name=updated_user.name,
            email=updated_user.email,
            is_admin=updated_user.is_admin,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


@router.put(
    "/password",
    responses={
        200: {"description": "Password changed successfully"},
        401: {"model": AuthErrorResponse, "description": "Authentication required"},
        400: {"model": AuthErrorResponse, "description": "Invalid current password"},
        422: {"model": AuthErrorResponse, "description": "Validation error"}
    }
)
async def change_password(
    password_change: ChangePasswordRequest,
    current_user: Annotated[dict, Depends(get_current_user_jwt)],
    session: Annotated[AsyncSession, Depends(get_async_db)]
) -> dict:
    """
    Change current user's password

    Args:
        password_change: Password change data
        current_user: Current authenticated user
        session: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If validation fails or current password is incorrect
    """
    user_repo = UserRepositoryImpl(session)

    # Validate that new passwords match
    if not password_change.validate_passwords_match():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="New password and confirmation do not match"
        )

    # Validate password strength
    is_valid, error_message = validate_password_strength(password_change.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_message
        )

    # Get current user
    user = await user_repo.get_by_id(current_user["user_id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Verify current password
    if not verify_password(password_change.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Update password
    try:
        user.update_password(password_change.new_password)
        await user_repo.update(user)
        await session.commit()

        return {
            "message": "Password changed successfully",
            "timestamp": user.updated_at.isoformat()
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@router.get(
    "/me",
    response_model=UserProfileResponse,
    responses={
        401: {"model": AuthErrorResponse, "description": "Authentication required"}
    }
)
async def get_current_user_me(
    current_user: Annotated[dict, Depends(get_current_user_jwt)],
    session: Annotated[AsyncSession, Depends(get_async_db)]
) -> UserProfileResponse:
    """
    Get current user information (alias for /profile)

    Args:
        current_user: Current authenticated user
        session: Database session

    Returns:
        User profile information
    """
    return await get_user_profile(current_user, session)


@router.get(
    "/settings",
    response_model=UserSettingsResponse,
    responses={
        401: {"model": AuthErrorResponse, "description": "Authentication required"},
    }
)
async def get_user_settings(
    current_user: Annotated[dict, Depends(get_current_user_jwt)],
    user_settings_service: UserSettingsServiceDep,
) -> UserSettingsResponse:
    """
    Get current user's settings
    
    Returns user preferences including subscription check frequency.
    Creates default settings if they don't exist.
    """
    try:
        settings = await user_settings_service.get_user_settings(
            user_id=current_user["user_id"]
        )
        
        return UserSettingsResponse.model_validate(settings)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user settings: {str(e)}"
        )


@router.put(
    "/settings",
    response_model=UserSettingsResponse,
    responses={
        401: {"model": AuthErrorResponse, "description": "Authentication required"},
        400: {"model": AuthErrorResponse, "description": "Validation error"},
    }
)
async def update_user_settings(
    request: UserSettingsUpdateRequest,
    current_user: Annotated[dict, Depends(get_current_user_jwt)],
    user_settings_service: UserSettingsServiceDep,
) -> UserSettingsResponse:
    """
    Update current user's settings

    Updates user preferences including subscription check frequency and preferred check time.
    """
    try:
        # Validate and convert frequency if provided
        frequency = None
        if request.subscription_check_frequency:
            frequency_map = {
                SubscriptionCheckFrequencyEnum.DAILY: SubscriptionCheckFrequency.DAILY,
                SubscriptionCheckFrequencyEnum.WEEKLY: SubscriptionCheckFrequency.WEEKLY,
            }
            frequency = frequency_map.get(request.subscription_check_frequency)

            if not frequency:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid subscription check frequency: {request.subscription_check_frequency}"
                )

        # Validate time if provided
        if (request.preferred_check_hour is not None) != (request.preferred_check_minute is not None):
            # If only one is provided, raise error
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both preferred_check_hour and preferred_check_minute must be provided together"
            )

        # Get current settings
        settings = await user_settings_service.get_user_settings(
            user_id=current_user["user_id"]
        )

        # Update frequency if provided
        if frequency:
            settings = await user_settings_service.update_subscription_frequency(
                user_id=current_user["user_id"],
                frequency=frequency
            )

        # Update check time if provided
        if request.preferred_check_hour is not None and request.preferred_check_minute is not None:
            settings = await user_settings_service.update_check_time(
                user_id=current_user["user_id"],
                hour=request.preferred_check_hour,
                minute=request.preferred_check_minute
            )

        # Update timezone if provided
        if request.timezone:
            settings = await user_settings_service.update_timezone(
                user_id=current_user["user_id"],
                timezone=request.timezone
            )

        return UserSettingsResponse.model_validate(settings)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user settings: {str(e)}"
        )


@router.get(
    "/timezones",
    response_model=list[str],
    responses={
        401: {"model": AuthErrorResponse, "description": "Authentication required"},
    }
)
async def get_available_timezones(
    current_user: Annotated[dict, Depends(get_current_user_jwt)],
) -> list[str]:
    """
    Get list of available IANA timezones

    Returns a sorted list of all valid timezone identifiers that can be used
    for the timezone setting.

    Returns:
        List of IANA timezone strings (e.g., ['America/New_York', 'Europe/Madrid', ...])
    """
    try:
        # Get all available timezones and sort them
        timezones = sorted(available_timezones())
        return timezones
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get available timezones: {str(e)}"
        )