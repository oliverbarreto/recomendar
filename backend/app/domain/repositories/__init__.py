"""
Domain repository interfaces for LabCastARR

This module contains all repository interface definitions following the Repository pattern.
These interfaces define the contract for data access operations without specifying
the implementation details.

All repository interfaces extend BaseRepository and provide domain-specific operations.
Implementations of these interfaces will be found in the infrastructure layer.
"""

# Base repository interface
from .base import BaseRepository

# Domain-specific repository interfaces
from .user import UserRepository
from .channel import ChannelRepository
from .episode import EpisodeRepository
from .tag import TagRepository
from .event import EventRepository
from .followed_channel_repository import FollowedChannelRepository
from .youtube_video_repository import YouTubeVideoRepository
from .user_settings_repository import UserSettingsRepository

__all__ = [
    "BaseRepository",
    "UserRepository", 
    "ChannelRepository",
    "EpisodeRepository",
    "TagRepository",
    "EventRepository",
    "FollowedChannelRepository",
    "YouTubeVideoRepository",
    "UserSettingsRepository",
]