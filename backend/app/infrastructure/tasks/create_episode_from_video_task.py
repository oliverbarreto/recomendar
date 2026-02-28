"""
Celery task for creating an episode from a YouTube video
"""
from celery import shared_task
import logging
import asyncio
from typing import Optional

from app.infrastructure.database.connection import get_background_task_session
from app.infrastructure.repositories.youtube_video_repository_impl import YouTubeVideoRepositoryImpl
from app.infrastructure.repositories.channel_repository import ChannelRepositoryImpl
from app.infrastructure.repositories.episode_repository import EpisodeRepositoryImpl
from app.domain.entities.youtube_video import YouTubeVideoState
from app.domain.value_objects.video_id import VideoId
from app.domain.entities.episode import Episode
from app.core.config import settings

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
    name="app.infrastructure.tasks.create_episode_from_video_task.create_episode_from_youtube_video",
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True
)
def create_episode_from_youtube_video(
    self,
    youtube_video_id: int,
    channel_id: int,
    audio_language: Optional[str] = None,
    audio_quality: Optional[str] = None
) -> dict:
    """
    Create an episode from a YouTube video.
    
    This task:
    1. Updates video state to 'queued' -> 'downloading'
    2. Downloads audio using existing download service
    3. Creates episode record
    4. Updates video state to 'episode_created'
    5. Links episode_id to youtube_video
    
    Args:
        youtube_video_id: ID of the YouTube video record
        channel_id: ID of the podcast channel to create episode in
        
    Returns:
        Dictionary with results of the episode creation
    """
    async def _create_episode():
        session = await get_background_task_session()
        try:
            # Initialize repositories
            youtube_video_repo = YouTubeVideoRepositoryImpl(session)
            channel_repo = ChannelRepositoryImpl(session)
            episode_repo = EpisodeRepositoryImpl(session)
            
            # Get YouTube video
            youtube_video = await youtube_video_repo.get_by_id(youtube_video_id)
            if not youtube_video:
                logger.error(f"YouTube video {youtube_video_id} not found")
                return {"status": "error", "message": "YouTube video not found"}
            
            # Get channel
            channel = await channel_repo.get_by_id(channel_id)
            if not channel:
                logger.error(f"Channel {channel_id} not found")
                return {"status": "error", "message": "Channel not found"}
            
            # Update video state to queued (if not already queued)
            if youtube_video.state != YouTubeVideoState.QUEUED:
                youtube_video.queue_for_episode_creation()
                await youtube_video_repo.update(youtube_video)
            
            # Update state to downloading
            youtube_video.mark_as_downloading()
            await youtube_video_repo.update(youtube_video)
            
            # Get followed channel for metadata
            from app.infrastructure.repositories.followed_channel_repository_impl import FollowedChannelRepositoryImpl
            followed_channel_repo = FollowedChannelRepositoryImpl(session)
            followed_channel = await followed_channel_repo.get_by_id(youtube_video.followed_channel_id)
            
            # Create episode entity
            video_id = VideoId.from_url(youtube_video.url)
            episode = Episode.create_episode(
                channel_id=channel_id,
                video_url=youtube_video.url,
                title=youtube_video.title,
                description=youtube_video.description or "",
                publication_date=youtube_video.publish_date,
                youtube_channel=followed_channel.youtube_channel_name if followed_channel else None,
                youtube_channel_id=followed_channel.youtube_channel_id if followed_channel else None,
                youtube_channel_url=followed_channel.youtube_channel_url if followed_channel else None,
                thumbnail_url=youtube_video.thumbnail_url or "",
                requested_language=audio_language,
                requested_quality=audio_quality
            )
            
            # Save episode (in pending state, download will complete it)
            created_episode = await episode_repo.create(episode)
            
            # Commit the episode creation before queuing download
            await session.commit()
            episode_id = created_episode.id
            
            # Update video state to episode_created and link episode_id
            # Note: The actual download will complete the episode, but we mark it as created
            youtube_video.mark_as_episode_created(created_episode.id)
            await youtube_video_repo.update(youtube_video)
            await session.commit()
            
            # Close session before queuing download to prevent database locks
            await session.close()
            
            # Queue audio download using Celery task
            # Import here to avoid circular dependencies
            from app.infrastructure.tasks.download_episode_task import download_episode
            
            # Get user_id from channel for event tracking
            user_id = channel.user_id if channel else None
            
            try:
                # Queue the Celery download task
                download_task_result = download_episode.apply_async(
                    args=(episode_id,),
                    kwargs={
                        'user_id': user_id,
                        'channel_id': channel_id,
                        'audio_language': audio_language,
                        'audio_quality': audio_quality
                    }
                )
                
                logger.info(f"Successfully queued Celery download task {download_task_result.id} for episode {episode_id}")
                
                logger.info(f"Created episode {episode_id} from video {youtube_video_id}")
                
                # Create notification for episode creation
                try:
                    # Re-open a session for notification
                    notification_session = await get_background_task_session()
                    try:
                        from app.infrastructure.repositories.notification_repository_impl import NotificationRepositoryImpl
                        from app.application.services.notification_service import NotificationService
                        
                        notification_repo = NotificationRepositoryImpl(notification_session)
                        notification_service = NotificationService(notification_repo)
                        
                        await notification_service.notify_episode_created(
                            user_id=user_id,
                            episode_title=created_episode.title,
                            channel_name=channel.name,
                            episode_id=episode_id,
                            youtube_video_id=youtube_video_id
                        )
                        await notification_session.commit()
                        logger.info(f"Created notification for episode {episode_id}")
                    finally:
                        await notification_session.close()
                except Exception as notification_error:
                    # Log but don't fail the task if notification creation fails
                    logger.error(f"Failed to create notification for episode {episode_id}: {notification_error}", exc_info=True)
                
                return {
                    "status": "success",
                    "youtube_video_id": youtube_video_id,
                    "channel_id": channel_id,
                    "episode_id": episode_id,
                    "download_task_id": download_task_result.id,
                    "download_queued": True
                }
                
            except Exception as download_error:
                logger.error(f"Failed to queue Celery download task for episode {episode_id}: {download_error}", exc_info=True)
                # Re-open session to update video state
                error_session = await get_background_task_session()
                try:
                    error_repo = YouTubeVideoRepositoryImpl(error_session)
                    error_video = await error_repo.get_by_id(youtube_video_id)
                    if error_video:
                        error_video.state = YouTubeVideoState.REVIEWED
                        await error_repo.update(error_video)
                        await error_session.commit()
                finally:
                    await error_session.close()
                return {"status": "error", "message": f"Failed to queue download: {str(download_error)}"}
            
        except Exception as e:
            logger.error(f"Error creating episode from video {youtube_video_id}: {e}", exc_info=True)
            
            # Try to reset video state on error
            try:
                error_session = await get_background_task_session()
                try:
                    error_repo = YouTubeVideoRepositoryImpl(error_session)
                    error_video = await error_repo.get_by_id(youtube_video_id)
                    if error_video and error_video.state == YouTubeVideoState.DOWNLOADING:
                        error_video.state = YouTubeVideoState.REVIEWED
                        await error_repo.update(error_video)
                        await error_session.commit()
                finally:
                    await error_session.close()
            except Exception as cleanup_error:
                logger.error(f"Error during cleanup: {cleanup_error}")
            
            return {"status": "error", "message": str(e)}
    
    logger.info(f"Creating episode from video {youtube_video_id} for channel {channel_id}")
    return _run_async(_create_episode())

