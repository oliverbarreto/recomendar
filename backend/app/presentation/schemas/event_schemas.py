"""
Event API schemas - Phase 5 Enhanced Version
Pydantic schemas for event logging and monitoring endpoints
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

from app.domain.entities.event import EventType, EventStatus, EventSeverity


# Request Schemas
class EventCreateRequest(BaseModel):
    """Schema for creating a new event"""
    channel_id: int = Field(..., description="Channel ID associated with the event")
    episode_id: Optional[int] = Field(None, description="Episode ID if event relates to specific episode")
    user_id: Optional[int] = Field(None, description="User ID if event is a user action")
    event_type: EventType = Field(..., description="Type of event")
    action: str = Field(..., min_length=1, max_length=100, description="Action being performed")
    resource_type: str = Field(..., min_length=1, max_length=50, description="Type of resource (episode, channel, system)")
    resource_id: Optional[str] = Field(None, max_length=100, description="Resource identifier")
    message: str = Field(..., min_length=1, description="Event message")
    details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional event details")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Event metadata")
    severity: EventSeverity = Field(default=EventSeverity.INFO, description="Event severity level")
    duration_ms: Optional[int] = Field(None, ge=0, description="Duration in milliseconds for timed operations")
    ip_address: Optional[str] = Field(None, max_length=45, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")


class EventUpdateRequest(BaseModel):
    """Schema for updating an existing event"""
    status: Optional[EventStatus] = Field(None, description="New event status")
    message: Optional[str] = Field(None, min_length=1, description="Updated message")
    details: Optional[Dict[str, Any]] = Field(None, description="Updated details")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated metadata")
    severity: Optional[EventSeverity] = Field(None, description="Updated severity")
    duration_ms: Optional[int] = Field(None, ge=0, description="Duration in milliseconds")


class UserActionEventRequest(BaseModel):
    """Schema for creating user action events"""
    channel_id: int = Field(..., description="Channel ID")
    user_id: int = Field(..., description="User ID performing the action")
    action: str = Field(..., min_length=1, max_length=100, description="Action being performed")
    resource_type: str = Field(..., min_length=1, max_length=50, description="Resource type")
    resource_id: Optional[str] = Field(None, max_length=100, description="Resource ID")
    message: Optional[str] = Field(None, description="Event message")
    details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Event details")
    severity: EventSeverity = Field(default=EventSeverity.INFO, description="Event severity")
    ip_address: Optional[str] = Field(None, max_length=45, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")


class SystemEventRequest(BaseModel):
    """Schema for creating system events"""
    channel_id: int = Field(..., description="Channel ID (0 for system-wide events)")
    action: str = Field(..., min_length=1, max_length=100, description="System action")
    message: str = Field(..., min_length=1, description="Event message")
    severity: EventSeverity = Field(default=EventSeverity.INFO, description="Event severity")
    details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Event details")
    duration_ms: Optional[int] = Field(None, ge=0, description="Operation duration in milliseconds")


class ErrorEventRequest(BaseModel):
    """Schema for creating error events"""
    channel_id: int = Field(..., description="Channel ID")
    action: str = Field(..., min_length=1, max_length=100, description="Action that failed")
    error_message: str = Field(..., min_length=1, description="Error message")
    error_details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Error details")
    resource_type: str = Field(default="system", max_length=50, description="Resource type")
    resource_id: Optional[str] = Field(None, max_length=100, description="Resource ID")
    severity: EventSeverity = Field(default=EventSeverity.ERROR, description="Error severity")


# Query Parameter Schemas
class EventFilterParams(BaseModel):
    """Query parameters for filtering events"""
    channel_id: Optional[int] = Field(None, description="Filter by channel ID")
    user_id: Optional[int] = Field(None, description="Filter by user ID")
    episode_id: Optional[int] = Field(None, description="Filter by episode ID")
    event_type: Optional[EventType] = Field(None, description="Filter by event type")
    status: Optional[EventStatus] = Field(None, description="Filter by event status")
    severity: Optional[EventSeverity] = Field(None, description="Filter by minimum severity")
    resource_type: Optional[str] = Field(None, description="Filter by resource type")
    resource_id: Optional[str] = Field(None, description="Filter by resource ID")
    search: Optional[str] = Field(None, min_length=1, description="Search in event messages")
    hours: Optional[int] = Field(None, ge=1, le=8760, description="Filter events from last N hours")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(default=0, ge=0, description="Number of results to skip")

    model_config = ConfigDict(use_enum_values=True)


# Response Schemas
class EventResponse(BaseModel):
    """Schema for event response"""
    id: int = Field(..., description="Event ID")
    channel_id: int = Field(..., description="Channel ID")
    episode_id: Optional[int] = Field(None, description="Episode ID")
    user_id: Optional[int] = Field(None, description="User ID")
    event_type: EventType = Field(..., description="Event type")
    action: str = Field(..., description="Action performed")
    resource_type: str = Field(..., description="Resource type")
    resource_id: Optional[str] = Field(None, description="Resource ID")
    message: str = Field(..., description="Event message")
    details: Dict[str, Any] = Field(..., description="Event details")
    metadata: Dict[str, Any] = Field(..., description="Event metadata")
    status: EventStatus = Field(..., description="Event status")
    severity: EventSeverity = Field(..., description="Event severity")
    duration_ms: Optional[int] = Field(None, description="Duration in milliseconds")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class EventListResponse(BaseModel):
    """Schema for paginated event list response"""
    events: List[EventResponse] = Field(..., description="List of events")
    total: int = Field(..., description="Total number of events matching criteria")
    limit: int = Field(..., description="Applied limit")
    offset: int = Field(..., description="Applied offset")
    has_more: bool = Field(..., description="Whether there are more results")


class EventStatisticsResponse(BaseModel):
    """Schema for event statistics response"""
    total_events: int = Field(..., description="Total number of events")
    by_type: Dict[str, int] = Field(..., description="Event counts by type")
    by_status: Dict[str, int] = Field(..., description="Event counts by status")
    by_severity: Dict[str, int] = Field(..., description="Event counts by severity")
    time_period_hours: Optional[int] = Field(None, description="Time period for statistics")
    generated_at: datetime = Field(..., description="Statistics generation timestamp")


class SystemHealthResponse(BaseModel):
    """Schema for system health summary response"""
    health_status: str = Field(..., description="Overall health status")
    error_rate_percentage: float = Field(..., description="Error rate as percentage")
    total_events: int = Field(..., description="Total events in period")
    error_count: int = Field(..., description="Number of error events")
    stats: Dict[str, Any] = Field(..., description="Detailed statistics")
    recent_errors: List[EventResponse] = Field(..., description="Recent error events")
    check_timestamp: datetime = Field(..., description="Health check timestamp")


class MetricsResponse(BaseModel):
    """Schema for system metrics response"""
    system: Dict[str, Any] = Field(..., description="System metrics")
    application: Dict[str, Any] = Field(..., description="Application metrics")
    collection_timestamp: datetime = Field(..., description="Metrics collection timestamp")


class SystemHealthCheckResponse(BaseModel):
    """Schema for detailed system health check response"""
    health_status: str = Field(..., description="Overall health status")
    issues: List[str] = Field(..., description="List of identified issues")
    metrics: Dict[str, Any] = Field(..., description="Current system metrics")
    check_timestamp: datetime = Field(..., description="Health check timestamp")


class ApplicationHealthCheckResponse(BaseModel):
    """Schema for application health check response"""
    health_status: str = Field(..., description="Application health status")
    issues: List[str] = Field(..., description="List of identified issues")
    metrics: Dict[str, Any] = Field(..., description="Application metrics")
    event_summary: Dict[str, Any] = Field(..., description="Event-based health summary")
    check_timestamp: datetime = Field(..., description="Health check timestamp")


class MetricsReportResponse(BaseModel):
    """Schema for comprehensive metrics report response"""
    report_timestamp: datetime = Field(..., description="Report generation timestamp")
    current_metrics: Dict[str, Any] = Field(..., description="Current metrics snapshot")
    system_health: Dict[str, Any] = Field(..., description="System health status")
    application_health: Dict[str, Any] = Field(..., description="Application health status")
    historical_data: Dict[str, Any] = Field(..., description="Historical metrics data")
    collection_status: Dict[str, Any] = Field(..., description="Metrics collection status")


# Bulk Operation Schemas
class BulkEventStatusUpdate(BaseModel):
    """Schema for bulk event status updates"""
    event_ids: List[int] = Field(..., min_length=1, description="List of event IDs to update")
    status: EventStatus = Field(..., description="New status for all events")


class BulkEventStatusUpdateResponse(BaseModel):
    """Schema for bulk update response"""
    updated_count: int = Field(..., description="Number of events updated")
    event_ids: List[int] = Field(..., description="List of updated event IDs")


# Maintenance Operation Schemas
class EventCleanupRequest(BaseModel):
    """Schema for event cleanup request"""
    older_than_hours: int = Field(default=720, ge=1, le=8760, description="Clean events older than N hours")
    severity_threshold: EventSeverity = Field(default=EventSeverity.INFO, description="Only clean events below this severity")
    dry_run: bool = Field(default=True, description="Whether to perform a dry run")


class EventCleanupResponse(BaseModel):
    """Schema for event cleanup response"""
    deleted_count: int = Field(..., description="Number of events deleted")
    dry_run: bool = Field(..., description="Whether this was a dry run")
    cleanup_timestamp: datetime = Field(..., description="Cleanup operation timestamp")


class StaleEventCheckResponse(BaseModel):
    """Schema for stale event check response"""
    stale_events: List[EventResponse] = Field(..., description="List of stale events found")
    stale_count: int = Field(..., description="Number of stale events")
    max_age_hours: int = Field(..., description="Maximum age threshold used")
    check_timestamp: datetime = Field(..., description="Check timestamp")


# Error Response Schema
class ErrorResponse(BaseModel):
    """Standard error response schema"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


# Success Response Schema
class SuccessResponse(BaseModel):
    """Standard success response schema"""
    message: str = Field(..., description="Success message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")