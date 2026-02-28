# Task 0047: Celery Download Service Implementation

**Date**: 2025-11-14  
**Status**: ✅ Completed

## Problem

When creating episodes from YouTube videos via Celery tasks, downloads were not starting. The issue was that `DownloadService` uses FastAPI's `BackgroundTasks` and an `asyncio.Queue` with a persistent queue processor, which doesn't work within Celery's event loop lifecycle. Celery tasks create and close event loops, destroying any async tasks that depend on a persistent loop.

## Solution: Mixed Approach

Following the user's requirements, we implemented a **mixed approach** that:
1. **Keeps FastAPI DownloadService intact** - No changes to existing working code
2. **Creates a separate CeleryDownloadService** - Cloned download logic for Celery compatibility
3. **Maintains independence** - Both paths work independently for now
4. **Future-ready** - Easy migration path when FastAPI also moves to Celery tasks

## Implementation

### Files Created

1. **`backend/app/infrastructure/services/celery_download_service.py`**
   - Cloned download logic from `DownloadService._download_episode_task()`
   - Removed queue mechanism (`asyncio.Queue`, `_process_queue()`, `BackgroundTasks`)
   - Direct execution model compatible with Celery's event loop lifecycle
   - Includes `CeleryDownloadProgress` class for progress tracking
   - Same error handling, retry logic, and database lock handling

2. **`backend/app/infrastructure/tasks/download_episode_task.py`**
   - Celery task wrapper for `CeleryDownloadService`
   - Uses `_run_async()` pattern consistent with other Celery tasks
   - Handles service initialization and event service setup
   - Includes retry configuration for network errors

### Files Modified

1. **`backend/app/infrastructure/tasks/create_episode_from_video_task.py`**
   - Removed `DownloadService` usage
   - Now queues `download_episode` Celery task instead
   - Passes `user_id` and `channel_id` for event tracking
   - Returns `download_task_id` in response

## Architecture

### FastAPI Path (Unchanged)
```
API Request → EpisodeService.create_from_youtube_url()
  → DownloadService.queue_download()
    → asyncio.Queue → _process_queue() (persistent loop)
      → _download_episode_task()
```

### Celery Path (New)
```
Celery Task → create_episode_from_video_task()
  → download_episode.apply_async() (Celery task)
    → CeleryDownloadService.download_episode() (direct execution)
      → Download completes within Celery's event loop
```

## Key Differences

| Feature | FastAPI DownloadService | CeleryDownloadService |
|---------|------------------------|----------------------|
| **Queue Mechanism** | `asyncio.Queue` + persistent processor | None - direct execution |
| **BackgroundTasks** | Required (FastAPI) | Not used |
| **Event Loop** | Persistent (FastAPI app) | Created per task (`_run_async`) |
| **Concurrency** | Queue-based (`max_concurrent`) | Celery worker concurrency |
| **Progress Tracking** | In-memory dict | Per-task instance |
| **Error Handling** | Same | Same |
| **Retry Logic** | Same | Same |

## Code Structure

```
backend/app/infrastructure/
├── services/
│   ├── download_service.py (existing - FastAPI, unchanged)
│   └── celery_download_service.py (NEW - Celery-compatible)
└── tasks/
    ├── create_episode_from_video_task.py (updated to use Celery task)
    └── download_episode_task.py (NEW - Celery task wrapper)
```

## Benefits

1. **Zero Risk**: FastAPI code completely untouched
2. **Clear Separation**: FastAPI vs Celery paths are distinct
3. **Independent Testing**: Can test Celery path without affecting FastAPI
4. **Easy Migration**: When ready, FastAPI can switch to Celery tasks
5. **Consistent Patterns**: Follows existing Celery task patterns
6. **Same Logic**: Download logic is identical, just execution model differs

## Testing

To test the implementation:

1. **Rebuild Docker containers**:
   ```bash
   docker compose --env-file .env.production -f docker-compose.prod.yml build celery-worker
   docker compose --env-file .env.production -f docker-compose.prod.yml restart celery-worker
   ```

2. **Create episode from YouTube video**:
   - Navigate to `/subscriptions` → "Videos" tab
   - Click "Create Episode" on any video
   - Select channel and create

3. **Expected behavior**:
   - Episode is created
   - Celery download task is queued
   - Download starts immediately (status changes: "Queued" → "Downloading" → "Completed")
   - Audio file downloads successfully

4. **Verify in logs**:
   ```bash
   docker compose --env-file .env.production -f docker-compose.prod.yml logs -f celery-worker
   ```
   Should see:
   - "Queued Celery download task for episode X"
   - "Starting Celery download task for episode X"
   - "Successfully downloaded episode X"

## Future Migration Path

When ready to migrate FastAPI to also use Celery tasks:

1. Update FastAPI endpoints to queue `download_episode` Celery task instead of using `DownloadService.queue_download()`
2. Remove `DownloadService` queue mechanism (or keep for backward compatibility)
3. Both paths will use the same Celery task infrastructure

## Related Files

- `backend/app/infrastructure/services/celery_download_service.py` - Celery-compatible download service
- `backend/app/infrastructure/tasks/download_episode_task.py` - Celery task wrapper
- `backend/app/infrastructure/tasks/create_episode_from_video_task.py` - Updated to use Celery task
- `backend/app/infrastructure/services/download_service.py` - FastAPI service (unchanged)

## Notes

- The implementation intentionally duplicates download logic to keep paths independent
- Both services use the same underlying dependencies (`YouTubeService`, `FileService`, `EpisodeRepository`)
- Event service is optional and gracefully handled if unavailable
- Database session management follows the same pattern as other Celery tasks
- Error handling and retry logic are identical between both services





