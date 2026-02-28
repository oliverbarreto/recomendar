# LabCastARR Logging System Developer Guide

This guide provides comprehensive documentation for developers on the LabCastARR logging system - what gets logged, how to use it, and how it helps with operations and troubleshooting.

## 🏗️ Architecture Overview

The LabCastARR logging system is a **multi-layer, production-ready logging architecture** that combines:

- **Technical Logging**: Traditional application logs for debugging and system monitoring
- **Business Event Tracking**: User actions and business operations stored as Event entities
- **Performance Monitoring**: Request timing, slow operation detection, and bottleneck analysis
- **Security & Privacy**: Automatic sensitive data sanitization and audit trails

### Key Components

1. **Central Logging Configuration** (`app/core/logging.py`)
2. **Request Middleware** (`app/core/middleware/logging_middleware.py`)
3. **Logging Service** (`app/infrastructure/services/logging_service.py`)
4. **Event System Integration** (business event tracking)
5. **Configuration Management** (environment-specific settings)

---

## 📊 What Gets Logged Automatically

### HTTP Request/Response Logging
Every API request automatically logs:
```json
{
  "timestamp": "2025-09-28T10:30:15Z",
  "level": "info",
  "message": "Request completed",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "method": "POST",
  "path": "/v1/episodes",
  "status_code": 201,
  "processing_time_ms": 245.67,
  "client_ip": "192.168.1.100",
  "user_id": 1,
  "user_agent": "Mozilla/5.0..."
}
```

### User Action Events
All authenticated user actions create database Event records:
```python
# Automatically created for:
# - POST /v1/episodes (create_episode)
# - DELETE /v1/episodes/123 (delete_episode)
# - PUT /v1/channels/1 (update_channel)
# - POST /v1/auth/login (login)
# - POST /v1/auth/logout (logout)
```

### System Events
Application lifecycle and system operations:
```json
{
  "message": "LabCastARR application starting",
  "environment": "production",
  "version": "0.1.0",
  "database_url": "sqlite:///./data/labcastarr.db",
  "api_key_configured": true
}
```

### Performance Monitoring
- **Slow Requests**: Automatically flagged when > 1 second
- **External API Calls**: YouTube API timing and success rates
- **Database Operations**: Query performance and connection health

### Error Tracking
- **Exception Details**: Full stack traces with context
- **Error Context**: User, request, and system state when error occurred
- **Recovery Attempts**: Retry logic and fallback execution

---

## 🔧 How to Use the Logging System

### 1. Standard Python Logging (Backwards Compatible)
```python
import logging

# This still works exactly as before
logger = logging.getLogger(__name__)
logger.info("Episode processing started")
logger.error("Failed to download audio", exc_info=True)
```

### 2. Structured Logging (Recommended)
```python
from app.core.logging import get_structured_logger

structured_logger = get_structured_logger("downloader")

# Rich contextual logging
structured_logger.info(
    "Episode download completed",
    episode_id=123,
    file_size_mb=45.2,
    duration_seconds=1800,
    video_url="https://youtube.com/watch?v=abc123"
)
```

### 3. Specialized Logger Functions
```python
from app.core.logging import (
    get_api_logger,
    get_downloader_logger,
    get_rss_logger,
    get_database_logger,
    get_auth_logger,
    get_system_logger
)

# Use specialized loggers for different components
api_logger = get_api_logger()
downloader_logger = get_downloader_logger()
rss_logger = get_rss_logger()
```

### 4. Business Event Logging
```python
from app.application.services.event_service import EventService
from app.domain.entities.event import EventSeverity

# For explicit business event tracking
event_service = EventService(db_session)

await event_service.log_user_action(
    channel_id=1,
    user_id=123,
    action="create_episode",
    resource_type="episode",
    resource_id="456",
    message="User created new episode from YouTube video",
    details={
        "video_url": "https://youtube.com/watch?v=abc123",
        "processing_time_ms": 2500
    },
    severity=EventSeverity.INFO,
    ip_address="192.168.1.100",
    user_agent="Mozilla/5.0..."
)
```

