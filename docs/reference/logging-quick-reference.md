# LabCastARR Logging Quick Reference

## 🚀 Quick Start

```python
# Standard logging (backwards compatible)
import logging
logger = logging.getLogger(__name__)
logger.info("Something happened")

# Structured logging (recommended)
from app.core.logging import get_structured_logger
logger = get_structured_logger("module_name")
logger.info("Event occurred", user_id=123, duration_ms=250)
```

## 📊 What Gets Logged Automatically

- ✅ **HTTP Requests/Responses** (method, path, status, timing, user)
- ✅ **User Actions** (login/logout, create/update/delete operations)
- ✅ **Episode Lifecycle** (download start/progress/completion, RSS generation)
- ✅ **System Events** (startup/shutdown, database ops, external APIs)
- ✅ **Performance** (slow requests >1s, API response times)
- ✅ **Errors** (exceptions with full context and stack traces)

## 🔧 Common Patterns

### Basic Structured Logging
```python
from app.core.logging import get_structured_logger
logger = get_structured_logger("episodes")

logger.info(
    "Episode created",
    episode_id=123,
    user_id=456,
    video_url="https://youtube.com/...",
    processing_time_ms=1250
)
```

### Error Logging with Context
```python
try:
    # risky operation
    result = download_video()
except Exception as e:
    logger.error(
        "Download failed",
        episode_id=123,
        error_type=type(e).__name__,
        error_message=str(e),
        exc_info=True  # Include stack trace
    )
```

### Performance Monitoring
```python
import time
start = time.time()
# expensive operation
duration_ms = (time.time() - start) * 1000

logger.info(
    "Operation completed",
    operation="video_processing",
    duration_ms=duration_ms,
    success=True
)
```

### User Action Events
```python
from app.application.services.event_service import EventService
event_service = EventService(db_session)

await event_service.log_user_action(
    channel_id=1,
    user_id=123,
    action="create_episode",
    resource_type="episode",
    message="User created episode from YouTube video",
    ip_address=client_ip
)
```

## 🎬 Episode Lifecycle Events

### Download Progress Tracking
```python
from app.infrastructure.services.download_service import DownloadService

# Events are emitted automatically during download:
# - download_started (when queued)
# - download_progress (25%, 50%, 75%, 100%)
# - download_completed (audio ready)
# - download_failed (on errors)

download_service = DownloadService()
await download_service.queue_download(
    episode_id=123,
    background_tasks=background_tasks,
    user_id=456,
    channel_id=1,
    event_service=event_service
)
```

### RSS Generation Events
```python
from app.infrastructure.services.feed_generation_service_impl import FeedGenerationServiceImpl

# Create service with event tracking
feed_service = FeedGenerationServiceImpl(
    event_service=event_service,
    user_id=123,
    channel_id=1
)

# Events emitted automatically:
# - rss_generation_started
# - rss_generation_completed
# - rss_generation_failed
# - rss_episode_creation_failed (per episode)
rss_xml = feed_service.generate_rss_feed(channel, episodes, base_url)
```

## 📂 Specialized Loggers

```python
from app.core.logging import (
    get_api_logger,        # HTTP/API operations
    get_downloader_logger, # YouTube downloads
    get_rss_logger,        # RSS feed generation
    get_database_logger,   # Database operations
    get_auth_logger,       # Authentication
    get_system_logger      # System events
)
```

## ⚙️ Configuration

### Environment Variables
```bash
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR
ENABLE_FILE_LOGGING=true          # Log to files
ENABLE_REQUEST_LOGGING=true       # HTTP request logging
ENABLE_PERFORMANCE_LOGGING=true   # Slow request detection
LOG_SQL_QUERIES=false            # Database query logging
```

### Development vs Production
- **Development**: DEBUG level, colorized console only
- **Production**: INFO level, JSON logs + rotating files

## 🔍 Troubleshooting

### Find Logs by Correlation ID
```bash
grep "550e8400-e29b-41d4-a716-446655440000" logs/labcastarr.log
```

### Slow Requests
```bash
grep "Slow request detected" logs/labcastarr.log
```

### User Activity
```bash
jq 'select(.user_id == 123)' logs/labcastarr.log
```

### Errors with Context
```bash
jq 'select(.level == "error")' logs/labcastarr.log
```

### Episode Lifecycle Events
```bash
# Find all download progress for specific episode
jq 'select(.action | test("download_"))' logs/labcastarr.log

# Monitor RSS generation failures
jq 'select(.action == "rss_generation_failed")' logs/labcastarr.log

# Track episode completion rates
jq 'select(.action == "download_completed")' logs/labcastarr.log

# Find failed downloads by user
jq 'select(.action == "download_failed" and .user_id == 123)' logs/labcastarr.log
```

## 🔒 Security Features

- **Automatic Sanitization**: Passwords, tokens, API keys → `[REDACTED]`
- **User Context**: Safe logging of user actions with IP/device info
- **Audit Trail**: Complete record of who did what when

## 📈 Performance Impact

- **Request Logging**: ~1-2ms overhead
- **Event Creation**: ~5-10ms for database writes
- **Memory**: ~10-20MB additional RAM
- **Async**: Non-blocking operations

## 🎯 Best Practices

### ✅ DO
- Use structured logging for new code
- Include relevant context (user_id, episode_id, etc.)
- Log performance-critical operations with timing
- Use appropriate log levels

### ❌ DON'T
- Log sensitive data directly
- Use DEBUG in production
- Log in tight loops
- Ignore correlation IDs when debugging

## 📍 File Locations

- **Config**: `app/core/logging.py`
- **Middleware**: `app/core/middleware/logging_middleware.py`
- **Service**: `app/infrastructure/services/logging_service.py`
- **Logs**: `backend/logs/labcastarr.log` (production)

---

For complete documentation, see: [Logging System Developer Guide](./logging-system-developer-guide.md)