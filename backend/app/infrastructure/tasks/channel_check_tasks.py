"""
Celery tasks for checking followed channels for new videos

This module contains tasks for periodic checking of YouTube channels
and discovering new videos.
"""
from celery import shared_task
from typing import Optional
import logging
import asyncio
from zoneinfo import ZoneInfo
from datetime import datetime, timezone, timedelta

from app.infrastructure.database.connection import get_background_task_session
from app.infrastructure.repositories.followed_channel_repository_impl import FollowedChannelRepositoryImpl
from app.infrastructure.repositories.youtube_video_repository_impl import YouTubeVideoRepositoryImpl
from app.infrastructure.repositories.user_settings_repository_impl import UserSettingsRepositoryImpl
from app.infrastructure.services.youtube_metadata_service_impl import YouTubeMetadataServiceImpl
from app.infrastructure.services.ytdlp_discovery_strategy import YtdlpDiscoveryStrategy

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
    name="app.infrastructure.tasks.channel_check_tasks.check_followed_channel_for_new_videos",
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True
)
def check_followed_channel_for_new_videos(self, followed_channel_id: int) -> dict:
    """
    Check a followed channel for new videos.
    
    This task:
    1. Creates a "search started" notification
    2. Discovers new videos from the YouTube channel
    3. Handles auto-approve if enabled
    4. Creates a "search completed" notification with results
    5. Creates an "error" notification if something fails
    
    Args:
        followed_channel_id: ID of the followed channel to check
        
    Returns:
        Dictionary with results of the check
    """
    async def _check_channel():
        session = await get_background_task_session()
        notification_service = None
        followed_channel = None
        task_status = None
        
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
                    followed_channel_id=followed_channel.id
                )
                logger.info(f"Created search started notification for channel {followed_channel.youtube_channel_name}")
            except Exception as notification_error:
                # Log but don't fail the task if notification creation fails
                logger.error(f"Failed to create search started notification: {notification_error}", exc_info=True)

            # Mark task as started
            if task_status:
                task_status.mark_started()
                await task_status_repo.update(task_status)
                logger.info(f"Marked task {self.request.id} as started")

                # Update progress to show task is initializing
                task_status.update_progress(10, "Initializing yt-dlp discovery")
                await task_status_repo.update(task_status)
            
            # Initialize services
            metadata_service = YouTubeMetadataServiceImpl()

            # Use yt-dlp discovery strategy
            discovery_strategy = YtdlpDiscoveryStrategy(
                metadata_service=metadata_service,
                youtube_video_repository=youtube_video_repo
            )

            # Update progress before fetching videos
            if task_status:
                task_status.update_progress(20, "Fetching channel videos via yt-dlp")
                await task_status_repo.update(task_status)

            # Discover new videos
            new_videos = await discovery_strategy.discover_new_videos(
                followed_channel=followed_channel,
                max_videos=50
            )

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
                    
                    # Queue episode creation task - use apply_async with explicit args/kwargs to avoid Celery serialization issues
                    create_episode_from_youtube_video.apply_async(
                        args=(video.id, followed_channel.auto_approve_channel_id),
                        kwargs={}
                    )
                    logger.info(f"Auto-approved and queued episode creation for video {video.id}")
            
            # Get total pending videos count for the channel
            from app.domain.entities.youtube_video import YouTubeVideoState
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
                    total_videos_count=total_pending_count
                )
                logger.info(f"Created search completed notification for channel {followed_channel.youtube_channel_name}: {len(new_videos)} new videos")
            except Exception as notification_error:
                # Log but don't fail the task if notification creation fails
                logger.error(f"Failed to create search completed notification: {notification_error}", exc_info=True)
            
            # Mark task as success
            if task_status:
                import json
                task_status.mark_success(result_json=json.dumps({
                    "new_videos_count": len(new_videos),
                    "total_pending_count": total_pending_count
                }))
                await task_status_repo.update(task_status)
                logger.info(f"Marked task {self.request.id} as successful")
            
            return {
                "status": "success",
                "followed_channel_id": followed_channel_id,
                "new_videos_count": len(new_videos),
                "total_pending_count": total_pending_count,
                "auto_approved": followed_channel.auto_approve and len(new_videos) > 0
            }
            
        except Exception as e:
            logger.error(f"Error checking channel {followed_channel_id}: {e}", exc_info=True)
            
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
                        error_message=str(e)
                    )
                    logger.info(f"Created search error notification for channel {followed_channel.youtube_channel_name}")
                except Exception as notification_error:
                    logger.error(f"Failed to create search error notification: {notification_error}", exc_info=True)
            
            return {"status": "error", "message": str(e)}
        finally:
            await session.close()
    
    logger.info(f"Checking followed channel {followed_channel_id} for new videos")
    try:
        result = _run_async(_check_channel())
        logger.info(f"Task completed with result: {result}")
        return result
    except Exception as e:
        logger.error(f"CRITICAL ERROR in check_followed_channel_for_new_videos: {e}", exc_info=True)
        return {"status": "error", "message": f"Task execution failed: {str(e)}"}


