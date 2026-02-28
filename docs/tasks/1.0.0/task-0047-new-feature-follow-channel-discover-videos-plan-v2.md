# Fix Follow Channel Feature - Missing Parts Implementation

## Overview

Fix the Follow Channel feature to work properly with Celery/Redis infrastructure running in Docker. The main issues are: (1) 404 error when loading videos list, (2) Connection refused errors when triggering Celery tasks, (3) Missing retry mechanisms for failed tasks, and (4) Incomplete error handling in the UI.

## Root Cause Analysis

### Issue 1: 404 Error on `/youtube-videos` Endpoint

- **Problem**: The endpoint returns 404 instead of empty array when no videos exist
- **Location**: `backend/app/presentation/api/v1/youtube_videos.py` (line 30-111)
- **Cause**: The endpoint is properly implemented and should return `[]`, but there might be a routing issue or the frontend is calling the wrong URL

### Issue 2: Connection Refused (Errno 111)

- **Problem**: Celery tasks fail with connection refused when triggered
- **Location**:
  - `backend/app/presentation/api/v1/followed_channels.py` (lines 269-298, 310-352)
  - `backend/app/application/services/followed_channel_service.py` (lines 312-343)
- **Cause**: Celery tasks use `.apply_async()` which tries to connect to Redis immediately. If Redis is not accessible, it fails synchronously

### Issue 3: No Retry Mechanism

- **Problem**: Celery tasks don't have retry configuration
- **Location**: All task definitions in `backend/app/infrastructure/tasks/`
- **Cause**: Tasks are defined without `@shared_task` retry parameters

### Issue 4: Incomplete Error Handling

- **Problem**: UI doesn't properly handle task states and errors
- **Location**: Frontend hooks and components
- **Cause**: No task status polling or error state management

## Implementation Plan

### Part 1: Fix Backend - Celery Task Retry Configuration

**File**: `backend/app/infrastructure/tasks/channel_check_tasks.py`

Add retry configuration to all tasks:

- Add `autoretry_for` parameter for automatic retries on specific exceptions
- Add `retry_kwargs` with exponential backoff
- Add `max_retries` limit
- Handle connection errors gracefully

**Changes**:

```python
@shared_task(
    name="...",
    autoretry_for=(ConnectionError, TimeoutError, Exception),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True
)
```

**File**: `backend/app/infrastructure/tasks/backfill_channel_task.py`

Apply same retry configuration as above.

**File**: `backend/app/infrastructure/tasks/create_episode_from_video_task.py`

Apply same retry configuration as above.

### Part 2: Fix Backend - API Endpoint Error Handling

**File**: `backend/app/presentation/api/v1/youtube_videos.py`

Fix the list endpoint to ensure it returns `[]` for empty results:

- Remove any code that raises 404 for empty results
- Ensure the endpoint always returns a list
- Add better error logging

**File**: `backend/app/presentation/api/v1/followed_channels.py`

Improve error handling for trigger_check and trigger_backfill endpoints:

- Wrap Celery task calls in try-except for connection errors
- Return proper error messages when Celery is unavailable
- Add logging for debugging

### Part 3: Fix Backend - Add Task Status Tracking

**File**: `backend/app/infrastructure/database/models/task_status.py` (NEW)

Create a new model to track task execution status:

- Fields: `id`, `task_id`, `task_name`, `status`, `result`, `error_message`, `user_id`, `created_at`, `updated_at`
- Status enum: `PENDING`, `RUNNING`, `SUCCESS`, `FAILURE`, `RETRY`

**File**: Create Alembic migration for task_status table

**File**: `backend/app/infrastructure/tasks/channel_check_tasks.py`

Update tasks to store status in database:

- Store task start in database
- Update status on completion
- Store error messages on failure

### Part 4: Fix Backend - Add Task Status API Endpoints

**File**: `backend/app/presentation/api/v1/tasks.py` (NEW)

Create new endpoints for task status:

- `GET /v1/tasks/{task_id}` - Get task status
- `GET /v1/tasks` - List user's tasks with filters
- `POST /v1/tasks/{task_id}/retry` - Manually retry failed task

### Part 5: Fix Frontend - API Client Updates

**File**: `frontend/src/lib/api-client.ts`

Verify the YouTube videos endpoint URL is correct:

- Should be `/v1/youtube-videos` not `/youtube-videos`
- Add task status endpoints

### Part 6: Fix Frontend - Add Task Status Polling

**File**: `frontend/src/hooks/use-task-status.ts` (NEW)

Create hook for polling task status:

- Poll task status every 2-5 seconds while pending
- Stop polling when task completes or fails
- Handle retry logic

### Part 7: Fix Frontend - Update UI Components

**File**: `frontend/src/components/features/subscriptions/followed-channels-list.tsx`

Update to show task status:

- Show loading state when task is running
- Show success/error notifications
- Add retry button for failed tasks

**File**: `frontend/src/components/features/subscriptions/youtube-videos-list.tsx`

Fix empty state handling:

- Show proper empty state when no videos exist
- Don't show error for empty list
- Show loading state while fetching

### Part 8: Testing & Validation

**Manual Testing Checklist**:

1. Start Docker containers with Redis and Celery
2. Follow a YouTube channel
3. Trigger "check for new videos" - should work without errors
4. Verify videos appear in "Videos" tab
5. Test with channel that has no new videos - should return empty list
6. Stop Celery worker and test error handling
7. Restart Celery and verify retry mechanism works
8. Test backfill functionality
9. Test auto-approve workflow

**Integration Testing**:

- Test Celery task retry mechanism
- Test task status tracking
- Test error notifications in UI
- Test empty state handling

## Key Files to Modify

### Backend Files

1. `backend/app/infrastructure/tasks/channel_check_tasks.py` - Add retry config
2. `backend/app/infrastructure/tasks/backfill_channel_task.py` - Add retry config
3. `backend/app/infrastructure/tasks/create_episode_from_video_task.py` - Add retry config
4. `backend/app/presentation/api/v1/youtube_videos.py` - Fix empty list handling
5. `backend/app/presentation/api/v1/followed_channels.py` - Improve error handling
6. `backend/app/infrastructure/database/models/task_status.py` - NEW: Task status model
7. `backend/app/presentation/api/v1/tasks.py` - NEW: Task status endpoints
8. `backend/alembic/versions/XXXX_add_task_status.py` - NEW: Migration

### Frontend Files

1. `frontend/src/lib/api-client.ts` - Fix URL and add task endpoints
2. `frontend/src/hooks/use-task-status.ts` - NEW: Task status polling hook
3. `frontend/src/components/features/subscriptions/followed-channels-list.tsx` - Update UI
4. `frontend/src/components/features/subscriptions/youtube-videos-list.tsx` - Fix empty state

## Success Criteria

- ✅ Videos tab shows empty array `[]` when no videos exist (no 404 error)
- ✅ "Check for new videos" triggers Celery task successfully
- ✅ "Backfill videos" triggers Celery task successfully
- ✅ Failed tasks automatically retry with exponential backoff
- ✅ UI shows task status (pending, running, success, failure)
- ✅ UI displays proper error messages for different failure scenarios
- ✅ Discovered videos appear in "Videos" tab with all metadata
- ✅ User can create episodes from discovered videos
- ✅ Periodic checks work correctly via Celery Beat
