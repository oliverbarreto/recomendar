"""
Domain entities for LabCastARR

Contains all business entities with their core business logic and validation rules.
"""

from .user import User
from .channel import Channel
from .episode import Episode, EpisodeStatus
from .tag import Tag
from .event import Event, EventType, EventStatus
from .followed_channel import FollowedChannel, SubscriptionCheckFrequency
from .youtube_video import YouTubeVideo, YouTubeVideoState
from .user_settings import UserSettings
from .notification import Notification, NotificationType

__all__ = [
    "User",
    "Channel",
    "Episode",
    "EpisodeStatus", 
    "Tag",
    "Event",
    "EventType",
    "EventStatus",
    "FollowedChannel",
    "SubscriptionCheckFrequency",
    "YouTubeVideo",
    "YouTubeVideoState",
    "UserSettings",
    "Notification",
    "NotificationType",
]