# Fix Login Persistence for Inactive Users - Implementation Plan - VERSION 2 - GMAIL LIKE SESSION PERSISTENCE

## Overview

This plan implements comprehensive login persistence improvements to achieve Gmail-like session behavior. The primary goal is to allow users to be inactive for hours or days and still remain logged in, matching industry standards like Gmail where users don't need to re-login every hour or even every day.

## Key Problems Being Solved

1. **Inactive users get logged out**: When users close browser and return after hours, expired access token causes immediate logout even though refresh token is valid
2. **No token rotation**: Refresh tokens don't extend their expiration, limiting session lifetime
3. **No proactive refresh**: API calls fail with 401 before attempting refresh
4. **Limited activity detection**: Only captures few user interactions
5. **No window focus handling**: Users switching tabs don't get token refresh

## Solution 2: Implement Refresh Token Rotation

### Objective

Modify the refresh endpoint to return a new refresh token, enabling token rotation. Each refresh extends the refresh token expiration, allowing users to stay logged in for extended periods (weeks/months) with regular activity.

### Backend Changes

**File: `backend/app/presentation/schemas/auth_schemas.py`**

- Add `refresh_token` field to `RefreshTokenResponse` schema (line 30-34)
- Make it optional for backward compatibility: `refresh_token: Optional[str] = Field(None, description="New JWT refresh token for rotation")`
- Update schema documentation

**File: `backend/app/presentation/api/v1/auth.py`**

- Modify `refresh_token()` endpoint (lines 140-190)
- After verifying refresh token, extract claims including `remember_me` if present
- Create new refresh token using `jwt_service.create_refresh_token()` with same claims
- If `remember_me=True`, use extended expiration (90 days) from config
- Include new refresh token in response
- Preserve all original claims (email, is_admin, remember_me)

**File: `backend/app/core/jwt.py`**

- Verify `create_refresh_token()` handles `remember_me` claims correctly (lines 77-102)
- Ensure extended expiration uses `jwt_refresh_token_extended_expire_days` when `remember_me=True`
- Check `create_token_pair()` properly sets remember_me in refresh token claims

### Frontend Changes

**File: `frontend/src/types/index.ts`**

- Add `RefreshTokenResponse` interface (around line 227)
- Fields: `access_token: string`, `refresh_token?: string`, `token_type: string`, `expires_in: number`

**File: `frontend/src/contexts/auth-context.tsx`**

- Modify `refreshToken()` function (lines 140-172)
- Update to store new refresh token: `TokenStorage.setTokens(data.access_token, data.refresh_token || refreshTokenValue)`
- Handle backward compatibility: keep existing refresh token if backend doesn't return new one
- Add logging for token rotation

**File: `frontend/src/lib/api.ts`**

- Modify `performTokenRefresh()` function (lines 72-103)
- Update to store new refresh token: `localStorage.setItem('labcastarr_refresh_token', refreshData.refresh_token || refreshToken)`
- Ensure both tokens are updated

## Solution 3: Refresh Token Before Validation (CRITICAL for Inactive Users)

### Objective

Always attempt token refresh BEFORE validating with `/auth/me` when refresh token exists. This is the critical fix that allows inactive users to return after hours/days and stay logged in.

### Frontend Changes

**File: `frontend/src/contexts/auth-context.tsx`**

- Modify `initializeAuth()` function in `useEffect` hook (lines 181-205)
- **Critical implementation**: Always refresh before validation if refresh token exists
- Flow:

  1. Check if tokens exist → exit early if none
  2. If refresh token exists → attempt refresh FIRST
  3. If refresh succeeds → proceed to `/auth/me` with fresh access token
  4. If refresh fails → clear tokens and exit (refresh token expired/invalid)
  5. If no refresh token → attempt direct validation (backward compatibility)

- Add error handling for different failure scenarios
- Set user state only after successful validation
- Add logging for debugging initialization flow

**Key Code Pattern:**

```typescript
const initializeAuth = async () => {
  if (!TokenStorage.hasValidTokens()) {
    setIsLoading(false)
    return
  }

  const refreshTokenValue = TokenStorage.getRefreshToken()

  // CRITICAL: Refresh before validation
  if (refreshTokenValue) {
    try {
      await refreshToken()
    } catch (refreshError) {
      TokenStorage.clearAll()
      setIsLoading(false)
      return
    }
  }

  // Now validate with fresh access token
  try {
    const backendUser = await authenticatedApiRequest<any>("/auth/me")
    setUser(transformUserData(backendUser))
  } catch (error) {
    TokenStorage.clearAll()
  } finally {
    setIsLoading(false)
  }
}
```

## Solution 4: Add Token Expiration Check Utilities

### Objective

Check token expiration before API calls and during initialization to enable proactive refresh, preventing unnecessary 401 errors.

### Frontend Changes

**File: `frontend/src/contexts/auth-context.tsx`**

- Add `isAccessTokenExpired()` static method to `TokenStorage` class (after line 89)
- Add `isRefreshTokenExpired()` static method to `TokenStorage` class
- Decode JWT payload to read `exp` claim (no verification needed)
- For access token: expired if `currentTime >= exp - 5 minutes` (buffer)
- For refresh token: expired if `currentTime >= exp`
- Handle edge cases: missing token, invalid format, missing exp claim
- Return boolean indicating expiration status

