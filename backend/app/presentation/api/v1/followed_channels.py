"""
Followed Channels API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, List, Optional
import logging

from app.infrastructure.database.connection import get_async_db
from app.core.auth import get_current_user_jwt
from app.core.dependencies import (
    get_followed_channel_service,
    FollowedChannelServiceDep,
)
from app.application.services.followed_channel_service import (
    FollowedChannelService,
    FollowedChannelNotFoundError,
    DuplicateChannelError,
    InvalidChannelURLError,
)
from app.presentation.schemas.followed_channel_schemas import (
    FollowedChannelCreateRequest,
    FollowedChannelUpdateRequest,
    FollowedChannelResponse,
    FollowedChannelWithStatsResponse,
    BackfillRequest,
    BackfillResponse,
)
from app.presentation.schemas.celery_task_status_schemas import CeleryTaskStatusResponse
from app.application.services.celery_task_status_service import CeleryTaskStatusService
from app.infrastructure.repositories.celery_task_status_repository_impl import CeleryTaskStatusRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/followed-channels", tags=["followed-channels"])


@router.post(
    "",
    response_model=FollowedChannelResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Invalid channel URL or validation error"},
        409: {"description": "Channel already being followed"},
    }
)
async def follow_channel(
    request: FollowedChannelCreateRequest,
    current_user: Annotated[dict, Depends(get_current_user_jwt)],
    followed_channel_service: FollowedChannelService = Depends(get_followed_channel_service),
) -> FollowedChannelResponse:
    """
    Follow a YouTube channel
    
    This endpoint:
    1. Validates the YouTube channel URL
    2. Extracts channel metadata from YouTube
    3. Creates a followed channel record
    4. Triggers initial backfill task (last 20 videos of current year)
    5. Returns the followed channel information
    """
    try:
        # Log incoming request details
        user_id = current_user.get("user_id")
        logger.info(
            f"Follow channel request received - AFTER validation",
            extra={
                "user_id": user_id,
                "channel_url": request.channel_url,
                "auto_approve": request.auto_approve,
                "auto_approve_channel_id": request.auto_approve_channel_id,
                "request_data": request.model_dump() if hasattr(request, 'model_dump') else str(request)
            }
        )
        
        if not user_id:
            logger.error("Follow channel request received but user_id is None/empty", extra={"current_user": current_user})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        followed_channel = await followed_channel_service.follow_channel(
            user_id=user_id,
            channel_url=request.channel_url,
            auto_approve=request.auto_approve,
            auto_approve_channel_id=request.auto_approve_channel_id
        )
        
        logger.info(f"Successfully followed channel: {followed_channel.youtube_channel_name} (ID: {followed_channel.id})")
        
        return FollowedChannelResponse.model_validate(followed_channel)
        
    except DuplicateChannelError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except InvalidChannelURLError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to follow channel: {str(e)}"
        )


@router.get(
    "",
    response_model=List[FollowedChannelResponse],
    responses={
        401: {"description": "Authentication required"},
    }
)
async def list_followed_channels(
    current_user: Annotated[dict, Depends(get_current_user_jwt)],
    followed_channel_service: FollowedChannelService = Depends(get_followed_channel_service),
) -> List[FollowedChannelResponse]:
    """
    List all followed channels for the current user
    """
    try:
        channels = await followed_channel_service.get_followed_channels(
            user_id=current_user["user_id"]
        )
        
        return [FollowedChannelResponse.model_validate(channel) for channel in channels]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list followed channels: {str(e)}"
        )


@router.get(
    "/{followed_channel_id}",
    response_model=FollowedChannelResponse,
    responses={
        401: {"description": "Authentication required"},
        404: {"description": "Followed channel not found"},
    }
)
async def get_followed_channel(
    followed_channel_id: int,
    current_user: Annotated[dict, Depends(get_current_user_jwt)],
    followed_channel_service: FollowedChannelService = Depends(get_followed_channel_service),
) -> FollowedChannelResponse:
    """
    Get a specific followed channel
    """
    try:
        followed_channel = await followed_channel_service.get_followed_channel(
            followed_channel_id=followed_channel_id,
            user_id=current_user["user_id"]
        )
        
        return FollowedChannelResponse.model_validate(followed_channel)
        
    except FollowedChannelNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get followed channel: {str(e)}"
        )


@router.put(
    "/{followed_channel_id}",
    response_model=FollowedChannelResponse,
    responses={
        401: {"description": "Authentication required"},
        404: {"description": "Followed channel not found"},
        400: {"description": "Validation error"},
    }
)
async def update_followed_channel(
    followed_channel_id: int,
    request: FollowedChannelUpdateRequest,
    current_user: Annotated[dict, Depends(get_current_user_jwt)],
    followed_channel_service: FollowedChannelService = Depends(get_followed_channel_service),
) -> FollowedChannelResponse:
    """
    Update auto-approve settings for a followed channel
    """
    try:
        updated_channel = await followed_channel_service.update_auto_approve_settings(
            followed_channel_id=followed_channel_id,
            user_id=current_user["user_id"],
            auto_approve=request.auto_approve if request.auto_approve is not None else False,
            auto_approve_channel_id=request.auto_approve_channel_id
        )
        
        return FollowedChannelResponse.model_validate(updated_channel)
        
    except FollowedChannelNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update followed channel: {str(e)}"
        )


@router.put(
    "/{followed_channel_id}/metadata",
    response_model=FollowedChannelResponse,
    responses={
        401: {"description": "Authentication required"},
        404: {"description": "Followed channel not found"},
        400: {"description": "Failed to fetch metadata from YouTube"},
    }
)
async def update_channel_metadata(
    followed_channel_id: int,
    current_user: Annotated[dict, Depends(get_current_user_jwt)],
    followed_channel_service: FollowedChannelService = Depends(get_followed_channel_service),
) -> FollowedChannelResponse:
    """
    Update channel metadata from YouTube

    Fetches fresh metadata from YouTube and updates channel name, URL,
    thumbnail, and description. This is a synchronous operation.
    """
    try:
        updated_channel = await followed_channel_service.update_channel_metadata(
            followed_channel_id=followed_channel_id,
            user_id=current_user["user_id"]
        )

        logger.info(f"Successfully updated metadata for channel {followed_channel_id}")
        return FollowedChannelResponse.model_validate(updated_channel)

    except FollowedChannelNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InvalidChannelURLError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to update channel metadata: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update channel metadata: {str(e)}"
        )


@router.delete(
    "/{followed_channel_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"description": "Authentication required"},
        404: {"description": "Followed channel not found"},
    }
)
async def unfollow_channel(
    followed_channel_id: int,
    current_user: Annotated[dict, Depends(get_current_user_jwt)],
    followed_channel_service: FollowedChannelService = Depends(get_followed_channel_service),
):
    """
    Unfollow a YouTube channel
    
    This endpoint:
    1. Deletes all pending/reviewed videos for the channel
    2. Deletes the followed channel record
    3. Keeps episodes that were already created
    """
    try:
        success = await followed_channel_service.unfollow_channel(
            followed_channel_id=followed_channel_id,
            user_id=current_user["user_id"]
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Followed channel not found"
            )
        
    except FollowedChannelNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unfollow channel: {str(e)}"
        )


@router.post(
    "/{followed_channel_id}/check",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Check for recent videos using yt-dlp (comprehensive)",
    description="Queue a background task to check for new videos using yt-dlp. Retrieves up to 50 recent videos with full metadata.",
    responses={
        401: {"description": "Authentication required"},
        404: {"description": "Followed channel not found"},
    }
)
async def trigger_check(
    followed_channel_id: int,
    current_user: Annotated[dict, Depends(get_current_user_jwt)],
    followed_channel_service: FollowedChannelService = Depends(get_followed_channel_service),
) -> dict:
    """
    Manually trigger a check for new videos using yt-dlp (comprehensive method).

    This method uses yt-dlp to scan up to 50 recent videos. It's slower but more comprehensive.
    Use this for deep scans or when you need to check many historical videos.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        task_id = await followed_channel_service.trigger_check(
            followed_channel_id=followed_channel_id,
            user_id=current_user["user_id"]
        )
        
        return {
            "status": "queued",
            "message": "Check task queued successfully",
            "followed_channel_id": followed_channel_id,
            "task_id": task_id,
            "method": "ytdlp_full"
        }
        
    except FollowedChannelNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ConnectionError as e:
        logger.error(f"Celery connection error when triggering check: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Task queue is temporarily unavailable. Please ensure Redis and Celery worker are running."
        )
    except Exception as e:
        # Catch any Kombu/Celery exceptions that weren't converted to ConnectionError
        error_str = str(e)
        if 'Connection refused' in error_str or 'OperationalError' in type(e).__name__:
            logger.error(f"Celery connection error when triggering check: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Task queue is temporarily unavailable. Please ensure Redis and Celery worker are running."
            )
        # Re-raise other exceptions
        logger.error(f"Failed to trigger check for channel {followed_channel_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger check: {str(e)}"
        )


