"""
Notification API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Annotated, Optional
import logging

from app.core.auth import get_current_user_jwt
from app.application.services.notification_service import NotificationService
from app.infrastructure.repositories.notification_repository_impl import NotificationRepositoryImpl
from app.infrastructure.database.connection import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.presentation.schemas.notification_schemas import (
    NotificationResponse,
    NotificationListResponse,
    UnreadCountResponse,
    MarkAsReadResponse,
    DeleteNotificationResponse,
    DeleteAllNotificationsResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


def get_notification_repository(
    session: AsyncSession = Depends(get_async_db)
) -> NotificationRepositoryImpl:
    """Get notification repository instance"""
    return NotificationRepositoryImpl(session)


def get_notification_service(
    repository: NotificationRepositoryImpl = Depends(get_notification_repository)
) -> NotificationService:
    """Get notification service instance"""
    return NotificationService(repository)


@router.get(
    "/",
    response_model=NotificationListResponse,
    responses={
        401: {"description": "Authentication required"},
        500: {"description": "Internal server error"}
    }
)
async def get_notifications(
    current_user: Annotated[dict, Depends(get_current_user_jwt)],
    notification_service: NotificationService = Depends(get_notification_service),
    skip: int = Query(0, ge=0, description="Number of notifications to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of notifications to return"),
    unread_only: bool = Query(False, description="Return only unread notifications")
) -> NotificationListResponse:
    """
    Get paginated list of notifications for current user
    
    Args:
        current_user: Authenticated user from JWT
        notification_service: Notification service instance
        skip: Number of notifications to skip (for pagination)
        limit: Maximum number of notifications to return
        unread_only: If True, return only unread notifications
        
    Returns:
        Paginated list of notifications with metadata
    """
    try:
        user_id = current_user["user_id"]
        
        # Get notifications with counts
        notifications, total, unread_count = await notification_service.get_user_notifications(
            user_id=user_id,
            skip=skip,
            limit=limit,
            unread_only=unread_only
        )
        
        # Convert to response schemas
        notification_responses = [
            NotificationResponse(
                id=n.id,
                userId=n.user_id,
                type=n.type.value,
                title=n.title,
                message=n.message,
                dataJson=n.data_json,
                read=n.read,
                executedBy=n.executed_by,
                createdAt=n.created_at,
                updatedAt=n.updated_at
            )
            for n in notifications
        ]
        
        return NotificationListResponse(
            notifications=notification_responses,
            total=total,
            skip=skip,
            limit=limit,
            unread_count=unread_count
        )
        
    except Exception as e:
        logger.error(f"Error getting notifications for user {current_user.get('user_id')}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notifications"
        )


@router.get(
    "/unread-count",
    response_model=UnreadCountResponse,
    responses={
        401: {"description": "Authentication required"},
        500: {"description": "Internal server error"}
    }
)
async def get_unread_count(
    current_user: Annotated[dict, Depends(get_current_user_jwt)],
    notification_service: NotificationService = Depends(get_notification_service)
) -> UnreadCountResponse:
    """
    Get count of unread notifications for current user
    
    Args:
        current_user: Authenticated user from JWT
        notification_service: Notification service instance
        
    Returns:
        Count of unread notifications
    """
    try:
        user_id = current_user["user_id"]
        count = await notification_service.get_unread_count(user_id)
        
        return UnreadCountResponse(unread_count=count)
        
    except Exception as e:
        logger.error(f"Error getting unread count for user {current_user.get('user_id')}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve unread count"
        )


@router.put(
    "/{notification_id}/read",
    response_model=MarkAsReadResponse,
    responses={
        401: {"description": "Authentication required"},
        404: {"description": "Notification not found"},
        500: {"description": "Internal server error"}
    }
)
async def mark_notification_as_read(
    notification_id: int,
    current_user: Annotated[dict, Depends(get_current_user_jwt)],
    notification_service: NotificationService = Depends(get_notification_service)
) -> MarkAsReadResponse:
    """
    Mark a notification as read
    
    Args:
        notification_id: ID of notification to mark as read
        current_user: Authenticated user from JWT
        notification_service: Notification service instance
        
    Returns:
        Success response with notification ID
        
    Raises:
        HTTPException: If notification not found or doesn't belong to user
    """
    try:
        user_id = current_user["user_id"]
        
        notification = await notification_service.mark_as_read(
            notification_id=notification_id,
            user_id=user_id
        )
        
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found or access denied"
            )
        
        return MarkAsReadResponse(
            success=True,
            notificationId=notification_id,
            markedCount=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification {notification_id} as read: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notification as read"
        )


@router.put(
    "/mark-all-read",
    response_model=MarkAsReadResponse,
    responses={
        401: {"description": "Authentication required"},
        500: {"description": "Internal server error"}
    }
)
async def mark_all_notifications_as_read(
    current_user: Annotated[dict, Depends(get_current_user_jwt)],
    notification_service: NotificationService = Depends(get_notification_service)
) -> MarkAsReadResponse:
    """
    Mark all notifications as read for current user
    
    Args:
        current_user: Authenticated user from JWT
        notification_service: Notification service instance
        
    Returns:
        Success response with count of notifications marked as read
    """
    try:
        user_id = current_user["user_id"]
        count = await notification_service.mark_all_as_read(user_id)
        
        return MarkAsReadResponse(
            success=True,
            notificationId=None,
            markedCount=count
        )
        
    except Exception as e:
        logger.error(f"Error marking all notifications as read for user {current_user.get('user_id')}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark all notifications as read"
        )


@router.delete(
    "/{notification_id}",
    response_model=DeleteNotificationResponse,
    responses={
        200: {"description": "Notification deleted successfully"},
        401: {"description": "Authentication required"},
        404: {"description": "Notification not found"},
        500: {"description": "Internal server error"}
    }
)
async def delete_notification(
    notification_id: int,
    current_user: Annotated[dict, Depends(get_current_user_jwt)],
    notification_service: NotificationService = Depends(get_notification_service)
) -> DeleteNotificationResponse:
    """
    Delete a notification
    
    Args:
        notification_id: ID of notification to delete
        current_user: Authenticated user from JWT
        notification_service: Notification service instance
        
    Returns:
        Success response with deleted notification ID
        
    Raises:
        HTTPException: If notification not found or doesn't belong to user
    """
    try:
        user_id = current_user["user_id"]
        
        deleted = await notification_service.delete_notification(
            notification_id=notification_id,
            user_id=user_id
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found or access denied"
            )
        
        return DeleteNotificationResponse(
            success=True,
            notificationId=notification_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting notification {notification_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete notification"
        )


@router.delete(
    "/delete-all",
    response_model=DeleteAllNotificationsResponse,
    responses={
        200: {"description": "All notifications deleted successfully"},
        401: {"description": "Authentication required"},
        500: {"description": "Internal server error"}
    }
)
async def delete_all_notifications(
    current_user: Annotated[dict, Depends(get_current_user_jwt)],
    notification_service: NotificationService = Depends(get_notification_service)
) -> DeleteAllNotificationsResponse:
    """
    Delete all notifications for current user
    
    Args:
        current_user: Authenticated user from JWT
        notification_service: Notification service instance
        
    Returns:
        Success response with count of deleted notifications
    """
    try:
        user_id = current_user["user_id"]
        count = await notification_service.delete_all_notifications(user_id)
        
        return DeleteAllNotificationsResponse(
            success=True,
            deletedCount=count
        )
        
    except Exception as e:
        logger.error(f"Error deleting all notifications for user {current_user.get('user_id')}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete all notifications"
        )


