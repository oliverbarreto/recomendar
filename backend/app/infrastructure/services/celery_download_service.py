"""
Celery-compatible download service for episode downloads

This service is a clone of DownloadService but designed to work with Celery tasks.
It executes downloads directly without using a queue mechanism, making it compatible
with Celery's event loop lifecycle.

Note: This is intentionally separate from DownloadService to keep FastAPI and Celery
paths independent. In the future, FastAPI may also migrate to using Celery tasks.
"""
from typing import Optional, Dict, Any
import asyncio
import logging
from datetime import datetime
from enum import Enum
import traceback
import random

from app.infrastructure.services.youtube_service import YouTubeService, YouTubeDownloadError
from app.infrastructure.services.file_service import FileService
from app.domain.repositories.episode import EpisodeRepository
from app.domain.entities.episode import EpisodeStatus
from app.domain.entities.event import EventSeverity
from app.application.services.event_service import EventService
from app.core.config import settings

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Background task status"""
    QUEUED = "queued"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CeleryDownloadProgress:
    """Download progress information for Celery tasks"""

    def __init__(self, episode_id: int, event_service: Optional['EventService'] = None, user_id: Optional[int] = None, channel_id: Optional[int] = None):
        self.episode_id = episode_id
        self.status = TaskStatus.QUEUED
        self.percentage = "0%"
        self.speed = "N/A"
        self.eta = "N/A"
        self.downloaded_bytes = 0
        self.total_bytes = 0
        self.error_message: Optional[str] = None
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.updated_at = datetime.utcnow()

        # Business event tracking
        self.event_service = event_service
        self.user_id = user_id
        self.channel_id = channel_id or 1  # Default channel
        self.last_milestone = 0  # Track last reported milestone
        self.milestones = [25, 50, 75, 100]  # Progress milestones to track
    
    def update_progress(self, data: Dict[str, Any]):
        """Update progress from yt-dlp callback with business event tracking"""
        if data.get('status') == 'downloading':
            self.status = TaskStatus.PROCESSING
            old_percentage = self.percentage
            self.percentage = data.get('_percent_str', '0%').strip()
            self.speed = data.get('_speed_str', 'N/A').strip()
            self.eta = data.get('_eta_str', 'N/A').strip()
            self.downloaded_bytes = data.get('downloaded_bytes', 0)
            self.total_bytes = data.get('total_bytes', 0)

            # Track milestone events
            self._track_milestone_events(old_percentage, self.percentage)

        elif data.get('status') == 'finished':
            self.status = TaskStatus.COMPLETED
            old_percentage = self.percentage
            self.percentage = "100%"
            self.completed_at = datetime.utcnow()

            # Emit download completion event
            self._emit_download_completed_event()

        self.updated_at = datetime.utcnow()
    
    def mark_failed(self, error: str):
        """Mark as failed with error message and emit business event"""
        self.status = TaskStatus.FAILED
        self.error_message = error
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

        # Emit download failed event
        self._emit_download_failed_event(error)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            'episode_id': self.episode_id,
            'status': self.status.value,
            'percentage': self.percentage,
            'speed': self.speed,
            'eta': self.eta,
            'downloaded_bytes': self.downloaded_bytes,
            'total_bytes': self.total_bytes,
            'error_message': self.error_message,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'updated_at': self.updated_at.isoformat()
        }

    def _track_milestone_events(self, old_percentage: str, new_percentage: str):
        """Track and emit business events for download progress milestones"""
        if not self.event_service or not self.user_id:
            return

        try:
            # Extract numeric values from percentage strings
            old_percent = self._extract_percentage(old_percentage)
            new_percent = self._extract_percentage(new_percentage)

            # Check if we've crossed a milestone
            for milestone in self.milestones:
                if old_percent < milestone <= new_percent and milestone > self.last_milestone:
                    self.last_milestone = milestone
                    asyncio.create_task(self._emit_milestone_event(milestone))

        except Exception as e:
            logger.warning(f"Error tracking milestone events for episode {self.episode_id}: {e}")

    def _extract_percentage(self, percentage_str: str) -> float:
        """Extract numeric percentage from string like '45.2%'"""
        try:
            return float(percentage_str.replace('%', '').strip()) if percentage_str != 'N/A' else 0.0
        except (ValueError, AttributeError):
            return 0.0

    async def _emit_milestone_event(self, milestone: int):
        """Emit business event for download milestone"""
        if not self.event_service:
            return

        try:
            await self.event_service.log_user_action(
                channel_id=self.channel_id,
                user_id=self.user_id,
                action="download_progress",
                resource_type="episode",
                resource_id=str(self.episode_id),
                message=f"Episode download reached {milestone}% completion",
                details={
                    "milestone_percentage": milestone,
                    "download_speed": self.speed,
                    "eta": self.eta,
                    "downloaded_bytes": self.downloaded_bytes,
                    "total_bytes": self.total_bytes,
                    "status": self.status.value
                },
                severity=EventSeverity.INFO
            )
        except Exception as e:
            logger.error(f"Failed to emit milestone event for episode {self.episode_id}: {e}")

    def _emit_download_completed_event(self):
        """Emit business event for download completion"""
        if not self.event_service or not self.user_id:
            return

        try:
            asyncio.create_task(self.event_service.log_user_action(
                channel_id=self.channel_id,
                user_id=self.user_id,
                action="download_completed",
                resource_type="episode",
                resource_id=str(self.episode_id),
                message="Episode download completed successfully",
                details={
                    "total_bytes": self.total_bytes,
                    "download_duration_seconds": (
                        (self.completed_at - self.started_at).total_seconds()
                        if self.started_at and self.completed_at else None
                    ),
                    "status": self.status.value
                },
                severity=EventSeverity.INFO
            ))
        except Exception as e:
            logger.error(f"Failed to emit download completed event for episode {self.episode_id}: {e}")

    def _emit_download_failed_event(self, error: str):
        """Emit business event for download failure"""
        if not self.event_service or not self.user_id:
            return

        try:
            asyncio.create_task(self.event_service.log_user_action(
                channel_id=self.channel_id,
                user_id=self.user_id,
                action="download_failed",
                resource_type="episode",
                resource_id=str(self.episode_id),
                message=f"Episode download failed: {error}",
                details={
                    "error_message": error,
                    "percentage_reached": self.percentage,
                    "downloaded_bytes": self.downloaded_bytes,
                    "total_bytes": self.total_bytes,
                    "status": self.status.value
                },
                severity=EventSeverity.ERROR
            ))
        except Exception as e:
            logger.error(f"Failed to emit download failed event for episode {self.episode_id}: {e}")


class CeleryDownloadService:
    """
    Download service for Celery tasks - direct execution, no queue mechanism
    
    This service is designed to work within Celery's event loop lifecycle.
    It executes downloads directly without using asyncio.Queue or BackgroundTasks,
    making it compatible with Celery's task execution model.
    """

    def __init__(
        self,
        youtube_service: YouTubeService,
        file_service: FileService,
        episode_repository: EpisodeRepository
    ):
        self.youtube_service = youtube_service
        self.file_service = file_service
        self.episode_repository = episode_repository
        
        # Resource limits
        self.download_timeout = settings.download_timeout_minutes * 60
    
    async def download_episode(
        self,
        episode_id: int,
        event_service: Optional[EventService] = None,
        user_id: Optional[int] = None,
        channel_id: Optional[int] = None,
        audio_language: Optional[str] = None,
        audio_quality: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Directly download an episode - executes immediately without queue
        
        This method performs the download synchronously within the Celery task's
        event loop, making it compatible with Celery's execution model.
        
        Args:
            episode_id: Episode ID to download
            event_service: Optional event service for business event tracking
            user_id: Optional user ID for event tracking
            channel_id: Optional channel ID for event tracking
            
        Returns:
            Dictionary with download result:
            {
                "status": "success" | "error",
                "episode_id": int,
                "message": str,
                "file_path": str (if successful)
            }
        """
        # Create progress tracker
        progress = CeleryDownloadProgress(
            episode_id=episode_id,
            event_service=event_service,
            user_id=user_id,
            channel_id=channel_id
        )
        
        # Create fresh database session for download task
        from app.infrastructure.database.connection import get_background_task_session, log_database_operation
        from app.infrastructure.repositories.episode_repository import EpisodeRepositoryImpl
        
        bg_session = await get_background_task_session()
        bg_episode_repository = EpisodeRepositoryImpl(bg_session)
        
        # Log session creation
        session_id = getattr(bg_session, '_session_id', id(bg_session))
        log_database_operation('session_created', session_id, f'celery download task for episode {episode_id}')
        
        try:
            # Update episode status to processing
            await bg_episode_repository.update_status(
                episode_id,
                EpisodeStatus.PROCESSING
            )
            await bg_session.commit()
            
            # Emit download started event
            if event_service and user_id:
                try:
                    await event_service.log_user_action(
                        channel_id=channel_id or 1,
                        user_id=user_id,
                        action="download_started",
                        resource_type="episode",
                        resource_id=str(episode_id),
                        message="Episode download started via Celery task",
                        details={
                            "requested_language": audio_language,
                            "requested_quality": audio_quality,
                        },
                        severity=EventSeverity.INFO
                    )
                except Exception as e:
                    logger.warning(f"Failed to emit download started event for episode {episode_id}: {e}")
            
            progress.started_at = datetime.utcnow()
            progress.status = TaskStatus.PROCESSING
            
            # Get episode details
            episode = await bg_episode_repository.get_by_id(episode_id)
            if not episode:
                raise Exception(f"Episode {episode_id} not found")
            
            # Create progress hook for yt-dlp
            def progress_hook(d):
                try:
                    progress.update_progress(d)
                except Exception as e:
                    logger.warning(f"Progress callback error: {e}")
            
            logger.info(f"Starting download for episode {episode_id}: {episode.title}")
            
            # Download audio with timeout
            try:
                download_task = self.youtube_service.download_audio(
                    episode.video_url,
                    output_path=None,
                    progress_callback=progress_hook,
                    audio_language=audio_language,
                    audio_quality=audio_quality
                )

                result = await asyncio.wait_for(
                    download_task,
                    timeout=self.download_timeout
                )
                file_path, format_info = result
            except asyncio.TimeoutError:
                raise YouTubeDownloadError(f"Download timed out after {self.download_timeout} seconds")

            # Set audio preferences on episode entity (always call if we have format_info)
            if format_info and (audio_language or audio_quality):
                episode.set_audio_preferences(
                    requested_language=audio_language,
                    requested_quality=audio_quality,
                    actual_language=format_info.get('actual_language'),
                    actual_quality=format_info.get('actual_quality')
                )

            # Process and store file
            logger.info(f"Processing downloaded file for episode {episode_id}")
            final_path = await self.file_service.process_audio_file(
                file_path, episode
            )
            
            # Update episode with file path - enhanced retry with exponential backoff + jitter
            max_retries = 5
            base_delay = 1.0  # Base delay in seconds
            max_delay = 30.0  # Maximum delay cap
            
            for attempt in range(max_retries):
                try:
                    logger.info(f"Attempting to update episode {episode_id} status (attempt {attempt + 1}/{max_retries})")
                    
                    episode.mark_as_completed(final_path)
                    await bg_episode_repository.update(episode)
                    
                    # Commit the session explicitly
                    await bg_session.commit()
                    
                    # Log successful commit
                    log_database_operation('commit', session_id, f'episode {episode_id} completed')
                    logger.info(f"Successfully updated episode {episode_id} to completed status")
                    break  # Success, exit retry loop
                    
                except Exception as db_error:
                    is_database_locked = "database is locked" in str(db_error).lower()
                    is_retry_needed = is_database_locked and attempt < max_retries - 1
                    
                    # Log database lock detection
                    if is_database_locked:
                        log_database_operation('database_lock', session_id, f'episode {episode_id}, attempt {attempt + 1}')
                    
                    if is_retry_needed:
                        # Calculate exponential backoff with jitter
                        exponential_delay = min(base_delay * (2 ** attempt), max_delay)
                        jitter = random.uniform(0.1, 0.5) * exponential_delay
                        retry_delay = exponential_delay + jitter
                        
                        logger.warning(
                            f"Database locked for episode {episode_id} on attempt {attempt + 1}/{max_retries}, "
                            f"retrying in {retry_delay:.2f}s (exponential backoff + jitter)"
                        )
                        
                        try:
                            # Rollback current session
                            await bg_session.rollback()
                            
                            # Log rollback operation
                            log_database_operation('rollback', session_id, f'retry attempt {attempt + 1} for episode {episode_id}')
                            logger.debug(f"Rolled back session for episode {episode_id} retry")
                        except Exception as rollback_error:
                            logger.warning(f"Error during rollback for episode {episode_id}: {rollback_error}")
                        
                        # Wait with exponential backoff + jitter
                        await asyncio.sleep(retry_delay)
                        
                        # Refresh episode entity from database for next attempt
                        try:
                            episode = await bg_episode_repository.get_by_id(episode_id)
                            if not episode:
                                raise Exception(f"Episode {episode_id} not found during retry")
                            logger.debug(f"Refreshed episode {episode_id} entity for retry")
                        except Exception as refresh_error:
                            logger.error(f"Failed to refresh episode {episode_id} for retry: {refresh_error}")
                            raise refresh_error
                            
                    else:
                        # Final attempt failed or different error type
                        if is_database_locked:
                            logger.error(
                                f"Database remained locked for episode {episode_id} after {max_retries} attempts, "
                                f"final error: {db_error}"
                            )
                        else:
                            logger.error(f"Non-lock database error for episode {episode_id}: {db_error}")
                        raise db_error
            
            # Mark progress as completed
            progress.status = TaskStatus.COMPLETED
            progress.completed_at = datetime.utcnow()

            # Emit enriched download completed event and fallback notification
            if event_service and user_id and format_info:
                try:
                    await event_service.log_user_action(
                        channel_id=channel_id or 1,
                        user_id=user_id,
                        action="download_completed",
                        resource_type="episode",
                        resource_id=str(episode_id),
                        message="Episode download completed",
                        details={
                            "actual_language": format_info.get('actual_language'),
                            "actual_quality": format_info.get('actual_quality'),
                            "fallback_occurred": format_info.get('fallback_occurred', False),
                            "fallback_reason": format_info.get('fallback_reason'),
                        },
                        severity=EventSeverity.INFO
                    )
                except Exception as e:
                    logger.warning(f"Failed to emit download completed event: {e}")

                # Create notification if fallback occurred
                if format_info.get('fallback_occurred'):
                    try:
                        notification_session = await get_background_task_session()
                        try:
                            from app.infrastructure.repositories.notification_repository_impl import NotificationRepositoryImpl
                            from app.application.services.notification_service import NotificationService
                            from app.domain.entities.notification import NotificationType
                            notification_repo = NotificationRepositoryImpl(notification_session)
                            notification_service = NotificationService(notification_repo)
                            await notification_service.create_notification(
                                user_id=user_id,
                                notification_type=NotificationType.EPISODE_CREATED,
                                title="Audio Quality Fallback",
                                message=(
                                    f"Requested {audio_language or 'default'}/{audio_quality or 'default'}, "
                                    f"downloaded {format_info.get('actual_language') or 'original'}/"
                                    f"{format_info.get('actual_quality') or 'best'}: "
                                    f"{format_info.get('fallback_reason', 'N/A')}"
                                ),
                                data={"episode_id": episode_id}
                            )
                            await notification_session.commit()
                        finally:
                            await notification_session.close()
                    except Exception as notif_err:
                        logger.warning(f"Failed to create fallback notification: {notif_err}")

            logger.info(f"Successfully downloaded episode {episode_id}: {episode.title}")

            return {
                "status": "success",
                "episode_id": episode_id,
                "message": "Episode downloaded successfully",
                "file_path": final_path
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Download failed for episode {episode_id}: {error_msg}")
            logger.debug(f"Download error traceback: {traceback.format_exc()}")
            
            # Mark progress as failed
            progress.mark_failed(error_msg)
            
            # Update episode retry count and status using background session
            try:
                episode = await bg_episode_repository.get_by_id(episode_id)
                if episode:
                    episode.increment_retry_count()
                    
                    # Check if we should retry
                    if episode.can_retry():
                        episode.status = EpisodeStatus.PENDING
                        logger.info(f"Episode {episode_id} will be retried (attempt {episode.retry_count})")
                    else:
                        episode.status = EpisodeStatus.FAILED
                        logger.warning(f"Episode {episode_id} failed after {episode.retry_count} attempts")
                    
                    await bg_episode_repository.update(episode)
                    await bg_session.commit()
            except Exception as update_error:
                logger.error(f"Failed to update episode status after download failure: {update_error}")
                await bg_session.rollback()
            
            return {
                "status": "error",
                "episode_id": episode_id,
                "message": error_msg
            }
            
        finally:
            # Always close the background session
            session_id = getattr(bg_session, '_session_id', id(bg_session))
            try:
                await bg_session.close()
                # Log session closure
                log_database_operation('close', session_id, f'celery download task for episode {episode_id}')
            except Exception as close_error:
                logger.warning(f"Error closing background session {session_id}: {close_error}")