@router.post(
    "/{followed_channel_id}/check-rss",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Check for latest videos using RSS feed (fast)",
    description="Queue a background task to check for latest videos using YouTube RSS feed. Returns last ~10-15 videos. Fast method for frequent checks.",
    responses={
        401: {"description": "Authentication required"},
        404: {"description": "Followed channel not found"},
    }
)
async def trigger_check_rss(
    followed_channel_id: int,
    current_user: Annotated[dict, Depends(get_current_user_jwt)],
    followed_channel_service: FollowedChannelService = Depends(get_followed_channel_service),
) -> dict:
    """
    Manually trigger a check for new videos using RSS feed (fast method).

    This method uses YouTube's RSS feed to identify the last 10-15 videos, then uses
    yt-dlp only for metadata extraction of new videos. It's much faster than the full
    yt-dlp method but returns fewer videos.

    Best for frequent checks on active channels.
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        task_id = await followed_channel_service.trigger_check_rss(
            followed_channel_id=followed_channel_id,
            user_id=current_user["user_id"]
        )

        return {
            "status": "queued",
            "message": "RSS check task queued successfully",
            "followed_channel_id": followed_channel_id,
            "task_id": task_id,
            "method": "rss_feed"
        }

    except FollowedChannelNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ConnectionError as e:
        logger.error(f"Celery connection error when triggering RSS check: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Task queue is temporarily unavailable. Please ensure Redis and Celery worker are running."
        )
    except Exception as e:
        # Catch any Kombu/Celery exceptions that weren't converted to ConnectionError
        error_str = str(e)
        if 'Connection refused' in error_str or 'OperationalError' in type(e).__name__:
            logger.error(f"Celery connection error when triggering RSS check: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Task queue is temporarily unavailable. Please ensure Redis and Celery worker are running."
            )
        # Re-raise other exceptions
        logger.error(f"Failed to trigger RSS check for channel {followed_channel_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger RSS check: {str(e)}"
        )


@router.post(
    "/{followed_channel_id}/backfill",
    response_model=BackfillResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        401: {"description": "Authentication required"},
        404: {"description": "Followed channel not found"},
    }
)
async def trigger_backfill(
    followed_channel_id: int,
    request: BackfillRequest,
    current_user: Annotated[dict, Depends(get_current_user_jwt)],
    followed_channel_service: FollowedChannelService = Depends(get_followed_channel_service),
) -> BackfillResponse:
    """
    Manually trigger a backfill for historical videos
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from app.infrastructure.tasks.backfill_channel_task import backfill_followed_channel
        
        # Verify channel exists and belongs to user
        await followed_channel_service.get_followed_channel(
            followed_channel_id=followed_channel_id,
            user_id=current_user["user_id"]
        )
        
        # Queue backfill task - use apply_async with explicit args/kwargs to avoid Celery serialization issues
        task_result = backfill_followed_channel.apply_async(
            args=(followed_channel_id, request.year, request.max_videos),
            kwargs={}
        )
        
        return BackfillResponse(
            status="queued",
            task_id=task_result.id,
            followed_channel_id=followed_channel_id,
            year=request.year,
            max_videos=request.max_videos,
            message="Backfill task queued successfully"
        )
        
    except FollowedChannelNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ConnectionError as e:
        logger.error(f"Celery connection error when triggering backfill: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Task queue is temporarily unavailable. Please ensure Redis and Celery worker are running."
        )
    except Exception as e:
        # Catch any Kombu/Celery exceptions that weren't converted to ConnectionError
        error_str = str(e)
        if 'Connection refused' in error_str or 'OperationalError' in type(e).__name__:
            logger.error(f"Celery connection error when triggering backfill: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Task queue is temporarily unavailable. Please ensure Redis and Celery worker are running."
            )
        # Re-raise other exceptions
        logger.error(f"Failed to trigger backfill for channel {followed_channel_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger backfill: {str(e)}"
        )


