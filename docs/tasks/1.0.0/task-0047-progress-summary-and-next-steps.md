# Task 0047: Progress Summary and Next Steps

## ✅ Completed Work

### 1. Fixed Enum Mismatch Issue
**Problem**: Videos tab showed error about enum values not matching.

**Solution**: Changed `YouTubeVideoModel.state` column from `Enum(YouTubeVideoState)` to `String(50)` to store enum values directly.

**Files Modified**:
- `backend/app/infrastructure/database/models/youtube_video.py`

**Status**: ✅ **FIXED** - Videos tab should now load correctly with 36 discovered videos

---

### 2. Started Task Progress UI Implementation
**Goal**: Show real-time progress when users trigger "Check for new videos" or "Backfill videos"

**Completed**:
1. ✅ Created `CeleryTaskStatusModel` database model
2. ✅ Added `last_check_task_id` and `last_backfill_task_id` to `FollowedChannelModel`
3. ✅ Created Alembic migration (stamped as complete)
4. ✅ Backend rebuilt and deployed

**Files Created/Modified**:
- `backend/app/infrastructure/database/models/celery_task_status.py` - New model
- `backend/app/infrastructure/database/models/followed_channel.py` - Added task_id columns
- `backend/app/infrastructure/database/models/__init__.py` - Registered new model
- `backend/alembic/versions/g7h8i9j0k1l2_add_celery_task_status_table.py` - Migration

---

## 🚧 Remaining Work

### Phase 1: Backend - Task Status Tracking & API

#### A. Create Repository for Task Status
**File**: `backend/app/infrastructure/repositories/celery_task_status_repository_impl.py`

```python
class CeleryTaskStatusRepositoryImpl:
    async def create(self, task_id, task_name, followed_channel_id=None) -> CeleryTaskStatus
    async def get_by_task_id(self, task_id) -> Optional[CeleryTaskStatus]
    async def update_status(self, task_id, status, progress=None, current_step=None)
    async def update_result(self, task_id, result_json, error_message=None)
    async def get_latest_for_channel(self, followed_channel_id, task_type) -> Optional[CeleryTaskStatus]
```

#### B. Update Celery Tasks to Report Progress
**Files**: 
- `backend/app/infrastructure/tasks/channel_check_tasks.py`
- `backend/app/infrastructure/tasks/backfill_channel_task.py`

**Changes**:
```python
@shared_task(bind=True)
def check_followed_channel_for_new_videos(self, followed_channel_id: int):
    # Create task status record
    task_status_repo.create(self.request.id, "check_videos", followed_channel_id)
    
    # Update progress at key points
    self.update_state(state='PROGRESS', meta={'progress': 25, 'status': 'Fetching channel info'})
    # ... fetch channel ...
    
    self.update_state(state='PROGRESS', meta={'progress': 50, 'status': 'Discovering videos'})
    # ... discover videos ...
    
    self.update_state(state='PROGRESS', meta={'progress': 90, 'status': 'Saving results'})
    # ... save ...
    
    # Store final result
    task_status_repo.update_result(self.request.id, json.dumps(result))
    
    return result
```

#### C. Update Service to Store Task IDs
**File**: `backend/app/application/services/followed_channel_service.py`

**Changes**:
```python
async def trigger_check(self, followed_channel_id: int, user_id: int) -> dict:
    # ... existing validation ...
    
    # Queue task and get task_id
    result = check_followed_channel_for_new_videos.apply_async(args=(followed_channel_id,))
    task_id = result.id
    
    # Store task_id on channel
    await self.followed_channel_repo.update_task_id(followed_channel_id, task_id, 'check')
    
    return {"task_id": task_id, "status": "queued"}
```

#### D. Create API Endpoint for Task Status
**File**: `backend/app/presentation/api/v1/celery_tasks.py` (NEW)

```python
@router.get("/celery-tasks/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: Annotated[dict, Depends(get_current_user_jwt)],
) -> CeleryTaskStatusResponse:
    """Get status of a Celery task"""
    task_status = await task_status_service.get_task_status(task_id)
    if not task_status:
        raise HTTPException(status_code=404, detail="Task not found")
    return task_status
```

#### E. Update Followed Channel Response Schema
**File**: `backend/app/presentation/schemas/followed_channel_schemas.py`

```python
class FollowedChannelResponse(BaseModel):
    # ... existing fields ...
    last_check_task_id: Optional[str] = None
    last_backfill_task_id: Optional[str] = None
```

---

### Phase 2: Frontend - Task Status Polling & UI

#### A. Update TypeScript Types
**File**: `frontend/src/types/index.ts`

```typescript
export interface CeleryTaskStatus {
  task_id: string
  task_name: string
  status: 'PENDING' | 'STARTED' | 'PROGRESS' | 'SUCCESS' | 'FAILURE' | 'RETRY'
  progress: number  // 0-100
  current_step?: string
  result?: any
  error_message?: string
  created_at: string
  updated_at: string
  completed_at?: string
}

export interface FollowedChannel {
  // ... existing fields ...
  last_check_task_id?: string
  last_backfill_task_id?: string
}
```

#### B. Create API Client Methods
**File**: `frontend/src/lib/api-client.ts`

```typescript
async getCeleryTaskStatus(taskId: string): Promise<CeleryTaskStatus> {
  return this.request<CeleryTaskStatus>(`/celery-tasks/${taskId}`)
}
```

