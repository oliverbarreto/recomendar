# Implementation Plan: Fix Celery Task Status Display for Followed YouTube Channels

**Task ID:** task-0057
**Date:** 2025-11-30
**Status:** Plan Ready for Implementation

---

## Problem Summary

When users click "Search for new videos" on a followed YouTube channel, the UI shows "queued" status for the entire task execution (30-60 seconds), then suddenly jumps to "completed". This creates poor UX as users don't know if the task is actually running or stuck.

### Expected Behavior
```
✓ PENDING (0-1 sec)   → Shows "queued" → Task waiting in queue
✓ STARTED (1-2 sec)   → Shows "searching" → Worker picked up task
✓ PROGRESS (2-50 sec) → Shows "searching" with animation → Actively discovering videos
✓ SUCCESS (~50 sec)   → Shows "updated: {timestamp}" → Task completed
```

### Current Behavior
```
✗ PENDING (0-1 sec)   → Shows "queued"
✗ STARTED (1-50 sec)  → Shows "queued" ← WRONG - stays here entire time
✗ SUCCESS (~50 sec)   → Shows "updated: {timestamp}" ← Jumps suddenly
```

---

## Root Cause Analysis

### 1. Backend Issue: Missing Progress Updates

**Files Affected:**
- `backend/app/infrastructure/tasks/channel_check_rss_tasks.py` (RSS method)
- `backend/app/infrastructure/tasks/channel_check_tasks.py` (yt-dlp method)

**Problem:** Tasks only update status twice:
- Line ~100: `task_status.mark_started()` → Sets status to STARTED
- Line ~180: `task_status.mark_success()` → Sets status to SUCCESS
- **Missing:** No `task_status.update_progress()` calls during execution

**Impact:** Status skips the PROGRESS state entirely (PENDING → STARTED → SUCCESS)

### 2. Frontend Issue: Status Mapping

**File Affected:**
- `frontend/src/components/features/subscriptions/followed-channels-list.tsx`

**Problem:** Lines 144-152 map both PENDING and STARTED to "queued":
```typescript
case "PENDING":
case "STARTED":
  return {
    icon: MonitorPause,
    label: "queued",  // ← Both map to same label!
    colorClass: "text-yellow-500",
  }
```

**Impact:** Even when task is actively running (STARTED), UI still shows "queued"

---

## Implementation Plan

### Phase 1: Backend Changes (Both Task Files)

#### File 1: `backend/app/infrastructure/tasks/channel_check_rss_tasks.py`

Add progress updates at 5 strategic points in the `_check_channel_rss()` async function:

**Location 1 - After mark_started() (after line 103):**
```python
# Mark task as started
if task_status:
    task_status.mark_started()
    await task_status_repo.update(task_status)
    logger.info(f"Marked task {self.request.id} as started")

    # NEW: Update progress to show task is initializing
    task_status.update_progress(10, "Initializing RSS discovery")
    await task_status_repo.update(task_status)
```

**Location 2 - Before RSS discovery (before line 127):**
```python
# NEW: Update progress before fetching RSS feed
if task_status:
    task_status.update_progress(20, "Fetching RSS feed")
    await task_status_repo.update(task_status)

# Discover new videos using RSS
logger.info(f"[RSS Task] Starting discovery for channel {followed_channel_id}")
new_videos = await discovery_strategy.discover_new_videos(
    followed_channel=followed_channel,
    max_videos=50
)
```

**Location 3 - After discovery (after line 132):**
```python
logger.info(f"[RSS Task] Discovered {len(new_videos)} new videos")

# NEW: Update progress after discovery
if task_status:
    task_status.update_progress(60, f"Discovered {len(new_videos)} new videos")
    await task_status_repo.update(task_status)
```

**Location 4 - After last_checked update (after line 135):**
```python
# Update last_checked timestamp
await followed_channel_repo.update_last_checked(followed_channel.id)

# NEW: Update progress after saving data
if task_status:
    task_status.update_progress(80, "Saving discovery results")
    await task_status_repo.update(task_status)
```

**Location 5 - Before auto-approve loop (before line 138):**
```python
# Handle auto-approve if enabled
if followed_channel.auto_approve and followed_channel.auto_approve_channel_id:
    logger.info(f"Auto-approve enabled for channel {followed_channel_id}")

    # NEW: Update progress before auto-approve processing
    if task_status:
        task_status.update_progress(90, f"Auto-approving {len(new_videos)} videos")
        await task_status_repo.update(task_status)

    # Queue episode creation for each new video
    from app.infrastructure.tasks.create_episode_from_video_task import create_episode_from_youtube_video
```

