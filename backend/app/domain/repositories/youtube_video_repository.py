"""
YouTubeVideo repository interface

Domain layer interface for YouTube video data access
"""
from abc import abstractmethod
from typing import Optional, List
from datetime import datetime
from app.domain.repositories.base import BaseRepository
from app.domain.entities.youtube_video import YouTubeVideo, YouTubeVideoState


class YouTubeVideoRepository(BaseRepository[YouTubeVideo]):
    """
    Repository interface for YouTubeVideo entities.
    Extends BaseRepository with YouTube video-specific operations.
    """
    
    @abstractmethod
    async def get_by_video_id(self, video_id: str) -> Optional[YouTubeVideo]:
        """
        Get YouTube video by video ID (YouTube video ID, not database ID)
        
        Args:
            video_id: The YouTube video ID to search for
            
        Returns:
            The YouTube video if found, None otherwise
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def get_by_followed_channel_id(
        self,
        followed_channel_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> List[YouTubeVideo]:
        """
        Get YouTube videos by followed channel ID with pagination
        
        Args:
            followed_channel_id: The followed channel ID to filter by
            skip: Number of videos to skip (for pagination)
            limit: Maximum number of videos to return
            
        Returns:
            List of YouTube videos for the channel (may be empty)
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def get_by_state(
        self,
        state: YouTubeVideoState,
        user_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[YouTubeVideo]:
        """
        Get YouTube videos by state with optional user filter
        
        Args:
            state: The video state to filter by
            user_id: Optional user ID to filter by (returns videos from channels followed by user)
            skip: Number of videos to skip (for pagination)
            limit: Maximum number of videos to return
            
        Returns:
            List of YouTube videos with the specified state (may be empty)
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def get_pending_review(
        self,
        user_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[YouTubeVideo]:
        """
        Get videos pending review
        
        Args:
            user_id: Optional user ID to filter by
            skip: Number of videos to skip (for pagination)
            limit: Maximum number of videos to return
            
        Returns:
            List of videos pending review (may be empty)
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def update_state(
        self,
        youtube_video_id: int,
        state: YouTubeVideoState,
        episode_id: Optional[int] = None
    ) -> bool:
        """
        Update video state
        
        Args:
            youtube_video_id: The YouTube video ID
            state: The new state
            episode_id: Optional episode ID to link (required for EPISODE_CREATED state)
            
        Returns:
            True if state was updated, False if video not found
            
        Raises:
            RepositoryError: If update fails
        """
        pass
    
    @abstractmethod
    async def mark_as_reviewed(self, youtube_video_id: int) -> bool:
        """
        Mark video as reviewed
        
        Args:
            youtube_video_id: The YouTube video ID
            
        Returns:
            True if marked as reviewed, False if video not found
            
        Raises:
            RepositoryError: If update fails
        """
        pass
    
    @abstractmethod
    async def mark_as_discarded(self, youtube_video_id: int) -> bool:
        """
        Mark video as discarded
        
        Args:
            youtube_video_id: The YouTube video ID
            
        Returns:
            True if marked as discarded, False if video not found
            
        Raises:
            RepositoryError: If update fails
        """
        pass
    
    @abstractmethod
    async def search(
        self,
        query: str,
        user_id: Optional[int] = None,
        state: Optional[YouTubeVideoState] = None,
        followed_channel_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[YouTubeVideo]:
        """
        Search YouTube videos by title, description, or channel name
        
        Args:
            query: The search query string
            user_id: Optional user ID to filter by (returns videos from channels followed by user)
            state: Optional state to filter by
            followed_channel_id: Optional followed channel ID to filter by
            skip: Number of videos to skip (for pagination)
            limit: Maximum number of videos to return
            
        Returns:
            List of matching videos (may be empty)
            
        Raises:
            RepositoryError: If search fails
        """
        pass
    
    @abstractmethod
    async def get_count_by_state(
        self,
        state: YouTubeVideoState,
        user_id: Optional[int] = None
    ) -> int:
        """
        Get count of videos by state
        
        Args:
            state: The video state to count
            user_id: Optional user ID to filter by
            
        Returns:
            Count of videos with the specified state
            
        Raises:
            RepositoryError: If count fails
        """
        pass
    
    @abstractmethod
    async def get_videos_by_date_range(
        self,
        followed_channel_id: int,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 50
    ) -> List[YouTubeVideo]:
        """
        Get videos published within a date range for a followed channel
        
        Args:
            followed_channel_id: The followed channel ID to filter by
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            skip: Number of videos to skip (for pagination)
            limit: Maximum number of videos to return
            
        Returns:
            List of videos in the date range (may be empty)
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def video_id_exists(self, video_id: str) -> bool:
        """
        Check if a video ID already exists
        
        Args:
            video_id: The YouTube video ID to check
            
        Returns:
            True if video ID exists, False otherwise
            
        Raises:
            RepositoryError: If check fails
        """
        pass
    
    @abstractmethod
    async def delete_pending_videos_for_channel(
        self,
        followed_channel_id: int
    ) -> int:
        """
        Delete all pending/reviewed videos for a followed channel (when unfollowing)
        
        This deletes videos that are not yet converted to episodes.
        Videos with EPISODE_CREATED state are kept.
        
        Args:
            followed_channel_id: The followed channel ID
            
        Returns:
            Number of videos deleted
            
        Raises:
            RepositoryError: If deletion fails
        """
        pass







