"""
Episode service for coordinating episode-related business logic
"""
from typing import List, Optional, Tuple, Dict, Any
import logging
import time
from datetime import datetime, timedelta
from dataclasses import dataclass

from app.domain.entities.episode import Episode, EpisodeStatus
from app.domain.repositories.episode import EpisodeRepository
from app.application.services.metadata_processing_service import MetadataProcessingService
from app.infrastructure.services.youtube_service import YouTubeService
from app.infrastructure.services.upload_service import DuplicateEpisodeError
from app.domain.value_objects.video_id import VideoId
from app.core.logging import get_logger, get_structured_logger
from app.infrastructure.services.logging_service import logging_service

logger = get_logger("processor")
structured_logger = get_structured_logger("processor")


class EpisodeNotFoundError(Exception):
    """Exception raised when episode is not found"""
    pass


class BulkDeletionError(Exception):
    """Exception raised when bulk deletion fails"""
    pass


class FileCleanupError(Exception):
    """Exception raised when file cleanup fails"""
    pass


@dataclass
class BulkDeletionResult:
    """Result of bulk deletion operation with detailed statistics"""
    success: bool
    total_episodes: int
    deleted_episodes: int
    failed_episodes: int
    deleted_files: int
    failed_files: int
    partial_completion: bool
    error_message: Optional[str] = None
    failed_episode_details: Optional[List[Dict[str, Any]]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "success": self.success,
            "total_episodes": self.total_episodes,
            "deleted_episodes": self.deleted_episodes,
            "failed_episodes": self.failed_episodes,
            "deleted_files": self.deleted_files,
            "failed_files": self.failed_files,
            "partial_completion": self.partial_completion,
            "error_message": self.error_message,
            "failed_episode_details": self.failed_episode_details or []
        }


