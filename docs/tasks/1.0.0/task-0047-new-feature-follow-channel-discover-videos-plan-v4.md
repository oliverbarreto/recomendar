# Phase 3: Notification System Implementation Plan

## Overview

This plan implements the notification system for the Follow Channels feature, enabling users to receive real-time notifications when new videos are discovered from followed channels and when episodes are successfully created.

## Phase 3.1: Backend Notification Infrastructure

### Step 1: Database Schema and Migration

**Create Alembic migration for notifications table:**

File: `backend/alembic/versions/xxx_add_notifications_table.py`

- Create `notifications` table with columns:
  - `id` (Integer, primary key)
  - `user_id` (Integer, ForeignKey to users.id, indexed, NOT NULL)
  - `type` (String, enum: 'video_discovered', 'episode_created', indexed, NOT NULL)
  - `title` (String, 255 chars, NOT NULL)
  - `message` (Text, NOT NULL)
  - `data_json` (JSON, stores additional context like video IDs, channel IDs, etc.)
  - `read` (Boolean, default False, indexed)
  - `created_at` (DateTime, default utcnow, indexed)
  - `updated_at` (DateTime, default utcnow, onupdate utcnow)
- Add composite indexes:
  - `idx_notification_user_read` on (user_id, read, created_at DESC)
  - `idx_notification_user_created` on (user_id, created_at DESC)
- Add foreign key constraint with ON DELETE CASCADE

### Step 2: Domain Layer - Notification Entity

**Create domain entity:**

File: `backend/app/domain/entities/notification.py`

- Create `NotificationType` enum with values:
  - `VIDEO_DISCOVERED = "video_discovered"`
  - `EPISODE_CREATED = "episode_created"`
- Create `Notification` dataclass with:
  - Fields matching database schema
  - `mark_as_read()` method to toggle read status
  - `__post_init__()` for timestamp initialization
  - Type hints for all fields

**Update domain entities init:**

File: `backend/app/domain/entities/__init__.py`

- Import `Notification` and `NotificationType`
- Add to `__all__` list

### Step 3: Infrastructure Layer - Database Model

**Create SQLAlchemy model:**

File: `backend/app/infrastructure/database/models/notification.py`

- Create `NotificationModel` class extending `Base`
- Map to `notifications` table
- Define all columns matching migration schema
- Add relationship to `UserModel` (back_populates)
- Add composite indexes as `__table_args__`

**Update models init:**

File: `backend/app/infrastructure/database/models/__init__.py`

- Import `NotificationModel`
- Add to `__all__` list

**Update UserModel:**

File: `backend/app/infrastructure/database/models/user.py`

- Add `notifications` relationship:
  - `relationship("NotificationModel", back_populates="user", cascade="all, delete-orphan")`

### Step 4: Infrastructure Layer - Repository

**Create repository implementation:**

File: `backend/app/infrastructure/repositories/notification_repository_impl.py`

- Create `NotificationRepositoryImpl` class
- Implement methods:
  - `async create(notification: Notification) -> Notification`: Create new notification
  - `async get_by_id(notification_id: int) -> Optional[Notification]`: Get single notification
  - `async get_by_user(user_id: int, skip: int, limit: int, unread_only: bool) -> List[Notification]`: Get user's notifications with pagination
  - `async get_unread_count(user_id: int) -> int`: Count unread notifications
  - `async mark_as_read(notification_id: int, user_id: int) -> Notification`: Mark single as read
  - `async mark_all_as_read(user_id: int) -> int`: Mark all as read, return count
  - `async delete(notification_id: int, user_id: int) -> bool`: Delete notification
- Include proper error handling and logging
- Convert between domain entities and database models

### Step 5: Application Layer - Service

**Create notification service:**

File: `backend/app/application/services/notification_service.py`

- Create `NotificationService` class with repository dependency
- Implement core methods:
  - `async create_notification(...)`: Create notification with validation
  - `async get_user_notifications(...)`: Get paginated list
  - `async get_unread_count(user_id: int) -> int`: Get count
  - `async mark_as_read(notification_id: int, user_id: int)`: Mark as read
  - `async mark_all_as_read(user_id: int)`: Mark all as read
  - `async delete_notification(notification_id: int, user_id: int)`: Delete
- Implement helper methods for specific notification types:
  - `async notify_videos_discovered(user_id: int, channel_name: str, video_count: int, followed_channel_id: int)`: Create notification for video discovery
  - `async notify_episode_created(user_id: int, episode_title: str, channel_name: str, episode_id: int, youtube_video_id: int)`: Create notification for episode creation
- Add comprehensive logging for all operations

### Step 6: Presentation Layer - Schemas

**Create Pydantic schemas:**

File: `backend/app/presentation/schemas/notification_schemas.py`

- `NotificationResponse`: Full notification details
  - All fields from domain entity
  - Camel case field names for frontend
- `NotificationListResponse`: Paginated list response
  - `notifications: List[NotificationResponse]`
  - `total: int`
  - `skip: int`
  - `limit: int`
  - `unread_count: int`
- `UnreadCountResponse`: Simple count response
  - `unread_count: int`
