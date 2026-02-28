# Divide Subscriptions Page Tabs into Two Pages

## Overview

Split the current `/subscriptions` page tabs into two separate pages while preserving the original page functionality. Add sidebar navigation for both pages and implement URL search parameters for video filtering.

## Current State Analysis

### Current Implementation

- `/subscriptions` page uses tabs to switch between "Followed Channels" and "Videos"
- `VideoList` component uses local state for filtering (selectedState, selectedChannel, searchQuery)
- Backend API already supports filtering via query params (state, followed_channel_id, search)
- Sidebar has single "Subscriptions" link pointing to `/subscriptions` with `Rss` icon
- Notification button points to `/subscriptions?filter=pending`

### Video Filtering Analysis

**Recommendation: Use URL search params for video filtering**

Benefits:

- Enables bookmarking and sharing filtered views
- Browser back/forward buttons work correctly
- Page refresh maintains filter state
- Consistent with existing `/channel` page pattern
- Backend API already supports query params

Current filtering state:

- `selectedState`: YouTubeVideoState | 'all' (pending_review, reviewed, episode_created, downloading)
- `selectedChannel`: number | 'all' (followed_channel_id)
- `searchQuery`: string

## Implementation Plan

### 1. Create New Page Routes

#### 1.1 Create `/subscriptions/channels/page.tsx`

- Location: `frontend/src/app/subscriptions/channels/page.tsx`
- Content: Followed Channels tab content
- Include: PageHeader with "Follow Channel" button
- Include: Navigation link to `/subscriptions/videos` (tab-like navigation)
- Include: FollowChannelModal component

#### 1.2 Create `/subscriptions/videos/page.tsx`

- Location: `frontend/src/app/subscriptions/videos/page.tsx`
- Content: Videos tab content
- Include: PageHeader with "Follow Channel" button
- Include: Navigation link to `/subscriptions/channels` (tab-like navigation)
- Implement: URL search params for filtering (state, channel, search)

### 2. Update VideoList Component for URL Search Params

#### 2.1 Modify `frontend/src/components/features/subscriptions/video-list.tsx`

- Add `useSearchParams` and `useRouter` from `next/navigation`
- Read initial filter values from URL search params:
  - `state`: YouTubeVideoState | 'all'
  - `channel`: number | 'all' (followed_channel_id)
  - `search`: string
- Update URL when filters change (using `router.replace` to avoid history stack)
- Sync local state with URL params on mount and when URL changes
- Maintain backward compatibility with existing props

### 3. Update Sidebar Navigation

#### 3.1 Modify `frontend/src/components/layout/sidepanel.tsx`

- Replace single "Subscriptions" nav item with two items:
  - "Followed Channels" → `/subscriptions/channels` with `Rss` icon
  - "Videos" → `/subscriptions/videos` with `Video` icon (or `List` if preferred)
- Update `isActive` function to handle both new routes
- Update active state logic to highlight correct nav item

### 4. Update Notification Button

#### 4.1 Modify `frontend/src/components/layout/sidepanel.tsx`

- Change notification button href from `/subscriptions?filter=pending` to `/subscriptions/channels?filter=pending`
- Ensure the filter parameter is properly handled on the channels page

### 5. Add Tab-like Navigation Between Pages

#### 5.1 Create Navigation Component (or add inline)

- Add tab-like navigation buttons/links on both pages
- Style similar to existing Tabs component
- Links should navigate between `/subscriptions/channels` and `/subscriptions/videos`
- Highlight active page

### 6. Preserve Existing `/subscriptions` Page

#### 6.1 Verify `/subscriptions/page.tsx`

- Ensure no changes are made to this file
- Original tab-based functionality remains intact

## Files to Modify

1. `frontend/src/app/subscriptions/channels/page.tsx` (NEW)
2. `frontend/src/app/subscriptions/videos/page.tsx` (NEW)
3. `frontend/src/components/features/subscriptions/video-list.tsx` (MODIFY - add URL search params)
4. `frontend/src/components/layout/sidepanel.tsx` (MODIFY - update navigation)

## Files to Keep Unchanged

1. `frontend/src/app/subscriptions/page.tsx` (PRESERVE - no changes)

## Technical Details

### URL Search Params Structure for Videos Page

```
/subscriptions/videos?state=pending_review&channel=123&search=keyword
```

### Search Params Implementation Pattern

- Use Next.js 15 App Router `searchParams` prop (server component) or `useSearchParams` hook (client component)
- Follow pattern from `/channel` page (see `frontend/src/app/channel/page.tsx`)
- Use `router.replace()` to update URL without adding to history stack
- Parse and validate search params on component mount

### Navigation Active State

- Update `isActive` function in sidepanel to check:
  - `/subscriptions/channels` → active when pathname starts with `/subscriptions/channels`
  - `/subscriptions/videos` → active when pathname starts with `/subscriptions/videos`
  - Original `/subscriptions` → active when pathname is exactly `/subscriptions`

## Testing Considerations

- Verify both new pages render correctly
- Test navigation between pages via sidebar and tab links
- Verify URL search params work for video filtering
- Test browser back/forward buttons with filters
- Verify notification button redirects correctly
- Ensure original `/subscriptions` page still works
- Test filter persistence on page refresh
