# Task 0049: Replace Top Navigation with Collapsible Side Panel

## Overview

Replace the current top navigation header (`header.tsx`) with a left-hand collapsible side panel component that matches the Figma design specifications. The side panel will support both collapsed (icons only with tooltips) and expanded (icons + labels) states.

## Implementation Plan

### Phase 1: Component Cleanup and Preparation

1. **Remove unused Sidebar component**

- Delete `frontend/src/components/layout/sidebar.tsx`
- Remove Sidebar export from `frontend/src/components/layout/index.ts`

2. **Audit Header component usage**

- Verify all navigation items and functionality to migrate
- Document current props and state management (`onSearchToggle`, `showSearchButton`, mobile menu, QuickAdd dialog)

### Phase 2: Create New SidePanel Component

1. **Create `frontend/src/components/layout/sidepanel.tsx`**

- Implement collapsed/expanded state management using React state
- Add toggle button with chevron icon (left arrow when expanded, right when collapsed)
- Structure sections:
 - **Logo section**: Purple circular logo with microphone icon + "LabcastARR" text (visible only in expanded state)
 - **Primary navigation**: Home, Channel, Subscriptions (with icons and labels)
 - **Quick Add section**: Quick Add (dialog), Add from YouTube, Upload Episode (with separator above)
 - **Utility section**: Notifications (with badge), Theme Toggle, Settings (with separator above)
- Implement tooltip functionality for collapsed state using shadcn Tooltip component
- Match Figma styling: dark gray background, proper spacing, hover states, active state highlighting

2. **Navigation items mapping from Header**:

- Home (`/`) - Home icon (new, not in current header)
- Channel (`/channel`) - Podcast icon
- Subscriptions (`/subscriptions`) - Bell icon
- Quick Add (dialog action) - Zap icon
- Add from YouTube (`/episodes/add-from-youtube`) - Video icon
- Upload Episode (`/episodes/add-from-upload`) - Upload icon
- Notifications (`/subscriptions?filter=pending`) - Bell icon with pending count badge
- Theme Toggle - Moon/Sun icon (reuse ThemeToggle component)
- Settings (`/settings`) - Settings icon

3. **Features to implement**:

- Collapse/expand toggle with smooth animation
- Active route highlighting using `usePathname()` hook
- Tooltips for all navigation items in collapsed state
- Quick Add dialog integration (reuse QuickAddDialog component)
- Pending notifications badge (reuse `usePendingVideosCount` hook)
- Responsive behavior (mobile considerations)

### Phase 3: Update MainLayout Component

1. **Modify `frontend/src/components/layout/main-layout.tsx`**

- Replace `Header` import with `SidePanel`
- Update layout structure: side panel on left, main content area on right
- Adjust main content padding to account for side panel width
- Preserve `onSearchToggle` and `showSearchButton` props for pages that need them (e.g., channel page)
- Handle responsive layout (side panel behavior on mobile)

2. **Layout structure**:

- Side panel: fixed width when expanded (~240px), narrow when collapsed (~64px)
- Main content: flex-1 with proper margin/padding
- Ensure proper z-index layering

### Phase 4: Update Pages and Components

1. **Verify all pages using MainLayout**:

- `frontend/src/app/page.tsx` (home)
- `frontend/src/app/channel/page.tsx` (needs search toggle)
- `frontend/src/app/subscriptions/page.tsx`
- `frontend/src/app/episodes/add/page.tsx`
- `frontend/src/app/episodes/add-from-youtube/page.tsx`
- `frontend/src/app/episodes/add-from-upload/page.tsx`
- `frontend/src/app/episodes/[id]/page.tsx`
- `frontend/src/app/search/page.tsx`
- `frontend/src/app/settings/page.tsx`
- `frontend/src/app/setup/page.tsx`
- All should continue working without changes (MainLayout API preserved)

2. **Handle search functionality**:

- Channel page uses `onSearchToggle` prop - need to determine how to expose search in new side panel
- Options: Add search icon to side panel, or keep search button in main content area

### Phase 5: Styling and Polish

1. **Match Figma design specifications**:

- Dark gray side panel background (`bg-muted` or custom)
- White text and icons
- Proper spacing and padding
- Hover states with light gray background
- Active route highlighting
- Smooth collapse/expand transitions
- Purple accent for logo
- Proper separator lines between sections

2. **Responsive design**:

- Mobile: Side panel should overlay or transform to bottom navigation?
- Tablet: Consider collapsed state by default?
- Desktop: Full expanded/collapsed functionality

### Phase 6: Testing and Validation

1. **Functionality testing**:

- All navigation links work correctly
- Active state highlighting works
- Quick Add dialog opens correctly
- Theme toggle works
- Notifications badge shows correct count
- Search toggle works on channel page (if applicable)

2. **Visual testing**:

- Collapsed state shows icons with tooltips
- Expanded state shows icons + labels
- Smooth transitions between states
- Matches Figma design specifications
- Responsive behavior works correctly

3. **Accessibility**:

- Keyboard navigation support
- ARIA labels for screen readers
- Focus management for toggle button

## Files to Modify/Create

### New Files

- `frontend/src/components/layout/sidepanel.tsx` (create new)

### Files to Modify

- `frontend/src/components/layout/main-layout.tsx` (replace Header with SidePanel)
- `frontend/src/components/layout/index.ts` (remove Sidebar export, add SidePanel export)

### Files to Delete

- `frontend/src/components/layout/sidebar.tsx` (unused component)

### Files to Review (No Changes Expected)

- All page files using MainLayout (should continue working)
- `frontend/src/components/layout/header.tsx` (can be deprecated but keep for reference)

## Key Technical Decisions

1. **State Management**: Use React `useState` for collapse/expand state, optionally persist to localStorage
2. **Tooltips**: Use shadcn `Tooltip` component for collapsed state
3. **Icons**: Continue using Lucide React icons (already in use)
4. **Styling**: Use TailwindCSS v4 with existing design tokens
5. **Animation**: CSS transitions for smooth collapse/expand
6. **Search Integration**: Determine best UX for search toggle - may need to add search icon to side panel or keep in main content area

## Dependencies

- shadcn/ui Tooltip component (may need to install if not present)
- Existing components: ThemeToggle, QuickAddDialog
- Existing hooks: usePendingVideosCount, usePathname
- Lucide React icons (already installed)