# Prompt

> I want now to improve the UX of the /channel page. More concretely i want to hide the search component and add a seearch icon on the navigation header to the left of the "Dark Theme Toggle" button, that shows the current search component with a subtle and modern animation. We then need to click a button to hide the search component. We do not want to change the current search functionality and UX at all. Just the way we show the component with the objetive to make the search component less predominant in the page 

---

## Result

⏺ Perfect! Now I have a comprehensive understanding of the current structure. Let me analyze what needs to be
done and create a plan.

<ExitPlanMode plan="## Improve UX: Collapsible Search Interface from Navigation Header

Current State Analysis

- /channel page currently shows the SearchInterface component always visible as a prominent Card
- SearchInterface contains search input and tag filtering functionality
- Header has ThemeToggle and Settings buttons on the right side
- Navigation already supports dialog-based interactions (like QuickAdd)

Goal

Transform the search interface from always-visible to a collapsible overlay triggered by a search icon in
the header, making the search less predominant while preserving all functionality.

Implementation Plan

Phase 1: Create Search Overlay Component

1. Create SearchOverlay component (/components/features/search/search-overlay.tsx)
- Wrap the existing SearchInterface in a modern overlay/drawer
- Add smooth slide-down animation from the header
- Include close button and backdrop click to close
- Maintain all current search functionality and state management
- Add proper z-index for overlay positioning

Phase 2: Add Search Context/State Management

1. Create SearchContext (/contexts/search-context.tsx)
- Manage search overlay open/close state globally
- Allow triggering search overlay from anywhere in the app
- Handle URL state synchronization when overlay opens/closes

Phase 3: Update Header Component

1. Add Search Icon to Header (/components/layout/header.tsx)
- Add Search icon button to the right side, before ThemeToggle
- Position: [Search Icon] [Theme Toggle] [Settings] [Mobile Menu]
- Wire up to open the SearchOverlay
- Only show on pages that support search (like /channel)

Phase 4: Update Channel Page

1. Modify Channel Page (/app/channel/page.tsx)
- Remove the always-visible SearchInterface component
- Show EpisodeGrid directly with clean layout
- Integrate with SearchContext for when overlay is active
- Maintain URL parameter handling for search state

Phase 5: Create Smooth UX Transitions

1. Add Animation System
- Framer Motion or CSS-based slide animations
- Smooth backdrop fade-in/out
- Search overlay slides down from header position
- Subtle elevation and shadow effects

Phase 6: Handle Edge Cases

1. URL State Management
- When user lands on /channel?q=search&tags=1,2 directly, auto-open search overlay
- Preserve current search functionality when overlay closes
- Handle browser back/forward navigation

Phase 7: Mobile Responsiveness

1. Mobile-Specific Behavior
- On mobile, search overlay takes full screen height
- Ensure touch-friendly close interactions
- Maintain existing mobile navigation patterns

Technical Implementation Details

SearchOverlay Component Structure:

```
interface SearchOverlayProps {
isOpen: boolean
onClose: () => void
initialSearchQuery?: string
initialTagIds?: number[]
}
```

// Features:
// - Portal rendering for proper z-index
// - Backdrop blur and click-to-close
// - Slide-down animation from header
// - Responsive sizing (partial height on desktop, full on mobile)
// - Embedded SearchInterface component

Header Integration:

```
// Add to right side button group:
<Button
variant="ghost"
size="sm"
onClick={() => openSearchOverlay()}
className="h-8 w-8 p-0"
>
<Search className="h-4 w-4" />
</Button>
```

Animation Approach:

- CSS transforms for smooth slide-down effect
- Backdrop with opacity transition
- Search content fades in after slide completes
- Consistent with existing app animation patterns

Benefits

✅ Cleaner Page Layout: Channel page focuses on episodes without search dominating
✅ Modern UX Pattern: Search overlay is a widely-recognized pattern
✅ Preserved Functionality: All existing search features remain unchanged
✅ Better Mobile Experience: Full-screen search on mobile devices
✅ Consistent Design: Follows existing header interaction patterns
✅ Performance: Search components only rendered when needed

Files to Modify

1. /components/features/search/search-overlay.tsx (new)
2. /contexts/search-context.tsx (new)
3. /components/layout/header.tsx (modify)
4. /app/channel/page.tsx (modify)
5. /components/layout/main-layout.tsx (minor - add context provider)

This approach transforms the search from a prominent, always-visible interface into an elegant, on-demand overlay while maintaining all current functionality and improving the overall page aesthetics." />
