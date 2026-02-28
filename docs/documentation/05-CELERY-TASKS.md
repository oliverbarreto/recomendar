# LabCastARR Celery Background Tasks

**Document Version:** 1.0
**Last Updated:** 2026-01-29

---

## Table of Contents

1. [Overview](#overview)
2. [Celery Configuration](#celery-configuration)
3. [Task Reference](#task-reference)
4. [Task Workflows](#task-workflows)
5. [Scheduled Tasks](#scheduled-tasks)
6. [Error Handling](#error-handling)
7. [Monitoring and Status](#monitoring-and-status)
8. [Development Notes](#development-notes)

---

## Overview

LabCastARR uses **Celery** with **Redis** as the message broker for background task processing. This enables:

- Non-blocking API responses for long-running operations
- Scheduled periodic tasks (video discovery)
- Retry mechanisms for failed operations
- Progress tracking and status reporting

### Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   FastAPI   │────▶│    Redis    │────▶│   Celery    │
│   Backend   │     │   Broker    │     │   Worker    │
└─────────────┘     └─────────────┘     └─────────────┘
       │                                       │
       │                                       │
       ▼                                       ▼
┌─────────────┐                         ┌─────────────┐
│  SQLite DB  │◀────────────────────────│  External   │
│             │                         │  Services   │
└─────────────┘                         │  (yt-dlp)   │
                                        └─────────────┘
```

### Services

| Service | Purpose | Docker Container |
|---------|---------|------------------|
| Redis | Message broker & result backend | `redis-prod` / `redis-dev` |
| Celery Worker | Task execution | `celery-worker-prod` / `celery-worker-dev` |
| Celery Beat | Scheduled task scheduler | `celery-beat-prod` / `celery-beat-dev` |

---

## Celery Configuration

### Application Setup

**File:** `backend/app/infrastructure/celery_app.py`

```python
from celery import Celery
from app.core.config import settings

redis_url = settings.redis_url  # redis://redis:6379/0

celery_app = Celery(
    "labcastarr",
    broker=redis_url,
    backend=redis_url,
    include=[
        "app.infrastructure.tasks.channel_check_tasks",
        "app.infrastructure.tasks.channel_check_rss_tasks",
        "app.infrastructure.tasks.download_episode_task",
        "app.infrastructure.tasks.create_episode_from_video_task",
        "app.infrastructure.tasks.backfill_channel_task",
    ]
)

# Configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,      # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)
```

### Beat Schedule

**File:** `backend/app/infrastructure/celery_beat_schedule.py`

```python
from celery.schedules import crontab

beat_schedule = {
    "scheduled-channel-check-rss": {
        "task": "app.infrastructure.tasks.channel_check_rss_tasks.scheduled_check_all_channels_rss",
        "schedule": crontab(minute="*/30"),  # Every 30 minutes
        "options": {"queue": "channel_checks"},
    }
}
```

---

## Task Reference

### 1. Channel Check Task (yt-dlp Method)

**File:** `backend/app/infrastructure/tasks/channel_check_tasks.py`

**Task Name:** `check_followed_channel_for_new_videos`

**Purpose:** Comprehensive video discovery using yt-dlp

**Trigger:** Manual via API: `POST /v1/followed-channels/{id}/check`

**Duration:** 30-60 seconds per channel

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `followed_channel_id` | int | Channel to check |
| `user_id` | int | User who triggered check |

**Process:**
1. Create "search started" notification
2. Fetch channel from database
3. Use `YtdlpDiscoveryStrategy` to discover videos
4. Compare with existing videos in database
5. Save new videos with state `pending_review`
6. If auto-approve enabled, queue episode creation
7. Update `last_checked` timestamp
8. Create "search completed" notification

**Error Handling:**
- Auto-retry on `ConnectionError`, `TimeoutError`
- Max 3 retries with exponential backoff (60s, 120s, 600s)
- Creates "search error" notification on failure

```python
@celery_app.task(
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    retry_backoff=True,
    retry_backoff_max=600,
)
def check_followed_channel_for_new_videos(
    self,
    followed_channel_id: int,
    user_id: int
) -> dict:
    # Implementation
```

---

### 2. Channel Check RSS Task (Fast Method)

**File:** `backend/app/infrastructure/tasks/channel_check_rss_tasks.py`

**Task Name:** `check_followed_channel_for_new_videos_rss`

**Purpose:** Fast video discovery using YouTube RSS feeds

**Trigger:** Manual via API: `POST /v1/followed-channels/{id}/check-rss`

**Duration:** 5-10 seconds per channel

**Process:**
1. Create "search started" notification
2. Fetch YouTube RSS feed
3. Extract video IDs from feed (last 10-15 videos)
4. Check which videos are new (not in database)
5. Fetch metadata for new videos only using yt-dlp
6. Save new videos with state `pending_review`
7. If auto-approve enabled, queue episode creation
8. Create "search completed" notification

```python
@celery_app.task(bind=True)
def check_followed_channel_for_new_videos_rss(
    self,
    followed_channel_id: int,
    user_id: int
) -> dict:
    # Uses RSSDiscoveryStrategy
```

---

### 3. Scheduled Channel Check Task

**File:** `backend/app/infrastructure/tasks/channel_check_rss_tasks.py`

**Task Name:** `scheduled_check_all_channels_rss`

**Purpose:** Periodic check of all followed channels

**Trigger:** Celery Beat every 30 minutes

**Process:**
1. Query all followed channels
2. For each channel, queue individual RSS check task
3. Respect user settings (timezone, check frequency)

```python
@celery_app.task
def scheduled_check_all_channels_rss() -> dict:
    """
    Scheduled task that runs every 30 minutes.
    Checks all followed channels for new videos using RSS method.
    """
    channels = get_all_followed_channels()

    for channel in channels:
        check_followed_channel_for_new_videos_rss.delay(
            channel.id,
            channel.user_id
        )

    return {"channels_queued": len(channels)}
```

---

### 4. Download Episode Task

**File:** `backend/app/infrastructure/tasks/download_episode_task.py`

**Task Name:** `download_episode`

**Purpose:** Download audio from YouTube video

**Trigger:** Automatic after episode creation from YouTube URL

**Duration:** 1-5 minutes depending on video length

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `episode_id` | int | Episode to download |
| `user_id` | int | User who created episode |
| `channel_id` | int | Target channel |

**Process:**
1. Update task status to "STARTED"
2. Get episode from database
3. Update episode status to "processing"
4. Download audio using yt-dlp
5. Convert to MP3 if needed
6. Store in `media/channel_{id}/`
7. Update episode with file path, duration, size
8. Update episode status to "completed"
9. Regenerate RSS feed

**Error Handling:**
- Update episode status to "failed" on error
- Increment retry count
- Create error event log

```python
@celery_app.task(bind=True)
def download_episode(
    self,
    episode_id: int,
    user_id: int,
    channel_id: int
) -> dict:
    # Implementation using CeleryDownloadService
```

---

### 5. Create Episode from Video Task

**File:** `backend/app/infrastructure/tasks/create_episode_from_video_task.py`

**Task Name:** `create_episode_from_youtube_video`

**Purpose:** Create podcast episode from discovered YouTube video

**Trigger:**
- Manual via API: `POST /v1/youtube-videos/{id}/create-episode`
- Automatic via auto-approve workflow

**Process:**
1. Get YouTubeVideo from database
2. Update video state: `pending_review` → `queued`
3. Get FollowedChannel for channel context
4. Update video state: `queued` → `downloading`
5. Create Episode entity with video metadata
6. Save episode to database (status: `pending`)
7. Link episode_id to YouTubeVideo
8. Update video state: `downloading` → `episode_created`
9. Queue `download_episode` task
10. Create "episode created" notification

**State Transitions:**
```
YouTubeVideo: pending_review → queued → downloading → episode_created
Episode: pending → processing → completed (via download task)
```

```python
@celery_app.task(bind=True)
def create_episode_from_youtube_video(
    self,
    youtube_video_id: int,
    channel_id: int,
    user_id: int
) -> dict:
    # Implementation
```

---

### 6. Backfill Channel Task

**File:** `backend/app/infrastructure/tasks/backfill_channel_task.py`

**Task Name:** `backfill_followed_channel`

**Purpose:** Discover historical videos from YouTube channel

**Trigger:**
- Automatic on initial channel follow
- Manual via API: `POST /v1/followed-channels/{id}/backfill`

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `followed_channel_id` | int | - | Channel to backfill |
| `max_videos` | int | 20 | Maximum videos to fetch |
| `year` | int | current | Filter by year (optional) |

**Process:**
1. Get followed channel from database
2. Fetch videos from YouTube using yt-dlp
3. Filter by year if specified
4. Limit to max_videos
5. Check for existing videos in database
6. Save new videos with state `pending_review`

```python
@celery_app.task(bind=True)
def backfill_followed_channel(
    self,
    followed_channel_id: int,
    max_videos: int = 20,
    year: Optional[int] = None
) -> dict:
    # Implementation
```

---

## Task Workflows

### YouTube Episode Creation Workflow

```
User submits URL
       │
       ▼
┌─────────────────┐
│ POST /episodes  │
│ (sync response) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Episode created │
│ status: pending │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ download_episode.delay()│
│ (async task queued)     │
└────────────┬────────────┘
             │
             ▼
┌───────────────────────────────┐
│ Celery Worker picks up task   │
│ 1. Download audio (yt-dlp)    │
│ 2. Convert to MP3             │
│ 3. Save to media/             │
│ 4. Update episode metadata    │
│ 5. Regenerate RSS feed        │
└────────────┬──────────────────┘
             │
             ▼
┌─────────────────┐
│ Episode updated │
│ status: completed│
└─────────────────┘
```

### Video Discovery Workflow

```
┌──────────────────────────┐
│ Celery Beat (every 30m)  │
│ scheduled_check_all_...  │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│ Query all followed       │
│ channels from database   │
└────────────┬─────────────┘
             │
      ┌──────┴──────┐
      ▼             ▼
┌─────────┐   ┌─────────┐
│Channel 1│   │Channel 2│
└────┬────┘   └────┬────┘
     │              │
     ▼              ▼
┌──────────────────────────┐
│ RSS Check Task per       │
│ channel (parallel)       │
│                          │
│ 1. Fetch RSS feed        │
│ 2. Extract new video IDs │
│ 3. Fetch metadata        │
│ 4. Save to database      │
│ 5. Create notification   │
└────────────┬─────────────┘
             │
     ┌───────┴───────┐
     │               │
     ▼               ▼
┌─────────┐   ┌─────────────────┐
│ Auto-   │   │ Manual Review   │
│ Approve │   │ (pending_review)│
└────┬────┘   └─────────────────┘
     │
     ▼
┌──────────────────────────┐
│ create_episode_from_     │
│ youtube_video.delay()    │
└──────────────────────────┘
```

---

## Scheduled Tasks

### Celery Beat Schedule

| Task | Schedule | Purpose |
|------|----------|---------|
| `scheduled_check_all_channels_rss` | Every 30 minutes | Check all channels for new videos |

### Schedule Configuration

```python
# celery_beat_schedule.py
from celery.schedules import crontab

beat_schedule = {
    "scheduled-channel-check-rss": {
        "task": "app.infrastructure.tasks.channel_check_rss_tasks.scheduled_check_all_channels_rss",
        "schedule": crontab(minute="*/30"),
        "options": {
            "queue": "channel_checks",
            "expires": 1800,  # Expire after 30 minutes
        },
    }
}
```

### User Settings Integration

The scheduled task respects user preferences:

```python
# In scheduled_check_all_channels_rss
user_settings = get_user_settings(channel.user_id)

# Check if we should run based on user's preferred time
if should_check_now(user_settings.timezone, user_settings.check_time):
    check_followed_channel_for_new_videos_rss.delay(
        channel.id,
        channel.user_id
    )
```

---

## Error Handling

### Retry Configuration

```python
@celery_app.task(
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError, YouTubeError),
    retry_kwargs={
        'max_retries': 3,
        'countdown': 60,  # 60 seconds initial delay
    },
    retry_backoff=True,        # Exponential backoff
    retry_backoff_max=600,     # Max 10 minutes between retries
    retry_jitter=True,         # Add randomness to prevent thundering herd
)
def task_with_retries(self):
    try:
        # Task logic
    except Exception as e:
        # Log error
        raise self.retry(exc=e)
```

### Error Notifications

When tasks fail, notifications are created:

```python
@celery_app.task(bind=True)
def check_followed_channel_for_new_videos(self, channel_id, user_id):
    try:
        # Task logic
    except Exception as e:
        # Create error notification
        create_notification(
            user_id=user_id,
            type="channel_search_error",
            title="Search Failed",
            message=f"Failed to search channel: {str(e)}"
        )
        raise
```

### Task Status Tracking

All tasks update `CeleryTaskStatus` table:

```python
def update_task_status(
    task_id: str,
    status: str,
    progress: int = 0,
    current_step: str = None,
    result: dict = None,
    error_message: str = None
):
    task_status = get_or_create_task_status(task_id)
    task_status.status = status
    task_status.progress = progress
    task_status.current_step = current_step
    if status == "SUCCESS":
        task_status.result_json = json.dumps(result)
        task_status.completed_at = datetime.utcnow()
    elif status == "FAILURE":
        task_status.error_message = error_message
        task_status.completed_at = datetime.utcnow()
    save_task_status(task_status)
```

---

## Monitoring and Status

### Task Status API

```http
GET /v1/celery-tasks/{task_id}
```

**Response:**
```json
{
  "task_id": "abc123-def456",
  "task_name": "Check for new videos",
  "status": "PROGRESS",
  "progress": 75,
  "current_step": "Fetching video metadata (3/4)",
  "result": null,
  "error_message": null,
  "started_at": "2025-01-15T10:00:00Z",
  "completed_at": null
}
```

### Frontend Polling

```typescript
// use-task-status.ts
export function useTaskStatus(taskId: string | null) {
  return useQuery({
    queryKey: ['tasks', taskId],
    queryFn: () => api.get(`/v1/celery-tasks/${taskId}`),
    enabled: !!taskId,
    refetchInterval: (data) => {
      if (!data) return 2000;
      if (data.status === 'SUCCESS' || data.status === 'FAILURE') {
        return false; // Stop polling
      }
      return 2000; // Poll every 2 seconds
    },
  });
}
```

### Viewing Logs

```bash
# Development
docker compose -f docker-compose.dev.yml logs celery-worker-dev -f

# Production
docker compose -f docker-compose.prod.yml logs celery-worker-prod -f

# View Celery Beat logs
docker compose -f docker-compose.prod.yml logs celery-beat-prod -f
```

---

## Development Notes

### Local Development Without Docker

```bash
# Terminal 1: Redis
docker run -p 6379:6379 redis:alpine

# Terminal 2: Celery Worker
cd backend
uv run celery -A app.infrastructure.celery_app worker --loglevel=info

# Terminal 3: Celery Beat (for scheduled tasks)
cd backend
uv run celery -A app.infrastructure.celery_app beat --loglevel=info
```

### Important Limitation

**Celery workers do NOT auto-reload on code changes.**

After modifying task files, you must restart the workers:

```bash
# Development
docker compose -f docker-compose.dev.yml restart celery-worker-dev celery-beat-dev

# Production
docker compose -f docker-compose.prod.yml restart celery-worker-prod celery-beat-prod
```

### Testing Tasks Manually

```python
# In Python shell
from app.infrastructure.celery_app import celery_app
from app.infrastructure.tasks.channel_check_tasks import check_followed_channel_for_new_videos

# Queue task
result = check_followed_channel_for_new_videos.delay(1, 1)

# Check status
print(result.status)  # PENDING, STARTED, SUCCESS, FAILURE

# Get result (blocks until complete)
print(result.get(timeout=120))
```

### Environment Variables

```env
# Redis connection
REDIS_URL=redis://localhost:6379/0

# Task settings (in core/config.py)
CELERY_TASK_TIME_LIMIT=1800      # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT=1500 # 25 minutes
```

---

**End of Document**
