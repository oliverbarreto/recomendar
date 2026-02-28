"""
Notification Repository Implementation

Handles all database operations for notifications.
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
import logging
import json

from app.domain.entities.notification import Notification, NotificationType
from app.infrastructure.database.models.notification import NotificationModel

logger = logging.getLogger(__name__)


class NotificationRepositoryImpl:
    """
    Repository implementation for Notification entity
    Handles all database operations for notifications
    """
    
    def __init__(self, db_session: AsyncSession):
        """
        Initialize repository with database session
        
        Args:
            db_session: SQLAlchemy async session
        """
        self.db_session = db_session
    
    def _to_domain(self, model: NotificationModel) -> Notification:
        """
        Convert database model to domain entity

        Args:
            model: NotificationModel instance

        Returns:
            Notification domain entity
        """
        # Parse data_json if it's a string
        data_json = model.data_json
        if isinstance(data_json, str):
            try:
                data_json = json.loads(data_json)
            except (json.JSONDecodeError, TypeError):
                data_json = {}

        return Notification(
            id=model.id,
            user_id=model.user_id,
            type=NotificationType(model.type),
            title=model.title,
            message=model.message,
            data_json=data_json or {},
            read=model.read,
            executed_by=model.executed_by,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def _to_model(self, entity: Notification) -> NotificationModel:
        """
        Convert domain entity to database model

        Args:
            entity: Notification domain entity

        Returns:
            NotificationModel instance
        """
        return NotificationModel(
            id=entity.id,
            user_id=entity.user_id,
            type=entity.type.value,
            title=entity.title,
            message=entity.message,
            data_json=entity.data_json,
            read=entity.read,
            executed_by=entity.executed_by,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )
    
    async def create(self, notification: Notification) -> Notification:
        """
        Create a new notification

        Args:
            notification: Notification domain entity

        Returns:
            Created notification with ID
        """
        try:
            model = self._to_model(notification)
            self.db_session.add(model)
            await self.db_session.commit()  # CRITICAL FIX: Changed from flush() to commit() for immediate visibility
            await self.db_session.refresh(model)

            logger.info(f"Created notification {model.id} for user {model.user_id}")
            return self._to_domain(model)

        except Exception as e:
            logger.error(f"Error creating notification: {e}", exc_info=True)
            raise
    
    async def get_by_id(self, notification_id: int) -> Optional[Notification]:
        """
        Get notification by ID
        
        Args:
            notification_id: Notification ID
            
        Returns:
            Notification if found, None otherwise
        """
        try:
            stmt = select(NotificationModel).where(NotificationModel.id == notification_id)
            result = await self.db_session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if model:
                return self._to_domain(model)
            return None
            
        except Exception as e:
            logger.error(f"Error getting notification {notification_id}: {e}", exc_info=True)
            raise
    
    async def get_by_user(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
        unread_only: bool = False
    ) -> List[Notification]:
        """
        Get notifications for a user with pagination
        
        Args:
            user_id: User ID
            skip: Number of notifications to skip
            limit: Maximum number of notifications to return
            unread_only: If True, return only unread notifications
            
        Returns:
            List of notifications
        """
        try:
            stmt = select(NotificationModel).where(NotificationModel.user_id == user_id)
            
            if unread_only:
                stmt = stmt.where(NotificationModel.read == False)
            
            stmt = stmt.order_by(NotificationModel.created_at.desc())
            stmt = stmt.offset(skip).limit(limit)
            
            result = await self.db_session.execute(stmt)
            models = result.scalars().all()
            
            return [self._to_domain(model) for model in models]
            
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
            stmt = select(func.count(NotificationModel.id)).where(
                NotificationModel.user_id == user_id,
                NotificationModel.read == False
            )
            result = await self.db_session.execute(stmt)
            count = result.scalar()
            
            return count or 0
            
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
            Updated notification if found and belongs to user, None otherwise
        """
        try:
            # First, verify notification belongs to user
            notification = await self.get_by_id(notification_id)
            if not notification or notification.user_id != user_id:
                logger.warning(f"Notification {notification_id} not found or doesn't belong to user {user_id}")
                return None
            
            # Update the notification
            stmt = (
                update(NotificationModel)
                .where(NotificationModel.id == notification_id)
                .where(NotificationModel.user_id == user_id)
                .values(read=True)
            )
            await self.db_session.execute(stmt)
            
            # Get updated notification
            updated_notification = await self.get_by_id(notification_id)
            logger.info(f"Marked notification {notification_id} as read for user {user_id}")
            
            return updated_notification
            
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
            stmt = (
                update(NotificationModel)
                .where(NotificationModel.user_id == user_id)
                .where(NotificationModel.read == False)
                .values(read=True)
            )
            result = await self.db_session.execute(stmt)
            count = result.rowcount
            
            logger.info(f"Marked {count} notifications as read for user {user_id}")
            return count
            
        except Exception as e:
            logger.error(f"Error marking all notifications as read for user {user_id}: {e}", exc_info=True)
            raise
    
    async def delete(self, notification_id: int, user_id: int) -> bool:
        """
        Delete a notification
        
        Args:
            notification_id: Notification ID
            user_id: User ID (for security check)
            
        Returns:
            True if deleted, False if not found or doesn't belong to user
        """
        try:
            stmt = (
                delete(NotificationModel)
                .where(NotificationModel.id == notification_id)
                .where(NotificationModel.user_id == user_id)
            )
            result = await self.db_session.execute(stmt)
            
            deleted = result.rowcount > 0
            if deleted:
                logger.info(f"Deleted notification {notification_id} for user {user_id}")
            else:
                logger.warning(f"Notification {notification_id} not found or doesn't belong to user {user_id}")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Error deleting notification {notification_id}: {e}", exc_info=True)
            raise
    
    async def delete_all(self, user_id: int) -> int:
        """
        Delete all notifications for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Number of notifications deleted
        """
        try:
            stmt = delete(NotificationModel).where(NotificationModel.user_id == user_id)
            result = await self.db_session.execute(stmt)
            count = result.rowcount
            
            logger.info(f"Deleted {count} notifications for user {user_id}")
            return count
            
        except Exception as e:
            logger.error(f"Error deleting all notifications for user {user_id}: {e}", exc_info=True)
            raise
    
    async def get_total_count(self, user_id: int, unread_only: bool = False) -> int:
        """
        Get total count of notifications for a user
        
        Args:
            user_id: User ID
            unread_only: If True, count only unread notifications
            
        Returns:
            Total count of notifications
        """
        try:
            stmt = select(func.count(NotificationModel.id)).where(
                NotificationModel.user_id == user_id
            )
            
            if unread_only:
                stmt = stmt.where(NotificationModel.read == False)
            
            result = await self.db_session.execute(stmt)
            count = result.scalar()
            
            return count or 0
            
        except Exception as e:
            logger.error(f"Error getting total count for user {user_id}: {e}", exc_info=True)
            raise



