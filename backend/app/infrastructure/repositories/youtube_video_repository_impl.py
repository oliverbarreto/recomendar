"""
YouTubeVideo repository implementation using SQLAlchemy
"""
from sqlalchemy import select, and_, or_, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime
import logging
import json

from app.domain.repositories.youtube_video_repository import YouTubeVideoRepository
from app.domain.entities.youtube_video import YouTubeVideo, YouTubeVideoState
from app.infrastructure.database.models.youtube_video import YouTubeVideoModel
from app.infrastructure.repositories.base_repository_impl import BaseRepositoryImpl

logger = logging.getLogger(__name__)


class YouTubeVideoRepositoryImpl(BaseRepositoryImpl[YouTubeVideo, YouTubeVideoModel], YouTubeVideoRepository):
    """
    SQLAlchemy implementation of YouTubeVideoRepository
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session, YouTubeVideoModel)

    def _entity_to_model(self, entity: YouTubeVideo) -> YouTubeVideoModel:
        """Convert YouTubeVideo entity to YouTubeVideoModel"""
        return YouTubeVideoModel(
            id=entity.id,
            video_id=entity.video_id,
            followed_channel_id=entity.followed_channel_id,
            title=entity.title,
            description=entity.description,
            url=entity.url,
            thumbnail_url=entity.thumbnail_url,
            publish_date=entity.publish_date,
            duration=entity.duration,
            view_count=entity.view_count,
            like_count=entity.like_count,
            comment_count=entity.comment_count,
            metadata_json=entity.metadata_json,
            state=entity.state.value if isinstance(entity.state, YouTubeVideoState) else entity.state,
            episode_id=entity.episode_id,
            reviewed_at=entity.reviewed_at,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )

    def _model_to_entity(self, model: YouTubeVideoModel) -> YouTubeVideo:
        """Convert YouTubeVideoModel to YouTubeVideo entity"""
        # Convert state enum string to YouTubeVideoState enum
        state = YouTubeVideoState(model.state) if isinstance(model.state, str) else model.state
        
        return YouTubeVideo(
            id=model.id,
            video_id=model.video_id,
            followed_channel_id=model.followed_channel_id,
            title=model.title,
            description=model.description,
            url=model.url,
            thumbnail_url=model.thumbnail_url,
            publish_date=model.publish_date,
            duration=model.duration,
            view_count=model.view_count,
            like_count=model.like_count,
            comment_count=model.comment_count,
            metadata_json=model.metadata_json,
            state=state,
            episode_id=model.episode_id,
            reviewed_at=model.reviewed_at,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    async def get_by_video_id(self, video_id: str) -> Optional[YouTubeVideo]:
        """Get YouTube video by video ID"""
        try:
            stmt = select(YouTubeVideoModel).where(YouTubeVideoModel.video_id == video_id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if model:
                return self._model_to_entity(model)
            return None
        except Exception as e:
            logger.error(f"Error getting YouTube video by video_id {video_id}: {e}")
            raise

    async def get_by_followed_channel_id(
        self,
        followed_channel_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> List[YouTubeVideo]:
        """Get YouTube videos by followed channel ID"""
        try:
            stmt = (
                select(YouTubeVideoModel)
                .where(YouTubeVideoModel.followed_channel_id == followed_channel_id)
                .order_by(YouTubeVideoModel.publish_date.desc())
                .offset(skip)
                .limit(limit)
            )
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Error getting YouTube videos for channel {followed_channel_id}: {e}")
            raise

    async def get_by_state(
        self,
        state: YouTubeVideoState,
        user_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[YouTubeVideo]:
        """Get YouTube videos by state"""
        try:
            conditions = [YouTubeVideoModel.state == state.value]
            
            # If user_id provided, join with followed_channels to filter by user
            if user_id:
                from app.infrastructure.database.models.followed_channel import FollowedChannelModel
                stmt = (
                    select(YouTubeVideoModel)
                    .join(FollowedChannelModel, YouTubeVideoModel.followed_channel_id == FollowedChannelModel.id)
                    .where(
                        and_(
                            FollowedChannelModel.user_id == user_id,
                            YouTubeVideoModel.state == state.value
                        )
                    )
                    .order_by(YouTubeVideoModel.publish_date.desc())
                    .offset(skip)
                    .limit(limit)
                )
            else:
                stmt = (
                    select(YouTubeVideoModel)
                    .where(YouTubeVideoModel.state == state.value)
                    .order_by(YouTubeVideoModel.publish_date.desc())
                    .offset(skip)
                    .limit(limit)
                )
            
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Error getting YouTube videos by state {state.value}: {e}")
            raise

    async def get_pending_review(
        self,
        user_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[YouTubeVideo]:
        """Get videos pending review"""
        return await self.get_by_state(YouTubeVideoState.PENDING_REVIEW, user_id, skip, limit)

    async def update_state(
        self,
        youtube_video_id: int,
        state: YouTubeVideoState,
        episode_id: Optional[int] = None
    ) -> bool:
        """Update video state"""
        try:
            stmt = select(YouTubeVideoModel).where(YouTubeVideoModel.id == youtube_video_id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if not model:
                return False
            
            model.state = state.value
            if episode_id:
                model.episode_id = episode_id
            model.updated_at = datetime.utcnow()
            
            await self.session.commit()
            await self.session.refresh(model)
            return True
        except Exception as e:
            logger.error(f"Error updating state for video {youtube_video_id}: {e}")
            await self.session.rollback()
            raise

    async def mark_as_reviewed(self, youtube_video_id: int) -> bool:
        """Mark video as reviewed"""
        try:
            stmt = select(YouTubeVideoModel).where(YouTubeVideoModel.id == youtube_video_id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if not model:
                return False
            
            if model.state != YouTubeVideoState.PENDING_REVIEW.value:
                raise ValueError(f"Cannot mark as reviewed from state {model.state}")
            
            model.state = YouTubeVideoState.REVIEWED.value
            model.reviewed_at = datetime.utcnow()
            model.updated_at = datetime.utcnow()
            
            await self.session.commit()
            await self.session.refresh(model)
            return True
        except Exception as e:
            logger.error(f"Error marking video {youtube_video_id} as reviewed: {e}")
            await self.session.rollback()
            raise

    async def mark_as_discarded(self, youtube_video_id: int) -> bool:
        """Mark video as discarded"""
        try:
            stmt = select(YouTubeVideoModel).where(YouTubeVideoModel.id == youtube_video_id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if not model:
                return False
            
            if model.state in [YouTubeVideoState.EPISODE_CREATED.value, YouTubeVideoState.DISCARDED.value]:
                raise ValueError(f"Cannot discard video in state {model.state}")
            
            model.state = YouTubeVideoState.DISCARDED.value
            model.reviewed_at = datetime.utcnow()
            model.updated_at = datetime.utcnow()
            
            await self.session.commit()
            await self.session.refresh(model)
            return True
        except Exception as e:
            logger.error(f"Error marking video {youtube_video_id} as discarded: {e}")
            await self.session.rollback()
            raise

    async def search(
        self,
        query: str,
        user_id: Optional[int] = None,
        state: Optional[YouTubeVideoState] = None,
        followed_channel_id: Optional[int] = None,
        publish_year: Optional[int] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[YouTubeVideo]:
        """Search YouTube videos"""
        try:
            conditions = []
            
            # Add search condition only if query is provided
            if query:
                search_pattern = f"%{query.lower()}%"
                conditions.append(
                    or_(
                        func.lower(YouTubeVideoModel.title).like(search_pattern),
                        func.lower(YouTubeVideoModel.description).like(search_pattern)
                    )
                )
            
            if state:
                conditions.append(YouTubeVideoModel.state == state.value)
            
            if followed_channel_id:
                conditions.append(YouTubeVideoModel.followed_channel_id == followed_channel_id)
            
            if publish_year:
                # Filter by year using SQL YEAR function
                conditions.append(func.strftime('%Y', YouTubeVideoModel.publish_date) == str(publish_year))
            
            # If user_id provided, join with followed_channels
            if user_id:
                from app.infrastructure.database.models.followed_channel import FollowedChannelModel
                conditions.append(FollowedChannelModel.user_id == user_id)
                
                stmt = (
                    select(YouTubeVideoModel)
                    .join(FollowedChannelModel, YouTubeVideoModel.followed_channel_id == FollowedChannelModel.id)
                    .where(and_(*conditions))
                    .order_by(YouTubeVideoModel.publish_date.desc())
                    .offset(skip)
                    .limit(limit)
                )
            else:
                stmt = (
                    select(YouTubeVideoModel)
                    .where(and_(*conditions))
                    .order_by(YouTubeVideoModel.publish_date.desc())
                    .offset(skip)
                    .limit(limit)
                )
            
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Error searching YouTube videos with query '{query}': {e}")
            raise

    async def get_count_by_state(
        self,
        state: YouTubeVideoState,
        user_id: Optional[int] = None
    ) -> int:
        """Get count of videos by state"""
        try:
            conditions = [YouTubeVideoModel.state == state.value]
            
            if user_id:
                from app.infrastructure.database.models.followed_channel import FollowedChannelModel
                stmt = (
                    select(func.count(YouTubeVideoModel.id))
                    .join(FollowedChannelModel, YouTubeVideoModel.followed_channel_id == FollowedChannelModel.id)
                    .where(
                        and_(
                            FollowedChannelModel.user_id == user_id,
                            YouTubeVideoModel.state == state.value
                        )
                    )
                )
            else:
                stmt = select(func.count(YouTubeVideoModel.id)).where(
                    YouTubeVideoModel.state == state.value
                )
            
            result = await self.session.execute(stmt)
            count = result.scalar()
            return count if count is not None else 0
        except Exception as e:
            logger.error(f"Error getting count by state {state.value}: {e}")
            raise

    async def get_videos_by_date_range(
        self,
        followed_channel_id: int,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 50
    ) -> List[YouTubeVideo]:
        """Get videos published within a date range"""
        try:
            stmt = (
                select(YouTubeVideoModel)
                .where(
                    and_(
                        YouTubeVideoModel.followed_channel_id == followed_channel_id,
                        YouTubeVideoModel.publish_date >= start_date,
                        YouTubeVideoModel.publish_date <= end_date
                    )
                )
                .order_by(YouTubeVideoModel.publish_date.desc())
                .offset(skip)
                .limit(limit)
            )
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Error getting videos by date range for channel {followed_channel_id}: {e}")
            raise

    async def video_id_exists(self, video_id: str) -> bool:
        """Check if a video ID already exists"""
        try:
            stmt = select(func.count(YouTubeVideoModel.id)).where(
                YouTubeVideoModel.video_id == video_id
            )
            result = await self.session.execute(stmt)
            count = result.scalar()
            return (count or 0) > 0
        except Exception as e:
            logger.error(f"Error checking if video_id exists {video_id}: {e}")
            raise

    async def delete_pending_videos_for_channel(
        self,
        followed_channel_id: int
    ) -> int:
        """Delete all pending/reviewed videos for a followed channel"""
        try:
            # Delete videos in pending_review, reviewed, queued, downloading, or discarded states
            # Keep videos in episode_created state
            states_to_delete = [
                YouTubeVideoState.PENDING_REVIEW.value,
                YouTubeVideoState.REVIEWED.value,
                YouTubeVideoState.QUEUED.value,
                YouTubeVideoState.DOWNLOADING.value,
                YouTubeVideoState.DISCARDED.value
            ]
            
            stmt = delete(YouTubeVideoModel).where(
                and_(
                    YouTubeVideoModel.followed_channel_id == followed_channel_id,
                    YouTubeVideoModel.state.in_(states_to_delete)
                )
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            return result.rowcount
        except Exception as e:
            logger.error(f"Error deleting pending videos for channel {followed_channel_id}: {e}")
            await self.session.rollback()
            raise

    async def get_by_followed_channel_and_state(
        self,
        followed_channel_id: int,
        state: YouTubeVideoState,
        skip: int = 0,
        limit: int = 1000
    ) -> List[YouTubeVideo]:
        """
        Get YouTube videos by followed channel ID and state
        
        Args:
            followed_channel_id: ID of the followed channel
            state: Video state to filter by
            skip: Number of results to skip
            limit: Maximum number of results to return
            
        Returns:
            List of YouTube videos matching the criteria
        """
        try:
            stmt = (
                select(YouTubeVideoModel)
                .where(
                    and_(
                        YouTubeVideoModel.followed_channel_id == followed_channel_id,
                        YouTubeVideoModel.state == state.value
                    )
                )
                .order_by(YouTubeVideoModel.publish_date.desc())
                .offset(skip)
                .limit(limit)
            )
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(
                f"Error getting YouTube videos for channel {followed_channel_id} "
                f"with state {state.value}: {e}"
            )
            raise

    async def get_stats_by_followed_channel(
        self,
        followed_channel_id: int
    ) -> dict:
        """
        Get video statistics for a specific followed channel
        
        Args:
            followed_channel_id: ID of the followed channel
            
        Returns:
            Dictionary with counts for each state
        """
        try:
            stats = {
                "pending_review": 0,
                "reviewed": 0,
                "queued": 0,
                "downloading": 0,
                "episode_created": 0,
                "discarded": 0,
                "total": 0
            }
            
            # Get counts for each state
            for state in YouTubeVideoState:
                stmt = (
                    select(func.count(YouTubeVideoModel.id))
                    .where(
                        and_(
                            YouTubeVideoModel.followed_channel_id == followed_channel_id,
                            YouTubeVideoModel.state == state.value
                        )
                    )
                )
                result = await self.session.execute(stmt)
                count = result.scalar() or 0
                stats[state.value] = count
                stats["total"] += count
            
            return stats
        except Exception as e:
            logger.error(
                f"Error getting stats for followed channel {followed_channel_id}: {e}"
            )
            raise


