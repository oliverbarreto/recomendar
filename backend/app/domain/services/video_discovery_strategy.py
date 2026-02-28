"""
Video Discovery Strategy Interface

This module defines the abstract interface for video discovery strategies.
Different strategies can implement different methods for discovering new videos
(e.g., yt-dlp full scan, RSS feed, YouTube API, etc.)
"""

from abc import ABC, abstractmethod
from typing import List

from app.domain.entities.followed_channel import FollowedChannel
from app.domain.entities.youtube_video import YouTubeVideo


class VideoDiscoveryStrategy(ABC):
    """Abstract interface for video discovery strategies"""

    @abstractmethod
    async def discover_new_videos(
        self,
        followed_channel: FollowedChannel,
        max_videos: int = 50
    ) -> List[YouTubeVideo]:
        """
        Discover new videos from a followed channel.

        Args:
            followed_channel: The channel to check for new videos
            max_videos: Maximum number of videos to retrieve (may be ignored by some strategies)

        Returns:
            List of new YouTubeVideo entities (not yet persisted to database)

        Raises:
            Exception: If discovery fails
        """
        pass
