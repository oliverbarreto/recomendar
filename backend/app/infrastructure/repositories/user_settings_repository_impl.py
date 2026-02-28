"""
UserSettings repository implementation using SQLAlchemy
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
import logging

from app.domain.repositories.user_settings_repository import UserSettingsRepository
from app.domain.entities.user_settings import UserSettings
from app.domain.entities.followed_channel import SubscriptionCheckFrequency
from app.infrastructure.database.models.user_settings import UserSettingsModel
from app.infrastructure.repositories.base_repository_impl import BaseRepositoryImpl

logger = logging.getLogger(__name__)


class UserSettingsRepositoryImpl(BaseRepositoryImpl[UserSettings, UserSettingsModel], UserSettingsRepository):
    """
    SQLAlchemy implementation of UserSettingsRepository
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session, UserSettingsModel)

    def _entity_to_model(self, entity: UserSettings) -> UserSettingsModel:
        """Convert UserSettings entity to UserSettingsModel"""
        # Map domain enum to database enum
        from app.infrastructure.database.models.user_settings import SubscriptionCheckFrequency as DBFrequency

        frequency_map = {
            SubscriptionCheckFrequency.DAILY: DBFrequency.DAILY,
            SubscriptionCheckFrequency.WEEKLY: DBFrequency.WEEKLY,
        }

        db_frequency = frequency_map[entity.subscription_check_frequency]

        return UserSettingsModel(
            id=entity.id,
            user_id=entity.user_id,
            subscription_check_frequency=db_frequency,
            preferred_check_hour=entity.preferred_check_hour,
            preferred_check_minute=entity.preferred_check_minute,
            timezone=entity.timezone,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )

    def _model_to_entity(self, model: UserSettingsModel) -> UserSettings:
        """Convert UserSettingsModel to UserSettings entity"""
        # Map database enum to domain enum
        from app.infrastructure.database.models.user_settings import SubscriptionCheckFrequency as DBFrequency

        frequency_map = {
            DBFrequency.DAILY: SubscriptionCheckFrequency.DAILY,
            DBFrequency.WEEKLY: SubscriptionCheckFrequency.WEEKLY,
        }

        domain_frequency = frequency_map[model.subscription_check_frequency]

        return UserSettings(
            id=model.id,
            user_id=model.user_id,
            subscription_check_frequency=domain_frequency,
            preferred_check_hour=model.preferred_check_hour,
            preferred_check_minute=model.preferred_check_minute,
            timezone=model.timezone,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    async def get_by_user_id(self, user_id: int) -> Optional[UserSettings]:
        """Get user settings by user ID"""
        try:
            stmt = select(UserSettingsModel).where(UserSettingsModel.user_id == user_id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if model:
                return self._model_to_entity(model)
            return None
        except Exception as e:
            logger.error(f"Error getting user settings for user {user_id}: {e}")
            raise

    async def get_or_create_default(self, user_id: int) -> UserSettings:
        """Get user settings or create default settings if not found"""
        try:
            settings = await self.get_by_user_id(user_id)
            
            if settings:
                return settings
            
            # Create default settings
            default_settings = UserSettings(
                id=None,
                user_id=user_id,
                subscription_check_frequency=SubscriptionCheckFrequency.DAILY
            )
            
            return await self.create(default_settings)
        except Exception as e:
            logger.error(f"Error getting or creating default settings for user {user_id}: {e}")
            raise

    async def update_subscription_frequency(
        self,
        user_id: int,
        frequency: SubscriptionCheckFrequency
    ) -> bool:
        """Update subscription check frequency"""
        try:
            from app.infrastructure.database.models.user_settings import SubscriptionCheckFrequency as DBFrequency

            # Map domain enum to database enum
            frequency_map = {
                SubscriptionCheckFrequency.DAILY: DBFrequency.DAILY,
                SubscriptionCheckFrequency.WEEKLY: DBFrequency.WEEKLY,
            }

            stmt = select(UserSettingsModel).where(UserSettingsModel.user_id == user_id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()

            if not model:
                return False

            model.subscription_check_frequency = frequency_map[frequency]
            model.updated_at = datetime.utcnow()

            await self.session.commit()
            await self.session.refresh(model)
            return True
        except Exception as e:
            logger.error(f"Error updating subscription frequency for user {user_id}: {e}")
            await self.session.rollback()
            raise

