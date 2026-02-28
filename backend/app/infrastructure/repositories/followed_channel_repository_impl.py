"""
FollowedChannel repository implementation using SQLAlchemy
"""
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime, timedelta
import logging

from app.domain.repositories.followed_channel_repository import FollowedChannelRepository
from app.domain.entities.followed_channel import FollowedChannel
from app.infrastructure.database.models.followed_channel import FollowedChannelModel
from app.infrastructure.repositories.base_repository_impl import BaseRepositoryImpl

logger = logging.getLogger(__name__)


class FollowedChannelRepositoryImpl(BaseRepositoryImpl[FollowedChannel, FollowedChannelModel], FollowedChannelRepository):
    """
    SQLAlchemy implementation of FollowedChannelRepository
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session, FollowedChannelModel)

    def _entity_to_model(self, entity: FollowedChannel) -> FollowedChannelModel:
        """Convert FollowedChannel entity to FollowedChannelModel"""
        return FollowedChannelModel(
            id=entity.id,
            user_id=entity.user_id,
            youtube_channel_id=entity.youtube_channel_id,
            youtube_channel_name=entity.youtube_channel_name,
            youtube_channel_url=entity.youtube_channel_url,
            thumbnail_url=entity.thumbnail_url,
            youtube_channel_description=entity.youtube_channel_description,
            auto_approve=entity.auto_approve,
            auto_approve_channel_id=entity.auto_approve_channel_id,
            last_checked=entity.last_checked,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )

    def _model_to_entity(self, model: FollowedChannelModel) -> FollowedChannel:
        """Convert FollowedChannelModel to FollowedChannel entity"""
        return FollowedChannel(
            id=model.id,
            user_id=model.user_id,
            youtube_channel_id=model.youtube_channel_id,
            youtube_channel_name=model.youtube_channel_name,
            youtube_channel_url=model.youtube_channel_url,
            thumbnail_url=model.thumbnail_url,
            youtube_channel_description=model.youtube_channel_description,
            auto_approve=model.auto_approve,
            auto_approve_channel_id=model.auto_approve_channel_id,
            last_checked=model.last_checked,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    async def get_by_user_id(self, user_id: int) -> List[FollowedChannel]:
        """Get all followed channels for a user"""
        try:
            stmt = select(FollowedChannelModel).where(
                FollowedChannelModel.user_id == user_id
            ).order_by(FollowedChannelModel.created_at.desc())
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Error getting followed channels for user {user_id}: {e}")
            raise

    async def get_by_youtube_channel_id(
        self,
        youtube_channel_id: str,
        user_id: Optional[int] = None
    ) -> Optional[FollowedChannel]:
        """Get followed channel by YouTube channel ID"""
        try:
            conditions = [FollowedChannelModel.youtube_channel_id == youtube_channel_id]
            if user_id:
                conditions.append(FollowedChannelModel.user_id == user_id)
            
            stmt = select(FollowedChannelModel).where(and_(*conditions))
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if model:
                return self._model_to_entity(model)
            return None
        except Exception as e:
            logger.error(f"Error getting followed channel by YouTube ID {youtube_channel_id}: {e}")
            raise

    async def get_by_user_and_youtube_channel_id(
        self,
        user_id: int,
        youtube_channel_id: str
    ) -> Optional[FollowedChannel]:
        """Get followed channel by user ID and YouTube channel ID"""
        try:
            stmt = select(FollowedChannelModel).where(
                and_(
                    FollowedChannelModel.user_id == user_id,
                    FollowedChannelModel.youtube_channel_id == youtube_channel_id
                )
            )
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if model:
                return self._model_to_entity(model)
            return None
        except Exception as e:
            logger.error(f"Error getting followed channel by user {user_id} and YouTube ID {youtube_channel_id}: {e}")
            raise

    async def get_channels_to_check(
        self,
        user_frequency: str,
        last_check_before: Optional[datetime] = None
    ) -> List[FollowedChannel]:
        """Get followed channels that need to be checked"""
        try:
            # Calculate threshold date based on frequency
            now = datetime.utcnow()
            if user_frequency == "daily":
                threshold = now - timedelta(days=1)
            elif user_frequency == "twice_weekly":
                threshold = now - timedelta(days=3.5)
            elif user_frequency == "weekly":
                threshold = now - timedelta(days=7)
            else:
                threshold = now - timedelta(days=1)  # Default to daily
            
            # Use provided threshold if given, otherwise use calculated one
            check_threshold = last_check_before or threshold
            
            # Get channels that haven't been checked or were checked before threshold
            stmt = select(FollowedChannelModel).where(
                or_(
                    FollowedChannelModel.last_checked.is_(None),
                    FollowedChannelModel.last_checked < check_threshold
                )
            )
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Error getting channels to check for frequency {user_frequency}: {e}")
            raise

    async def update_last_checked(
        self,
        followed_channel_id: int,
        last_checked: Optional[datetime] = None
    ) -> bool:
        """Update the last checked timestamp"""
        try:
            stmt = select(FollowedChannelModel).where(FollowedChannelModel.id == followed_channel_id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if not model:
                return False
            
            model.last_checked = last_checked or datetime.utcnow()
            model.updated_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(model)
            return True
        except Exception as e:
            logger.error(f"Error updating last checked for channel {followed_channel_id}: {e}")
            await self.session.rollback()
            raise

    async def update_auto_approve_settings(
        self,
        followed_channel_id: int,
        auto_approve: bool,
        auto_approve_channel_id: Optional[int] = None
    ) -> bool:
        """Update auto-approve settings"""
        try:
            stmt = select(FollowedChannelModel).where(FollowedChannelModel.id == followed_channel_id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if not model:
                return False
            
            if auto_approve and not auto_approve_channel_id:
                raise ValueError("auto_approve_channel_id is required when enabling auto_approve")
            
            model.auto_approve = auto_approve
            model.auto_approve_channel_id = auto_approve_channel_id if auto_approve else None
            model.updated_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(model)
            return True
        except Exception as e:
            logger.error(f"Error updating auto-approve settings for channel {followed_channel_id}: {e}")
            await self.session.rollback()
            raise







