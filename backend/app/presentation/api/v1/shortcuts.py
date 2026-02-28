"""
iOS Shortcuts API endpoints

This module provides simplified API endpoints specifically designed for iOS Shortcuts,
allowing users to add podcast episodes from YouTube directly from the iOS Share Sheet
without exposing the main API key.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field, field_validator
from typing import Optional
import logging

from app.application.services.episode_service import EpisodeService
from app.application.services.url_validation_service import URLValidationService
from app.infrastructure.services.download_service import DownloadService
from app.infrastructure.services.youtube_service import YouTubeExtractionError
from app.core.dependencies import get_episode_service, get_url_validation_service, get_download_service
from app.core.auth import require_shortcut_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/shortcuts", tags=["shortcuts"])


class ShortcutEpisodeRequest(BaseModel):
    """Request schema for creating episode via iOS Shortcut"""
    video_url: str = Field(
        ...,
        description="YouTube video URL",
        examples=["https://www.youtube.com/watch?v=dQw4w9WgXcQ"]
    )
    channel_id: int = Field(
        default=1,
        gt=0,
        description="Channel ID to add episode to (defaults to 1)"
    )

    @field_validator('video_url')
    @classmethod
    def validate_url_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Video URL cannot be empty")
        return v.strip()


class ShortcutEpisodeResponse(BaseModel):
    """Simplified response schema for iOS Shortcut"""
    success: bool
    message: str
    episode_id: Optional[int] = None
    title: Optional[str] = None
    error_code: Optional[str] = None


async def _isolated_download_queue(download_service, episode_id: int):
    """
    Helper function to queue download with proper session isolation
    (Same implementation as in episodes.py)
    """
    import asyncio

    try:
        # Wait to ensure API request session is fully closed
        logger.info(f"Waiting for API session cleanup before starting download for episode {episode_id}")
        await asyncio.sleep(3)

        from fastapi import BackgroundTasks

        background_tasks = BackgroundTasks()

        logger.info(f"Starting isolated download queue for episode {episode_id}")
        success = await download_service.queue_download(episode_id, background_tasks)
        if success:
            logger.info(f"Successfully queued download for episode {episode_id}")
        else:
            logger.warning(f"Failed to queue download for episode {episode_id}")
    except Exception as e:
        logger.error(f"Error in isolated download queue for episode {episode_id}: {e}")


@router.post("/episode", response_model=ShortcutEpisodeResponse, status_code=201)
async def create_episode_from_shortcut(
    request: ShortcutEpisodeRequest,
    background_tasks: BackgroundTasks,
    _: bool = Depends(require_shortcut_key),
    episode_service: EpisodeService = Depends(get_episode_service),
    url_validator: URLValidationService = Depends(get_url_validation_service),
    download_service: DownloadService = Depends(get_download_service)
):
    """
    Create a new podcast episode from YouTube URL via iOS Shortcut

    This endpoint is specifically designed for iOS Shortcuts integration:
    - Simple request/response format optimized for notifications
    - Separate API key authentication for security
    - Streamlined error messages
    - No complex transaction handling exposed

    Usage:
    1. Share a YouTube video in iOS
    2. Select your LabCastARR shortcut
    3. Episode is automatically created and downloaded

    Authentication:
    - Requires X-Shortcut-Key header with valid shortcut API key
    - Get your key from the LabCastARR settings page

    Args:
        request: YouTube video URL and optional channel ID
        background_tasks: FastAPI background tasks for async download
        _: Shortcut API key validation (injected dependency)
        episode_service: Episode service for business logic
        url_validator: URL validation service
        download_service: Download service for background processing

    Returns:
        ShortcutEpisodeResponse with success status and episode details

    Raises:
        HTTPException: For various error conditions with appropriate status codes
    """
    try:
        logger.info(f"[Shortcut] Creating episode from URL: {request.video_url}")

        # Validate YouTube URL
        validation = url_validator.validate_youtube_url(request.video_url)
        if not validation['valid']:
            logger.warning(f"[Shortcut] Invalid YouTube URL: {validation['error']}")
            return ShortcutEpisodeResponse(
                success=False,
                message=validation['error'],
                error_code=validation.get('error_code', 'INVALID_URL')
            )

        # Create episode with metadata extraction
        episode = await episode_service.create_from_youtube_url(
            channel_id=request.channel_id,
            video_url=validation['normalized_url'],
            tags=[]  # No tags for shortcut-created episodes
        )

        # Commit transaction and close session
        episode_repo = episode_service.episode_repository

        from app.infrastructure.database.connection import log_database_operation

        session_id = getattr(episode_repo.db_session, '_session_id', id(episode_repo.db_session))

        await episode_repo.db_session.commit()
        log_database_operation('commit', session_id, f'episode {episode.id} created via shortcut')
        logger.info(f"[Shortcut] Transaction committed for episode {episode.id}")

        episode_id = episode.id
        episode_title = episode.title

        # Close session
        try:
            await episode_repo.db_session.close()
            log_database_operation('close', session_id, f'Shortcut API request for episode {episode_id}')
            logger.info(f"[Shortcut] API session closed for episode {episode_id}")
        except Exception as session_close_error:
            logger.warning(f"[Shortcut] Error closing API session for episode {episode_id}: {session_close_error}")

        # Queue background download with session isolation
        background_tasks.add_task(
            _isolated_download_queue,
            download_service,
            episode_id
        )

        logger.info(f"[Shortcut] Successfully created episode {episode_id}: {episode_title}")

        return ShortcutEpisodeResponse(
            success=True,
            message=f"Episode '{episode_title}' added successfully! Download starting...",
            episode_id=episode_id,
            title=episode_title
        )

    except YouTubeExtractionError as e:
        logger.error(f"[Shortcut] YouTube extraction failed: {e}")
        return ShortcutEpisodeResponse(
            success=False,
            message=f"Could not extract video info: {str(e)}",
            error_code="YOUTUBE_EXTRACTION_ERROR"
        )

    except ValueError as e:
        logger.error(f"[Shortcut] Validation error: {e}")
        return ShortcutEpisodeResponse(
            success=False,
            message=str(e),
            error_code="VALIDATION_ERROR"
        )

    except Exception as e:
        logger.error(f"[Shortcut] Unexpected error creating episode: {e}")
        return ShortcutEpisodeResponse(
            success=False,
            message="Failed to create episode. Please try again.",
            error_code="INTERNAL_ERROR"
        )


@router.get("/health", response_model=dict)
async def shortcut_health_check(_: bool = Depends(require_shortcut_key)):
    """
    Health check endpoint for iOS Shortcuts integration

    Use this endpoint to verify that:
    - Your shortcut API key is valid
    - The shortcut API is available
    - Your device can reach the server

    Returns:
        dict: Health status information
    """
    return {
        "status": "healthy",
        "message": "iOS Shortcuts API is operational",
        "api_version": "v1"
    }