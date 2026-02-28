"""
Event Logging API endpoints - Phase 5 Enhanced Version
Comprehensive event logging and monitoring API with advanced querying
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import List, Optional
import logging
from datetime import datetime, timedelta

from app.presentation.schemas.event_schemas import (
    EventCreateRequest, EventUpdateRequest, EventResponse, EventListResponse,
    UserActionEventRequest, SystemEventRequest, ErrorEventRequest,
    EventStatisticsResponse, SystemHealthResponse, MetricsResponse,
    SystemHealthCheckResponse, ApplicationHealthCheckResponse, MetricsReportResponse,
    BulkEventStatusUpdate, BulkEventStatusUpdateResponse,
    EventCleanupRequest, EventCleanupResponse, StaleEventCheckResponse,
    ErrorResponse, SuccessResponse, EventFilterParams
)
from app.application.services.event_service import (
    EventService, EventFilterCriteria, EventNotFoundError, EventValidationError
)
from app.application.services.metrics_service import MetricsCollectionService
from app.domain.entities.event import EventType, EventStatus, EventSeverity

logger = logging.getLogger(__name__)

# TODO: These would need to be implemented in the dependencies module
# For now using placeholder dependency functions
async def get_event_service() -> EventService:
    """Placeholder for event service dependency"""
    raise NotImplementedError("Event service dependency not implemented")

async def get_metrics_service() -> MetricsCollectionService:
    """Placeholder for metrics service dependency"""
    raise NotImplementedError("Metrics service dependency not implemented")

router = APIRouter(prefix="/events", tags=["events", "monitoring"])


# Core Event CRUD Operations

@router.post("/", response_model=EventResponse, status_code=201)
async def create_event(
    event_data: EventCreateRequest,
    request: Request,
    event_service: EventService = Depends(get_event_service)
):
    """
    Create a new event
    
    Creates a comprehensive event record with all Phase 5 enhanced fields.
    Automatically captures client IP and user agent if not provided.
    """
    try:
        # Auto-capture client information if not provided
        if not event_data.ip_address:
            event_data.ip_address = request.client.host
        if not event_data.user_agent:
            event_data.user_agent = request.headers.get("user-agent")
        
        event = await event_service.create_event(
            channel_id=event_data.channel_id,
            event_type=event_data.event_type,
            action=event_data.action,
            message=event_data.message,
            episode_id=event_data.episode_id,
            user_id=event_data.user_id,
            resource_type=event_data.resource_type,
            resource_id=event_data.resource_id,
            details=event_data.details,
            metadata=event_data.metadata,
            severity=event_data.severity,
            duration_ms=event_data.duration_ms,
            ip_address=event_data.ip_address,
            user_agent=event_data.user_agent
        )
        
        logger.info(f"Created event {event.id} for channel {event.channel_id}")
        return EventResponse.model_validate(event)
        
    except EventValidationError as e:
        logger.warning(f"Event validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create event: {e}")
        raise HTTPException(status_code=500, detail="Failed to create event")


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: int,
    event_service: EventService = Depends(get_event_service)
):
    """Get a specific event by ID"""
    try:
        event = await event_service.get_event_by_id(event_id)
        return EventResponse.model_validate(event)
    except EventNotFoundError:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
    except Exception as e:
        logger.error(f"Failed to get event {event_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve event")


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    update_data: EventUpdateRequest,
    event_service: EventService = Depends(get_event_service)
):
    """Update an existing event"""
    try:
        # Get current event
        event = await event_service.get_event_by_id(event_id)
        
        # Update fields if provided
        if update_data.status:
            event = await event_service.update_event_status(
                event_id, 
                update_data.status, 
                update_data.message,
                update_data.duration_ms
            )
        
        # For other fields, we'd need additional update methods in the service
        return EventResponse.model_validate(event)
        
    except EventNotFoundError:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
    except Exception as e:
        logger.error(f"Failed to update event {event_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update event")


# Specialized Event Creation Endpoints

@router.post("/user-actions", response_model=EventResponse, status_code=201)
async def create_user_action_event(
    event_data: UserActionEventRequest,
    request: Request,
    event_service: EventService = Depends(get_event_service)
):
    """Create a user action event with automatic IP/user agent capture"""
    try:
        # Auto-capture client information
        ip_address = event_data.ip_address or request.client.host
        user_agent = event_data.user_agent or request.headers.get("user-agent")
        
        event = await event_service.log_user_action(
            channel_id=event_data.channel_id,
            user_id=event_data.user_id,
            action=event_data.action,
            resource_type=event_data.resource_type,
            resource_id=event_data.resource_id,
            message=event_data.message or f"User {event_data.user_id} performed {event_data.action}",
            details=event_data.details,
            severity=event_data.severity,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return EventResponse.model_validate(event)
        
    except Exception as e:
        logger.error(f"Failed to create user action event: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user action event")


@router.post("/system-events", response_model=EventResponse, status_code=201)
async def create_system_event(
    event_data: SystemEventRequest,
    event_service: EventService = Depends(get_event_service)
):
    """Create a system event for monitoring and diagnostics"""
    try:
        event = await event_service.log_system_event(
            channel_id=event_data.channel_id,
            action=event_data.action,
            message=event_data.message,
            severity=event_data.severity,
            details=event_data.details,
            duration_ms=event_data.duration_ms
        )
        
        return EventResponse.model_validate(event)
        
    except Exception as e:
        logger.error(f"Failed to create system event: {e}")
        raise HTTPException(status_code=500, detail="Failed to create system event")


@router.post("/error-events", response_model=EventResponse, status_code=201)
async def create_error_event(
    event_data: ErrorEventRequest,
    event_service: EventService = Depends(get_event_service)
):
    """Create an error event for error tracking and monitoring"""
    try:
        event = await event_service.log_error_event(
            channel_id=event_data.channel_id,
            action=event_data.action,
            error=event_data.error_message,
            resource_type=event_data.resource_type,
            resource_id=event_data.resource_id,
            severity=event_data.severity,
            include_traceback=False  # Don't include traceback for API-created errors
        )
        
        # Add error details to the event
        if event_data.error_details:
            event.details.update(event_data.error_details)
        
        return EventResponse.model_validate(event)
        
    except Exception as e:
        logger.error(f"Failed to create error event: {e}")
        raise HTTPException(status_code=500, detail="Failed to create error event")


# Event Querying and Listing

@router.get("/", response_model=EventListResponse)
async def list_events(
    channel_id: Optional[int] = Query(None, description="Filter by channel ID"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    episode_id: Optional[int] = Query(None, description="Filter by episode ID"),
    event_type: Optional[EventType] = Query(None, description="Filter by event type"),
    status: Optional[EventStatus] = Query(None, description="Filter by event status"),
    severity: Optional[EventSeverity] = Query(None, description="Filter by minimum severity"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[str] = Query(None, description="Filter by resource ID"),
    search: Optional[str] = Query(None, description="Search in event messages"),
    hours: Optional[int] = Query(None, ge=1, le=8760, description="Filter events from last N hours"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    event_service: EventService = Depends(get_event_service)
):
    """
    List events with comprehensive filtering options
    
    Supports filtering by various criteria including time ranges, event types,
    status, severity, and text search.
    """
    try:
        # Build filter criteria
        criteria = EventFilterCriteria(
            channel_id=channel_id,
            user_id=user_id,
            episode_id=episode_id,
            event_type=event_type,
            status=status,
            severity=severity,
            resource_type=resource_type,
            resource_id=resource_id,
            search_query=search,
            limit=limit,
            offset=offset
        )
        
        # Add time filter if hours specified
        if hours:
            criteria.start_time = datetime.utcnow() - timedelta(hours=hours)
        
        events = await event_service.get_events_by_criteria(criteria)
        
        # For simplicity, we'll return the actual count as total
        # In production, you'd want a separate count query
        total = len(events)  # This is a simplified approach
        
        response = EventListResponse(
            events=[EventResponse.model_validate(event) for event in events],
            total=total,
            limit=limit,
            offset=offset,
            has_more=total == limit  # Simplified logic
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to list events: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve events")


@router.get("/recent", response_model=EventListResponse)
async def get_recent_events(
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    limit: int = Query(100, ge=1, le=1000),
    severity: Optional[EventSeverity] = Query(None, description="Minimum severity level"),
    event_service: EventService = Depends(get_event_service)
):
    """Get recent events within specified time window"""
    try:
        events = await event_service.get_recent_events(
            hours=hours,
            limit=limit,
            severity=severity
        )
        
        return EventListResponse(
            events=[EventResponse.model_validate(event) for event in events],
            total=len(events),
            limit=limit,
            offset=0,
            has_more=len(events) == limit
        )
        
    except Exception as e:
        logger.error(f"Failed to get recent events: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve recent events")


@router.get("/errors", response_model=EventListResponse)
async def get_error_events(
    channel_id: Optional[int] = Query(None, description="Filter by channel ID"),
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    limit: int = Query(50, ge=1, le=500),
    event_service: EventService = Depends(get_event_service)
):
    """Get recent error and critical events"""
    try:
        events = await event_service.get_error_events(
            channel_id=channel_id,
            hours=hours,
            limit=limit
        )
        
        return EventListResponse(
            events=[EventResponse.model_validate(event) for event in events],
            total=len(events),
            limit=limit,
            offset=0,
            has_more=len(events) == limit
        )
        
    except Exception as e:
        logger.error(f"Failed to get error events: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve error events")


@router.get("/performance", response_model=EventListResponse)
async def get_performance_events(
    min_duration_ms: Optional[int] = Query(None, ge=0, description="Minimum duration in milliseconds"),
    event_type: Optional[EventType] = Query(None, description="Filter by event type"),
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(100, ge=1, le=500),
    event_service: EventService = Depends(get_event_service)
):
    """Get performance events for analysis"""
    try:
        events = await event_service.get_performance_metrics(
            channel_id=None,
            hours=hours,
            min_duration_ms=min_duration_ms
        )
        
        # Apply additional filtering if needed
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        # Apply limit
        events = events[:limit]
        
        return EventListResponse(
            events=[EventResponse.model_validate(event) for event in events],
            total=len(events),
            limit=limit,
            offset=0,
            has_more=len(events) == limit
        )
        
    except Exception as e:
        logger.error(f"Failed to get performance events: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve performance events")


# Statistics and Analytics

@router.get("/statistics", response_model=EventStatisticsResponse)
async def get_event_statistics(
    channel_id: Optional[int] = Query(None, description="Filter by channel ID"),
    hours: int = Query(24, ge=1, le=8760, description="Time period in hours"),
    event_service: EventService = Depends(get_event_service)
):
    """Get comprehensive event statistics"""
    try:
        stats = await event_service.get_event_statistics(
            channel_id=channel_id,
            hours=hours
        )
        
        return EventStatisticsResponse(
            total_events=stats.get("total_events", 0),
            by_type=stats.get("by_type", {}),
            by_status=stats.get("by_status", {}),
            by_severity=stats.get("by_severity", {}),
            time_period_hours=hours,
            generated_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Failed to get event statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate statistics")


@router.get("/health-summary", response_model=SystemHealthResponse)
async def get_system_health_summary(
    channel_id: Optional[int] = Query(None, description="Filter by channel ID"),
    hours: int = Query(24, ge=1, le=168, description="Time period in hours"),
    event_service: EventService = Depends(get_event_service)
):
    """Get system health summary based on events"""
    try:
        health_summary = await event_service.get_system_health_summary(
            channel_id=channel_id,
            hours=hours
        )
        
        return SystemHealthResponse(
            health_status=health_summary["health_status"],
            error_rate_percentage=health_summary["error_rate_percentage"],
            total_events=health_summary["total_events"],
            error_count=health_summary["error_count"],
            stats=health_summary["stats"],
            recent_errors=[
                EventResponse.model_validate(event) 
                for event in health_summary["recent_errors"]
            ],
            check_timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Failed to get system health summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate health summary")


# Metrics and System Health

@router.get("/metrics", response_model=MetricsResponse)
async def get_current_metrics(
    metrics_service: MetricsCollectionService = Depends(get_metrics_service)
):
    """Get current system and application metrics"""
    try:
        metrics = await metrics_service.collect_comprehensive_metrics()
        
        return MetricsResponse(
            system=metrics["system"],
            application=metrics["application"],
            collection_timestamp=datetime.fromisoformat(metrics["collection_timestamp"])
        )
        
    except Exception as e:
        logger.error(f"Failed to collect metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to collect metrics")


@router.get("/health/system", response_model=SystemHealthCheckResponse)
async def check_system_health(
    metrics_service: MetricsCollectionService = Depends(get_metrics_service)
):
    """Perform comprehensive system health check"""
    try:
        health_check = await metrics_service.check_system_health()
        
        return SystemHealthCheckResponse(
            health_status=health_check["health_status"],
            issues=health_check["issues"],
            metrics=health_check["metrics"],
            check_timestamp=datetime.fromisoformat(health_check["check_timestamp"])
        )
        
    except Exception as e:
        logger.error(f"Failed to check system health: {e}")
        raise HTTPException(status_code=500, detail="Failed to check system health")


@router.get("/health/application", response_model=ApplicationHealthCheckResponse)
async def check_application_health(
    metrics_service: MetricsCollectionService = Depends(get_metrics_service)
):
    """Check application-specific health metrics"""
    try:
        health_check = await metrics_service.check_application_health()
        
        return ApplicationHealthCheckResponse(
            health_status=health_check["health_status"],
            issues=health_check["issues"],
            metrics=health_check["metrics"],
            event_summary=health_check["event_summary"],
            check_timestamp=datetime.fromisoformat(health_check["check_timestamp"])
        )
        
    except Exception as e:
        logger.error(f"Failed to check application health: {e}")
        raise HTTPException(status_code=500, detail="Failed to check application health")


@router.get("/metrics/report", response_model=MetricsReportResponse)
async def generate_metrics_report(
    include_history_hours: int = Query(24, ge=1, le=168, description="Hours of history to include"),
    metrics_service: MetricsCollectionService = Depends(get_metrics_service)
):
    """Generate comprehensive metrics report"""
    try:
        report = await metrics_service.generate_metrics_report(
            include_history_hours=include_history_hours
        )
        
        return MetricsReportResponse(**report)
        
    except Exception as e:
        logger.error(f"Failed to generate metrics report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate metrics report")


# Bulk Operations

@router.put("/bulk/status", response_model=BulkEventStatusUpdateResponse)
async def bulk_update_event_status(
    update_data: BulkEventStatusUpdate,
    event_service: EventService = Depends(get_event_service)
):
    """Bulk update event status"""
    try:
        updated_count = await event_service.bulk_update_event_status(
            event_ids=update_data.event_ids,
            status=update_data.status
        )
        
        return BulkEventStatusUpdateResponse(
            updated_count=updated_count,
            event_ids=update_data.event_ids
        )
        
    except Exception as e:
        logger.error(f"Failed to bulk update event status: {e}")
        raise HTTPException(status_code=500, detail="Failed to bulk update events")


# Maintenance Operations

@router.post("/cleanup", response_model=EventCleanupResponse)
async def cleanup_old_events(
    cleanup_data: EventCleanupRequest,
    event_service: EventService = Depends(get_event_service)
):
    """Clean up old events to manage database size"""
    try:
        deleted_count = await event_service.cleanup_old_events(
            older_than_hours=cleanup_data.older_than_hours,
            severity_threshold=cleanup_data.severity_threshold,
            dry_run=cleanup_data.dry_run
        )
        
        return EventCleanupResponse(
            deleted_count=deleted_count,
            dry_run=cleanup_data.dry_run,
            cleanup_timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Failed to cleanup events: {e}")
        raise HTTPException(status_code=500, detail="Failed to cleanup events")


@router.get("/stale", response_model=StaleEventCheckResponse)
async def check_stale_events(
    max_age_hours: int = Query(24, ge=1, le=168, description="Maximum age in hours"),
    event_service: EventService = Depends(get_event_service)
):
    """Find potentially stale events that need attention"""
    try:
        stale_events = await event_service.find_stale_events(
            max_age_hours=max_age_hours,
            status_filter=[EventStatus.IN_PROGRESS, EventStatus.STARTED]
        )
        
        return StaleEventCheckResponse(
            stale_events=[EventResponse.model_validate(event) for event in stale_events],
            stale_count=len(stale_events),
            max_age_hours=max_age_hours,
            check_timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Failed to check stale events: {e}")
        raise HTTPException(status_code=500, detail="Failed to check stale events")


@router.post("/stale/mark-failed", response_model=SuccessResponse)
async def mark_stale_events_failed(
    max_age_hours: int = Query(24, ge=1, le=168, description="Maximum age in hours"),
    event_service: EventService = Depends(get_event_service)
):
    """Mark stale in-progress events as failed"""
    try:
        failed_count = await event_service.mark_stale_events_as_failed(
            max_age_hours=max_age_hours
        )
        
        return SuccessResponse(
            message=f"Marked {failed_count} stale events as failed"
        )
        
    except Exception as e:
        logger.error(f"Failed to mark stale events as failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark stale events as failed")