### 5. Application-Level Logging
```python
from app.infrastructure.services.logging_service import logging_service

# Database operations
await logging_service.log_database_operation(
    operation="insert",
    table="episodes",
    duration_ms=15.3,
    success=True,
    details={"episode_id": 123, "channel_id": 1}
)

# External API calls
await logging_service.log_external_api_call(
    service="youtube",
    endpoint="https://www.youtube.com/watch?v=abc123",
    method="GET",
    status_code=200,
    duration_ms=850.5,
    success=True,
    request_details={"operation": "metadata_extraction"}
)

# Error reporting with context
await logging_service.log_error_with_context(
    error=exception,
    context={
        "episode_id": 123,
        "user_id": 1,
        "operation": "audio_download"
    }
)
```

---

## 🎬 Episode Lifecycle Event Tracking

The system provides comprehensive business event tracking for the complete episode creation process, from initial download through RSS feed generation.

### Download Progress Events

The enhanced `DownloadProgress` class automatically emits business events at key milestones:

```python
from app.infrastructure.services.download_service import DownloadService
from app.application.services.event_service import EventService

# Initialize download service with event tracking
download_service = DownloadService()

# Queue download with user context for event tracking
await download_service.queue_download(
    episode_id=123,
    background_tasks=background_tasks,
    user_id=456,
    channel_id=1,
    event_service=event_service
)

# Events automatically emitted:
# 1. download_started - Episode queued for processing
# 2. download_progress - Progress milestones (25%, 50%, 75%, 100%)
# 3. download_completed - Audio file ready
# 4. download_failed - Download error with context
```

### Progress Milestone Event Example
```json
{
  "action": "download_progress",
  "resource_type": "episode",
  "resource_id": "123",
  "message": "Episode download reached 50% completion",
  "details": {
    "milestone_percentage": 50,
    "download_speed": "2.5MB/s",
    "eta": "00:02:30",
    "downloaded_bytes": 15728640,
    "total_bytes": 31457280,
    "status": "processing"
  },
  "severity": "INFO",
  "user_id": 456,
  "channel_id": 1,
  "created_at": "2025-09-28T10:30:15Z"
}
```

### RSS Generation Events

The `FeedGenerationServiceImpl` tracks RSS feed creation and episode processing:

```python
from app.infrastructure.services.feed_generation_service_impl import FeedGenerationServiceImpl

# Create service with event tracking
feed_service = FeedGenerationServiceImpl(
    event_service=event_service,
    user_id=123,
    channel_id=1
)

# Generate RSS with automatic event tracking
try:
    rss_xml = feed_service.generate_rss_feed(channel, episodes, base_url)
    # Events emitted:
    # - rss_generation_started
    # - rss_generation_completed (with feed size)
    # - rss_episode_creation_failed (per failed episode)
except Exception as e:
    # Event emitted:
    # - rss_generation_failed (with error details)
    pass
```

### RSS Generation Event Example
```json
{
  "action": "rss_generation_completed",
  "resource_type": "channel",
  "resource_id": "1",
  "message": "RSS feed generation completed for channel 'My Podcast'",
  "details": {
    "channel_id": 1,
    "channel_name": "My Podcast",
    "episode_count": 25,
    "completed_episodes": 23,
    "feed_size_bytes": 45678
  },
  "severity": "INFO",
  "user_id": 123,
  "channel_id": 1
}
```

### Complete Episode Lifecycle Flow

