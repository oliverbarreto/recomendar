# Prompt


> What was the poblem that prevented Safari to function correctly ?
⎿  5-hour limit reached ∙ resets 1am
    /upgrade to increase your usage limit.

> continue

---

## Result

⏺ Based on the extensive troubleshooting we just completed, the problem that prevented Safari from functioning correctly was actually multiple cascading issues related to mixed content security and

API endpoint configuration:

Primary Issues That Broke Safari:

1. Mixed Content Blocking (HTTPS → HTTP)

- Safari was accessing the app via https://labcastarr.oliverbarreto.com
- Frontend was making API calls to http://localhost:8000 (HTTP)
- Safari's strict mixed content policy blocked these insecure requests
- Chrome/Arc were more permissive and allowed the mixed content

2. Missing Trailing Slashes in API Endpoints

- Episodes API calls were going to /v1/episodes instead of /v1/episodes/
- FastAPI was returning 307 Temporary Redirect responses
- Safari handled these redirects differently, causing data loading failures

3. Hardcoded localhost URLs 

Throughout Codebase

- Multiple components had hardcoded http://localhost:8000 references
- Episode retry functionality in episode-grid.tsx
- Audio download URLs in episode-detail.tsx
- Feed URL generation in channel-dashboard.tsx

Technical Root Cause:

The core issue was that Safari enforces Mixed Content Security Policy much more strictly than Chrome-based browsers. When a page is served over HTTPS, Safari blocks any HTTP requests as potentiallyinsecure, while Chrome/Arc would show warnings but still allow the requests.

How We Fixed It:

1. Smart URL Resolution: Implemented dynamic API endpoint detection
2. Environment-Aware Configuration: Used NEXT_PUBLIC_API_URL when available
3. Protocol Detection: Automatically switched to HTTPS API when page is HTTPS
4. Trailing Slash Consistency: Fixed all API endpoint paths to match FastAPI routing
5. Centralized API Management: Eliminated hardcoded URLs throughout the codebase

This is a common issue in web applications where development works locally (HTTP) but production requires HTTPS, and different browsers handle mixed content with varying levels of strictness.

Since this is a retrospective question about completed work, no plan is needed - the issues have already been resolved and Safari now works correctly with the application.