class EpisodeService:
    """
    Application service for episode management business logic
    """
    
    def __init__(
        self,
        episode_repository: EpisodeRepository,
        metadata_service: MetadataProcessingService,
        youtube_service: YouTubeService
    ):
        self.episode_repository = episode_repository
        self.metadata_service = metadata_service
        self.youtube_service = youtube_service
    
    async def create_from_youtube_url(
        self,
        channel_id: int,
        video_url: str,
        tags: Optional[List[str]] = None,
        requested_language: Optional[str] = None,
        requested_quality: Optional[str] = None
    ) -> Episode:
        """
        Create episode from YouTube URL
        
        Args:
            channel_id: Channel to associate episode with
            video_url: YouTube video URL
            tags: Optional tags for episode
            
        Returns:
            Created Episode entity
            
        Raises:
            DuplicateEpisodeError: If episode already exists
            YouTubeExtractionError: If metadata extraction fails
        """
        try:
            logger.info(f"Creating episode from YouTube URL: {video_url}")
            
            # Extract video ID
            video_id = VideoId.from_url(video_url)
            
            # Check for duplicates
            existing = await self.episode_repository.get_by_video_id_and_channel(
                video_id, channel_id
            )
            
            if existing:
                logger.warning(f"Episode already exists: {video_id.value} in channel {channel_id}")
                raise DuplicateEpisodeError(
                    f"Episode with video ID {video_id.value} already exists in this channel"
                )
            
            # Extract metadata from YouTube
            logger.debug(f"Extracting metadata for video: {video_id.value}")
            metadata = await self.youtube_service.extract_metadata(video_url)
            
            # Process metadata into Episode entity
            episode = self.metadata_service.process_youtube_metadata(
                channel_id=channel_id,
                metadata=metadata,
                tags=tags
            )

            # Store requested audio preferences
            if requested_language or requested_quality:
                episode.requested_language = requested_language
                episode.requested_quality = requested_quality

            # Save to repository
            episode = await self.episode_repository.create(episode)
            
            logger.info(f"Successfully created episode {episode.id}: {episode.title}")
            return episode
            
        except DuplicateEpisodeError:
            raise
        except Exception as e:
            logger.error(f"Failed to create episode from URL {video_url}: {e}")
            raise
    
    async def create_from_upload(
        self,
        channel_id: int,
        title: str,
        description: Optional[str],
        publication_date: datetime,
        audio_file_path: str,
        file_size: int,
        duration_seconds: int,
        original_filename: str,
        tags: Optional[List[str]] = None
    ) -> Episode:
        """
        Create episode from uploaded audio file
        
        Args:
            channel_id: Channel to associate episode with
            title: Episode title
            description: Episode description
            publication_date: Publication date
            audio_file_path: Relative path to audio file
            file_size: File size in bytes
            duration_seconds: Audio duration in seconds
            original_filename: Original uploaded filename
            tags: Optional tags for episode
            
        Returns:
            Created Episode entity
            
        Raises:
            DuplicateEpisodeError: If episode with same title already exists in channel
        """
        try:
            logger.info(f"Creating episode from upload: {title} in channel {channel_id}")
            
            # Check for duplicate titles in channel
            existing_episodes = await self.episode_repository.get_by_filters(
                filters={'channel_id': channel_id},
                limit=1000  # Get all episodes to check titles
            )
            
            for existing in existing_episodes:
                if existing.title.lower().strip() == title.lower().strip():
                    logger.warning(f"Episode with title '{title}' already exists in channel {channel_id}")
                    raise DuplicateEpisodeError(
                        f"Episode with title '{title}' already exists in this channel",
                        existing_episode_id=existing.id
                    )
            
            # Create Episode entity
            from app.domain.value_objects.duration import Duration

            episode = Episode(
                id=None,
                channel_id=channel_id,
                video_id=VideoId.generate_upload_id(),  # Generate unique up_* ID for uploaded episodes
                title=title,
                description=description or "",
                publication_date=publication_date,
                audio_file_path=audio_file_path,
                video_url="",  # No video URL for uploads
                thumbnail_url="",  # No thumbnail for uploads
                duration=Duration(duration_seconds) if duration_seconds > 0 else None,
                keywords=[],
                status=EpisodeStatus.COMPLETED,  # Immediate completion for uploads
                retry_count=0,
                download_date=datetime.utcnow(),
                media_file_size=file_size,
                source_type="upload",
                original_filename=original_filename
            )
            
            # Save to repository
            episode = await self.episode_repository.create(episode)
            
            # Associate tags if provided
            if tags:
                # Convert tag names to tag IDs
                from app.domain.repositories.tag import TagRepository
                tag_repository = TagRepository(self.episode_repository.db_session)
                
                tag_ids = []
                for tag_name in tags:
                    tag = await tag_repository.get_or_create_by_name(tag_name, channel_id)
                    tag_ids.append(tag.id)
                
                # Update episode tags
                await self.episode_repository.update_episode_tags(episode.id, tag_ids)
                
                # Reload episode with tags
                episode = await self.episode_repository.get_by_id(episode.id)
            
            logger.info(f"Successfully created episode from upload {episode.id}: {episode.title}")
            return episode
            
        except DuplicateEpisodeError:
            raise
        except Exception as e:
            logger.error(f"Failed to create episode from upload: {e}")
            raise
    
    async def get_episode(self, episode_id: int) -> Optional[Episode]:
        """Get episode by ID"""
        try:
            return await self.episode_repository.get_by_id(episode_id)
        except Exception as e:
            logger.error(f"Failed to get episode {episode_id}: {e}")
            raise
    
    async def list_episodes(
        self,
        channel_id: int,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> Tuple[List[Episode], int]:
        """
        List episodes with filtering and pagination
        
        Args:
            channel_id: Channel ID to filter by
            skip: Number of episodes to skip
            limit: Maximum number of episodes to return
            status: Filter by episode status
            search_query: Search in title and description
            
        Returns:
            Tuple of (episodes, total_count)
        """
        try:
            logger.debug(f"Listing episodes for channel {channel_id}")
            
            # Build filters
            filters = {"channel_id": channel_id}
            
            if status:
                try:
                    episode_status = EpisodeStatus(status.lower())
                    filters["status"] = episode_status
                except ValueError:
                    logger.warning(f"Invalid status filter: {status}")
            
            if search_query:
                filters["search"] = search_query.strip()
            
            # Get episodes from repository
            episodes = await self.episode_repository.get_by_filters(
                filters=filters,
                skip=skip,
                limit=limit,
                order_by="created_at",
                order_desc=True
            )
            
            # Get total count
            total = await self.episode_repository.count_by_filters(filters)
            
            return episodes, total
            
        except Exception as e:
            logger.error(f"Failed to list episodes: {e}")
            raise
    
    async def update_episode(
        self,
        episode_id: int,
        updates: Dict[str, Any]
    ) -> Optional[Episode]:
        """
        Update episode metadata
        
        Args:
            episode_id: Episode ID to update
            updates: Dictionary of fields to update
            
        Returns:
            Updated Episode entity or None if not found
        """
        try:
            episode = await self.episode_repository.get_by_id(episode_id)
            if not episode:
                return None
            
            logger.info(f"Updating episode {episode_id}")
            
            # Apply updates using domain methods
            if 'title' in updates or 'description' in updates or 'keywords' in updates:
                episode.update_metadata(
                    title=updates.get('title'),
                    description=updates.get('description'),
                    keywords=updates.get('keywords')
                )

            # Handle tag updates
            if 'tags' in updates:
                tag_ids = updates.get('tags', [])
                logger.info(f"Updating tags for episode {episode_id}: {tag_ids}")
                await self.episode_repository.update_episode_tags(episode_id, tag_ids)

            # Save updates
            updated_episode = await self.episode_repository.update(episode)

            # Commit the transaction
            await self.episode_repository.db_session.commit()

            # Reload the episode with tags to return complete data
            final_episode = await self.episode_repository.get_by_id(episode_id)

            logger.info(f"Successfully updated episode {episode_id}")
            return final_episode
            
        except Exception as e:
            logger.error(f"Failed to update episode {episode_id}: {e}")
            raise
    
    async def delete_episode(self, episode_id: int) -> bool:
        """
        Delete episode from database (files handled separately)
        
        Args:
            episode_id: Episode ID to delete
            
        Returns:
            True if deleted successfully, False if not found
        """
        try:
            episode = await self.episode_repository.get_by_id(episode_id)
            if not episode:
                return False
            
            logger.info(f"Deleting episode {episode_id}: {episode.title}")
            
            # Delete from repository
            await self.episode_repository.delete(episode_id)
            
            logger.info(f"Successfully deleted episode {episode_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete episode {episode_id}: {e}")
            raise
    
    async def get_episode_by_video_id(
        self,
        video_id: str,
        channel_id: int
    ) -> Optional[Episode]:
        """Get episode by video ID and channel"""
        try:
            video_id_obj = VideoId(video_id)
            return await self.episode_repository.get_by_video_id_and_channel(
                video_id_obj, channel_id
            )
        except Exception as e:
            logger.error(f"Failed to get episode by video ID {video_id}: {e}")
            raise
    
    async def get_episodes_by_status(
        self,
        status: EpisodeStatus,
        limit: int = 100
    ) -> List[Episode]:
        """Get episodes by status (useful for batch operations)"""
        try:
            filters = {"status": status}
            episodes = await self.episode_repository.get_by_filters(
                filters=filters,
                limit=limit,
                order_by="created_at",
                order_desc=False
            )
            return episodes
        except Exception as e:
            logger.error(f"Failed to get episodes by status {status}: {e}")
            raise
    
    async def get_pending_episodes(self, limit: int = 10) -> List[Episode]:
        """Get pending episodes for processing"""
        return await self.get_episodes_by_status(EpisodeStatus.PENDING, limit)
    
    async def get_failed_episodes(self, limit: int = 10) -> List[Episode]:
        """Get failed episodes that can be retried"""
        try:
            episodes = await self.get_episodes_by_status(EpisodeStatus.FAILED, limit)
            # Filter to only include episodes that can be retried
            retryable = [ep for ep in episodes if ep.can_retry()]
            return retryable
        except Exception as e:
            logger.error(f"Failed to get failed episodes: {e}")
            raise
    
    async def get_stuck_processing_episodes(self, limit: int = 10) -> List[Episode]:
        """Get episodes that have been processing for too long"""
        try:
            episodes = await self.get_episodes_by_status(EpisodeStatus.PROCESSING, limit)
            # Filter to only include stuck episodes
            stuck = [ep for ep in episodes if ep.is_processing_stuck()]
            return stuck
        except Exception as e:
            logger.error(f"Failed to get stuck processing episodes: {e}")
            raise
    
    async def mark_episode_as_failed(
        self,
        episode_id: int,
        error_message: str
    ) -> bool:
        """Mark episode as failed with error message"""
        try:
            episode = await self.episode_repository.get_by_id(episode_id)
            if not episode:
                return False
            
            episode.increment_retry_count()
            episode.update_status(EpisodeStatus.FAILED)
            
            await self.episode_repository.update(episode)
            
            logger.info(f"Marked episode {episode_id} as failed: {error_message}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark episode {episode_id} as failed: {e}")
            return False
    
    async def mark_episode_as_completed(
        self,
        episode_id: int,
        audio_file_path: str,
        duration_seconds: Optional[int] = None
    ) -> bool:
        """Mark episode as completed"""
        try:
            episode = await self.episode_repository.get_by_id(episode_id)
            if not episode:
                return False
            
            episode.mark_as_completed(audio_file_path, duration_seconds)
            
            await self.episode_repository.update(episode)
            
            logger.info(f"Marked episode {episode_id} as completed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark episode {episode_id} as completed: {e}")
            return False
    
    async def get_channel_stats(self, channel_id: int) -> Dict[str, Any]:
        """Get statistics for a channel's episodes"""
        try:
            filters = {"channel_id": channel_id}
            
            # Get counts by status
            total = await self.episode_repository.count_by_filters(filters)
            
            stats = {"total": total}
            
            for status in EpisodeStatus:
                status_filters = {**filters, "status": status}
                count = await self.episode_repository.count_by_filters(status_filters)
                stats[status.value] = count
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get channel stats for channel {channel_id}: {e}")
            raise
    
    async def cleanup_old_episodes(
        self,
        channel_id: int,
        keep_days: int = 90
    ) -> int:
        """
        Clean up old episodes (useful for maintenance)
        
        Args:
            channel_id: Channel to clean up
            keep_days: Number of days to keep episodes
            
        Returns:
            Number of episodes cleaned up
        """
        try:
            logger.info(f"Cleaning up episodes older than {keep_days} days for channel {channel_id}")
            
            cutoff_date = datetime.utcnow() - timedelta(days=keep_days)
            
            # Get old episodes
            old_episodes = await self.episode_repository.get_episodes_before_date(
                channel_id, cutoff_date
            )
            
            cleaned_count = 0
            for episode in old_episodes:
                try:
                    await self.delete_episode(episode.id)
                    cleaned_count += 1
                except Exception as e:
                    logger.error(f"Failed to delete old episode {episode.id}: {e}")
            
            logger.info(f"Cleaned up {cleaned_count} old episodes")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old episodes: {e}")
            raise

    async def set_episode_favorite(self, episode_id: int, is_favorited: bool) -> bool:
        """
        Set episode favorite status

        Args:
            episode_id: Episode ID to update
            is_favorited: New favorite status

        Returns:
            True if updated successfully, False if episode not found
        """
        try:
            episode = await self.episode_repository.get_by_id(episode_id)
            if not episode:
                return False

            logger.info(f"Setting episode {episode_id} favorite status to {is_favorited}")

            # Update favorite status using domain method
            episode.set_favorite(is_favorited)

            # Save updates
            await self.episode_repository.update(episode)

            # Commit the transaction
            await self.episode_repository.db_session.commit()

            logger.info(f"Successfully updated favorite status for episode {episode_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to set favorite status for episode {episode_id}: {e}")
            raise

    async def toggle_episode_favorite(self, episode_id: int) -> Optional[bool]:
        """
        Toggle episode favorite status

        Args:
            episode_id: Episode ID to toggle

        Returns:
            New favorite status or None if episode not found
        """
        try:
            episode = await self.episode_repository.get_by_id(episode_id)
            if not episode:
                return None

            logger.info(f"Toggling favorite status for episode {episode_id}")

            # Toggle favorite status using domain method
            new_status = episode.toggle_favorite()

            # Save updates
            await self.episode_repository.update(episode)

            # Commit the transaction
            await self.episode_repository.db_session.commit()

            logger.info(f"Successfully toggled favorite status for episode {episode_id} to {new_status}")
            return new_status

        except Exception as e:
            logger.error(f"Failed to toggle favorite status for episode {episode_id}: {e}")
            raise

    async def get_favorite_episodes(
        self,
        channel_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Episode], int]:
        """
        Get favorite episodes for a channel

        Args:
            channel_id: Channel ID to filter by
            skip: Number of episodes to skip
            limit: Maximum number of episodes to return

        Returns:
            Tuple of (episodes, total_count)
        """
        try:
            logger.debug(f"Getting favorite episodes for channel {channel_id}")

            # Build filters for favorites
            filters = {
                "channel_id": channel_id,
                "is_favorited": True
            }

            # Get episodes from repository
            episodes = await self.episode_repository.get_by_filters(
                filters=filters,
                skip=skip,
                limit=limit,
                order_by="created_at",
                order_desc=True
            )

            # Get total count
            total = await self.episode_repository.count_by_filters(filters)

            return episodes, total

        except Exception as e:
            logger.error(f"Failed to get favorite episodes: {e}")
            raise

    async def reset_episode_for_redownload(self, episode_id: int) -> bool:
        """
        Reset episode status to pending for re-download

        This method resets an episode to pending status, clears the audio file path,
        and resets retry count to allow re-downloading with the fixed MP3 conversion.

        Args:
            episode_id: Episode ID to reset

        Returns:
            True if reset successfully, False if episode not found
        """
        try:
            episode = await self.episode_repository.get_by_id(episode_id)
            if not episode:
                logger.warning(f"Episode {episode_id} not found for reset")
                return False

            logger.info(f"Resetting episode {episode_id} for re-download: {episode.title}")

            # Reset episode for re-download
            episode.reset_for_redownload()

            # Save changes
            await self.episode_repository.update(episode)
            await self.episode_repository.db_session.commit()

            logger.info(f"Successfully reset episode {episode_id} for re-download")
            return True

        except Exception as e:
            logger.error(f"Failed to reset episode {episode_id} for re-download: {e}")
            raise

    async def delete_all_episodes_for_channel(
        self,
        channel_id: int,
        dry_run: bool = False
    ) -> BulkDeletionResult:
        """
        Delete all episodes and their media files for a specific channel

        This method performs a bulk deletion of all episodes in a channel,
        including their associated media files. It provides comprehensive
        error handling and detailed reporting of the operation results.

        Args:
            channel_id: Channel ID to delete episodes from
            dry_run: If True, only count episodes without deleting

        Returns:
            BulkDeletionResult with detailed operation statistics

        Raises:
            BulkDeletionError: If the operation fails critically
        """
        try:
            logger.info(f"Starting bulk deletion for channel {channel_id} (dry_run={dry_run})")

            # Initialize counters and tracking
            total_episodes = 0
            deleted_episodes = 0
            failed_episodes = 0
            deleted_files = 0
            failed_files = 0
            failed_episode_details = []

            # Get all episodes for the channel
            try:
                episodes, total_episodes = await self.list_episodes(
                    channel_id=channel_id,
                    skip=0,
                    limit=10000  # Large limit to get all episodes
                )
                logger.info(f"Found {total_episodes} episodes to delete in channel {channel_id}")

                if total_episodes == 0:
                    return BulkDeletionResult(
                        success=True,
                        total_episodes=0,
                        deleted_episodes=0,
                        failed_episodes=0,
                        deleted_files=0,
                        failed_files=0,
                        partial_completion=False,
                        error_message="No episodes found to delete"
                    )

                if dry_run:
                    return BulkDeletionResult(
                        success=True,
                        total_episodes=total_episodes,
                        deleted_episodes=0,
                        failed_episodes=0,
                        deleted_files=0,
                        failed_files=0,
                        partial_completion=False,
                        error_message=f"Dry run: Would delete {total_episodes} episodes"
                    )

            except Exception as e:
                logger.error(f"Failed to retrieve episodes for channel {channel_id}: {e}")
                raise BulkDeletionError(f"Failed to retrieve episodes: {str(e)}")

            # Import FileService for file operations
            from app.infrastructure.services.file_service import FileService
            from app.core.config import settings
            from pathlib import Path

            file_service = FileService()
            media_path = Path(settings.media_path)

            # Process each episode (transaction is already managed by FastAPI dependencies)
            for episode in episodes:
                episode_failed = False
                error_details = {
                    "episode_id": episode.id,
                    "title": episode.title[:100] + "..." if len(episode.title) > 100 else episode.title,
                    "errors": []
                }

                try:
                    # 1. Delete media file if it exists
                    if episode.audio_file_path:
                        try:
                            file_deleted = await file_service.delete_episode_file(episode.audio_file_path)
                            if file_deleted:
                                deleted_files += 1
                                logger.debug(f"Deleted media file for episode {episode.id}: {episode.audio_file_path}")
                            else:
                                failed_files += 1
                                error_details["errors"].append("Failed to delete media file")
                                logger.warning(f"Failed to delete media file for episode {episode.id}: {episode.audio_file_path}")
                        except Exception as file_error:
                            failed_files += 1
                            episode_failed = True
                            error_msg = f"File deletion error: {str(file_error)}"
                            error_details["errors"].append(error_msg)
                            logger.error(f"Error deleting file for episode {episode.id}: {file_error}")

                    # 2. Delete episode from database
                    try:
                        deletion_success = await self.delete_episode(episode.id)
                        if deletion_success:
                            deleted_episodes += 1
                            logger.debug(f"Deleted episode {episode.id} from database")
                        else:
                            failed_episodes += 1
                            episode_failed = True
                            error_details["errors"].append("Failed to delete from database")
                            logger.error(f"Failed to delete episode {episode.id} from database")
                    except Exception as db_error:
                        failed_episodes += 1
                        episode_failed = True
                        error_msg = f"Database deletion error: {str(db_error)}"
                        error_details["errors"].append(error_msg)
                        logger.error(f"Database error deleting episode {episode.id}: {db_error}")

                except Exception as episode_error:
                    failed_episodes += 1
                    episode_failed = True
                    error_msg = f"General episode error: {str(episode_error)}"
                    error_details["errors"].append(error_msg)
                    logger.error(f"Error processing episode {episode.id}: {episode_error}")

                # Track failed episodes for detailed reporting
                if episode_failed:
                    failed_episode_details.append(error_details)

            # Determine success status
            partial_completion = failed_episodes > 0 and deleted_episodes > 0
            overall_success = failed_episodes == 0 or partial_completion

            # Prepare result message
            error_message = None
            if failed_episodes > 0:
                if deleted_episodes == 0:
                    error_message = f"Failed to delete all {failed_episodes} episodes"
                else:
                    error_message = f"Partially completed: {failed_episodes} episodes failed to delete"

            result = BulkDeletionResult(
                success=overall_success,
                total_episodes=total_episodes,
                deleted_episodes=deleted_episodes,
                failed_episodes=failed_episodes,
                deleted_files=deleted_files,
                failed_files=failed_files,
                partial_completion=partial_completion,
                error_message=error_message,
                failed_episode_details=failed_episode_details[:10]  # Limit to first 10 failures
            )

            # Log final results
            if overall_success:
                if partial_completion:
                    logger.warning(f"Bulk deletion completed with issues for channel {channel_id}: "
                                 f"{deleted_episodes}/{total_episodes} episodes deleted, "
                                 f"{deleted_files} files deleted, {failed_files} file failures")
                else:
                    logger.info(f"Bulk deletion completed successfully for channel {channel_id}: "
                              f"{deleted_episodes} episodes and {deleted_files} files deleted")
            else:
                logger.error(f"Bulk deletion failed for channel {channel_id}: "
                           f"Only {deleted_episodes}/{total_episodes} episodes deleted")

            return result

        except BulkDeletionError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error during bulk deletion for channel {channel_id}: {e}")
            raise BulkDeletionError(f"Unexpected error: {str(e)}")

    async def get_episode_count_for_channel(self, channel_id: int) -> int:
        """
        Get the total count of episodes for a channel

        Args:
            channel_id: Channel ID to count episodes for

        Returns:
            Total number of episodes in the channel

        Raises:
            Exception: If the count operation fails
        """
        try:
            logger.debug(f"Getting episode count for channel {channel_id}")

            filters = {"channel_id": channel_id}
            count = await self.episode_repository.count_by_filters(filters)

            logger.debug(f"Found {count} episodes in channel {channel_id}")
            return count

        except Exception as e:
            logger.error(f"Failed to get episode count for channel {channel_id}: {e}")
            raise