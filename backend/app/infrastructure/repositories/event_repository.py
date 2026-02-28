"""
Event repository implementation using SQLAlchemy - Phase 5 Enhanced Version
Infrastructure layer implementation for event data access with advanced querying
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import (
    select, update, delete, func, and_, or_, desc, asc, 
    case, text, literal_column
)
from sqlalchemy.orm import selectinload

from app.domain.repositories.event_repository import EventRepositoryInterface
from app.domain.entities.event import Event, EventType, EventStatus, EventSeverity
from app.infrastructure.database.models.event import EventModel


class EventRepositoryImpl(EventRepositoryInterface):
    """
    SQLAlchemy implementation of Event repository with Phase 5 advanced querying capabilities
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
    
    def _model_to_entity(self, model: EventModel) -> Optional[Event]:
        """Convert SQLAlchemy model to domain entity"""
        if not model:
            return None
        
        return Event(
            id=model.id,
            channel_id=model.channel_id,
            episode_id=model.episode_id,
            user_id=model.user_id,
            event_type=EventType(model.event_type),
            action=model.action,
            resource_type=model.resource_type,
            resource_id=model.resource_id,
            message=model.message,
            details=model.details or {},
            metadata=model.event_metadata or {},
            status=EventStatus(model.status),
            severity=EventSeverity(model.severity),
            duration_ms=model.duration_ms,
            ip_address=model.ip_address,
            user_agent=model.user_agent,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def _entity_to_model(self, entity: Event, model: Optional[EventModel] = None) -> EventModel:
        """Convert domain entity to SQLAlchemy model"""
        if model is None:
            model = EventModel()
        
        model.channel_id = entity.channel_id
        model.episode_id = entity.episode_id
        model.user_id = entity.user_id
        model.event_type = entity.event_type.value
        model.action = entity.action
        model.resource_type = entity.resource_type
        model.resource_id = entity.resource_id
        model.message = entity.message
        model.details = entity.details
        model.event_metadata = entity.metadata
        model.status = entity.status.value
        model.severity = entity.severity.value
        model.duration_ms = entity.duration_ms
        model.ip_address = entity.ip_address
        model.user_agent = entity.user_agent
        model.updated_at = entity.updated_at
        
        if entity.id is not None:
            model.id = entity.id
        if entity.created_at is not None:
            model.created_at = entity.created_at
        
        return model
    
    async def create(self, event: Event) -> Event:
        """Create a new event"""
        model = self._entity_to_model(event)
        self.db_session.add(model)
        await self.db_session.flush()
        await self.db_session.refresh(model)
        return self._model_to_entity(model)
    
    async def get_by_id(self, event_id: int) -> Optional[Event]:
        """Get event by ID"""
        stmt = select(EventModel).where(EventModel.id == event_id)
        result = await self.db_session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_entity(model)
    
    async def update(self, event: Event) -> Optional[Event]:
        """Update an existing event"""
        if event.id is None:
            return None
        
        stmt = select(EventModel).where(EventModel.id == event.id)
        result = await self.db_session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        updated_model = self._entity_to_model(event, model)
        updated_model.updated_at = datetime.utcnow()
        await self.db_session.flush()
        await self.db_session.refresh(updated_model)
        return self._model_to_entity(updated_model)
    
    async def delete(self, event_id: int) -> bool:
        """Delete an event"""
        stmt = delete(EventModel).where(EventModel.id == event_id)
        result = await self.db_session.execute(stmt)
        return result.rowcount > 0
    
    # Phase 5 Enhanced Query Methods Implementation
    
    async def get_by_channel_id(
        self,
        channel_id: int,
        limit: int = 100,
        offset: int = 0,
        event_type: Optional[EventType] = None,
        status: Optional[EventStatus] = None,
        severity: Optional[EventSeverity] = None
    ) -> List[Event]:
        """Get events by channel ID with filtering"""
        stmt = select(EventModel).where(EventModel.channel_id == channel_id)
        
        if event_type:
            stmt = stmt.where(EventModel.event_type == event_type.value)
        if status:
            stmt = stmt.where(EventModel.status == status.value)
        if severity:
            stmt = stmt.where(EventModel.severity == severity.value)
        
        stmt = stmt.order_by(desc(EventModel.created_at)).offset(offset).limit(limit)
        
        result = await self.db_session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]
    
    async def get_by_user_id(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Event]:
        """Get events by user ID with time range filtering"""
        stmt = select(EventModel).where(EventModel.user_id == user_id)
        
        if start_time:
            stmt = stmt.where(EventModel.created_at >= start_time)
        if end_time:
            stmt = stmt.where(EventModel.created_at <= end_time)
        
        stmt = stmt.order_by(desc(EventModel.created_at)).offset(offset).limit(limit)
        
        result = await self.db_session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]
    
    async def get_by_episode_id(self, episode_id: int) -> List[Event]:
        """Get all events for a specific episode"""
        stmt = (
            select(EventModel)
            .where(EventModel.episode_id == episode_id)
            .order_by(asc(EventModel.created_at))
        )
        result = await self.db_session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]
    
    async def get_recent_events(
        self,
        hours: int = 24,
        limit: int = 100,
        severity: Optional[EventSeverity] = None
    ) -> List[Event]:
        """Get recent events within specified time window"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        stmt = select(EventModel).where(EventModel.created_at >= cutoff_time)
        
        if severity:
            # Get events with severity >= specified level
            severity_levels = {
                EventSeverity.DEBUG: 0,
                EventSeverity.INFO: 1,
                EventSeverity.WARNING: 2,
                EventSeverity.ERROR: 3,
                EventSeverity.CRITICAL: 4
            }
            min_level = severity_levels[severity]
            severity_case = case(
                (EventModel.severity == EventSeverity.DEBUG.value, 0),
                (EventModel.severity == EventSeverity.INFO.value, 1),
                (EventModel.severity == EventSeverity.WARNING.value, 2),
                (EventModel.severity == EventSeverity.ERROR.value, 3),
                (EventModel.severity == EventSeverity.CRITICAL.value, 4),
                else_=1
            )
            stmt = stmt.where(severity_case >= min_level)
        
        stmt = stmt.order_by(desc(EventModel.created_at)).limit(limit)
        
        result = await self.db_session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]
    
    async def get_error_events(
        self,
        channel_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Event]:
        """Get error and critical severity events"""
        stmt = select(EventModel).where(
            or_(
                EventModel.severity == EventSeverity.ERROR.value,
                EventModel.severity == EventSeverity.CRITICAL.value
            )
        )
        
        if channel_id:
            stmt = stmt.where(EventModel.channel_id == channel_id)
        if start_time:
            stmt = stmt.where(EventModel.created_at >= start_time)
        if end_time:
            stmt = stmt.where(EventModel.created_at <= end_time)
        
        stmt = stmt.order_by(desc(EventModel.created_at)).limit(limit)
        
        result = await self.db_session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]
    
    async def get_performance_events(
        self,
        min_duration_ms: Optional[int] = None,
        event_type: Optional[EventType] = None,
        limit: int = 100
    ) -> List[Event]:
        """Get events with performance tracking data"""
        stmt = select(EventModel).where(EventModel.duration_ms.isnot(None))
        
        if min_duration_ms:
            stmt = stmt.where(EventModel.duration_ms >= min_duration_ms)
        if event_type:
            stmt = stmt.where(EventModel.event_type == event_type.value)
        
        stmt = stmt.order_by(desc(EventModel.duration_ms)).limit(limit)
        
        result = await self.db_session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]
    
    async def search_events(
        self,
        query: str,
        channel_id: Optional[int] = None,
        event_type: Optional[EventType] = None,
        limit: int = 100
    ) -> List[Event]:
        """Search events by message content"""
        search_term = f"%{query}%"
        stmt = select(EventModel).where(EventModel.message.ilike(search_term))
        
        if channel_id:
            stmt = stmt.where(EventModel.channel_id == channel_id)
        if event_type:
            stmt = stmt.where(EventModel.event_type == event_type.value)
        
        stmt = stmt.order_by(desc(EventModel.created_at)).limit(limit)
        
        result = await self.db_session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]
    
    async def get_event_statistics(
        self,
        channel_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get aggregated event statistics"""
        base_query = select(EventModel)
        
        if channel_id:
            base_query = base_query.where(EventModel.channel_id == channel_id)
        if start_time:
            base_query = base_query.where(EventModel.created_at >= start_time)
        if end_time:
            base_query = base_query.where(EventModel.created_at <= end_time)
        
        # Count by event type
        type_stats = await self.db_session.execute(
            select(
                EventModel.event_type,
                func.count().label('count')
            )
            .select_from(base_query.subquery())
            .group_by(EventModel.event_type)
        )
        
        # Count by status
        status_stats = await self.db_session.execute(
            select(
                EventModel.status,
                func.count().label('count')
            )
            .select_from(base_query.subquery())
            .group_by(EventModel.status)
        )
        
        # Count by severity
        severity_stats = await self.db_session.execute(
            select(
                EventModel.severity,
                func.count().label('count')
            )
            .select_from(base_query.subquery())
            .group_by(EventModel.severity)
        )
        
        # Total count
        total_result = await self.db_session.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        
        return {
            "total_events": total_result.scalar(),
            "by_type": dict(type_stats.all()),
            "by_status": dict(status_stats.all()),
            "by_severity": dict(severity_stats.all())
        }
    
    async def cleanup_old_events(
        self,
        older_than_hours: int = 720,
        severity_threshold: EventSeverity = EventSeverity.INFO
    ) -> int:
        """Clean up old events below specified severity threshold"""
        cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
        
        # Define severity levels for comparison
        severity_levels = [
            EventSeverity.DEBUG.value,
            EventSeverity.INFO.value,
            EventSeverity.WARNING.value,
            EventSeverity.ERROR.value,
            EventSeverity.CRITICAL.value
        ]
        threshold_index = severity_levels.index(severity_threshold.value)
        severities_to_delete = severity_levels[:threshold_index]
        
        if not severities_to_delete:
            return 0
        
        stmt = delete(EventModel).where(
            and_(
                EventModel.created_at < cutoff_time,
                EventModel.severity.in_(severities_to_delete)
            )
        )
        
        result = await self.db_session.execute(stmt)
        return result.rowcount
    
    async def get_stale_events(
        self,
        max_age_hours: int = 24,
        status_filter: Optional[List[EventStatus]] = None
    ) -> List[Event]:
        """Get events that might be stuck or stale"""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        stmt = select(EventModel).where(EventModel.created_at < cutoff_time)
        
        if status_filter:
            status_values = [status.value for status in status_filter]
            stmt = stmt.where(EventModel.status.in_(status_values))
        else:
            # Default to events that might be stuck in progress
            stmt = stmt.where(
                or_(
                    EventModel.status == EventStatus.IN_PROGRESS.value,
                    EventModel.status == EventStatus.STARTED.value
                )
            )
        
        stmt = stmt.order_by(asc(EventModel.created_at))
        
        result = await self.db_session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]
    
    async def count_events_by_type(
        self,
        channel_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[EventType, int]:
        """Count events grouped by type"""
        stmt = select(
            EventModel.event_type,
            func.count().label('count')
        )
        
        conditions = []
        if channel_id:
            conditions.append(EventModel.channel_id == channel_id)
        if start_time:
            conditions.append(EventModel.created_at >= start_time)
        if end_time:
            conditions.append(EventModel.created_at <= end_time)
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        stmt = stmt.group_by(EventModel.event_type)
        
        result = await self.db_session.execute(stmt)
        
        # Convert to EventType enum keys
        counts = {}
        for event_type_value, count in result.all():
            try:
                event_type = EventType(event_type_value)
                counts[event_type] = count
            except ValueError:
                # Handle unknown event types gracefully
                counts[event_type_value] = count
        
        return counts
    
    async def get_user_activity(
        self,
        user_id: int,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Event]:
        """Get user activity events for audit purposes"""
        stmt = select(EventModel).where(
            and_(
                EventModel.user_id == user_id,
                EventModel.event_type == EventType.USER_ACTION.value
            )
        )
        
        if start_time:
            stmt = stmt.where(EventModel.created_at >= start_time)
        if end_time:
            stmt = stmt.where(EventModel.created_at <= end_time)
        
        stmt = stmt.order_by(desc(EventModel.created_at))
        
        result = await self.db_session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]
    
    # Additional utility methods for Phase 5
    
    async def get_events_by_resource(
        self,
        resource_type: str,
        resource_id: str,
        limit: int = 50
    ) -> List[Event]:
        """Get events for a specific resource"""
        stmt = (
            select(EventModel)
            .where(
                and_(
                    EventModel.resource_type == resource_type,
                    EventModel.resource_id == resource_id
                )
            )
            .order_by(desc(EventModel.created_at))
            .limit(limit)
        )
        
        result = await self.db_session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]
    
    async def update_event_status(
        self,
        event_id: int,
        status: EventStatus,
        message: Optional[str] = None
    ) -> bool:
        """Update event status with optional message"""
        values = {
            "status": status.value,
            "updated_at": datetime.utcnow()
        }
        
        if message:
            values["message"] = message
        
        stmt = update(EventModel).where(EventModel.id == event_id).values(**values)
        result = await self.db_session.execute(stmt)
        return result.rowcount > 0
    
    async def bulk_update_status(
        self,
        event_ids: List[int],
        status: EventStatus
    ) -> int:
        """Bulk update event status"""
        stmt = (
            update(EventModel)
            .where(EventModel.id.in_(event_ids))
            .values(
                status=status.value,
                updated_at=datetime.utcnow()
            )
        )
        result = await self.db_session.execute(stmt)
        return result.rowcount