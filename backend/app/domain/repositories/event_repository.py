"""
Event Repository Interface - Phase 5 Enhanced Version
Domain layer interface for event data access and querying
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.domain.entities.event import Event, EventType, EventStatus, EventSeverity


class EventRepositoryInterface(ABC):
    """
    Abstract repository interface for Event entities with Phase 5 advanced querying capabilities
    """
    
    @abstractmethod
    async def create(self, event: Event) -> Event:
        """
        Create a new event
        
        Args:
            event: Event entity to create
            
        Returns:
            Created event entity with assigned ID
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, event_id: int) -> Optional[Event]:
        """
        Get event by ID
        
        Args:
            event_id: Event ID
            
        Returns:
            Event entity or None if not found
        """
        pass
    
    @abstractmethod
    async def update(self, event: Event) -> Optional[Event]:
        """
        Update an existing event
        
        Args:
            event: Event entity with updated data
            
        Returns:
            Updated event entity or None if not found
        """
        pass
    
    @abstractmethod
    async def delete(self, event_id: int) -> bool:
        """
        Delete an event
        
        Args:
            event_id: Event ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    # Phase 5 Enhanced Query Methods
    
    @abstractmethod
    async def get_by_channel_id(
        self,
        channel_id: int,
        limit: int = 100,
        offset: int = 0,
        event_type: Optional[EventType] = None,
        status: Optional[EventStatus] = None,
        severity: Optional[EventSeverity] = None
    ) -> List[Event]:
        """
        Get events by channel ID with filtering
        
        Args:
            channel_id: Channel ID
            limit: Maximum number of results
            offset: Number of results to skip
            event_type: Filter by event type
            status: Filter by status
            severity: Filter by severity
            
        Returns:
            List of event entities matching criteria
        """
        pass
    
    @abstractmethod
    async def get_by_user_id(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Event]:
        """
        Get events by user ID with time range filtering
        
        Args:
            user_id: User ID
            limit: Maximum number of results
            offset: Number of results to skip
            start_time: Filter events after this time
            end_time: Filter events before this time
            
        Returns:
            List of event entities for the user
        """
        pass
    
    @abstractmethod
    async def get_by_episode_id(self, episode_id: int) -> List[Event]:
        """
        Get all events for a specific episode
        
        Args:
            episode_id: Episode ID
            
        Returns:
            List of event entities for the episode
        """
        pass
    
    @abstractmethod
    async def get_recent_events(
        self,
        hours: int = 24,
        limit: int = 100,
        severity: Optional[EventSeverity] = None
    ) -> List[Event]:
        """
        Get recent events within specified time window
        
        Args:
            hours: Number of hours to look back
            limit: Maximum number of results
            severity: Filter by minimum severity level
            
        Returns:
            List of recent events
        """
        pass
    
    @abstractmethod
    async def get_error_events(
        self,
        channel_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Event]:
        """
        Get error and critical severity events
        
        Args:
            channel_id: Optional channel filter
            start_time: Filter events after this time
            end_time: Filter events before this time
            limit: Maximum number of results
            
        Returns:
            List of error events
        """
        pass
    
    @abstractmethod
    async def get_performance_events(
        self,
        min_duration_ms: Optional[int] = None,
        event_type: Optional[EventType] = None,
        limit: int = 100
    ) -> List[Event]:
        """
        Get events with performance tracking data
        
        Args:
            min_duration_ms: Filter events with duration >= this value
            event_type: Filter by event type
            limit: Maximum number of results
            
        Returns:
            List of events with performance data
        """
        pass
    
    @abstractmethod
    async def search_events(
        self,
        query: str,
        channel_id: Optional[int] = None,
        event_type: Optional[EventType] = None,
        limit: int = 100
    ) -> List[Event]:
        """
        Search events by message content
        
        Args:
            query: Search term to match in message
            channel_id: Optional channel filter
            event_type: Optional event type filter
            limit: Maximum number of results
            
        Returns:
            List of matching events
        """
        pass
    
    @abstractmethod
    async def get_event_statistics(
        self,
        channel_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get aggregated event statistics
        
        Args:
            channel_id: Optional channel filter
            start_time: Filter events after this time
            end_time: Filter events before this time
            
        Returns:
            Dictionary with event counts by type, status, severity
        """
        pass
    
    @abstractmethod
    async def cleanup_old_events(
        self,
        older_than_hours: int = 720,  # 30 days default
        severity_threshold: EventSeverity = EventSeverity.INFO
    ) -> int:
        """
        Clean up old events below specified severity threshold
        
        Args:
            older_than_hours: Delete events older than this many hours
            severity_threshold: Only delete events below this severity
            
        Returns:
            Number of events deleted
        """
        pass
    
    @abstractmethod
    async def get_stale_events(
        self,
        max_age_hours: int = 24,
        status_filter: Optional[List[EventStatus]] = None
    ) -> List[Event]:
        """
        Get events that might be stuck or stale
        
        Args:
            max_age_hours: Consider events older than this as stale
            status_filter: Filter by specific statuses (e.g., in_progress)
            
        Returns:
            List of potentially stale events
        """
        pass
    
    @abstractmethod
    async def count_events_by_type(
        self,
        channel_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[EventType, int]:
        """
        Count events grouped by type
        
        Args:
            channel_id: Optional channel filter
            start_time: Filter events after this time
            end_time: Filter events before this time
            
        Returns:
            Dictionary mapping event types to counts
        """
        pass
    
    @abstractmethod
    async def get_user_activity(
        self,
        user_id: int,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Event]:
        """
        Get user activity events for audit purposes
        
        Args:
            user_id: User ID
            start_time: Filter events after this time
            end_time: Filter events before this time
            
        Returns:
            List of user action events
        """
        pass