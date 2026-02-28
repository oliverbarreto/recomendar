# Task 0047: New Feature: Follow Channel and Discover Videos

## Overview

This feature enables users to follow YouTube channels, automatically discover new videos via periodic checks, and selectively create podcast episodes from discovered videos. The system stores video metadata separately from episodes and manages video lifecycle states.

## Architecture Decisions

### Scheduling: Celery + Redis

**Rationale**: Professional-grade task queue that provides:

- Reliable periodic scheduling (daily, twice weekly, weekly)
- Retry mechanisms and failure handling
- Horizontal scalability for future growth
- Task monitoring and status tracking
- Seamless integration with existing background downloads

**Implementation Approach**:

- Add Redis service to docker-compose
- Add Celery worker service to docker-compose  
- Use Celery Beat for periodic scheduling
- Database-backed task state (SQLite compatible)

### Data Model

- New `followed_channels` table for YouTube channel subscriptions
- New `youtube_videos` table for discovered video metadata (separate from episodes)
- User settings table for global check frequency preference
- Video state enum: `pending_review`, `reviewed`, `queued`, `downloading`, `episode_created`, `discarded`

## Phase 1: Infrastructure Setup

### 1.1 Add Celery + Redis Dependencies

- **Backend**: Add `celery[redis]` and `redis` to `pyproject.toml`
- **Docker**: Add Redis service to all docker-compose files (dev, prod, pre)
- **Docker**: Add Celery worker service to docker-compose
- **Docker**: Add Celery Beat scheduler service to docker-compose
- **Configuration**: Add Redis connection settings to `backend/app/core/config.py`
- **Environment**: Add Redis URL to all `.env` files

### 1.2 Celery Setup

- **File**: Create `backend/app/infrastructure/celery_app.py`
  - Initialize Celery app with Redis broker
  - Configure task routing and serialization
  - Setup task result backend
- **File**: Create `backend/app/infrastructure/celery_config.py`
  - Task timezone settings
  - Task routing rules
  - Worker configuration
- **File**: Create `backend/celery_worker.py` (entry point for worker)
- **File**: Create `backend/celery_beat.py` (entry point for beat scheduler)

## Phase 2: Database Schema

### 2.1 Followed Channels Table

- **Model**: `backend/app/infrastructure/database/models/followed_channel.py`
  - Fields: `id`, `user_id`, `youtube_channel_id`, `youtube_channel_name`, `youtube_channel_url`, `thumbnail_url`, `auto_approve` (boolean), `auto_approve_channel_id` (FK to channels), `last_checked`, `created_at`, `updated_at`
  - Indexes: `user_id`, `youtube_channel_id`, `youtube_channel_id + user_id` (unique)
  - Relationship: `user` (FK to users)

### 2.2 YouTube Videos Table

- **Model**: `backend/app/infrastructure/database/models/youtube_video.py`
  - Fields: `id`, `video_id` (unique YouTube ID), `followed_channel_id` (FK), `title`, `description`, `url`, `thumbnail_url`, `publish_date`, `duration`, `view_count`, `like_count`, `comment_count`, `metadata_json` (raw yt-dlp JSON), `state` (enum), `episode_id` (nullable FK to episodes), `reviewed_at`, `created_at`, `updated_at`
  - Indexes: `video_id`, `followed_channel_id`, `state`, `publish_date`, `followed_channel_id + state`
  - Relationships: `followed_channel`, `episode` (nullable)

### 2.3 User Settings Extension

- **Model**: Extend or create `backend/app/infrastructure/database/models/user_settings.py`
  - Fields: `id`, `user_id` (unique), `subscription_check_frequency` (enum: daily, twice_weekly, weekly), `created_at`, `updated_at`
  - Relationship: `user` (one-to-one)

### 2.4 Database Migration

- **File**: Create Alembic migration `backend/alembic/versions/XXXX_add_follow_channel_feature.py`
  - Create `followed_channels` table
  - Create `youtube_videos` table
  - Create/update `user_settings` table
  - Add foreign key constraints
  - Add indexes

## Phase 3: Domain Layer

### 3.1 Entities