```python
async def create_episode_with_full_tracking(
    video_url: str,
    channel_id: int,
    user_id: int,
    event_service: EventService
):
    """Complete episode creation with business event tracking"""

    # 1. Episode entity creation (via API middleware)
    # Event: create_episode

    # 2. Download tracking
    download_service = DownloadService()
    await download_service.queue_download(
        episode_id=episode.id,
        background_tasks=background_tasks,
        user_id=user_id,
        channel_id=channel_id,
        event_service=event_service
    )
    # Events: download_started -> download_progress (25%, 50%, 75%, 100%) -> download_completed

    # 3. RSS generation
    feed_service = FeedGenerationServiceImpl(
        event_service=event_service,
        user_id=user_id,
        channel_id=channel_id
    )
    rss_xml = feed_service.generate_rss_feed(channel, episodes, base_url)
    # Events: rss_generation_started -> rss_generation_completed

    # Complete audit trail from user action to final RSS feed
```

---

## 📂 Log Categories and Levels

### Logger Categories
The system uses hierarchical logger names for organization:

- **`labcastarr.api`** - HTTP requests, responses, middleware
- **`labcastarr.downloader`** - YouTube downloads, media processing
- **`labcastarr.processor`** - Audio conversion, file processing
- **`labcastarr.rss`** - RSS feed generation, XML processing
- **`labcastarr.database`** - Database operations, migrations
- **`labcastarr.auth`** - Authentication, JWT operations
- **`labcastarr.system`** - Application lifecycle, health checks

### Log Levels by Environment

**Development:**
- **Level**: DEBUG (shows everything)
- **Output**: Colorized console with human-readable format
- **File Logging**: Disabled by default

**Production:**
- **Level**: INFO (focuses on important events)
- **Output**: Structured JSON logs + rotating file logs
- **File Logging**: Enabled with rotation (10MB max, 5 backups)

### Event Types
Business events are categorized as:
- **USER_ACTION** - User-initiated operations (create/update/delete, login/logout)
- **EPISODE_LIFECYCLE** - Download and RSS generation events (download_progress, rss_generation_*)
- **SYSTEM_EVENT** - Automated system operations (background tasks, health checks)
- **PERFORMANCE_EVENT** - Performance metrics and alerts (slow requests, milestone timing)
- **SECURITY_EVENT** - Authentication, authorization events (failed logins, access violations)

### Episode-Specific Event Actions
- `download_started` - Episode queued for download
- `download_progress` - Progress milestone reached (25%, 50%, 75%, 100%)
- `download_completed` - Audio file successfully downloaded
- `download_failed` - Download error with detailed context
- `rss_generation_started` - RSS feed generation begins
- `rss_generation_completed` - RSS feed successfully created
- `rss_generation_failed` - RSS generation error
- `rss_episode_creation_failed` - Individual episode creation failure during RSS generation

---

## ⚙️ Configuration Options

### Environment Variables
```bash
# Logging Configuration
LOG_LEVEL=INFO                          # DEBUG, INFO, WARNING, ERROR
LOG_FILE_PATH=./logs/labcastarr.log      # Log file location
LOG_MAX_FILE_SIZE=10                     # MB before rotation
LOG_BACKUP_COUNT=5                       # Number of backup files
ENABLE_FILE_LOGGING=true                 # Enable/disable file logging
ENABLE_REQUEST_LOGGING=true              # HTTP request/response logging
ENABLE_PERFORMANCE_LOGGING=true          # Slow request detection
LOG_SQL_QUERIES=false                    # Database query logging (debug)
```

### Development vs Production Defaults

**Development (`ENVIRONMENT=development`):**
```python
LOG_LEVEL=DEBUG
ENABLE_FILE_LOGGING=false    # Console only
ENABLE_REQUEST_LOGGING=true
LOG_FORMAT="human_readable"  # Colorized console output
```

**Production (`ENVIRONMENT=production`):**
```python
LOG_LEVEL=INFO
ENABLE_FILE_LOGGING=true     # File + console
ENABLE_REQUEST_LOGGING=true
LOG_FORMAT="json"            # Structured JSON logs
```

### Docker Configuration
```yaml
# docker-compose.prod.yml
environment:
  - LOG_LEVEL=INFO
  - ENABLE_FILE_LOGGING=true
  - ENABLE_REQUEST_LOGGING=true
volumes:
  - ./backend/logs:/app/logs  # Persist logs outside container
```

