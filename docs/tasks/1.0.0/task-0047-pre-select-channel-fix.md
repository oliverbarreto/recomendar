# Task 0047: Pre-select Channel in Create Episode Dialog

**Date**: 2025-11-14  
**Status**: ✅ Completed

## Problem

When clicking "Create Episode" from a YouTube video, the modal dialog appeared with a channel selector dropdown, but no channel was pre-selected. This required the user to manually select the channel even though there's only one channel available in the application (ID: 1 in the `channels` table).

## Root Cause

1. **Data Access Issue**: The component was incorrectly accessing channel data as `channelsData?.data`, but `useChannels()` returns `Channel[]` directly, not wrapped in a `data` property.
2. **Timing Issue**: The `handleCreateEpisode` function tried to synchronously select the channel, but channels might not be loaded yet when the dialog opens (React Query is async).

## Solution

### Changes Made

**File**: `frontend/src/components/features/subscriptions/video-list.tsx`

1. **Fixed data access** (line 65):
   - Changed from `const { data: channelsData } = useChannels()` and `channelsData?.data || []`
   - To: `const { data: channels = [] } = useChannels()`
   - `useChannels()` returns `Channel[]` directly, not wrapped in a `data` property

2. **Added `useEffect` hook** (lines 70-75):
   - Automatically selects the channel when the dialog opens AND channels are loaded
   - Handles the async nature of React Query data loading
   - Only selects if there's exactly one channel and none is currently selected

```typescript
// Auto-select channel when dialog opens and channels are loaded
useEffect(() => {
    if (createEpisodeDialogOpen && channels.length === 1 && !selectedPodcastChannel) {
        setSelectedPodcastChannel(channels[0].id)
    }
}, [createEpisodeDialogOpen, channels, selectedPodcastChannel])
```

3. **Updated `handleCreateEpisode` function** (lines 85-91):
   - Kept synchronous check as a fallback for when channels are already loaded
   - This provides immediate selection when possible

```typescript
const handleCreateEpisode = (video: YouTubeVideo) => {
    setSelectedVideoForEpisode(video)
    // Pre-select the first channel if there's only one available
    if (channels.length === 1) {
        setSelectedPodcastChannel(channels[0].id)
    }
    setCreateEpisodeDialogOpen(true)
}
```

4. **Added `handleDialogClose` function** (lines 105-112):
   - Properly resets state when the dialog closes (via Cancel button or X button)
   - Ensures clean state for the next dialog opening

```typescript
const handleDialogClose = (open: boolean) => {
    setCreateEpisodeDialogOpen(open)
    if (!open) {
        // Reset state when dialog closes
        setSelectedVideoForEpisode(null)
        setSelectedPodcastChannel(null)
    }
}
```

5. **Updated Dialog component** (line 224):
   - Changed `onOpenChange` handler from `setCreateEpisodeDialogOpen` to `handleDialogClose`
   - Ensures proper cleanup when dialog is closed by any means

## Benefits

1. **Improved UX**: Users can immediately click "Create Episode" without needing to select the channel
2. **Future-proof**: When multiple channels are supported, the logic will still work correctly (only pre-selects when there's exactly one channel)
3. **Proper State Management**: Dialog state is properly cleaned up when closed, preventing stale data

## Testing

To test this fix:

1. Navigate to `/subscriptions` → "Videos" tab
2. Click "Create Episode" on any video
3. **Expected**: The channel dropdown should be pre-filled with the available channel
4. **Expected**: The "Create Episode" button should be enabled immediately
5. Click "Cancel" or close the dialog
6. Open the dialog again
7. **Expected**: The channel should still be pre-selected

## Related Files

- `frontend/src/components/features/subscriptions/video-list.tsx` - Main component with the fix

## Notes

- This fix maintains the dropdown UI, which is correct for future multi-channel support
- The solution is elegant and doesn't require backend changes
- No database migrations or API changes needed

