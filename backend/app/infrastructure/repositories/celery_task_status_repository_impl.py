"""
Celery Task Status repository implementation using SQLAlchemy
"""
from sqlalchemy import select, and_, desc, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

from app.domain.entities.celery_task_status import CeleryTaskStatus, TaskStatus
from app.infrastructure.database.models.celery_task_status import CeleryTaskStatusModel

logger = logging.getLogger(__name__)


class CeleryTaskStatusRepository:
    """
    SQLAlchemy implementation of Celery Task Status repository
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    def _entity_to_model(self, entity: CeleryTaskStatus) -> CeleryTaskStatusModel:
        """Convert CeleryTaskStatus entity to CeleryTaskStatusModel"""
        return CeleryTaskStatusModel(
            id=entity.id,
            task_id=entity.task_id,
            task_name=entity.task_name,
            status=entity.status.value if isinstance(entity.status, TaskStatus) else entity.status,
            progress=entity.progress,
            current_step=entity.current_step,
            result_json=entity.result_json,
            error_message=entity.error_message,
            followed_channel_id=entity.followed_channel_id,
            youtube_video_id=entity.youtube_video_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            started_at=entity.started_at,
            completed_at=entity.completed_at
        )
    
    def _model_to_entity(self, model: CeleryTaskStatusModel) -> CeleryTaskStatus:
        """Convert CeleryTaskStatusModel to CeleryTaskStatus entity"""
        status = TaskStatus(model.status) if isinstance(model.status, str) else model.status
        
        return CeleryTaskStatus(
            id=model.id,
            task_id=model.task_id,
            task_name=model.task_name,
            status=status,
            progress=model.progress,
            current_step=model.current_step,
            result_json=model.result_json,
            error_message=model.error_message,
            followed_channel_id=model.followed_channel_id,
            youtube_video_id=model.youtube_video_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            started_at=model.started_at,
            completed_at=model.completed_at
        )
    
    async def create(self, entity: CeleryTaskStatus) -> CeleryTaskStatus:
        """Create a new task status record"""
        try:
            model = self._entity_to_model(entity)
            self.session.add(model)
            await self.session.commit()
            await self.session.refresh(model)
            return self._model_to_entity(model)
        except Exception as e:
            logger.error(f"Error creating task status: {e}")
            await self.session.rollback()
            raise
    
    async def update(self, entity: CeleryTaskStatus) -> CeleryTaskStatus:
        """Update an existing task status record"""
        try:
            stmt = select(CeleryTaskStatusModel).where(CeleryTaskStatusModel.id == entity.id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if not model:
                raise ValueError(f"Task status {entity.id} not found")
            
            # Update fields
            model.status = entity.status.value if isinstance(entity.status, TaskStatus) else entity.status
            model.progress = entity.progress
            model.current_step = entity.current_step
            model.result_json = entity.result_json
            model.error_message = entity.error_message
            model.updated_at = datetime.utcnow()
            model.started_at = entity.started_at
            model.completed_at = entity.completed_at
            
            await self.session.commit()
            await self.session.refresh(model)
            return self._model_to_entity(model)
        except Exception as e:
            logger.error(f"Error updating task status {entity.id}: {e}")
            await self.session.rollback()
            raise
    
    async def get_by_task_id(self, task_id: str) -> Optional[CeleryTaskStatus]:
        """Get task status by Celery task ID"""
        try:
            stmt = select(CeleryTaskStatusModel).where(CeleryTaskStatusModel.task_id == task_id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if model:
                return self._model_to_entity(model)
            return None
        except Exception as e:
            logger.error(f"Error getting task status by task_id {task_id}: {e}")
            raise
    
    async def get_by_followed_channel_id(
        self,
        followed_channel_id: int,
        limit: int = 10
    ) -> List[CeleryTaskStatus]:
        """Get task statuses for a followed channel (most recent first)"""
        try:
            stmt = (
                select(CeleryTaskStatusModel)
                .where(CeleryTaskStatusModel.followed_channel_id == followed_channel_id)
                .order_by(desc(CeleryTaskStatusModel.created_at))
                .limit(limit)
            )
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Error getting task statuses for channel {followed_channel_id}: {e}")
            raise
    
    async def get_latest_by_followed_channel_id(
        self,
        followed_channel_id: int
    ) -> Optional[CeleryTaskStatus]:
        """Get the most recent task status for a followed channel"""
        try:
            stmt = (
                select(CeleryTaskStatusModel)
                .where(CeleryTaskStatusModel.followed_channel_id == followed_channel_id)
                .order_by(desc(CeleryTaskStatusModel.created_at))
                .limit(1)
            )
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()

            if model:
                return self._model_to_entity(model)
            return None
        except Exception as e:
            logger.error(f"Error getting latest task status for channel {followed_channel_id}: {e}")
            raise

    async def get_all(self, limit: Optional[int] = None) -> List[CeleryTaskStatus]:
        """Get all task statuses (most recent first)"""
        try:
            stmt = select(CeleryTaskStatusModel).order_by(desc(CeleryTaskStatusModel.created_at))
            if limit:
                stmt = stmt.limit(limit)

            result = await self.session.execute(stmt)
            models = result.scalars().all()
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Error getting all task statuses: {e}")
            raise

    async def get_by_status(self, status: TaskStatus, limit: Optional[int] = None) -> List[CeleryTaskStatus]:
        """Get task statuses by status (most recent first)"""
        try:
            stmt = (
                select(CeleryTaskStatusModel)
                .where(CeleryTaskStatusModel.status == status.value)
                .order_by(desc(CeleryTaskStatusModel.created_at))
            )
            if limit:
                stmt = stmt.limit(limit)

            result = await self.session.execute(stmt)
            models = result.scalars().all()
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Error getting task statuses by status {status}: {e}")
            raise

    async def get_by_status_and_age(
        self,
        status: TaskStatus,
        older_than_minutes: int
    ) -> List[CeleryTaskStatus]:
        """Get task statuses by status that are older than specified minutes"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(minutes=older_than_minutes)
            stmt = (
                select(CeleryTaskStatusModel)
                .where(
                    and_(
                        CeleryTaskStatusModel.status == status.value,
                        CeleryTaskStatusModel.created_at < cutoff_time
                    )
                )
                .order_by(desc(CeleryTaskStatusModel.created_at))
            )
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Error getting task statuses by status {status} and age: {e}")
            raise

    async def get_summary(self) -> Dict[str, Any]:
        """Get summary of task statuses grouped by status"""
        try:
            stmt = (
                select(
                    CeleryTaskStatusModel.status,
                    func.count(CeleryTaskStatusModel.id).label('count')
                )
                .group_by(CeleryTaskStatusModel.status)
            )
            result = await self.session.execute(stmt)
            rows = result.all()

            summary = {
                'total': 0,
                'by_status': {}
            }

            for row in rows:
                status_str = row[0]
                count = row[1]
                summary['by_status'][status_str] = count
                summary['total'] += count

            return summary
        except Exception as e:
            logger.error(f"Error getting task status summary: {e}")
            raise

    async def delete(self, task_id: str) -> bool:
        """Delete a task status record by task ID"""
        try:
            stmt = delete(CeleryTaskStatusModel).where(CeleryTaskStatusModel.task_id == task_id)
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting task status {task_id}: {e}")
            await self.session.rollback()
            raise

    async def delete_by_status(self, status: TaskStatus) -> int:
        """Delete all task status records with the given status"""
        try:
            stmt = delete(CeleryTaskStatusModel).where(CeleryTaskStatusModel.status == status.value)
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount
        except Exception as e:
            logger.error(f"Error deleting task statuses by status {status}: {e}")
            await self.session.rollback()
            raise