**File: `frontend/src/lib/api.ts`**

- Modify `apiRequest()` function (lines 105-224)
- Before adding Authorization header, check if access token expired
- If expired → trigger `performTokenRefresh()` proactively
- Only proceed with request after ensuring valid token
- Maintain existing 401 error handling as fallback
- Prevent infinite loops: track refresh attempts, limit retries

## Solution 5: Improve Activity Detection

### Objective

Expand activity detection to capture more user interactions, ensuring tokens refresh during active use.

### Frontend Changes

**File: `frontend/src/hooks/use-activity-detection.ts`**

- Modify `ACTIVITY_EVENTS` array (lines 14-18)
- Add `'mousedown'` event (captures mouse clicks)
- Add `'click'` event (captures button/link clicks)
- Keep existing: `keypress`, `scroll`, `touchstart`
- Do NOT add `'mousemove'` (too noisy) or `'focus'` (handled separately)

**File: `frontend/src/contexts/auth-context.tsx`**

- Verify activity detection usage (line 175-178)
- Ensure 5-minute debounce is appropriate
- Test performance impact

## Solution 6: Smart Window Focus Handler (NEW - Critical for Inactive Users)

### Objective

Refresh token when user returns to tab/window after being away, but only if token is expired or expiring soon. Handles users switching tabs or minimizing browser.

### Frontend Changes

**File: `frontend/src/contexts/auth-context.tsx`**

- Add new `useEffect` hook for window focus handling (after line 227)
- Implement smart focus handler:

  1. Only triggers if user logged in and tokens exist
  2. Checks if access token expired using `TokenStorage.isAccessTokenExpired()`
  3. Only refreshes if expired/expiring soon (not on every focus)
  4. Prevents excessive refreshes: minimum 5-minute interval between focus refreshes
  5. Handles errors gracefully (don't log out immediately)

- Track last focus refresh time
- Do NOT show loading spinner (background operation)

**Implementation:**

```typescript
useEffect(() => {
  if (!user) return

  let lastFocusRefresh = 0
  const MIN_FOCUS_REFRESH_INTERVAL = 5 * 60 * 1000

  const handleFocus = async () => {
    const now = Date.now()
    if (now - lastFocusRefresh < MIN_FOCUS_REFRESH_INTERVAL) return

    if (
      !TokenStorage.hasValidTokens() ||
      !TokenStorage.isAccessTokenExpired()
    ) {
      return
    }

    try {
      await refreshToken()
      lastFocusRefresh = now
    } catch (error) {
      console.warn("Focus refresh failed:", error)
    }
  }

  window.addEventListener("focus", handleFocus)
  return () => window.removeEventListener("focus", handleFocus)
}, [user, refreshToken])
```

## Testing Scenarios

### Inactive User Scenarios (Primary Goal)

1. **User inactive 2 hours, closes browser, returns:**

   - Access token expired (60 min), refresh token valid (90 days)
   - Expected: Refresh succeeds → Validation succeeds → User stays logged in ✅

2. **User inactive 5 hours, closes browser, returns:**

   - Same as above → User stays logged in ✅

3. **User inactive 1 day, closes browser, returns:**

   - Refresh token still valid → User stays logged in ✅

4. **User switches tabs, inactive 2 hours, returns to tab:**

   - Window focus handler detects expired token → Refreshes → User stays logged in ✅

5. **User inactive 3 months, closes browser, returns:**

   - Refresh token expired (90 days) → Refresh fails → User redirected to login ✅ (Expected)

### Active User Scenarios

1. **User actively browsing:**

   - Activity detection refreshes every 5 minutes
   - Token rotation extends refresh token expiration
   - User stays logged in seamlessly ✅

2. **User makes rapid API calls:**

   - Expiration check prevents 401 errors
   - Proactive refresh before API calls
   - Smooth experience ✅

## Files to Modify

### Backend

- `backend/app/presentation/schemas/auth_schemas.py` - Add refresh_token to RefreshTokenResponse
- `backend/app/presentation/api/v1/auth.py` - Implement refresh token rotation
- `backend/app/core/jwt.py` - Verify remember_me handling

### Frontend

- `frontend/src/contexts/auth-context.tsx` - Multiple changes: rotation, pre-validation, expiration checks, focus handler
- `frontend/src/lib/api.ts` - Expiration check, refresh token storage
- `frontend/src/hooks/use-activity-detection.ts` - Add more activity events
- `frontend/src/types/index.ts` - Add RefreshTokenResponse interface

## Implementation Order

1. **Solution 2 (Refresh Token Rotation)** - Backend first, then frontend

   - Foundation for extending session lifetime

2. **Solution 4 (Token Expiration Check)** - Independent

   - Provides utilities needed by other solutions

3. **Solution 3 (Pre-Validation Refresh)** - Depends on 2 and 4

   - **CRITICAL** for inactive users

4. **Solution 6 (Window Focus Handler)** - Depends on 2 and 4

   - Handles tab switching scenarios

5. **Solution 5 (Activity Detection)** - Independent

   - Improves active user experience
