# Implementation Plan: Fix Celery Task Status Display for Followed YouTube Channels

**Date:** 2025-11-30
**Task:** Fix the "queued" status persisting throughout task execution instead of showing "searching"

---

## Executive Summary

This plan addresses a UX issue where the Followed YouTube Channel cards show "queued" status for the entire task duration (30-60 seconds), then suddenly jump to "completed". The expected behavior is:

1. **"queued" (0-1 sec)** - Task waiting in Celery queue
2. **"searching" (1-50 sec)** - Task actively processing (discovering videos, extracting metadata)  
3. **"updated: {timestamp}"** - Task completed successfully

### Root Causes Identified

1. **Backend:** Celery tasks only call `mark_started()` and `mark_success()`, never `update_progress()`. This causes status to skip the PROGRESS state entirely.
2. **Frontend:** Both PENDING and STARTED states map to "queued" instead of differentiating between queued vs actively processing.

---

## Task Status State Machine

**Current (Broken):**
```
PENDING → STARTED → SUCCESS
 (queued)  (queued)  (completed)
```

**Expected (Fixed):**
```
PENDING → STARTED → PROGRESS → SUCCESS
 (queued) (searching) (searching) (completed)
```

**Celery Task States:**
- `PENDING` - Task created, waiting in queue
- `STARTED` - Worker picked up task, beginning execution
- `PROGRESS` - Task actively processing (with progress updates)
- `SUCCESS` - Task completed successfully
- `FAILURE` - Task failed
- `RETRY` - Task will retry after failure

---

## Implementation Strategy

### Phase 1: Backend - Add Progress Updates to Celery Tasks

**Objective:** Add `update_progress()` calls at key execution milestones in both RSS and yt-dlp discovery tasks.

#### File 1: `/Users/oliver/local/dev/labcastarr/backend/app/infrastructure/tasks/channel_check_rss_tasks.py`

**Current Issue:** Task only calls:
- Line 100-102: `mark_started()` → Status becomes STARTED
- Line 180-188: `mark_success()` → Status becomes SUCCESS
- **Never calls `update_progress()`** → Status never reaches PROGRESS

**Solution:** Add progress updates at 5 key points during execution:

```python
# After line 102 (after mark_started):
if task_status:
    task_status.update_progress(10, "Initializing RSS feed discovery")
    await task_status_repo.update(task_status)
    logger.info(f"Task {self.request.id} progress: 10% - Initializing")

# After line 118 (after rss_service initialization):
if task_status:
    task_status.update_progress(20, "Fetching RSS feed from YouTube")
    await task_status_repo.update(task_status)
    logger.info(f"Task {self.request.id} progress: 20% - Fetching RSS")

# After line 132 (after discovering videos):
if task_status:
    task_status.update_progress(60, f"Discovered {len(new_videos)} new videos, extracting metadata")
    await task_status_repo.update(task_status)
    logger.info(f"Task {self.request.id} progress: 60% - Metadata extraction")

# After line 135 (after updating last_checked):
if task_status:
    task_status.update_progress(80, "Saving video data and creating notifications")
    await task_status_repo.update(task_status)
    logger.info(f"Task {self.request.id} progress: 80% - Saving data")

# Before auto-approve processing (if auto_approve enabled):
if task_status and followed_channel.auto_approve:
    task_status.update_progress(90, "Queueing episodes for auto-approval")
    await task_status_repo.update(task_status)
    logger.info(f"Task {self.request.id} progress: 90% - Auto-approve processing")
```

**Rationale:**
- **10%** - Initialization shows task is actively running (not just queued)
- **20%** - RSS fetch is the first network operation (may take 2-5 seconds)
- **60%** - Metadata extraction is the most time-consuming step (yt-dlp calls for each new video)
- **80%** - Database operations and notification creation
- **90%** - Auto-approve workflow (only if enabled)
- **100%** - Set automatically by `mark_success()`

#### File 2: `/Users/oliver/local/dev/labcastarr/backend/app/infrastructure/tasks/channel_check_tasks.py`

**Current Issue:** Same as RSS task - only calls `mark_started()` and `mark_success()`.

**Solution:** Add progress updates at 5 key points (similar to RSS task):

