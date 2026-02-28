# LabCastARR Database Schema Documentation

**Document Version:** 1.0
**Last Updated:** 2026-01-29

---

## Table of Contents

1. [Overview](#overview)
2. [Entity Relationship Diagram](#entity-relationship-diagram)
3. [Table Schemas](#table-schemas)
4. [Indexes](#indexes)
5. [Migration History](#migration-history)
6. [Database Configuration](#database-configuration)

---

## Overview

LabCastARR uses **SQLite** with **WAL (Write-Ahead Logging) mode** for concurrent access support. The database is managed through **SQLAlchemy** ORM with **Alembic** for migrations.

### Database Files

| Environment | Database File | Location |
|-------------|---------------|----------|
| Development | `labcastarr-dev.db` | `backend/data/` |
| Production | `labcastarr.db` | `backend/data/` |

### Database Statistics

- **Total Tables**: 14 (including 1 junction table)
- **Total Migrations**: 14 versions
- **Primary Key Type**: Auto-incrementing INTEGER

---

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USERS                                           │
│  ┌──────────┐                                                               │
│  │  users   │                                                               │
│  ├──────────┤                                                               │
│  │ id (PK)  │◄─────────────────────────────────────────────────────────┐   │
│  │ email    │                                                           │   │
│  │ username │                                                           │   │
│  │ password │                                                           │   │
│  └──────────┘                                                           │   │
└─────────────────────────────────────────────────────────────────────────────┘
       │              │              │               │              │
       │1             │1             │1              │1             │1
       │              │              │               │              │
       ▼*             ▼*             ▼1              ▼*             ▼*
┌────────────┐ ┌────────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────┐
│  channels  │ │followed_channels│ │user_settings│ │notifications│ │   events   │
├────────────┤ ├────────────────┤ ├─────────────┤ ├─────────────┤ ├────────────┤
│ id (PK)    │ │ id (PK)        │ │ id (PK)     │ │ id (PK)     │ │ id (PK)    │
│ user_id(FK)│ │ user_id (FK)   │ │ user_id(FK) │ │ user_id(FK) │ │ user_id(FK)│
│ title      │ │ youtube_channel│ │ timezone    │ │ type        │ │ event_type │
│ description│ │ _id            │ │ check_time  │ │ title       │ │ action     │
└────────────┘ │ auto_approve   │ │ check_freq  │ │ message     │ │ resource_id│
     │1        │ auto_approve_  │ └─────────────┘ │ read        │ │ details    │
     │         │ channel_id(FK)─┼─────┐           └─────────────┘ └────────────┘
     │         └────────────────┘     │
     │               │1               │
     │               │                │
     │               ▼*               │
     │         ┌────────────────┐     │
     │         │ youtube_videos │     │
     │         ├────────────────┤     │
     │         │ id (PK)        │     │
     │         │ video_id (UK)  │     │
     │         │ followed_      │     │
     │         │ channel_id(FK) │     │
     │         │ title          │     │
     │         │ state          │     │
     │         │ episode_id(FK)─┼─────┼───┐
     │         └────────────────┘     │   │
     │                                │   │
     ▼*                               │   │
┌────────────┐                        │   │
│  episodes  │◄───────────────────────┘   │
├────────────┤                            │
│ id (PK)    │◄───────────────────────────┘
│ channel_id │
│ title      │
│ video_url  │
│ status     │
│ source_type│
└────────────┘
     │
     │*
     ▼
┌──────────────────┐
│   episode_tags   │ (Junction Table)
├──────────────────┤
│ episode_id (FK)  │
│ tag_id (FK)      │
└──────────────────┘
     │
     │*
     ▼
┌────────────┐
│    tags    │
├────────────┤
│ id (PK)    │
│ name       │
│ color      │
│ channel_id │
└────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                        CELERY TASK TRACKING                                  │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      celery_task_status                               │   │
│  ├──────────────────────────────────────────────────────────────────────┤   │
│  │ id (PK)                                                               │   │
│  │ task_id (UK) ─ Celery task UUID                                      │   │
│  │ task_name                                                             │   │
│  │ status (PENDING/STARTED/PROGRESS/SUCCESS/FAILURE/RETRY)              │   │
│  │ progress (0-100)                                                      │   │
│  │ current_step                                                          │   │
│  │ followed_channel_id (FK to followed_channels, nullable)              │   │
│  │ youtube_video_id (FK to youtube_videos, nullable)                    │   │
│  │ result_json / error_message                                          │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Table Schemas

### 1. `users`

Primary user authentication table.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO | Unique user ID |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | User email address |
| `username` | VARCHAR(100) | NOT NULL | Display name |
| `password_hash` | VARCHAR(255) | NOT NULL | Bcrypt hashed password |
| `is_active` | BOOLEAN | DEFAULT TRUE | Account status |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Registration time |
| `updated_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Last update time |

---

### 2. `channels`

Podcast channel configuration.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO | Unique channel ID |
| `user_id` | INTEGER | FK(users.id), NOT NULL | Channel owner |
| `title` | VARCHAR(255) | NOT NULL | Podcast title |
| `description` | TEXT | NULL | Podcast description |
| `author_name` | VARCHAR(255) | NULL | Host name |
| `author_email` | VARCHAR(255) | NULL | Contact email |
| `website_url` | VARCHAR(500) | NULL | Podcast website |
| `image_url` | VARCHAR(500) | NULL | Cover art URL |
| `language` | VARCHAR(10) | DEFAULT 'en' | ISO language code |
| `category` | VARCHAR(100) | NULL | iTunes category |
| `explicit` | BOOLEAN | DEFAULT FALSE | Explicit content flag |
| `feed_url` | VARCHAR(500) | NULL | Generated RSS feed URL |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Creation time |
| `updated_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Last update time |

**Indexes:**
- `idx_channels_user_id` on `user_id`

---

### 3. `episodes`

Podcast episode records.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO | Unique episode ID |
| `channel_id` | INTEGER | FK(channels.id), NOT NULL | Parent channel |
| `title` | VARCHAR(500) | NOT NULL | Episode title |
| `description` | TEXT | NULL | Episode description |
| `video_url` | VARCHAR(500) | NULL | Source YouTube URL |
| `video_id` | VARCHAR(50) | NULL, UNIQUE | YouTube video ID |
| `thumbnail_url` | VARCHAR(500) | NULL | Episode thumbnail |
| `audio_file_path` | VARCHAR(500) | NULL | Stored audio file path |
| `duration` | INTEGER | NULL | Duration in seconds |
| `publication_date` | DATETIME | NULL | Episode publish date |
| `download_date` | DATETIME | NULL | When audio was downloaded |
| `status` | VARCHAR(50) | DEFAULT 'pending' | Processing status |
| `retry_count` | INTEGER | DEFAULT 0 | Download retry attempts |
| `keywords` | TEXT | NULL | JSON array of keywords |
| `media_file_size` | INTEGER | NULL | File size in bytes |
| `source_type` | VARCHAR(20) | DEFAULT 'youtube' | 'youtube' or 'upload' |
| `original_filename` | VARCHAR(255) | NULL | Original uploaded filename |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Creation time |
| `updated_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Last update time |

**Status Values:**
- `pending` - Queued for processing
- `processing` - Download/conversion in progress
- `completed` - Ready for distribution
- `failed` - Error occurred

**Indexes:**
- `idx_episodes_channel_id` on `channel_id`
- `idx_episodes_status` on `status`
- `idx_episodes_video_id` on `video_id` (UNIQUE)
- `idx_episodes_source_type` on `source_type`
- `idx_episodes_publication_date` on `publication_date`

---

### 4. `tags`

Episode categorization tags.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO | Unique tag ID |
| `name` | VARCHAR(100) | NOT NULL | Tag name |
| `color` | VARCHAR(20) | NULL | Hex color code |
| `channel_id` | INTEGER | FK(channels.id), NOT NULL | Parent channel |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Creation time |

**Indexes:**
- `idx_tags_channel_id` on `channel_id`
- UNIQUE constraint on `(name, channel_id)`

---

### 5. `episode_tags`

Junction table for episode-tag many-to-many relationship.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `episode_id` | INTEGER | FK(episodes.id), NOT NULL | Episode reference |
| `tag_id` | INTEGER | FK(tags.id), NOT NULL | Tag reference |

**Constraints:**
- PRIMARY KEY (`episode_id`, `tag_id`)
- CASCADE DELETE on both foreign keys

---

### 6. `followed_channels`

YouTube channel subscriptions for video discovery.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO | Unique ID |
| `user_id` | INTEGER | FK(users.id), NOT NULL | Subscription owner |
| `youtube_channel_id` | VARCHAR(255) | NOT NULL | YouTube channel ID |
| `youtube_channel_name` | VARCHAR(255) | NOT NULL | Channel display name |
| `youtube_channel_url` | VARCHAR(500) | NOT NULL | Channel URL |
| `youtube_channel_description` | TEXT | NULL | Channel description |
| `thumbnail_url` | VARCHAR(500) | NULL | Channel avatar |
| `auto_approve` | BOOLEAN | DEFAULT FALSE | Auto-create episodes |
| `auto_approve_channel_id` | INTEGER | FK(channels.id), NULL | Target channel for auto |
| `last_checked` | DATETIME | NULL | Last video check time |
| `last_check_task_id` | VARCHAR(255) | NULL | Last check Celery task |
| `last_backfill_task_id` | VARCHAR(255) | NULL | Last backfill task |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Subscription time |
| `updated_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Last update |

**Indexes:**
- `idx_followed_channels_user_id` on `user_id`
- `idx_followed_channels_youtube_channel_id` on `youtube_channel_id`
- `idx_followed_channels_last_checked` on `last_checked`
- UNIQUE constraint on `(youtube_channel_id, user_id)`

---

### 7. `youtube_videos`

Discovered videos from followed channels.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO | Unique ID |
| `video_id` | VARCHAR(255) | UNIQUE, NOT NULL | YouTube video ID |
| `followed_channel_id` | INTEGER | FK(followed_channels.id), NOT NULL | Source channel |
| `title` | VARCHAR(500) | NOT NULL | Video title |
| `description` | TEXT | NULL | Video description |
| `url` | VARCHAR(500) | NOT NULL | Video URL |
| `thumbnail_url` | VARCHAR(500) | NULL | Video thumbnail |
| `publish_date` | DATETIME | NOT NULL | YouTube publish date |
| `duration` | INTEGER | NULL | Duration in seconds |
| `view_count` | INTEGER | NULL | View count at discovery |
| `like_count` | INTEGER | NULL | Like count at discovery |
| `comment_count` | INTEGER | NULL | Comment count |
| `metadata_json` | TEXT | NULL | Full yt-dlp metadata |
| `state` | VARCHAR(50) | DEFAULT 'pending_review' | Workflow state |
| `episode_id` | INTEGER | FK(episodes.id), NULL | Created episode link |
| `reviewed_at` | DATETIME | NULL | Review timestamp |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Discovery time |
| `updated_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Last update |

**State Values:**
- `pending_review` - Awaiting user review
- `reviewed` - Marked for later
- `queued` - Queued for episode creation
- `downloading` - Episode creation in progress
- `episode_created` - Episode successfully created
- `discarded` - User discarded video

**Indexes:**
- `idx_youtube_videos_video_id` (UNIQUE)
- `idx_youtube_videos_followed_channel_id`
- `idx_youtube_videos_state`
- `idx_youtube_videos_publish_date`
- `idx_youtube_videos_episode_id`
- Composite: `idx_youtube_videos_channel_state` on `(followed_channel_id, state)`

---

### 8. `events`

Audit log for user actions and system events.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO | Unique ID |
| `user_id` | INTEGER | FK(users.id), NULL | Acting user |
| `event_type` | VARCHAR(50) | NOT NULL | Event category |
| `action` | VARCHAR(100) | NOT NULL | Specific action |
| `resource_type` | VARCHAR(50) | NULL | Affected resource type |
| `resource_id` | INTEGER | NULL | Affected resource ID |
| `details` | TEXT | NULL | JSON event details |
| `severity` | VARCHAR(20) | DEFAULT 'info' | Log level |
| `duration_ms` | INTEGER | NULL | Operation duration |
| `ip_address` | VARCHAR(45) | NULL | Client IP |
| `user_agent` | VARCHAR(500) | NULL | Client user agent |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Event time |

**Event Types:**
- `user_action` - User-initiated actions
- `system_event` - System operations
- `error` - Error occurrences
- `auth` - Authentication events

**Severity Levels:**
- `debug`, `info`, `warning`, `error`, `critical`

**Indexes:**
- `idx_events_user_id`
- `idx_events_event_type`
- `idx_events_created_at`
- `idx_events_resource_type`

---

### 9. `notifications`

User notification system.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO | Unique ID |
| `user_id` | INTEGER | FK(users.id), NOT NULL | Notification recipient |
| `type` | VARCHAR(50) | NOT NULL | Notification type |
| `title` | VARCHAR(255) | NOT NULL | Notification title |
| `message` | TEXT | NOT NULL | Notification body |
| `data_json` | TEXT | NULL | Additional JSON data |
| `read` | BOOLEAN | DEFAULT FALSE | Read status |
| `executed_by` | VARCHAR(50) | NULL | Source of notification |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Creation time |
| `updated_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Last update |

**Notification Types:**
- `video_discovered` - New videos found
- `episode_created` - Episode creation complete
- `channel_search_started` - Search initiated
- `channel_search_completed` - Search finished
- `channel_search_error` - Search failed

**Indexes:**
- `idx_notifications_user_read_created` on `(user_id, read, created_at)`
- `idx_notifications_user_created` on `(user_id, created_at)`

---

### 10. `celery_task_status`

Background task status tracking.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO | Unique ID |
| `task_id` | VARCHAR(255) | UNIQUE, NOT NULL | Celery task UUID |
| `task_name` | VARCHAR(255) | NOT NULL | Human-readable name |
| `status` | VARCHAR(50) | DEFAULT 'PENDING' | Task status |
| `progress` | INTEGER | DEFAULT 0 | Progress percentage |
| `current_step` | VARCHAR(255) | NULL | Current operation |
| `result_json` | TEXT | NULL | Task result (SUCCESS) |
| `error_message` | TEXT | NULL | Error details (FAILURE) |
| `followed_channel_id` | INTEGER | NULL | Related channel |
| `youtube_video_id` | INTEGER | NULL | Related video |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Task creation |
| `updated_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Last update |
| `started_at` | DATETIME | NULL | Task start time |
| `completed_at` | DATETIME | NULL | Task completion |

**Status Values:**
- `PENDING` - Queued for execution
- `STARTED` - Worker picked up task
- `PROGRESS` - In progress with updates
- `SUCCESS` - Completed successfully
- `FAILURE` - Failed with error
- `RETRY` - Retrying after failure

**Indexes:**
- `idx_celery_task_status_task_id` (UNIQUE)
- `idx_celery_task_status_status`
- `idx_celery_task_status_followed_channel_id`
- `idx_celery_task_status_youtube_video_id`
- `idx_celery_task_status_created_at`

---

### 11. `user_settings`

User preferences and configuration.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO | Unique ID |
| `user_id` | INTEGER | FK(users.id), UNIQUE, NOT NULL | User reference |
| `timezone` | VARCHAR(50) | DEFAULT 'UTC' | User timezone |
| `check_time` | VARCHAR(10) | NULL | Preferred check time |
| `check_frequency` | VARCHAR(20) | DEFAULT 'daily' | Check frequency |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Creation time |
| `updated_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Last update |

**Check Frequency Values:**
- `hourly`, `daily`, `weekly`

---

## Indexes

### Performance-Critical Indexes

```sql
-- Episode queries
CREATE INDEX idx_episodes_channel_id ON episodes(channel_id);
CREATE INDEX idx_episodes_status ON episodes(status);
CREATE UNIQUE INDEX idx_episodes_video_id ON episodes(video_id);

-- YouTube video discovery
CREATE UNIQUE INDEX idx_youtube_videos_video_id ON youtube_videos(video_id);
CREATE INDEX idx_youtube_videos_state ON youtube_videos(state);
CREATE INDEX idx_youtube_videos_channel_state ON youtube_videos(followed_channel_id, state);

-- Notifications (for unread queries)
CREATE INDEX idx_notifications_user_read ON notifications(user_id, read, created_at);

-- Events (for activity log queries)
CREATE INDEX idx_events_created_at ON events(created_at);
CREATE INDEX idx_events_user_id ON events(user_id);

-- Task status (for polling)
CREATE UNIQUE INDEX idx_celery_task_status_task_id ON celery_task_status(task_id);
```

---

## Migration History

| Version | Revision | Description |
|---------|----------|-------------|
| 1 | `79b4815371be` | Initial schema: users, channels, episodes, tags |
| 2 | `138dbddf3ea3` | Add media_file_size to episodes |
| 3 | `210e7d798b58` | Transform video IDs to prefixed format |
| 4 | `36ae9abb89c6` | Add YouTube channel description |
| 5 | `a1b2c3d4e5f6` | Add source_type, original_filename (uploads) |
| 6 | `b2c3d4e5f6g7` | Make video_id nullable |
| 7 | `d6d8d07b41e3` | Add video_id indexes and constraints |
| 8 | `f1a2b3c4d5e6` | Add follow channel feature tables |
| 9 | `7f7abf5fdf3f` | Add timezone to user_settings |
| 10 | `9fb1bc92c905` | Add check_time to user_settings |
| 11 | `7d0e08ad4b92` | Ensure user_settings defaults |
| 12 | `g7h8i9j0k1l2` | Add celery_task_status table |
| 13 | `h9i0j1k2l3m4` | Add notifications table |
| 14 | `37bd0516b334` | Add executed_by to notifications |

### Running Migrations

```bash
# Apply all pending migrations
cd backend && uv run alembic upgrade head

# View current migration status
cd backend && uv run alembic current

# Generate new migration
cd backend && uv run alembic revision --autogenerate -m "description"

# Rollback one migration
cd backend && uv run alembic downgrade -1
```

---

## Database Configuration

### SQLite WAL Mode

The database uses Write-Ahead Logging for better concurrency:

```python
# backend/app/infrastructure/database/connection.py
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
```

### Async Support

The application uses `aiosqlite` for async database operations:

```python
engine = create_async_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
```

### Database URL Configuration

```env
# Development
DATABASE_URL=sqlite:///./data/labcastarr-dev.db

# Production
DATABASE_URL=sqlite:///./data/labcastarr.db
```

---

**End of Document**
