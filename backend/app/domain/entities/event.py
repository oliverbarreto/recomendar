"""
Event domain entity - Phase 5 Enhanced Version
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class EventType(str, Enum):
    """Event type enumeration - enhanced for Phase 5"""
    # User actions
    USER_ACTION = "user_action"
    
    # System events
    SYSTEM_EVENT = "system_event"
    
    # Background tasks
    BACKGROUND_TASK = "background_task"
    
    # Error events
    ERROR_EVENT = "error_event"
    
    # Security events
    SECURITY_EVENT = "security_event"
    
    # Performance events
    PERFORMANCE_EVENT = "performance_event"
    
    # Legacy event types (maintain backwards compatibility)
    EPISODE_CREATED = "episode_created"
    EPISODE_UPDATED = "episode_updated"
    EPISODE_DELETED = "episode_deleted"
    DOWNLOAD_STARTED = "download_started"
    DOWNLOAD_COMPLETED = "download_completed"
    DOWNLOAD_FAILED = "download_failed"
    RSS_GENERATED = "rss_generated"
    CHANNEL_UPDATED = "channel_updated"
    TAG_CREATED = "tag_created"
    TAG_UPDATED = "tag_updated"
    TAG_DELETED = "tag_deleted"


class EventStatus(str, Enum):
    """Event status enumeration - enhanced for Phase 5"""
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    # Legacy statuses (maintain backwards compatibility)
    REQUESTED = "requested"
    PROCESSING = "processing"


class EventSeverity(str, Enum):
    """Event severity enumeration"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Event:
    """
    Event domain entity for system events and audit logging - Phase 5 Enhanced Version
    """
    # Core identifiers
    id: Optional[int]
    channel_id: int
    episode_id: Optional[int] = None
    user_id: Optional[int] = None
    
    # Event classification
    event_type: EventType = EventType.USER_ACTION
    action: str = ""
    resource_type: str = ""  # 'episode', 'channel', 'tag', 'system'
    resource_id: Optional[str] = None  # flexible identifier
    
    # Event content
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)  # structured event data
    metadata: Dict[str, Any] = field(default_factory=dict)  # additional context
    
    # Event status and priority
    status: EventStatus = EventStatus.STARTED
    severity: EventSeverity = EventSeverity.INFO
    
    # Performance tracking
    duration_ms: Optional[int] = None  # for timed operations
    
    # Request context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        # Validate channel_id
        if self.channel_id <= 0:
            raise ValueError("Valid channel_id is required")
        
        # Validate episode_id if provided
        if self.episode_id is not None and self.episode_id <= 0:
            raise ValueError("episode_id must be positive if provided")
        
        # Validate user_id if provided
        if self.user_id is not None and self.user_id <= 0:
            raise ValueError("user_id must be positive if provided")
        
        # Set default resource_type based on event context
        if not self.resource_type:
            if self.episode_id:
                self.resource_type = "episode"
            elif self.event_type in [EventType.SYSTEM_EVENT, EventType.PERFORMANCE_EVENT]:
                self.resource_type = "system"
            else:
                self.resource_type = "channel"
        
        # Set default resource_id if not provided
        if not self.resource_id:
            if self.episode_id:
                self.resource_id = str(self.episode_id)
            elif self.resource_type == "channel":
                self.resource_id = str(self.channel_id)
        
        # Ensure dictionaries are initialized
        if self.details is None:
            self.details = {}
        if self.metadata is None:
            self.metadata = {}
        
        # Set timestamps
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        
        # Validate action is provided
        if not self.action and not self.message:
            raise ValueError("Either action or message must be provided")
    
    def update_status(self, new_status: EventStatus, message: Optional[str] = None) -> None:
        """
        Update event status with optional message
        """
        if not self._is_valid_status_transition(self.status, new_status):
            raise ValueError(f"Invalid status transition from {self.status.value} to {new_status.value}")
        
        self.status = new_status
        
        if message is not None:
            self.message = message
        
        # Add status change to metadata
        self.metadata[f"status_changed_at_{new_status.value}"] = datetime.utcnow().isoformat()
    
    def _is_valid_status_transition(self, from_status: EventStatus, to_status: EventStatus) -> bool:
        """
        Validate if status transition is allowed
        """
        valid_transitions = {
            EventStatus.REQUESTED: [EventStatus.PROCESSING, EventStatus.FAILED],
            EventStatus.PROCESSING: [EventStatus.COMPLETED, EventStatus.FAILED],
            EventStatus.COMPLETED: [],  # Terminal state
            EventStatus.FAILED: [EventStatus.REQUESTED]  # Allow retry
        }
        
        return to_status in valid_transitions.get(from_status, [])
    
    def add_metadata(self, key: str, value: Any) -> None:
        """
        Add metadata entry
        """
        if not key:
            raise ValueError("Metadata key cannot be empty")
        
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get metadata value by key
        """
        return self.metadata.get(key, default)
    
    def mark_as_completed(self, message: Optional[str] = None) -> None:
        """
        Mark event as completed
        """
        self.update_status(EventStatus.COMPLETED, message)
    
    def mark_as_failed(self, error_message: str, error_details: Optional[Dict[str, Any]] = None) -> None:
        """
        Mark event as failed with error information
        """
        self.update_status(EventStatus.FAILED, error_message)
        
        if error_details:
            self.metadata.update({
                "error_details": error_details,
                "failed_at": datetime.utcnow().isoformat()
            })
    
    def get_processing_duration(self) -> Optional[int]:
        """
        Get processing duration in seconds if event is completed
        """
        if self.status != EventStatus.COMPLETED:
            return None
        
        completed_at_str = self.metadata.get(f"status_changed_at_{EventStatus.COMPLETED.value}")
        processing_at_str = self.metadata.get(f"status_changed_at_{EventStatus.PROCESSING.value}")
        
        if not (completed_at_str and processing_at_str):
            return None
        
        try:
            completed_at = datetime.fromisoformat(completed_at_str)
            processing_at = datetime.fromisoformat(processing_at_str)
            return int((completed_at - processing_at).total_seconds())
        except (ValueError, TypeError):
            return None
    
    def is_stale(self, max_age_hours: int = 24) -> bool:
        """
        Check if event is stale (older than max_age_hours)
        """
        if not self.created_at:
            return True
        
        age_hours = (datetime.utcnow() - self.created_at).total_seconds() / 3600
        return age_hours > max_age_hours
    
    @classmethod
    def create_episode_event(
        cls,
        channel_id: int,
        episode_id: int,
        event_type: EventType,
        message: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'Event':
        """
        Factory method to create an episode-related event
        """
        episode_events = [
            EventType.EPISODE_CREATED,
            EventType.EPISODE_UPDATED,
            EventType.EPISODE_DELETED,
            EventType.DOWNLOAD_STARTED,
            EventType.DOWNLOAD_COMPLETED,
            EventType.DOWNLOAD_FAILED,
        ]
        
        if event_type not in episode_events:
            raise ValueError(f"Event type {event_type.value} is not an episode event")
        
        return cls(
            id=None,
            channel_id=channel_id,
            episode_id=episode_id,
            event_type=event_type,
            message=message,
            metadata=metadata or {}
        )
    
    @classmethod
    def create_channel_event(
        cls,
        channel_id: int,
        event_type: EventType,
        message: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'Event':
        """
        Factory method to create a channel-related event
        """
        channel_events = [
            EventType.CHANNEL_UPDATED,
            EventType.RSS_GENERATED,
            EventType.TAG_CREATED,
            EventType.TAG_UPDATED,
            EventType.TAG_DELETED,
        ]
        
        if event_type not in channel_events:
            raise ValueError(f"Event type {event_type.value} is not a channel event")
        
        return cls(
            id=None,
            channel_id=channel_id,
            episode_id=None,
            event_type=event_type,
            message=message,
            metadata=metadata or {}
        )
    
    # New Phase 5 factory methods
    @classmethod
    def create_user_action(
        cls,
        channel_id: int,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        user_id: Optional[int] = None,
        message: str = "",
        details: Optional[Dict[str, Any]] = None,
        severity: EventSeverity = EventSeverity.INFO,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> 'Event':
        """Factory method to create a user action event"""
        return cls(
            id=None,
            channel_id=channel_id,
            user_id=user_id,
            event_type=EventType.USER_ACTION,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            message=message,
            details=details or {},
            severity=severity,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @classmethod
    def create_system_event(
        cls,
        channel_id: int,
        action: str,
        message: str,
        severity: EventSeverity = EventSeverity.INFO,
        details: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[int] = None
    ) -> 'Event':
        """Factory method to create a system event"""
        return cls(
            id=None,
            channel_id=channel_id,
            event_type=EventType.SYSTEM_EVENT,
            action=action,
            resource_type="system",
            message=message,
            details=details or {},
            severity=severity,
            duration_ms=duration_ms
        )
    
    @classmethod
    def create_error_event(
        cls,
        channel_id: int,
        action: str,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None,
        severity: EventSeverity = EventSeverity.ERROR,
        resource_type: str = "system",
        resource_id: Optional[str] = None
    ) -> 'Event':
        """Factory method to create an error event"""
        return cls(
            id=None,
            channel_id=channel_id,
            event_type=EventType.ERROR_EVENT,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            message=error_message,
            details=error_details or {},
            severity=severity,
            status=EventStatus.FAILED
        )
    
    def update_timing(self, duration_ms: int) -> None:
        """Update event with timing information"""
        self.duration_ms = duration_ms
        self.updated_at = datetime.utcnow()
    
    def add_details(self, key: str, value: Any) -> None:
        """Add details entry"""
        if not key:
            raise ValueError("Details key cannot be empty")
        self.details[key] = value
        self.updated_at = datetime.utcnow()
    
    def is_user_action(self) -> bool:
        """Check if this is a user action event"""
        return self.event_type == EventType.USER_ACTION
    
    def is_system_event(self) -> bool:
        """Check if this is a system event"""
        return self.event_type == EventType.SYSTEM_EVENT
    
    def is_error_event(self) -> bool:
        """Check if this is an error event"""
        return self.event_type == EventType.ERROR_EVENT
    
    def has_duration(self) -> bool:
        """Check if event has duration tracking"""
        return self.duration_ms is not None
    
    def get_severity_level(self) -> int:
        """Get numeric severity level for comparison"""
        severity_levels = {
            EventSeverity.DEBUG: 0,
            EventSeverity.INFO: 1,
            EventSeverity.WARNING: 2,
            EventSeverity.ERROR: 3,
            EventSeverity.CRITICAL: 4
        }
        return severity_levels.get(self.severity, 1)