# Task 0047: Follow Channel and Discover Videos - Architecture & Implementation Summary

**Date**: 2025-11-14  
**Status**: ✅ Implemented  
**Version**: v2

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Data Structures](#data-structures)
4. [Complete Flow](#complete-flow)
5. [API Endpoints](#api-endpoints)
6. [Celery Tasks](#celery-tasks)
7. [State Machine](#state-machine)
8. [Error Handling & Retry Logic](#error-handling--retry-logic)
9. [Database Schema](#database-schema)
10. [Services & Components](#services--components)

---

## Overview

The "Follow Channel and Discover Videos" feature enables users to:

1. **Follow YouTube channels** - Subscribe to channels for automatic video discovery
2. **Discover new videos** - Automatically fetch metadata for new videos from followed channels
3. **Review videos** - Browse discovered videos and decide which ones to convert to episodes
4. **Create episodes** - Convert selected videos into podcast episodes with automatic audio download

### Key Design Decisions

- **Celery + Redis**: Professional task queue for reliable background processing
- **Separate Video Storage**: Videos are stored separately from episodes until user decides to create an episode
- **State Machine**: Videos transition through states: `pending_review` → `reviewed` → `queued` → `downloading` → `episode_created`
- **Dual Download Paths**: FastAPI BackgroundTasks for Quick Add, Celery tasks for Follow Channel feature
- **Auto-approve**: Optional automatic episode creation for new videos
- **Separate Pages**: Followed Channels and Videos are now on separate pages (`/subscriptions/channels` and `/subscriptions/videos`) for better navigation and organization
- **URL Search Params**: Videos page supports URL search parameters for filtering (state, channel, search) enabling bookmarking and sharing filtered views

---

## Architecture

### System Components

```
┌─────────────────┐
│   FastAPI App   │
│  (HTTP Server)  │
└────────┬────────┘
         │
         ├─────────────────────────────────────┐
         │                                     │
         ▼                                     ▼
┌─────────────────┐                  ┌─────────────────┐
│  API Endpoints  │                  │  Celery Worker  │
│                 │                  │                 │
│ - Follow Channel│                  │ - Check Channel │
│ - List Videos   │                  │ - Backfill      │
│ - Create Episode│                  │ - Create Episode│
│ - Download      │                  │ - Download Audio│
└────────┬────────┘                  └────────┬────────┘
         │                                     │
         │                                     │
         ▼                                     ▼
┌─────────────────────────────────────────────────────┐
│              Redis (Message Broker)                 │
│  - Task Queue                                       │
│  - Result Backend                                   │
└─────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│              SQLite Database                        │
│  - followed_channels                                │
│  - youtube_videos                                   │
│  - episodes                                         │
│  - celery_task_status                               │
└─────────────────────────────────────────────────────┘
```

### Celery Configuration

**File**: `backend/app/infrastructure/celery_app.py`

- **Broker**: Redis (`redis://redis:6379/0`)
- **Result Backend**: Redis (same instance)
- **Task Serialization**: JSON
- **Worker Pool**: Prefork (4 workers)
- **Task Time Limits**: 30 minutes hard, 25 minutes soft
- **Registered Tasks**:
  - `app.infrastructure.tasks.channel_check_tasks.*`
  - `app.infrastructure.tasks.backfill_channel_task.*`
  - `app.infrastructure.tasks.create_episode_from_video_task.*`
  - `app.infrastructure.tasks.download_episode_task.*`

### Task Routing

**File**: `backend/app/infrastructure/celery_config.py`

Tasks are routed to different queues for better organization:

- `channel_checks` - Periodic and manual channel checks
- `backfills` - Historical video backfill operations
- `episode_creation` - Episode creation from videos
- `celery` (default) - Download tasks and other operations

### Periodic Scheduling

**File**: `backend/app/infrastructure/celery_beat_schedule.py`

- **Daily Check**: Runs at 2 AM UTC via `periodic_check_all_channels` task
- **User Preferences**: Supports daily, twice-weekly, and weekly check frequencies
- **Dynamic Scheduling**: Can be extended to support per-user schedules

---

## Data Structures

### FollowedChannel Entity

**File**: `backend/app/domain/entities/followed_channel.py`

```python
@dataclass
class FollowedChannel:
    id: Optional[int]
    user_id: int
    youtube_channel_id: str  # YouTube channel ID (UCxxxxx or @handle)
    youtube_channel_name: str
    youtube_channel_url: str
    thumbnail_url: Optional[str] = None

    # Auto-approve settings
    auto_approve: bool = False
    auto_approve_channel_id: Optional[int] = None

    # Tracking
    last_checked: Optional[datetime] = None
    last_check_task_id: Optional[str] = None  # Celery task ID
    last_backfill_task_id: Optional[str] = None  # Celery task ID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
```

**Key Methods**:

- `update_auto_approve()` - Enable/disable auto-approve
- `update_last_checked()` - Update last check timestamp
- `update_metadata()` - Update channel metadata from YouTube

### YouTubeVideo Entity

**File**: `backend/app/domain/entities/youtube_video.py`

```python
@dataclass
class YouTubeVideo:
    id: Optional[int]
    video_id: str  # YouTube video ID (11 chars)
    followed_channel_id: int

    # Video metadata
    title: str
    description: Optional[str] = None
    url: str = ""
    thumbnail_url: Optional[str] = None
    publish_date: Optional[datetime] = None

    # Statistics
    duration: Optional[int] = None  # seconds
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    comment_count: Optional[int] = None

    # Raw metadata
    metadata_json: Optional[str] = None  # Full yt-dlp JSON

    # State and workflow
    state: YouTubeVideoState = YouTubeVideoState.PENDING_REVIEW
    episode_id: Optional[int] = None

    # Timestamps
    reviewed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
```

**State Transitions**:

- `mark_as_reviewed()` - `pending_review` → `reviewed`
- `mark_as_discarded()` - `pending_review`/`reviewed` → `discarded`
- `queue_for_episode_creation()` - `pending_review`/`reviewed` → `queued`
- `mark_as_downloading()` - `queued` → `downloading`
- `mark_as_episode_created()` - `downloading` → `episode_created`

**Validation Methods**:

- `can_create_episode()` - Check if video can be used to create episode
- `can_be_discarded()` - Check if video can be discarded

### YouTubeVideoState Enum

```python
class YouTubeVideoState(Enum):
    PENDING_REVIEW = "pending_review"  # Initial state, waiting for user review
    REVIEWED = "reviewed"              # User has reviewed, ready for episode creation
    QUEUED = "queued"                  # Queued for episode creation
    DOWNLOADING = "downloading"        # Audio download in progress
    EPISODE_CREATED = "episode_created" # Episode created successfully
    DISCARDED = "discarded"            # User discarded the video
```

---

## Complete Flow

### 1. Follow a Channel

**User Action**: User provides YouTube channel URL via UI

**Flow**:

```
User → POST /v1/followed-channels
  → FollowedChannelService.follow_channel()
    → YouTubeMetadataService.extract_channel_info()
      → Extract channel metadata (name, ID, URL, thumbnail)
    → Check for duplicates
    → Create FollowedChannel entity
    → Save to database
    → Queue backfill_followed_channel Celery task
      → Backfill last 20 videos of current year
```

**API Endpoint**: `POST /v1/followed-channels`

**Celery Task**: `backfill_followed_channel(followed_channel_id, year, max_videos)`

**Result**:

- FollowedChannel created in database
- Initial backfill task queued
- Returns FollowedChannelResponse with channel info

### 2. Discover New Videos

**Trigger**:

- Manual: User clicks "Check for new videos"
- Automatic: Periodic check via Celery Beat (daily at 2 AM UTC)
- Auto-approve: After following a channel (initial backfill)

**Flow**:

```
Trigger → check_followed_channel_for_new_videos(followed_channel_id)
  → Get FollowedChannel from database
  → ChannelDiscoveryService.discover_new_videos()
    → YouTubeMetadataService.list_channel_videos()
      → Fetch latest videos from YouTube (max 50)
    → For each video:
      → Check if video_id exists in database
      → If new: Create YouTubeVideo entity (state: pending_review)
      → Save to database
  → Update FollowedChannel.last_checked
  → If auto_approve enabled:
    → For each new video:
      → Queue create_episode_from_youtube_video task
```

**API Endpoint**: `POST /v1/followed-channels/{id}/check`

**Celery Task**: `check_followed_channel_for_new_videos(followed_channel_id)`

**Result**:

- New videos stored in `youtube_videos` table with `state = "pending_review"`
- If auto-approve: Episodes automatically queued for creation

### 3. Review Videos

**User Action**: User browses videos in `/subscriptions/videos` page

**Flow**:

```
User → GET /v1/youtube-videos?state=pending_review
  → YouTubeVideoService.search_videos()
    → Filter by state, channel, search query
    → Return list of YouTubeVideo entities
  → Display in UI
```

**User Actions**:

- **Mark as Reviewed**: `POST /v1/youtube-videos/{id}/review`
  - Transitions: `pending_review` → `reviewed`
- **Discard**: `POST /v1/youtube-videos/{id}/discard`
  - Transitions: `pending_review`/`reviewed` → `discarded`

**API Endpoints**:

- `GET /v1/youtube-videos` - List videos with filters
- `POST /v1/youtube-videos/{id}/review` - Mark as reviewed
- `POST /v1/youtube-videos/{id}/discard` - Discard video

### 4. Create Episode from Video

**User Action**: User clicks "Create Episode" on a reviewed video

**Flow**:

```
User → POST /v1/youtube-videos/{id}/create-episode
  → YouTubeVideoService.create_episode_from_video()
    → Verify video exists and belongs to user
    → Verify video.can_create_episode() (state must be pending_review or reviewed)
    → Verify channel exists and belongs to user
    → Queue create_episode_from_youtube_video Celery task
      → Create Episode entity
        → Extract video metadata
        → Set thumbnail_url from YouTubeVideo
        → Create episode in PENDING status
      → Update YouTubeVideo state: reviewed → queued → downloading → episode_created
      → Link episode_id to YouTubeVideo
      → Queue download_episode Celery task
        → CeleryDownloadService.download_episode()
          → Download audio from YouTube
          → Process and store audio file
          → Update episode status: PENDING → PROCESSING → COMPLETED
```

**API Endpoint**: `POST /v1/youtube-videos/{id}/create-episode`

**Celery Tasks**:

1. `create_episode_from_youtube_video(youtube_video_id, channel_id)`
2. `download_episode(episode_id, user_id, channel_id)`

**Result**:

- Episode created in database
- YouTubeVideo linked to episode
- Audio download queued and processed
- Episode ready for podcast feed

### 5. Download Audio

**Trigger**: Automatically after episode creation

**Flow**:

```
download_episode(episode_id) Celery Task
  → CeleryDownloadService.download_episode()
    → Get episode from database
    → Update status: PENDING → PROCESSING
    → YouTubeService.download_audio()
      → Use yt-dlp to download audio
      → Progress tracking via callbacks
    → FileService.process_audio_file()
      → Convert to MP3
      → Store in media directory
    → Update episode:
      → Set audio_file_path
      → Update status: PROCESSING → COMPLETED
      → Set download_date
```

**Celery Task**: `download_episode(episode_id, user_id, channel_id)`

**Service**: `CeleryDownloadService` (Celery-compatible, direct execution)

**Result**:

- Audio file downloaded and stored
- Episode status: `COMPLETED`
- Episode ready for podcast feed

---

## API Endpoints

### Followed Channels

#### Follow a Channel

```http
POST /v1/followed-channels
Authorization: Bearer <token>
Content-Type: application/json

{
  "channel_url": "https://www.youtube.com/@channel",
  "auto_approve": false,
  "auto_approve_channel_id": null
}

Response: 201 Created
{
  "id": 1,
  "user_id": 1,
  "youtube_channel_id": "UCxxxxx",
  "youtube_channel_name": "Channel Name",
  "youtube_channel_url": "https://www.youtube.com/@channel",
  "thumbnail_url": "https://...",
  "auto_approve": false,
  "auto_approve_channel_id": null,
  "last_checked": null,
  "created_at": "2025-11-14T12:00:00Z"
}
```

#### List Followed Channels

```http
GET /v1/followed-channels
Authorization: Bearer <token>

Response: 200 OK
[
  {
    "id": 1,
    "youtube_channel_name": "Channel Name",
    ...
  }
]
```

#### Get Followed Channel

```http
GET /v1/followed-channels/{id}
Authorization: Bearer <token>

Response: 200 OK
{
  "id": 1,
  ...
}
```

#### Update Followed Channel

```http
PUT /v1/followed-channels/{id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "auto_approve": true,
  "auto_approve_channel_id": 1
}

Response: 200 OK
```

#### Unfollow Channel

```http
DELETE /v1/followed-channels/{id}
Authorization: Bearer <token>

Response: 204 No Content
```

#### Trigger Check for New Videos

```http
POST /v1/followed-channels/{id}/check
Authorization: Bearer <token>

Response: 202 Accepted
{
  "status": "queued",
  "message": "Check task queued successfully",
  "followed_channel_id": 1
}
```

#### Backfill Historical Videos

```http
POST /v1/followed-channels/{id}/backfill
Authorization: Bearer <token>
Content-Type: application/json

{
  "year": 2024,
  "max_videos": 20
}

Response: 202 Accepted
{
  "status": "queued",
  "task_id": "abc-123",
  "followed_channel_id": 1,
  "year": 2024,
  "max_videos": 20
}
```

### YouTube Videos

#### List Videos

```http
GET /v1/youtube-videos?state=pending_review&followed_channel_id=1&search=query&skip=0&limit=50
Authorization: Bearer <token>

Response: 200 OK
[
  {
    "id": 1,
    "video_id": "dQw4w9WgXcQ",
    "title": "Video Title",
    "description": "Description",
    "url": "https://www.youtube.com/watch?v=...",
    "thumbnail_url": "https://...",
    "publish_date": "2025-11-14T12:00:00Z",
    "duration": 180,
    "view_count": 1000,
    "state": "pending_review",
    "followed_channel_id": 1,
    "episode_id": null
  }
]
```

#### Mark Video as Reviewed

```http
POST /v1/youtube-videos/{id}/review
Authorization: Bearer <token>

Response: 200 OK
{
  "id": 1,
  "state": "reviewed",
  ...
}
```

#### Discard Video

```http
POST /v1/youtube-videos/{id}/discard
Authorization: Bearer <token>

Response: 200 OK
{
  "id": 1,
  "state": "discarded",
  ...
}
```

#### Create Episode from Video

```http
POST /v1/youtube-videos/{id}/create-episode
Authorization: Bearer <token>
Content-Type: application/json

{
  "channel_id": 1
}

Response: 202 Accepted
{
  "status": "queued",
  "task_id": "abc-123",
  "youtube_video_id": 1,
  "channel_id": 1,
  "episode_id": 5,
  "message": "Episode creation queued successfully"
}
```

#### Get Video Statistics

```http
GET /v1/youtube-videos/stats
Authorization: Bearer <token>

Response: 200 OK
{
  "total": 100,
  "pending_review": 50,
  "reviewed": 30,
  "episode_created": 20
}
```

---

## Celery Tasks

### 1. check_followed_channel_for_new_videos

**File**: `backend/app/infrastructure/tasks/channel_check_tasks.py`

**Purpose**: Check a followed channel for new videos and discover them

**Signature**:

```python
@shared_task(
    name="app.infrastructure.tasks.channel_check_tasks.check_followed_channel_for_new_videos",
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True
)
def check_followed_channel_for_new_videos(self, followed_channel_id: int) -> dict
```

**Process**:

1. Get FollowedChannel from database
2. Use ChannelDiscoveryService to discover new videos
3. Create YouTubeVideo entities for new videos (state: `pending_review`)
4. If auto-approve enabled, queue episode creation for each new video
5. Update `last_checked` timestamp

**Returns**:

```python
{
    "status": "success",
    "followed_channel_id": 1,
    "new_videos_count": 5,
    "auto_approved": False
}
```

**Retry Logic**:

- Retries on `ConnectionError` and `TimeoutError`
- Max 3 retries with exponential backoff (60s initial, max 600s)
- Jitter added to prevent thundering herd

### 2. periodic_check_all_channels

**File**: `backend/app/infrastructure/tasks/channel_check_tasks.py`

**Purpose**: Periodically check all followed channels (called by Celery Beat)

**Signature**:

```python
@shared_task(
    name="app.infrastructure.tasks.channel_check_tasks.periodic_check_all_channels",
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True
)
def periodic_check_all_channels(self) -> dict
```

**Process**:

1. Get all FollowedChannels from database
2. For each channel, check if it's time to check (based on frequency preference)
3. Queue `check_followed_channel_for_new_videos` task for each channel

**Schedule**: Daily at 2 AM UTC (configurable)

### 3. backfill_followed_channel

**File**: `backend/app/infrastructure/tasks/backfill_channel_task.py`

**Purpose**: Backfill historical videos from a followed channel

**Signature**:

```python
@shared_task(
    name="app.infrastructure.tasks.backfill_channel_task.backfill_followed_channel",
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True
)
def backfill_followed_channel(
    self,
    followed_channel_id: int,
    year: Optional[int] = None,
    max_videos: int = 20
) -> dict
```

**Process**:

1. Get FollowedChannel from database
2. Use ChannelDiscoveryService to backfill videos
3. Filter by year if specified
4. Create YouTubeVideo entities for discovered videos
5. Update `last_backfill_task_id` in FollowedChannel

**Returns**:

```python
{
    "status": "success",
    "followed_channel_id": 1,
    "year": 2024,
    "videos_backfilled": 20
}
```

### 4. create_episode_from_youtube_video

**File**: `backend/app/infrastructure/tasks/create_episode_from_video_task.py`

**Purpose**: Create an episode from a YouTube video

**Signature**:

```python
@shared_task(
    name="app.infrastructure.tasks.create_episode_from_video_task.create_episode_from_youtube_video",
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True
)
def create_episode_from_youtube_video(
    self,
    youtube_video_id: int,
    channel_id: int
) -> dict
```

**Process**:

1. Get YouTubeVideo and Channel from database
2. Update video state: `reviewed` → `queued` → `downloading`
3. Create Episode entity with metadata from YouTubeVideo
   - Includes `thumbnail_url` from YouTubeVideo
4. Save episode to database
5. Update YouTubeVideo: link `episode_id`, state → `episode_created`
6. Queue `download_episode` Celery task

**Returns**:

```python
{
    "status": "success",
    "youtube_video_id": 1,
    "channel_id": 1,
    "episode_id": 5,
    "download_task_id": "abc-123",
    "download_queued": True
}
```

### 5. download_episode

**File**: `backend/app/infrastructure/tasks/download_episode_task.py`

**Purpose**: Download audio file for an episode

**Signature**:

```python
@shared_task(
    name="app.infrastructure.tasks.download_episode_task.download_episode",
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True
)
def download_episode(
    self,
    episode_id: int,
    user_id: Optional[int] = None,
    channel_id: Optional[int] = None
) -> dict
```

**Process**:

1. Create CeleryDownloadService instance
2. Download episode audio:
   - Get episode from database
   - Update status: `PENDING` → `PROCESSING`
   - Download audio using YouTubeService
   - Process and store file using FileService
   - Update episode: set `audio_file_path`, status → `COMPLETED`
3. Handle errors and retries

**Service**: `CeleryDownloadService` (direct execution, no queue)

**Returns**:

```python
{
    "status": "success",
    "episode_id": 5,
    "message": "Episode downloaded successfully",
    "file_path": "/media/channel_1/episode_5.mp3"
}
```

---

## State Machine

### YouTubeVideo State Transitions

```
┌─────────────────┐
│ pending_review  │ ← Initial state (newly discovered)
└────────┬────────┘
         │
         ├─ mark_as_reviewed() ──┐
         │                        │
         ▼                        ▼
┌─────────────────┐      ┌─────────────────┐
│   reviewed      │      │   discarded     │
└────────┬────────┘      └─────────────────┘
         │
         ├─ queue_for_episode_creation() ──┐
         │                                  │
         ▼                                  │
┌─────────────────┐                        │
│    queued       │                        │
└────────┬────────┘                        │
         │                                  │
         ├─ mark_as_downloading() ─────────┤
         │                                  │
         ▼                                  │
┌─────────────────┐                        │
│  downloading    │                        │
└────────┬────────┘                        │
         │                                  │
         ├─ mark_as_episode_created() ─────┤
         │                                  │
         ▼                                  │
┌─────────────────┐                        │
│episode_created  │                        │
└─────────────────┘                        │
                                           │
         ┌─────────────────────────────────┘
         │
         └─ mark_as_discarded() (from pending_review or reviewed)
```

### Episode Status Transitions

```
PENDING → PROCESSING → COMPLETED
   │          │
   │          └─→ FAILED (on error)
   │
   └─→ FAILED (on error)
```

### Valid State Transitions

| From State       | To State          | Method                         | Notes                         |
| ---------------- | ----------------- | ------------------------------ | ----------------------------- |
| `pending_review` | `reviewed`        | `mark_as_reviewed()`           | User reviewed video           |
| `pending_review` | `discarded`       | `mark_as_discarded()`          | User discarded video          |
| `reviewed`       | `discarded`       | `mark_as_discarded()`          | User discarded after review   |
| `pending_review` | `queued`          | `queue_for_episode_creation()` | Auto-approve or manual create |
| `reviewed`       | `queued`          | `queue_for_episode_creation()` | User creates episode          |
| `queued`         | `downloading`     | `mark_as_downloading()`        | Download task started         |
| `downloading`    | `episode_created` | `mark_as_episode_created()`    | Episode created successfully  |

---

## Error Handling & Retry Logic

### Celery Task Retries

All Celery tasks include retry configuration:

```python
@shared_task(
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True
)
```

**Retry Behavior**:

- **Max Retries**: 3 attempts
- **Initial Delay**: 60 seconds
- **Exponential Backoff**: Delay doubles with each retry
- **Max Delay**: 600 seconds (10 minutes)
- **Jitter**: Random variation to prevent thundering herd

**Retryable Errors**:

- `ConnectionError` - Network/Redis connection issues
- `TimeoutError` - YouTube API timeouts

### Database Lock Handling

**File**: `backend/app/infrastructure/services/celery_download_service.py`

Download service includes sophisticated database lock retry logic:

```python
max_retries = 5
base_delay = 1.0  # seconds
max_delay = 30.0  # seconds

for attempt in range(max_retries):
    try:
        # Update episode
        await bg_episode_repository.update(episode)
        await bg_session.commit()
        break
    except Exception as db_error:
        if "database is locked" in str(db_error).lower():
            # Exponential backoff + jitter
            delay = min(base_delay * (2 ** attempt), max_delay)
            jitter = random.uniform(0.1, 0.5) * delay
            await asyncio.sleep(delay + jitter)
            # Retry with refreshed entity
```

**Features**:

- Detects SQLite database locks
- Exponential backoff with jitter
- Refreshes entity from database before retry
- Rollback and retry pattern

### API Error Handling

**Connection Errors**:

- Catches `ConnectionError` and `kombu.exceptions.OperationalError`
- Returns HTTP 503 (Service Unavailable)
- Clear error message: "Task queue is temporarily unavailable"

**Validation Errors**:

- `FollowedChannelNotFoundError` → HTTP 404
- `InvalidStateTransitionError` → HTTP 400
- `DuplicateChannelError` → HTTP 409

---

## Database Schema

### followed_channels Table

```sql
CREATE TABLE followed_channels (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    youtube_channel_id VARCHAR(255) NOT NULL,
    youtube_channel_name VARCHAR(255) NOT NULL,
    youtube_channel_url VARCHAR(500) NOT NULL,
    thumbnail_url VARCHAR(500),

    -- Auto-approve settings
    auto_approve BOOLEAN DEFAULT FALSE NOT NULL,
    auto_approve_channel_id INTEGER,

    -- Tracking
    last_checked DATETIME,
    last_check_task_id VARCHAR(255),
    last_backfill_task_id VARCHAR(255),

    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,

    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (auto_approve_channel_id) REFERENCES channels(id),
    UNIQUE (youtube_channel_id, user_id)
);

CREATE INDEX idx_followed_channel_user_id ON followed_channels(user_id);
CREATE INDEX idx_followed_channel_youtube_id ON followed_channels(youtube_channel_id);
CREATE INDEX idx_followed_channel_last_checked ON followed_channels(last_checked);
CREATE INDEX idx_followed_channel_last_check_task ON followed_channels(last_check_task_id);
CREATE INDEX idx_followed_channel_last_backfill_task ON followed_channels(last_backfill_task_id);
```

### youtube_videos Table

```sql
CREATE TABLE youtube_videos (
    id INTEGER PRIMARY KEY,
    video_id VARCHAR(255) NOT NULL UNIQUE,
    followed_channel_id INTEGER NOT NULL,

    -- Video metadata
    title VARCHAR(500) NOT NULL,
    description TEXT,
    url VARCHAR(500) NOT NULL,
    thumbnail_url VARCHAR(500),
    publish_date DATETIME NOT NULL,

    -- Statistics
    duration INTEGER,
    view_count INTEGER,
    like_count INTEGER,
    comment_count INTEGER,

    -- Raw metadata
    metadata_json TEXT,

    -- State and workflow
    state VARCHAR(50) NOT NULL DEFAULT 'pending_review',
    episode_id INTEGER,

    -- Timestamps
    reviewed_at DATETIME,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,

    FOREIGN KEY (followed_channel_id) REFERENCES followed_channels(id),
    FOREIGN KEY (episode_id) REFERENCES episodes(id)
);

CREATE INDEX idx_youtube_video_followed_channel ON youtube_videos(followed_channel_id);
CREATE INDEX idx_youtube_video_state ON youtube_videos(state);
CREATE INDEX idx_youtube_video_publish_date ON youtube_videos(publish_date);
CREATE INDEX idx_youtube_video_channel_state ON youtube_videos(followed_channel_id, state);
CREATE INDEX idx_youtube_video_episode_id ON youtube_videos(episode_id);
```

### celery_task_status Table

```sql
CREATE TABLE celery_task_status (
    id INTEGER PRIMARY KEY,
    task_id VARCHAR(255) NOT NULL UNIQUE,
    task_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    progress INTEGER DEFAULT 0,
    current_step VARCHAR(255),
    result_json TEXT,
    error_message TEXT,

    -- Foreign keys
    followed_channel_id INTEGER,
    youtube_video_id INTEGER,

    -- Timestamps
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    started_at DATETIME,
    completed_at DATETIME,

    FOREIGN KEY (followed_channel_id) REFERENCES followed_channels(id),
    FOREIGN KEY (youtube_video_id) REFERENCES youtube_videos(id)
);

CREATE INDEX idx_celery_task_status_task_id ON celery_task_status(task_id);
CREATE INDEX idx_celery_task_status_status ON celery_task_status(status);
CREATE INDEX idx_celery_task_status_followed_channel_id ON celery_task_status(followed_channel_id);
CREATE INDEX idx_celery_task_status_youtube_video_id ON celery_task_status(youtube_video_id);
```

---

## Services & Components

### Application Services

#### FollowedChannelService

**File**: `backend/app/application/services/followed_channel_service.py`

**Responsibilities**:

- Follow/unfollow channels
- Update channel settings (auto-approve)
- Trigger manual checks and backfills
- Get followed channels with statistics

**Key Methods**:

- `follow_channel()` - Follow a new channel
- `unfollow_channel()` - Unfollow a channel
- `update_auto_approve()` - Update auto-approve settings
- `trigger_check()` - Queue check task
- `trigger_backfill()` - Queue backfill task
- `get_followed_channels()` - List user's followed channels

#### YouTubeVideoService

**File**: `backend/app/application/services/youtube_video_service.py`

**Responsibilities**:

- List and search videos
- Manage video state transitions
- Create episodes from videos

**Key Methods**:

- `search_videos()` - List videos with filters
- `get_video()` - Get single video
- `mark_as_reviewed()` - Mark video as reviewed
- `mark_as_discarded()` - Discard video
- `create_episode_from_video()` - Queue episode creation

### Infrastructure Services

#### ChannelDiscoveryService

**File**: `backend/app/infrastructure/services/channel_discovery_service_impl.py`

**Responsibilities**:

- Discover new videos from followed channels
- Backfill historical videos
- Deduplicate videos

**Key Methods**:

- `discover_new_videos()` - Find new videos since last check
- `backfill_channel_videos()` - Fetch historical videos

#### YouTubeMetadataService

**File**: `backend/app/infrastructure/services/youtube_metadata_service_impl.py`

**Responsibilities**:

- Extract channel metadata from YouTube
- Extract video metadata from YouTube
- List videos from a channel

**Key Methods**:

- `extract_channel_info()` - Get channel metadata
- `extract_metadata()` - Get video metadata
- `list_channel_videos()` - List videos from channel

#### CeleryDownloadService

**File**: `backend/app/infrastructure/services/celery_download_service.py`

**Responsibilities**:

- Download episode audio files
- Process and store audio files
- Track download progress
- Handle errors and retries

**Key Methods**:

- `download_episode()` - Download and process audio file

**Differences from DownloadService**:

- Direct execution (no queue mechanism)
- Works within Celery's event loop lifecycle
- No BackgroundTasks dependency

### Repositories

#### FollowedChannelRepository

**File**: `backend/app/infrastructure/repositories/followed_channel_repository_impl.py`

**Methods**:

- `create()` - Create followed channel
- `get_by_id()` - Get by ID
- `get_by_user_and_youtube_channel_id()` - Check for duplicates
- `get_all_by_user()` - List user's channels
- `update()` - Update channel
- `delete()` - Delete channel

#### YouTubeVideoRepository

**File**: `backend/app/infrastructure/repositories/youtube_video_repository_impl.py`

**Methods**:

- `create()` - Create video
- `get_by_id()` - Get by ID
- `get_by_video_id()` - Get by YouTube video ID
- `search()` - Search with filters
- `update()` - Update video
- `delete()` - Delete video

---

## Key Implementation Details

### Async Execution in Celery

**Pattern**: `_run_async()` helper function

```python
def _run_async(coro):
    """Helper to run async function in Celery task"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()
```

**Usage**: All Celery tasks use this pattern to execute async code:

```python
def celery_task(self, arg1, arg2):
    async def _async_work():
        # Async code here
        pass

    return _run_async(_async_work())
```

### Database Session Management

**Background Task Sessions**:

- Use `get_background_task_session()` for Celery tasks
- Separate from FastAPI request sessions
- Prevents database lock conflicts

**Session Isolation**:

- Close sessions before queuing new tasks
- Wait 3 seconds for session cleanup (prevents SQLite locks)
- Create new sessions for each task

### Task ID Tracking

**FollowedChannel** tracks Celery task IDs:

- `last_check_task_id` - ID of last check task
- `last_backfill_task_id` - ID of last backfill task

**Purpose**:

- UI can poll task status
- Track task progress
- Link tasks to channels

### Auto-approve Feature

**Flow**:

1. User enables auto-approve when following channel
2. When new videos are discovered:
   - Videos are created in `pending_review` state
   - Immediately transitioned to `queued` state
   - Episode creation tasks are queued automatically
3. Episodes are created and downloaded without user intervention

**Configuration**:

- Set `auto_approve = True` on FollowedChannel
- Set `auto_approve_channel_id` to target podcast channel

---

## Future Enhancements

### Planned Features

1. **Advanced Filtering**:

   - The `/subscriptions/videos` page should have a filter to allow filtering videos by Youtube Channel and date range (per year allowing to select various years and all years)
   - Bulk operations: The `/subscriptions/videos` page should allow selecting multiple videos and performing actions on them: create episodes, mark as reviewed, discard, etc.

2. **Task Progress UI**:

   - Real-time progress indicators for check/backfill operations: In the same way we provide feedback when we are creaiting an episode from a video, we should provide feedback when we are checking for new videos or backfilling videos. The Youtube channel card in `/subscriptions/channels` page should show the progress of the check/backfill operation, showing and icon on the card indicating the status: pending, in progress, completed, failed:
   - Clickable results that navigate to Videos page: The Youtube channel card in `/subscriptions/channels` page should:
     - show information about the number of videos discovered in the last operation, the number of videos in pending/reviewed/discarded state
     - have a button on each type of video status (pending/reviewed/discarded) to navigate to the `/subscriptions/videos` page with the filter applied to the channel for that type of video status and the channel
   - Status polling via API: The Youtube channel card in `/subscriptions/channels` page should poll the status of the check/backfill operation via API and update the UI accordingly

3. **Notification System**:

   - Notify users when new videos are discovered after a check/backfill operation
   - Notify when episodes are created, both from the interaction of the user via the FastAPI (Quick Add Episode, Create Episode from locall uploaded video, Create Episode from Youtube Video) routes or from the Celery tasks (Create Episode from Video)
   - Email/push notifications (DO NOT IMPLEMENT - Pending to decide if we want to implement this in the future)

4. **Migration to Celery for All Downloads - (DO NOT IMPLEMENT - Pending to decide in the future)**:
   - Move FastAPI BackgroundTasks downloads to Celery (Pending to decide if we want to implement this in the future)
   - Unified download infrastructure (Pending to decide if we want to implement this in the future)
   - Better scalability (Pending to decide if we want to implement this in the future)

### Technical Improvements

1. **Task Status Tracking**:

   - Implement `CeleryTaskStatus` model usage
   - Real-time progress updates
   - Task history and audit trail

2. **Rate Limiting (DO NOT IMPLEMENT - Might be implemented in the future)**:

   - Per-user rate limits for manual triggers
   - Global rate limits for YouTube API calls
   - Queue prioritization

3. **Caching (DO NOT IMPLEMENT - Might be implemented in the future)**:
   - Cache YouTube API responses
   - Cache channel metadata
   - Redis caching layer

---

## Related Files

### Backend

**Celery Configuration**:

- `backend/app/infrastructure/celery_app.py` - Celery app initialization
- `backend/app/infrastructure/celery_config.py` - Task routing and configuration
- `backend/app/infrastructure/celery_beat_schedule.py` - Periodic task schedule
- `backend/celery_worker.py` - Worker entry point

**Tasks**:

- `backend/app/infrastructure/tasks/channel_check_tasks.py` - Channel checking tasks
- `backend/app/infrastructure/tasks/backfill_channel_task.py` - Backfill task
- `backend/app/infrastructure/tasks/create_episode_from_video_task.py` - Episode creation task
- `backend/app/infrastructure/tasks/download_episode_task.py` - Download task

**Services**:

- `backend/app/infrastructure/services/celery_download_service.py` - Celery download service
- `backend/app/infrastructure/services/channel_discovery_service_impl.py` - Discovery service
- `backend/app/infrastructure/services/youtube_metadata_service_impl.py` - Metadata service

**API Endpoints**:

- `backend/app/presentation/api/v1/followed_channels.py` - Followed channels API
- `backend/app/presentation/api/v1/youtube_videos.py` - YouTube videos API

**Domain Entities**:

- `backend/app/domain/entities/followed_channel.py` - FollowedChannel entity
- `backend/app/domain/entities/youtube_video.py` - YouTubeVideo entity

**Database Models**:

- `backend/app/infrastructure/database/models/followed_channel.py` - FollowedChannel model
- `backend/app/infrastructure/database/models/youtube_video.py` - YouTubeVideo model
- `backend/app/infrastructure/database/models/celery_task_status.py` - Task status model

### Frontend

**Pages**:

- `frontend/src/app/subscriptions/channels/page.tsx` - Followed Channels page
- `frontend/src/app/subscriptions/videos/page.tsx` - Videos page
- `frontend/src/app/subscriptions/page.tsx` - Original subscriptions page with tabs (preserved)

**Components**:

- `frontend/src/components/features/subscriptions/followed-channels-list.tsx` - Followed channels list
- `frontend/src/components/features/subscriptions/video-list.tsx` - Videos list (with URL search params support)
- `frontend/src/components/features/subscriptions/youtube-video-card.tsx` - Video card component

**Hooks**:

- `frontend/src/hooks/use-followed-channels.ts` - Followed channels hooks
- `frontend/src/hooks/use-youtube-videos.ts` - YouTube videos hooks

**API Client**:

- `frontend/src/lib/api-client.ts` - API client methods

---

## Testing

### Manual Testing Checklist

1. **Follow Channel**:

   - [ ] Follow a YouTube channel via UI
   - [ ] Verify channel appears in `/subscriptions/channels` page
   - [ ] Verify initial backfill task is queued
   - [ ] Check logs for backfill task execution

2. **Discover Videos**:

   - [ ] Trigger "Check for new videos" manually
   - [ ] Verify videos appear in `/subscriptions/videos` page
   - [ ] Verify videos have correct metadata (title, thumbnail, etc.)
   - [ ] Check periodic task runs at scheduled time

3. **Review Videos**:

   - [ ] Mark video as reviewed
   - [ ] Discard a video
   - [ ] Verify state transitions correctly

4. **Create Episode**:

   - [ ] Create episode from reviewed video
   - [ ] Verify episode is created in database
   - [ ] Verify download task is queued
   - [ ] Verify audio file is downloaded
   - [ ] Verify episode appears in podcast feed

5. **Auto-approve**:
   - [ ] Enable auto-approve on followed channel
   - [ ] Trigger check for new videos
   - [ ] Verify episodes are automatically created
   - [ ] Verify downloads start automatically

### Monitoring

**Celery Worker Logs**:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml logs -f celery-worker
```

**Backend Logs**:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml logs -f backend
```

**Redis Status**:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml exec redis redis-cli PING
```

---

## Conclusion

The "Follow Channel and Discover Videos" feature provides a complete workflow for:

1. Following YouTube channels
2. Automatically discovering new videos
3. Reviewing and selecting videos
4. Creating podcast episodes with automatic audio download

The architecture uses Celery for reliable background processing, maintains clean separation between videos and episodes, and provides a robust state machine for workflow management. The dual download paths (FastAPI BackgroundTasks and Celery) ensure flexibility while maintaining independence between systems.