```python
# After line 96 (after mark_started):
if task_status:
    task_status.update_progress(10, "Initializing yt-dlp video discovery")
    await task_status_repo.update(task_status)
    logger.info(f"Task {self.request.id} progress: 10% - Initializing")

# After line 117 (after discovery_strategy initialization):
if task_status:
    task_status.update_progress(20, "Fetching channel videos via yt-dlp")
    await task_status_repo.update(task_status)
    logger.info(f"Task {self.request.id} progress: 20% - Fetching videos")

# After line 123 (after discovering videos):
if task_status:
    task_status.update_progress(60, f"Discovered {len(new_videos)} new videos, extracting metadata")
    await task_status_repo.update(task_status)
    logger.info(f"Task {self.request.id} progress: 60% - Metadata extraction")

# After line 126 (after updating last_checked):
if task_status:
    task_status.update_progress(80, "Saving video data and creating notifications")
    await task_status_repo.update(task_status)
    logger.info(f"Task {self.request.id} progress: 80% - Saving data")

# Before auto-approve processing (if auto_approve enabled):
if task_status and followed_channel.auto_approve:
    task_status.update_progress(90, "Queueing episodes for auto-approval")
    await task_status_repo.update(task_status)
    logger.info(f"Task {self.request.id} progress: 90% - Auto-approve processing")
```

**Rationale:**
- **10%** - Shows task transition from queued to active
- **20%** - yt-dlp channel listing (slower than RSS, 10-20 seconds for 50 videos)
- **60%** - Metadata extraction for new videos (yt-dlp calls)
- **80%** - Database and notification operations
- **90%** - Auto-approve workflow processing

**Important Notes:**
1. Each `update_progress()` call sets `status = TaskStatus.PROGRESS` automatically (see entity line 61)
2. Progress updates include human-readable `current_step` messages for debugging
3. All updates are logged for troubleshooting
4. Updates are committed to database immediately so frontend polling sees them

---

### Phase 2: Frontend - Fix Status Mapping

**Objective:** Map STARTED state to "searching" instead of "queued" to reflect active processing.

#### File 3: `/Users/oliver/local/dev/labcastarr/frontend/src/components/features/subscriptions/followed-channels-list.tsx`

**Current Issue (Lines 144-152):**
```typescript
case "PENDING":
case "STARTED":
  return {
    icon: MonitorPause,
    label: "queued",  // ❌ WRONG - shows "queued" even when actively processing
    colorClass: "text-yellow-500",
    bgClass: "bg-yellow-100 dark:bg-yellow-900/30",
  }
```

**Solution:** Separate PENDING and STARTED cases:

```typescript
// Lines 144-152 - Replace entire switch case
case "PENDING":
  return {
    icon: MonitorPause,
    label: "queued",
    colorClass: "text-yellow-500",
    bgClass: "bg-yellow-100 dark:bg-yellow-900/30",
  }
case "STARTED":
  return {
    icon: MonitorCog,
    label: "searching",
    colorClass: "text-blue-500",
    bgClass: "bg-blue-100 dark:bg-blue-900/30",
    animate: true,  // Spinning animation
  }
case "PROGRESS":
  return {
    icon: MonitorCog,
    label: "searching",
    colorClass: "text-blue-500",
    bgClass: "bg-blue-100 dark:bg-blue-900/30",
    animate: true,
  }
```

**Rationale:**
- **PENDING** → "queued" (yellow, paused icon) - Task in queue, not yet picked up by worker
- **STARTED** → "searching" (blue, spinning cog) - Worker started task, initializing
- **PROGRESS** → "searching" (blue, spinning cog) - Task actively processing with progress updates
- Both STARTED and PROGRESS use spinning animation to show activity
- Color change (yellow → blue) provides visual feedback of state transition

**Visual States:**
```
PENDING:  [⏸️ queued] (yellow, static)
STARTED:  [⚙️ searching] (blue, spinning)  ← NEW!
PROGRESS: [⚙️ searching] (blue, spinning)
SUCCESS:  [✓ updated: DD/MM/YYYY HH:MM] (green, static)
```

---

## Error Handling & Edge Cases

### Backend Error Handling

**Scenario:** Progress update fails (database error, network issue)
**Solution:** Wrap each progress update in try-except:

```python
# Recommended pattern for all progress updates
try:
    if task_status:
        task_status.update_progress(20, "Fetching RSS feed")
        await task_status_repo.update(task_status)
        logger.info(f"Task {self.request.id} progress: 20% - Fetching RSS")
except Exception as progress_error:
    # Log but don't fail the task
    logger.warning(f"Failed to update task progress: {progress_error}")
    # Continue task execution - progress updates are non-critical
```

**Rationale:**
- Progress updates are UI-only features, not critical to task success
- Failing the entire task due to a progress update error would be worse UX
- Logging allows debugging if progress updates systematically fail

### Frontend Backward Compatibility

**Scenario:** Old task status records without progress field
**Solution:** Already handled - `task_status?.status` checks ensure graceful degradation

**Scenario:** Task status not yet created when frontend polls
**Solution:** Already handled - `getTaskStatusDisplay()` returns null if no status (lines 199-200)

### Database Lock Handling

**Scenario:** High-frequency progress updates cause database lock contention
**Solution:** 
1. Progress updates are spaced ~20% apart (5 updates total)
2. SQLite WAL mode already configured (handles concurrent reads/writes)
3. Each update is a separate transaction (quick commit)

**Risk:** LOW - Progress updates are infrequent enough to avoid contention

---

## Testing Strategy

### Unit Testing

**Backend Tests:**
```python
# Test: task_status entity update_progress method
def test_update_progress_sets_progress_state():
    task_status = CeleryTaskStatus(task_id="test", task_name="test")
    task_status.update_progress(50, "Testing")
    assert task_status.status == TaskStatus.PROGRESS
    assert task_status.progress == 50
    assert task_status.current_step == "Testing"

# Test: progress updates in channel_check_rss_tasks
async def test_rss_task_progress_updates(mock_session):
    # Mock task status repository
    # Call task with followed_channel_id
    # Verify update_progress called at expected points
    # Verify progress values: 10, 20, 60, 80, 90
```

**Frontend Tests:**
```typescript
// Test: status mapping function
describe('getTaskStatusDisplay', () => {
  it('maps PENDING to queued', () => {
    const result = getTaskStatusDisplay({status: 'PENDING'}, null);
    expect(result.label).toBe('queued');
    expect(result.animate).toBeUndefined();
  });
  
  it('maps STARTED to searching with animation', () => {
    const result = getTaskStatusDisplay({status: 'STARTED'}, null);
    expect(result.label).toBe('searching');
    expect(result.animate).toBe(true);
  });
  
  it('maps PROGRESS to searching with animation', () => {
    const result = getTaskStatusDisplay({status: 'PROGRESS'}, null);
    expect(result.label).toBe('searching');
    expect(result.animate).toBe(true);
  });
});
```

### Integration Testing

**Test Scenario 1: RSS Feed Discovery (Fast)**
1. Click "Search for Latest Videos (RSS Feed)" on a channel card
2. Verify status changes: queued (0-1s) → searching (5-10s) → updated
3. Verify spinning animation during "searching"
4. Verify final timestamp shows completion time

**Test Scenario 2: yt-dlp Discovery (Slow)**
1. Click "Search for Recent Videos (Slow API)" on a channel card
2. Verify status changes: queued (0-1s) → searching (30-60s) → updated
3. Verify spinning animation persists throughout discovery
4. Verify final timestamp shows completion time

**Test Scenario 3: Error Handling**
1. Trigger task with invalid channel (should fail)
2. Verify status shows error state (not stuck on "searching")
3. Verify retry status if configured

**Test Scenario 4: Concurrent Tasks**
1. Trigger discovery on multiple channels simultaneously
2. Verify each card shows correct independent status
3. Verify no status cross-contamination between channels

### Manual Testing Checklist

- [ ] RSS task shows "searching" status during execution
- [ ] yt-dlp task shows "searching" status during execution
- [ ] Spinning animation appears during active processing
- [ ] Status transitions are smooth (no flickering)
- [ ] Final "updated" timestamp is accurate
- [ ] Browser refresh preserves final status
- [ ] Multiple concurrent tasks work independently
- [ ] Error states display correctly
- [ ] Task progress persists across page navigation
- [ ] Polling stops when task completes (no infinite requests)

---

## Performance Considerations

### Database Impact