- `MarkAsReadResponse`: Confirmation response
  - `success: bool`
  - `notification_id: int`
  - `marked_count: int` (for mark all)

### Step 7: Presentation Layer - API Endpoints

**Create API router:**

File: `backend/app/presentation/api/v1/notifications.py`

- Create FastAPI router with prefix `/notifications`
- Implement endpoints:
  - `GET /` - List user notifications
    - Query params: `skip`, `limit`, `unread_only`
    - Returns `NotificationListResponse`
    - Protected by JWT authentication
  - `GET /unread-count` - Get unread count
    - Returns `UnreadCountResponse`
    - Protected by JWT authentication
  - `PUT /{id}/read` - Mark single as read
    - Path param: notification ID
    - Returns `MarkAsReadResponse`
    - Protected by JWT authentication
  - `PUT /mark-all-read` - Mark all as read
    - Returns `MarkAsReadResponse` with count
    - Protected by JWT authentication
  - `DELETE /{id}` - Delete notification
    - Path param: notification ID
    - Returns 204 No Content
    - Protected by JWT authentication
- Add proper error handling (404, 403, 500)
- Add OpenAPI documentation

**Register router:**

File: `backend/app/main.py` or API router registration file

- Import notifications router
- Register with main API router: `app.include_router(notifications.router, prefix="/v1")`

### Step 8: Dependency Injection Setup

**Update dependencies:**

File: `backend/app/core/dependencies.py`

- Add `get_notification_repository()` function:
  - Returns `NotificationRepositoryImpl` with AsyncSession
- Add `get_notification_service()` function:
  - Returns `NotificationService` with repository dependency
- Add type aliases:
  - `NotificationRepositoryDep`
  - `NotificationServiceDep`

### Step 9: Integration with Celery Tasks

**Update channel check task:**

File: `backend/app/infrastructure/tasks/channel_check_tasks.py`

