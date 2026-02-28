"""
Followed Channel Application Service

Application service for managing followed YouTube channels and subscriptions
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.domain.entities.followed_channel import FollowedChannel
from app.domain.entities.celery_task_status import CeleryTaskStatus, TaskStatus
from app.domain.repositories.followed_channel_repository import FollowedChannelRepository
from app.domain.repositories.youtube_video_repository import YouTubeVideoRepository
from app.domain.services.youtube_metadata_service import YouTubeMetadataServiceInterface
from app.domain.services.channel_discovery_service import ChannelDiscoveryServiceInterface
from app.infrastructure.repositories.celery_task_status_repository_impl import CeleryTaskStatusRepository
from app.infrastructure.tasks.channel_check_tasks import check_followed_channel_for_new_videos
from app.infrastructure.tasks.backfill_channel_task import backfill_followed_channel
from app.core.logging import get_structured_logger

logger = get_structured_logger("followed_channel_service")


class FollowedChannelNotFoundError(Exception):
    """Exception raised when followed channel is not found"""
    pass


class DuplicateChannelError(Exception):
    """Exception raised when channel is already being followed"""
    pass


class InvalidChannelURLError(Exception):
    """Exception raised when channel URL is invalid"""
    pass


class FollowedChannelService:
    """
    Application service for followed channel management
    
    Handles business logic for following YouTube channels, discovering videos,
    and managing subscription settings.
    """
    
    def __init__(
        self,
        followed_channel_repository: FollowedChannelRepository,
        youtube_video_repository: YouTubeVideoRepository,
        metadata_service: YouTubeMetadataServiceInterface,
        discovery_service: ChannelDiscoveryServiceInterface,
        task_status_repository: CeleryTaskStatusRepository
    ):
        """
        Initialize the followed channel service
        
        Args:
            followed_channel_repository: Repository for followed channels
            youtube_video_repository: Repository for YouTube videos
            metadata_service: Service for extracting YouTube metadata
            discovery_service: Service for discovering videos
            task_status_repository: Repository for Celery task status tracking
        """
        self.followed_channel_repository = followed_channel_repository
        self.youtube_video_repository = youtube_video_repository
        self.metadata_service = metadata_service
        self.discovery_service = discovery_service
        self.task_status_repository = task_status_repository
    
    async def follow_channel(
        self,
        user_id: int,
        channel_url: str,
        auto_approve: bool = False,
        auto_approve_channel_id: Optional[int] = None
    ) -> FollowedChannel:
        """
        Follow a YouTube channel
        
        This method:
        1. Extracts channel metadata from YouTube
        2. Checks if channel is already being followed
        3. Creates FollowedChannel entity
        4. Triggers initial backfill task
        
        Args:
            user_id: ID of the user following the channel
            channel_url: YouTube channel URL (supports various formats)
            auto_approve: Enable auto-approve for new videos
            auto_approve_channel_id: Target podcast channel ID for auto-approval
        
        Returns:
            Created FollowedChannel entity
        
        Raises:
            DuplicateChannelError: If channel is already being followed
            InvalidChannelURLError: If URL is invalid
        """
        try:
            logger.info(f"Following channel for user {user_id}: {channel_url}")
            
            # Extract channel metadata from YouTube
            channel_metadata = await self.metadata_service.extract_channel_info(channel_url)
            
            if not channel_metadata or not channel_metadata.get("channel_id"):
                raise InvalidChannelURLError(f"Could not extract channel information from URL: {channel_url}")
            
            youtube_channel_id = channel_metadata["channel_id"]
            
            # Check if channel is already being followed by this user
            existing = await self.followed_channel_repository.get_by_user_and_youtube_channel_id(
                user_id=user_id,
                youtube_channel_id=youtube_channel_id
            )
            
            if existing:
                logger.warning(f"Channel {youtube_channel_id} already being followed by user {user_id}")
                raise DuplicateChannelError(
                    f"YouTube channel '{channel_metadata.get('name', 'Unknown')}' is already being followed"
                )
            
            # Create FollowedChannel entity
            followed_channel = FollowedChannel(
                id=None,
                user_id=user_id,
                youtube_channel_id=youtube_channel_id,
                youtube_channel_name=channel_metadata.get("name") or "Unknown Channel",
                youtube_channel_url=channel_metadata.get("url") or channel_url,
                thumbnail_url=channel_metadata.get("thumbnail_url"),
                youtube_channel_description=channel_metadata.get("description"),
                auto_approve=auto_approve,
                auto_approve_channel_id=auto_approve_channel_id if auto_approve else None
            )
            
            # Save to repository
            created_channel = await self.followed_channel_repository.create(followed_channel)
            
            logger.info(f"Successfully followed channel {created_channel.id}: {created_channel.youtube_channel_name}")
            
        except (DuplicateChannelError, InvalidChannelURLError):
            raise
        except Exception as e:
            logger.error(f"Failed to follow channel {channel_url}: {e}", exc_info=True)
            raise
        
        # Trigger initial backfill task (last 20 videos of current year)
        # This is done AFTER the main try-except to prevent Celery errors from failing the follow operation
        try:
            current_year = datetime.now().year
            # Use apply_async with explicit args/kwargs to avoid Celery serialization issues
            task_result = backfill_followed_channel.apply_async(
                args=(created_channel.id, current_year, 20),
                kwargs={}
            )
            logger.info(
                f"Queued initial backfill for channel {created_channel.id}",
                extra={"task_id": task_result.id if task_result else None}
            )
        except Exception as e:
            # Log the error but don't fail the follow operation
            logger.error(
                f"Failed to queue backfill task for channel {created_channel.id}: {e}",
                exc_info=True
            )
            # Continue - the channel is already followed, backfill can be triggered manually
        
        return created_channel
    
    async def unfollow_channel(self, followed_channel_id: int, user_id: int) -> bool:
        """
        Unfollow a YouTube channel
        
        This method:
        1. Verifies the channel belongs to the user
        2. Deletes all pending/reviewed videos for the channel
        3. Deletes the FollowedChannel entity
        4. Keeps episodes that were already created
        
        Args:
            followed_channel_id: ID of the followed channel
            user_id: ID of the user (for verification)
        
        Returns:
            True if channel was unfollowed, False if not found
        
        Raises:
            FollowedChannelNotFoundError: If channel not found or doesn't belong to user
        """
        try:
            logger.info(f"Unfollowing channel {followed_channel_id} for user {user_id}")
            
            # Get followed channel and verify ownership
            followed_channel = await self.followed_channel_repository.get_by_id(followed_channel_id)
            
            if not followed_channel:
                raise FollowedChannelNotFoundError(f"Followed channel {followed_channel_id} not found")
            
            if followed_channel.user_id != user_id:
                raise FollowedChannelNotFoundError(
                    f"Followed channel {followed_channel_id} does not belong to user {user_id}"
                )
            
            # Delete all pending/reviewed videos (keep episode_created ones)
            deleted_count = await self.youtube_video_repository.delete_pending_videos_for_channel(
                followed_channel_id=followed_channel_id
            )
            logger.info(f"Deleted {deleted_count} pending videos for channel {followed_channel_id}")
            
            # Delete the followed channel
            deleted = await self.followed_channel_repository.delete(followed_channel_id)
            
            if deleted:
                logger.info(f"Successfully unfollowed channel {followed_channel_id}")
            
            return deleted
            
        except FollowedChannelNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to unfollow channel {followed_channel_id}: {e}", exc_info=True)
            raise
    
    async def get_followed_channels(self, user_id: int) -> List[FollowedChannel]:
        """
        Get all followed channels for a user
        
        Args:
            user_id: ID of the user
        
        Returns:
            List of FollowedChannel entities
        """
        try:
            channels = await self.followed_channel_repository.get_by_user_id(user_id)
            return channels
        except Exception as e:
            logger.error(f"Failed to get followed channels for user {user_id}: {e}")
            raise
    
    async def get_followed_channel(self, followed_channel_id: int, user_id: int) -> Optional[FollowedChannel]:
        """
        Get a specific followed channel
        
        Args:
            followed_channel_id: ID of the followed channel
            user_id: ID of the user (for verification)
        
        Returns:
            FollowedChannel entity if found and belongs to user, None otherwise
        
        Raises:
            FollowedChannelNotFoundError: If channel not found or doesn't belong to user
        """
        try:
            followed_channel = await self.followed_channel_repository.get_by_id(followed_channel_id)
            
            if not followed_channel:
                raise FollowedChannelNotFoundError(f"Followed channel {followed_channel_id} not found")
            
            if followed_channel.user_id != user_id:
                raise FollowedChannelNotFoundError(
                    f"Followed channel {followed_channel_id} does not belong to user {user_id}"
                )
            
            return followed_channel
            
        except FollowedChannelNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get followed channel {followed_channel_id}: {e}")
            raise
    
    async def update_auto_approve_settings(
        self,
        followed_channel_id: int,
        user_id: int,
        auto_approve: bool,
        auto_approve_channel_id: Optional[int] = None
    ) -> FollowedChannel:
        """
        Update auto-approve settings for a followed channel
        
        Args:
            followed_channel_id: ID of the followed channel
            user_id: ID of the user (for verification)
            auto_approve: Enable/disable auto-approve
            auto_approve_channel_id: Target podcast channel ID (required if auto_approve is True)
        
        Returns:
            Updated FollowedChannel entity
        
        Raises:
            FollowedChannelNotFoundError: If channel not found or doesn't belong to user
        """
        try:
            # Get and verify channel
            followed_channel = await self.get_followed_channel(followed_channel_id, user_id)
            
            # Update auto-approve settings
            followed_channel.update_auto_approve(
                auto_approve=auto_approve,
                auto_approve_channel_id=auto_approve_channel_id
            )
            
            # Save to repository
            updated = await self.followed_channel_repository.update(followed_channel)
            
            logger.info(f"Updated auto-approve settings for channel {followed_channel_id}: {auto_approve}")
            return updated
            
        except FollowedChannelNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to update auto-approve settings for channel {followed_channel_id}: {e}")
            raise

    async def update_channel_metadata(
        self,
        followed_channel_id: int,
        user_id: int
    ) -> FollowedChannel:
        """
        Update channel metadata from YouTube

        Fetches fresh metadata from YouTube and updates the followed channel
        with new name, URL, thumbnail, and description.

        Args:
            followed_channel_id: ID of the followed channel
            user_id: ID of the user (for verification)

        Returns:
            Updated FollowedChannel entity

        Raises:
            FollowedChannelNotFoundError: If channel not found or doesn't belong to user
            InvalidChannelURLError: If fetching metadata from YouTube fails
        """
        try:
            # Get and verify channel
            followed_channel = await self.get_followed_channel(followed_channel_id, user_id)

            logger.info(f"Updating metadata for channel {followed_channel_id}: {followed_channel.youtube_channel_name}")

            # Extract fresh metadata from YouTube
            try:
                channel_metadata = await self.metadata_service.extract_channel_info(
                    followed_channel.youtube_channel_url
                )
            except Exception as e:
                logger.error(f"Failed to extract channel metadata: {e}", exc_info=True)
                raise InvalidChannelURLError(
                    f"Could not fetch updated channel information from YouTube. "
                    f"The channel may be unavailable or deleted."
                )

            if not channel_metadata:
                raise InvalidChannelURLError("Failed to fetch channel metadata from YouTube")

            # Update entity with fresh metadata (keeps existing data if fetch fails)
            followed_channel.update_metadata(
                youtube_channel_name=channel_metadata.get("name"),
                youtube_channel_url=channel_metadata.get("url"),
                thumbnail_url=channel_metadata.get("thumbnail_url"),
                youtube_channel_description=channel_metadata.get("description")
            )

            # Save to repository
            updated = await self.followed_channel_repository.update(followed_channel)

            logger.info(f"Successfully updated metadata for channel {followed_channel_id}")
            return updated

        except FollowedChannelNotFoundError:
            raise
        except InvalidChannelURLError:
            raise
        except Exception as e:
            logger.error(f"Failed to update channel metadata for channel {followed_channel_id}: {e}", exc_info=True)
            raise

    async def trigger_check(self, followed_channel_id: int, user_id: int) -> str:
        """
        Manually trigger a check for new videos using yt-dlp full method

        Args:
            followed_channel_id: ID of the followed channel
            user_id: ID of the user (for verification)

        Returns:
            Task ID of the queued Celery task

        Raises:
            FollowedChannelNotFoundError: If channel not found or doesn't belong to user
            ConnectionError: If Celery/Redis is unavailable
        """
        try:
            # Verify channel exists and belongs to user
            channel = await self.get_followed_channel(followed_channel_id, user_id)

            # Queue check task - use apply_async with explicit args/kwargs to avoid Celery serialization issues
            try:
                task_result = check_followed_channel_for_new_videos.apply_async(
                    args=(followed_channel_id,),
                    kwargs={}
                )
            except (ConnectionError, OSError) as e:
                logger.error(f"Failed to connect to task queue: {e}")
                raise ConnectionError(f"Task queue is unavailable: {str(e)}")
            except Exception as e:
                # Catch Kombu/Celery specific exceptions (OperationalError, etc.)
                if 'Connection refused' in str(e) or 'OperationalError' in type(e).__name__:
                    logger.error(f"Failed to connect to task queue: {e}")
                    raise ConnectionError(f"Task queue is unavailable: {str(e)}")
                raise

            # Create task status record
            task_status = CeleryTaskStatus(
                task_id=task_result.id,
                task_name="check_followed_channel_for_new_videos",
                status=TaskStatus.PENDING,
                followed_channel_id=followed_channel_id
            )
            await self.task_status_repository.create(task_status)

            logger.info(f"Queued manual check for channel {followed_channel_id}, task ID: {task_result.id}")
            return task_result.id

        except FollowedChannelNotFoundError:
            raise
        except ConnectionError:
            raise
        except Exception as e:
            logger.error(f"Failed to trigger check for channel {followed_channel_id}: {e}", exc_info=True)
            raise

    async def trigger_check_rss(self, followed_channel_id: int, user_id: int) -> str:
        """
        Manually trigger a check for new videos using RSS feed method

        Args:
            followed_channel_id: ID of the followed channel
            user_id: ID of the user (for verification)

        Returns:
            Task ID of the queued Celery task

        Raises:
            FollowedChannelNotFoundError: If channel not found or doesn't belong to user
            ConnectionError: If Celery/Redis is unavailable
        """
        from app.infrastructure.tasks.channel_check_rss_tasks import check_followed_channel_for_new_videos_rss

        try:
            # Verify channel exists and belongs to user
            channel = await self.get_followed_channel(followed_channel_id, user_id)

            # Queue RSS check task
            try:
                task_result = check_followed_channel_for_new_videos_rss.apply_async(
                    args=(followed_channel_id,),
                    kwargs={}
                )
            except (ConnectionError, OSError) as e:
                logger.error(f"Failed to connect to task queue: {e}")
                raise ConnectionError(f"Task queue is unavailable: {str(e)}")
            except Exception as e:
                # Catch Kombu/Celery specific exceptions (OperationalError, etc.)
                if 'Connection refused' in str(e) or 'OperationalError' in type(e).__name__:
                    logger.error(f"Failed to connect to task queue: {e}")
                    raise ConnectionError(f"Task queue is unavailable: {str(e)}")
                raise

            # Create task status record
            task_status = CeleryTaskStatus(
                task_id=task_result.id,
                task_name="check_followed_channel_for_new_videos_rss",
                status=TaskStatus.PENDING,
                followed_channel_id=followed_channel_id
            )
            await self.task_status_repository.create(task_status)

            logger.info(f"Queued RSS check for channel {followed_channel_id}, task ID: {task_result.id}")
            return task_result.id

        except FollowedChannelNotFoundError:
            raise
        except ConnectionError:
            raise
        except Exception as e:
            logger.error(f"Failed to trigger RSS check for channel {followed_channel_id}: {e}", exc_info=True)
            raise
    
    async def trigger_backfill(
        self,
        followed_channel_id: int,
        user_id: int,
        year: Optional[int] = None,
        max_videos: int = 20
    ) -> bool:
        """
        Manually trigger a backfill for historical videos
        
        Args:
            followed_channel_id: ID of the followed channel
            user_id: ID of the user (for verification)
            year: Optional year to backfill (None for all years)
            max_videos: Maximum number of videos to fetch
        
        Returns:
            True if backfill was queued
        
        Raises:
            FollowedChannelNotFoundError: If channel not found or doesn't belong to user
        """
        try:
            # Verify channel exists and belongs to user
            await self.get_followed_channel(followed_channel_id, user_id)
            
            # Queue backfill task - use apply_async with explicit args/kwargs to avoid Celery serialization issues
            backfill_followed_channel.apply_async(
                args=(followed_channel_id, year, max_videos),
                kwargs={}
            )
            
            logger.info(f"Queued backfill for channel {followed_channel_id} (year: {year}, max: {max_videos})")
            return True
            
        except FollowedChannelNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to trigger backfill for channel {followed_channel_id}: {e}")
            raise