#### File 2: `backend/app/infrastructure/tasks/channel_check_tasks.py`

Apply identical progress update pattern to `_check_channel()` function:

**Location 1 - After mark_started() (after line 96):**
```python
# Mark task as started
if task_status:
    task_status.mark_started()
    await task_status_repo.update(task_status)
    logger.info(f"Marked task {self.request.id} as started")

    # NEW: Update progress to show task is initializing
    task_status.update_progress(10, "Initializing yt-dlp discovery")
    await task_status_repo.update(task_status)
```

**Location 2 - Before discovery (before line 120):**
```python
# NEW: Update progress before fetching videos
if task_status:
    task_status.update_progress(20, "Fetching channel videos via yt-dlp")
    await task_status_repo.update(task_status)

# Discover new videos
new_videos = await discovery_strategy.discover_new_videos(
    followed_channel=followed_channel,
    max_videos=50
)
```

**Location 3 - After discovery (after line 123):**
```python
# After discovery completes
# NEW: Update progress after discovery
if task_status:
    task_status.update_progress(60, f"Discovered {len(new_videos)} new videos")
    await task_status_repo.update(task_status)
```

**Location 4 - After last_checked update (after line 126):**
```python
# Update last_checked timestamp
await followed_channel_repo.update_last_checked(followed_channel.id)

# NEW: Update progress after saving data
if task_status:
    task_status.update_progress(80, "Saving discovery results")
    await task_status_repo.update(task_status)
```

**Location 5 - Before auto-approve loop (before line 129):**
```python
# Handle auto-approve if enabled
if followed_channel.auto_approve and followed_channel.auto_approve_channel_id:
    logger.info(f"Auto-approve enabled for channel {followed_channel_id}")

    # NEW: Update progress before auto-approve processing
    if task_status:
        task_status.update_progress(90, f"Auto-approving {len(new_videos)} videos")
        await task_status_repo.update(task_status)

    # Queue episode creation for each new video
    from app.infrastructure.tasks.create_episode_from_video_task import create_episode_from_youtube_video
```

#### Error Handling Pattern

All progress updates should include try-except to prevent task failure if progress update fails:

```python
# Optional: Wrap progress updates in try-except
try:
    if task_status:
        task_status.update_progress(60, f"Discovered {len(new_videos)} new videos")
        await task_status_repo.update(task_status)
except Exception as progress_error:
    # Log but don't fail the task
    logger.warning(f"Failed to update progress: {progress_error}")
```

---

### Phase 2: Frontend Changes

#### File: `frontend/src/components/features/subscriptions/followed-channels-list.tsx`

**Change Lines 144-160** - Separate PENDING and STARTED cases:

**BEFORE:**
```typescript
function getTaskStatusDisplay(
  taskStatus: CeleryTaskStatus | null | undefined,
  lastChecked: string | undefined
) {
  if (taskStatus) {
    switch (taskStatus.status) {
      case "PENDING":
      case "STARTED":                    // ← Combined with PENDING
        return {
          icon: MonitorPause,
          label: "queued",               // ← Shows "queued" for both
          colorClass: "text-yellow-500",
          bgClass: "bg-yellow-100 dark:bg-yellow-900/30",
        }
      case "PROGRESS":
        return {
          icon: MonitorCog,
          label: "searching",
          colorClass: "text-blue-500",
          bgClass: "bg-blue-100 dark:bg-blue-900/30",
          animate: true,
        }
      // ... rest of cases
    }
  }
}
```

**AFTER:**
```typescript
function getTaskStatusDisplay(
  taskStatus: CeleryTaskStatus | null | undefined,
  lastChecked: string | undefined
) {
  if (taskStatus) {
    switch (taskStatus.status) {
      case "PENDING":
        return {
          icon: MonitorPause,
          label: "queued",
          colorClass: "text-yellow-500",
          bgClass: "bg-yellow-100 dark:bg-yellow-900/30",
        }
      case "STARTED":                    // ← Separated from PENDING
      case "PROGRESS":                   // ← Both show "searching"
        return {
          icon: MonitorCog,
          label: "searching",            // ← Now shows "searching" for STARTED
          colorClass: "text-blue-500",
          bgClass: "bg-blue-100 dark:bg-blue-900/30",
          animate: true,                 // ← Spinning animation for both
        }
      case "SUCCESS":
        return {
          icon: CircleCheck,
          label: lastChecked
            ? `updated: ${safeFormatDate(
                lastChecked,
                "dd/MM/yyyy HH:mm",
                "completed"
              )}`
            : "completed",
          colorClass: "text-green-500",
          bgClass: "bg-green-100 dark:bg-green-900/30",
        }
      // ... rest unchanged
    }
  }
}
```