---

## 🔍 Operations and Troubleshooting

### Correlation ID Tracing
Every request gets a unique correlation ID for tracing across components:

```bash
# Find all logs for a specific request
grep "550e8400-e29b-41d4-a716-446655440000" logs/labcastarr.log

# Response headers include correlation ID
X-Correlation-ID: 550e8400-e29b-41d4-a716-446655440000
```

### Performance Analysis

**Identifying Slow Requests:**
```bash
# Find requests taking > 1 second
grep "Slow request detected" logs/labcastarr.log

# JSON query for slow requests
jq 'select(.message == "Slow request detected")' logs/labcastarr.log
```

**YouTube API Performance:**
```bash
# Check YouTube API response times
grep "youtube.*duration_ms" logs/labcastarr.log | jq '.duration_ms'
```

### Error Investigation

**Finding Errors with Context:**
```bash
# All errors with stack traces
grep -A 10 '"level":"error"' logs/labcastarr.log

# Errors for specific user
jq 'select(.level == "error" and .user_id == 123)' logs/labcastarr.log

# Database-related errors
grep '"table":"' logs/labcastarr.log | grep '"success":false'
```

**Common Error Patterns:**
```python
# Database connection issues
"Database operation failed"

# YouTube API problems
"Failed to extract metadata"

# Authentication failures
"Authentication required"

# File system issues
"Failed to save media file"
```

### User Activity Analysis

**User Behavior Tracking:**
```bash
# All actions by user
jq 'select(.user_id == 123)' logs/labcastarr.log

# Episode creation patterns
grep "create_episode" logs/labcastarr.log

# Login/logout activity
grep "login\|logout" logs/labcastarr.log
```

### Episode Lifecycle Monitoring
**Log File Queries:**
```bash
# Track complete episode lifecycle
jq 'select(.action | test("download_|rss_")) | {action, episode_id: .resource_id, timestamp: .created_at}' logs/labcastarr.log

# Monitor download performance
jq 'select(.action == "download_progress") | {episode_id: .resource_id, percentage: .details.milestone_percentage, speed: .details.download_speed}' logs/labcastarr.log

# Find RSS generation failures
jq 'select(.action == "rss_generation_failed") | {channel_id: .resource_id, error: .details.error_message, timestamp: .created_at}' logs/labcastarr.log

# Track episode completion rates
jq 'select(.action == "download_completed") | {episode_id: .resource_id, duration: .details.download_duration_seconds, size: .details.total_bytes}' logs/labcastarr.log
```

**Event Database Queries:**
```sql
-- Most active users
SELECT user_id, COUNT(*) as action_count
FROM events
WHERE event_type = 'USER_ACTION'
GROUP BY user_id
ORDER BY action_count DESC;

-- Episode download success rate by user
SELECT
    user_id,
    COUNT(CASE WHEN action = 'download_completed' THEN 1 END) as completed,
    COUNT(CASE WHEN action = 'download_failed' THEN 1 END) as failed,
    ROUND(COUNT(CASE WHEN action = 'download_completed' THEN 1 END) * 100.0 /
          (COUNT(CASE WHEN action = 'download_completed' THEN 1 END) +
           COUNT(CASE WHEN action = 'download_failed' THEN 1 END)), 2) as success_rate
FROM events
WHERE action IN ('download_completed', 'download_failed')
GROUP BY user_id;

-- RSS generation performance metrics
SELECT
    DATE(created_at) as date,
    COUNT(CASE WHEN action = 'rss_generation_completed' THEN 1 END) as successful,
    COUNT(CASE WHEN action = 'rss_generation_failed' THEN 1 END) as failed,
    AVG(CAST(JSON_EXTRACT(details, '$.feed_size_bytes') AS INTEGER)) as avg_feed_size
FROM events
WHERE action LIKE 'rss_generation_%'
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Recent episode processing events
SELECT action, resource_id as episode_id, message, created_at
FROM events
WHERE action LIKE 'download_%' OR action LIKE 'rss_%'
AND created_at > datetime('now', '-1 hour')
ORDER BY created_at DESC;
```

