"""
Episode API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, UploadFile, File, Form
from typing import List, Optional
import logging
from datetime import datetime

from app.presentation.schemas.episode_schemas import (
    EpisodeCreate, EpisodeUpdate, EpisodeResponse, EpisodeListResponse,
    ProgressResponse, EpisodeStatusResponse, MetadataAnalysisRequest, 
    MetadataAnalysisResponse, ErrorResponse, SuccessResponse, EpisodeCreateFromUpload
)
from app.application.services.episode_service import EpisodeService
from app.application.services.url_validation_service import URLValidationService
from app.application.services.metadata_processing_service import MetadataProcessingService
from app.application.services.upload_processing_service import UploadProcessingService
from app.infrastructure.services.youtube_service import YouTubeService, YouTubeExtractionError
from app.infrastructure.services.download_service import DownloadService
from app.infrastructure.services.file_service import FileService
from app.infrastructure.services.upload_service import (
    FileValidationError,
    FileSizeLimitError,
    FileConversionError,
    DuplicateEpisodeError
)
from app.domain.repositories.episode import EpisodeRepository
from app.core.dependencies import (
    get_episode_service,
    get_url_validation_service,
    get_download_service,
    get_file_service,
    get_upload_processing_service
)
from app.presentation.api.v1.media import detect_audio_mime_type
from app.core.config import settings
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/episodes", tags=["episodes"])


async def _isolated_download_queue(
    download_service, episode_id: int,
    audio_language: str = None, audio_quality: str = None
):
    """
    DEPRECATED: This function is no longer used. Episode downloads now go through Celery tasks.
    Kept for backward compatibility during transition period.
    """
    import asyncio

    try:
        # CRITICAL: Wait 3 seconds to ensure API request session is fully closed
        # This prevents concurrent database access that causes SQLite locks
        logger.info(f"Waiting for API session cleanup before starting download for episode {episode_id}")
        await asyncio.sleep(3)

        from fastapi import BackgroundTasks

        # Create new background tasks instance for isolated execution
        background_tasks = BackgroundTasks()

        # Queue download - DownloadService will create its own fresh session
        logger.info(f"Starting isolated download queue for episode {episode_id}")
        success = await download_service.queue_download(
            episode_id, background_tasks,
            audio_language=audio_language,
            audio_quality=audio_quality
        )
        if success:
            logger.info(f"Successfully queued download for episode {episode_id}")
        else:
            logger.warning(f"Failed to queue download for episode {episode_id}")
    except Exception as e:
        logger.error(f"Error in isolated download queue for episode {episode_id}: {e}")


# IMPORTANT: Upload route must come BEFORE the root "/" route
# to ensure FastAPI matches the more specific path first
@router.post("/upload", response_model=EpisodeResponse, status_code=201)
async def upload_episode(
    channel_id: int = Form(..., gt=0, description="Channel ID to associate episode with"),
    title: str = Form(..., min_length=1, max_length=500, description="Episode title"),
    description: Optional[str] = Form(None, max_length=5000, description="Episode description"),
    publication_date: Optional[str] = Form(None, description="Publication date (ISO format, defaults to now)"),
    tags: Optional[List[str]] = Form(None, description="Optional tags for the episode"),
    audio_file: UploadFile = File(..., description="Audio file to upload"),
    episode_service: EpisodeService = Depends(get_episode_service),
    upload_processing_service: UploadProcessingService = Depends(get_upload_processing_service),
    file_service: FileService = Depends(get_file_service)
):
    """
    Create a new episode by uploading an audio file

    This endpoint:
    1. Validates the uploaded audio file (format, size)
    2. Streams the file to disk for memory efficiency
    3. Converts to MP3 if needed (WAV, FLAC, OGG → MP3)
    4. Extracts audio metadata (duration, bitrate)
    5. Creates episode entity with status "completed"
    6. Returns episode with all metadata

    Supported formats: MP3, M4A, WAV, OGG, FLAC
    Maximum file size: 500MB (configurable)

    Note: If episode creation fails (e.g., duplicate title), the uploaded file
    is automatically cleaned up to prevent orphaned files.
    """
    stored_file_path = None  # Track stored file for cleanup on error

    try:
        logger.info(f"Upload episode request: {title} for channel {channel_id}")

        # Validate file size before processing
        if audio_file.size and audio_file.size > settings.max_upload_file_size_mb * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail={
                    "error": f"File size exceeds maximum allowed size of {settings.max_upload_file_size_mb}MB",
                    "code": "FILE_TOO_LARGE",
                    "max_size_mb": settings.max_upload_file_size_mb
                }
            )

        # Parse publication date
        pub_date = datetime.utcnow()
        if publication_date:
            try:
                pub_date = datetime.fromisoformat(publication_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "Invalid publication date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)",
                        "code": "INVALID_DATE_FORMAT"
                    }
                )

        # Process uploaded file (streaming, validation, conversion)
        logger.info(f"Processing uploaded file: {audio_file.filename}")
        processing_result = await upload_processing_service.process_uploaded_episode(
            upload_file=audio_file,
            channel_id=channel_id,
            episode_title=title
        )

        # IMPORTANT: Store file path for cleanup if episode creation fails
        stored_file_path = processing_result['file_path']
        logger.debug(f"File stored at: {stored_file_path} (will be cleaned up if episode creation fails)")

        # Create episode from upload
        logger.info(f"Creating episode from upload: {title}")
        episode = await episode_service.create_from_upload(
            channel_id=channel_id,
            title=title,
            description=description,
            publication_date=pub_date,
            audio_file_path=processing_result['file_path'],
            file_size=processing_result['file_size'],
            duration_seconds=processing_result['duration_seconds'],
            original_filename=processing_result['original_filename'],
            tags=tags
        )

        # Commit the transaction
        await episode_service.episode_repository.db_session.commit()

        logger.info(f"Successfully created episode from upload {episode.id}: {episode.title}")
        return EpisodeResponse.from_entity(episode)

    except FileSizeLimitError as e:
        # File size errors occur before storage, no cleanup needed
        logger.error(f"File size limit exceeded: {e}")
        raise HTTPException(
            status_code=413,
            detail={
                "error": str(e),
                "code": "FILE_TOO_LARGE",
                "max_size_mb": settings.max_upload_file_size_mb
            }
        )
    except FileValidationError as e:
        # File validation errors are handled by upload_processing_service
        # Temp files are already cleaned up, no final file stored yet
        logger.error(f"File validation failed: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": str(e),
                "code": "INVALID_FILE_FORMAT",
                "allowed_formats": settings.allowed_upload_formats
            }
        )
    except FileConversionError as e:
        # Conversion errors are handled by upload_processing_service
        # Temp files are already cleaned up, no final file stored yet
        logger.error(f"File conversion failed: {e}")
        raise HTTPException(
            status_code=422,
            detail={
                "error": str(e),
                "code": "FILE_CONVERSION_ERROR"
            }
        )
    except DuplicateEpisodeError as e:
        # CRITICAL: File was stored but episode creation failed due to duplicate
        # Clean up the stored file to prevent orphaning
        logger.error(f"Duplicate episode detected: {e}")

        if stored_file_path:
            logger.info(f"Cleaning up stored file due to duplicate episode: {stored_file_path}")
            cleanup_success = await file_service.delete_episode_file(stored_file_path)

            if cleanup_success:
                logger.info(f"Successfully cleaned up orphaned file: {stored_file_path}")
            else:
                logger.warning(f"Failed to clean up file {stored_file_path} - may become orphaned")

        raise HTTPException(
            status_code=409,
            detail={
                "error": str(e),
                "code": "DUPLICATE_EPISODE"
            }
        )
    except ValueError as e:
        # ValueError can occur during episode creation (after file storage)
        # Clean up the stored file
        logger.error(f"Validation error during episode creation: {e}")

        if stored_file_path:
            logger.info(f"Cleaning up stored file due to validation error: {stored_file_path}")
            cleanup_success = await file_service.delete_episode_file(stored_file_path)

            if cleanup_success:
                logger.info(f"Successfully cleaned up orphaned file: {stored_file_path}")
            else:
                logger.warning(f"Failed to clean up file {stored_file_path} - may become orphaned")

        raise HTTPException(
            status_code=400,
            detail={
                "error": str(e),
                "code": "VALIDATION_ERROR"
            }
        )
    except Exception as e:
        # Unexpected errors after file storage - clean up the stored file
        logger.error(f"Unexpected error uploading episode: {e}")
        import traceback
        logger.debug(f"Traceback: {traceback.format_exc()}")

        if stored_file_path:
            logger.info(f"Cleaning up stored file due to unexpected error: {stored_file_path}")
            try:
                cleanup_success = await file_service.delete_episode_file(stored_file_path)

                if cleanup_success:
                    logger.info(f"Successfully cleaned up orphaned file: {stored_file_path}")
                else:
                    logger.warning(f"Failed to clean up file {stored_file_path} - may become orphaned")
            except Exception as cleanup_error:
                logger.error(f"Error during file cleanup: {cleanup_error}")

        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "code": "INTERNAL_ERROR"
            }
        )


@router.post("/", response_model=EpisodeResponse, status_code=201)
async def create_episode(
    episode_data: EpisodeCreate,
    episode_service: EpisodeService = Depends(get_episode_service),
    url_validator: URLValidationService = Depends(get_url_validation_service),
):
    """
    Create a new episode from YouTube URL

    This endpoint:
    1. Validates the YouTube URL format
    2. Extracts video metadata from YouTube
    3. Creates episode entity in database
    4. COMMITS the transaction explicitly
    5. Queues Celery download task
    6. Returns episode with initial status
    """
    try:
        logger.info(f"Creating episode from URL: {episode_data.video_url}")

        # Validate YouTube URL
        validation = url_validator.validate_youtube_url(episode_data.video_url)
        if not validation['valid']:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": validation['error'],
                    "code": validation.get('error_code', 'INVALID_URL')
                }
            )

        # Create episode with metadata extraction
        episode = await episode_service.create_from_youtube_url(
            channel_id=episode_data.channel_id,
            video_url=validation['normalized_url'],
            tags=episode_data.tags,
            requested_language=episode_data.audio_language,
            requested_quality=episode_data.audio_quality
        )

        # CRITICAL: Get the current session and explicitly commit
        # This ensures the episode is fully persisted before Celery task starts
        episode_repo = episode_service.episode_repository

        # Import logging function
        from app.infrastructure.database.connection import log_database_operation

        # Get session ID for logging
        session_id = getattr(episode_repo.db_session, '_session_id', id(episode_repo.db_session))

        await episode_repo.db_session.commit()
        log_database_operation('commit', session_id, f'episode {episode.id} created')
        logger.info(f"Transaction committed for episode {episode.id}")

        # Store episode ID for Celery task
        episode_id = episode.id

        # Close session before queuing Celery task
        try:
            await episode_repo.db_session.close()
            log_database_operation('close', session_id, f'API request for episode {episode_id}')
            logger.info(f"API session closed for episode {episode_id}")
        except Exception as session_close_error:
            logger.warning(f"Error closing API session for episode {episode_id}: {session_close_error}")

        # Queue download via Celery task (replaces BackgroundTasks + DownloadService)
        from app.infrastructure.tasks.download_episode_task import download_episode
        download_episode.apply_async(
            args=(episode_id,),
            kwargs={
                'channel_id': episode_data.channel_id,
                'audio_language': episode_data.audio_language,
                'audio_quality': episode_data.audio_quality
            }
        )

        logger.info(f"Successfully created episode {episode.id}: {episode.title}")
        return EpisodeResponse.from_entity(episode)
        
    except YouTubeExtractionError as e:
        logger.error(f"YouTube extraction failed: {e}")
        raise HTTPException(
            status_code=422,
            detail={
                "error": str(e),
                "code": "YOUTUBE_EXTRACTION_ERROR"
            }
        )
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": str(e),
                "code": "VALIDATION_ERROR"
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error creating episode: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "code": "INTERNAL_ERROR"
            }
        )


@router.get("/", response_model=EpisodeListResponse)
async def list_episodes(
    channel_id: int = Query(..., gt=0, description="Channel ID to filter by"),
    skip: int = Query(0, ge=0, description="Number of episodes to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of episodes to return"),
    status: Optional[str] = Query(None, description="Filter by episode status"),
    search: Optional[str] = Query(None, max_length=500, description="Search in title and description"),
    episode_service: EpisodeService = Depends(get_episode_service)
):
    """
    List episodes with filtering and pagination
    
    Supports filtering by:
    - Channel ID (required)
    - Status (pending, processing, completed, failed)
    - Search query (searches title and description)
    """
    try:
        logger.debug(f"Listing episodes for channel {channel_id}")
        
        episodes, total = await episode_service.list_episodes(
            channel_id=channel_id,
            skip=skip,
            limit=limit,
            status=status,
            search_query=search
        )
        
        episode_responses = [
            EpisodeResponse.from_entity(
                episode, 
                episodes_list=episodes,
                total_count=total,
                skip=skip
            )
            for episode in episodes
        ]
        
        return EpisodeListResponse(
            episodes=episode_responses,
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error listing episodes: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to list episodes",
                "code": "INTERNAL_ERROR"
            }
        )


@router.get("/db-stats", response_model=dict)
async def get_database_statistics():
    """
    Get database connection statistics for monitoring and debugging
    
    This endpoint provides insights into database session usage,
    helping to identify potential connection leaks or performance issues.
    """
    try:
        from app.infrastructure.database.connection import get_connection_stats
        
        stats = get_connection_stats()
        
        return {
            "success": True,
            "message": "Database statistics retrieved successfully",
            "data": {
                "connection_stats": stats,
                "timestamp": datetime.utcnow().isoformat(),
                "database_type": "SQLite with WAL mode"
            }
        }
        
    except Exception as e:
        logger.error(f"Error retrieving database statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to retrieve database statistics",
                "code": "INTERNAL_ERROR"
            }
        )


@router.get("/webm-detection", response_model=dict)
async def detect_webm_files(
    channel_id: int = 1,
    episode_service: EpisodeService = Depends(get_episode_service)
):
    """
    Detect episodes with WebM files disguised as MP3s

    This endpoint scans all completed episodes to identify which ones
    still have WebM file headers instead of proper MP3 format.
    These are the files that need targeted re-download.

    Args:
        channel_id: Channel ID to scan episodes for (default: 1)
    """
    try:
        logger.info(f"Starting WebM detection scan for channel {channel_id}")

        # Get all completed episodes for the channel
        episodes_result = await episode_service.list_episodes(
            channel_id=channel_id,
            status="completed",
            skip=0,
            limit=100
        )

        episodes = episodes_result[0]  # episodes is tuple (episodes, total)

        webm_episodes = []
        valid_mp3_episodes = []
        missing_files = []

        media_path = Path(settings.media_path)

        for episode in episodes:
            if not episode.audio_file_path:
                continue

            file_path = media_path / episode.audio_file_path

            if not file_path.exists():
                missing_files.append({
                    "id": episode.id,
                    "title": episode.title,
                    "video_id": episode.video_id.value,
                    "audio_file_path": episode.audio_file_path,
                    "issue": "file_not_found"
                })
                continue

            try:
                # Detect actual file format using headers
                content_type = detect_audio_mime_type(file_path)
                file_size = file_path.stat().st_size

                if content_type == "video/webm":
                    # Read first few bytes for debugging
                    with open(file_path, 'rb') as f:
                        header_hex = f.read(12).hex()

                    webm_episodes.append({
                        "id": episode.id,
                        "title": episode.title,
                        "video_id": episode.video_id.value,
                        "audio_file_path": episode.audio_file_path,
                        "content_type": content_type,
                        "file_size_mb": round(file_size / (1024 * 1024), 2),
                        "header_hex": header_hex,
                        "issue": "webm_format"
                    })
                else:
                    valid_mp3_episodes.append({
                        "id": episode.id,
                        "title": episode.title,
                        "video_id": episode.video_id.value,
                        "content_type": content_type,
                        "file_size_mb": round(file_size / (1024 * 1024), 2)
                    })

            except Exception as e:
                missing_files.append({
                    "id": episode.id,
                    "title": episode.title,
                    "video_id": episode.video_id.value,
                    "audio_file_path": episode.audio_file_path,
                    "issue": f"detection_error: {str(e)}"
                })

        return {
            "success": True,
            "scan_summary": {
                "total_episodes_scanned": len(episodes),
                "webm_files_found": len(webm_episodes),
                "valid_mp3_files": len(valid_mp3_episodes),
                "missing_files": len(missing_files)
            },
            "webm_episodes": webm_episodes,
            "valid_episodes": valid_mp3_episodes[:5],  # Show first 5 valid ones as sample
            "missing_files": missing_files,
            "recommendation": f"Found {len(webm_episodes)} episodes with WebM format that need re-download"
        }

    except Exception as e:
        logger.error(f"Error in WebM detection: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": f"Failed to detect WebM files: {str(e)}",
                "code": "WEBM_DETECTION_FAILED"
            }
        )


@router.get("/{episode_id}", response_model=EpisodeResponse)
async def get_episode(
    episode_id: int,
    episode_service: EpisodeService = Depends(get_episode_service)
):
    """Get episode by ID"""
    try:
        episode = await episode_service.get_episode(episode_id)
        if not episode:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Episode not found",
                    "code": "EPISODE_NOT_FOUND"
                }
            )
        
        return EpisodeResponse.from_entity(episode)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting episode {episode_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to get episode",
                "code": "INTERNAL_ERROR"
            }
        )


@router.get("/{episode_id}/progress", response_model=ProgressResponse)
async def get_download_progress(
    episode_id: int,
    download_service: DownloadService = Depends(get_download_service),
    episode_service: EpisodeService = Depends(get_episode_service)
):
    """Get real-time download progress for an episode"""
    try:
        # Verify episode exists
        episode = await episode_service.get_episode(episode_id)
        if not episode:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Episode not found",
                    "code": "EPISODE_NOT_FOUND"
                }
            )
        
        # Get progress from download service
        progress = download_service.get_download_progress(episode_id)
        
        if not progress:
            # No active download, return episode status
            return ProgressResponse(
                episode_id=episode_id,
                status=episode.status.value,
                percentage="100%" if episode.status.value == "completed" else "0%",
                speed="N/A",
                eta="N/A",
                downloaded_bytes=0,
                total_bytes=0,
                error_message=None,
                started_at=None,
                completed_at=episode.download_date,
                updated_at=episode.updated_at
            )
        
        return ProgressResponse(**progress)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting progress for episode {episode_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to get download progress",
                "code": "INTERNAL_ERROR"
            }
        )


@router.get("/{episode_id}/status", response_model=EpisodeStatusResponse)
async def get_episode_status(
    episode_id: int,
    episode_service: EpisodeService = Depends(get_episode_service)
):
    """Get episode processing status"""
    try:
        episode = await episode_service.get_episode(episode_id)
        if not episode:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Episode not found",
                    "code": "EPISODE_NOT_FOUND"
                }
            )
        
        return EpisodeStatusResponse(
            episode_id=episode_id,
            status=episode.status.value,
            retry_count=episode.retry_count,
            audio_file_path=episode.audio_file_path,
            download_date=episode.download_date,
            created_at=episode.created_at,
            updated_at=episode.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting status for episode {episode_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to get episode status",
                "code": "INTERNAL_ERROR"
            }
        )


@router.post("/analyze", response_model=MetadataAnalysisResponse)
async def analyze_youtube_video(
    request: MetadataAnalysisRequest,
    url_validator: URLValidationService = Depends(get_url_validation_service),
    youtube_service: YouTubeService = Depends()
):
    """
    Analyze YouTube video metadata without creating episode
    
    This endpoint allows users to preview video information
    before deciding to add it as an episode.
    """
    try:
        # Validate URL
        validation = url_validator.validate_youtube_url(request.video_url)
        if not validation['valid']:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": validation['error'],
                    "code": validation.get('error_code', 'INVALID_URL')
                }
            )
        
        # Extract metadata
        metadata = await youtube_service.extract_metadata(validation['normalized_url'])
        
        return MetadataAnalysisResponse(
            video_id=metadata['video_id'],
            title=metadata['title'],
            description=metadata['description'][:500],  # Truncate for preview
            duration_seconds=metadata.get('duration_seconds'),
            thumbnail_url=metadata.get('thumbnail_url'),
            uploader=metadata.get('uploader'),
            view_count=metadata.get('view_count', 0),
            publication_date=metadata.get('publication_date'),
            keywords=metadata.get('keywords', [])[:10],  # Limit keywords
            video_url=metadata['video_url'],
            availability=metadata.get('availability'),
            channel=metadata.get('channel'),
            channel_id=metadata.get('channel_id'),
            channel_url=metadata.get('channel_url')
        )
        
    except YouTubeExtractionError as e:
        logger.error(f"YouTube analysis failed: {e}")
        raise HTTPException(
            status_code=422,
            detail={
                "error": str(e),
                "code": "YOUTUBE_EXTRACTION_ERROR"
            }
        )
    except Exception as e:
        logger.error(f"Error analyzing video: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to analyze video",
                "code": "INTERNAL_ERROR"
            }
        )


@router.post("/{episode_id}/retry", response_model=SuccessResponse)
async def retry_episode_download(
    episode_id: int,
    episode_service: EpisodeService = Depends(get_episode_service),
):
    """Retry episode download (for failed episodes) or re-download (for completed episodes)"""
    try:
        episode = await episode_service.get_episode(episode_id)
        if not episode:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Episode not found",
                    "code": "EPISODE_NOT_FOUND"
                }
            )

        # Allow retry for both failed and completed episodes
        if episode.status.value not in ["failed", "completed"]:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Episode must be in failed or completed state for retry",
                    "code": "INVALID_STATUS"
                }
            )

        # Check retry limit only for failed episodes
        if episode.status.value == "failed" and not episode.can_retry():
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Episode has exceeded maximum retry attempts",
                    "code": "MAX_RETRIES_EXCEEDED"
                }
            )

        # Re-use original audio preferences if they were set
        retry_language = episode.requested_language
        retry_quality = episode.requested_quality

        if episode.status.value == "completed":
            # For completed episodes, reset for re-download
            reset_success = await episode_service.reset_episode_for_redownload(episode_id)
            if not reset_success:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": "Failed to reset episode for re-download",
                        "code": "RETRY_FAILED"
                    }
                )
        else:
            # For failed episodes, reset status to pending
            await episode_service.reset_episode_for_redownload(episode_id)

        # Queue download via Celery task
        from app.infrastructure.tasks.download_episode_task import download_episode
        download_episode.apply_async(
            args=(episode_id,),
            kwargs={
                'channel_id': episode.channel_id,
                'audio_language': retry_language,
                'audio_quality': retry_quality
            }
        )

        return SuccessResponse(
            message="Download retry queued successfully",
            data={"episode_id": episode_id}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrying download for episode {episode_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to retry download",
                "code": "INTERNAL_ERROR"
            }
        )


@router.put("/{episode_id}", response_model=EpisodeResponse)
async def update_episode(
    episode_id: int,
    episode_data: EpisodeUpdate,
    episode_service: EpisodeService = Depends(get_episode_service)
):
    """Update episode metadata"""
    try:
        # Prepare updates dictionary
        updates = {}
        if episode_data.title is not None:
            updates["title"] = episode_data.title
        if episode_data.description is not None:
            updates["description"] = episode_data.description
        if episode_data.keywords is not None:
            updates["keywords"] = episode_data.keywords
        if episode_data.tags is not None:
            updates["tags"] = episode_data.tags

        # Update episode
        episode = await episode_service.update_episode(episode_id, updates)
        
        if not episode:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Episode not found",
                    "code": "EPISODE_NOT_FOUND"
                }
            )
        
        return EpisodeResponse.from_entity(episode)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating episode {episode_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to update episode",
                "code": "INTERNAL_ERROR"
            }
        )


@router.post("/download-direct", response_model=dict)
async def download_youtube_direct(
    video_url: str,
    channel_id: int = 1,
    url_validator: URLValidationService = Depends(get_url_validation_service)
):
    """
    Direct YouTube audio download without database interaction
    
    This endpoint bypasses the complex background task system and directly
    downloads YouTube audio to the filesystem for testing purposes.
    """
    try:
        logger.info(f"Starting direct download for URL: {video_url}")
        
        # Validate YouTube URL
        validation = url_validator.validate_youtube_url(video_url)
        if not validation['valid']:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": validation['error'],
                    "code": validation.get('error_code', 'INVALID_URL')
                }
            )
        
        # Initialize services directly
        from app.infrastructure.services.youtube_service import YouTubeService
        from app.infrastructure.services.file_service import FileService
        from pathlib import Path
        from app.core.config import settings
        import shutil
        
        youtube_service = YouTubeService()
        file_service = FileService()
        
        # Ensure directories exist
        media_path = Path(settings.media_path)
        temp_path = Path(settings.temp_path)
        channel_dir = media_path / f"channel_{channel_id}"
        
        media_path.mkdir(parents=True, exist_ok=True)
        temp_path.mkdir(parents=True, exist_ok=True)
        channel_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Using media path: {media_path}")
        logger.info(f"Using temp path: {temp_path}")
        
        # Extract metadata for filename
        metadata = await youtube_service.extract_metadata(validation['normalized_url'])
        
        video_id = metadata['video_id']

        # Define output path with only video_id
        output_filename = f"{video_id}.%(ext)s"
        output_path = channel_dir / output_filename
        
        logger.info(f"Downloading to: {output_path}")
        
        # Download audio directly
        downloaded_file, _format_info = await youtube_service.download_audio(
            validation['normalized_url'],
            output_path=str(output_path)
        )
        
        logger.info(f"Download completed: {downloaded_file}")
        
        # Get file info
        file_path = Path(downloaded_file)
        file_size = file_path.stat().st_size if file_path.exists() else 0
        relative_path = file_path.relative_to(media_path) if file_path.exists() else None
        
        return {
            "success": True,
            "message": "Audio downloaded successfully",
            "data": {
                "video_id": video_id,
                "title": metadata['title'],
                "duration_seconds": metadata.get('duration_seconds'),
                "downloaded_file": str(downloaded_file),
                "relative_path": str(relative_path) if relative_path else None,
                "file_size_bytes": file_size,
                "file_size_mb": round(file_size / (1024 * 1024), 2),
                "media_directory": str(media_path),
                "channel_directory": str(channel_dir)
            }
        }
        
    except Exception as e:
        logger.error(f"Direct download failed: {e}")
        import traceback
        logger.debug(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "code": "DOWNLOAD_FAILED"
            }
        )


@router.delete("/{episode_id}", response_model=SuccessResponse)
async def delete_episode(
    episode_id: int,
    episode_service: EpisodeService = Depends(get_episode_service),
    file_service: FileService = Depends(get_file_service),
    download_service: DownloadService = Depends(get_download_service)
):
    """Delete episode and associated files"""
    try:
        # Get episode first to check if it exists
        episode = await episode_service.get_episode(episode_id)
        if not episode:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Episode not found", 
                    "code": "EPISODE_NOT_FOUND"
                }
            )
        
        # Cancel any active download
        if episode.status.value in ["pending", "processing"]:
            await download_service.cancel_download(episode_id)
            logger.info(f"Cancelled active download for episode {episode_id}")
        
        # Delete audio file if it exists
        if episode.audio_file_path:
            file_deleted = await file_service.delete_episode_file(episode.audio_file_path)
            if file_deleted:
                logger.info(f"Deleted audio file for episode {episode_id}: {episode.audio_file_path}")
            else:
                logger.warning(f"Failed to delete audio file for episode {episode_id}")
        
        # Delete episode from database
        success = await episode_service.delete_episode(episode_id)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Failed to delete episode from database",
                    "code": "DELETION_FAILED"
                }
            )
        
        # Explicitly commit the transaction
        await episode_service.episode_repository.db_session.commit()
        
        logger.info(f"Successfully deleted episode {episode_id}: {episode.title}")
        
        return SuccessResponse(
            message="Episode deleted successfully",
            data={
                "episode_id": episode_id,
                "title": episode.title,
                "file_deleted": episode.audio_file_path is not None
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting episode {episode_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to delete episode",
                "code": "INTERNAL_ERROR"
            }
        )


@router.post("/{episode_id}/favorite", response_model=SuccessResponse)
async def favorite_episode(
    episode_id: int,
    episode_service: EpisodeService = Depends(get_episode_service)
):
    """Add episode to favorites"""
    try:
        episode = await episode_service.get_episode(episode_id)
        if not episode:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Episode not found",
                    "code": "EPISODE_NOT_FOUND"
                }
            )

        # Set as favorite
        success = await episode_service.set_episode_favorite(episode_id, True)

        if not success:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Failed to favorite episode",
                    "code": "FAVORITE_FAILED"
                }
            )

        return SuccessResponse(
            message="Episode added to favorites",
            data={"episode_id": episode_id, "is_favorited": True}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error favoriting episode {episode_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to favorite episode",
                "code": "INTERNAL_ERROR"
            }
        )


@router.delete("/{episode_id}/favorite", response_model=SuccessResponse)
async def unfavorite_episode(
    episode_id: int,
    episode_service: EpisodeService = Depends(get_episode_service)
):
    """Remove episode from favorites"""
    try:
        episode = await episode_service.get_episode(episode_id)
        if not episode:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Episode not found",
                    "code": "EPISODE_NOT_FOUND"
                }
            )

        # Remove from favorites
        success = await episode_service.set_episode_favorite(episode_id, False)

        if not success:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Failed to unfavorite episode",
                    "code": "UNFAVORITE_FAILED"
                }
            )

        return SuccessResponse(
            message="Episode removed from favorites",
            data={"episode_id": episode_id, "is_favorited": False}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unfavoriting episode {episode_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to unfavorite episode",
                "code": "INTERNAL_ERROR"
            }
        )


@router.post("/fix-status", response_model=dict)
async def fix_episode_statuses(
    file_service: FileService = Depends(get_file_service),
    episode_service: EpisodeService = Depends(get_episode_service)
):
    """
    Fix episodes that have downloaded media files but wrong status
    This is a temporary endpoint to fix episodes that got stuck in pending status
    """
    try:
        from pathlib import Path
        from app.core.config import settings
        
        # Get all pending episodes
        pending_episodes = await episode_service.list_episodes(
            channel_id=1,  # Assuming channel 1
            status="pending",
            skip=0,
            limit=100
        )
        
        fixed_count = 0
        media_path = Path(settings.media_path)
        
        for episode in pending_episodes[0]:  # episodes is tuple (episodes, total)
            # Check if media file exists
            channel_dir = media_path / f"channel_{episode.channel_id}"
            audio_files = list(channel_dir.glob(f"{episode.video_id}_*"))
            
            if audio_files:
                audio_file = audio_files[0]
                relative_path = audio_file.relative_to(media_path)
                
                # Update episode status manually
                episode.mark_as_completed(str(relative_path))
                await episode_service.episode_repository.update(episode)
                fixed_count += 1
                
                logger.info(f"Fixed episode {episode.id}: {episode.title}")
        
        # Commit changes
        await episode_service.episode_repository.db_session.commit()
        
        return {
            "success": True,
            "message": f"Fixed {fixed_count} episodes",
            "fixed_count": fixed_count
        }

    except Exception as e:
        logger.error(f"Error fixing episode statuses: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to fix episode statuses",
                "code": "INTERNAL_ERROR"
            }
        )



@router.post("/bulk-redownload", response_model=dict)
async def bulk_redownload_episodes(
    channel_id: int = 1,
    exclude_episode_ids: List[int] = None,
    episode_service: EpisodeService = Depends(get_episode_service),
):
    """
    Re-download all completed episodes to fix WebM format issues

    This endpoint triggers re-download of all completed episodes to ensure
    they are properly converted to MP3 format for iTunes compatibility.

    Args:
        channel_id: Channel ID to re-download episodes for (default: 1)
        exclude_episode_ids: List of episode IDs to skip (e.g., recently downloaded ones)
    """
    try:
        if exclude_episode_ids is None:
            exclude_episode_ids = []

        logger.info(f"Starting bulk re-download for channel {channel_id}, excluding: {exclude_episode_ids}")

        # Get all completed episodes for the channel
        episodes_result = await episode_service.list_episodes(
            channel_id=channel_id,
            status="completed",
            skip=0,
            limit=100
        )

        episodes = episodes_result[0]  # episodes is tuple (episodes, total)

        # Filter out excluded episodes
        episodes_to_redownload = [
            ep for ep in episodes
            if ep.id not in exclude_episode_ids and ep.audio_file_path is not None
        ]

        if not episodes_to_redownload:
            return {
                "success": True,
                "message": "No episodes found to re-download",
                "total_episodes": 0,
                "excluded_count": len(exclude_episode_ids),
                "queued_count": 0
            }

        # Queue each episode for re-download
        queued_count = 0
        failed_count = 0

        for episode in episodes_to_redownload:
            try:
                # Reset episode status to pending to trigger re-download
                await episode_service.reset_episode_for_redownload(episode.id)

                # Queue download via Celery task, re-using original audio preferences
                from app.infrastructure.tasks.download_episode_task import download_episode
                download_episode.apply_async(
                    args=(episode.id,),
                    kwargs={
                        'channel_id': channel_id,
                        'audio_language': episode.requested_language,
                        'audio_quality': episode.requested_quality
                    }
                )

                queued_count += 1
                logger.info(f"Queued episode {episode.id} for re-download: {episode.title[:50]}...")

            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to queue episode {episode.id} for re-download: {e}")

        return {
            "success": True,
            "message": f"Queued {queued_count} episodes for re-download",
            "total_episodes": len(episodes),
            "episodes_to_redownload": len(episodes_to_redownload),
            "excluded_count": len(exclude_episode_ids),
            "queued_count": queued_count,
            "failed_count": failed_count,
            "episode_details": [
                {
                    "id": ep.id,
                    "title": ep.title[:50] + "..." if len(ep.title) > 50 else ep.title,
                    "video_id": ep.video_id.value,
                    "status": "queued" if ep.id not in exclude_episode_ids else "excluded"
                }
                for ep in episodes_to_redownload
            ]
        }

    except Exception as e:
        logger.error(f"Error in bulk re-download: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": f"Failed to start bulk re-download: {str(e)}",
                "code": "BULK_REDOWNLOAD_FAILED"
            }
        )


@router.get("/stats/count", response_model=dict)
async def get_episode_count(
    channel_id: int = Query(1, gt=0, description="Channel ID to count episodes for"),
    episode_service: EpisodeService = Depends(get_episode_service)
):
    """
    Get the total count of episodes for a channel

    This endpoint provides the episode count for the delete confirmation dialog,
    allowing users to see exactly how many episodes will be deleted.

    Args:
        channel_id: Channel ID to count episodes for (default: 1)
    """
    try:
        logger.info(f"Getting episode count for channel {channel_id}")

        count = await episode_service.get_episode_count_for_channel(channel_id)

        return {
            "success": True,
            "channel_id": channel_id,
            "episode_count": count,
            "message": f"Found {count} episodes in channel {channel_id}"
        }

    except Exception as e:
        logger.error(f"Error getting episode count for channel {channel_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": f"Failed to get episode count: {str(e)}",
                "code": "EPISODE_COUNT_FAILED"
            }
        )


@router.delete("/actions/bulk-delete-all", response_model=dict)
async def bulk_delete_all_episodes(
    channel_id: int = Query(1, gt=0, description="Channel ID to delete episodes from"),
    dry_run: bool = Query(False, description="If true, only count episodes without deleting"),
    confirm_token: Optional[str] = Query(None, description="Confirmation token for extra safety"),
    episode_service: EpisodeService = Depends(get_episode_service),
    file_service: FileService = Depends(get_file_service)
):
    """
    Delete all episodes and media files for a specific channel

    This endpoint performs a bulk deletion of all episodes in a channel,
    including their associated media files. It provides comprehensive
    error handling and detailed reporting of the operation results.

    IMPORTANT: This operation is irreversible. All episode data and media files
    will be permanently deleted.

    Args:
        channel_id: Channel ID to delete episodes from (default: 1)
        dry_run: If true, only count episodes without actually deleting them
        confirm_token: Optional confirmation token for extra safety

    Returns:
        Detailed results of the bulk deletion operation
    """
    try:
        # Import the custom exceptions
        from app.application.services.episode_service import BulkDeletionError

        logger.info(f"Bulk delete all episodes request for channel {channel_id} (dry_run={dry_run})")

        # Validate confirmation token if provided (optional additional safety)
        if confirm_token and confirm_token != "DELETE_ALL_EPISODES":
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid confirmation token",
                    "code": "INVALID_CONFIRMATION_TOKEN"
                }
            )

        # Perform the bulk deletion using the service
        try:
            result = await episode_service.delete_all_episodes_for_channel(
                channel_id=channel_id,
                dry_run=dry_run
            )

            # Convert result to dictionary for API response
            result_dict = result.to_dict()

            # Determine appropriate HTTP status code
            if result.success:
                if result.partial_completion:
                    # Partial success - some episodes failed
                    status_code = 207  # Multi-Status
                    result_dict.update({
                        "message": f"Partially completed: {result.deleted_episodes} of {result.total_episodes} episodes deleted",
                        "warning": "Some episodes could not be deleted. See failed_episode_details for more information."
                    })
                elif result.total_episodes == 0:
                    # No episodes to delete
                    status_code = 200
                    result_dict.update({
                        "message": "No episodes found to delete" if not dry_run else f"Dry run: No episodes found in channel {channel_id}"
                    })
                else:
                    # Complete success
                    status_code = 200
                    if dry_run:
                        result_dict.update({
                            "message": f"Dry run completed: Would delete {result.total_episodes} episodes and their media files"
                        })
                    else:
                        result_dict.update({
                            "message": f"Successfully deleted {result.deleted_episodes} episodes and {result.deleted_files} media files"
                        })
            else:
                # Complete failure
                status_code = 500
                result_dict.update({
                    "message": f"Bulk deletion failed: {result.error_message or 'Unknown error'}"
                })

            # Add additional metadata
            result_dict.update({
                "channel_id": channel_id,
                "dry_run": dry_run,
                "timestamp": datetime.utcnow().isoformat()
            })

            # Log the operation result
            if result.success:
                if result.partial_completion:
                    logger.warning(f"Bulk deletion completed with issues for channel {channel_id}: "
                                 f"{result.deleted_episodes}/{result.total_episodes} episodes deleted")
                else:
                    logger.info(f"Bulk deletion completed successfully for channel {channel_id}: "
                              f"{result.deleted_episodes} episodes deleted")
            else:
                logger.error(f"Bulk deletion failed for channel {channel_id}: {result.error_message}")

            # Return result with appropriate status code
            if status_code != 200:
                raise HTTPException(status_code=status_code, detail=result_dict)

            return result_dict

        except BulkDeletionError as bulk_error:
            logger.error(f"Bulk deletion service error for channel {channel_id}: {bulk_error}")
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error": str(bulk_error),
                    "code": "BULK_DELETION_FAILED",
                    "channel_id": channel_id,
                    "dry_run": dry_run,
                    "message": f"Bulk deletion operation failed: {str(bulk_error)}"
                }
            )

    except HTTPException:
        # Re-raise HTTP exceptions (our custom ones)
        raise

    except Exception as e:
        logger.error(f"Unexpected error in bulk delete endpoint for channel {channel_id}: {e}")
        import traceback
        logger.debug(f"Bulk delete error traceback: {traceback.format_exc()}")

        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": f"Internal server error: {str(e)}",
                "code": "INTERNAL_ERROR",
                "channel_id": channel_id,
                "dry_run": dry_run,
                "message": "An unexpected error occurred during bulk deletion. Please try again or contact support if the problem persists."
            }
        )