**Rationale:**
- PENDING = Task in queue (not yet picked up) → Show "queued"
- STARTED = Task started execution → Show "searching" with animation
- PROGRESS = Task actively progressing → Show "searching" with animation

---

## Deployment Strategy

### Order of Deployment

**CRITICAL:** Deploy backend BEFORE frontend to avoid UI expecting PROGRESS state that doesn't exist yet.

**Step 1: Deploy Backend (Both Task Files)**
- Changes are backward compatible (existing tasks without progress still work)
- New tasks will immediately start using PROGRESS state
- No database migration needed (progress field already exists)

**Step 2: Deploy Frontend**
- Once backend is deployed, frontend can safely expect STARTED/PROGRESS states
- STARTED now correctly shows "searching" instead of "queued"

### Rollback Plan

If issues arise:

**Backend Rollback:**
```python
# Comment out all progress update blocks
# if task_status:
#     task_status.update_progress(10, "Initializing...")
#     await task_status_repo.update(task_status)
```

**Frontend Rollback:**
```typescript
// Revert to combined cases
case "PENDING":
case "STARTED":
  return { label: "queued", ... }
```

---

## Testing Plan

### Unit Tests

**Backend Tests:**
```python
# Test progress updates are called
async def test_check_rss_updates_progress():
    # Mock task status repository
    # Call check_followed_channel_for_new_videos_rss
    # Assert update_progress was called 5 times
    # Assert progress values: 10, 20, 60, 80, 90
```

**Frontend Tests:**
```typescript
// Test status mapping
test('PENDING shows queued', () => {
  const result = getTaskStatusDisplay({ status: 'PENDING' }, undefined)
  expect(result.label).toBe('queued')
})

test('STARTED shows searching', () => {
  const result = getTaskStatusDisplay({ status: 'STARTED' }, undefined)
  expect(result.label).toBe('searching')
  expect(result.animate).toBe(true)
})

test('PROGRESS shows searching', () => {
  const result = getTaskStatusDisplay({ status: 'PROGRESS' }, undefined)
  expect(result.label).toBe('searching')
  expect(result.animate).toBe(true)
})
```

### Integration Testing

**Manual Test Checklist:**

1. **Basic Flow:**
   - [ ] Click "Search for Latest Videos (RSS Feed)"
   - [ ] Verify status shows "queued" for < 2 seconds
   - [ ] Verify status changes to "searching" with spinning icon
   - [ ] Verify status shows "searching" for entire discovery duration
   - [ ] Verify status changes to "updated: {timestamp}" when complete
   - [ ] Verify new videos appear in Videos tab

2. **yt-dlp Method:**
   - [ ] Click "Search for Recent Videos (Slow API)"
   - [ ] Verify same status progression as RSS method
   - [ ] Verify longer "searching" duration (30-60 seconds)

3. **Concurrent Tasks:**
   - [ ] Trigger search on Channel A
   - [ ] Immediately trigger search on Channel B
   - [ ] Verify both show independent status updates
   - [ ] Verify both complete successfully

4. **Error Handling:**
   - [ ] Trigger search on invalid/deleted channel
   - [ ] Verify status changes to "retry" or error state
   - [ ] Verify error notification appears

5. **Auto-Approve:**
   - [ ] Enable auto-approve on a channel
   - [ ] Trigger search
   - [ ] Verify progress reaches 90% ("Auto-approving X videos")
   - [ ] Verify episodes are created automatically

6. **Page Refresh:**
   - [ ] Trigger search
   - [ ] Refresh page while task is running
   - [ ] Verify status still shows "searching" (polling resumes)
   - [ ] Verify task completes correctly

### Performance Testing

**Database Impact:**
- Measure query count before/after changes
- Expected: +5 UPDATE queries per task (negligible overhead)
- Monitor database load during concurrent tasks