**Progress Updates Per Task:** 5 updates (10%, 20%, 60%, 80%, 90%)
**Database Operations:** 
- 5 × UPDATE on `celery_task_status` table
- Each update modifies: `status`, `progress`, `current_step`, `updated_at`

**Impact:** NEGLIGIBLE
- SQLite handles 5 small updates easily
- Updates are ~20% spaced (not high-frequency)
- WAL mode prevents read blocking

### Frontend Polling Impact

**Current Polling Strategy:** Every 2 seconds while task is active
**Impact of Changes:** NONE
- Frontend polling rate unchanged
- More status updates visible (better UX)
- Polling still stops when `status === 'SUCCESS'`

### Network Impact

**Additional Network Requests:** NONE
- Frontend already polls task status endpoint
- More status changes visible, but same request frequency

---

## Rollback Plan

### If Backend Changes Cause Issues

**Symptoms:** Tasks failing, database errors, performance degradation

**Rollback Steps:**
1. Comment out all `update_progress()` calls in both task files
2. Keep `mark_started()` and `mark_success()` calls
3. Restart Celery workers
4. System reverts to old behavior (always shows "queued")

**Rollback Code Pattern:**
```python
# Wrap all new progress updates like this for easy rollback:
# PROGRESS_UPDATE_V1_START
if task_status:
    task_status.update_progress(20, "Fetching RSS feed")
    await task_status_repo.update(task_status)
# PROGRESS_UPDATE_V1_END
```

### If Frontend Changes Cause Issues

**Symptoms:** Status not displayed, errors in console, broken UI

**Rollback Steps:**
1. Revert `getTaskStatusDisplay()` function to combine PENDING/STARTED cases
2. Redeploy frontend
3. Old behavior restored (shows "queued" for both states)

**Rollback Commit:**
```bash
git revert <commit-hash-of-frontend-changes>
npm run build
npm run start
```

---

## Migration & Deployment

### Database Migration

**Required:** NO
- No schema changes
- `progress` and `current_step` fields already exist in `celery_task_status` table
- Existing rows will have `progress=0, current_step=NULL` (valid default)

### Deployment Order

**Critical:** Backend MUST be deployed before frontend

**Recommended Deployment Steps:**

1. **Deploy Backend First:**
   ```bash
   # Stop Celery workers
   docker compose -f docker-compose.prod.yml stop celery-worker celery-beat
   
   # Deploy backend code changes
   docker compose -f docker-compose.prod.yml up --build -d backend
   
   # Restart Celery workers (picks up new task code)
   docker compose -f docker-compose.prod.yml up --build -d celery-worker celery-beat
   ```

2. **Verify Backend:**
   - Trigger a test task via API
   - Check logs for progress updates: `docker compose logs celery-worker -f`
   - Verify database updates: Query `celery_task_status` table for PROGRESS status

3. **Deploy Frontend:**
   ```bash
   docker compose -f docker-compose.prod.yml up --build -d frontend
   ```

4. **Verify End-to-End:**
   - Open `/subscriptions/channels` page
   - Trigger discovery task
   - Verify status changes: queued → searching → updated

**Why This Order:**
- Frontend can safely poll backend with old or new status values
- Backend changes are backward-compatible (old frontend sees STARTED as "queued", still works)
- Deploying frontend first would show "searching" before backend sends PROGRESS state (confusing UX)

### Development Environment

```bash
# Development deployment (with hot reload)
docker compose -f docker-compose.dev.yml down
docker compose --env-file .env.development -f docker-compose.dev.yml up --build

# Note: Celery workers don't hot-reload, so restart after backend changes:
docker compose -f docker-compose.dev.yml restart celery-worker-dev celery-beat-dev
```

---

## Code Review Checklist

### Backend Review

- [ ] Progress updates added at 5 key points in RSS task
- [ ] Progress updates added at 5 key points in yt-dlp task
- [ ] Progress percentages are consistent (10, 20, 60, 80, 90)
- [ ] `current_step` messages are descriptive and helpful
- [ ] All progress updates are logged
- [ ] Error handling doesn't fail task on progress update error
- [ ] Task still completes successfully if progress updates fail
- [ ] No duplicate progress updates at same percentage
- [ ] Auto-approve branch includes progress update

### Frontend Review

