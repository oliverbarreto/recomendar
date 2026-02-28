"""
YouTube Videos API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, List, Optional

from app.infrastructure.database.connection import get_async_db
from app.core.auth import get_current_user_jwt
from app.core.dependencies import (
    get_youtube_video_service,
)
from app.application.services.youtube_video_service import (
    YouTubeVideoService,
    YouTubeVideoNotFoundError,
    InvalidStateTransitionError,
)
from app.domain.entities.youtube_video import YouTubeVideoState
from app.presentation.schemas.youtube_video_schemas import (
    YouTubeVideoResponse,
    YouTubeVideoListFilters,
    CreateEpisodeFromVideoRequest,
    CreateEpisodeFromVideoResponse,
    YouTubeVideoStatsResponse,
    BulkActionRequest,
    BulkActionResponse,
    BulkActionResult,
    BulkActionType,
)

router = APIRouter(prefix="/youtube-videos", tags=["youtube-videos"])


@router.get(
    "",
    response_model=List[YouTubeVideoResponse],
    responses={
        401: {"description": "Authentication required"},
    }
)
async def list_youtube_videos(
    current_user: Annotated[dict, Depends(get_current_user_jwt)],
    state: Optional[str] = Query(default=None, description="Filter by state"),
    followed_channel_id: Optional[int] = Query(default=None, description="Filter by followed channel ID"),
    search: Optional[str] = Query(default=None, description="Search query"),
    publish_year: Optional[int] = Query(default=None, description="Filter by publish year (e.g., 2024)"),
    skip: int = Query(default=0, ge=0, description="Number of videos to skip"),
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of videos to return"),
    youtube_video_service: YouTubeVideoService = Depends(get_youtube_video_service),
) -> List[YouTubeVideoResponse]:
    """
    List YouTube videos with optional filters
    
    Supports filtering by:
    - state: pending_review, reviewed, episode_created, etc.
    - followed_channel_id: Filter by specific channel
    - search: Search by title or description
    - publish_year: Filter by year (e.g., 2024)
    """
    try:
        # Convert state string to enum if provided
        state_enum = None
        if state:
            try:
                state_enum = YouTubeVideoState(state)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid state: {state}"
                )
        
        # Get videos based on filters
        # If any filter is provided (including year), use search with empty query
        if search or state_enum or followed_channel_id or publish_year:
            videos = await youtube_video_service.search_videos(
                query=search or "",
                user_id=current_user["user_id"],
                state=state_enum,
                followed_channel_id=followed_channel_id,
                publish_year=publish_year,
                skip=skip,
                limit=limit
            )
        else:
            # Get pending videos by default when no filters
            videos = await youtube_video_service.get_pending_videos(
                user_id=current_user["user_id"],
                skip=skip,
                limit=limit
            )
        
        # Always return a list, even if empty
        return [YouTubeVideoResponse.model_validate(video) for video in videos]
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404, 400) as-is
        raise
    except Exception as e:
        # Log the full error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to list videos: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list videos: {str(e)}"
        )


@router.post(
    "/{youtube_video_id}/review",
    response_model=YouTubeVideoResponse,
    responses={
        401: {"description": "Authentication required"},
        404: {"description": "YouTube video not found"},
        400: {"description": "Invalid state transition"},
    }
)
async def mark_video_as_reviewed(
    youtube_video_id: int,
    current_user: Annotated[dict, Depends(get_current_user_jwt)],
    youtube_video_service: YouTubeVideoService = Depends(get_youtube_video_service),
) -> YouTubeVideoResponse:
    """
    Mark a video as reviewed
    """
    try:
        updated_video = await youtube_video_service.mark_as_reviewed(
            youtube_video_id=youtube_video_id,
            user_id=current_user["user_id"]
        )
        
        return YouTubeVideoResponse.model_validate(updated_video)
        
    except YouTubeVideoNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InvalidStateTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark video as reviewed: {str(e)}"
        )


@router.post(
    "/{youtube_video_id}/discard",
    response_model=YouTubeVideoResponse,
    responses={
        401: {"description": "Authentication required"},
        404: {"description": "YouTube video not found"},
        400: {"description": "Invalid state transition"},
    }
)
async def discard_video(
    youtube_video_id: int,
    current_user: Annotated[dict, Depends(get_current_user_jwt)],
    youtube_video_service: YouTubeVideoService = Depends(get_youtube_video_service),
) -> YouTubeVideoResponse:
    """
    Mark a video as discarded
    """
    try:
        updated_video = await youtube_video_service.mark_as_discarded(
            youtube_video_id=youtube_video_id,
            user_id=current_user["user_id"]
        )
        
        return YouTubeVideoResponse.model_validate(updated_video)
        
    except YouTubeVideoNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InvalidStateTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to discard video: {str(e)}"
        )


@router.post(
    "/{youtube_video_id}/create-episode",
    response_model=CreateEpisodeFromVideoResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        401: {"description": "Authentication required"},
        404: {"description": "YouTube video or channel not found"},
        400: {"description": "Invalid state transition or validation error"},
    }
)
async def create_episode_from_video(
    youtube_video_id: int,
    request: CreateEpisodeFromVideoRequest,
    current_user: Annotated[dict, Depends(get_current_user_jwt)],
    youtube_video_service: YouTubeVideoService = Depends(get_youtube_video_service),
) -> CreateEpisodeFromVideoResponse:
    """
    Create an episode from a YouTube video
    
    This endpoint:
    1. Verifies video and channel ownership
    2. Queues episode creation task
    3. Updates video state to queued -> downloading
    4. Returns task information
    """
    try:
        result = await youtube_video_service.create_episode_from_video(
            youtube_video_id=youtube_video_id,
            channel_id=request.channel_id,
            user_id=current_user["user_id"],
            audio_language=request.audio_language,
            audio_quality=request.audio_quality
        )
        
        return CreateEpisodeFromVideoResponse(
            status=result["status"],
            task_id=result["task_id"],
            youtube_video_id=result["youtube_video_id"],
            channel_id=result["channel_id"],
            episode_id=result.get("episode_id"),
            message=result["message"]
        )
        
    except YouTubeVideoNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InvalidStateTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
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
            detail=f"Failed to create episode: {str(e)}"
        )


@router.get(
    "/stats",
    response_model=YouTubeVideoStatsResponse,
    responses={
        401: {"description": "Authentication required"},
    }
)
async def get_video_stats(
    current_user: Annotated[dict, Depends(get_current_user_jwt)],
    youtube_video_service: YouTubeVideoService = Depends(get_youtube_video_service),
) -> YouTubeVideoStatsResponse:
    """
    Get video statistics for the current user
    
    Returns counts by state for notification bell and dashboard
    """
    try:
        # Get counts for each state
        pending_count = await youtube_video_service.get_pending_count(
            user_id=current_user["user_id"]
        )
        
        # Get other counts
        reviewed_videos = await youtube_video_service.get_videos_by_state(
            state=YouTubeVideoState.REVIEWED,
            user_id=current_user["user_id"],
            skip=0,
            limit=1000
        )
        
        episode_created_videos = await youtube_video_service.get_videos_by_state(
            state=YouTubeVideoState.EPISODE_CREATED,
            user_id=current_user["user_id"],
            skip=0,
            limit=1000
        )
        
        queued_videos = await youtube_video_service.get_videos_by_state(
            state=YouTubeVideoState.QUEUED,
            user_id=current_user["user_id"],
            skip=0,
            limit=1000
        )
        
        downloading_videos = await youtube_video_service.get_videos_by_state(
            state=YouTubeVideoState.DOWNLOADING,
            user_id=current_user["user_id"],
            skip=0,
            limit=1000
        )
        
        discarded_videos = await youtube_video_service.get_videos_by_state(
            state=YouTubeVideoState.DISCARDED,
            user_id=current_user["user_id"],
            skip=0,
            limit=1000
        )
        
        return YouTubeVideoStatsResponse(
            pending_review=pending_count,
            reviewed=len(reviewed_videos),
            queued=len(queued_videos),
            downloading=len(downloading_videos),
            episode_created=len(episode_created_videos),
            discarded=len(discarded_videos),
            total=pending_count + len(reviewed_videos) + len(episode_created_videos) + len(queued_videos) + len(downloading_videos) + len(discarded_videos)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get video stats: {str(e)}"
        )


@router.get(
    "/stats/channel/{followed_channel_id}",
    response_model=YouTubeVideoStatsResponse,
    responses={
        401: {"description": "Authentication required"},
        404: {"description": "Followed channel not found"},
    }
)
async def get_channel_video_stats(
    followed_channel_id: int,
    current_user: Annotated[dict, Depends(get_current_user_jwt)],
    youtube_video_service: YouTubeVideoService = Depends(get_youtube_video_service),
) -> YouTubeVideoStatsResponse:
    """
    Get video statistics for a specific followed channel
    
    Returns counts by state for the channel card display
    
    Args:
        followed_channel_id: ID of the followed channel
        
    Returns:
        Video counts for each state (pending_review, reviewed, etc.)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Verify the channel belongs to the current user
        stats = await youtube_video_service.get_channel_video_stats(
            followed_channel_id=followed_channel_id,
            user_id=current_user["user_id"]
        )
        
        return YouTubeVideoStatsResponse(
            pending_review=stats.get("pending_review", 0),
            reviewed=stats.get("reviewed", 0),
            queued=stats.get("queued", 0),
            downloading=stats.get("downloading", 0),
            episode_created=stats.get("episode_created", 0),
            discarded=stats.get("discarded", 0),
            total=stats.get("total", 0)
        )
        
    except ValueError as e:
        # Channel not found or doesn't belong to user
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get channel video stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get channel video stats: {str(e)}"
        )


