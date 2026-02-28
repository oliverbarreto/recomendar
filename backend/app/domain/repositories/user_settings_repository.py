"""
UserSettings repository interface

Domain layer interface for user settings data access
"""
from abc import abstractmethod
from typing import Optional
from app.domain.repositories.base import BaseRepository
from app.domain.entities.user_settings import UserSettings
from app.domain.entities.followed_channel import SubscriptionCheckFrequency


class UserSettingsRepository(BaseRepository[UserSettings]):
    """
    Repository interface for UserSettings entities.
    Extends BaseRepository with user settings-specific operations.
    """
    
    @abstractmethod
    async def get_by_user_id(self, user_id: int) -> Optional[UserSettings]:
        """
        Get user settings by user ID
        
        Args:
            user_id: The user ID to search for
            
        Returns:
            The user settings if found, None otherwise
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def get_or_create_default(self, user_id: int) -> UserSettings:
        """
        Get user settings or create default settings if not found
        
        Args:
            user_id: The user ID
            
        Returns:
            User settings (existing or newly created with defaults)
            
        Raises:
            RepositoryError: If retrieval or creation fails
        """
        pass
    
    @abstractmethod
    async def update_subscription_frequency(
        self,
        user_id: int,
        frequency: SubscriptionCheckFrequency
    ) -> bool:
        """
        Update subscription check frequency for a user
        
        Args:
            user_id: The user ID
            frequency: The new check frequency
            
        Returns:
            True if updated, False if user settings not found
            
        Raises:
            RepositoryError: If update fails
        """
        pass

