# Task 0047: Enum Fix and Task Progress UI

## Issue 1: ✅ FIXED - Enum Value Mismatch

### Problem
The Videos tab was showing an error:
```
Error loading videos: Failed to list videos: 'pending_review' is not among the defined enum values. 
Enum name: youtubevideostate. Possible values: PENDING_REV.., REVIEWED, QUEUED, ..., DISCARDED
```

### Root Cause
SQLAlchemy's `Enum` column type was storing enum VALUES (`"pending_review"`) in the database, but the error message suggested it was trying to match against enum NAMES (`"PENDING_REVIEW"`).

The issue was in the model definition:
```python
# OLD - Using Enum column type
state = Column(Enum(YouTubeVideoState), nullable=False, default=YouTubeVideoState.PENDING_REVIEW, index=True)
```

### Solution
Changed the column type from `Enum` to `String` to store the enum values directly:

```python
# NEW - Using String column type
state = Column(String(50), nullable=False, default="pending_review", index=True)
```

The repository already had proper string-to-enum conversion:
```python
state = YouTubeVideoState(model.state) if isinstance(model.state, str) else model.state
```

### Files Modified
- `backend/app/infrastructure/database/models/youtube_video.py` - Changed state column from Enum to String

### Verification
Database already had correct lowercase values:
```sql
SELECT DISTINCT state FROM youtube_videos;
-- Result: pending_review
```

**Status**: ✅ **FIXED** - Videos tab should now load correctly

---

## Issue 2: 🚧 IN PROGRESS - Task Progress Indicators

### Requirements

When users trigger background operations (Check for new videos, Backfill videos), they need visual feedback:

1. **Progress Indicator**: Show that a Celery task is running
2. **Task Status**: Display current status (queued, running, completed, failed)
3. **Results Navigation**: Click to navigate to Videos tab with filtered results
4. **Similar to Episode Creation**: Follow the same pattern used when creating episodes from videos

### Current Behavior
- User clicks "Check for new videos" or "Backfill videos"
- Success toast appears immediately
- No indication that task is running in background
- No way to see when task completes
- No way to navigate to results

### Desired Behavior
- User clicks action → Card shows "Task queued" indicator
- Card updates to "Discovering videos..." with progress
- On completion: "Found 5 new videos" with link to view
- Click link → Navigate to Videos tab filtered by that channel
- On error: Show error message with retry option

### Implementation Plan

#### Step 1: Backend - Task Status Tracking
- [ ] Create `CeleryTaskStatus` model to track task execution
- [ ] Store task_id, status, progress, result in database
- [ ] Update tasks to report progress
- [ ] Create API endpoint to query task status: `GET /api/v1/celery-tasks/{task_id}`

#### Step 2: Backend - Link Tasks to Channels
- [ ] Add `last_check_task_id` to `FollowedChannelModel`
- [ ] Add `last_backfill_task_id` to `FollowedChannelModel`
- [ ] Update task creation to store task_id on channel
- [ ] Return task_id in API response

#### Step 3: Frontend - Task Status Hook
- [ ] Create `useCeleryTaskStatus(taskId)` hook
- [ ] Poll task status every 2-3 seconds while running
- [ ] Stop polling when task completes/fails
- [ ] Cache results to avoid redundant requests

#### Step 4: Frontend - Channel Card UI
- [ ] Add task status indicator to channel card
- [ ] Show spinner + status message while running
- [ ] Show success message + result count on completion
- [ ] Show error message + retry button on failure
- [ ] Add "View Results" button that navigates to Videos tab

#### Step 5: Frontend - Navigation
- [ ] Create navigation function to Videos tab with filters
- [ ] Filter by channel_id and state=pending_review
- [ ] Highlight newly discovered videos

### Technical Approach

#### Database Schema
```python
class CeleryTaskStatusModel(Base):
    __tablename__ = "celery_task_status"
    
    id = Column(Integer, primary_key=True)
    task_id = Column(String(255), unique=True, nullable=False, index=True)
    task_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)  # PENDING, STARTED, SUCCESS, FAILURE, RETRY
    progress = Column(Integer, default=0)  # 0-100
    result_json = Column(Text)  # JSON result
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
```

#### Task Progress Reporting
```python
@shared_task(bind=True)
def check_followed_channel_for_new_videos(self, followed_channel_id: int):
    # Update task status
    self.update_state(state='PROGRESS', meta={'progress': 10, 'status': 'Fetching channel info'})
    
    # ... fetch channel ...
    
    self.update_state(state='PROGRESS', meta={'progress': 50, 'status': 'Discovering videos'})
    
    # ... discover videos ...
    
    self.update_state(state='PROGRESS', meta={'progress': 90, 'status': 'Saving results'})
    
    return {'status': 'success', 'new_videos_count': len(new_videos)}
```

#### Frontend Hook
```typescript
export function useCeleryTaskStatus(taskId: string | null) {
  return useQuery({
    queryKey: ['celery-task', taskId],
    queryFn: async () => {
      if (!taskId) return null
      return await apiClient.getCeleryTaskStatus(taskId)
    },
    enabled: !!taskId,
    refetchInterval: (data) => {
      // Stop polling if task is complete
      if (data?.status === 'SUCCESS' || data?.status === 'FAILURE') {
        return false
      }
      return 2000 // Poll every 2 seconds
    },
  })
}
```

#### Channel Card Component
```tsx
function FollowedChannelCard({ channel }) {
  const { data: taskStatus } = useCeleryTaskStatus(channel.last_check_task_id)
  
  return (
    <Card>
      {/* ... channel info ... */}
      
      {taskStatus && taskStatus.status !== 'SUCCESS' && (
        <div className="flex items-center gap-2">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span>{taskStatus.meta?.status || 'Processing...'}</span>
          <Progress value={taskStatus.meta?.progress || 0} />
        </div>
      )}
      
      {taskStatus?.status === 'SUCCESS' && (
        <Button onClick={() => navigateToVideos(channel.id)}>
          View {taskStatus.result?.new_videos_count} New Videos
        </Button>
      )}
    </Card>
  )
}
```

### Next Steps

1. Create database migration for `celery_task_status` table
2. Implement task status tracking in Celery tasks
3. Create API endpoint for task status queries
4. Implement frontend hook and UI components
5. Test complete flow end-to-end

**Status**: 🚧 **IN PROGRESS**

---

**Date**: 2025-11-14
**Version**: v2.1





