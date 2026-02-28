"""
Channel repository implementation using SQLAlchemy
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import logging

from app.domain.repositories.channel import ChannelRepository
from app.domain.entities.channel import Channel
from app.domain.value_objects.email import Email
from app.infrastructure.database.models.channel import ChannelModel
from app.infrastructure.repositories.base_repository_impl import BaseRepositoryImpl

logger = logging.getLogger(__name__)


class ChannelRepositoryImpl(BaseRepositoryImpl[Channel, ChannelModel], ChannelRepository):
    """
    SQLAlchemy implementation of ChannelRepository
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session, ChannelModel)

    def _entity_to_model(self, entity: Channel) -> ChannelModel:
        """Convert Channel entity to ChannelModel"""
        return ChannelModel(
            id=entity.id,
            user_id=entity.user_id,
            name=entity.name,
            description=entity.description,
            website_url=entity.website_url,
            image_url=entity.image_url,
            category=entity.category,
            language=entity.language,
            explicit_content=entity.explicit_content,
            author_name=entity.author_name,
            author_email=entity.author_email.value if entity.author_email else None,
            owner_name=entity.owner_name,
            owner_email=entity.owner_email.value if entity.owner_email else None,
            feed_url=entity.feed_url,
            feed_last_updated=entity.feed_last_updated,
            feed_validation_score=entity.feed_validation_score,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )

    def _model_to_entity(self, model: ChannelModel) -> Channel:
        """Convert ChannelModel to Channel entity"""
        return Channel(
            id=model.id,
            user_id=model.user_id,
            name=model.name,
            description=model.description,
            website_url=model.website_url,
            image_url=model.image_url,
            category=model.category,
            language=model.language,
            explicit_content=model.explicit_content,
            author_name=model.author_name,
            author_email=Email.create_optional(model.author_email),
            owner_name=model.owner_name,
            owner_email=Email.create_optional(model.owner_email),
            feed_url=model.feed_url,
            feed_last_updated=model.feed_last_updated,
            feed_validation_score=model.feed_validation_score,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    async def find_by_user_id(self, user_id: int) -> Optional[Channel]:
        """Find first channel by user ID (returns first if multiple exist)"""
        try:
            stmt = select(ChannelModel).where(ChannelModel.user_id == user_id).order_by(ChannelModel.id)
            result = await self.session.execute(stmt)
            model = result.scalars().first()  # Get first channel if multiple exist

            if model:
                return self._model_to_entity(model)
            return None

        except Exception as e:
            logger.error(f"Error finding channel by user_id {user_id}: {e}")
            raise

    async def update_feed_url(self, channel_id: int, feed_url: str) -> bool:
        """Update the RSS feed URL for a channel"""
        try:
            stmt = select(ChannelModel).where(ChannelModel.id == channel_id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()

            if model:
                model.feed_url = feed_url
                await self.session.commit()
                return True
            return False

        except Exception as e:
            logger.error(f"Error updating feed URL for channel {channel_id}: {e}")
            await self.session.rollback()
            raise

    async def find_by_name(self, name: str) -> List[Channel]:
        """Find channels by name (partial match, case-insensitive)"""
        try:
            stmt = select(ChannelModel).where(
                ChannelModel.name.ilike(f"%{name}%")
            )
            result = await self.session.execute(stmt)
            models = result.scalars().all()

            return [self._model_to_entity(model) for model in models]

        except Exception as e:
            logger.error(f"Error finding channels by name {name}: {e}")
            raise

    async def get_channels_by_category(self, category: str) -> List[Channel]:
        """Get all channels in a specific category"""
        try:
            stmt = select(ChannelModel).where(ChannelModel.category == category)
            result = await self.session.execute(stmt)
            models = result.scalars().all()

            return [self._model_to_entity(model) for model in models]

        except Exception as e:
            logger.error(f"Error getting channels by category {category}: {e}")
            raise

    async def get_channels_by_language(self, language: str) -> List[Channel]:
        """Get all channels in a specific language"""
        try:
            stmt = select(ChannelModel).where(ChannelModel.language == language)
            result = await self.session.execute(stmt)
            models = result.scalars().all()

            return [self._model_to_entity(model) for model in models]

        except Exception as e:
            logger.error(f"Error getting channels by language {language}: {e}")
            raise

    async def update_metadata(self, channel_id: int, **kwargs) -> bool:
        """Update channel metadata fields"""
        try:
            stmt = select(ChannelModel).where(ChannelModel.id == channel_id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()

            if model:
                for key, value in kwargs.items():
                    if hasattr(model, key):
                        setattr(model, key, value)

                await self.session.commit()
                return True
            return False

        except Exception as e:
            logger.error(f"Error updating metadata for channel {channel_id}: {e}")
            await self.session.rollback()
            raise

    async def channel_name_exists(self, name: str, exclude_channel_id: Optional[int] = None) -> bool:
        """Check if a channel name already exists"""
        try:
            stmt = select(ChannelModel).where(ChannelModel.name == name)

            if exclude_channel_id:
                stmt = stmt.where(ChannelModel.id != exclude_channel_id)

            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()

            return model is not None

        except Exception as e:
            logger.error(f"Error checking if channel name exists {name}: {e}")
            raise