"""
Celery tasks for checking followed channels for new videos using RSS feeds

This module contains tasks for checking YouTube channels using RSS feeds
for faster discovery of recent videos.
"""

from celery import shared_task
from typing import Dict, Any
import logging
import asyncio

from app.infrastructure.database.connection import get_background_task_session
from app.infrastructure.repositories.followed_channel_repository_impl import FollowedChannelRepositoryImpl
from app.infrastructure.repositories.youtube_video_repository_impl import YouTubeVideoRepositoryImpl
from app.infrastructure.services.youtube_metadata_service_impl import YouTubeMetadataServiceImpl
from app.infrastructure.services.youtube_rss_service import YouTubeRSSService
from app.infrastructure.services.rss_discovery_strategy import RSSDiscoveryStrategy
from app.domain.entities.youtube_video import YouTubeVideoState

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
    bind=True,
    name="app.infrastructure.tasks.channel_check_rss_tasks.check_followed_channel_for_new_videos_rss",
    autoretry_for=(ConnectionError, TimeoutError),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def check_followed_channel_for_new_videos_rss(
    self,
    followed_channel_id: int,
    executed_by: str = 'user'
) -> Dict[str, Any]:
    """
    Check for new videos using RSS feed strategy.

    This task:
    1. Creates a "search started" notification
    2. Fetches RSS feed (last 10-15 videos)
    3. Discovers new videos and extracts metadata
    4. Handles auto-approve if enabled
    5. Creates a "search completed" notification with results
    6. Creates an "error" notification if something fails

    Args:
        followed_channel_id: ID of the followed channel to check
        executed_by: Who triggered the check ('user' or 'system'), defaults to 'user'

    Returns:
        Dictionary with results of the check
    """
    async def _check_channel_rss():
        session = await get_background_task_session()
        notification_service = None
        followed_channel = None
        task_status = None
        rss_service = None

        try:
            # Initialize repositories
            followed_channel_repo = FollowedChannelRepositoryImpl(session)
            youtube_video_repo = YouTubeVideoRepositoryImpl(session)

            # Initialize task status repository
            from app.infrastructure.repositories.celery_task_status_repository_impl import CeleryTaskStatusRepository
            task_status_repo = CeleryTaskStatusRepository(session)

            # Get task status record
            task_status = await task_status_repo.get_by_task_id(self.request.id)

            # Initialize notification service early for error handling
            from app.infrastructure.repositories.notification_repository_impl import NotificationRepositoryImpl
            from app.application.services.notification_service import NotificationService

            notification_repo = NotificationRepositoryImpl(session)
            notification_service = NotificationService(notification_repo)

            # Get followed channel
            followed_channel = await followed_channel_repo.get_by_id(followed_channel_id)
            if not followed_channel:
                logger.error(f"Followed channel {followed_channel_id} not found")
                if task_status:
                    task_status.mark_failure(error_message="Followed channel not found")
                    await task_status_repo.update(task_status)
                return {"status": "error", "message": "Followed channel not found"}

            # Create "search started" notification FIRST (before any status updates)
            try:
                await notification_service.notify_channel_search_started(
                    user_id=followed_channel.user_id,
                    channel_name=followed_channel.youtube_channel_name,
                    followed_channel_id=followed_channel.id,
                    executed_by=executed_by
                )
                logger.info(f"Created search started notification for channel {followed_channel.youtube_channel_name} (executed_by={executed_by})")
            except Exception as notification_error:
                # Log but don't fail the task if notification creation fails
                logger.error(f"Failed to create search started notification: {notification_error}", exc_info=True)

            # Mark task as started
            if task_status:
                task_status.mark_started()
                await task_status_repo.update(task_status)
                logger.info(f"Marked task {self.request.id} as started")

                # Update progress to show task is initializing
                task_status.update_progress(10, "Initializing RSS discovery")
                await task_status_repo.update(task_status)

            # Initialize RSS discovery strategy
            rss_service = YouTubeRSSService()
            metadata_service = YouTubeMetadataServiceImpl()
            discovery_strategy = RSSDiscoveryStrategy(
                rss_service=rss_service,
                metadata_service=metadata_service,
                youtube_video_repository=youtube_video_repo
            )

            # Update progress before fetching RSS feed
            if task_status:
                task_status.update_progress(20, "Fetching RSS feed")
                await task_status_repo.update(task_status)

            # Discover new videos using RSS
            logger.info(f"[RSS Task] Starting discovery for channel {followed_channel_id}")
            new_videos = await discovery_strategy.discover_new_videos(
                followed_channel=followed_channel,
                max_videos=50  # Ignored by RSS strategy
            )
            logger.info(f"[RSS Task] Discovered {len(new_videos)} new videos")

            # Update progress after discovery
            if task_status:
                task_status.update_progress(60, f"Discovered {len(new_videos)} new videos")
                await task_status_repo.update(task_status)

            # Update last_checked timestamp
            await followed_channel_repo.update_last_checked(followed_channel.id)

            # Update progress after saving data
            if task_status:
                task_status.update_progress(80, "Saving discovery results")
                await task_status_repo.update(task_status)

            # Handle auto-approve if enabled
            if followed_channel.auto_approve and followed_channel.auto_approve_channel_id:
                logger.info(f"Auto-approve enabled for channel {followed_channel_id}")

                # Update progress before auto-approve processing
                if task_status:
                    task_status.update_progress(90, f"Auto-approving {len(new_videos)} videos")
                    await task_status_repo.update(task_status)

                # Queue episode creation for each new video
                from app.infrastructure.tasks.create_episode_from_video_task import create_episode_from_youtube_video

                for video in new_videos:
                    # Transition video to queued state immediately for auto-approve
                    video.queue_for_episode_creation()
                    await youtube_video_repo.update(video)

                    # Queue episode creation task
                    create_episode_from_youtube_video.apply_async(
                        args=(video.id, followed_channel.auto_approve_channel_id),
                        kwargs={}
                    )
                    logger.info(f"Auto-approved and queued episode creation for video {video.id}")

            # Get total pending videos count for the channel
            pending_videos = await youtube_video_repo.get_by_followed_channel_and_state(
                followed_channel_id=followed_channel.id,
                state=YouTubeVideoState.PENDING_REVIEW
            )
            total_pending_count = len(pending_videos) if pending_videos else 0

            # Create "search completed" notification
            try:
                await notification_service.notify_channel_search_completed(
                    user_id=followed_channel.user_id,
                    channel_name=followed_channel.youtube_channel_name,
                    followed_channel_id=followed_channel.id,
                    new_videos_count=len(new_videos),
                    total_videos_count=total_pending_count,
                    executed_by=executed_by
                )
                logger.info(
                    f"Created search completed notification for channel {followed_channel.youtube_channel_name}: "
                    f"{len(new_videos)} new videos (executed_by={executed_by})"
                )
            except Exception as notification_error:
                # Log but don't fail the task if notification creation fails
                logger.error(f"Failed to create search completed notification: {notification_error}", exc_info=True)

            # Mark task as success
            if task_status:
                import json
                task_status.mark_success(result_json=json.dumps({
                    "new_videos_count": len(new_videos),
                    "total_pending_count": total_pending_count,
                    "method": "rss_feed"
                }))
                await task_status_repo.update(task_status)
                logger.info(f"Marked task {self.request.id} as successful")

            return {
                "status": "success",
                "followed_channel_id": followed_channel_id,
                "new_videos_count": len(new_videos),
                "total_pending_count": total_pending_count,
                "auto_approved": followed_channel.auto_approve and len(new_videos) > 0,
                "method": "rss_feed"
            }

        except Exception as e:
            logger.error(f"Error checking channel {followed_channel_id} via RSS: {e}", exc_info=True)

            # Mark task as failed
            if task_status:
                task_status.mark_failure(error_message=str(e))
                await task_status_repo.update(task_status)
                logger.info(f"Marked task {self.request.id} as failed")

            # Create error notification if we have the notification service and channel info
            if notification_service and followed_channel:
                try:
                    await notification_service.notify_channel_search_error(
                        user_id=followed_channel.user_id,
                        channel_name=followed_channel.youtube_channel_name,
                        followed_channel_id=followed_channel.id,
                        error_message=str(e),
                        executed_by=executed_by
                    )
                    logger.info(f"Created search error notification for channel {followed_channel.youtube_channel_name} (executed_by={executed_by})")
                except Exception as notification_error:
                    logger.error(f"Failed to create search error notification: {notification_error}", exc_info=True)

            return {"status": "error", "message": str(e)}

        finally:
            # Cleanup RSS service session
            if rss_service:
                try:
                    await rss_service.close()
                except Exception as cleanup_error:
                    logger.error(f"Error closing RSS service: {cleanup_error}")

            await session.close()

    logger.info(f"Checking followed channel {followed_channel_id} for new videos using RSS")
    try:
        result = _run_async(_check_channel_rss())
        logger.info(f"Task completed with result: {result}")
        return result
    except Exception as e:
        logger.error(f"CRITICAL ERROR in check_followed_channel_for_new_videos_rss: {e}", exc_info=True)
        return {"status": "error", "message": f"Task execution failed: {str(e)}"}
