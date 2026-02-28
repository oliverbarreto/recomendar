# Task 0047: Fix Episode Download Not Starting from YouTube Video

**Date**: 2025-11-14  
**Status**: ✅ Completed

## Problem

When creating an episode from a YouTube video using the "Create Episode from Video" feature:
- Episode is created successfully
- Episode shows "Queued for download" status
- Download never starts - episode remains queued indefinitely

However, when using the "Quick Add" feature (direct YouTube URL):
- Episode is created successfully
- Download starts immediately and completes correctly

## Root Cause

The issue was in `backend/app/infrastructure/tasks/create_episode_from_video_task.py`:

1. **FastAPI BackgroundTasks doesn't work in Celery**: The Celery task was trying to use FastAPI's `BackgroundTasks()` to queue downloads, but `BackgroundTasks` only works within a FastAPI request context. Inside a Celery task, there's no FastAPI request, so the background task never executes.

2. **DownloadService not properly initialized**: The code was creating `DownloadService()` without its required dependencies (`YouTubeService`, `FileService`, `EpisodeRepository`).

3. **Session management**: The database session wasn't being properly closed before queuing the download, which could cause database locks.

## Solution

### Changes Made

**File**: `backend/app/infrastructure/tasks/create_episode_from_video_task.py`

1. **Proper session management** (lines 111-125):
   - Commit episode creation before queuing download
   - Close the session before queuing download to prevent database locks
   - Wait 3 seconds for session cleanup (following the `_isolated_download_queue` pattern)

2. **Proper DownloadService initialization** (lines 127-146):
   - Create a new database session for the download service
   - Properly initialize `YouTubeService`, `FileService`, and `EpisodeRepository`
   - Create `DownloadService` with all required dependencies

3. **Direct queue_download call** (lines 148-155):
   - Call `download_service.queue_download()` directly (not via BackgroundTasks)
   - Pass a dummy `BackgroundTasks` instance (required by API signature but not actually used)
   - The actual queuing happens via `asyncio.Queue`, which works fine in Celery tasks

4. **Improved error handling** (lines 157-170, 187-205):
   - Properly handle download queue failures
   - Reset video state on errors
   - Use separate sessions for error handling to avoid conflicts

### Key Changes

```python
# Before (broken):
download_service = DownloadService()  # Missing dependencies
background_tasks = BackgroundTasks()  # Doesn't work in Celery
await download_service.queue_download(episode_id, background_tasks)

# After (fixed):
# Close session and wait for cleanup
await session.close()
await asyncio.sleep(3)

# Create new session and properly initialize services
download_session = await get_background_task_session()
youtube_service = YouTubeService()
file_service = FileService()
download_episode_repo = EpisodeRepositoryImpl(download_session)

download_service = DownloadService(
    youtube_service=youtube_service,
    file_service=file_service,
    episode_repository=download_episode_repo
)

# Queue download directly (BackgroundTasks is dummy but required by API)
background_tasks = BackgroundTasks()
await download_service.queue_download(episode_id, background_tasks)
```

## How It Works Now

1. **Episode Creation**: Celery task creates the episode and commits it to the database
2. **Session Cleanup**: Closes the session and waits 3 seconds to ensure cleanup
3. **Download Queuing**: Creates a new session, properly initializes DownloadService, and queues the download
4. **Download Processing**: DownloadService's queue processor (running as an asyncio task) picks up the queued download and processes it

## Testing

To test this fix:

1. Navigate to `/subscriptions` → "Videos" tab
2. Click "Create Episode" on any YouTube video
3. Select the channel and click "Create Episode"
4. **Expected**: Episode is created and download starts immediately
5. **Expected**: Episode status changes from "Queued" → "Downloading" → "Completed"
6. **Expected**: Audio file is downloaded and episode is ready

## Related Files

- `backend/app/infrastructure/tasks/create_episode_from_video_task.py` - Fixed Celery task
- `backend/app/infrastructure/services/download_service.py` - Download service implementation
- `backend/app/presentation/api/v1/episodes.py` - Quick Add endpoint (reference implementation)

## Notes

- The fix follows the same pattern as `_isolated_download_queue` used in the Quick Add feature
- DownloadService uses an asyncio.Queue internally, which works fine in Celery tasks
- The 3-second delay ensures database sessions are fully closed before starting downloads
- Each Celery task creates its own DownloadService instance, which is fine since downloads are independent





