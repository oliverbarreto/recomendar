# Fix Login Persistence Issues - Implementation Plan - VERSION 1

## Overview

This plan addresses login persistence problems by implementing refresh token rotation, proactive token refresh, expiration checking, and improved activity detection.

## Solution 2: Implement Refresh Token Rotation

### Objective

Modify the refresh endpoint to return a new refresh token, enabling token rotation for better security and session persistence.

### Backend Changes

**File: `backend/app/presentation/schemas/auth_schemas.py`**

- Add `refresh_token` field to `RefreshTokenResponse` schema (currently missing)
- Make it optional initially for backward compatibility, then required

**File: `backend/app/presentation/api/v1/auth.py`**

- Modify `refresh_token()` endpoint (lines 140-190)
- After verifying refresh token, create a new refresh token using `jwt_service.create_refresh_token()`
- Include the new refresh token in the response
- Preserve `remember_me` claim from original refresh token if present

**File: `backend/app/core/jwt.py`**

- Ensure `create_refresh_token()` method properly handles `remember_me` claims
- Verify that refresh token creation respects extended expiration when `remember_me=True`

### Frontend Changes

**File: `frontend/src/types/index.ts`**

- Update `AuthResponse` interface to include `refresh_token` field (if not already present)
- Add new interface `RefreshTokenResponse` matching backend schema

**File: `frontend/src/contexts/auth-context.tsx`**

- Modify `refreshToken()` function (lines 140-172)
- Update to store new refresh token from response: `TokenStorage.setTokens(data.access_token, data.refresh_token)`
- Handle cases where backend might not return refresh token (backward compatibility)

**File: `frontend/src/lib/api.ts`**

- Modify `performTokenRefresh()` function (lines 72-103)
- Update to store new refresh token: `localStorage.setItem('labcastarr_refresh_token', refreshData.refresh_token)`
- Ensure refresh token is updated in addition to access token

## Solution 3: Refresh Token Before Validation on Initialization

### Objective

Attempt token refresh before validating with `/auth/me` to prevent unnecessary logouts when access token is expired but refresh token is valid.

### Frontend Changes

**File: `frontend/src/contexts/auth-context.tsx`**

- Modify `initializeAuth()` function in `useEffect` hook (lines 181-205)
- Before calling `/auth/me`, check if tokens exist and attempt refresh first
- Only proceed to `/auth/me` if refresh succeeds or if no refresh token exists
- Clear tokens only if both refresh and validation fail
- Add proper error handling to distinguish between refresh failures and validation failures

**Implementation approach:**

1. Check if refresh token exists
2. If exists, attempt refresh
3. If refresh succeeds, proceed to `/auth/me` validation
4. If refresh fails, clear tokens and exit
5. If no refresh token exists, attempt direct validation (for backward compatibility)

## Solution 4: Add Token Expiration Check Utility

### Objective

Check token expiration before making API calls to prevent unnecessary 401 errors and improve user experience.

### Frontend Changes

**File: `frontend/src/contexts/auth-context.tsx`**

- Add static method `isAccessTokenExpired()` to `TokenStorage` class (around line 89)
- Implement JWT payload decoding to check `exp` claim
- Return boolean indicating if token is expired or will expire soon (e.g., within 5 minutes)
- Handle edge cases: missing token, invalid JWT format, missing exp claim

**File: `frontend/src/lib/api.ts`**

- Modify `apiRequest()` function (lines 105-224)
- Before making request, check if access token is expired using new utility
- If expired or expiring soon, trigger refresh proactively
- Only proceed with request after ensuring valid token
- Maintain existing 401 error handling as fallback

**Implementation details:**

- Decode JWT without verification (just read exp claim)
- Consider token expired if current time >= exp - 5 minutes (buffer)
- Use this check before adding Authorization header

## Solution 5: Improve Activity Detection

### Objective

Expand activity detection to capture more user interactions, ensuring tokens refresh more reliably during active use.

### Frontend Changes

**File: `frontend/src/hooks/use-activity-detection.ts`**

- Modify `ACTIVITY_EVENTS` array (lines 14-18)
- Add `'mousedown'` event (captures mouse clicks)
- Add `'click'` event (captures button/link clicks)
- Consider adding `'focus'` event for input fields (optional, may be too noisy)
- Keep existing events: `keypress`, `scroll`, `touchstart`

**File: `frontend/src/contexts/auth-context.tsx`**

- Verify activity detection hook usage (line 175-178)
- Ensure debounce time (5 minutes) is appropriate for new events
- Test that increased event frequency doesn't cause performance issues

## Testing Considerations

1. **Refresh Token Rotation:**

- Test that new refresh token works for subsequent refreshes
- Test backward compatibility if old backend doesn't return refresh token
- Verify refresh token expiration is properly extended with remember_me

2. **Pre-Validation Refresh:**

- Test initialization with expired access token but valid refresh token
- Test initialization with no tokens
- Test initialization with invalid refresh token

3. **Token Expiration Check:**

- Test API calls with expired tokens
- Test API calls with tokens expiring soon
- Test API calls with valid tokens
- Verify proactive refresh doesn't cause infinite loops

4. **Activity Detection:**

- Test that new events trigger refresh appropriately
- Verify debounce prevents excessive refresh calls
- Test performance impact of additional event listeners

## Files to Modify

### Backend

- `backend/app/presentation/schemas/auth_schemas.py`
- `backend/app/presentation/api/v1/auth.py`
- `backend/app/core/jwt.py` (if needed for remember_me handling)

### Frontend

- `frontend/src/contexts/auth-context.tsx`
- `frontend/src/lib/api.ts`
- `frontend/src/hooks/use-activity-detection.ts`
- `frontend/src/types/index.ts`

## Implementation Order

1. Solution 2 (Refresh Token Rotation) - Backend first, then frontend
2. Solution 4 (Token Expiration Check) - Can be done independently
3. Solution 3 (Pre-Validation Refresh) - Depends on Solution 2
4. Solution 5 (Activity Detection) - Independent, can be done anytime
