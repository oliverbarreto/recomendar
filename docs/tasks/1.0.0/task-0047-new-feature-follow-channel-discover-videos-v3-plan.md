# Follow Channels Feature Enhancement Plan

## Overview

This plan implements three major feature enhancements to the Follow Channels functionality:

1. Advanced Filtering for Videos page
2. Task Progress UI with real-time feedback
3. Notification System for discovered videos and created episodes

## Phase 1: Advanced Filtering for Videos Page

### 1.1 Add YouTube Channel Filter Dropdown

**Backend Changes:**

- No backend changes needed - the API already supports `followed_channel_id` filter parameter in `GET /v1/youtube-videos`

**Frontend Changes:**

- Update `frontend/src/components/features/subscriptions/video-list.tsx`:
- Add a Select dropdown for filtering by YouTube channel (currently missing)
- Position it between the state filter and view mode buttons
- Fetch followed channels using `useFollowedChannels()` hook
- Update URL params to include `channel` parameter (already implemented but not exposed in UI)
- Sync selected channel with URL params for bookmarking

**Files to modify:**

- `frontend/src/components/features/subscriptions/video-list.tsx` (lines 301-344)

### 1.2 Add Date Range/Year Filtering

**Backend Changes:**

- Update `backend/app/infrastructure/repositories/youtube_video_repository_impl.py`:
- Add `publish_year` and `publish_date_range` parameters to `search()` method
- Add SQL filters for `publish_date` field using year or date range

- Update `backend/app/application/services/youtube_video_service.py`:
- Add year/date range parameters to `search_videos()` method
- Pass through to repository

- Update `backend/app/presentation/api/v1/youtube_videos.py`:
- Add optional query parameters: `publish_year: Optional[int]` and `publish_date_from/to: Optional[date]`
- Pass to service layer

- Update `backend/app/presentation/schemas/youtube_video_schemas.py`:
- Add year/date range fields to search request schema if needed

**Frontend Changes:**

- Update `frontend/src/components/features/subscriptions/video-list.tsx`:
- Add year filter dropdown (2020-current year, "All Years" option)
- Position near channel filter
- Update URL params to include `year` parameter
- Update API call to include year filter

- Update `frontend/src/hooks/use-youtube-videos.ts`:
- Add year parameter to filter interface
- Pass to API client

- Update `frontend/src/lib/api-client.ts`:
- Add year parameter to `getYouTubeVideos()` method

**Files to modify:**

- `backend/app/infrastructure/repositories/youtube_video_repository_impl.py`
- `backend/app/application/services/youtube_video_service.py`
- `backend/app/presentation/api/v1/youtube_videos.py`
- `frontend/src/components/features/subscriptions/video-list.tsx`
- `frontend/src/hooks/use-youtube-videos.ts`
- `frontend/src/lib/api-client.ts`

### 1.3 Add Bulk Operations

**Backend Changes:**

- Create new endpoint `POST /v1/youtube-videos/bulk-action`:
- Accept `video_ids: List[int]` and `action: str` (review, discard, create_episode)
- For `create_episode` action, require `channel_id: int`
- Process each video in a loop, applying the action
- Return summary of successful/failed operations

- Update `backend/app/application/services/youtube_video_service.py`:
- Add `bulk_mark_as_reviewed()`, `bulk_discard()`, `bulk_create_episodes()` methods
- Handle validation and error collection

- Update `backend/app/presentation/schemas/youtube_video_schemas.py`:
- Add `BulkActionRequest` schema with `video_ids`, `action`, and optional `channel_id`
- Add `BulkActionResponse` schema with success/failure counts and details

**Frontend Changes:**

- Update `frontend/src/components/features/subscriptions/video-list.tsx`:
- Add checkbox selection mode (toggle with a "Select" button in toolbar)
- Add "Select All" checkbox in header when in selection mode
- Add bulk action toolbar that appears when videos are selected
- Include buttons: "Mark as Reviewed", "Discard", "Create Episodes"
- For "Create Episodes", show channel selection dialog
- Clear selection after bulk action completes

- Update `frontend/src/components/features/subscriptions/youtube-video-card.tsx`:
- Add checkbox overlay when in selection mode
- Handle click to toggle selection

- Update `frontend/src/hooks/use-youtube-videos.ts`:
- Add `useBulkAction()` mutation hook

- Update `frontend/src/lib/api-client.ts`:
- Add `bulkActionVideos()` method

**Files to modify:**

- `backend/app/presentation/api/v1/youtube_videos.py` (new endpoint)
- `backend/app/application/services/youtube_video_service.py`
- `backend/app/presentation/schemas/youtube_video_schemas.py`
- `frontend/src/components/features/subscriptions/video-list.tsx`
- `frontend/src/components/features/subscriptions/youtube-video-card.tsx`
- `frontend/src/hooks/use-youtube-videos.ts`
- `frontend/src/lib/api-client.ts`

## Phase 2: Task Progress UI with Real-time Feedback

### 2.1 Backend Infrastructure - Task Status Tracking

**Database Schema:**