- Import notification service and repository
- After discovering new videos (line ~100):
  - Get user_id from followed_channel
  - If new videos found, create notification:
    - Call `notification_service.notify_videos_discovered()`
    - Pass user_id, channel_name, video_count, followed_channel_id
  - Handle errors gracefully (log but don't fail task)
- Create new session for notification service

**Update episode creation task:**

File: `backend/app/infrastructure/tasks/create_episode_from_video_task.py`

- Import notification service and repository
- After successfully creating episode (line ~120):
  - Get user_id from channel
  - Create notification:
    - Call `notification_service.notify_episode_created()`
    - Pass user_id, episode.title, channel_name, episode_id, youtube_video_id
  - Handle errors gracefully (log but don't fail task)
- Create new session for notification service

### Step 10: Integration with API Endpoints

**Update episodes endpoint:**

File: `backend/app/presentation/api/v1/episodes.py`

**Upload endpoint (line ~80):**

- After successful episode creation from upload (line ~153):
  - Get notification service from dependencies
  - Get current user from JWT
  - Call `notification_service.notify_episode_created()`
  - Handle errors gracefully

**YouTube URL endpoint (line ~274):**

- After queuing download task (line ~343):
  - Get notification service from dependencies
  - Get current user from JWT
  - Create notification for episode creation initiation
  - Handle errors gracefully

**Update YouTube videos endpoint:**

File: `backend/app/presentation/api/v1/youtube_videos.py`

**Create episode from video endpoint (line ~203):**

- After queuing episode creation task:
  - Get notification service from dependencies
  - Get current user from JWT
  - Create notification (optional, since Celery task will create one)
  - Handle errors gracefully

## Phase 3.2: Frontend Notification UI

### Step 1: Type Definitions

**Update types file:**

File: `frontend/src/types/index.ts`

Add notification types:

```typescript
export enum NotificationType {
  VIDEO_DISCOVERED = "video_discovered",
  EPISODE_CREATED = "episode_created",
}

export interface Notification {
  id: number
  user_id: number
  type: NotificationType
  title: string
  message: string
  data_json?: Record<string, any>
  read: boolean
  created_at: string
  updated_at: string
}

export interface NotificationListResponse {
  notifications: Notification[]
  total: number
  skip: number
  limit: number
  unread_count: number
}

export interface UnreadCountResponse {
  unread_count: number
}
```

### Step 2: API Client Methods

**Update API client:**

File: `frontend/src/lib/api-client.ts`

Add notification methods:

- `getNotifications(skip?, limit?, unreadOnly?): Promise<NotificationListResponse>`: Fetch notifications list
- `getUnreadCount(): Promise<UnreadCountResponse>`: Fetch unread count
- `markNotificationAsRead(id: number): Promise<void>`: Mark single as read
- `markAllNotificationsAsRead(): Promise<void>`: Mark all as read
- `deleteNotification(id: number): Promise<void>`: Delete notification

### Step 3: React Hooks

**Create notifications hook:**

File: `frontend/src/hooks/use-notifications.ts`

Implement hooks using TanStack Query:

- `useNotifications(options?)`: Query hook for fetching notifications
  - Supports pagination and filtering
  - Auto-refetch on window focus
- `useUnreadCount()`: Query hook for unread count
  - Polls every 30 seconds
  - Auto-refetch on window focus
- `useMarkAsRead()`: Mutation hook for marking as read
  - Invalidates queries on success
- `useMarkAllAsRead()`: Mutation hook for marking all as read
  - Invalidates queries on success
- `useDeleteNotification()`: Mutation hook for deletion
  - Invalidates queries on success

### Step 4: Notification Item Component

**Create notification item component:**

File: `frontend/src/components/features/notifications/notification-item.tsx`

Features:

- Display notification with appropriate icon based on type
- Show title, message, and relative timestamp ("2 hours ago")
- Visual indicator for unread (bold text, colored dot)
- Click handler to:
  - Mark as read
  - Navigate to relevant page (channel videos, episode detail)
- Delete button (X icon)
- Hover states and animations
- Use Lucide icons: Video for video_discovered, CheckCircle for episode_created

### Step 5: Notification Bell Component

**Create notification bell component:**

File: `frontend/src/components/layout/notification-bell.tsx`

Features:

- Bell icon button in header/toolbar
- Badge showing unread count (red, only if > 0)
- Dropdown/popover on click:
  - Header with "Notifications" title and "Mark all as read" button
  - List of recent notifications (max 5-10)
  - Each uses NotificationItem component
  - "View All" link to full page
  - Empty state: "No notifications" with icon
- Use shadcn Popover component
- Auto-close on navigation
- Polling for unread count

### Step 6: Update Side Panel

**Update side panel:**

File: `frontend/src/components/layout/sidepanel.tsx`

Changes:

- Add notification bell near top of utility items section (line ~102)
- Replace existing "Notifications" nav item that links to channels?filter=pending
- Position bell icon component in header or utility section
- Ensure proper spacing and alignment
- Keep collapsed state support

### Step 7: Notification List Page (Optional)

**Create notifications page:**

File: `frontend/src/app/notifications/page.tsx`

Features:

- Full page view of all notifications
- Tabs/filters: All, Unread, Read
- Pagination controls
- Mark all as read button in header
- Uses NotificationItem components
- Empty states for each tab
- Responsive grid layout

### Step 8: Navigation from Notifications

**Implement smart navigation:**

In `notification-item.tsx`, implement click handler logic:

- For VIDEO_DISCOVERED:
  - Navigate to `/subscriptions/videos?channel={followed_channel_id}&state=pending_review`
  - Parse followed_channel_id from data_json
- For EPISODE_CREATED:
  - Navigate to `/channel?episode={episode_id}` or episode detail page
  - Parse episode_id from data_json
- Mark as read on navigation
- Show loading state during navigation

## Testing Strategy

### Backend Testing

1. **Database Migration:**

   - Run migration up and down
   - Verify table structure and indexes
   - Test foreign key cascade

2. **Repository Tests:**

   - Test CRUD operations
   - Test pagination and filtering
   - Test mark as read/delete with wrong user_id (should fail)

3. **Service Tests:**

   - Test notification creation
   - Test helper methods
   - Test error handling

4. **API Tests:**

   - Test all endpoints with authenticated requests
   - Test unauthorized access (401)
   - Test pagination parameters
   - Test mark all as read count

5. **Integration Tests:**

   - Trigger video discovery and verify notification created
   - Trigger episode creation and verify notification created
   - Verify notifications for different users don't leak

### Frontend Testing

1. **Component Tests:**

   - Test NotificationBell renders correctly
   - Test badge shows/hides based on count
   - Test NotificationItem click handlers
   - Test delete functionality

2. **Hook Tests:**

   - Test useNotifications fetching
   - Test useUnreadCount polling
   - Test mutation hooks invalidate queries

3. **Integration Tests:**

   - Test notification bell popover interaction
   - Test navigation from notifications
   - Test mark as read updates UI
   - Test real-time polling updates count

4. **E2E Tests:**

   - Follow a channel → discover videos → verify notification
   - Create episode → verify notification
   - Click notification → verify navigation
   - Mark all as read → verify count becomes 0

## Implementation Order

1. Backend database migration
2. Backend domain entity and model
3. Backend repository
4. Backend service
5. Backend API endpoints
6. Backend dependency injection
7. Backend Celery task integration
8. Backend API endpoint integration
9. Frontend types
10. Frontend API client
11. Frontend hooks
12. Frontend NotificationItem component
13. Frontend NotificationBell component
14. Frontend SidePanel integration
15. Frontend Notifications page (optional)
16. Testing and bug fixes

## Notes and Considerations

- **Security:** Ensure notifications are properly scoped to users (user_id checks in all operations)
- **Performance:** Add database indexes for fast queries, use pagination
- **Polling:** Frontend polls unread count every 30 seconds (configurable)
- **Real-time:** Consider WebSockets/SSE in future for true real-time updates
- **Cleanup:** Consider adding a cleanup job to delete old read notifications (e.g., >30 days)
- **Rate limiting:** Consider rate limiting notification creation to prevent spam
- **Batch notifications:** For bulk operations, consider grouping notifications (e.g., "10 videos discovered" instead of 10 separate notifications)
- **User preferences:** Consider adding user settings for notification preferences in future