- **File**: `backend/app/domain/entities/followed_channel.py`
  - `FollowedChannel` entity class
  - `SubscriptionCheckFrequency` enum (daily, twice_weekly, weekly)
- **File**: `backend/app/domain/entities/youtube_video.py`
  - `YouTubeVideo` entity class
  - `YouTubeVideoState` enum (pending_review, reviewed, queued, downloading, episode_created, discarded)

### 3.2 Repository Interfaces

- **File**: `backend/app/domain/repositories/followed_channel_repository.py`
  - Interface: `FollowedChannelRepository` with methods for CRUD operations
  - Methods: `create`, `get_by_id`, `get_by_user_id`, `get_by_youtube_channel_id`, `update`, `delete`
- **File**: `backend/app/domain/repositories/youtube_video_repository.py`
  - Interface: `YouTubeVideoRepository` with methods for video management
  - Methods: `create`, `get_by_id`, `get_by_video_id`, `get_by_followed_channel_id`, `get_pending_review`, `update_state`, `list_with_filters`
- **File**: `backend/app/domain/repositories/user_settings_repository.py`
  - Interface: `UserSettingsRepository` for user preferences

### 3.3 Domain Services

- **File**: `backend/app/domain/services/youtube_metadata_service.py`
  - Abstract interface for YouTube metadata extraction
  - Methods: `extract_channel_info`, `extract_video_metadata`, `list_channel_videos`
- **File**: `backend/app/domain/services/channel_discovery_service.py`
  - Business logic for discovering new videos
  - Methods: `discover_new_videos`, `backfill_channel_videos`

## Phase 4: Infrastructure Layer

### 4.1 Repository Implementations

- **File**: `backend/app/infrastructure/repositories/followed_channel_repository_impl.py`
  - Implement `FollowedChannelRepository` using SQLAlchemy
- **File**: `backend/app/infrastructure/repositories/youtube_video_repository_impl.py`
  - Implement `YouTubeVideoRepository` using SQLAlchemy
- **File**: `backend/app/infrastructure/repositories/user_settings_repository_impl.py`
  - Implement `UserSettingsRepository` using SQLAlchemy

### 4.2 YouTube Metadata Service Implementation

- **File**: `backend/app/infrastructure/services/youtube_metadata_service_impl.py`
  - Implement using yt-dlp (similar to video-search-engine project)
  - Use `FullMetadataService` pattern from reference project
  - Methods: Extract channel metadata, video metadata, list videos with pagination
  - Handle: Channel creation date detection, unavailable videos (members-only), error handling

### 4.3 Celery Tasks

- **File**: `backend/app/infrastructure/tasks/channel_check_tasks.py`
  - Task: `check_followed_channel_for_new_videos(followed_channel_id: int)`
    - Fetches latest videos from YouTube channel
    - Compares with existing videos in database
    - Creates new `youtube_videos` records for new videos
    - Updates `last_checked` timestamp
    - Handles auto-approve logic (if enabled)
- **File**: `backend/app/infrastructure/tasks/backfill_channel_task.py`
  - Task: `backfill_followed_channel(followed_channel_id: int, year: Optional[int] = None, max_videos: int = 20)`
    - Fetches historical videos (by year or all)
    - Creates video records without triggering auto-approve
- **File**: `backend/app/infrastructure/tasks/create_episode_from_video_task.py`
  - Task: `create_episode_from_youtube_video(youtube_video_id: int, channel_id: int)`
    - Updates video state to `queued` → `downloading`
    - Downloads audio using existing download service
    - Creates episode record
    - Updates video state to `episode_created`
    - Links episode_id to youtube_video

### 4.4 Celery Beat Schedule

- **File**: `backend/app/infrastructure/celery_beat_schedule.py`
  - Dynamic schedule based on user settings
  - Task: Periodic check task that queries user preferences
  - Routes to appropriate frequency schedules:
    - Daily: Run every day at configurable time
    - Twice weekly: Run on specific days (e.g., Mon/Thu)
    - Weekly: Run once per week

## Phase 5: Application Layer

### 5.1 Application Services

- **File**: `backend/app/application/services/follow_channel_service.py`
  - Use case: Follow a YouTube channel
  - Validates channel URL
  - Extracts channel metadata using YouTube service
  - Creates `followed_channel` record
  - Triggers initial backfill task (async)
  - Returns followed channel info
