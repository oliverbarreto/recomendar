"""
Notification Pydantic schemas for API requests and responses
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


class NotificationResponse(BaseModel):
    """
    Response schema for a single notification
    """
    id: int = Field(..., description="Notification ID")
    user_id: int = Field(..., alias="userId", description="User ID")
    type: str = Field(..., description="Notification type")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    data_json: Optional[Dict[str, Any]] = Field(None, alias="dataJson", description="Additional data")
    read: bool = Field(..., description="Whether notification has been read")
    executed_by: str = Field(default="user", alias="executedBy", description="Who triggered the action: 'user' or 'system'")
    created_at: datetime = Field(..., alias="createdAt", description="Creation timestamp")
    updated_at: datetime = Field(..., alias="updatedAt", description="Update timestamp")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "userId": 1,
                "type": "video_discovered",
                "title": "New videos from Example Channel",
                "message": "5 new videos discovered from Example Channel",
                "dataJson": {
                    "followed_channel_id": 1,
                    "video_count": 5,
                    "channel_name": "Example Channel"
                },
                "read": False,
                "executedBy": "user",
                "createdAt": "2025-11-17T10:00:00Z",
                "updatedAt": "2025-11-17T10:00:00Z"
            }
        }
    )


class NotificationListResponse(BaseModel):
    """
    Response schema for paginated list of notifications
    """
    notifications: List[NotificationResponse] = Field(..., description="List of notifications")
    total: int = Field(..., description="Total number of notifications")
    skip: int = Field(..., description="Number of notifications skipped")
    limit: int = Field(..., description="Maximum number of notifications returned")
    unread_count: int = Field(..., description="Count of unread notifications")
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "notifications": [
                    {
                        "id": 1,
                        "userId": 1,
                        "type": "video_discovered",
                        "title": "New videos from Example Channel",
                        "message": "5 new videos discovered from Example Channel",
                        "dataJson": {"followed_channel_id": 1, "video_count": 5},
                        "read": False,
                        "executedBy": "user",
                        "createdAt": "2025-11-17T10:00:00Z",
                        "updatedAt": "2025-11-17T10:00:00Z"
                    }
                ],
                "total": 10,
                "skip": 0,
                "limit": 20,
                "unread_count": 5
            }
        }
    )


class UnreadCountResponse(BaseModel):
    """
    Response schema for unread notification count
    """
    unread_count: int = Field(..., description="Count of unread notifications")
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "unread_count": 5
            }
        }
    )


class MarkAsReadResponse(BaseModel):
    """
    Response schema for mark as read operations
    """
    success: bool = Field(..., description="Whether operation was successful")
    notification_id: Optional[int] = Field(None, alias="notificationId", description="Notification ID (for single mark)")
    marked_count: Optional[int] = Field(None, alias="markedCount", description="Number marked (for mark all)")
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "success": True,
                "notificationId": 1,
                "markedCount": None
            }
        }
    )


class DeleteNotificationResponse(BaseModel):
    """
    Response schema for delete notification operation
    """
    success: bool = Field(..., description="Whether operation was successful")
    notification_id: int = Field(..., alias="notificationId", description="Deleted notification ID")
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "success": True,
                "notificationId": 1
            }
        }
    )


class DeleteAllNotificationsResponse(BaseModel):
    """
    Response schema for delete all notifications operation
    """
    success: bool = Field(..., description="Whether operation was successful")
    deleted_count: int = Field(..., alias="deletedCount", description="Number of notifications deleted")
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "success": True,
                "deletedCount": 10
            }
        }
    )