- [ ] PENDING and STARTED cases are separate
- [ ] STARTED maps to "searching" with spinning animation
- [ ] PROGRESS maps to "searching" with spinning animation
- [ ] Color scheme is consistent (yellow=queued, blue=searching, green=success)
- [ ] Icons are appropriate (MonitorPause, MonitorCog, CircleCheck)
- [ ] No breaking changes to existing status display logic
- [ ] SUCCESS state still shows timestamp correctly
- [ ] Backward compatible with old task records

### General Review

- [ ] No new dependencies added
- [ ] Code follows existing patterns (see CeleryDownloadService example)
- [ ] Logging is consistent with existing style
- [ ] No performance regressions
- [ ] Changes are reversible (rollback plan works)
- [ ] Documentation updated (if needed)

---

## Alternative Approaches Considered

### Alternative 1: Use Celery's Native Progress Tracking

**Description:** Celery has built-in `self.update_state()` for progress tracking

**Pros:**
- Standard Celery pattern
- No custom database updates needed

**Cons:**
- Requires Celery result backend (Redis/RabbitMQ)
- Current architecture uses custom `celery_task_status` table
- Would require significant refactoring
- Redis dependency adds complexity

**Decision:** REJECTED - Too much refactoring, breaks existing architecture

### Alternative 2: WebSocket Real-Time Updates

**Description:** Push status updates via WebSocket instead of polling

**Pros:**
- True real-time updates
- No polling overhead

**Cons:**
- Requires WebSocket infrastructure (not currently implemented)
- Added complexity (connection management, fallback)
- Polling works fine for 2-second intervals

**Decision:** REJECTED - Overkill for this use case, polling is sufficient

### Alternative 3: More Granular Progress Updates

**Description:** Update progress every 10% instead of every 20%

**Pros:**
- Smoother progress bar (if we add one)
- More frequent feedback

**Cons:**
- More database writes (10 updates vs 5)
- Diminishing UX returns
- Could hit database lock contention

**Decision:** REJECTED - 5 updates is optimal balance

---

## Success Criteria

### Functional Requirements

✅ **"queued" status appears for <2 seconds** (only while task is in Celery queue)
✅ **"searching" status appears for bulk of execution** (10-60 seconds depending on method)
✅ **Spinning animation shows during active processing**
✅ **Final "updated" timestamp displays after completion**
✅ **Status transitions are smooth without flickering**
✅ **Both RSS and yt-dlp methods show correct status progression**

### Performance Requirements

✅ **No increase in frontend polling frequency**
✅ **No significant database performance impact** (<5ms per progress update)
✅ **Task execution time unchanged** (progress updates add <50ms total overhead)
✅ **No memory leaks from status polling**

### Quality Requirements

✅ **All existing tests pass**
✅ **Code follows existing architecture patterns**
✅ **Changes are backward-compatible**
✅ **Rollback plan is tested and works**
✅ **Error states handled gracefully**

---

## Timeline Estimate

**Total Implementation Time: 3-4 hours**

- **Backend Implementation:** 1.5 hours
  - Add progress updates to RSS task: 45 min
  - Add progress updates to yt-dlp task: 45 min
  
- **Frontend Implementation:** 30 minutes
  - Update status mapping: 15 min
  - Visual verification: 15 min

- **Testing:** 1-2 hours
  - Unit tests: 30 min
  - Integration testing: 30-60 min
  - Manual testing all scenarios: 30 min

- **Deployment & Verification:** 30 minutes
  - Deploy backend: 10 min
  - Deploy frontend: 10 min
  - End-to-end verification: 10 min

---

## Post-Implementation Tasks

### Monitoring

1. **Check Celery worker logs** for progress update messages
2. **Monitor database** for PROGRESS state records
3. **Track frontend polling** for status changes
4. **Watch for error logs** related to progress updates

### Documentation

1. Update feature documentation with new status flow
2. Add troubleshooting section for status display issues
3. Document progress update pattern for future Celery tasks

### Potential Enhancements

1. **Add progress bar** to channel cards (visual representation of 0-100%)
2. **Show `current_step` message** in tooltip (e.g., "Fetching RSS feed...")
3. **Add task duration display** (e.g., "searching (15s)")
4. **Notification on completion** (optional, may be annoying)