- The `celery_task_status` table already exists (created in previous implementation)
- Verify columns: `task_id`, `task_name`, `status`, `progress`, `current_step`, `result_json`, `error_message`, `followed_channel_id`, `youtube_video_id`, timestamps

**Backend Changes:**

- Update `backend/app/infrastructure/tasks/channel_check_tasks.py`:
- In `check_followed_channel_for_new_videos()` task, create/update `CeleryTaskStatus` record
- Update progress at key milestones (0%, 50%, 100%)
- Store result JSON with video counts

- Update `backend/app/infrastructure/tasks/backfill_channel_task.py`:
- In `backfill_followed_channel()` task, create/update `CeleryTaskStatus` record
- Update progress during video discovery
- Store result JSON with backfill stats

- Create repository for task status:
- `backend/app/infrastructure/repositories/celery_task_status_repository_impl.py`
- Methods: `create()`, `update()`, `get_by_task_id()`, `get_by_followed_channel_id()`

- Create service for task status:
- `backend/app/application/services/celery_task_status_service.py`
- Methods: `get_task_status()`, `get_channel_task_status()`

- Create API endpoints:
- `GET /v1/celery-tasks/{task_id}` - Get task status by ID
- `GET /v1/followed-channels/{id}/task-status` - Get latest task status for channel

- Create schemas:
- `backend/app/presentation/schemas/celery_task_status_schemas.py`
- `CeleryTaskStatusResponse` with all task details

**Files to create:**

- `backend/app/infrastructure/repositories/celery_task_status_repository_impl.py`
- `backend/app/application/services/celery_task_status_service.py`
- `backend/app/presentation/api/v1/celery_tasks.py`
- `backend/app/presentation/schemas/celery_task_status_schemas.py`

**Files to modify:**

- `backend/app/infrastructure/tasks/channel_check_tasks.py`
- `backend/app/infrastructure/tasks/backfill_channel_task.py`
- `backend/app/core/dependencies.py` (add service dependencies)

### 2.2 Frontend UI - Status Indicators and Progress Display

**Frontend Changes:**

- Update `frontend/src/types/index.ts`:
- Add `CeleryTaskStatus` interface
- Add task status fields to `FollowedChannel` interface

- Create new hook `frontend/src/hooks/use-task-status.ts`:
- `useTaskStatus(taskId)` - Poll task status every 2 seconds while task is running
- `useChannelTaskStatus(channelId)` - Get latest task status for channel
- Auto-stop polling when task completes/fails

- Update `frontend/src/lib/api-client.ts`:
- Add `getTaskStatus(taskId)` method
- Add `getChannelTaskStatus(channelId)` method

- Update `frontend/src/components/features/subscriptions/followed-channels-list.tsx`:
- Add status indicator badge on each channel card (pending/in progress/completed/failed)
- Show progress bar when task is running
- Display task result summary (e.g., "5 new videos discovered")
- Add clickable badges that navigate to Videos page with filters applied
- Poll task status when `last_check_task_id` or `last_backfill_task_id` exists
- Show different icons for different task states (spinner, check, error)

- Create new component `frontend/src/components/features/subscriptions/task-status-badge.tsx`:
- Reusable badge component for task status display
- Props: `taskId`, `taskType`, `onComplete` callback
- Handles polling internally

- Create new component `frontend/src/components/features/subscriptions/channel-stats-badges.tsx`:
- Display video counts by state (pending/reviewed/discarded)
- Each badge is clickable and navigates to Videos page with filters
- Props: `channelId`, `stats` object

**Files to create:**

- `frontend/src/hooks/use-task-status.ts`
- `frontend/src/components/features/subscriptions/task-status-badge.tsx`
- `frontend/src/components/features/subscriptions/channel-stats-badges.tsx`

**Files to modify:**

- `frontend/src/types/index.ts`
- `frontend/src/lib/api-client.ts`
- `frontend/src/components/features/subscriptions/followed-channels-list.tsx`

## Phase 3: Notification System

### 3.1 Backend - Notification Infrastructure

**Database Schema:**

- Create new table `notifications`:
- `id`, `user_id`, `type` (enum: video_discovered, episode_created), `title`, `message`, `data_json`, `read`, `created_at`
- Indexes on `user_id`, `read`, `created_at`

- Create Alembic migration:
- `backend/alembic/versions/xxx_add_notifications_table.py`

**Backend Changes:**

- Create domain entity:
- `backend/app/domain/entities/notification.py`
- `Notification` dataclass with fields and `mark_as_read()` method

- Create database model:
- `backend/app/infrastructure/database/models/notification.py`
- SQLAlchemy model for notifications table

- Create repository:
- `backend/app/infrastructure/repositories/notification_repository_impl.py`
- Methods: `create()`, `get_by_user()`, `mark_as_read()`, `mark_all_as_read()`, `delete()`

- Create service:
- `backend/app/application/services/notification_service.py`
- Methods: `create_notification()`, `get_user_notifications()`, `mark_as_read()`, `get_unread_count()`
- Helper methods: `notify_videos_discovered()`, `notify_episode_created()`

