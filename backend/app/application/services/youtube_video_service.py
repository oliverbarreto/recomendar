"""
YouTube Video Application Service

Application service for managing discovered YouTube videos
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.domain.entities.youtube_video import YouTubeVideo, YouTubeVideoState
from app.domain.repositories.youtube_video_repository import YouTubeVideoRepository
from app.domain.repositories.followed_channel_repository import FollowedChannelRepository
from app.domain.repositories.channel import ChannelRepository
from app.infrastructure.tasks.create_episode_from_video_task import create_episode_from_youtube_video
from app.core.logging import get_structured_logger

logger = get_structured_logger("youtube_video_service")


class YouTubeVideoNotFoundError(Exception):
    """Exception raised when YouTube video is not found"""
    pass


class InvalidStateTransitionError(Exception):
    """Exception raised when video state transition is invalid"""
    pass


class YouTubeVideoService:
    """
    Application service for YouTube video management
    
    Handles business logic for managing discovered videos, reviewing them,
    and creating episodes from videos.
    """
    
    def __init__(
        self,
        youtube_video_repository: YouTubeVideoRepository,
        followed_channel_repository: FollowedChannelRepository,
        channel_repository: ChannelRepository
    ):
        """
        Initialize the YouTube video service
        
        Args:
            youtube_video_repository: Repository for YouTube videos
            followed_channel_repository: Repository for followed channels
            channel_repository: Repository for podcast channels
        """
        self.youtube_video_repository = youtube_video_repository
        self.followed_channel_repository = followed_channel_repository
        self.channel_repository = channel_repository
    
    async def get_pending_videos(
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
            List of YouTubeVideo entities with PENDING_REVIEW state
        """
        try:
            videos = await self.youtube_video_repository.get_pending_review(
                user_id=user_id,
                skip=skip,
                limit=limit
            )
            return videos
        except Exception as e:
            logger.error(f"Failed to get pending videos: {e}")
            raise
    
    async def get_videos_by_state(
        self,
        state: YouTubeVideoState,
        user_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[YouTubeVideo]:
        """
        Get videos by state
        
        Args:
            state: Video state to filter by
            user_id: Optional user ID to filter by
            skip: Number of videos to skip (for pagination)
            limit: Maximum number of videos to return
        
        Returns:
            List of YouTubeVideo entities with the specified state
        """
        try:
            videos = await self.youtube_video_repository.get_by_state(
                state=state,
                user_id=user_id,
                skip=skip,
                limit=limit
            )
            return videos
        except Exception as e:
            logger.error(f"Failed to get videos by state {state.value}: {e}")
            raise
    
    async def get_videos_by_channel(
        self,
        followed_channel_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> List[YouTubeVideo]:
        """
        Get videos by followed channel
        
        Args:
            followed_channel_id: ID of the followed channel
            skip: Number of videos to skip (for pagination)
            limit: Maximum number of videos to return
        
        Returns:
            List of YouTubeVideo entities for the channel
        """
        try:
            videos = await self.youtube_video_repository.get_by_followed_channel_id(
                followed_channel_id=followed_channel_id,
                skip=skip,
                limit=limit
            )
            return videos
        except Exception as e:
            logger.error(f"Failed to get videos for channel {followed_channel_id}: {e}")
            raise
    
    async def get_video(self, youtube_video_id: int, user_id: Optional[int] = None) -> Optional[YouTubeVideo]:
        """
        Get a specific YouTube video
        
        Args:
            youtube_video_id: ID of the YouTube video
            user_id: Optional user ID to verify ownership (checks if video belongs to user's followed channels)
        
        Returns:
            YouTubeVideo entity if found, None otherwise
        
        Raises:
            YouTubeVideoNotFoundError: If video not found or doesn't belong to user
        """
        try:
            video = await self.youtube_video_repository.get_by_id(youtube_video_id)
            
            if not video:
                raise YouTubeVideoNotFoundError(f"YouTube video {youtube_video_id} not found")
            
            # Verify ownership if user_id provided
            if user_id:
                followed_channel = await self.followed_channel_repository.get_by_id(video.followed_channel_id)
                if not followed_channel or followed_channel.user_id != user_id:
                    raise YouTubeVideoNotFoundError(
                        f"YouTube video {youtube_video_id} does not belong to user {user_id}"
                    )
            
            return video
            
        except YouTubeVideoNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get YouTube video {youtube_video_id}: {e}")
            raise
    
    async def mark_as_reviewed(self, youtube_video_id: int, user_id: int) -> YouTubeVideo:
        """
        Mark a video as reviewed
        
        Args:
            youtube_video_id: ID of the YouTube video
            user_id: ID of the user (for verification)
        
        Returns:
            Updated YouTubeVideo entity
        
        Raises:
            YouTubeVideoNotFoundError: If video not found or doesn't belong to user
            InvalidStateTransitionError: If state transition is invalid
        """
        try:
            # Get and verify video
            video = await self.get_video(youtube_video_id, user_id)
            
            # Mark as reviewed
            video.mark_as_reviewed()
            
            # Save to repository
            updated = await self.youtube_video_repository.update(video)
            
            logger.info(f"Marked video {youtube_video_id} as reviewed")
            return updated
            
        except (YouTubeVideoNotFoundError, InvalidStateTransitionError):
            raise
        except Exception as e:
            logger.error(f"Failed to mark video {youtube_video_id} as reviewed: {e}")
            raise
    
    async def mark_as_discarded(self, youtube_video_id: int, user_id: int) -> YouTubeVideo:
        """
        Mark a video as discarded
        
        Args:
            youtube_video_id: ID of the YouTube video
            user_id: ID of the user (for verification)
        
        Returns:
            Updated YouTubeVideo entity
        
        Raises:
            YouTubeVideoNotFoundError: If video not found or doesn't belong to user
            InvalidStateTransitionError: If state transition is invalid
        """
        try:
            # Get and verify video
            video = await self.get_video(youtube_video_id, user_id)
            
            # Mark as discarded
            video.mark_as_discarded()
            
            # Save to repository
            updated = await self.youtube_video_repository.update(video)
            
            logger.info(f"Marked video {youtube_video_id} as discarded")
            return updated
            
        except (YouTubeVideoNotFoundError, InvalidStateTransitionError):
            raise
        except Exception as e:
            logger.error(f"Failed to mark video {youtube_video_id} as discarded: {e}")
            raise
    
    async def create_episode_from_video(
        self,
        youtube_video_id: int,
        channel_id: int,
        user_id: int,
        audio_language: Optional[str] = None,
        audio_quality: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create an episode from a YouTube video
        
        This method:
        1. Verifies video and channel ownership
        2. Verifies video can be used to create episode
        3. Queues episode creation task
        4. Updates video state
        
        Args:
            youtube_video_id: ID of the YouTube video
            channel_id: ID of the podcast channel to create episode in
            user_id: ID of the user (for verification)
        
        Returns:
            Dictionary with task information
        
        Raises:
            YouTubeVideoNotFoundError: If video not found or doesn't belong to user
            InvalidStateTransitionError: If video cannot be used to create episode
        """
        try:
            # Get and verify video
            video = await self.get_video(youtube_video_id, user_id)
            
            # Verify video can be used to create episode
            if not video.can_create_episode():
                raise InvalidStateTransitionError(
                    f"Video {youtube_video_id} cannot be used to create episode from state {video.state.value}"
                )
            
            # Verify channel exists and belongs to user
            channel = await self.channel_repository.get_by_id(channel_id)
            if not channel:
                raise ValueError(f"Channel {channel_id} not found")
            
            # Verify channel belongs to user
            if channel.user_id != user_id:
                raise ValueError(f"Channel {channel_id} does not belong to user {user_id}")
            
            # Queue episode creation task - use apply_async with explicit args/kwargs to avoid Celery serialization issues
            task_result = create_episode_from_youtube_video.apply_async(
                args=(youtube_video_id, channel_id),
                kwargs={
                    'audio_language': audio_language,
                    'audio_quality': audio_quality
                }
            )
            
            logger.info(f"Queued episode creation from video {youtube_video_id} for channel {channel_id}")
            
            return {
                "status": "queued",
                "task_id": task_result.id,
                "youtube_video_id": youtube_video_id,
                "channel_id": channel_id,
                "message": "Episode creation queued successfully"
            }
            
        except (YouTubeVideoNotFoundError, InvalidStateTransitionError):
            raise
        except Exception as e:
            logger.error(f"Failed to create episode from video {youtube_video_id}: {e}")
            raise
    
    async def search_videos(
        self,
        query: str,
        user_id: Optional[int] = None,
        state: Optional[YouTubeVideoState] = None,
        followed_channel_id: Optional[int] = None,
        publish_year: Optional[int] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[YouTubeVideo]:
        """
        Search YouTube videos by title or description
        
        Args:
            query: Search query string
            user_id: Optional user ID to filter by
            state: Optional state to filter by
            followed_channel_id: Optional followed channel ID to filter by
            publish_year: Optional year to filter by (e.g., 2024)
            skip: Number of videos to skip (for pagination)
            limit: Maximum number of videos to return
        
        Returns:
            List of matching YouTubeVideo entities
        """
        try:
            videos = await self.youtube_video_repository.search(
                query=query,
                user_id=user_id,
                state=state,
                followed_channel_id=followed_channel_id,
                publish_year=publish_year,
                skip=skip,
                limit=limit
            )
            return videos
        except Exception as e:
            logger.error(f"Failed to search videos with query '{query}': {e}")
            raise
    
    async def get_pending_count(self, user_id: Optional[int] = None) -> int:
        """
        Get count of videos pending review
        
        Args:
            user_id: Optional user ID to filter by
        
        Returns:
            Count of pending videos
        """
        try:
            count = await self.youtube_video_repository.get_count_by_state(
                state=YouTubeVideoState.PENDING_REVIEW,
                user_id=user_id
            )
            return count
        except Exception as e:
            logger.error(f"Failed to get pending video count: {e}")
            raise
    
    async def bulk_mark_as_reviewed(
        self,
        video_ids: List[int],
        user_id: int
    ) -> List[Dict[str, Any]]:
        """
        Mark multiple videos as reviewed
        
        Args:
            video_ids: List of video IDs to mark as reviewed
            user_id: ID of the user (for verification)
        
        Returns:
            List of results with success/failure for each video
        """
        results = []
        for video_id in video_ids:
            try:
                await self.mark_as_reviewed(video_id, user_id)
                results.append({
                    "video_id": video_id,
                    "success": True,
                    "error": None
                })
            except Exception as e:
                results.append({
                    "video_id": video_id,
                    "success": False,
                    "error": str(e)
                })
        return results
    
    async def bulk_discard(
        self,
        video_ids: List[int],
        user_id: int
    ) -> List[Dict[str, Any]]:
        """
        Mark multiple videos as discarded
        
        Args:
            video_ids: List of video IDs to discard
            user_id: ID of the user (for verification)
        
        Returns:
            List of results with success/failure for each video
        """
        results = []
        for video_id in video_ids:
            try:
                await self.mark_as_discarded(video_id, user_id)
                results.append({
                    "video_id": video_id,
                    "success": True,
                    "error": None
                })
            except Exception as e:
                results.append({
                    "video_id": video_id,
                    "success": False,
                    "error": str(e)
                })
        return results
    
    async def bulk_create_episodes(
        self,
        video_ids: List[int],
        channel_id: int,
        user_id: int,
        audio_language: Optional[str] = None,
        audio_quality: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Create episodes from multiple videos

        Args:
            video_ids: List of video IDs to create episodes from
            channel_id: ID of the podcast channel
            user_id: ID of the user (for verification)
            audio_language: Preferred audio language (ISO 639-1)
            audio_quality: Preferred audio quality tier

        Returns:
            List of results with success/failure and task IDs for each video
        """
        results = []
        for video_id in video_ids:
            try:
                result = await self.create_episode_from_video(
                    video_id, channel_id, user_id,
                    audio_language=audio_language,
                    audio_quality=audio_quality
                )
                results.append({
                    "video_id": video_id,
                    "success": True,
                    "error": None,
                    "task_id": result.get("task_id")
                })
            except Exception as e:
                results.append({
                    "video_id": video_id,
                    "success": False,
                    "error": str(e),
                    "task_id": None
                })
        return results
    
    async def get_channel_video_stats(
        self,
        followed_channel_id: int,
        user_id: int
    ) -> Dict[str, int]:
        """
        Get video statistics for a specific followed channel
        
        Args:
            followed_channel_id: ID of the followed channel
            user_id: ID of the user (for ownership verification)
        
        Returns:
            Dictionary with counts for each state:
            - pending_review: Number of videos pending review
            - reviewed: Number of reviewed videos
            - queued: Number of queued videos
            - downloading: Number of videos being downloaded
            - episode_created: Number of videos with episodes created
            - discarded: Number of discarded videos
            - total: Total number of videos
        
        Raises:
            ValueError: If channel not found or doesn't belong to user
        """
        try:
            # Verify the channel exists and belongs to the user
            followed_channel = await self.followed_channel_repository.get_by_id(followed_channel_id)
            
            if not followed_channel:
                raise ValueError(f"Followed channel {followed_channel_id} not found")
            
            if followed_channel.user_id != user_id:
                raise ValueError(f"Followed channel {followed_channel_id} does not belong to user {user_id}")
            
            # Get stats from repository
            stats = await self.youtube_video_repository.get_stats_by_followed_channel(followed_channel_id)
            
            logger.info(f"Retrieved video stats for channel {followed_channel_id}: {stats}")
            
            return stats
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to get video stats for channel {followed_channel_id}: {e}")
            raise

