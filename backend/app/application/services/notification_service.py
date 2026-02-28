"""
Notification Service

Business logic for managing user notifications.
"""
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from app.domain.entities.notification import Notification, NotificationType
from app.infrastructure.repositories.notification_repository_impl import NotificationRepositoryImpl

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for managing user notifications
    Handles business logic for notification creation, retrieval, and management
    """
    
    def __init__(self, notification_repository: NotificationRepositoryImpl):
        """
        Initialize service with repository
        
        Args:
            notification_repository: Repository for notification data access
        """
        self.notification_repository = notification_repository
    
    async def create_notification(
        self,
        user_id: int,
        notification_type: NotificationType,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        executed_by: str = 'user'
    ) -> Notification:
        """
        Create a new notification

        Args:
            user_id: ID of user to notify
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            data: Optional additional data (JSON serializable)
            executed_by: Who triggered the action ('user' or 'system'), defaults to 'user'

        Returns:
            Created notification
        """
        try:
            # Create notification entity
            notification = Notification(
                user_id=user_id,
                type=notification_type,
                title=title,
                message=message,
                data_json=data or {},
                read=False,
                executed_by=executed_by
            )
            
            # Save to database
            created_notification = await self.notification_repository.create(notification)
            
            logger.info(
                f"Created notification {created_notification.id} "
                f"for user {user_id}: {notification_type.value}"
            )
            
            return created_notification
            
        except Exception as e:
            logger.error(f"Error creating notification for user {user_id}: {e}", exc_info=True)
            raise
    
    async def get_user_notifications(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
        unread_only: bool = False
    ) -> tuple[List[Notification], int, int]:
        """
        Get notifications for a user with pagination
        
        Args:
            user_id: User ID
            skip: Number to skip for pagination
            limit: Maximum number to return
            unread_only: If True, return only unread notifications
            
        Returns:
            Tuple of (notifications list, total count, unread count)
        """
        try:
            # Get notifications
            notifications = await self.notification_repository.get_by_user(
                user_id=user_id,
                skip=skip,
                limit=limit,
                unread_only=unread_only
            )
            
            # Get total count
            total_count = await self.notification_repository.get_total_count(
                user_id=user_id,
                unread_only=unread_only
            )
            
            # Get unread count
            unread_count = await self.notification_repository.get_unread_count(user_id)
            
            logger.info(
                f"Retrieved {len(notifications)} notifications for user {user_id} "
                f"(total: {total_count}, unread: {unread_count})"
            )
            
            return notifications, total_count, unread_count
            
        except Exception as e:
            logger.error(f"Error getting notifications for user {user_id}: {e}", exc_info=True)
            raise
    
    async def get_unread_count(self, user_id: int) -> int:
        """
        Get count of unread notifications for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Count of unread notifications
        """
        try:
            count = await self.notification_repository.get_unread_count(user_id)
            return count
            
        except Exception as e:
            logger.error(f"Error getting unread count for user {user_id}: {e}", exc_info=True)
            raise
    
    async def mark_as_read(self, notification_id: int, user_id: int) -> Optional[Notification]:
        """
        Mark a notification as read
        
        Args:
            notification_id: Notification ID
            user_id: User ID (for security check)
            
        Returns:
            Updated notification if successful, None if not found or unauthorized
        """
        try:
            notification = await self.notification_repository.mark_as_read(
                notification_id=notification_id,
                user_id=user_id
            )
            
            if notification:
                logger.info(f"Marked notification {notification_id} as read for user {user_id}")
            else:
                logger.warning(
                    f"Failed to mark notification {notification_id} as read for user {user_id} "
                    "(not found or unauthorized)"
                )
            
            return notification
            
        except Exception as e:
            logger.error(f"Error marking notification {notification_id} as read: {e}", exc_info=True)
            raise
    
    async def mark_all_as_read(self, user_id: int) -> int:
        """
        Mark all notifications as read for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Number of notifications marked as read
        """
        try:
            count = await self.notification_repository.mark_all_as_read(user_id)
            logger.info(f"Marked {count} notifications as read for user {user_id}")
            return count
            
        except Exception as e:
            logger.error(f"Error marking all notifications as read for user {user_id}: {e}", exc_info=True)
            raise
    
    async def delete_notification(self, notification_id: int, user_id: int) -> bool:
        """
        Delete a notification
        
        Args:
            notification_id: Notification ID
            user_id: User ID (for security check)
            
        Returns:
            True if deleted, False if not found or unauthorized
        """
        try:
            deleted = await self.notification_repository.delete(
                notification_id=notification_id,
                user_id=user_id
            )
            
            if deleted:
                logger.info(f"Deleted notification {notification_id} for user {user_id}")
            else:
                logger.warning(
                    f"Failed to delete notification {notification_id} for user {user_id} "
                    "(not found or unauthorized)"
                )
            
            return deleted
            
        except Exception as e:
            logger.error(f"Error deleting notification {notification_id}: {e}", exc_info=True)
            raise
    
    async def delete_all_notifications(self, user_id: int) -> int:
        """
        Delete all notifications for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Number of notifications deleted
        """
        try:
            count = await self.notification_repository.delete_all(user_id)
            logger.info(f"Deleted {count} notifications for user {user_id}")
            return count
            
        except Exception as e:
            logger.error(f"Error deleting all notifications for user {user_id}: {e}", exc_info=True)
            raise
    
    # Helper methods for specific notification types
    
    async def notify_videos_discovered(
        self,
        user_id: int,
        channel_name: str,
        video_count: int,
        followed_channel_id: int
    ) -> Notification:
        """
        Create notification for newly discovered videos
        
        Args:
            user_id: User ID to notify
            channel_name: Name of the YouTube channel
            video_count: Number of videos discovered
            followed_channel_id: ID of the followed channel
            
        Returns:
            Created notification
        """
        try:
            title = f"New videos from {channel_name}"
            
            if video_count == 1:
                message = f"1 new video discovered from {channel_name}"
            else:
                message = f"{video_count} new videos discovered from {channel_name}"
            
            data = {
                "followed_channel_id": followed_channel_id,
                "video_count": video_count,
                "channel_name": channel_name
            }
            
            notification = await self.create_notification(
                user_id=user_id,
                notification_type=NotificationType.VIDEO_DISCOVERED,
                title=title,
                message=message,
                data=data
            )
            
            logger.info(
                f"Created video discovery notification for user {user_id}: "
                f"{video_count} videos from {channel_name}"
            )
            
            return notification
            
        except Exception as e:
            logger.error(
                f"Error creating video discovery notification for user {user_id}: {e}",
                exc_info=True
            )
            # Don't raise - notification failure shouldn't break the main flow
            raise
    
    async def notify_episode_created(
        self,
        user_id: int,
        episode_title: str,
        channel_name: str,
        episode_id: int,
        youtube_video_id: Optional[int] = None
    ) -> Notification:
        """
        Create notification for episode creation
        
        Args:
            user_id: User ID to notify
            episode_title: Title of the created episode
            channel_name: Name of the podcast channel
            episode_id: ID of the created episode
            youtube_video_id: Optional ID of the source YouTube video
            
        Returns:
            Created notification
        """
        try:
            title = "Episode created"
            message = f"Episode '{episode_title}' has been created in {channel_name}"
            
            data = {
                "episode_id": episode_id,
                "episode_title": episode_title,
                "channel_name": channel_name
            }
            
            if youtube_video_id:
                data["youtube_video_id"] = youtube_video_id
            
            notification = await self.create_notification(
                user_id=user_id,
                notification_type=NotificationType.EPISODE_CREATED,
                title=title,
                message=message,
                data=data
            )
            
            logger.info(
                f"Created episode creation notification for user {user_id}: "
                f"episode {episode_id} '{episode_title}'"
            )
            
            return notification
            
        except Exception as e:
            logger.error(
                f"Error creating episode creation notification for user {user_id}: {e}",
                exc_info=True
            )
            # Don't raise - notification failure shouldn't break the main flow
            raise
    
    async def notify_channel_search_started(
        self,
        user_id: int,
        channel_name: str,
        followed_channel_id: int,
        executed_by: str = 'user'
    ) -> Notification:
        """
        Create notification when search for new videos starts

        Args:
            user_id: User ID to notify
            channel_name: Name of the YouTube channel
            followed_channel_id: ID of the followed channel
            executed_by: Who triggered the action ('user' or 'system'), defaults to 'user'

        Returns:
            Created notification
        """
        try:
            title = f"Searching for new videos"
            message = f"Searching for new videos from {channel_name}"

            data = {
                "followed_channel_id": followed_channel_id,
                "channel_name": channel_name
            }

            notification = await self.create_notification(
                user_id=user_id,
                notification_type=NotificationType.CHANNEL_SEARCH_STARTED,
                title=title,
                message=message,
                data=data,
                executed_by=executed_by
            )
            
            logger.info(
                f"Created channel search started notification for user {user_id}: "
                f"channel {channel_name}"
            )
            
            return notification
            
        except Exception as e:
            logger.error(
                f"Error creating search started notification for user {user_id}: {e}",
                exc_info=True
            )
            raise
    
    async def notify_channel_search_completed(
        self,
        user_id: int,
        channel_name: str,
        followed_channel_id: int,
        new_videos_count: int,
        total_videos_count: int,
        executed_by: str = 'user'
    ) -> Notification:
        """
        Create notification when search for new videos completes successfully

        Args:
            user_id: User ID to notify
            channel_name: Name of the YouTube channel
            followed_channel_id: ID of the followed channel
            new_videos_count: Number of new videos found
            total_videos_count: Total videos in pending review state
            executed_by: Who triggered the action ('user' or 'system'), defaults to 'user'

        Returns:
            Created notification
        """
        try:
            title = f"Search completed for {channel_name}"

            if new_videos_count == 0:
                message = f"No new videos found from {channel_name}"
            elif new_videos_count == 1:
                message = f"1 new video found from {channel_name}"
            else:
                message = f"{new_videos_count} new videos found from {channel_name}"

            data = {
                "followed_channel_id": followed_channel_id,
                "channel_name": channel_name,
                "new_videos_count": new_videos_count,
                "total_videos_count": total_videos_count
            }

            notification = await self.create_notification(
                user_id=user_id,
                notification_type=NotificationType.CHANNEL_SEARCH_COMPLETED,
                title=title,
                message=message,
                data=data,
                executed_by=executed_by
            )
            
            logger.info(
                f"Created channel search completed notification for user {user_id}: "
                f"channel {channel_name}, {new_videos_count} new videos"
            )
            
            return notification
            
        except Exception as e:
            logger.error(
                f"Error creating search completed notification for user {user_id}: {e}",
                exc_info=True
            )
            raise
    
    async def notify_channel_search_error(
        self,
        user_id: int,
        channel_name: str,
        followed_channel_id: int,
        error_message: Optional[str] = None,
        executed_by: str = 'user'
    ) -> Notification:
        """
        Create notification when search for new videos fails

        Args:
            user_id: User ID to notify
            channel_name: Name of the YouTube channel
            followed_channel_id: ID of the followed channel
            error_message: Optional error message for debugging
            executed_by: Who triggered the action ('user' or 'system'), defaults to 'user'

        Returns:
            Created notification
        """
        try:
            title = f"Search failed for {channel_name}"
            message = f"Error searching for new videos from {channel_name}. You can retry from the subscriptions page."

            data = {
                "followed_channel_id": followed_channel_id,
                "channel_name": channel_name
            }

            if error_message:
                data["error_message"] = error_message

            notification = await self.create_notification(
                user_id=user_id,
                notification_type=NotificationType.CHANNEL_SEARCH_ERROR,
                title=title,
                message=message,
                data=data,
                executed_by=executed_by
            )
            
            logger.info(
                f"Created channel search error notification for user {user_id}: "
                f"channel {channel_name}"
            )
            
            return notification
            
        except Exception as e:
            logger.error(
                f"Error creating search error notification for user {user_id}: {e}",
                exc_info=True
            )
            raise



