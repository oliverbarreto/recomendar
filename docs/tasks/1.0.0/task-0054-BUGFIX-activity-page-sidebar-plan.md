# Add Sidebar to Activity Page

## Problem

The `/activity` page is missing the sidebar navigation because it's not using the `MainLayout` component that includes the `SidePanel`.

## Solution

Wrap the Activity page content with the `MainLayout` component, following the same pattern used by other pages like `/subscriptions/channels` and `/subscriptions/videos`.

## Changes Required

### File: `frontend/src/app/activity/page.tsx`

1. **Import MainLayout component** at the top of the file
2. **Wrap the page content** with `<MainLayout>` component
3. **Adjust container styling** to match the pattern used by other pages (use `py-6` instead of `p-6` to avoid double horizontal padding, since MainLayout already provides horizontal padding)

The MainLayout component will automatically:

- Include the SidePanel (sidebar) with all navigation items
- Handle responsive layout with proper margins for the sidebar
- Manage sidebar collapse state

## Implementation Details

The change is minimal - just wrapping existing content with MainLayout:

```typescript
// Before: Direct content rendering
return <div className="container mx-auto p-6 space-y-6">{/* content */}</div>

// After: Wrapped with MainLayout
return (
  <MainLayout>
    <div className="container mx-auto py-6 space-y-6">{/* content */}</div>
  </MainLayout>
)
```

This matches the pattern used in:

- `frontend/src/app/subscriptions/channels/page.tsx`
- `frontend/src/app/subscriptions/videos/page.tsx`
- `frontend/src/app/page.tsx`
