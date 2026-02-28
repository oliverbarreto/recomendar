"""
FollowedChannel domain entity

Represents a YouTube channel that a user is following for new video discovery.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class SubscriptionCheckFrequency(Enum):
    """Frequency for checking followed channels for new videos"""
    DAILY = "daily"
    WEEKLY = "weekly"


@dataclass
class FollowedChannel:
    """
    FollowedChannel domain entity representing a YouTube channel subscription
    
    Represents a YouTube channel that a user has subscribed to follow.
    The system will periodically check this channel for new videos.
    """
    id: Optional[int]
    user_id: int
    youtube_channel_id: str  # YouTube channel ID (UCxxxxx or @handle)
    youtube_channel_name: str
    youtube_channel_url: str
    thumbnail_url: Optional[str] = None
    youtube_channel_description: Optional[str] = None

    # Auto-approve settings
    auto_approve: bool = False
    auto_approve_channel_id: Optional[int] = None  # Target podcast channel ID
    
    # Tracking
    last_checked: Optional[datetime] = None  # Timestamp of last check for new videos
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate and initialize followed channel"""
        # Validate required fields
        if self.user_id <= 0:
            raise ValueError("Valid user_id is required")
        
        if not self.youtube_channel_id or len(self.youtube_channel_id.strip()) < 1:
            raise ValueError("YouTube channel ID is required")
        self.youtube_channel_id = self.youtube_channel_id.strip()
        
        if not self.youtube_channel_name or len(self.youtube_channel_name.strip()) < 1:
            raise ValueError("YouTube channel name is required")
        self.youtube_channel_name = self.youtube_channel_name.strip()
        
        if not self.youtube_channel_url or len(self.youtube_channel_url.strip()) < 1:
            raise ValueError("YouTube channel URL is required")
        self.youtube_channel_url = self.youtube_channel_url.strip()
        
        # Validate auto-approve settings
        if self.auto_approve and not self.auto_approve_channel_id:
            raise ValueError("auto_approve_channel_id is required when auto_approve is enabled")
        
        # Set timestamps
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def update_auto_approve(self, auto_approve: bool, auto_approve_channel_id: Optional[int] = None) -> None:
        """
        Update auto-approve settings
        
        Args:
            auto_approve: Enable/disable auto-approve
            auto_approve_channel_id: Target podcast channel ID (required if auto_approve is True)
        """
        if auto_approve and not auto_approve_channel_id:
            raise ValueError("auto_approve_channel_id is required when enabling auto_approve")
        
        self.auto_approve = auto_approve
        self.auto_approve_channel_id = auto_approve_channel_id if auto_approve else None
        self.updated_at = datetime.utcnow()
    
    def update_last_checked(self, last_checked: Optional[datetime] = None) -> None:
        """
        Update the last checked timestamp
        
        Args:
            last_checked: Timestamp to set (defaults to now)
        """
        self.last_checked = last_checked or datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def update_metadata(
        self,
        youtube_channel_name: Optional[str] = None,
        youtube_channel_url: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        youtube_channel_description: Optional[str] = None
    ) -> None:
        """
        Update channel metadata from YouTube

        Args:
            youtube_channel_name: Updated channel name
            youtube_channel_url: Updated channel URL
            thumbnail_url: Updated thumbnail URL
            youtube_channel_description: Updated channel description
        """
        if youtube_channel_name is not None:
            if not youtube_channel_name or len(youtube_channel_name.strip()) < 1:
                raise ValueError("YouTube channel name cannot be empty")
            self.youtube_channel_name = youtube_channel_name.strip()
        
        if youtube_channel_url is not None:
            if not youtube_channel_url or len(youtube_channel_url.strip()) < 1:
                raise ValueError("YouTube channel URL cannot be empty")
            self.youtube_channel_url = youtube_channel_url.strip()
        
        if thumbnail_url is not None:
            self.thumbnail_url = thumbnail_url.strip() if thumbnail_url else None

        if youtube_channel_description is not None:
            self.youtube_channel_description = youtube_channel_description.strip() if youtube_channel_description else None

        self.updated_at = datetime.utcnow()