**UI Responsiveness:**
- Polling should not slow down UI
- Status updates should appear within 2 seconds of backend change

---

## Success Criteria

### Backend
- [x] Both task files (`channel_check_rss_tasks.py` and `channel_check_tasks.py`) call `update_progress()` at 5 strategic points
- [x] Progress percentages increment logically: 10% → 20% → 60% → 80% → 90% → 100%
- [x] Step descriptions are user-friendly ("Fetching RSS feed", "Discovering videos", etc.)
- [x] Error handling prevents task failure if progress update fails
- [x] Logs show progress updates for debugging

### Frontend
- [x] PENDING status shows "queued" (yellow, no animation)
- [x] STARTED status shows "searching" (blue, spinning animation)
- [x] PROGRESS status shows "searching" (blue, spinning animation)
- [x] SUCCESS status shows "updated: {timestamp}" (green checkmark)
- [x] Animation is smooth and doesn't flicker

### User Experience
- [x] User sees "queued" for < 2 seconds after clicking button
- [x] User sees "searching" with animation for entire discovery duration (5-60 seconds)
- [x] User sees "updated: {timestamp}" when task completes
- [x] No more sudden jumps from "queued" to "completed"
- [x] Status accurately reflects what task is doing

---

## Additional Considerations

### Database Schema
No migration needed. The `celery_task_status` table already has:
- `progress` (INTEGER) - Percentage 0-100
- `current_step` (VARCHAR) - Step description

### Backward Compatibility
- Old task records without progress still display correctly (show "queued" or "completed")
- New tasks immediately benefit from progress updates
- No breaking changes to API responses

### Future Enhancements (Out of Scope)
- Show progress percentage in UI (e.g., "searching... 60%")
- Show current step description in tooltip
- Add progress bar to channel card
- Real-time WebSocket updates instead of polling

---

## Critical Files Summary

### Files to Modify (3 files)

1. **`backend/app/infrastructure/tasks/channel_check_rss_tasks.py`**
   - Add 5 `update_progress()` calls in `_check_channel_rss()` function
   - Lines affected: ~103, ~127, ~132, ~135, ~138

2. **`backend/app/infrastructure/tasks/channel_check_tasks.py`**
   - Add 5 `update_progress()` calls in `_check_channel()` function
   - Lines affected: ~96, ~120, ~123, ~126, ~129

3. **`frontend/src/components/features/subscriptions/followed-channels-list.tsx`**
   - Separate PENDING and STARTED cases in `getTaskStatusDisplay()` function
   - Lines affected: 144-160

### Reference Files (No changes needed)

- `backend/app/domain/entities/celery_task_status.py` - Contains `update_progress()` method definition
- `backend/app/infrastructure/services/celery_download_service.py` - Example of proper progress update usage
- `docs/documentation/TECHNICAL-ANALYSIS-FEATURE-follow-channels-architecture.md` - Architecture reference

---

## Implementation Checklist

- [ ] **Phase 1: Backend Changes**
  - [ ] Modify `channel_check_rss_tasks.py` (add 5 progress updates)
  - [ ] Modify `channel_check_tasks.py` (add 5 progress updates)
  - [ ] Test both tasks locally
  - [ ] Verify database updates
  - [ ] Deploy backend to development environment
  - [ ] Verify in development

- [ ] **Phase 2: Frontend Changes**
  - [ ] Modify `followed-channels-list.tsx` (separate PENDING/STARTED cases)
  - [ ] Test status display locally
  - [ ] Deploy frontend to development environment
  - [ ] Run full integration test suite

- [ ] **Phase 3: Testing**
  - [ ] Complete manual test checklist
  - [ ] Performance testing
  - [ ] Cross-browser testing
  - [ ] Mobile responsive testing

- [ ] **Phase 4: Production Deployment**
  - [ ] Deploy backend first (wait 10 minutes for stability)
  - [ ] Deploy frontend second
  - [ ] Monitor logs for errors
  - [ ] Verify user reports

---

## Estimated Effort

- **Backend changes:** 30 minutes (repetitive pattern across 2 files)
- **Frontend changes:** 10 minutes (simple case separation)
- **Testing:** 30 minutes (manual integration testing)
- **Documentation:** 15 minutes (update task file, add comments)

**Total:** ~1.5 hours

---

**Plan Status:** ✅ Ready for Implementation
**Reviewed By:** Claude Code AI Agent
**Approved By:** [Pending user approval]