@shared_task(
    name="app.infrastructure.tasks.channel_check_tasks.periodic_check_all_channels",
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True
)
def periodic_check_all_channels(self) -> dict:
    """
    Periodic task that checks all followed channels based on user preferences.
    
    This task is scheduled by Celery Beat and queries the database
    for users and their check frequency preferences, then queues
    individual channel check tasks.
    
    Returns:
        Dictionary with results of the periodic check
    """
    async def _check_all_channels():
        session = await get_background_task_session()
        try:
            # Initialize repositories
            followed_channel_repo = FollowedChannelRepositoryImpl(session)
            user_settings_repo = UserSettingsRepositoryImpl(session)
            
            # Get all followed channels grouped by user
            # For each user, get their check frequency and check their channels
            from app.domain.repositories.user import UserRepository
            from app.infrastructure.repositories.user_repository import UserRepositoryImpl
            
            user_repo = UserRepositoryImpl(session)
            all_users = await user_repo.get_all(skip=0, limit=1000)  # Get all users
            
            total_queued = 0
            
            for user in all_users:
                # Get or create user settings
                user_settings = await user_settings_repo.get_or_create_default(user.id)
                frequency = user_settings.subscription_check_frequency.value
                
                # Get user's followed channels
                user_channels = await followed_channel_repo.get_by_user_id(user.id)
                
                # Calculate threshold date based on frequency
                from datetime import datetime, timedelta
                now = datetime.utcnow()
                if frequency == "daily":
                    threshold = now - timedelta(days=1)
                elif frequency == "twice_weekly":
                    threshold = now - timedelta(days=3.5)
                elif frequency == "weekly":
                    threshold = now - timedelta(days=7)
                else:
                    threshold = now - timedelta(days=1)  # Default to daily
                
                # Filter channels that need checking
                for channel in user_channels:
                    # Check if channel needs checking
                    if channel.last_checked is None or channel.last_checked < threshold:
                        # Queue check task - use apply_async with explicit args/kwargs to avoid Celery serialization issues
                        check_followed_channel_for_new_videos.apply_async(
                            args=(channel.id,),
                            kwargs={}
                        )
                        total_queued += 1
                        logger.debug(f"Queued check for channel {channel.id} (user: {user.id}, frequency: {frequency})")
            
            logger.info(f"Periodic check queued {total_queued} channel checks")
            return {
                "status": "success",
                "queued_channels": total_queued
            }
            
        except Exception as e:
            logger.error(f"Error in periodic check: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}
        finally:
            await session.close()
    
    logger.info("Running periodic check for all channels")
    return _run_async(_check_all_channels())


@shared_task(
    name="app.infrastructure.tasks.channel_check_tasks.scheduled_check_all_channels_rss",
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True
)
def scheduled_check_all_channels_rss(self) -> dict:
    """
    Scheduled task to check all followed channels for new videos using RSS method.

    This task is scheduled by Celery Beat and runs every 30 minutes. It checks if current
    time matches any user's preferred check time in their timezone, then queues individual
    RSS check tasks for channels that need checking based on frequency settings.

    The RSS method is faster (5-10s per channel) compared to full yt-dlp method (30-60s),
    making it ideal for automated daily/weekly checks.

    Timezone-aware: Respects each user's timezone and preferred check time (hour:minute).
    Only queues checks when current time matches user's preference (±30 minute window).

    Returns:
        Dictionary with results of the scheduled check
    """
    async def _check_all_channels_rss():
        session = await get_background_task_session()
        try:
            # Initialize repositories
            followed_channel_repo = FollowedChannelRepositoryImpl(session)
            user_settings_repo = UserSettingsRepositoryImpl(session)

            # Get all users
            from app.domain.repositories.user import UserRepository
            from app.infrastructure.repositories.user_repository import UserRepositoryImpl

            user_repo = UserRepositoryImpl(session)
            all_users = await user_repo.get_all(skip=0, limit=1000)  # Get all users

            total_queued = 0
            users_processed = 0

            # Log task execution start
            now_utc = datetime.now(timezone.utc)
            logger.info("=" * 80)
            logger.info("Starting scheduled channel check (RSS method)")
            logger.info(f"Current UTC time: {now_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            logger.info("=" * 80)

            for user in all_users:
                users_processed += 1

                # Get or create user settings
                user_settings = await user_settings_repo.get_or_create_default(user.id)
                frequency = user_settings.subscription_check_frequency.value

                # Get user's timezone and preferred check time
                try:
                    user_tz = ZoneInfo(user_settings.timezone)
                except Exception as e:
                    logger.warning(
                        f"Invalid timezone '{user_settings.timezone}' for user {user.id}, "
                        f"falling back to UTC: {str(e)}"
                    )
                    user_tz = ZoneInfo("UTC")

                preferred_hour = user_settings.preferred_check_hour
                preferred_minute = user_settings.preferred_check_minute

                # Get current time in user's timezone
                now_user_tz = now_utc.astimezone(user_tz)

                # Check if current time matches user's preferred check time
                # Beat runs at :00 and :30, so users can only choose those minutes
                # We match if hour and minute both match exactly
                current_hour = now_user_tz.hour
                current_minute = now_user_tz.minute

                time_matches = (
                    current_hour == preferred_hour and
                    current_minute == preferred_minute
                )

                if not time_matches:
                    # Not the right time for this user
                    logger.debug(
                        f"User {user.id} check time {preferred_hour:02d}:{preferred_minute:02d} "
                        f"does not match current time {current_hour:02d}:{current_minute:02d} "
                        f"in timezone {user_settings.timezone} - skipping"
                    )
                    continue  # Skip this user

                # Time matches! Log it
                logger.info(
                    f"User {user.id} check time {preferred_hour:02d}:{preferred_minute:02d} "
                    f"matches current time {current_hour:02d}:{current_minute:02d} "
                    f"in timezone {user_settings.timezone} - processing channels"
                )

                # Get user's followed channels
                user_channels = await followed_channel_repo.get_by_user_id(user.id)

                if not user_channels:
                    logger.debug(f"User {user.id} has no followed channels, skipping")
                    continue

                # Calculate threshold date based on frequency
                if frequency == "daily":
                    threshold = now_utc.replace(tzinfo=None) - timedelta(days=1)
                elif frequency == "weekly":
                    threshold = now_utc.replace(tzinfo=None) - timedelta(days=7)
                else:
                    threshold = now_utc.replace(tzinfo=None) - timedelta(days=1)  # Default to daily

                # Filter channels that need checking
                channels_queued_for_user = 0
                for channel in user_channels:
                    # Check if channel needs checking (hasn't been checked within threshold)
                    if channel.last_checked is None or channel.last_checked < threshold:
                        # Queue RSS check task with executed_by='system'
                        # Import the RSS check task
                        from app.infrastructure.tasks.channel_check_rss_tasks import check_followed_channel_for_new_videos_rss

                        check_followed_channel_for_new_videos_rss.apply_async(
                            args=(channel.id,),
                            kwargs={'executed_by': 'system'}
                        )
                        total_queued += 1
                        channels_queued_for_user += 1
                        logger.info(
                            f"Queueing channel {channel.id} ({channel.youtube_channel_name}) "
                            f"for user {user.id} - scheduled check at "
                            f"{preferred_hour:02d}:{preferred_minute:02d} {user_settings.timezone}"
                        )
                    else:
                        logger.debug(
                            f"Channel {channel.id} ({channel.youtube_channel_name}) already checked recently at {channel.last_checked}"
                        )

                if channels_queued_for_user > 0:
                    logger.info(
                        f"User {user.id}: Queued {channels_queued_for_user} channels for checking "
                        f"(frequency: {frequency}, scheduled time: {preferred_hour:02d}:{preferred_minute:02d} {user_settings.timezone})"
                    )

            logger.info(
                f"Scheduled RSS check completed: Processed {users_processed} users, "
                f"queued {total_queued} channel checks (executed_by: system)"
            )
            return {
                "status": "success",
                "users_processed": users_processed,
                "queued_channels": total_queued,
                "method": "rss_feed",
                "executed_by": "system"
            }

        except Exception as e:
            logger.error(f"Error in scheduled RSS check: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}
        finally:
            await session.close()

    logger.info("Running scheduled RSS check for all channels (executed_by: system)")
    return _run_async(_check_all_channels_rss())


# Simple test task for verifying Celery is working
@shared_task(
    name="app.infrastructure.tasks.channel_check_tasks.test_task",
    bind=True
)
def test_task(self, message: str = "Hello from Celery!") -> dict:
    """
    Simple test task to verify Celery is working correctly.
    
    Args:
        message: Test message to return
        
    Returns:
        Dictionary with the test message
    """
    logger.info(f"Test task received message: {message}")
    return {
        "status": "success",
        "message": message,
        "task_id": test_task.request.id if hasattr(test_task.request, 'id') else None,
    }


