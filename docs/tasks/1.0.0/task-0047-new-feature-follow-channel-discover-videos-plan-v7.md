# Activity Page and Notification System Redesign

## Overview

This plan transforms the notification system by:

1. Creating a new `/activity` page with a table view of all notifications
2. Converting the notification bell to a direct navigation link
3. Adding filtering, pagination, and management features
4. Updating the sidebar navigation

## Phase 1: Backend API Enhancements

### 1.1 Add Delete All Notifications Endpoint

**File**: [`backend/app/presentation/api/v1/notifications.py`](backend/app/presentation/api/v1/notifications.py)

Add a new endpoint to delete all notifications for a user:

```python
@router.delete(
    "/delete-all",
    response_model=DeleteAllResponse,
    responses={
        401: {"description": "Authentication required"},
        500: {"description": "Internal server error"}
    }
)
async def delete_all_notifications(
    current_user: Annotated[dict, Depends(get_current_user_jwt)],
    notification_service: NotificationService = Depends(get_notification_service)
) -> DeleteAllResponse:
    """Delete all notifications for current user"""
```

### 1.2 Add Delete Single Notification Endpoint

Add endpoint to delete a single notification (not just mark as read).

### 1.3 Update Response Schemas

**File**: [`backend/app/presentation/schemas/notification_schemas.py`](backend/app/presentation/schemas/notification_schemas.py)

Add new response schemas for delete operations.

### 1.4 Update Notification Service

**File**: [`backend/app/application/services/notification_service.py`](backend/app/application/services/notification_service.py)

Add methods:

- `delete_notification(notification_id, user_id)`
- `delete_all_notifications(user_id)`

### 1.5 Update Notification Repository

**File**: [`backend/app/infrastructure/repositories/notification_repository_impl.py`](backend/app/infrastructure/repositories/notification_repository_impl.py)

Implement delete methods in the repository layer.

## Phase 2: Frontend Type Definitions

### 2.1 Update Types

**File**: [`frontend/src/types/index.ts`](frontend/src/types/index.ts)

Add new response types:

- `DeleteNotificationResponse`
- `DeleteAllNotificationsResponse`

## Phase 3: Frontend API Client

### 3.1 Add API Methods

**File**: [`frontend/src/lib/api-client.ts`](frontend/src/lib/api-client.ts)

Add new methods:

- `deleteNotification(notificationId: number)`
- `deleteAllNotifications()`

## Phase 4: Frontend Hooks

### 4.1 Add Delete Hooks

**File**: [`frontend/src/hooks/use-notifications.ts`](frontend/src/hooks/use-notifications.ts)

Add new hooks:

- `useDeleteNotification()` - Delete single notification
- `useDeleteAllNotifications()` - Delete all notifications with confirmation

## Phase 5: Activity Page Components

### 5.1 Create Activity Table Component

**File**: `frontend/src/components/features/activity/activity-table.tsx`

Create a responsive table component with columns:

- Type (with icon and descriptive text)
- Channel (with link to `/subscriptions/videos?channel={id}`)
- Date (dd/MM/yyyy format)
- Time (HH:mm:ss format)
- Description
- Actions (context menu with "Mark as read" option)

Features:

- Row highlighting for unread notifications
- Click row to mark as read and navigate
- Context menu with ellipsis icon for actions

### 5.2 Create Activity Filters Component

**File**: `frontend/src/components/features/activity/activity-filters.tsx`

Create filters component with:

- Notification type filter (dropdown with all types)
- Date range picker (from/to dates)
- Channel filter (dropdown with followed channels)
- Read status filter ("Unread only" / "Show all")

### 5.3 Create Activity Page Actions Component

**File**: `frontend/src/components/features/activity/activity-actions.tsx`

Create actions bar with:

- "Mark all as read" button (with confirmation dialog)
- "Delete all" button (with confirmation dialog)

### 5.4 Create Activity Page

**File**: `frontend/src/app/activity/page.tsx`

Main page component that:

- Combines filters, table, and actions
- Manages pagination state
- Handles URL search params for filters (bookmarkable)
- Shows loading and empty states
- Defaults to "Unread only" filter on initial load

## Phase 6: Update Notification Bell

### 6.1 Simplify Notification Bell Component

**File**: [`frontend/src/components/layout/notification-bell.tsx`](frontend/src/components/layout/notification-bell.tsx)

