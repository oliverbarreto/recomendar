"""
Episode repository implementation using SQLAlchemy
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_, desc, asc
from sqlalchemy.orm import selectinload

from app.domain.repositories.episode import EpisodeRepository
from app.domain.entities.episode import Episode, EpisodeStatus
from app.domain.entities.tag import Tag
from app.domain.value_objects.video_id import VideoId
from app.domain.value_objects.duration import Duration
from app.infrastructure.database.models.episode import EpisodeModel


class EpisodeRepositoryImpl(EpisodeRepository):
    """
    SQLAlchemy implementation of Episode repository
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
    
    def _model_to_entity(self, model: EpisodeModel) -> Episode:
        """Convert SQLAlchemy model to domain entity"""
        if not model:
            return None
        
        duration = None
        if model.duration_seconds:
            duration = Duration(model.duration_seconds)

        # Convert tag models to tag entities (only if tags were loaded)
        tags = []
        try:
            if hasattr(model, 'tags') and model.tags is not None:
                for tag_model in model.tags:
                    tags.append(Tag(
                        id=tag_model.id,
                        channel_id=tag_model.channel_id,
                        name=tag_model.name,
                        color=tag_model.color,
                        usage_count=tag_model.usage_count or 0,
                        is_system_tag=tag_model.is_system_tag or False,
                        last_used_at=tag_model.last_used_at,
                        created_at=tag_model.created_at,
                        updated_at=tag_model.updated_at
                    ))
        except Exception:
            # If we can't load tags (e.g., not eagerly loaded), just use empty list
            tags = []

        return Episode(
            id=model.id,
            channel_id=model.channel_id,
            video_id=VideoId(model.video_id),
            title=model.title,
            description=model.description or "",
            publication_date=model.publication_date,
            audio_file_path=model.audio_file_path,
            video_url=model.video_url or "",
            thumbnail_url=model.thumbnail_url or "",
            duration=duration,
            keywords=model.keywords or [],
            tags=tags,
            status=EpisodeStatus(model.status),
            retry_count=model.retry_count or 0,
            download_date=model.download_date,
            created_at=model.created_at,
            updated_at=model.updated_at,
            # YouTube channel information
            youtube_channel=model.youtube_channel,
            youtube_channel_id=model.youtube_channel_id,
            youtube_channel_url=model.youtube_channel_url,
            # User preferences
            is_favorited=model.is_favorited or False,
            # Media file information
            media_file_size=model.media_file_size or 0,
            # Upload source tracking
            source_type=model.source_type or "youtube",
            original_filename=model.original_filename,
            # Audio language and quality preferences
            audio_language=model.audio_language,
            audio_quality=model.audio_quality,
            requested_language=model.requested_language,
            requested_quality=model.requested_quality
        )
    
    def _entity_to_model(self, entity: Episode, model: Optional[EpisodeModel] = None) -> EpisodeModel:
        """Convert domain entity to SQLAlchemy model"""
        if model is None:
            model = EpisodeModel()
        
        model.channel_id = entity.channel_id
        model.video_id = entity.video_id.value
        model.title = entity.title
        model.description = entity.description
        model.publication_date = entity.publication_date
        model.audio_file_path = entity.audio_file_path
        model.video_url = entity.video_url
        model.thumbnail_url = entity.thumbnail_url
        model.duration_seconds = entity.duration.seconds if entity.duration else None
        model.keywords = entity.keywords
        model.status = entity.status.value
        model.retry_count = entity.retry_count
        model.download_date = entity.download_date
        model.updated_at = entity.updated_at
        # YouTube channel information
        model.youtube_channel = entity.youtube_channel
        model.youtube_channel_id = entity.youtube_channel_id
        model.youtube_channel_url = entity.youtube_channel_url
        # User preferences
        model.is_favorited = entity.is_favorited
        # Media file information
        model.media_file_size = entity.media_file_size
        # Upload source tracking
        model.source_type = entity.source_type
        model.original_filename = entity.original_filename
        # Audio language and quality preferences
        model.audio_language = entity.audio_language
        model.audio_quality = entity.audio_quality
        model.requested_language = entity.requested_language
        model.requested_quality = entity.requested_quality

        if entity.id is not None:
            model.id = entity.id
        if entity.created_at is not None:
            model.created_at = entity.created_at
        
        return model
    
    async def create(self, entity: Episode) -> Episode:
        """Create a new episode"""
        model = self._entity_to_model(entity)
        self.db_session.add(model)
        await self.db_session.flush()
        await self.db_session.refresh(model)
        return self._model_to_entity(model)
    
    async def get_by_id(self, entity_id: int) -> Optional[Episode]:
        """Get episode by ID"""
        stmt = select(EpisodeModel).options(selectinload(EpisodeModel.tags)).where(EpisodeModel.id == entity_id)
        result = await self.db_session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Episode]:
        """Get all episodes with pagination"""
        stmt = (
            select(EpisodeModel)
            .offset(skip)
            .limit(limit)
            .order_by(desc(EpisodeModel.created_at))
        )
        result = await self.db_session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]
    
    async def update(self, entity: Episode) -> Episode:
        """Update an existing episode"""
        if entity.id is None:
            raise ValueError("Episode ID is required for update")
        
        stmt = select(EpisodeModel).where(EpisodeModel.id == entity.id)
        result = await self.db_session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            raise ValueError(f"Episode with ID {entity.id} not found")
        
        updated_model = self._entity_to_model(entity, model)
        await self.db_session.flush()
        await self.db_session.refresh(updated_model)
        return self._model_to_entity(updated_model)
    
    async def delete(self, entity_id: int) -> bool:
        """Delete episode by ID"""
        stmt = delete(EpisodeModel).where(EpisodeModel.id == entity_id)
        result = await self.db_session.execute(stmt)
        return result.rowcount > 0
    
    async def exists(self, entity_id: int) -> bool:
        """Check if episode exists"""
        stmt = select(func.count(EpisodeModel.id)).where(EpisodeModel.id == entity_id)
        result = await self.db_session.execute(stmt)
        count = result.scalar()
        return count > 0
    
    async def find_by_video_id(self, video_id: VideoId) -> Optional[Episode]:
        """Find episode by video ID"""
        stmt = select(EpisodeModel).where(EpisodeModel.video_id == video_id.value)
        result = await self.db_session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def find_by_video_id_and_channel(self, video_id: VideoId, channel_id: int) -> Optional[Episode]:
        """
        Find episode by video ID and channel ID

        This method provides channel-scoped lookups, which is more appropriate
        when serving media files where the same video_id should be unique per channel.

        Args:
            video_id: The YouTube video ID
            channel_id: The channel ID for scoping

        Returns:
            The episode if found, None otherwise
        """
        stmt = select(EpisodeModel).options(selectinload(EpisodeModel.tags)).where(
            and_(
                EpisodeModel.video_id == video_id.value,
                EpisodeModel.channel_id == channel_id
            )
        )
        result = await self.db_session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None
    
    async def find_by_channel(self, channel_id: int, skip: int = 0, limit: int = 50) -> List[Episode]:
        """Find episodes by channel"""
        stmt = (
            select(EpisodeModel)
            .where(EpisodeModel.channel_id == channel_id)
            .offset(skip)
            .limit(limit)
            .order_by(desc(EpisodeModel.publication_date))
        )
        result = await self.db_session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]
    
    async def find_by_status(self, status: EpisodeStatus) -> List[Episode]:
        """Find episodes by status"""
        stmt = (
            select(EpisodeModel)
            .where(EpisodeModel.status == status.value)
            .order_by(asc(EpisodeModel.created_at))
        )
        result = await self.db_session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]
    
    async def search(self, query: str, channel_id: int, skip: int = 0, limit: int = 50) -> List[Episode]:
        """Search episodes by title, description, or keywords"""
        search_term = f"%{query}%"
        stmt = (
            select(EpisodeModel)
            .where(
                and_(
                    EpisodeModel.channel_id == channel_id,
                    or_(
                        EpisodeModel.title.ilike(search_term),
                        EpisodeModel.description.ilike(search_term),
                        EpisodeModel.keywords.contains([query])
                    )
                )
            )
            .offset(skip)
            .limit(limit)
            .order_by(desc(EpisodeModel.publication_date))
        )
        result = await self.db_session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]
    
    async def update_status(self, episode_id: int, status: EpisodeStatus) -> bool:
        """Update episode status"""
        stmt = (
            update(EpisodeModel)
            .where(EpisodeModel.id == episode_id)
            .values(
                status=status.value,
                updated_at=datetime.utcnow()
            )
        )
        result = await self.db_session.execute(stmt)
        return result.rowcount > 0
    
    async def increment_retry_count(self, episode_id: int) -> bool:
        """Increment retry count"""
        stmt = (
            update(EpisodeModel)
            .where(EpisodeModel.id == episode_id)
            .values(
                retry_count=EpisodeModel.retry_count + 1,
                updated_at=datetime.utcnow()
            )
        )
        result = await self.db_session.execute(stmt)
        return result.rowcount > 0
    
    async def get_failed_episodes(self, max_retries: int = 3) -> List[Episode]:
        """Get failed episodes eligible for retry"""
        stmt = (
            select(EpisodeModel)
            .where(
                and_(
                    EpisodeModel.status == EpisodeStatus.FAILED.value,
                    EpisodeModel.retry_count < max_retries
                )
            )
            .order_by(asc(EpisodeModel.updated_at))
        )
        result = await self.db_session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]
    
    async def get_episodes_by_date_range(
        self,
        channel_id: int,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 50
    ) -> List[Episode]:
        """Get episodes by date range"""
        stmt = (
            select(EpisodeModel)
            .where(
                and_(
                    EpisodeModel.channel_id == channel_id,
                    EpisodeModel.publication_date >= start_date,
                    EpisodeModel.publication_date <= end_date
                )
            )
            .offset(skip)
            .limit(limit)
            .order_by(desc(EpisodeModel.publication_date))
        )
        result = await self.db_session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]
    
    async def video_id_exists(self, video_id: VideoId, channel_id: int) -> bool:
        """Check if video ID exists for channel"""
        stmt = select(func.count(EpisodeModel.id)).where(
            and_(
                EpisodeModel.video_id == video_id.value,
                EpisodeModel.channel_id == channel_id
            )
        )
        result = await self.db_session.execute(stmt)
        count = result.scalar()
        return count > 0
    
    async def bulk_update_status(self, episode_ids: List[int], status: EpisodeStatus) -> int:
        """Bulk update episode status"""
        stmt = (
            update(EpisodeModel)
            .where(EpisodeModel.id.in_(episode_ids))
            .values(
                status=status.value,
                updated_at=datetime.utcnow()
            )
        )
        result = await self.db_session.execute(stmt)
        return result.rowcount
    
    async def get_by_filters(
        self,
        filters: Dict[str, Any],
        skip: int = 0,
        limit: int = 50,
        order_by: str = "created_at",
        order_desc: bool = True
    ) -> List[Episode]:
        """Get episodes with flexible filtering"""
        # Load tags along with episodes (greenlet issues have been resolved)
        stmt = select(EpisodeModel).options(selectinload(EpisodeModel.tags))

        # Apply filters
        conditions = []

        if "channel_id" in filters:
            conditions.append(EpisodeModel.channel_id == filters["channel_id"])

        if "status" in filters:
            if isinstance(filters["status"], EpisodeStatus):
                conditions.append(EpisodeModel.status == filters["status"].value)
            else:
                conditions.append(EpisodeModel.status == filters["status"])

        if "search" in filters and filters["search"]:
            search_term = f"%{filters['search']}%"
            conditions.append(
                or_(
                    EpisodeModel.title.ilike(search_term),
                    EpisodeModel.description.ilike(search_term)
                )
            )

        if "is_favorited" in filters:
            conditions.append(EpisodeModel.is_favorited == filters["is_favorited"])
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        # Apply ordering
        order_column = getattr(EpisodeModel, order_by, EpisodeModel.created_at)
        if order_desc:
            stmt = stmt.order_by(desc(order_column))
        else:
            stmt = stmt.order_by(asc(order_column))
        
        # Apply pagination
        stmt = stmt.offset(skip).limit(limit)
        
        result = await self.db_session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]
    
    async def count_by_filters(self, filters: Dict[str, Any]) -> int:
        """Count episodes with filters"""
        stmt = select(func.count(EpisodeModel.id))

        # Apply filters
        conditions = []

        if "channel_id" in filters:
            conditions.append(EpisodeModel.channel_id == filters["channel_id"])

        if "status" in filters:
            if isinstance(filters["status"], EpisodeStatus):
                conditions.append(EpisodeModel.status == filters["status"].value)
            else:
                conditions.append(EpisodeModel.status == filters["status"])

        if "search" in filters and filters["search"]:
            search_term = f"%{filters['search']}%"
            conditions.append(
                or_(
                    EpisodeModel.title.ilike(search_term),
                    EpisodeModel.description.ilike(search_term)
                )
            )

        if "is_favorited" in filters:
            conditions.append(EpisodeModel.is_favorited == filters["is_favorited"])
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        result = await self.db_session.execute(stmt)
        return result.scalar() or 0
    
    async def get_by_video_id_and_channel(self, video_id: VideoId, channel_id: int) -> Optional[Episode]:
        """Get episode by video ID and channel"""
        stmt = select(EpisodeModel).where(
            and_(
                EpisodeModel.video_id == video_id.value,
                EpisodeModel.channel_id == channel_id
            )
        )
        result = await self.db_session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None
    
    async def get_episodes_before_date(self, channel_id: int, cutoff_date: datetime) -> List[Episode]:
        """Get episodes created before specified date"""
        stmt = (
            select(EpisodeModel)
            .where(
                and_(
                    EpisodeModel.channel_id == channel_id,
                    EpisodeModel.created_at < cutoff_date
                )
            )
            .order_by(asc(EpisodeModel.created_at))
        )
        result = await self.db_session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]
    async def update_episode_tags(self, episode_id: int, tag_ids: List[int]) -> bool:
        """Update episode tags by replacing all tags with the provided list"""
        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Updating tags for episode {episode_id} with tag_ids: {tag_ids}")

            # Get the episode WITHOUT loading tags (to avoid greenlet issues)
            stmt = select(EpisodeModel).where(EpisodeModel.id == episode_id)
            result = await self.db_session.execute(stmt)
            episode_model = result.scalar_one_or_none()

            if not episode_model:
                logger.error(f"Episode {episode_id} not found")
                return False

            # Clear existing tags first by deleting from episode_tags table
            from app.infrastructure.database.models.tag import TagModel
            from sqlalchemy import text

            # Clear existing relationships
            clear_sql = text("DELETE FROM episode_tags WHERE episode_id = :episode_id")
            await self.db_session.execute(clear_sql, {"episode_id": episode_id})
            logger.info(f"Cleared existing tags for episode {episode_id}")

            # Add new tag relationships if any
            if tag_ids:
                # Insert new relationships
                for tag_id in tag_ids:
                    insert_sql = text("INSERT INTO episode_tags (episode_id, tag_id) VALUES (:episode_id, :tag_id)")
                    await self.db_session.execute(insert_sql, {"episode_id": episode_id, "tag_id": tag_id})
                logger.info(f"Added {len(tag_ids)} new tags for episode {episode_id}")

            # Update the updated_at timestamp
            episode_model.updated_at = datetime.utcnow()

            # Don't commit here - let the calling service handle the transaction
            await self.db_session.flush()
            logger.info(f"Successfully updated tags for episode {episode_id}")
            return True

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error updating episode tags for episode {episode_id}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Don't rollback here - let the calling service handle it
            return False