---

## 🔒 Security and Privacy

### Automatic Sensitive Data Sanitization
The system automatically redacts sensitive information:

```python
# These fields are automatically sanitized:
SENSITIVE_FIELDS = [
    'password', 'token', 'api_key', 'secret',
    'auth', 'authorization', 'x-api-key',
    'jwt', 'access_token', 'refresh_token'
]

# Before sanitization:
"Authorization: Bearer abc123xyz789"

# After sanitization:
"Authorization: Bearer [REDACTED]"
```

### User Context Logging
User information is safely captured and logged:

```json
{
  "user_id": 123,
  "user_email": "[REDACTED]",  // Email is sanitized in logs
  "action": "create_episode",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "timestamp": "2025-09-28T10:30:15Z"
}
```

### Audit Trail
Complete record of user actions for compliance:

- **Authentication Events**: Login/logout with IP and device info
- **Resource Changes**: Create/update/delete operations with timestamps
- **Data Access**: Episode streaming, RSS feed access
- **Administrative Actions**: User management, system configuration

---

## 📈 Performance Impact

### Logging Overhead
- **Request Logging**: ~1-2ms overhead per request
- **Event Creation**: ~5-10ms for database writes
- **File I/O**: Asynchronous, minimal blocking
- **Memory Usage**: Structured logging uses ~10-20MB additional RAM

### Optimization Features
- **Configurable Levels**: Disable debug logging in production
- **Selective Logging**: Skip health checks and static assets
- **Async Operations**: Non-blocking event creation
- **Log Rotation**: Prevents disk space issues

---

## 🚀 Advanced Usage Examples

### Custom Performance Monitoring
```python
import time
from app.core.logging import get_structured_logger

logger = get_structured_logger("custom")

# Time expensive operations
start_time = time.time()
result = expensive_operation()
duration_ms = (time.time() - start_time) * 1000

logger.info(
    "Custom operation completed",
    operation="expensive_calculation",
    duration_ms=duration_ms,
    result_size=len(result),
    cache_hit=False
)
```

### Background Task Logging
```python
from app.infrastructure.services.logging_service import logging_service

async def background_download_task(episode_id: int):
    try:
        # Log task start
        await logging_service.log_background_task(
            task_name="episode_download",
            task_id=f"episode_{episode_id}",
            status="started",
            details={"episode_id": episode_id}
        )

        # Perform download...

        # Log task completion
        await logging_service.log_background_task(
            task_name="episode_download",
            task_id=f"episode_{episode_id}",
            status="completed",
            duration_ms=download_time,
            details={
                "episode_id": episode_id,
                "file_size_mb": file_size
            }
        )

    except Exception as e:
        await logging_service.log_background_task(
            task_name="episode_download",
            task_id=f"episode_{episode_id}",
            status="failed",
            error_message=str(e),
            details={"episode_id": episode_id}
        )
```

### Security Event Logging
```python
from app.core.logging import get_auth_logger
from app.domain.entities.event import EventSeverity

auth_logger = get_auth_logger()

# Failed login attempts
auth_logger.warning(
    "Failed login attempt",
    email=email,
    ip_address=client_ip,
    user_agent=user_agent,
    failure_reason="invalid_password"
)

# Suspicious activity
await event_service.log_security_event(
    event_type="multiple_failed_logins",
    severity=EventSeverity.WARNING,
    details={
        "ip_address": client_ip,
        "attempt_count": 5,
        "time_window_minutes": 10
    }
)
```