- **File**: `backend/app/application/services/youtube_video_service.py`
  - Use case: List videos with filters (pending, reviewed, episode_created)
  - Use case: Mark video as reviewed
  - Use case: Discard video
  - Use case: Create episode from video (queues task)
  - Use case: Get video details
- **File**: `backend/app/application/services/channel_discovery_orchestrator.py`
  - Orchestrates periodic checks
  - Queries user settings for frequency
  - Queues channel check tasks based on schedule
  - Handles auto-approve logic

## Phase 6: API Layer

### 6.1 API Routes

- **File**: `backend/app/presentation/api/v1/followed_channels.py`
  - `POST /v1/followed-channels` - Follow a channel (requires YouTube URL)
  - `GET /v1/followed-channels` - List user's followed channels
  - `GET /v1/followed-channels/{id}` - Get followed channel details
  - `PUT /v1/followed-channels/{id}` - Update followed channel (auto-approve settings)
  - `DELETE /v1/followed-channels/{id}` - Unfollow channel (delete pending videos, keep episodes)
  - `POST /v1/followed-channels/{id}/backfill` - Trigger backfill for specific year/all years
- **File**: `backend/app/presentation/api/v1/youtube_videos.py`
  - `GET /v1/youtube-videos` - List videos with filters (state, channel, search)
  - `GET /v1/youtube-videos/{id}` - Get video details
  - `POST /v1/youtube-videos/{id}/review` - Mark as reviewed
  - `POST /v1/youtube-videos/{id}/discard` - Mark as discarded
  - `POST /v1/youtube-videos/{id}/create-episode` - Queue episode creation
  - `GET /v1/youtube-videos/stats` - Get counts by state (for notification bell)

### 6.2 Pydantic Schemas

- **File**: `backend/app/presentation/schemas/followed_channel.py`
  - `FollowedChannelCreate`, `FollowedChannelUpdate`, `FollowedChannelResponse`, `FollowedChannelWithStats`
- **File**: `backend/app/presentation/schemas/youtube_video.py`
  - `YouTubeVideoResponse`, `YouTubeVideoCreateEpisode`, `YouTubeVideoListFilters`, `YouTubeVideoStats`

### 6.3 Register Routes

- **File**: Update `backend/app/main.py`
  - Include followed_channels router
  - Include youtube_videos router
  - Add dependency injection for new services

## Phase 7: Frontend Implementation

### 7.1 Context Menu Extensions

- **File**: `frontend/src/components/features/episodes/episode-card.tsx`
  - Add "Follow Channel" menu item (only for YouTube episodes)
  - Opens confirmation modal
- **File**: `frontend/src/components/features/episodes/episode-detail.tsx`
  - Add "Follow Channel" to context menu
  - Same confirmation modal

### 7.2 Follow Channel Modal

- **File**: `frontend/src/components/features/subscriptions/follow-channel-modal.tsx`
  - Modal form for following a channel
  - Shows channel info preview
  - Options: Auto-approve toggle, target podcast channel selection
  - Triggers API call to follow channel

### 7.3 Subscriptions Page

- **File**: `frontend/src/app/subscriptions/page.tsx`
  - Main subscriptions page component
  - Tabs: Videos, Followed Channels
  - Search and filter functionality
- **File**: `frontend/src/components/features/subscriptions/video-list.tsx`
  - Video grid/list component
  - Filters: pending_review, reviewed, episode_created
  - Search by title/channel
  - Actions: Review, Discard, Create Episode
- **File**: `frontend/src/components/features/subscriptions/followed-channels-list.tsx`
  - List of followed channels
  - Channel cards with stats (total videos, pending count)
  - Actions: Edit settings, Backfill, Unfollow
  - Backfill modal for selecting year/range

### 7.4 Video Card Component

- **File**: `frontend/src/components/features/subscriptions/youtube-video-card.tsx`
  - Video card for subscriptions page
  - Shows: thumbnail, title, channel, publish date, state badge
  - Actions: View on YouTube, Review, Discard, Create Episode
  - State indicators (pending, reviewed, downloading, episode_created)

