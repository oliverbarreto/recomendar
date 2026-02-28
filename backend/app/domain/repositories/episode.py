"""
Episode repository interface
"""
from abc import abstractmethod
from datetime import datetime
from typing import List, Optional
from app.domain.repositories.base import BaseRepository
from app.domain.entities.episode import Episode, EpisodeStatus
from app.domain.value_objects.video_id import VideoId

class EpisodeRepository(BaseRepository[Episode]):
    """
    Repository interface for Episode entities.
    Extends BaseRepository with episode-specific operations.
    """
    
    @abstractmethod
    async def find_by_video_id(self, video_id: VideoId) -> Optional[Episode]:
        """
        Find an episode by YouTube video ID
        
        Args:
            video_id: The YouTube video ID to search for
            
        Returns:
            The episode if found, None otherwise
            
        Raises:
            RepositoryError: If search fails
        """
        pass
    
    @abstractmethod
    async def find_by_channel(self, channel_id: int, skip: int = 0, limit: int = 50) -> List[Episode]:
        """
        Find episodes by channel with pagination
        
        Args:
            channel_id: The channel ID to filter by
            skip: Number of episodes to skip (for pagination)
            limit: Maximum number of episodes to return
            
        Returns:
            List of episodes for the channel (may be empty)
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def find_by_status(self, status: EpisodeStatus) -> List[Episode]:
        """
        Find episodes by processing status
        
        Args:
            status: The episode status to filter by
            
        Returns:
            List of episodes with the specified status (may be empty)
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def search(self, query: str, channel_id: int, skip: int = 0, limit: int = 50) -> List[Episode]:
        """
        Search episodes by title, description, or keywords
        
        Args:
            query: The search query string
            channel_id: The channel ID to search within
            skip: Number of episodes to skip (for pagination)
            limit: Maximum number of episodes to return
            
        Returns:
            List of matching episodes (may be empty)
            
        Raises:
            RepositoryError: If search fails
        """
        pass
    
    @abstractmethod
    async def update_status(self, episode_id: int, status: EpisodeStatus) -> bool:
        """
        Update episode processing status
        
        Args:
            episode_id: The episode ID
            status: The new status
            
        Returns:
            True if status was updated, False if episode not found
            
        Raises:
            RepositoryError: If update fails
        """
        pass
    
    @abstractmethod
    async def increment_retry_count(self, episode_id: int) -> bool:
        """
        Increment retry count for failed episode downloads
        
        Args:
            episode_id: The episode ID
            
        Returns:
            True if retry count was incremented, False if episode not found
            
        Raises:
            RepositoryError: If update fails
        """
        pass
    
    @abstractmethod
    async def get_failed_episodes(self, max_retries: int = 3) -> List[Episode]:
        """
        Get episodes that have failed processing and are under retry limit
        
        Args:
            max_retries: Maximum number of retries allowed
            
        Returns:
            List of failed episodes eligible for retry (may be empty)
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def get_episodes_by_date_range(
        self, 
        channel_id: int, 
        start_date: datetime, 
        end_date: datetime,
        skip: int = 0,
        limit: int = 50
    ) -> List[Episode]:
        """
        Get episodes published within a date range for a channel
        
        Args:
            channel_id: The channel ID to filter by
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            skip: Number of episodes to skip (for pagination)
            limit: Maximum number of episodes to return
            
        Returns:
            List of episodes in the date range (may be empty)
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def video_id_exists(self, video_id: VideoId, channel_id: int) -> bool:
        """
        Check if a video ID already exists for a channel
        
        Args:
            video_id: The video ID to check
            channel_id: The channel ID to check within
            
        Returns:
            True if video ID exists for the channel, False otherwise
            
        Raises:
            RepositoryError: If check fails
        """
        pass
    
    @abstractmethod
    async def bulk_update_status(self, episode_ids: List[int], status: EpisodeStatus) -> int:
        """
        Update status for multiple episodes
        
        Args:
            episode_ids: List of episode IDs to update
            status: The new status for all episodes
            
        Returns:
            Number of episodes updated
            
        Raises:
            RepositoryError: If bulk update fails
        """
        pass