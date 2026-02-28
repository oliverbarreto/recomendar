"""
FollowedChannel repository interface

Domain layer interface for followed channel data access
"""
from abc import abstractmethod
from typing import Optional, List
from datetime import datetime
from app.domain.repositories.base import BaseRepository
from app.domain.entities.followed_channel import FollowedChannel


class FollowedChannelRepository(BaseRepository[FollowedChannel]):
    """
    Repository interface for FollowedChannel entities.
    Extends BaseRepository with followed channel-specific operations.
    """
    
    @abstractmethod
    async def get_by_user_id(self, user_id: int) -> List[FollowedChannel]:
        """
        Get all followed channels for a user
        
        Args:
            user_id: The user ID to filter by
            
        Returns:
            List of followed channels for the user (may be empty)
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def get_by_youtube_channel_id(
        self,
        youtube_channel_id: str,
        user_id: Optional[int] = None
    ) -> Optional[FollowedChannel]:
        """
        Get followed channel by YouTube channel ID
        
        Args:
            youtube_channel_id: The YouTube channel ID to search for
            user_id: Optional user ID to filter by (checks if specific user follows the channel)
            
        Returns:
            The followed channel if found, None otherwise
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def get_by_user_and_youtube_channel_id(
        self,
        user_id: int,
        youtube_channel_id: str
    ) -> Optional[FollowedChannel]:
        """
        Get followed channel by user ID and YouTube channel ID (unique combination)
        
        Args:
            user_id: The user ID
            youtube_channel_id: The YouTube channel ID
            
        Returns:
            The followed channel if found, None otherwise
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def get_channels_to_check(
        self,
        user_frequency: str,
        last_check_before: Optional[datetime] = None
    ) -> List[FollowedChannel]:
        """
        Get followed channels that need to be checked based on user's check frequency
        
        Args:
            user_frequency: User's subscription check frequency (daily, twice_weekly, weekly)
            last_check_before: Optional datetime threshold - only return channels
                last checked before this time (or never checked)
            
        Returns:
            List of followed channels that need checking
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def update_last_checked(
        self,
        followed_channel_id: int,
        last_checked: Optional[datetime] = None
    ) -> bool:
        """
        Update the last checked timestamp for a followed channel
        
        Args:
            followed_channel_id: The followed channel ID
            last_checked: Timestamp to set (defaults to now)
            
        Returns:
            True if updated, False if channel not found
            
        Raises:
            RepositoryError: If update fails
        """
        pass
    
    @abstractmethod
    async def update_auto_approve_settings(
        self,
        followed_channel_id: int,
        auto_approve: bool,
        auto_approve_channel_id: Optional[int] = None
    ) -> bool:
        """
        Update auto-approve settings for a followed channel
        
        Args:
            followed_channel_id: The followed channel ID
            auto_approve: Enable/disable auto-approve
            auto_approve_channel_id: Target podcast channel ID (required if auto_approve is True)
            
        Returns:
            True if updated, False if channel not found
            
        Raises:
            RepositoryError: If update fails
        """
        pass