def get_task_status_service(
    session: AsyncSession = Depends(get_async_db)
) -> CeleryTaskStatusService:
    """Dependency to get task status service"""
    repository = CeleryTaskStatusRepository(session)
    return CeleryTaskStatusService(repository)


@router.get(
    "/{followed_channel_id}/task-status",
    response_model=CeleryTaskStatusResponse,
    responses={
        401: {"description": "Authentication required"},
        404: {"description": "Followed channel or task status not found"},
    }
)
async def get_channel_task_status(
    followed_channel_id: int,
    current_user: Annotated[dict, Depends(get_current_user_jwt)],
    followed_channel_service: FollowedChannelService = Depends(get_followed_channel_service),
    task_status_service: CeleryTaskStatusService = Depends(get_task_status_service),
) -> CeleryTaskStatusResponse:
    """
    Get the latest task status for a followed channel
    
    Returns the most recent check or backfill task status for the channel.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Verify channel exists and belongs to user
        await followed_channel_service.get_followed_channel(
            followed_channel_id=followed_channel_id,
            user_id=current_user["user_id"]
        )
        
        # Get latest task status
        task_status = await task_status_service.get_latest_channel_task_status(
            followed_channel_id=followed_channel_id
        )
        
        if not task_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No task status found for channel {followed_channel_id}"
            )
        
        return CeleryTaskStatusResponse.model_validate(task_status)
        
    except FollowedChannelNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status for channel {followed_channel_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}"
        )