@router.get(
    "/{youtube_video_id}",
    response_model=YouTubeVideoResponse,
    responses={
        401: {"description": "Authentication required"},
        404: {"description": "YouTube video not found"},
    }
)
async def get_youtube_video(
    youtube_video_id: int,
    current_user: Annotated[dict, Depends(get_current_user_jwt)],
    youtube_video_service: YouTubeVideoService = Depends(get_youtube_video_service),
) -> YouTubeVideoResponse:
    """
    Get a specific YouTube video
    """
    try:
        video = await youtube_video_service.get_video(
            youtube_video_id=youtube_video_id,
            user_id=current_user["user_id"]
        )
        
        return YouTubeVideoResponse.model_validate(video)
        
    except YouTubeVideoNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get video: {str(e)}"
        )


@router.post(
    "/bulk-action",
    response_model=BulkActionResponse,
    responses={
        401: {"description": "Authentication required"},
        400: {"description": "Invalid request or missing required fields"},
    }
)
async def bulk_action_videos(
    request: BulkActionRequest,
    current_user: Annotated[dict, Depends(get_current_user_jwt)],
    youtube_video_service: YouTubeVideoService = Depends(get_youtube_video_service),
) -> BulkActionResponse:
    """
    Perform bulk actions on multiple videos
    
    Supported actions:
    - review: Mark videos as reviewed
    - discard: Mark videos as discarded
    - create_episode: Create episodes from videos (requires channel_id)
    """
    try:
        user_id = current_user["user_id"]
        
        # Validate channel_id for create_episode action
        if request.action == BulkActionType.CREATE_EPISODE:
            if not request.channel_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="channel_id is required for create_episode action"
                )
        
        # Perform bulk action based on type
        if request.action == BulkActionType.REVIEW:
            results = await youtube_video_service.bulk_mark_as_reviewed(
                video_ids=request.video_ids,
                user_id=user_id
            )
        elif request.action == BulkActionType.DISCARD:
            results = await youtube_video_service.bulk_discard(
                video_ids=request.video_ids,
                user_id=user_id
            )
        elif request.action == BulkActionType.CREATE_EPISODE:
            results = await youtube_video_service.bulk_create_episodes(
                video_ids=request.video_ids,
                channel_id=request.channel_id,
                user_id=user_id,
                audio_language=request.audio_language,
                audio_quality=request.audio_quality
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action: {request.action}"
            )
        
        # Count successes and failures
        successful = sum(1 for r in results if r["success"])
        failed = len(results) - successful
        
        # Convert results to response format
        bulk_results = [
            BulkActionResult(
                video_id=r["video_id"],
                success=r["success"],
                error=r.get("error"),
                task_id=r.get("task_id")
            )
            for r in results
        ]
        
        return BulkActionResponse(
            action=request.action.value,
            total=len(request.video_ids),
            successful=successful,
            failed=failed,
            results=bulk_results
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to perform bulk action: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform bulk action: {str(e)}"
        )

