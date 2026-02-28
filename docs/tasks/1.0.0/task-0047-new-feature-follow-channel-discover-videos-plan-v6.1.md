# Follow Channel Feature - Workflow and UI Improvements

This plan implements three objectives to improve the "Follow Channel and Discover Videos" feature workflow and user experience.

## Critical Bug Fix

**Fix API Client Bug** - The notification methods in [`frontend/src/lib/api-client.ts`](frontend/src/lib/api-client.ts) use `this.fetch` which doesn't exist. Must change to `this.request`.

## Objective 1: Improve Background Task Workflow and Notifications

### Backend Changes

1. **Add new notification types** in [`backend/app/domain/entities/notification.py`](backend/app/domain/entities/notification.py):

- `CHANNEL_SEARCH_STARTED` - When search task begins
- `CHANNEL_SEARCH_COMPLETED` - When search finishes successfully
- `CHANNEL_SEARCH_ERROR` - When search fails

2. **Update channel check task** in [`backend/app/infrastructure/tasks/channel_check_tasks.py`](backend/app/infrastructure/tasks/channel_check_tasks.py):

- Create "search started" notification at task start
- Update existing "videos discovered" notification with proper linking
- Add error notification on task failure
- Update `last_checked` field and track task status

3. **Add video stats per channel endpoint** in [`backend/app/presentation/api/v1/youtube_videos.py`](backend/app/presentation/api/v1/youtube_videos.py):

- New `GET /youtube-videos/stats/{followed_channel_id}` endpoint
- Returns counts by state for a specific followed channel

### Frontend Changes

4. **Update notification types** in [`frontend/src/types/index.ts`](frontend/src/types/index.ts):

- Add new `NotificationType` enum values

5. **Update notification item** in [`frontend/src/components/features/notifications/notification-item.tsx`](frontend/src/components/features/notifications/notification-item.tsx):

- Add icons for new notification types (search started, completed, error)
- Add navigation URLs with proper filters (channel + state)

## Objective 2: Improve Followed Channel Card Component

### Backend Changes

6. **Add stats endpoint per channel** - Create or enhance endpoint to return video counts by state for a specific followed channel

### Frontend Changes

7. **Create enhanced channel card component** - Refactor [`frontend/src/components/features/subscriptions/followed-channels-list.tsx`](frontend/src/components/features/subscriptions/followed-channels-list.tsx):

- Add link to `/subscriptions/videos?channel={id}`
- Add video stats display with badges:
- All videos count
- Pending Review count (clickable)
- Reviewed count
- Downloading count
- Episode Created count
- Add task status indicator with icons:
- `monitor-pause` (queued) - "queued"
- `monitor-cog` (searching) - "searching"
- `circle-check` (finished) - "updated: dd/MM/YYYY"
- `cloud-alert` (error) - "retry"

8. **Add hooks for channel-specific data**:

- Create `useChannelVideoStats` hook for fetching video counts per channel
- Use existing `useChannelTaskStatus` hook for task status polling

9. **Add API client method** in [`frontend/src/lib/api-client.ts`](frontend/src/lib/api-client.ts):

- `getChannelVideoStats(followedChannelId: number)` method

## Objective 3: Improve Notification Bell and Popup

### Frontend Changes

10. **Enhance notification bell component** in [`frontend/src/components/layout/notification-bell.tsx`](frontend/src/components/layout/notification-bell.tsx):

- Add link to `/subscriptions/channels` page at top of popup
- Filter to show only notifications from last 10 days
- Visual distinction between read/unread notifications
- Individual notification delete button (already exists)
- Clear all (mark all as read) button (already exists)
- Badge with unread count on sidebar icon (already exists)

11. **Update notification item styling** in [`frontend/src/components/features/notifications/notification-item.tsx`](frontend/src/components/features/notifications/notification-item.tsx):

- Add badge with count for video discovery notifications
- Enhanced read/unread visual distinction

## Files to Modify

**Backend:**

- `backend/app/domain/entities/notification.py` - Add notification types
- `backend/app/infrastructure/tasks/channel_check_tasks.py` - Task notifications
- `backend/app/application/services/notification_service.py` - Helper methods
- `backend/app/presentation/api/v1/youtube_videos.py` - Per-channel stats endpoint

**Frontend:**

- `frontend/src/lib/api-client.ts` - Fix bug + add new methods
- `frontend/src/types/index.ts` - New types
- `frontend/src/components/features/subscriptions/followed-channels-list.tsx` - Enhanced card
- `frontend/src/components/layout/notification-bell.tsx` - Enhancements
- `frontend/src/components/features/notifications/notification-item.tsx` - Icons/styling
- `frontend/src/hooks/use-youtube-videos.ts` - Add channel stats hook

## Implementation Order

1. Fix critical API client bug
2. Backend notification types and task updates
3. Backend per-channel video stats endpoint
4. Frontend types and API client updates
5. Frontend channel card improvements
6. Frontend notification bell improvements
7. Testing with Docker production configuration