### Episode Lifecycle Integration Example
```python
from app.infrastructure.services.download_service import DownloadService
from app.infrastructure.services.feed_generation_service_impl import FeedGenerationServiceImpl
from app.application.services.event_service import EventService
from app.core.logging import get_structured_logger

logger = get_structured_logger("episode_lifecycle")

async def create_episode_with_full_tracking(
    video_url: str,
    channel_id: int,
    user_id: int,
    session: AsyncSession
) -> Episode:
    """Complete episode creation with comprehensive event tracking"""

    # Initialize services with event tracking
    event_service = EventService(session)
    download_service = DownloadService()

    try:
        # 1. Create episode entity (logged via API middleware)
        episode = await episode_service.create_episode(
            video_url=video_url,
            channel_id=channel_id,
            user_id=user_id
        )

        # 2. Queue download with business event tracking
        success = await download_service.queue_download(
            episode_id=episode.id,
            background_tasks=background_tasks,
            user_id=user_id,
            channel_id=channel_id,
            event_service=event_service
        )

        if not success:
            logger.warning(
                "Failed to queue episode download",
                episode_id=episode.id,
                user_id=user_id,
                video_url=video_url
            )
            return episode

        # Events automatically emitted during download:
        # - download_started (immediate)
        # - download_progress (25%, 50%, 75%, 100%)
        # - download_completed or download_failed

        # 3. RSS generation (typically triggered after download completion)
        feed_service = FeedGenerationServiceImpl(
            event_service=event_service,
            user_id=user_id,
            channel_id=channel_id
        )

        # Get updated episodes list for RSS generation
        episodes = await episode_repository.get_published_by_channel_id(channel_id)
        channel = await channel_repository.get_by_id(channel_id)

        # Generate RSS with automatic event tracking
        rss_xml = feed_service.generate_rss_feed(
            channel=channel,
            episodes=episodes,
            base_url="https://api.labcastarr.com"
        )

        # Events automatically emitted:
        # - rss_generation_started
        # - rss_generation_completed (with feed metrics)
        # - rss_episode_creation_failed (if any episodes fail)

        logger.info(
            "Episode creation lifecycle completed",
            episode_id=episode.id,
            user_id=user_id,
            channel_id=channel_id,
            rss_feed_size=len(rss_xml.encode('utf-8'))
        )

        return episode

    except Exception as e:
        logger.error(
            "Episode creation lifecycle failed",
            episode_id=getattr(episode, 'id', None),
            user_id=user_id,
            channel_id=channel_id,
            error_type=type(e).__name__,
            error_message=str(e),
            exc_info=True
        )
        raise
```

---

## 🎯 Best Practices

### DO:
- Use structured logging for new code
- Include relevant context in log messages (user_id, episode_id, channel_id)
- Use appropriate log levels (DEBUG for detailed info, INFO for important events)
- Log user actions that modify data
- Include timing information for performance analysis
- Pass EventService to services that need business event tracking
- Emit milestone events for long-running operations (downloads, RSS generation)

### DON'T:
- Log sensitive data directly (use sanitization)
- Use DEBUG level in production
- Log in tight loops without throttling
- Include large objects in log messages
- Ignore correlation IDs in debugging

### Example: Good Logging Practice
```python
from app.core.logging import get_structured_logger

logger = get_structured_logger("episode_processor")

async def process_episode(episode_id: int, user_id: int):
    start_time = time.time()

    try:
        logger.info(
            "Episode processing started",
            episode_id=episode_id,
            user_id=user_id,
            operation="process_episode"
        )

        # Processing logic...

        processing_time = (time.time() - start_time) * 1000

        logger.info(
            "Episode processing completed successfully",
            episode_id=episode_id,
            user_id=user_id,
            processing_time_ms=processing_time,
            file_size_mb=result.file_size,
            operation="process_episode"
        )

        return result

    except Exception as e:
        processing_time = (time.time() - start_time) * 1000

        logger.error(
            "Episode processing failed",
            episode_id=episode_id,
            user_id=user_id,
            processing_time_ms=processing_time,
            error_type=type(e).__name__,
            error_message=str(e),
            operation="process_episode",
            exc_info=True  # Include stack trace
        )

        raise
```

---

This logging system provides comprehensive visibility into your LabCastARR application, enabling effective debugging, performance optimization, security monitoring, and user behavior analysis.