"""
User Settings Application Service

Application service for managing user preferences for subscription checks
"""
from typing import Optional
import logging

from app.domain.entities.user_settings import UserSettings
from app.domain.entities.followed_channel import SubscriptionCheckFrequency
from app.domain.repositories.user_settings_repository import UserSettingsRepository
from app.core.logging import get_structured_logger

logger = get_structured_logger("user_settings_service")


class UserSettingsService:
    """
    Application service for user settings management
    
    Handles business logic for managing user preferences,
    particularly subscription check frequency.
    """
    
    def __init__(self, user_settings_repository: UserSettingsRepository):
        """
        Initialize the user settings service
        
        Args:
            user_settings_repository: Repository for user settings
        """
        self.user_settings_repository = user_settings_repository
    
    async def get_user_settings(self, user_id: int) -> UserSettings:
        """
        Get user settings or create defaults if not found
        
        Args:
            user_id: ID of the user
        
        Returns:
            UserSettings entity (existing or newly created with defaults)
        """
        try:
            settings = await self.user_settings_repository.get_or_create_default(user_id)
            return settings
        except Exception as e:
            logger.error(f"Failed to get user settings for user {user_id}: {e}")
            raise
    
    async def update_subscription_frequency(
        self,
        user_id: int,
        frequency: SubscriptionCheckFrequency
    ) -> UserSettings:
        """
        Update subscription check frequency for a user

        Args:
            user_id: ID of the user
            frequency: New check frequency (daily or weekly)

        Returns:
            Updated UserSettings entity
        """
        try:
            # Get or create settings
            settings = await self.get_user_settings(user_id)

            # Update frequency
            settings.update_subscription_frequency(frequency)

            # Save to repository
            updated = await self.user_settings_repository.update(settings)

            logger.info(f"Updated subscription frequency for user {user_id}: {frequency.value}")
            return updated

        except Exception as e:
            logger.error(f"Failed to update subscription frequency for user {user_id}: {e}")
            raise

    async def update_check_time(
        self,
        user_id: int,
        hour: int,
        minute: int
    ) -> UserSettings:
        """
        Update preferred check time for a user

        Args:
            user_id: ID of the user
            hour: Preferred hour (0-23) in UTC
            minute: Preferred minute (0-59)

        Returns:
            Updated UserSettings entity
        """
        try:
            # Get or create settings
            settings = await self.get_user_settings(user_id)

            # Update check time
            settings.update_check_time(hour, minute)

            # Save to repository
            updated = await self.user_settings_repository.update(settings)

            logger.info(f"Updated check time for user {user_id}: {hour:02d}:{minute:02d} UTC")
            return updated

        except Exception as e:
            logger.error(f"Failed to update check time for user {user_id}: {e}")
            raise

    async def update_timezone(
        self,
        user_id: int,
        timezone: str
    ) -> UserSettings:
        """
        Update preferred timezone for a user

        Args:
            user_id: ID of the user
            timezone: IANA timezone string (e.g., 'Europe/Madrid', 'America/New_York')

        Returns:
            Updated UserSettings entity
        """
        try:
            # Get or create settings
            settings = await self.get_user_settings(user_id)

            # Update timezone (validation happens in entity method)
            settings.update_timezone(timezone)

            # Save to repository
            updated = await self.user_settings_repository.update(settings)

            logger.info(f"Updated timezone for user {user_id}: {timezone}")
            return updated

        except Exception as e:
            logger.error(f"Failed to update timezone for user {user_id}: {e}")
            raise







