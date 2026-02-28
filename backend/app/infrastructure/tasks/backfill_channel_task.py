"""
Celery task for backfilling historical videos from a followed channel
"""
from celery import shared_task
from typing import Optional
import logging
import asyncio

from app.infrastructure.database.connection import get_background_task_session
from app.infrastructure.repositories.followed_channel_repository_impl import FollowedChannelRepositoryImpl
from app.infrastructure.repositories.youtube_video_repository_impl import YouTubeVideoRepositoryImpl
from app.infrastructure.services.youtube_metadata_service_impl import YouTubeMetadataServiceImpl
from app.infrastructure.services.channel_discovery_service_impl import ChannelDiscoveryServiceImpl

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
    name="app.infrastructure.tasks.backfill_channel_task.backfill_followed_channel",
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True
)
def backfill_followed_channel(
    self,
    followed_channel_id: int,
    year: Optional[int] = None,
    max_videos: int = 20
) -> dict:
    """
    Backfill historical videos from a followed channel.
    
    Args:
        followed_channel_id: ID of the followed channel
        year: Optional year to backfill (None for all years)
        max_videos: Maximum number of videos to fetch
        
    Returns:
        Dictionary with results of the backfill
    """
    async def _backfill_channel():
        session = await get_background_task_session()
        try:
            # Initialize repositories
            followed_channel_repo = FollowedChannelRepositoryImpl(session)
            youtube_video_repo = YouTubeVideoRepositoryImpl(session)
            
            # Get followed channel
            followed_channel = await followed_channel_repo.get_by_id(followed_channel_id)
            if not followed_channel:
                logger.error(f"Followed channel {followed_channel_id} not found")
                return {"status": "error", "message": "Followed channel not found"}
            
            # Initialize services
            metadata_service = YouTubeMetadataServiceImpl()
            discovery_service = ChannelDiscoveryServiceImpl(
                metadata_service=metadata_service,
                youtube_video_repository=youtube_video_repo,
                followed_channel_repository=followed_channel_repo
            )
            
            # Backfill videos
            backfilled_videos = await discovery_service.backfill_channel_videos(
                followed_channel=followed_channel,
                max_videos=max_videos,
                year=year
            )
            
            logger.info(f"Backfilled {len(backfilled_videos)} videos for channel {followed_channel_id} (year: {year})")
            
            return {
                "status": "success",
                "followed_channel_id": followed_channel_id,
                "year": year,
                "videos_backfilled": len(backfilled_videos)
            }
            
        except Exception as e:
            logger.error(f"Error backfilling channel {followed_channel_id}: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}
        finally:
            await session.close()
    
    logger.info(f"Backfilling channel {followed_channel_id} (year: {year}, max: {max_videos})")
    return _run_async(_backfill_channel())

