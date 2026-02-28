# Prompt

I now want you to add a new button in the frontend navbar to "quick add" an episode that utilizes the quick add operation in the API, that takes a video url and directly creates an episode without going through the multi-step form of "Add Episode" button. The information needed to create the episode should be extracted automatically extracted from the video url.

Utilize the existing API endpoint for quick add episode:

---

## Result

⏺ Perfect! No errors. Now let me update the final todo:

⏺ Perfect! I've successfully implemented the Quick Add Episode feature with all TypeScript issues resolved.
Here's a summary of what was implemented:

Summary of Changes Made:

1. Created QuickAddDialog Component (quick-add-dialog.tsx):

- Modal dialog with YouTube URL input field
- Basic URL validation for YouTube links
- Automatic channel detection (uses first available channel)
- Integration with existing episodeApi.create() method
- Loading states and error handling
- Success feedback with toast notifications

2. Enhanced Header Component (header.tsx):

- Added "Quick Add" button with Zap icon to the navbar
- Button appears in both desktop (right side) and mobile (mobile menu) layouts
- Integrated QuickAddDialog component with proper state management
- Auto-refresh functionality after successful episode creation

3. Key Features Implemented:

- One-click Access: Quick Add button prominently placed in navbar
- Streamlined UX: Simple dialog with just URL input field
- Auto-extraction: Uses existing API to automatically extract video metadata
- Error Handling: Proper validation and user feedback
- Responsive Design: Works on both desktop and mobile devices
- TypeScript Safe: Proper error typing without any types

4. API Integration:

- Uses existing episodeApi.create() method
- Leverages existing video analysis capabilities
- Maintains consistency with current episode creation workflow

How It Works:

1. User clicks "Quick Add" button in navbar (desktop) or mobile menu
2. Modal opens with YouTube URL input field
3. User pastes URL and clicks "Add Episode"
4. System validates URL and shows loading state
5. API calls automatically extract video metadata and create episode
6. Success notification shows episode title and processing status
7. Page refreshes to show the new episode in the grid

The feature provides a much faster alternative to the full "Add Episode" form, perfect for users who want
to quickly add episodes without configuring additional metadata manually.