Transform the component to:

- Remove the popover/popup functionality
- Convert to a simple Link component wrapping the bell icon
- Keep the unread count badge (polling every 5 seconds)
- Navigate directly to `/activity` on click
- Maintain the collapsed state support for sidebar

Example structure:

```tsx
<Link href="/activity">
  <Button variant="ghost" size="icon">
    <Bell className="h-5 w-5" />
    {unreadCount > 0 && (
      <Badge variant="destructive">
        {unreadCount > 99 ? "99+" : unreadCount}
      </Badge>
    )}
  </Button>
</Link>
```

### 6.2 Remove Notification Item Component Usage

**File**: [`frontend/src/components/features/notifications/notification-item.tsx`](frontend/src/components/features/notifications/notification-item.tsx)

This component will be repurposed for the Activity page table rows instead of popup items.

## Phase 7: Update Sidebar Navigation

### 7.1 Add Activity Link to Sidebar

**File**: [`frontend/src/components/layout/sidepanel.tsx`](frontend/src/components/layout/sidepanel.tsx)

Add new navigation item:

```typescript
{
  name: "Activity",
  href: "/activity",
  icon: Clock
}
```

Position it after "Subscriptions Videos" in the primary navigation section.

## Phase 8: Notification Type Display

### 8.1 Create Notification Type Helper

**File**: `frontend/src/lib/notification-helpers.ts`

Create utility functions:

- `getNotificationTypeLabel(type: NotificationType): string` - Returns descriptive text
- `getNotificationTypeIcon(type: NotificationType)` - Returns appropriate icon
- `getNotificationTypeColor(type: NotificationType)` - Returns color classes

Map enum values to user-friendly labels:

- `channel_search_started` → "Search Started"
- `channel_search_completed` → "Search Completed"
- `channel_search_error` → "Search Error"
- `video_discovered` → "Videos Discovered"
- `episode_created` → "Episode Created"

## Phase 9: Testing and Polish

### 9.1 Test Complete Flow

- Trigger channel search and verify notifications appear
- Test filtering by type, date, channel, and read status
- Test pagination with large notification lists
- Test mark as read (single and bulk)
- Test delete (single and bulk with confirmations)
- Test bell badge updates in real-time
- Test navigation from bell to activity page
- Test responsive design on mobile/tablet
- Test URL persistence for filters (bookmarking)

### 9.2 Accessibility Review

- Ensure keyboard navigation works
- Verify screen reader compatibility
- Test focus management
- Validate ARIA labels

### 9.3 Performance Optimization

- Verify polling intervals are appropriate
- Check query invalidation logic
- Ensure pagination doesn't cause unnecessary re-renders

## Implementation Notes

### Key Design Decisions

1. **URL Search Params**: Use URL search params for all filters to enable bookmarking and sharing
2. **Default Filter**: Page loads with "Unread only" filter active by default
3. **Real-time Updates**: Continue polling every 5 seconds for unread count
4. **Confirmation Dialogs**: Both "Mark all as read" and "Delete all" require confirmation
5. **Row Actions**: Context menu on each row for granular control
6. **Direct Navigation**: Bell icon becomes a direct link (no popup)

### Files to Create

- `frontend/src/app/activity/page.tsx`
- `frontend/src/components/features/activity/activity-table.tsx`
- `frontend/src/components/features/activity/activity-filters.tsx`
- `frontend/src/components/features/activity/activity-actions.tsx`
- `frontend/src/lib/notification-helpers.ts`

### Files to Modify

- `backend/app/presentation/api/v1/notifications.py`
- `backend/app/presentation/schemas/notification_schemas.py`
- `backend/app/application/services/notification_service.py`
- `backend/app/infrastructure/repositories/notification_repository_impl.py`
- `frontend/src/types/index.ts`
- `frontend/src/lib/api-client.ts`
- `frontend/src/hooks/use-notifications.ts`
- `frontend/src/components/layout/notification-bell.tsx`
- `frontend/src/components/layout/sidepanel.tsx`
- `frontend/src/components/features/notifications/notification-item.tsx` (repurpose)

### Dependencies

- Existing notification system (polling, API endpoints)
- Existing UI components (Table, Dialog, DropdownMenu, DatePicker)
- Existing routing structure
- React Query for data fetching
- URL search params for filter state
