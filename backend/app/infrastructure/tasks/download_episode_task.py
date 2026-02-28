"""
Celery task for downloading episode audio files

This task wraps the CeleryDownloadService to download episodes within Celery's
execution context. It's designed to work independently from FastAPI's DownloadService.
"""
from celery import shared_task
import logging
import asyncio
from typing import Optional

from app.infrastructure.database.connection import get_background_task_session
from app.infrastructure.repositories.episode_repository import EpisodeRepositoryImpl
from app.infrastructure.services.celery_download_service import CeleryDownloadService
from app.infrastructure.services.youtube_service import YouTubeService
from app.infrastructure.services.file_service import FileService

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Helper to run async function in Celery task"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@shared_task(
    name="app.infrastructure.tasks.download_episode_task.download_episode",
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True
)
def download_episode(
    self,
    episode_id: int,
    user_id: Optional[int] = None,
    channel_id: Optional[int] = None,
    audio_language: Optional[str] = None,
    audio_quality: Optional[str] = None
) -> dict:
    """
    Download an episode's audio file from YouTube
    
    This Celery task:
    1. Creates a CeleryDownloadService instance
    2. Downloads the episode audio file
    3. Processes and stores the file
    4. Updates episode status to completed
    
    Args:
        episode_id: ID of the episode to download
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
    async def _download():
        # Initialize services
        youtube_service = YouTubeService()
        file_service = FileService()
        
        # Create a session for the repository
        session = await get_background_task_session()
        try:
            episode_repository = EpisodeRepositoryImpl(session)
            
            # Create CeleryDownloadService
            download_service = CeleryDownloadService(
                youtube_service=youtube_service,
                file_service=file_service,
                episode_repository=episode_repository
            )
            
            # Optional: Get event service if user_id is provided
            event_service = None
            if user_id:
                try:
                    from app.application.services.event_service import EventService
                    from app.infrastructure.repositories.event_repository_impl import EventRepositoryImpl
                    event_repository = EventRepositoryImpl(session)
                    event_service = EventService(event_repository)
                except Exception as e:
                    logger.warning(f"Could not initialize event service: {e}")
                    # Continue without event service - it's optional
            
            # Download the episode
            logger.info(f"Starting Celery download task for episode {episode_id}")
            result = await download_service.download_episode(
                episode_id=episode_id,
                event_service=event_service,
                user_id=user_id,
                channel_id=channel_id,
                audio_language=audio_language,
                audio_quality=audio_quality
            )
            
            logger.info(f"Celery download task completed for episode {episode_id}: {result.get('status')}")
            return result
            
        finally:
            await session.close()
    
    logger.info(f"Queued Celery download task for episode {episode_id}")
    return _run_async(_download())

