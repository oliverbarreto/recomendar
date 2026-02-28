"""
Database models for LabCastARR

This module contains all SQLAlchemy model definitions.
Models are imported here to ensure they are registered with SQLAlchemy.
"""

# Import all models here so they are registered with SQLAlchemy
from .user import UserModel
from .channel import ChannelModel
from .episode import EpisodeModel
from .tag import TagModel, episode_tags
from .event import EventModel
from .followed_channel import FollowedChannelModel
from .youtube_video import YouTubeVideoModel, YouTubeVideoState
from .user_settings import UserSettingsModel, SubscriptionCheckFrequency
from .celery_task_status import CeleryTaskStatusModel
from .notification import NotificationModel

__all__ = [
    "UserModel",
    "ChannelModel", 
    "EpisodeModel",
    "TagModel",
    "EventModel",
    "FollowedChannelModel",
    "YouTubeVideoModel",
    "YouTubeVideoState",
    "UserSettingsModel",
    "SubscriptionCheckFrequency",
    "CeleryTaskStatusModel",
    "NotificationModel",
    "episode_tags",
]