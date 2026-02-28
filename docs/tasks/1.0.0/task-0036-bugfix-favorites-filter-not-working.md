# Task 0036 - Bugfix Favorites Filter Not Working

## Prompt

The favorites filter is not working in the /channel page. I have favorioed various episodes and when filtering by show favorites only, the filter does not work. I have tested filtering by tag, and the filter works correctly. Analyze the code and fix the bug.
@frontend/src/app/channel/page.tsx


---

## Result

I'll analyze the code to identify why the favorites filter isn't working on the /channel page. Let me examine the relevant components.
Read search-interface.tsx, use-search.ts
Grep "favorites" (in frontend/src, type: tsx)
⎿
1 line of output
Grep "is_favorite" (in frontend/src)
⎿
8 lines of output
Read episode-grid.tsx
Read use-episodes.ts
Read api-client.ts
Grep "favoritesOnly|favorites_only|is_favorited" (in frontend/src/lib)
⎿
4 lines of output
Now let me check the backend API to understand what parameter name is expected for the favorites filter:
Grep "favorites|is_favorite" (in backend/app/presentation/api/v1)
⎿
9 lines of output
Read episodes.py
Grep "def get_episodes|@router.get\("/\"|skip.*limit.*favorites" (in backend/app/presentation/api/v1/episodes.py)
⎿
21 lines of output
Perfect! Now I can see the issue. Let me check the episode service to see if it accepts a favorites parameter:
Read episode_service.py
Grep "async def list_episodes" (in backend/app/application/services/episode_service.py)
⎿
31 lines of output
Perfect! Now I've found the root cause. Let me check the frontend types to confirm:
Read episode.ts
Now I have a complete understanding of the issue. Let me present my findings and the fix plan:
Bug Analysis
I've identified the root cause of the favorites filter not working on the /channel page:
The Problem
Frontend sends favoritesOnly parameter: The search-interface.tsx component receives and manages the favoritesOnly state
But it's never sent to the backend: Looking at episode-grid.tsx, the component receives favoritesOnly but it's NOT passed to the API call
Backend API doesn't support it: The backend endpoint episodes.py list_episodes doesn't have a favorites_only query parameter
Client-side filtering is missing: Unlike tags (which have client-side filtering in episode-grid.tsx), there's no client-side filter for favorites
Why Tags Work But Favorites Don't
Tags: Have client-side filtering implemented in episode-grid.tsx lines 130-142
Favorites: No client-side filtering exists, and the parameter isn't used anywhere
Fix Plan
I'll implement client-side filtering for favorites (similar to how tags work) since:
Episodes already have the is_favorited field in the response
This is consistent with the current tag filtering approach
It doesn't require backend changes
It's the quickest and most maintainable solution
Changes Required
frontend/src/components/features/episodes/episode-grid.tsx - Add favorites filter to the client-side filtering logic
Test the fix to ensure it works correctly
Plan Mode
⎿
User approved the plan
Update Todos

Add client-side favorites filtering to episode-grid.tsx
Edit episode-grid.tsx
⎿
Added 5 lines
123
12345678
Update Todos

Add client-side favorites filtering to episode-grid.tsx
Perfect! I've fixed the favorites filter bug. Here's what was changed:
Fix Summary
File Modified: frontend/src/components/features/episodes/episode-grid.tsx The Problem:
The favoritesOnly parameter was being passed through the component chain but never actually used to filter episodes
Tag filtering worked because it had client-side filtering logic, but favorites filtering was completely missing
The Solution: Added client-side filtering for favorites in the additionalFilteredEpisodes useMemo hook:
// Apply favorites filter - show only favorited episodes (client-side since backend doesn't support this)
if (favoritesOnly) {
  filtered = filtered.filter(episode => episode.is_favorited === true)
}
This follows the same pattern as the existing tag filter and also added favoritesOnly to the dependency array so the filter re-runs when the favorites toggle changes. Testing: The favorites filter should now work correctly on the /channel page. When you toggle "Favorites Only", it will show only episodes where is_favorited === true.
