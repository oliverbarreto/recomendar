"""
Download service for handling background episode downloads
"""
from fastapi import BackgroundTasks
from typing import Callable, Optional, Dict, Any
import asyncio
import logging
from datetime import datetime, timedelta
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


class DownloadProgress:
    """Download progress information with business event tracking"""

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


class DownloadService:
    """
    Service for managing background episode downloads
    """
    
    def __init__(
        self,
        youtube_service: YouTubeService,
        file_service: 'FileService',
        episode_repository: EpisodeRepository
    ):
        self.youtube_service = youtube_service
        self.file_service = file_service
        self.episode_repository = episode_repository
        
        # Track active downloads and progress
        self.active_downloads: Dict[int, asyncio.Task] = {}
        self.download_progress: Dict[int, DownloadProgress] = {}
        self.download_queue = None  # Will be initialized when needed
        
        # Resource limits
        self.max_concurrent = settings.max_concurrent_downloads
        self.download_timeout = settings.download_timeout_minutes * 60
        
        # Queue processor - will be started when needed
        self._queue_processor_task = None
        self._initialized = False
    
    async def _ensure_initialized(self):
        """Ensure the download service is properly initialized"""
        if not self._initialized:
            # Initialize async components
            self.download_queue = asyncio.Queue(maxsize=settings.task_queue_size)
            self._initialized = True
            # Start the queue processor
            self._start_queue_processor()
    
    def _start_queue_processor(self):
        """Start the background queue processor"""
        try:
            if self._queue_processor_task is None or self._queue_processor_task.done():
                self._queue_processor_task = asyncio.create_task(self._process_queue())
                logger.info("Started download queue processor")
        except RuntimeError as e:
            # If we're not in an async context, log a warning - the processor will be started later
            logger.warning(f"Could not start queue processor immediately: {e}")
            logger.info("Queue processor will be started when first download is queued")
    
    async def queue_download(
        self,
        episode_id: int,
        background_tasks: BackgroundTasks,
        progress_callback: Optional[Callable] = None,
        priority: int = 0,
        user_id: Optional[int] = None,
        channel_id: Optional[int] = None,
        event_service: Optional[EventService] = None,
        audio_language: Optional[str] = None,
        audio_quality: Optional[str] = None
    ) -> bool:
        """
        Queue episode download as background task

        Args:
            episode_id: Episode ID to download
            background_tasks: FastAPI background tasks
            progress_callback: Optional progress callback
            priority: Task priority (higher = more priority)
            user_id: User ID for event tracking
            channel_id: Channel ID for event tracking
            event_service: Event service for business event tracking

        Returns:
            True if queued successfully, False otherwise
        """
        try:
            # Ensure service is initialized
            await self._ensure_initialized()
            
            # Check if already downloading
            if episode_id in self.active_downloads:
                logger.warning(f"Episode {episode_id} is already being downloaded")
                return False
            
            # Update episode status to processing
            await self.episode_repository.update_status(
                episode_id, 
                EpisodeStatus.PROCESSING
            )
            
            # Create progress tracker with business event tracking
            progress = DownloadProgress(
                episode_id=episode_id,
                event_service=event_service,
                user_id=user_id,
                channel_id=channel_id
            )
            self.download_progress[episode_id] = progress

            # Emit download started event
            if event_service and user_id:
                try:
                    await event_service.log_user_action(
                        channel_id=channel_id or 1,
                        user_id=user_id,
                        action="download_started",
                        resource_type="episode",
                        resource_id=str(episode_id),
                        message="Episode download queued and started",
                        details={"priority": priority},
                        severity=EventSeverity.INFO
                    )
                except Exception as e:
                    logger.warning(f"Failed to emit download started event for episode {episode_id}: {e}")
            
            # Add to queue
            queue_item = {
                'episode_id': episode_id,
                'priority': priority,
                'progress_callback': progress_callback,
                'queued_at': datetime.utcnow(),
                'audio_language': audio_language,
                'audio_quality': audio_quality
            }
            
            await self.download_queue.put(queue_item)
            
            logger.info(f"Queued download for episode {episode_id} (priority: {priority})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to queue download for episode {episode_id}: {e}")
            # Clean up on failure
            if episode_id in self.download_progress:
                del self.download_progress[episode_id]
            return False
    
    async def _process_queue(self):
        """Main queue processing loop"""
        while True:
            try:
                # Wait for queue items
                if len(self.active_downloads) >= self.max_concurrent:
                    await asyncio.sleep(1)
                    continue
                
                try:
                    queue_item = await asyncio.wait_for(
                        self.download_queue.get(), 
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                episode_id = queue_item['episode_id']
                
                # Start download task
                download_task = asyncio.create_task(
                    self._download_episode_task(
                        episode_id,
                        queue_item['progress_callback'],
                        audio_language=queue_item.get('audio_language'),
                        audio_quality=queue_item.get('audio_quality')
                    )
                )
                
                # Track active download
                self.active_downloads[episode_id] = download_task
                
                # Set up completion callback
                download_task.add_done_callback(
                    lambda task, eid=episode_id: self._on_download_complete(eid, task)
                )
                
                logger.info(f"Started download task for episode {episode_id}")
                
            except Exception as e:
                logger.error(f"Error in queue processor: {e}")
                await asyncio.sleep(5)  # Brief pause on error
    
    def _on_download_complete(self, episode_id: int, task: asyncio.Task):
        """Callback when download task completes"""
        try:
            # Remove from active downloads
            if episode_id in self.active_downloads:
                del self.active_downloads[episode_id]
            
            # Check task result
            if task.exception():
                logger.error(f"Download task failed for episode {episode_id}: {task.exception()}")
            else:
                logger.info(f"Download task completed for episode {episode_id}")
                
        except Exception as e:
            logger.error(f"Error in download completion callback: {e}")
    
    async def _download_episode_task(
        self,
        episode_id: int,
        progress_callback: Optional[Callable] = None,
        audio_language: Optional[str] = None,
        audio_quality: Optional[str] = None
    ):
        """Background task to download episode audio"""
        progress = self.download_progress.get(episode_id)
        if not progress:
            logger.error(f"No progress tracker found for episode {episode_id}")
            return
        
        # Create fresh database session for background task
        from app.infrastructure.database.connection import get_background_task_session, log_database_operation
        from app.infrastructure.repositories.episode_repository import EpisodeRepositoryImpl
        
        bg_session = await get_background_task_session()
        bg_episode_repository = EpisodeRepositoryImpl(bg_session)
        
        # Log session creation
        session_id = getattr(bg_session, '_session_id', id(bg_session))
        log_database_operation('session_created', session_id, f'background task for episode {episode_id}')
        
        try:
            progress.started_at = datetime.utcnow()
            progress.status = TaskStatus.PROCESSING
            
            # Get episode details using background task repository
            episode = await bg_episode_repository.get_by_id(episode_id)
            if not episode:
                raise Exception(f"Episode {episode_id} not found")
            
            # Create progress hook for yt-dlp
            def progress_hook(d):
                try:
                    progress.update_progress(d)
                    if progress_callback:
                        progress_callback(progress.to_dict())
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

            # Set audio preferences on episode entity
            if audio_language or audio_quality:
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
            max_retries = 5  # Increased from 3 to 5
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
            
            logger.info(f"Successfully downloaded episode {episode_id}: {episode.title}")
            
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
            
            # Re-raise for task tracking
            raise
        finally:
            # Always close the background session
            session_id = getattr(bg_session, '_session_id', id(bg_session))
            try:
                await bg_session.close()
                # Log session closure
                log_database_operation('close', session_id, f'background task for episode {episode_id}')
            except Exception as close_error:
                logger.warning(f"Error closing background session {session_id}: {close_error}")
    
    def get_download_progress(self, episode_id: int) -> Optional[Dict[str, Any]]:
        """Get current download progress for an episode"""
        progress = self.download_progress.get(episode_id)
        if progress:
            return progress.to_dict()
        return None
    
    def get_active_downloads(self) -> Dict[int, Dict[str, Any]]:
        """Get all active download progress"""
        return {
            episode_id: progress.to_dict() 
            for episode_id, progress in self.download_progress.items()
            if progress.status in [TaskStatus.QUEUED, TaskStatus.PROCESSING]
        }
    
    def get_download_stats(self) -> Dict[str, Any]:
        """Get download service statistics"""
        active_count = len([
            p for p in self.download_progress.values()
            if p.status in [TaskStatus.QUEUED, TaskStatus.PROCESSING]
        ])
        
        completed_count = len([
            p for p in self.download_progress.values()
            if p.status == TaskStatus.COMPLETED
        ])
        
        failed_count = len([
            p for p in self.download_progress.values()
            if p.status == TaskStatus.FAILED
        ])
        
        queue_size = self.download_queue.qsize() if self.download_queue else 0
        
        return {
            'active_downloads': active_count,
            'completed_downloads': completed_count,
            'failed_downloads': failed_count,
            'queue_size': queue_size,
            'max_concurrent': self.max_concurrent,
            'processor_running': self._queue_processor_task and not self._queue_processor_task.done()
        }
    
    async def cancel_download(self, episode_id: int) -> bool:
        """Cancel a download if it's in progress"""
        try:
            # Cancel active task
            if episode_id in self.active_downloads:
                task = self.active_downloads[episode_id]
                task.cancel()
                
                # Update progress
                if episode_id in self.download_progress:
                    progress = self.download_progress[episode_id]
                    progress.status = TaskStatus.CANCELLED
                    progress.completed_at = datetime.utcnow()
                
                logger.info(f"Cancelled download for episode {episode_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to cancel download for episode {episode_id}: {e}")
            return False
    
    async def retry_failed_download(
        self, 
        episode_id: int,
        background_tasks: BackgroundTasks
    ) -> bool:
        """Retry a failed download"""
        from app.infrastructure.database.connection import get_background_task_session
        from app.infrastructure.repositories.episode_repository import EpisodeRepositoryImpl
        
        bg_session = await get_background_task_session()
        bg_episode_repository = EpisodeRepositoryImpl(bg_session)
        
        try:
            episode = await bg_episode_repository.get_by_id(episode_id)
            if not episode:
                return False
            
            if episode.status != EpisodeStatus.FAILED:
                logger.warning(f"Episode {episode_id} is not in failed state")
                return False
            
            if not episode.can_retry():
                logger.warning(f"Episode {episode_id} has exceeded retry limit")
                return False
            
            # Reset episode for retry
            episode.reset_for_retry()
            await bg_episode_repository.update(episode)
            await bg_session.commit()
            
            # Clear old progress
            if episode_id in self.download_progress:
                del self.download_progress[episode_id]
            
            # Queue for retry
            return await self.queue_download(episode_id, background_tasks, priority=1)
            
        except Exception as e:
            logger.error(f"Failed to retry download for episode {episode_id}: {e}")
            await bg_session.rollback()
            return False
        finally:
            await bg_session.close()
    
    async def cleanup_old_progress(self, max_age_hours: int = 24):
        """Clean up old progress entries"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            
            to_remove = []
            for episode_id, progress in self.download_progress.items():
                if (progress.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] 
                    and progress.completed_at 
                    and progress.completed_at < cutoff_time):
                    to_remove.append(episode_id)
            
            for episode_id in to_remove:
                del self.download_progress[episode_id]
                logger.debug(f"Cleaned up old progress for episode {episode_id}")
            
            if to_remove:
                logger.info(f"Cleaned up {len(to_remove)} old progress entries")
                
        except Exception as e:
            logger.error(f"Error during progress cleanup: {e}")
    
    async def shutdown(self):
        """Shutdown the download service gracefully"""
        try:
            logger.info("Shutting down download service...")
            
            # Cancel queue processor
            if self._queue_processor_task and not self._queue_processor_task.done():
                self._queue_processor_task.cancel()
                try:
                    await self._queue_processor_task
                except asyncio.CancelledError:
                    pass
            
            # Cancel all active downloads
            for episode_id, task in list(self.active_downloads.items()):
                logger.info(f"Cancelling download for episode {episode_id}")
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            self.active_downloads.clear()
            logger.info("Download service shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during download service shutdown: {e}")