"""
Channel Discovery Service Domain Layer

Abstract interface for discovering new videos from followed channels.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.domain.entities.followed_channel import FollowedChannel
from app.domain.entities.youtube_video import YouTubeVideo


class ChannelDiscoveryServiceInterface(ABC):
    """
    Interface for channel discovery service
    
    Provides business logic for discovering new videos from followed channels
    and managing the discovery workflow.
    """
    
    @abstractmethod
    async def discover_new_videos(
        self,
        followed_channel: FollowedChannel,
        max_videos: int = 50
    ) -> List[YouTubeVideo]:
        """
        Discover new videos from a followed channel
        
        This method:
        1. Fetches latest videos from YouTube channel
        2. Compares with existing videos in database
        3. Returns list of new videos that need to be created
        
        Args:
            followed_channel: The followed channel to check
            max_videos: Maximum number of recent videos to check
        
        Returns:
            List of new YouTubeVideo entities (may be empty)
        
        Raises:
            DiscoveryError: If discovery fails
        """
        pass
    
    @abstractmethod
    async def backfill_channel_videos(
        self,
        followed_channel: FollowedChannel,
        max_videos: int = 20,
        year: Optional[int] = None
    ) -> List[YouTubeVideo]:
        """
        Backfill historical videos from a followed channel
        
        This method fetches historical videos and creates YouTubeVideo
        entities for them. Used when first following a channel or
        when user requests backfill for specific years.
        
        Args:
            followed_channel: The followed channel to backfill
            max_videos: Maximum number of videos to fetch
            year: Optional year to filter videos (None for all years)
        
        Returns:
            List of YouTubeVideo entities created (may be empty)
        
        Raises:
            DiscoveryError: If backfill fails
        """
        pass
    
    @abstractmethod
    async def check_for_new_videos_since(
        self,
        followed_channel: FollowedChannel,
        since_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Check for new videos published since a specific date
        
        Args:
            followed_channel: The followed channel to check
            since_date: Date to check from (if None, uses last_checked)
        
        Returns:
            List of video metadata dictionaries for new videos
        
        Raises:
            DiscoveryError: If check fails
        """
        pass







