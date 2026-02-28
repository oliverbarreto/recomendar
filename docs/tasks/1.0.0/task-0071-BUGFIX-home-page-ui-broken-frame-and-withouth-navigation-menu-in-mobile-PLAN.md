# Fix Home Page Mobile UI and Navigation

## Problem Analysis

1. **Container Overflow Issue**: The `ChannelDashboard` component has `container mx-auto` which conflicts with `MainLayout`'s existing container (`max-w-7xl mx-auto px-4`), causing horizontal overflow on mobile devices.

2. **Missing Mobile Navigation**: The `SidePanel` is hidden on mobile (`hidden md:block`), and `MainLayout` doesn't include a mobile navigation menu, leaving users without navigation on mobile devices.

3. **Horizontal Scroll Section**: The "Latest Episodes" horizontal scroll section uses fixed-width cards (`w-80` = 320px) which may contribute to overflow issues on smaller screens.

## Solution

### 1. Fix Container Overflow in ChannelDashboard

**File**: `frontend/src/components/features/channel-dashboard.tsx`

- Remove the redundant `container mx-auto` classes from line 276
- Keep `space-y-6 min-w-0` classes for proper spacing and width constraints
- Ensure the horizontal scroll container properly handles overflow on mobile

**Changes**:

- Line 276: Change `className="space-y-6 min-w-0 container mx-auto "` to `className="space-y-6 min-w-0"`
- Verify the horizontal scroll section (Latest Episodes) properly constrains width on mobile

### 2. Add Mobile Navigation Menu to MainLayout

**File**: `frontend/src/components/layout/main-layout.tsx`

- Add a mobile navigation header that shows only on mobile devices (`md:hidden`)
- Include a hamburger menu button that toggles a mobile navigation drawer
- The mobile navigation should include all navigation items from `SidePanel`:
- Dashboard (/)
- Channel (/channel)
- Followed Channels (/subscriptions/channels)
- Subscriptions Videos (/subscriptions/videos)
- Activity (/activity)
- Quick Add (dialog)
- Add from YouTube (/episodes/add-from-youtube)
- Upload Episode (/episodes/add-from-upload)
- Settings (/settings)
- Theme toggle

**Implementation Approach**:

- Create a mobile header component or add mobile navigation directly to `MainLayout`
- Use a drawer/sheet component (likely from shadcn/ui) for the mobile menu
- Position the header at the top of the screen on mobile
- Ensure proper z-index layering (mobile nav should be above content but below modals)

### 3. Ensure Proper Mobile Responsiveness

**Files**:

- `frontend/src/components/features/channel-dashboard.tsx`
- `frontend/src/components/layout/main-layout.tsx`

- Verify that padding and margins work correctly on mobile
- Ensure the main content area doesn't overflow horizontally
- Test that the horizontal scroll section for Latest Episodes works properly on mobile without causing page-level overflow

## Implementation Details

### Mobile Navigation Component Structure

The mobile navigation should:

- Be a sticky header at the top on mobile only
- Include a hamburger icon that opens a drawer/sheet
- Show navigation items in a vertical list when drawer is open
- Match the navigation structure from `SidePanel` but adapted for mobile
- Include theme toggle and settings access

### Testing Checklist

- [ ] Home page displays correctly on iPhone (portrait and landscape)
- [ ] Home page displays correctly on iPad (portrait and landscape)
- [ ] No horizontal scrolling at the page level
- [ ] Mobile navigation menu is accessible and functional
- [ ] All navigation links work correctly from mobile menu
- [ ] Latest Episodes horizontal scroll works without causing page overflow
- [ ] Other pages (/channel, /activity, etc.) still work correctly

## Files to Modify

1. `frontend/src/components/features/channel-dashboard.tsx` - Remove redundant container classes
2. `frontend/src/components/layout/main-layout.tsx` - Add mobile navigation header and drawer

## Files to Potentially Create

1. `frontend/src/components/layout/mobile-nav.tsx` - New component for mobile navigation (optional, can be inline in MainLayout)