### 7.5 Notification Bell

- **File**: Update `frontend/src/components/layout/header.tsx`
  - Add notification bell icon (Bell from lucide-react)
  - Badge showing count of pending_review videos
  - Link to /subscriptions?filter=pending
  - Hook: `use-pending-videos-count.ts` for real-time count

### 7.6 API Hooks

- **File**: `frontend/src/hooks/use-followed-channels.ts`
  - `useFollowedChannels`, `useFollowChannel`, `useUnfollowChannel`, `useUpdateFollowedChannel`, `useBackfillChannel`
- **File**: `frontend/src/hooks/use-youtube-videos.ts`
  - `useYouTubeVideos`, `useYouTubeVideo`, `useMarkVideoReviewed`, `useDiscardVideo`, `useCreateEpisodeFromVideo`, `useVideoStats`

### 7.7 Types

- **File**: Update `frontend/src/types/index.ts`
  - Add `FollowedChannel` interface
  - Add `YouTubeVideo` interface
  - Add `YouTubeVideoState` enum
  - Add `SubscriptionCheckFrequency` enum

### 7.8 Navigation Updates

- **File**: Update `frontend/src/components/layout/sidebar.tsx`
  - Add "Subscriptions" navigation item (icon: Bell or Users)

### 7.9 Settings Integration

- **File**: Update `frontend/src/components/features/settings/settings-interface.tsx`
  - Add "Subscriptions" section
  - Setting: Global check frequency (daily, twice weekly, weekly)
  - Default time for daily checks

## Phase 8: Auto-Approve Logic

### 8.1 Auto-Approve Implementation

- **File**: Update `backend/app/infrastructure/tasks/channel_check_tasks.py`
  - When auto-approve is enabled:
    - New videos automatically transition to `queued` state
    - Queue `create_episode_from_youtube_video` task immediately
    - Use `auto_approve_channel_id` to determine target podcast channel

### 8.2 Auto-Approve Settings UI

- **File**: Update `follow-channel-modal.tsx`
  - Add toggle for auto-approve
  - Show channel selector when auto-approve enabled
  - Store selection in `auto_approve_channel_id`

## Phase 9: Testing & Validation

### 9.1 Backend Tests

- Test YouTube metadata extraction
- Test video discovery logic
- Test Celery task execution
- Test state transitions
- Test auto-approve workflow

### 9.2 Frontend Tests

- Test video list filtering
- Test follow channel flow
- Test notification bell count
- Test video state transitions

### 9.3 Integration Tests

- Test end-to-end: Follow → Discover → Create Episode
- Test periodic check scheduling
- Test backfill functionality

## Phase 10: Documentation

### 10.1 API Documentation

- Update OpenAPI/Swagger docs with new endpoints
- Document request/response schemas
- Document error codes

### 10.2 User Documentation

- Document how to follow channels
- Document subscriptions page usage
- Document auto-approve feature

### 10.3 Developer Documentation

- Document Celery setup and configuration
- Document task scheduling system
- Document database schema relationships

## Key Implementation Details

### Video State Machine

```
pending_review → reviewed (user action)
pending_review → queued (create episode action)
queued → downloading (task started)
downloading → episode_created (task completed)
pending_review → discarded (user action)
```

### Periodic Check Logic

- User selects global frequency (daily, twice weekly, weekly)
- Celery Beat schedules task based on frequency
- Task queries all followed channels for user
- Queues `check_followed_channel_for_new_videos` for each channel
- Updates `last_checked` timestamp

### Initial Backfill

- When following a channel:
  - Extract channel metadata (including creation date if available)
  - Queue `backfill_followed_channel` task with `max_videos=20`, `year=current_year`
  - Task runs independently of periodic checks
  - User can trigger additional backfills via UI

### Video Deletion Rules

- When unfollowing a channel:
  - Delete all `youtube_videos` records in `pending_review` or `reviewed` states
  - Delete all `youtube_videos` records in `queued` or `downloading` states (cancels in-progress)
  - Keep `youtube_videos` records where `episode_id` is not null (episode_created state)
  - Delete `followed_channel` record
  - Episodes remain in database (already created)