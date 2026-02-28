"""
Event repository interface
"""
from abc import abstractmethod
from datetime import datetime
from typing import List, Optional
from app.domain.repositories.base import BaseRepository
from app.domain.entities.event import Event, EventType, EventStatus

class EventRepository(BaseRepository[Event]):
    """
    Repository interface for Event entities.
    Extends BaseRepository with event-specific operations and cleanup functionality.
    """
    
    @abstractmethod
    async def find_by_channel(self, channel_id: int, skip: int = 0, limit: int = 100) -> List[Event]:
        """
        Find events by channel with pagination
        
        Args:
            channel_id: The channel ID to filter by
            skip: Number of events to skip (for pagination)
            limit: Maximum number of events to return
            
        Returns:
            List of events for the channel (may be empty)
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def find_by_type(self, event_type: EventType) -> List[Event]:
        """
        Find events by event type
        
        Args:
            event_type: The event type to filter by
            
        Returns:
            List of events with the specified type (may be empty)
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def find_by_status(self, status: EventStatus) -> List[Event]:
        """
        Find events by processing status
        
        Args:
            status: The event status to filter by
            
        Returns:
            List of events with the specified status (may be empty)
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def find_by_episode(self, episode_id: int) -> List[Event]:
        """
        Find all events related to a specific episode
        
        Args:
            episode_id: The episode ID to filter by
            
        Returns:
            List of events for the episode (may be empty)
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def cleanup_old_events(self, older_than: datetime) -> int:
        """
        Delete events older than the specified date
        
        Args:
            older_than: Delete events created before this datetime
            
        Returns:
            Number of events deleted
            
        Raises:
            RepositoryError: If cleanup fails
        """
        pass
    
    @abstractmethod
    async def get_pending_events(self, limit: int = 100) -> List[Event]:
        """
        Get events that are pending processing
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of pending events ordered by creation time (may be empty)
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def update_event_status(
        self, 
        event_id: int, 
        status: EventStatus, 
        message: Optional[str] = None
    ) -> bool:
        """
        Update event status and optional message
        
        Args:
            event_id: The event ID
            status: The new status
            message: Optional status message
            
        Returns:
            True if event was updated, False if event not found
            
        Raises:
            RepositoryError: If update fails
        """
        pass
    
    @abstractmethod
    async def get_failed_events(self, limit: int = 100) -> List[Event]:
        """
        Get events that have failed processing
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of failed events ordered by creation time (may be empty)
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def get_events_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime,
        channel_id: Optional[int] = None,
        event_type: Optional[EventType] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Event]:
        """
        Get events within a date range with optional filters
        
        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            channel_id: Optional channel ID to filter by
            event_type: Optional event type to filter by
            skip: Number of events to skip (for pagination)
            limit: Maximum number of events to return
            
        Returns:
            List of events in the date range (may be empty)
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def count_events_by_type(self, channel_id: Optional[int] = None) -> dict[EventType, int]:
        """
        Get count of events by type, optionally filtered by channel
        
        Args:
            channel_id: Optional channel ID to filter by
            
        Returns:
            Dictionary mapping event types to counts
            
        Raises:
            RepositoryError: If counting fails
        """
        pass
    
    @abstractmethod
    async def bulk_cleanup_completed_events(self, older_than: datetime, batch_size: int = 1000) -> int:
        """
        Clean up completed events in batches to avoid performance issues
        
        Args:
            older_than: Delete completed events created before this datetime
            batch_size: Number of events to delete per batch
            
        Returns:
            Total number of events deleted
            
        Raises:
            RepositoryError: If cleanup fails
        """
        pass