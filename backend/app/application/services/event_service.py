"""
Event service for coordinating event logging and monitoring - Phase 5 Enhanced Version
Application service for comprehensive event management business logic
"""
import logging
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import time
import traceback
import asyncio
from dataclasses import dataclass

from app.domain.entities.event import Event, EventType, EventStatus, EventSeverity
from app.domain.repositories.event_repository import EventRepositoryInterface

logger = logging.getLogger(__name__)


class EventNotFoundError(Exception):
    """Exception raised when event is not found"""
    pass


class EventValidationError(Exception):
    """Exception raised when event validation fails"""
    pass


@dataclass
class EventFilterCriteria:
    """Filter criteria for event queries"""
    channel_id: Optional[int] = None
    user_id: Optional[int] = None
    episode_id: Optional[int] = None
    event_type: Optional[EventType] = None
    status: Optional[EventStatus] = None
    severity: Optional[EventSeverity] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    search_query: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    limit: int = 100
    offset: int = 0


@dataclass
class PerformanceMetrics:
    """Performance tracking data"""
    operation_name: str
    duration_ms: int
    success: bool
    metadata: Dict[str, Any]


class EventService:
    """
    Application service for event logging and monitoring with Phase 5 capabilities
    """
    
    def __init__(self, event_repository: EventRepositoryInterface):
        self.event_repository = event_repository
    
    # Core Event Management Methods
    
    async def create_event(
        self,
        channel_id: int,
        event_type: EventType,
        action: str,
        message: str,
        **kwargs
    ) -> Event:
        """
        Create a new event with comprehensive data
        
        Args:
            channel_id: Channel ID
            event_type: Type of event
            action: Action being performed
            message: Event message
            **kwargs: Additional event fields (episode_id, user_id, etc.)
        
        Returns:
            Created event entity
        """
        try:
            event = Event(
                id=None,
                channel_id=channel_id,
                event_type=event_type,
                action=action,
                message=message,
                **kwargs
            )
            
            return await self.event_repository.create(event)
            
        except Exception as e:
            logger.error(f"Failed to create event: {str(e)}")
            # Create a fallback error event
            try:
                error_event = Event.create_error_event(
                    channel_id=channel_id,
                    action="create_event_failed",
                    error_message=f"Failed to create event: {str(e)}",
                    error_details={"original_action": action, "error": str(e)}
                )
                await self.event_repository.create(error_event)
            except:
                pass  # Don't let error logging fail the operation
            raise
    
    async def get_event_by_id(self, event_id: int) -> Event:
        """Get event by ID"""
        event = await self.event_repository.get_by_id(event_id)
        if not event:
            raise EventNotFoundError(f"Event with ID {event_id} not found")
        return event
    
    async def update_event_status(
        self,
        event_id: int,
        status: EventStatus,
        message: Optional[str] = None,
        duration_ms: Optional[int] = None
    ) -> Event:
        """Update event status with optional timing data"""
        event = await self.get_event_by_id(event_id)
        event.update_status(status, message)
        
        if duration_ms is not None:
            event.update_timing(duration_ms)
        
        updated_event = await self.event_repository.update(event)
        if not updated_event:
            raise EventNotFoundError(f"Failed to update event {event_id}")
        
        return updated_event
    
    # Phase 5 Enhanced Logging Methods
    
    async def log_user_action(
        self,
        channel_id: int,
        user_id: int,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        message: str = "",
        details: Optional[Dict[str, Any]] = None,
        severity: EventSeverity = EventSeverity.INFO,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Event:
        """Log user action event"""
        event = Event.create_user_action(
            channel_id=channel_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            message=message or f"User performed {action} on {resource_type}",
            details=details,
            severity=severity,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return await self.event_repository.create(event)
    
    async def log_system_event(
        self,
        channel_id: int,
        action: str,
        message: str,
        severity: EventSeverity = EventSeverity.INFO,
        details: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[int] = None
    ) -> Event:
        """Log system event"""
        event = Event.create_system_event(
            channel_id=channel_id,
            action=action,
            message=message,
            severity=severity,
            details=details,
            duration_ms=duration_ms
        )
        
        return await self.event_repository.create(event)
    
    async def log_error_event(
        self,
        channel_id: int,
        action: str,
        error: Union[Exception, str],
        resource_type: str = "system",
        resource_id: Optional[str] = None,
        severity: EventSeverity = EventSeverity.ERROR,
        include_traceback: bool = True
    ) -> Event:
        """Log error event with detailed error information"""
        if isinstance(error, Exception):
            error_message = str(error)
            error_details = {
                "error_type": error.__class__.__name__,
                "error_message": str(error)
            }
            if include_traceback:
                error_details["traceback"] = traceback.format_exc()
        else:
            error_message = str(error)
            error_details = {"error_message": error_message}
        
        event = Event.create_error_event(
            channel_id=channel_id,
            action=action,
            error_message=error_message,
            error_details=error_details,
            severity=severity,
            resource_type=resource_type,
            resource_id=resource_id
        )
        
        return await self.event_repository.create(event)
    
    async def log_performance_event(
        self,
        channel_id: int,
        operation: str,
        duration_ms: int,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None
    ) -> Event:
        """Log performance tracking event"""
        severity = EventSeverity.INFO if success else EventSeverity.WARNING
        message = f"Operation {operation} took {duration_ms}ms"
        
        if not success:
            message += " (failed)"
        
        performance_details = {
            "operation": operation,
            "success": success,
            "duration_ms": duration_ms
        }
        if details:
            performance_details.update(details)
        
        event = Event(
            id=None,
            channel_id=channel_id,
            event_type=EventType.PERFORMANCE_EVENT,
            action=operation,
            resource_type="system",
            message=message,
            details=performance_details,
            severity=severity,
            duration_ms=duration_ms
        )
        
        return await self.event_repository.create(event)
    
    # Performance Tracking Utilities
    
    @asynccontextmanager
    async def track_operation(
        self,
        channel_id: int,
        operation_name: str,
        auto_log: bool = True,
        details: Optional[Dict[str, Any]] = None
    ):
        """Context manager for tracking operation performance"""
        start_time = time.time()
        success = False
        error_details = None
        
        try:
            yield
            success = True
        except Exception as e:
            error_details = {"error": str(e), "error_type": e.__class__.__name__}
            raise
        finally:
            duration_ms = int((time.time() - start_time) * 1000)
            
            if auto_log:
                try:
                    if success:
                        await self.log_performance_event(
                            channel_id=channel_id,
                            operation=operation_name,
                            duration_ms=duration_ms,
                            success=True,
                            details=details
                        )
                    else:
                        combined_details = details or {}
                        if error_details:
                            combined_details.update(error_details)
                        
                        await self.log_error_event(
                            channel_id=channel_id,
                            action=operation_name,
                            error=combined_details.get("error", "Unknown error"),
                            severity=EventSeverity.ERROR
                        )
                except Exception as log_error:
                    logger.error(f"Failed to log operation tracking: {log_error}")
    
    # Event Querying Methods
    
    async def get_events_by_criteria(
        self,
        criteria: EventFilterCriteria
    ) -> List[Event]:
        """Get events by comprehensive filter criteria"""
        if criteria.channel_id:
            return await self.event_repository.get_by_channel_id(
                channel_id=criteria.channel_id,
                limit=criteria.limit,
                offset=criteria.offset,
                event_type=criteria.event_type,
                status=criteria.status,
                severity=criteria.severity
            )
        elif criteria.user_id:
            return await self.event_repository.get_by_user_id(
                user_id=criteria.user_id,
                limit=criteria.limit,
                offset=criteria.offset,
                start_time=criteria.start_time,
                end_time=criteria.end_time
            )
        elif criteria.episode_id:
            return await self.event_repository.get_by_episode_id(criteria.episode_id)
        elif criteria.search_query:
            return await self.event_repository.search_events(
                query=criteria.search_query,
                channel_id=criteria.channel_id,
                event_type=criteria.event_type,
                limit=criteria.limit
            )
        else:
            return await self.event_repository.get_recent_events(
                hours=24,
                limit=criteria.limit,
                severity=criteria.severity
            )
    
    async def get_recent_events(
        self,
        hours: int = 24,
        limit: int = 100,
        severity: Optional[EventSeverity] = None
    ) -> List[Event]:
        """Get recent events"""
        return await self.event_repository.get_recent_events(
            hours=hours,
            limit=limit,
            severity=severity
        )
    
    async def get_error_events(
        self,
        channel_id: Optional[int] = None,
        hours: int = 24,
        limit: int = 50
    ) -> List[Event]:
        """Get recent error events"""
        start_time = datetime.utcnow() - timedelta(hours=hours) if hours else None
        
        return await self.event_repository.get_error_events(
            channel_id=channel_id,
            start_time=start_time,
            limit=limit
        )
    
    async def get_performance_metrics(
        self,
        channel_id: Optional[int] = None,
        hours: int = 24,
        min_duration_ms: Optional[int] = None
    ) -> List[Event]:
        """Get performance events for analysis"""
        return await self.event_repository.get_performance_events(
            min_duration_ms=min_duration_ms,
            limit=100
        )
    
    async def get_user_activity(
        self,
        user_id: int,
        hours: int = 24
    ) -> List[Event]:
        """Get user activity for audit purposes"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        return await self.event_repository.get_user_activity(
            user_id=user_id,
            start_time=start_time
        )
    
    # Analytics and Statistics
    
    async def get_event_statistics(
        self,
        channel_id: Optional[int] = None,
        hours: int = 24
    ) -> Dict[str, Any]:
        """Get comprehensive event statistics"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        return await self.event_repository.get_event_statistics(
            channel_id=channel_id,
            start_time=start_time
        )
    
    async def get_system_health_summary(
        self,
        channel_id: Optional[int] = None,
        hours: int = 24
    ) -> Dict[str, Any]:
        """Get system health summary based on events"""
        stats = await self.get_event_statistics(channel_id=channel_id, hours=hours)
        error_events = await self.get_error_events(channel_id=channel_id, hours=hours)
        
        total_events = stats.get("total_events", 0)
        error_count = len(error_events)
        error_rate = (error_count / total_events * 100) if total_events > 0 else 0
        
        # Classify health status
        if error_rate == 0:
            health_status = "healthy"
        elif error_rate < 5:
            health_status = "good"
        elif error_rate < 15:
            health_status = "warning"
        else:
            health_status = "critical"
        
        return {
            "health_status": health_status,
            "error_rate_percentage": round(error_rate, 2),
            "total_events": total_events,
            "error_count": error_count,
            "stats": stats,
            "recent_errors": error_events[:5]  # Last 5 errors
        }
    
    # Maintenance Methods
    
    async def cleanup_old_events(
        self,
        older_than_hours: int = 720,  # 30 days
        severity_threshold: EventSeverity = EventSeverity.INFO,
        dry_run: bool = False
    ) -> int:
        """Clean up old events to manage database size"""
        if dry_run:
            # Count what would be deleted
            cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
            # This would require a new repository method for counting
            logger.info(f"DRY RUN: Would cleanup events older than {cutoff_time}")
            return 0
        
        deleted_count = await self.event_repository.cleanup_old_events(
            older_than_hours=older_than_hours,
            severity_threshold=severity_threshold
        )
        
        # Log the cleanup operation
        await self.log_system_event(
            channel_id=0,  # System-wide operation
            action="event_cleanup",
            message=f"Cleaned up {deleted_count} old events",
            details={
                "deleted_count": deleted_count,
                "older_than_hours": older_than_hours,
                "severity_threshold": severity_threshold.value
            }
        )
        
        return deleted_count
    
    async def find_stale_events(
        self,
        max_age_hours: int = 24,
        status_filter: Optional[List[EventStatus]] = None
    ) -> List[Event]:
        """Find potentially stale events that need attention"""
        return await self.event_repository.get_stale_events(
            max_age_hours=max_age_hours,
            status_filter=status_filter
        )
    
    async def mark_stale_events_as_failed(
        self,
        max_age_hours: int = 24
    ) -> int:
        """Mark stale in-progress events as failed"""
        stale_events = await self.find_stale_events(
            max_age_hours=max_age_hours,
            status_filter=[EventStatus.IN_PROGRESS, EventStatus.STARTED]
        )
        
        failed_count = 0
        for event in stale_events:
            try:
                await self.update_event_status(
                    event.id,
                    EventStatus.FAILED,
                    f"Marked as failed due to staleness (over {max_age_hours}h old)"
                )
                failed_count += 1
            except Exception as e:
                logger.error(f"Failed to mark event {event.id} as failed: {e}")
        
        if failed_count > 0:
            await self.log_system_event(
                channel_id=0,
                action="mark_stale_events_failed",
                message=f"Marked {failed_count} stale events as failed",
                details={"failed_count": failed_count, "max_age_hours": max_age_hours}
            )
        
        return failed_count
    
    # Bulk Operations
    
    async def bulk_update_event_status(
        self,
        event_ids: List[int],
        status: EventStatus
    ) -> int:
        """Bulk update event status"""
        return await self.event_repository.bulk_update_status(event_ids, status)
    
    async def create_events_batch(
        self,
        events: List[Event]
    ) -> List[Event]:
        """Create multiple events in batch (would need repository support)"""
        created_events = []
        for event in events:
            try:
                created_event = await self.event_repository.create(event)
                created_events.append(created_event)
            except Exception as e:
                logger.error(f"Failed to create event in batch: {e}")
                # Continue with other events
        
        return created_events