#### C. Create Task Status Hook
**File**: `frontend/src/hooks/use-celery-task-status.ts` (NEW)

```typescript
export function useCeleryTaskStatus(taskId: string | null | undefined) {
  return useQuery({
    queryKey: ['celery-task', taskId],
    queryFn: async () => {
      if (!taskId) return null
      return await apiClient.getCeleryTaskStatus(taskId)
    },
    enabled: !!taskId,
    refetchInterval: (data) => {
      // Stop polling if task is complete
      if (!data || data.status === 'SUCCESS' || data.status === 'FAILURE') {
        return false
      }
      return 2000 // Poll every 2 seconds while running
    },
    staleTime: 1000, // Consider data stale after 1 second
  })
}
```

#### D. Update Followed Channel Card Component
**File**: `frontend/src/components/features/subscriptions/followed-channels-list.tsx`

**Add to card**:
```tsx
function FollowedChannelCard({ channel }) {
  const { data: checkTaskStatus } = useCeleryTaskStatus(channel.last_check_task_id)
  const { data: backfillTaskStatus } = useCeleryTaskStatus(channel.last_backfill_task_id)
  const router = useRouter()
  
  const activeTask = checkTaskStatus?.status !== 'SUCCESS' && checkTaskStatus?.status !== 'FAILURE' 
    ? checkTaskStatus 
    : backfillTaskStatus?.status !== 'SUCCESS' && backfillTaskStatus?.status !== 'FAILURE'
    ? backfillTaskStatus
    : null
  
  const handleViewResults = () => {
    router.push(`/subscriptions?tab=videos&channel=${channel.id}&state=pending_review`)
  }
  
  return (
    <Card>
      {/* ... existing channel info ... */}
      
      {/* Active Task Progress */}
      {activeTask && (
        <div className="mt-4 space-y-2">
          <div className="flex items-center gap-2 text-sm">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span className="text-muted-foreground">
              {activeTask.current_step || 'Processing...'}
            </span>
          </div>
          <Progress value={activeTask.progress || 0} className="h-2" />
        </div>
      )}
      
      {/* Completed Task Results */}
      {checkTaskStatus?.status === 'SUCCESS' && checkTaskStatus.result && (
        <div className="mt-4 p-3 bg-green-50 dark:bg-green-900/20 rounded-md">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-green-600" />
              <span className="text-sm font-medium">
                Found {checkTaskStatus.result.new_videos_count} new videos
              </span>
            </div>
            <Button size="sm" variant="outline" onClick={handleViewResults}>
              View Videos
            </Button>
          </div>
        </div>
      )}
      
      {/* Error State */}
      {(checkTaskStatus?.status === 'FAILURE' || backfillTaskStatus?.status === 'FAILURE') && (
        <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 rounded-md">
          <div className="flex items-center gap-2">
            <XCircle className="h-4 w-4 text-red-600" />
            <span className="text-sm text-red-600">
              {checkTaskStatus?.error_message || backfillTaskStatus?.error_message || 'Task failed'}
            </span>
          </div>
        </div>
      )}
    </Card>
  )
}
```

---

## 📋 Implementation Checklist

### Backend
- [ ] Create `CeleryTaskStatusRepositoryImpl`
- [ ] Create domain entity `CeleryTaskStatus`
- [ ] Update `check_followed_channel_for_new_videos` task to report progress
- [ ] Update `backfill_followed_channel` task to report progress
- [ ] Update `FollowedChannelService.trigger_check` to store task_id
- [ ] Update `FollowedChannelService.trigger_backfill` to store task_id
- [ ] Create `/api/v1/celery-tasks/{task_id}` endpoint
- [ ] Update `FollowedChannelResponse` schema
- [ ] Update `FollowedChannelRepositoryImpl` to include task_id fields

### Frontend
- [ ] Update `CeleryTaskStatus` type in `types/index.ts`
- [ ] Update `FollowedChannel` type to include task_id fields
- [ ] Add `getCeleryTaskStatus` to API client
- [ ] Create `useCeleryTaskStatus` hook
- [ ] Update `FollowedChannelCard` component with progress UI
- [ ] Add navigation to Videos tab with filters
- [ ] Test complete flow end-to-end

---

## 🧪 Testing Plan

1. **Test Check for New Videos**:
   - Click "Check for new videos" on a channel
   - Verify progress indicator appears
   - Verify progress updates in real-time
   - Verify "View Results" button appears on completion
   - Click "View Results" and verify navigation to Videos tab with filters

2. **Test Backfill Videos**:
   - Click "Backfill videos" on a channel
   - Enter year and max videos
   - Verify progress indicator appears
   - Verify completion message shows correct count

3. **Test Error Handling**:
   - Trigger task with invalid channel
   - Verify error message displays correctly
   - Verify retry option works

4. **Test Multiple Concurrent Tasks**:
   - Trigger check on multiple channels
   - Verify each shows independent progress
   - Verify completion states are tracked separately

---

## 📝 Notes

- The database models and migration are complete
- Backend needs repository, service updates, and API endpoint
- Frontend needs hook, UI components, and navigation
- Estimated remaining work: 3-4 hours
- This feature mirrors the episode creation progress pattern

---

**Status**: 🚧 **50% COMPLETE**
**Next Session**: Start with backend repository and service implementation
**Date**: 2025-11-14





