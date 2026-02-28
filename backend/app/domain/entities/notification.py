"""
Notification Domain Entity

Represents a user notification for various system events.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class NotificationType(str, Enum):
    """
    Notification type enum
    
    Types:
        VIDEO_DISCOVERED: New videos found from a followed channel
        EPISODE_CREATED: Episode successfully created from a video
        CHANNEL_SEARCH_STARTED: Search for new videos has started
        CHANNEL_SEARCH_COMPLETED: Search for new videos completed successfully
        CHANNEL_SEARCH_ERROR: Search for new videos failed
    """
    VIDEO_DISCOVERED = "video_discovered"
    EPISODE_CREATED = "episode_created"
    CHANNEL_SEARCH_STARTED = "channel_search_started"
    CHANNEL_SEARCH_COMPLETED = "channel_search_completed"
    CHANNEL_SEARCH_ERROR = "channel_search_error"


@dataclass
class Notification:
    """
    Domain entity for user notifications

    Attributes:
        id: Database ID
        user_id: ID of user who receives the notification
        type: Type of notification (video discovered, episode created, etc.)
        title: Notification title
        message: Notification message/description
        data_json: Additional structured data (JSON object)
        read: Whether notification has been read
        executed_by: Who triggered the action ('user' or 'system')
        created_at: Notification creation timestamp
        updated_at: Last update timestamp
    """
    user_id: int
    type: NotificationType
    title: str
    message: str
    id: Optional[int] = None
    data_json: Optional[Dict[str, Any]] = None
    read: bool = False
    executed_by: str = 'user'
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize timestamps and validate fields"""
        # Set timestamps if not provided
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

        # Validate user_id
        if self.user_id <= 0:
            raise ValueError("User ID must be positive")

        # Validate title and message
        if not self.title or not self.title.strip():
            raise ValueError("Notification title cannot be empty")
        if not self.message or not self.message.strip():
            raise ValueError("Notification message cannot be empty")

        # Validate executed_by
        if self.executed_by not in ('user', 'system'):
            raise ValueError("executed_by must be either 'user' or 'system'")

        # Ensure data_json is a dict
        if self.data_json is None:
            self.data_json = {}
    
    def mark_as_read(self) -> None:
        """Mark notification as read"""
        self.read = True
        self.updated_at = datetime.utcnow()
    
    def mark_as_unread(self) -> None:
        """Mark notification as unread"""
        self.read = False
        self.updated_at = datetime.utcnow()
    
    def is_read(self) -> bool:
        """Check if notification has been read"""
        return self.read



