# Task Status Tracking and Notifications Implementation

## Problem Analysis

The current implementation has these gaps:

1. **Task ID not tracked**: When `trigger_check` queues a Celery task, the task ID is not stored or returned to the frontend
2. **No CeleryTaskStatus creation**: The task doesn't create a `CeleryTaskStatus` record when queued
3. **Frontend polling not triggered**: The frontend doesn't know which task to poll for status updates
4. **Notifications not showing**: The notification bell doesn't display task-related notifications

## Backend Changes

### 1. Update `trigger_check` endpoint to return task ID

**File**: [`backend/app/presentation/api/v1/followed_channels.py`](backend/app/presentation/api/v1/followed_channels.py)

Modify the `trigger_check` endpoint (line 272) to return the task ID:

```python
@router.post(
    "/{followed_channel_id}/check",
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_check(...) -> dict:
    task_id = await followed_channel_service.trigger_check(
        followed_channel_id=followed_channel_id,
        user_id=current_user["user_id"]
    )

    return {
        "status": "queued",
        "message": "Check task queued successfully",
        "followed_channel_id": followed_channel_id,
        "task_id": task_id  # Add this
    }
```

### 2. Update `FollowedChannelService.trigger_check` to create task status and return task ID

**File**: [`backend/app/application/services/followed_channel_service.py`](backend/app/application/services/followed_channel_service.py)

Modify `trigger_check` method (line 312) to:

- Create a `CeleryTaskStatus` record when queuing the task
- Return the task ID instead of boolean
- Inject `CeleryTaskStatusRepository` via constructor

```python
async def trigger_check(self, followed_channel_id: int, user_id: int) -> str:
    # Verify channel exists
    channel = await self.get_followed_channel(followed_channel_id, user_id)

    # Queue task
    task_result = check_followed_channel_for_new_videos.apply_async(
        args=(followed_channel_id,),
        kwargs={}
    )

    # Create task status record
    task_status = CeleryTaskStatus(
        task_id=task_result.id,
        task_name="check_followed_channel_for_new_videos",
        status=TaskStatus.PENDING,
        followed_channel_id=followed_channel_id
    )
    await self.task_status_repository.create(task_status)

    return task_result.id
```

### 3. Update Celery task to update task status at each stage

**File**: [`backend/app/infrastructure/tasks/channel_check_tasks.py`](backend/app/infrastructure/tasks/channel_check_tasks.py)

The task already creates notifications but needs to update `CeleryTaskStatus`:

```python
async def _check_channel():
    session = await get_background_task_session()

    # Initialize repositories
    task_status_repo = CeleryTaskStatusRepository(session)

    # Get task status record
    task_status = await task_status_repo.get_by_task_id(self.request.id)

    try:
        # Mark as started
        task_status.mark_started()
        await task_status_repo.update(task_status)

        # ... existing notification creation ...

        # Discover videos
        new_videos = await discovery_service.discover_new_videos(...)

        # Mark as success
        task_status.mark_success(result_json=json.dumps({
            "new_videos_count": len(new_videos),
            "total_pending_count": total_pending_count
        }))
        await task_status_repo.update(task_status)

    except Exception as e:
        # Mark as failed
        task_status.mark_failure(error_message=str(e))
        await task_status_repo.update(task_status)
        raise
```

## Frontend Changes

### 4. Update API client to handle task ID response

**File**: [`frontend/src/lib/api-client.ts`](frontend/src/lib/api-client.ts)

Update the return type for `triggerCheck`:

```typescript
async triggerCheck(id: number): Promise<{ task_id: string; status: string }> {
  return this.request(`/followed-channels/${id}/check`, {
    method: 'POST'
  })
}
```

### 5. Update `useTriggerCheck` hook to start polling

**File**: [`frontend/src/hooks/use-followed-channels.ts`](frontend/src/hooks/use-followed-channels.ts)

Modify the mutation to trigger task status polling:

```typescript
export function useTriggerCheck() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id: number) => {
      const response = await apiClient.triggerCheck(id)
      return { channelId: id, taskId: response.task_id }
    },
    onSuccess: (data) => {
      // Invalidate to refresh channel list
      queryClient.invalidateQueries({ queryKey: followedChannelKeys.all })

      // Start polling for this specific channel's task status
      queryClient.invalidateQueries({
        queryKey: ["task-status", "channel", data.channelId],
      })

      toast.success("Check task queued successfully")
    },
    onError: (error: Error) => {
      toast.error(`Failed to trigger check: ${error.message}`)
    },
  })
}
```

### 6. Update `useChannelTaskStatus` to poll more aggressively

**File**: [`frontend/src/hooks/use-task-status.ts`](frontend/src/hooks/use-task-status.ts)

Ensure the hook polls frequently for active tasks:

```typescript
export function useChannelTaskStatus(channelId: number | null | undefined) {
  return useQuery({
    queryKey: ["task-status", "channel", channelId],
    queryFn: async () => {
      if (!channelId) return null
      return await apiClient.getChannelTaskStatus(channelId)
    },
    enabled: !!channelId,
    refetchInterval: (data) => {
      // Poll every 2 seconds if task is active
      if (
        data?.status === "PENDING" ||
        data?.status === "STARTED" ||
        data?.status === "PROGRESS"
      ) {
        return 2000
      }
      // Poll every 30 seconds otherwise
      return 30000
    },
    staleTime: 1000, // Consider data stale after 1 second
  })
}
```

### 7. Ensure notifications hook polls frequently

**File**: [`frontend/src/hooks/use-notifications.ts`](frontend/src/hooks/use-notifications.ts)

Update to poll more frequently:

```typescript
export function useUnreadNotificationCount() {
  return useQuery({
    queryKey: ["notifications", "unread-count"],
    queryFn: async () => {
      return await apiClient.getUnreadNotificationCount()
    },
    refetchInterval: 5000, // Poll every 5 seconds
    staleTime: 1000,
  })
}
```

## Implementation Order

1. Backend: Update `trigger_check` endpoint to return task ID
2. Backend: Modify `FollowedChannelService` to create task status and return ID
3. Backend: Update Celery task to update task status at each stage
4. Frontend: Update API client type definitions
5. Frontend: Modify `useTriggerCheck` to handle task ID
6. Frontend: Ensure `useChannelTaskStatus` polls aggressively
7. Frontend: Ensure notifications poll frequently
8. Test the complete flow

## Testing Checklist

- [ ] Click "Check for New Videos" shows task ID in response
- [ ] Channel card immediately shows "queued" status
- [ ] Channel card updates to "searching" when task starts
- [ ] Notification bell shows "search started" notification
- [ ] Channel card updates to "completed" with date when done
- [ ] Notification bell shows "search completed" with count badge
- [ ] Stats badges update with new video counts
- [ ] Error handling works (test by simulating failure)
- [ ] Notification bell filters to last 10 days
- [ ] Mark as read / Clear all works correctly