- Update Celery tasks to create notifications:
- `backend/app/infrastructure/tasks/channel_check_tasks.py`:
- After discovering videos, call `notification_service.notify_videos_discovered()`
- `backend/app/infrastructure/tasks/create_episode_from_video_task.py`:
- After creating episode, call `notification_service.notify_episode_created()`

- Update FastAPI routes to create notifications:
- `backend/app/presentation/api/v1/episodes.py`:
- After Quick Add Episode, create notification
- After Create Episode from local file, create notification
- `backend/app/presentation/api/v1/youtube_videos.py`:
- After Create Episode from Video (manual trigger), create notification

- Create API endpoints:
- `GET /v1/notifications` - List user notifications (with pagination, filter by read/unread)
- `GET /v1/notifications/unread-count` - Get unread notification count
- `PUT /v1/notifications/{id}/read` - Mark notification as read
- `PUT /v1/notifications/mark-all-read` - Mark all as read
- `DELETE /v1/notifications/{id}` - Delete notification

- Create schemas:
- `backend/app/presentation/schemas/notification_schemas.py`
- `NotificationResponse`, `NotificationListResponse`, `UnreadCountResponse`

**Files to create:**

- `backend/alembic/versions/xxx_add_notifications_table.py`
- `backend/app/domain/entities/notification.py`
- `backend/app/infrastructure/database/models/notification.py`
- `backend/app/infrastructure/repositories/notification_repository_impl.py`
- `backend/app/application/services/notification_service.py`
- `backend/app/presentation/api/v1/notifications.py`
- `backend/app/presentation/schemas/notification_schemas.py`

**Files to modify:**

- `backend/app/infrastructure/tasks/channel_check_tasks.py`
- `backend/app/infrastructure/tasks/create_episode_from_video_task.py`
- `backend/app/presentation/api/v1/episodes.py`
- `backend/app/presentation/api/v1/youtube_videos.py`
- `backend/app/core/dependencies.py`
- `backend/app/infrastructure/database/models/__init__.py`

### 3.2 Frontend - Notification UI

**Frontend Changes:**

- Update `frontend/src/types/index.ts`:
- Add `Notification` interface
- Add `NotificationType` enum

- Create hook `frontend/src/hooks/use-notifications.ts`:
- `useNotifications()` - Fetch notifications list
- `useUnreadCount()` - Poll unread count every 30 seconds
- `useMarkAsRead()` - Mark notification as read mutation
- `useMarkAllAsRead()` - Mark all as read mutation
- `useDeleteNotification()` - Delete notification mutation

- Update `frontend/src/lib/api-client.ts`:
- Add notification API methods

- Create notification bell component `frontend/src/components/layout/notification-bell.tsx`:
- Bell icon with unread count badge
- Dropdown popover with notification list
- Click notification to mark as read and navigate to relevant page
- "Mark all as read" button
- Empty state when no notifications

- Update `frontend/src/components/layout/sidepanel.tsx`:
- Add notification bell to header/toolbar area
- Position near user profile or settings

- Create notification item component `frontend/src/components/features/notifications/notification-item.tsx`:
- Display notification with icon, title, message, timestamp
- Handle click to navigate and mark as read
- Delete button

- Create notification list page (optional) `frontend/src/app/notifications/page.tsx`:
- Full page view of all notifications
- Filter by read/unread
- Pagination

**Files to create:**

- `frontend/src/hooks/use-notifications.ts`
- `frontend/src/components/layout/notification-bell.tsx`
- `frontend/src/components/features/notifications/notification-item.tsx`
- `frontend/src/app/notifications/page.tsx` (optional)

**Files to modify:**

- `frontend/src/types/index.ts`
- `frontend/src/lib/api-client.ts`
- `frontend/src/components/layout/sidepanel.tsx`

## Testing Strategy

### Phase 1 Testing:

- Test channel filter dropdown with multiple channels
- Test year filter with videos from different years
- Test bulk operations with various selections
- Test URL params persistence and browser back/forward

### Phase 2 Testing:

- Test task status polling during check/backfill operations
- Test progress indicators update correctly
- Test clickable badges navigate with correct filters
- Test polling stops when task completes

### Phase 3 Testing:

- Test notifications created for video discovery
- Test notifications created for episode creation (all paths)
- Test notification bell updates in real-time
- Test mark as read functionality
- Test navigation from notifications

## Implementation Notes

- All URL params in Videos page should be synced (state, channel, year, search)
- Task status polling should use exponential backoff if needed
- Notification polling should be efficient (only fetch count, not full list)
- Consider adding toast notifications for immediate feedback
- Bulk operations should show progress indicator for large selections
- Error handling should be comprehensive with user-friendly messages

## Implementation Plan

Phase 1.1: Add YouTube Channel Filter Dropdown to Videos page
Phase 1.2: Add Date Range/Year Filtering (backend + frontend)
Phase 1.3: Add Bulk Operations for videos (select multiple, perform actions)
Phase 2.1: Implement Backend Infrastructure for Task Status Tracking
Phase 2.2: Implement Frontend Ul for Task Progress Display
Phase 3.1: Implement Backend Notification Infrastructure
Phase 3.2: Implement Frontend Notification Ul
