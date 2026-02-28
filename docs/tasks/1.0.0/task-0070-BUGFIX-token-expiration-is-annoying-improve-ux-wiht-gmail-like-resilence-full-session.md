# Investigate login process issues

_Exported on 2/12/2025 at 12:29:03 WET from Cursor (2.1.42)_

---

**User**

explore the codebase of the frontend and backend to identify the login process. I am having a terrible user experience since yi practicaly have to login every 5 minutes. Every time i rebuild the docker containers i must login. While testing the same version with same containers for a while, i hae to login several times.

Analyze what the current implementation and the potential problems. There might be something missing

---

**Cursor**

Analyzing the login flow and token management to identify why frequent logins are required. Exploring the frontend and backend authentication implementation.

Reviewing key authentication files to understand token expiration and refresh logic:

Checking the activity detection hook and how token refresh is handled:

Checking JWT secret key configuration and Docker environment setup:

Checking Docker Compose configuration for environment variable handling:

## Analysis: Login persistence issues

### Current implementation

1. Token configuration:

   - Access token: 60 minutes expiration
   - Refresh token: 30 days (standard) or 90 days (with "remember me")
   - Frontend auto-refresh: every 48 minutes (80% of 60 min)
   - Activity-based refresh: every 5 minutes (on user activity)

2. Token storage:
   - Tokens stored in `localStorage` (persists across browser sessions)
   - Keys: `labcastarr_access_token`, `labcastarr_refresh_token`, `labcastarr_user`

### Critical issues identified

#### Issue 1: JWT secret key not persisted across container rebuilds

Problem:

- `JWT_SECRET_KEY` is not explicitly set in `docker-compose.dev.yml`
- Relies on `.env.development` which may be missing or inconsistent
- Default secret: `"your-secret-key-change-in-production"`
- When containers rebuild, if the secret changes, all existing tokens become invalid

Evidence:

```22:27:docker-compose.dev.yml
    env_file:
      - .env.development
    environment:
      - ENVIRONMENT=${ENVIRONMENT:-development}
      - DATABASE_URL=${DATABASE_URL:-sqlite:///./data/labcastarr-dev.db}
      - API_KEY_SECRET=${API_KEY_SECRET:-dev-secret-key-change-in-production}
```

No `JWT_SECRET_KEY` environment variable is set.

#### Issue 2: Token refresh doesn't update refresh token

Problem:

- Refresh endpoint only returns a new access token
- Refresh token is never rotated or extended
- If refresh token expires (30/90 days), user is logged out

Evidence:

```140:190:backend/app/presentation/api/v1/auth.py
async def refresh_token(
    request: RefreshTokenRequest
) -> RefreshTokenResponse:
    """
    Refresh access token using refresh token
    ...
    """
    # Verify refresh token
    jwt_service = get_jwt_service()
    payload = jwt_service.verify_token(request.refresh_token, token_type="refresh")
    ...
    # Create new access token with same claims (using sliding token)
    ...
    return RefreshTokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=jwt_service.access_token_expire_minutes * 60
    )
```

No new refresh token is returned.

#### Issue 3: Initialization doesn't attempt refresh before validation

Problem:

- On app mount, it validates the token with `/auth/me`
- If expired/invalid, it clears tokens immediately
- No attempt to refresh before validation

Evidence:

```180:205:frontend/src/contexts/auth-context.tsx
  // Check for existing auth on mount
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        // Check if we have stored tokens
        if (!TokenStorage.hasValidTokens()) {
          setIsLoading(false)
          return
        }

        // Try to get current user with existing token
        const backendUser = await authenticatedApiRequest<any>('/auth/me')
        const currentUser = transformUserData(backendUser)
        setUser(currentUser)
        TokenStorage.setUser(currentUser)
      } catch (error) {
        console.error('Failed to initialize auth:', error)
        // Clear invalid tokens
        TokenStorage.clearAll()
      } finally {
        setIsLoading(false)
      }
    }

    initializeAuth()
  }, [])
```

If `/auth/me` fails (e.g., expired access token), tokens are cleared without attempting refresh.

#### Issue 4: Activity detection may not trigger frequently enough

Problem:

- Activity detection only listens to: `keypress`, `scroll`, `touchstart`
- If user is inactive or just reading, no refresh happens
- Auto-refresh timer is 48 minutes, leaving only a 12-minute window before expiration

Evidence:

```14:18:frontend/src/hooks/use-activity-detection.ts
const ACTIVITY_EVENTS = [
    'keypress',
    'scroll',
    'touchstart',
] as const
```

#### Issue 5: No token expiration check before API calls

Problem:

- API calls use the stored access token without checking expiration
- If expired, request fails with 401, then refresh is attempted
- This causes unnecessary failed requests

### Recommended solutions

#### Solution 1: Persist JWT secret key across container rebuilds

Add to `docker-compose.dev.yml`:

```yaml
environment:
  - JWT_SECRET_KEY=${JWT_SECRET_KEY:-dev-jwt-secret-key-change-in-production}
```

Or use a Docker volume or external secret management.

#### Solution 2: Implement refresh token rotation

Modify the refresh endpoint to return a new refresh token:

```python
# In backend/app/presentation/api/v1/auth.py
return RefreshTokenResponse(
    access_token=access_token,
    refresh_token=new_refresh_token,  # Add this
    token_type="bearer",
    expires_in=jwt_service.access_token_expire_minutes * 60
)
```

#### Solution 3: Refresh token before validation on initialization

Modify `auth-context.tsx` to attempt refresh before validating:

```typescript
// Try to refresh token first if access token might be expired
if (TokenStorage.hasValidTokens()) {
  try {
    await refreshToken() // Refresh before validation
  } catch (refreshError) {
    // If refresh fails, then clear tokens
    TokenStorage.clearAll()
    setIsLoading(false)
    return
  }
}
```

#### Solution 4: Add token expiration check utility

Create a utility to check token expiration before API calls:

```typescript
static isAccessTokenExpired(): boolean {
  const token = this.getAccessToken()
  if (!token) return true

  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    const exp = payload.exp * 1000 // Convert to milliseconds
    return Date.now() >= exp
  } catch {
    return true
  }
}
```

#### Solution 5: Improve activity detection

Add more activity events or use a heartbeat mechanism:

```typescript
const ACTIVITY_EVENTS = [
  "keypress",
  "scroll",
  "touchstart",
  "mousedown", // Add this
  "click", // Add this
] as const
```

### Priority fixes

1. High: Persist JWT secret key (fixes container rebuild issue)
2. High: Refresh token before validation on initialization (fixes frequent logouts)
3. Medium: Implement refresh token rotation (improves long-term persistence)
4. Medium: Add token expiration check utility (prevents unnecessary 401s)
5. Low: Improve activity detection (better UX)

Should I implement these fixes?

```plaintext
    env_file:
      - .env.development
    environment:
      - ENVIRONMENT=${ENVIRONMENT:-development}
      - DATABASE_URL=${DATABASE_URL:-sqlite:///./data/labcastarr-dev.db}
      - API_KEY_SECRET=${API_KEY_SECRET:-dev-secret-key-change-in-production}
```

```python
async def refresh_token(
    request: RefreshTokenRequest
) -> RefreshTokenResponse:
    """
    Refresh access token using refresh token
    ...
    """
    # Verify refresh token
    jwt_service = get_jwt_service()
    payload = jwt_service.verify_token(request.refresh_token, token_type="refresh")
    ...
    # Create new access token with same claims (using sliding token)
    ...
    return RefreshTokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=jwt_service.access_token_expire_minutes * 60
    )
```

```typescriptreact
  // Check for existing auth on mount
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        // Check if we have stored tokens
        if (!TokenStorage.hasValidTokens()) {
          setIsLoading(false)
          return
        }

        // Try to get current user with existing token
        const backendUser = await authenticatedApiRequest<any>('/auth/me')
        const currentUser = transformUserData(backendUser)
        setUser(currentUser)
        TokenStorage.setUser(currentUser)
      } catch (error) {
        console.error('Failed to initialize auth:', error)
        // Clear invalid tokens
        TokenStorage.clearAll()
      } finally {
        setIsLoading(false)
      }
    }

    initializeAuth()
  }, [])
```

```typescript
const ACTIVITY_EVENTS = ["keypress", "scroll", "touchstart"] as const
```

```yaml
environment:
  - JWT_SECRET_KEY=${JWT_SECRET_KEY:-dev-jwt-secret-key-change-in-production}
```

```python
# In backend/app/presentation/api/v1/auth.py
return RefreshTokenResponse(
    access_token=access_token,
    refresh_token=new_refresh_token,  # Add this
    token_type="bearer",
    expires_in=jwt_service.access_token_expire_minutes * 60
)
```

```typescript
// Try to refresh token first if access token might be expired
if (TokenStorage.hasValidTokens()) {
  try {
    await refreshToken() // Refresh before validation
  } catch (refreshError) {
    // If refresh fails, then clear tokens
    TokenStorage.clearAll()
    setIsLoading(false)
    return
  }
}
```

```typescript
static isAccessTokenExpired(): boolean {
  const token = this.getAccessToken()
  if (!token) return true

  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    const exp = payload.exp * 1000 // Convert to milliseconds
    return Date.now() >= exp
  } catch {
    return true
  }
}
```

```typescript
const ACTIVITY_EVENTS = [
  "keypress",
  "scroll",
  "touchstart",
  "mousedown", // Add this
  "click", // Add this
] as const
```

---

**User**

Generate an implementation plan for solutions 2 to 5 (forget about the solution 1 related to containers). Identify files that will be modified and clear objectives and tasks

---

**Cursor**

Reviewing relevant files to understand the current implementation before drafting the plan.

Creating the implementation plan:

---

**User**

what would be the user experience after we implement these changes ? Describe what are the cases and behavior if we implement your proposed solutions

---

**Cursor**

## User Experience After Implementation

### Current behavior (before fixes)

**Scenario 1: User logs in**

- User enters credentials and clicks "Remember me"
- Tokens stored in localStorage
- Access token expires in 60 minutes
- Refresh token expires in 90 days (with remember me)

**Scenario 2: Normal usage (within 60 minutes)**

- User browses, clicks, scrolls
- Activity detection may trigger refresh every 5 minutes (only on keypress/scroll/touchstart)
- Auto-refresh timer triggers at 48 minutes
- User stays logged in

**Scenario 3: Access token expires (after 60 minutes)**

- Next API call fails with 401
- Frontend attempts refresh
- Refresh succeeds, but refresh token is not rotated
- User continues working

**Scenario 4: User closes browser and returns**

- App initializes
- Checks `/auth/me` with stored access token
- If access token expired → immediate logout (no refresh attempt)
- User must log in again

**Scenario 5: User inactive for 5+ minutes**

- No activity events trigger
- Token may expire without refresh
- User gets logged out on next action

**Scenario 6: Container rebuild**

- JWT secret may change
- All tokens invalid
- User must log in again

---

### After Solution 2: Refresh Token Rotation

**Scenario 1: User logs in**

- Same as before

**Scenario 2: Normal usage with refresh**

- When refresh happens, both access and refresh tokens are updated
- Refresh token expiration extends with each refresh
- Session persists longer

**Scenario 3: Access token expires**

- Refresh succeeds and returns new refresh token
- Refresh token expiration resets (30/90 days from refresh)
- User stays logged in longer

**Scenario 4: User closes browser and returns**

- Still logs out if access token expired (Solution 3 fixes this)

**Scenario 5: Long-term usage**

- With regular refreshes, refresh token keeps extending
- User can stay logged in for extended periods if active

---

### After Solution 3: Pre-Validation Refresh

**Scenario 1: User logs in**

- Same as before

**Scenario 2: User closes browser and returns (access token expired, refresh token valid)**

- App initializes
- Detects tokens exist
- Attempts refresh before validation
- Refresh succeeds → new access token obtained
- Then validates with `/auth/me` → success
- User stays logged in

**Scenario 3: User closes browser and returns (both tokens expired)**

- App initializes
- Attempts refresh → fails (refresh token expired)
- Clears tokens
- User redirected to login

**Scenario 4: User closes browser and returns (no tokens)**

- App initializes
- No tokens found → user sees login page

**Scenario 5: User closes browser and returns (refresh token invalid/corrupted)**

- App initializes
- Attempts refresh → fails
- Clears tokens
- User redirected to login

---

### After Solution 4: Token Expiration Check

**Scenario 1: User logs in**

- Same as before

**Scenario 2: Normal usage (token expiring soon)**

- Before each API call, checks if token expires within 5 minutes
- If expiring soon → proactively refreshes
- Then makes API call with fresh token
- Fewer 401 errors

**Scenario 3: Multiple rapid API calls**

- First call detects expiration → triggers refresh
- Subsequent calls use refreshed token
- No cascading 401 errors

**Scenario 4: User inactive, then makes API call**

- Token expired during inactivity
- Expiration check detects expired token
- Triggers refresh before API call
- If refresh succeeds → API call proceeds
- If refresh fails → tokens cleared, user redirected to login

**Scenario 5: Network issues during refresh**

- Expiration check triggers refresh
- Refresh fails (network error)
- Tokens cleared
- User redirected to login

---

### After Solution 5: Improved Activity Detection

**Scenario 1: User logs in**

- Same as before

**Scenario 2: User actively browsing**

- Clicks buttons/links → `mousedown` and `click` events trigger
- Scrolls → `scroll` event triggers
- Types → `keypress` event triggers
- More frequent activity detection
- Token refreshes every 5 minutes during active use
- User stays logged in during active sessions

**Scenario 3: User reading content (no interaction)**

- Only scroll events trigger
- Still refreshes every 5 minutes while scrolling
- Better than before (previously only keypress/scroll/touchstart)

**Scenario 4: User inactive (no mouse/keyboard/scroll)**

- No activity events
- Relies on auto-refresh timer (48 minutes)
- Token refreshes at 48 minutes if user is still on page

---

### Combined behavior (all solutions together)

**Scenario 1: User logs in with "Remember me"**

- Tokens stored: access (60 min), refresh (90 days)
- User can work normally

**Scenario 2: Active usage session**

- User clicks, scrolls, types
- Activity detection refreshes every 5 minutes
- Each refresh rotates both tokens
- Refresh token expiration extends
- Expiration check prevents 401s
- User stays logged in seamlessly

**Scenario 3: User closes browser, returns next day**

- App initializes
- Access token expired (60 min), refresh token valid (90 days)
- Pre-validation refresh succeeds → new tokens
- User stays logged in
- No login required

**Scenario 4: User closes browser, returns after 2 months**

- App initializes
- Access token expired, refresh token expired (90 days)
- Pre-validation refresh fails
- Tokens cleared
- User redirected to login

**Scenario 5: User inactive for 1 hour, then clicks something**

- Token expired during inactivity
- Click triggers activity detection
- Expiration check detects expired token
- Proactive refresh before API call
- If refresh succeeds → user continues working
- If refresh fails → user redirected to login

**Scenario 6: User makes rapid API calls**

- First call checks expiration → refreshes if needed
- Subsequent calls use fresh token
- No 401 errors
- Smooth experience

**Scenario 7: Network interruption**

- User making API calls
- Network drops temporarily
- Expiration check triggers refresh → fails
- Tokens cleared
- User redirected to login
- On reconnect, user logs in again

**Scenario 8: Container rebuild (JWT secret changes)**

- All tokens invalid
- Refresh fails
- User redirected to login
- User logs in again

---

### Summary of improvements

| Scenario                         | Before                                 | After                                       |
| -------------------------------- | -------------------------------------- | ------------------------------------------- |
| **Normal active usage**          | May get logged out if inactive         | Stays logged in with activity detection     |
| **Return after closing browser** | Logged out if access token expired     | Stays logged in if refresh token valid      |
| **Long-term usage**              | Refresh token expires after 30/90 days | Refresh token extends with each refresh     |
| **API calls with expired token** | 401 error, then refresh                | Proactive refresh, no 401                   |
| **Inactive user returns**        | Logged out                             | Refresh attempted, stays logged in if valid |
| **Container rebuild**            | Logged out                             | Logged out (expected, security requirement) |

### Edge cases handled

1. Expired access token, valid refresh token → refresh succeeds, user stays logged in
2. Both tokens expired → user redirected to login
3. Invalid/corrupted tokens → cleared, user redirected to login
4. Network errors during refresh → tokens cleared, user redirected to login
5. Rapid API calls → proactive refresh prevents cascading failures
6. Token expiring soon → refreshed before expiration

### Remaining limitations

1. Container rebuilds still require re-login (security requirement)
2. Network failures during refresh cause logout (expected)
3. Refresh token expiration (30/90 days) still applies, but extends with activity
4. Browser localStorage cleared → user must log in again

Overall, the experience is smoother with fewer unexpected logouts, better session persistence, and proactive token management.

---

**User**

i want to make sure we improve the case of the user not being active. The case is that we can perfectly stay inactive for a long time, an hour, two, five... It should not ask me to login for hours. What is the standard in this aspect ? For example, i use google gmail and i do not have to re-login every hour, not even during the same day

---

**Cursor**

Analyzing how to handle inactive users and align with industry standards (e.g., Gmail).

## Current Problem with Inactive Users

**Scenario: User inactive for 2 hours**

- User logs in, checks "Remember me" → refresh token valid for 90 days
- User stays on page but inactive (no clicks/scrolls)
- Auto-refresh timer triggers at 48 minutes → access token refreshed
- User closes browser after 2 hours
- User returns → access token expired (60 min), refresh token still valid (90 days)
- Current code: Tries `/auth/me` with expired access token → fails → logs out
- Expected: Should refresh token first, then validate → stays logged in

**Scenario: User inactive for 5 hours**

- Same as above, but refresh token still valid
- Current code: Still logs out because no refresh before validation
- Expected: Should stay logged in

## Industry Standards (Gmail, GitHub, etc.)

**Standard Pattern:**

1. Access tokens: 15-60 minutes (short-lived for security)
2. Refresh tokens: 7-90 days (long-lived for UX)
3. "Remember me": Extends refresh token to 30-90 days
4. Automatic refresh: When user returns, refresh access token using refresh token before validation
5. Inactivity handling: Refresh token persists even during long inactivity periods

**Gmail Behavior:**

- Log in once with "Stay signed in"
- Stay logged in for weeks/months
- Can be inactive for hours/days
- Only logs out if:
  - Refresh token expires (30+ days)
  - User explicitly logs out
  - Security event occurs

## What Needs to Be Fixed

### Critical Fix: Solution 3 (Pre-Validation Refresh)

This is the main fix for inactive users:

**Current Code (lines 181-205):**

```typescript
// Try to get current user with existing token
const backendUser = await authenticatedApiRequest<any>("/auth/me")
// If this fails → logout
```

**Fixed Code:**

```typescript
// Check if we have stored tokens
if (!TokenStorage.hasValidTokens()) {
  setIsLoading(false)
  return
}

// CRITICAL: Refresh token BEFORE validation
try {
  await refreshToken() // This will work if refresh token is valid
} catch (refreshError) {
  // Refresh failed (refresh token expired/invalid)
  TokenStorage.clearAll()
  setIsLoading(false)
  return
}

// Now validate with fresh access token
try {
  const backendUser = await authenticatedApiRequest<any>("/auth/me")
  // Success - user stays logged in
} catch (error) {
  // Even if this fails, we already have fresh token from refresh
  // This shouldn't happen, but handle gracefully
}
```

### Additional Improvements Needed

#### 1. Window Focus Handler (Smart Version)

Add a window focus handler that refreshes when the user returns to the tab, but only if enough time has passed:

```typescript
// Refresh when user returns to tab (but not too aggressively)
useEffect(() => {
  if (!user) return

  let lastFocusRefresh = Date.now()
  const MIN_FOCUS_REFRESH_INTERVAL = 5 * 60 * 1000 // 5 minutes

  const handleFocus = async () => {
    const now = Date.now()
    // Only refresh if enough time has passed since last refresh
    if (now - lastFocusRefresh < MIN_FOCUS_REFRESH_INTERVAL) {
      return
    }

    // Check if token might be expired
    if (TokenStorage.isAccessTokenExpired()) {
      try {
        await refreshToken()
        lastFocusRefresh = now
      } catch (error) {
        // Refresh failed, but don't log out immediately
        // Let the next API call handle it
      }
    }
  }

  window.addEventListener("focus", handleFocus)
  return () => window.removeEventListener("focus", handleFocus)
}, [user])
```

#### 2. Ensure Auto-Refresh Works When Inactive

The current auto-refresh timer (48 minutes) works even when inactive, which is good. Ensure it continues working:

```typescript
// This already works correctly - refreshes every 48 minutes
// regardless of user activity
useEffect(() => {
  if (!user) return
  const refreshInterval = setInterval(async () => {
    try {
      await refreshToken()
    } catch (error) {
      await logout()
    }
  }, 48 * 60 * 1000)
  return () => clearInterval(refreshInterval)
}, [user])
```

#### 3. Refresh Token Expiration Check

Add a check to see if refresh token is expired before attempting refresh:

```typescript
static isRefreshTokenExpired(): boolean {
  const token = this.getRefreshToken()
  if (!token) return true

  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    const exp = payload.exp * 1000
    return Date.now() >= exp
  } catch {
    return true
  }
}
```

## Updated User Experience After All Fixes

### Scenario 1: User logs in with "Remember me"

- Tokens: Access (60 min), Refresh (90 days)
- User stays logged in

### Scenario 2: User inactive for 2 hours (still on page)

- Auto-refresh triggers at 48 minutes → access token refreshed
- User stays logged in
- If user closes browser and returns → refresh before validation → stays logged in

### Scenario 3: User inactive for 5 hours (closes browser)

- User closes browser after 1 hour
- Access token expired, refresh token valid (90 days)
- User returns → refresh before validation → new access token → stays logged in

### Scenario 4: User inactive for 2 days

- Refresh token still valid (90 days)
- User returns → refresh before validation → stays logged in

### Scenario 5: User inactive for 3 months

- Refresh token expired (90 days)
- User returns → refresh fails → redirected to login

### Scenario 6: User switches tabs, returns after 2 hours

- Window focus handler checks token expiration
- If expired → refreshes proactively
- User stays logged in

## Summary: What Makes It Work Like Gmail

1. Long refresh token expiration (90 days with "Remember me")
2. Refresh before validation on initialization (Solution 3)
3. Smart window focus handler (refreshes when returning to tab)
4. Auto-refresh timer (works even when inactive)
5. Token expiration checks (proactive refresh)

With these fixes:

- User can be inactive for hours → stays logged in
- User can close browser and return days later → stays logged in
- User only logs out if refresh token expires (90 days) or explicitly logs out
- Matches Gmail-like behavior

The most critical fix is Solution 3 (refresh before validation), which handles the case where users return after being inactive. The other improvements enhance the experience further.

Should I update the implementation plan to include these additional improvements for inactive users?

```typescript
// Try to get current user with existing token
const backendUser = await authenticatedApiRequest<any>("/auth/me")
// If this fails → logout
```

```typescript
// Check if we have stored tokens
if (!TokenStorage.hasValidTokens()) {
  setIsLoading(false)
  return
}

// CRITICAL: Refresh token BEFORE validation
try {
  await refreshToken() // This will work if refresh token is valid
} catch (refreshError) {
  // Refresh failed (refresh token expired/invalid)
  TokenStorage.clearAll()
  setIsLoading(false)
  return
}

// Now validate with fresh access token
try {
  const backendUser = await authenticatedApiRequest<any>("/auth/me")
  // Success - user stays logged in
} catch (error) {
  // Even if this fails, we already have fresh token from refresh
  // This shouldn't happen, but handle gracefully
}
```

```typescript
// Refresh when user returns to tab (but not too aggressively)
useEffect(() => {
  if (!user) return

  let lastFocusRefresh = Date.now()
  const MIN_FOCUS_REFRESH_INTERVAL = 5 * 60 * 1000 // 5 minutes

  const handleFocus = async () => {
    const now = Date.now()
    // Only refresh if enough time has passed since last refresh
    if (now - lastFocusRefresh < MIN_FOCUS_REFRESH_INTERVAL) {
      return
    }

    // Check if token might be expired
    if (TokenStorage.isAccessTokenExpired()) {
      try {
        await refreshToken()
        lastFocusRefresh = now
      } catch (error) {
        // Refresh failed, but don't log out immediately
        // Let the next API call handle it
      }
    }
  }

  window.addEventListener("focus", handleFocus)
  return () => window.removeEventListener("focus", handleFocus)
}, [user])
```

```typescript
// This already works correctly - refreshes every 48 minutes
// regardless of user activity
useEffect(() => {
  if (!user) return
  const refreshInterval = setInterval(async () => {
    try {
      await refreshToken()
    } catch (error) {
      await logout()
    }
  }, 48 * 60 * 1000)
  return () => clearInterval(refreshInterval)
}, [user])
```

```typescript
static isRefreshTokenExpired(): boolean {
  const token = this.getRefreshToken()
  if (!token) return true

  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    const exp = payload.exp * 1000
    return Date.now() >= exp
  } catch {
    return true
  }
}
```

---

**User**

now generate the plan to implement this solution

---

**Cursor**

Updating the plan to include improvements for inactive users, ensuring Gmail-like session persistence.

Creating a new plan with all improvements:

---

**User**

Implement the plan to improve UX

---

**Cursor**

Implementing the plan, starting with Solution 2 (Refresh Token Rotation) on the backend, then moving to the frontend.

Implementing Solution 2: Refresh Token Rotation, starting with backend changes.

```python
"""
Authentication API request/response schemas
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    """Login request schema"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, description="User password")
    remember_me: bool = Field(default=False, description="Remember login for extended period")


class LoginResponse(BaseModel):
    """Login response schema"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration time in seconds")
    user: "UserProfileResponse" = Field(..., description="User profile information")


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""
    refresh_token: str = Field(..., description="Valid refresh token")


class RefreshTokenResponse(BaseModel):
    """Refresh token response schema"""
    access_token: str = Field(..., description="New JWT access token")
    refresh_token: Optional[str] = Field(None, description="New JWT refresh token for rotation")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration time in seconds")


class LogoutRequest(BaseModel):
    """Logout request schema"""
    refresh_token: Optional[str] = Field(None, description="Refresh token to invalidate")


class UserProfileResponse(BaseModel):
    """User profile response schema"""
    id: int = Field(..., description="User ID")
    name: str = Field(..., description="User full name")
    email: EmailStr = Field(..., description="User email address")
    is_admin: bool = Field(..., description="Whether user has admin privileges")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last profile update timestamp")

    class Config:
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    """Change password request schema"""
    current_password: str = Field(..., min_length=1, description="Current password")
    new_password: str = Field(..., min_length=8, description="New password (minimum 8 characters)")
    confirm_password: str = Field(..., min_length=8, description="Confirmation of new password")

    def validate_passwords_match(self) -> bool:
        """Validate that new password and confirmation match"""
        return self.new_password == self.confirm_password


class UpdateProfileRequest(BaseModel):
    """Update user profile request schema"""
    name: Optional[str] = Field(None, min_length=2, max_length=100, description="User full name")
    email: Optional[EmailStr] = Field(None, description="User email address")


class AuthErrorResponse(BaseModel):
    """Authentication error response schema"""
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Specific error code")


class TokenValidationResponse(BaseModel):
    """Token validation response schema"""
    valid: bool = Field(..., description="Whether token is valid")
    user_id: Optional[int] = Field(None, description="User ID if token is valid")
    expires_at: Optional[datetime] = Field(None, description="Token expiration time")


# Update forward references
LoginResponse.model_rebuild()
```

---

**User**

Implement the plan as specified, it is attached for your reference. Do NOT edit the plan file itself.

To-do's from the plan have already been created. Do not create them again. Mark them as in_progress as you work, starting with the first one. Don't stop until you have completed all the to-dos.

---

**Cursor**

Continuing implementation. Updating the refresh token endpoint to return a new refresh token.

Updating the refresh token endpoint to create and return a new refresh token:

```python
"""
Authentication API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.infrastructure.database.connection import get_async_db
from app.infrastructure.repositories.user_repository import UserRepositoryImpl
from app.core.jwt import get_jwt_service, verify_password, validate_password_strength
from app.application.services.event_service import EventService
from app.domain.entities.event import EventSeverity
from app.presentation.schemas.auth_schemas import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    LogoutRequest,
    UserProfileResponse,
    ChangePasswordRequest,
    UpdateProfileRequest,
    AuthErrorResponse,
    TokenValidationResponse
)
from app.core.auth import get_current_user_jwt

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/login",
    response_model=LoginResponse,
    responses={
        401: {"model": AuthErrorResponse, "description": "Invalid credentials"},
        422: {"model": AuthErrorResponse, "description": "Validation error"}
    }
)
async def login(
    credentials: LoginRequest,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_async_db)]
) -> LoginResponse:
    """
    Authenticate user and return JWT tokens

    Args:
        credentials: User login credentials
        session: Database session

    Returns:
        JWT tokens and user profile

    Raises:
        HTTPException: If authentication fails
    """
    user_repo = UserRepositoryImpl(session)

    # Find user by email
    user = await user_repo.find_by_email(credentials.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Verify password
    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Create token pair
    additional_claims = {
        "email": user.email,
        "is_admin": user.is_admin
    }

    # Extend refresh token expiration for "remember me"
    if credentials.remember_me:
        additional_claims["remember_me"] = True

    jwt_service = get_jwt_service()
    tokens = jwt_service.create_token_pair(user.id, additional_claims, remember_me=credentials.remember_me)

    # Log successful login event
    try:
        event_service = EventService(session)

        # Get client information
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        await event_service.log_user_action(
            channel_id=1,  # Default channel for now
            user_id=user.id,
            action="login",
            resource_type="auth",
            resource_id=None,
            message=f"User {user.email} logged in successfully",
            details={
                "remember_me": credentials.remember_me,
                "user_email": user.email,
                "is_admin": user.is_admin,
                "token_type": tokens["token_type"]
            },
            severity=EventSeverity.INFO,
            ip_address=client_ip,
            user_agent=user_agent
        )
    except Exception as e:
        # Don't fail login if event logging fails
        pass

    # Return response
    return LoginResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        expires_in=tokens["expires_in"],
        user=UserProfileResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            is_admin=user.is_admin,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    )


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    responses={
        401: {"model": AuthErrorResponse, "description": "Invalid refresh token"},
        422: {"model": AuthErrorResponse, "description": "Validation error"}
    }
)
async def refresh_token(
    request: RefreshTokenRequest
) -> RefreshTokenResponse:
    """
    Refresh access token using refresh token

    Args:
        request: Refresh token request

    Returns:
        New access token

    Raises:
        HTTPException: If refresh token is invalid
    """
    # Verify refresh token
    jwt_service = get_jwt_service()
    payload = jwt_service.verify_token(request.refresh_token, token_type="refresh")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    # Extract claims from refresh token for token rotation
    additional_claims = {
        "email": payload.get("email"),
        "is_admin": payload.get("is_admin", False)
    }

    # Preserve remember_me claim if present
    remember_me = payload.get("remember_me", False)
    if remember_me:
        additional_claims["remember_me"] = True

    from datetime import datetime, timezone, timedelta
    from app.core.config import settings

    # Create sliding access token for better UX
    access_token = jwt_service.create_sliding_token({
        "sub": str(user_id),  # JWT 'sub' claim must be a string
        "jti": f"{user_id}_{datetime.now(timezone.utc).timestamp()}",
        **additional_claims
    })

    # Create new refresh token with same claims (token rotation)
    # This extends the refresh token expiration with each refresh
    base_claims = {
        "sub": str(user_id),
        **additional_claims
    }

    # Use extended expiration if remember_me is True
    if remember_me:
        refresh_expire_delta = timedelta(days=settings.jwt_refresh_token_extended_expire_days)
        new_refresh_token = jwt_service.create_refresh_token(base_claims, expires_delta=refresh_expire_delta)
    else:
        new_refresh_token = jwt_service.create_refresh_token(base_claims)

    return RefreshTokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=jwt_service.access_token_expire_minutes * 60
    )


@router.post(
    "/refresh-sliding",
    response_model=RefreshTokenResponse,
    responses={
        401: {"model": AuthErrorResponse, "description": "Invalid or non-sliding token"},
        422: {"model": AuthErrorResponse, "description": "Validation error"}
    }
)
async def refresh_sliding_token(
    current_user: Annotated[dict, Depends(get_current_user_jwt)]
) -> RefreshTokenResponse:
    """
    Refresh sliding token based on activity

    This endpoint extends the token expiration for active users,
    providing seamless session continuation without re-authentication.

    Args:
        current_user: Current authenticated user (validates existing token)

    Returns:
        New access token with extended expiration

    Raises:
        HTTPException: If token is invalid or not a sliding token
    """
    jwt_service = get_jwt_service()

    # Get the current token from the request
    current_token = current_user.get("token")
    if not current_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No token provided"
        )

    # Refresh the sliding token
    new_token = jwt_service.refresh_sliding_token(current_token)
    if not new_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is not a sliding token or is invalid"
        )

    return RefreshTokenResponse(
        access_token=new_token,
        token_type="bearer",
        expires_in=jwt_service.access_token_expire_minutes * 60
    )


@router.post(
    "/logout",
    responses={
        200: {"description": "Successfully logged out"},
        401: {"model": AuthErrorResponse, "description": "Invalid token"}
    }
)
async def logout(
    logout_request: LogoutRequest,
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user_jwt)],
    session: Annotated[AsyncSession, Depends(get_async_db)]
) -> dict:
    """
    Logout user by blacklisting tokens

    Args:
        request: Logout request with optional refresh token
        current_user: Current authenticated user

    Returns:
        Success message
    """
    # The access token is automatically blacklisted by the dependency
    success_count = 1

    # Also blacklist refresh token if provided
    if logout_request.refresh_token:
        jwt_service = get_jwt_service()
        if jwt_service.blacklist_token(logout_request.refresh_token):
            success_count += 1

    # Log successful logout event
    try:
        event_service = EventService(session)

        # Get client information
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        await event_service.log_user_action(
            channel_id=1,  # Default channel for now
            user_id=current_user["user_id"],
            action="logout",
            resource_type="auth",
            resource_id=None,
            message=f"User {current_user.get('email', 'unknown')} logged out successfully",
            details={
                "tokens_invalidated": success_count,
                "user_email": current_user.get("email"),
                "is_admin": current_user.get("is_admin", False)
            },
            severity=EventSeverity.INFO,
            ip_address=client_ip,
            user_agent=user_agent
        )
    except Exception as e:
        # Don't fail logout if event logging fails
        pass

    return {
        "message": "Successfully logged out",
        "tokens_invalidated": success_count
    }


@router.get(
    "/me",
    response_model=UserProfileResponse,
    responses={
        401: {"model": AuthErrorResponse, "description": "Authentication required"}
    }
)
async def get_current_user_profile(
    current_user: Annotated[dict, Depends(get_current_user_jwt)],
    session: Annotated[AsyncSession, Depends(get_async_db)]
) -> UserProfileResponse:
    """
    Get current user profile

    Args:
        current_user: Current authenticated user
        session: Database session

    Returns:
        User profile information
    """
    user_repo = UserRepositoryImpl(session)
    user = await user_repo.get_by_id(current_user["user_id"])

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserProfileResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        is_admin=user.is_admin,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@router.post(
    "/validate-token",
    response_model=TokenValidationResponse,
    responses={
        200: {"description": "Token validation result"}
    }
)
async def validate_token(
    token: str
) -> TokenValidationResponse:
    """
    Validate JWT token (utility endpoint)

    Args:
        token: JWT token to validate

    Returns:
        Token validation result
    """
    jwt_service = get_jwt_service()
    payload = jwt_service.verify_token(token)

    if payload:
        from datetime import datetime, timezone
        expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

        return TokenValidationResponse(
            valid=True,
            user_id=payload.get("sub"),
            expires_at=expires_at
        )
    else:
        return TokenValidationResponse(
            valid=False,
            user_id=None,
            expires_at=None
        )


@router.get(
    "/debug-jwt",
    responses={
        200: {"description": "JWT service debug information"}
    }
)
async def debug_jwt_service() -> dict:
    """
    Debug endpoint to verify JWT service configuration
    """
    import hashlib
    from datetime import datetime, timezone
    jwt_service = get_jwt_service()

    # Get secret key hash for debugging
    secret_hash = hashlib.md5(jwt_service.secret_key.encode()).hexdigest()[:10]
    instance_id = hex(id(jwt_service))

    return {
        "instance_id": instance_id,
        "secret_key_hash": secret_hash,
        "secret_key_length": len(jwt_service.secret_key),
        "algorithm": jwt_service.algorithm,
        "access_token_expire_minutes": jwt_service.access_token_expire_minutes,
        "refresh_token_expire_days": jwt_service.refresh_token_expire_days,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
```

Moving to frontend changes. Adding token expiration check utilities to TokenStorage:

Adding expiration check methods to TokenStorage:

```typescriptreact
'use client'

import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react'
import { User, LoginRequest } from '@/types'
import { authApi } from '@/lib/api'
import { getApiBaseUrl } from '@/lib/api-url'
import { useActivityDetection } from '@/hooks/use-activity-detection'

// Transform backend user data (snake_case) to frontend format (camelCase)
function transformUserData(backendUser: any): User {
  return {
    id: backendUser.id,
    name: backendUser.name,
    email: backendUser.email,
    isAdmin: backendUser.is_admin,
    createdAt: backendUser.created_at,
    updatedAt: backendUser.updated_at
  }
}

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isRefreshing: boolean
  isAuthenticated: boolean
  login: (credentials: LoginRequest) => Promise<void>
  logout: () => Promise<void>
  refreshToken: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

// Token storage utilities
const TOKEN_KEYS = {
  ACCESS_TOKEN: 'labcastarr_access_token',
  REFRESH_TOKEN: 'labcastarr_refresh_token',
  USER: 'labcastarr_user'
}

class TokenStorage {
  static setTokens(accessToken: string, refreshToken: string) {
    if (typeof window !== 'undefined') {
      localStorage.setItem(TOKEN_KEYS.ACCESS_TOKEN, accessToken)
      localStorage.setItem(TOKEN_KEYS.REFRESH_TOKEN, refreshToken)
    }
  }

  static getAccessToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem(TOKEN_KEYS.ACCESS_TOKEN)
    }
    return null
  }

  static getRefreshToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem(TOKEN_KEYS.REFRESH_TOKEN)
    }
    return null
  }

  static setUser(user: User) {
    if (typeof window !== 'undefined') {
      localStorage.setItem(TOKEN_KEYS.USER, JSON.stringify(user))
    }
  }

  static getUser(): User | null {
    if (typeof window !== 'undefined') {
      const userData = localStorage.getItem(TOKEN_KEYS.USER)
      return userData ? JSON.parse(userData) : null
    }
    return null
  }

  static clearAll() {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(TOKEN_KEYS.ACCESS_TOKEN)
      localStorage.removeItem(TOKEN_KEYS.REFRESH_TOKEN)
      localStorage.removeItem(TOKEN_KEYS.USER)
    }
  }

  static hasValidTokens(): boolean {
    const accessToken = this.getAccessToken()
    const refreshToken = this.getRefreshToken()
    return !!(accessToken && refreshToken)
  }

  static isAccessTokenExpired(): boolean {
    const token = this.getAccessToken()
    if (!token) return true

    try {
      // Decode JWT payload without verification (just read exp claim)
      const payload = JSON.parse(atob(token.split('.')[1]))
      const exp = payload.exp * 1000 // Convert to milliseconds
      const bufferMs = 5 * 60 * 1000 // 5 minutes buffer
      return Date.now() >= (exp - bufferMs)
    } catch {
      return true // If we can't parse, consider expired
    }
  }

  static isRefreshTokenExpired(): boolean {
    const token = this.getRefreshToken()
    if (!token) return true

    try {
      // Decode JWT payload without verification (just read exp claim)
      const payload = JSON.parse(atob(token.split('.')[1]))
      const exp = payload.exp * 1000 // Convert to milliseconds
      return Date.now() >= exp
    } catch {
      return true // If we can't parse, consider expired
    }
  }
}

// Custom API request function that includes JWT token
async function authenticatedApiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const accessToken = TokenStorage.getAccessToken()

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
    ...options.headers,
  }

  // Add Authorization header if we have an access token
  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`
  }

  const API_BASE_URL = getApiBaseUrl()
  const response = await fetch(`${API_BASE_URL}/v1${endpoint}`, {
    ...options,
    headers,
    credentials: 'same-origin',
  })

  if (!response.ok) {
    let errorData
    try {
      errorData = await response.json()
    } catch {
      errorData = { message: `HTTP ${response.status}: ${response.statusText}` }
    }
    throw new Error(errorData.message || `HTTP error! status: ${response.status}`)
  }

  const contentType = response.headers.get('content-type')
  if (contentType && contentType.includes('application/json')) {
    return response.json()
  }

  return response.text() as unknown as T
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)

  // Memoized refresh function for activity detection
  const refreshToken = useCallback(async () => {
    try {
      setIsRefreshing(true)
      const refreshTokenValue = TokenStorage.getRefreshToken()

      if (!refreshTokenValue) {
        throw new Error('No refresh token available')
      }

      const response = await fetch(`${getApiBaseUrl()}/v1/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
        },
        body: JSON.stringify({ refresh_token: refreshTokenValue }),
      })

      if (!response.ok) {
        throw new Error('Token refresh failed')
      }

      const data = await response.json()

      // Update stored access token
      TokenStorage.setTokens(data.access_token, refreshTokenValue)
    } catch (error) {
      console.error('Token refresh error:', error)
      throw error
    } finally {
      setIsRefreshing(false)
    }
  }, [])

  // Activity-based token refresh (every 5 minutes of activity)
  useActivityDetection(
    user ? refreshToken : undefined,
    5 * 60 * 1000 // Refresh on activity every 5 minutes
  )

  // Check for existing auth on mount
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        // Check if we have stored tokens
        if (!TokenStorage.hasValidTokens()) {
          setIsLoading(false)
          return
        }

        // Try to get current user with existing token
        const backendUser = await authenticatedApiRequest<any>('/auth/me')
        const currentUser = transformUserData(backendUser)
        setUser(currentUser)
        TokenStorage.setUser(currentUser)
      } catch (error) {
        console.error('Failed to initialize auth:', error)
        // Clear invalid tokens
        TokenStorage.clearAll()
      } finally {
        setIsLoading(false)
      }
    }

    initializeAuth()
  }, [])

  // Auto-refresh token functionality
  // Refresh at 80% of token lifetime (60 min * 0.8 = 48 min)
  useEffect(() => {
    if (!user) return

    const TOKEN_LIFETIME_MINUTES = 60 // Should match backend jwt_access_token_expire_minutes
    const REFRESH_PERCENTAGE = 0.8 // Refresh at 80% of token lifetime
    const refreshIntervalMs = TOKEN_LIFETIME_MINUTES * REFRESH_PERCENTAGE * 60 * 1000

    const refreshInterval = setInterval(async () => {
      try {
        await refreshToken()
      } catch (error) {
        console.error('Auto-refresh failed:', error)
        // If refresh fails, log out the user
        await logout()
      }
    }, refreshIntervalMs) // Refresh every 48 minutes (access token expires in 60)

    return () => clearInterval(refreshInterval)
  }, [user])

  // REMOVED: Window focus refresh was too aggressive
  // This was triggering refreshes on every click between DevTools and page,
  // causing state loss and poor UX. The auto-refresh timer (every 48 min) is sufficient.
  //
  // useEffect(() => {
  //   const handleFocus = async () => {
  //     if (user && TokenStorage.hasValidTokens()) {
  //       try {
  //         await refreshToken()
  //       } catch (error) {
  //         console.error('Focus refresh failed:', error)
  //         await logout()
  //       }
  //     }
  //   }
  //
  //   window.addEventListener('focus', handleFocus)
  //   return () => window.removeEventListener('focus', handleFocus)
  // }, [user])

  const login = async (credentials: LoginRequest) => {
    try {
      setIsLoading(true)

      // Call backend login endpoint directly
      const apiUrl = getApiBaseUrl()
      console.log('Login API URL:', apiUrl) // Debug logging for Safari troubleshooting

      const response = await fetch(`${apiUrl}/v1/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
        },
        body: JSON.stringify(credentials),
      })

      if (!response.ok) {
        const errorData = await response.json()

        // Handle different error formats
        let errorMessage = 'Login failed'
        if (typeof errorData.detail === 'string') {
          errorMessage = errorData.detail
        } else if (Array.isArray(errorData.detail)) {
          // Handle FastAPI validation errors (array format)
          errorMessage = errorData.detail.map((err: any) => err.msg).join(', ')
        } else if (errorData.message) {
          errorMessage = errorData.message
        }

        throw new Error(errorMessage)
      }

      const data = await response.json()

      // Store tokens and user data
      TokenStorage.setTokens(data.access_token, data.refresh_token)
      const transformedUser = transformUserData(data.user)
      TokenStorage.setUser(transformedUser)
      setUser(transformedUser)
    } catch (error) {
      console.error('Login error:', error)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async () => {
    try {
      const refreshTokenValue = TokenStorage.getRefreshToken()

      if (refreshTokenValue) {
        // Call backend logout endpoint
        await authenticatedApiRequest('/auth/logout', {
          method: 'POST',
          body: JSON.stringify({ refresh_token: refreshTokenValue }),
        })
      }
    } catch (error) {
      console.error('Logout error:', error)
      // Continue with logout even if backend call fails
    } finally {
      // Clear local storage and state
      TokenStorage.clearAll()
      setUser(null)
    }
  }

  const value: AuthContextType = {
    user,
    isLoading,
    isRefreshing,
    isAuthenticated: !!user,
    login,
    logout,
    refreshToken,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

// Hook to get the current access token
export function useAccessToken() {
  return TokenStorage.getAccessToken()
}

// Export token storage for use in API client
export { TokenStorage, authenticatedApiRequest }
```

Adding the RefreshTokenResponse interface:

```typescript
/**
 * LabCastARR Frontend Type Definitions
 */

// API Response types
export interface ApiResponse<T> {
  data: T
  message?: string
  success: boolean
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

// User types
export interface User {
  id: number
  name: string
  email: string
  isAdmin: boolean
  createdAt: string
  updatedAt: string
}

// Channel types
export interface Channel {
  id: number
  user_id: number
  name: string
  description: string
  website_url: string // Now required
  image_url?: string
  category: string
  language: string
  explicit_content: boolean
  author_name: string
  author_email: string
  owner_name: string
  owner_email: string
  feed_url: string
  created_at: string
  updated_at: string
}

export interface ChannelCreateRequest {
  user_id: number
  name: string
  description: string
  website_url: string // Now required
  author_name?: string
  author_email?: string
}

export interface ChannelUpdateRequest {
  name?: string
  description?: string
  website_url?: string
  image_url?: string
  category?: string
  language?: string
  explicit_content?: boolean
  author_name?: string
  author_email?: string
  owner_name?: string
  owner_email?: string
}

export interface ChannelStatistics {
  channel_id: number
  channel_name: string
  total_episodes: number
  published_episodes: number
  draft_episodes: number
  processing_episodes: number
  total_duration_seconds: number
  total_size_bytes: number
  unique_youtube_channels: number
  feed_validation_score?: number
  feed_last_updated?: string
  latest_episode?: {
    title: string
    publication_date: string
    duration?: number
  }
  created_at: string
  updated_at: string
}

// RSS Feed types
export interface FeedValidationResponse {
  channel_id: number
  is_valid: boolean
  score: number
  errors: string[]
  warnings: string[]
  recommendations: string[]
  validation_details: {
    total_episodes: number
    channel_complete: boolean
    itunes_complete: boolean
    episodes_valid: boolean
  }
  validated_at: string
}

export interface FeedInfoResponse {
  channel_id: number
  channel_name: string
  feed_url: string
  episode_count: number
  last_updated?: string
  validation_score?: number
  latest_episode_title?: string
  latest_episode_date?: string
}

// Episode types
export enum EpisodeStatus {
  PENDING = "pending",
  PROCESSING = "processing",
  COMPLETED = "completed",
  FAILED = "failed",
}

export interface Episode {
  id: number
  channel_id: number
  video_id: string | null // Optional for uploaded episodes
  title: string
  description: string
  publication_date: string
  audio_file_path: string | null
  video_url: string
  thumbnail_url: string | null
  duration_seconds: number | null
  keywords: string[]
  status: EpisodeStatus
  retry_count: number
  download_date: string | null
  created_at: string
  updated_at: string
  tags: Array<{
    id: number
    name: string
    color: string
    usage_count: number
    is_system_tag: boolean
    created_at: string
    updated_at: string
  }>

  // YouTube channel information
  youtube_channel: string | null
  youtube_channel_id: string | null
  youtube_channel_url: string | null

  // User preferences
  is_favorited: boolean

  // New fields from enhancement
  media_file_size?: number

  // Episode numbering
  episode_number?: number
}

// Tag types
export interface Tag {
  id: number
  channel_id: number
  name: string
  color: string
  usage_count?: number
  is_system_tag?: boolean
  created_at: string
  updated_at: string
}

// Event types
export enum EventType {
  EPISODE_CREATED = "episode_created",
  EPISODE_UPDATED = "episode_updated",
  EPISODE_DELETED = "episode_deleted",
  DOWNLOAD_STARTED = "download_started",
  DOWNLOAD_COMPLETED = "download_completed",
  DOWNLOAD_FAILED = "download_failed",
  RSS_GENERATED = "rss_generated",
  CHANNEL_UPDATED = "channel_updated",
}

export enum EventStatus {
  REQUESTED = "requested",
  PROCESSING = "processing",
  COMPLETED = "completed",
  FAILED = "failed",
}

export interface Event {
  id: number
  channelId: number
  episodeId?: number
  eventType: EventType
  message: string
  eventData: Record<string, unknown>
  status: EventStatus
  createdAt: string
}

// Authentication types
export interface LoginRequest {
  email: string
  password: string
  remember_me?: boolean // Optional: Extend session duration to 90 days when true
}

export interface RegisterRequest {
  name: string
  email: string
  password: string
}

export interface AuthResponse {
  user: User
  token?: string
}

export interface RefreshTokenResponse {
  access_token: string
  refresh_token?: string
  token_type: string
  expires_in: number
}

// Form types
export interface CreateEpisodeRequest {
  channel_id: number
  video_url: string
  tags?: string[]
}

export interface UpdateEpisodeRequest {
  title?: string
  description?: string
  keywords?: string[]
  tags?: number[]
}

export interface ChannelSettingsRequest {
  name?: string
  description?: string
  websiteUrl?: string
  category?: string
  language?: string
  explicitContent?: boolean
  authorName?: string
  authorEmail?: string
  ownerName?: string
  ownerEmail?: string
}

export interface CreateTagRequest {
  name: string
  color: string
}

export interface UpdateTagRequest {
  name?: string
  color?: string
}

export interface UserProfileRequest {
  name?: string
  email?: string
}

export interface PasswordChangeRequest {
  current_password: string
  new_password: string
  confirm_password: string
}

// Search and filter types
export interface EpisodeSearchParams {
  query?: string
  status?: EpisodeStatus
  tags?: number[]
  startDate?: string
  endDate?: string
  page?: number
  pageSize?: number
}

export interface SearchFilters {
  channel_id?: number
  tags?: number[]
  status?: EpisodeStatus
  start_date?: string
  end_date?: string
  min_duration?: number
  max_duration?: number
  keywords?: string[]
}

export interface SearchRequest {
  query: string
  channel_id: number
  filters?: SearchFilters
  sort_by?: "relevance" | "date" | "title" | "duration"
  sort_order?: "asc" | "desc"
  limit?: number
  offset?: number
}

export interface SearchResult {
  id: number
  channel_id: number
  title: string
  description: string
  video_url: string
  thumbnail_url: string
  duration_seconds?: number
  publication_date: string
  status: EpisodeStatus
  tags?: Tag[]
  relevance_score?: number
  matched_fields?: string[]
  highlights?: Record<string, string>
  // Additional fields to match Episode interface for audio context
  video_id?: string
  audio_file_path: string | null
  keywords?: string[]
  retry_count?: number
  download_date?: string
  created_at?: string
  updated_at?: string
  media_file_size?: number
  youtube_channel?: string
  youtube_channel_id?: string
  youtube_channel_url?: string
  is_favorited?: boolean
  // Episode numbering
  episode_number?: number
}

export interface SearchResponse {
  results: SearchResult[]
  total_count: number
  search_time_ms: number
  query: string
  filters_applied: SearchFilters
  suggestions?: string[]
  facets?: Record<string, Array<{ value: string | number; count: number }>>
}

export interface SearchSuggestion {
  query: string
  type: "recent" | "popular" | "completion"
  count?: number
}

export interface TagSuggestion {
  id: number
  name: string
  color: string
  usage_count: number
  match_score: number
}

export interface TagSuggestionsResponse {
  suggestions: TagSuggestion[]
  query: string
  total_count: number
}

export interface EventFilterParams {
  eventType?: EventType
  status?: EventStatus
  startDate?: string
  endDate?: string
  page?: number
  pageSize?: number
}

// Error types
export interface ApiError {
  status: number
  message: string
  details?: string
  timestamp: string
}

// UI State types
export interface LoadingState {
  [key: string]: boolean
}

export interface Toast {
  id: string
  type: "success" | "error" | "warning" | "info"
  message: string
  duration?: number
}

// Health check types
export interface HealthResponse {
  status: string
  service?: string
  version?: string
  timestamp: string
  database?: string
  error?: string
}

export interface DetailedHealthResponse extends HealthResponse {
  components: {
    database?: {
      status: string
      type?: string
      error?: string
    }
    filesystem?: {
      status: string
      media_path: string
      feeds_path: string
      media_accessible: boolean
      feeds_accessible: boolean
      error?: string
    }
  }
}

// Follow Channel Feature Types
export enum SubscriptionCheckFrequency {
  DAILY = "daily",
  WEEKLY = "weekly",
}

export enum YouTubeVideoState {
  PENDING_REVIEW = "pending_review",
  REVIEWED = "reviewed",
  QUEUED = "queued",
  DOWNLOADING = "downloading",
  EPISODE_CREATED = "episode_created",
  DISCARDED = "discarded",
}

export interface FollowedChannel {
  id: number
  user_id: number
  youtube_channel_id: string
  youtube_channel_name: string
  youtube_channel_url: string
  thumbnail_url?: string
  auto_approve: boolean
  auto_approve_channel_id?: number
  last_checked?: string
  created_at: string
  updated_at: string
}

export interface FollowedChannelCreateRequest {
  channel_url: string
  auto_approve?: boolean
  auto_approve_channel_id?: number
}

export interface FollowedChannelUpdateRequest {
  auto_approve?: boolean
  auto_approve_channel_id?: number
}

export interface FollowedChannelWithStats extends FollowedChannel {
  pending_videos_count?: number
  reviewed_videos_count?: number
  episode_created_count?: number
  total_videos_count?: number
}

export interface BackfillRequest {
  year?: number
  max_videos?: number
}

export interface BackfillResponse {
  status: string
  task_id: string
  followed_channel_id: number
  year?: number
  max_videos: number
  message: string
}

export interface YouTubeVideo {
  id: number
  video_id: string
  followed_channel_id: number
  title: string
  description?: string
  url: string
  thumbnail_url?: string
  publish_date?: string
  duration?: number
  view_count?: number
  like_count?: number
  comment_count?: number
  state: YouTubeVideoState
  episode_id?: number
  reviewed_at?: string
  created_at: string
  updated_at: string
}

export interface YouTubeVideoListFilters {
  state?: YouTubeVideoState
  followed_channel_id?: number
  search?: string
  publish_year?: number
  skip?: number
  limit?: number
}

export interface CreateEpisodeFromVideoRequest {
  channel_id: number
}

export type BulkActionType = "review" | "discard" | "create_episode"

export interface BulkActionRequest {
  video_ids: number[]
  action: BulkActionType
  channel_id?: number
}

export interface BulkActionResult {
  video_id: number
  success: boolean
  error?: string
  task_id?: string
}

export interface BulkActionResponse {
  action: string
  total: number
  successful: number
  failed: number
  results: BulkActionResult[]
}

export type TaskStatus =
  | "PENDING"
  | "STARTED"
  | "PROGRESS"
  | "SUCCESS"
  | "FAILURE"
  | "RETRY"

export interface CeleryTaskStatus {
  id: number
  task_id: string
  task_name: string
  status: TaskStatus
  progress: number
  current_step?: string
  result_json?: string
  error_message?: string
  followed_channel_id?: number
  youtube_video_id?: number
  created_at: string
  updated_at: string
  started_at?: string
  completed_at?: string
}

export interface CreateEpisodeFromVideoResponse {
  status: string
  task_id: string
  youtube_video_id: number
  channel_id: number
  episode_id?: number
  message: string
}

export interface YouTubeVideoStats {
  pending_review: number
  reviewed: number
  queued: number
  downloading: number
  episode_created: number
  discarded: number
  total: number
}

export interface UserSettings {
  id: number
  user_id: number
  subscription_check_frequency: SubscriptionCheckFrequency
  preferred_check_hour: number
  preferred_check_minute: number
  timezone: string
  created_at: string
  updated_at: string
}

export interface UserSettingsUpdateRequest {
  subscription_check_frequency?: SubscriptionCheckFrequency
  preferred_check_hour?: number
  preferred_check_minute?: number
  timezone?: string
}

// Notification types
export enum NotificationType {
  VIDEO_DISCOVERED = "video_discovered",
  EPISODE_CREATED = "episode_created",
  CHANNEL_SEARCH_STARTED = "channel_search_started",
  CHANNEL_SEARCH_COMPLETED = "channel_search_completed",
  CHANNEL_SEARCH_ERROR = "channel_search_error",
}

export interface Notification {
  id: number
  userId: number
  type: NotificationType
  title: string
  message: string
  dataJson?: Record<string, any>
  read: boolean
  executedBy: "user" | "system"
  createdAt: string
  updatedAt: string
}

export interface NotificationListResponse {
  notifications: Notification[]
  total: number
  skip: number
  limit: number
  unread_count: number
}

export interface UnreadCountResponse {
  unread_count: number
}

export interface DeleteNotificationResponse {
  success: boolean
  notification_id: number
}

export interface DeleteAllNotificationsResponse {
  success: boolean
  deleted_count: number
}
```

Updating the refreshToken function to handle the new refresh token:

```typescriptreact
'use client'

import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react'
import { User, LoginRequest } from '@/types'
import { authApi } from '@/lib/api'
import { getApiBaseUrl } from '@/lib/api-url'
import { useActivityDetection } from '@/hooks/use-activity-detection'

// Transform backend user data (snake_case) to frontend format (camelCase)
function transformUserData(backendUser: any): User {
  return {
    id: backendUser.id,
    name: backendUser.name,
    email: backendUser.email,
    isAdmin: backendUser.is_admin,
    createdAt: backendUser.created_at,
    updatedAt: backendUser.updated_at
  }
}

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isRefreshing: boolean
  isAuthenticated: boolean
  login: (credentials: LoginRequest) => Promise<void>
  logout: () => Promise<void>
  refreshToken: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

// Token storage utilities
const TOKEN_KEYS = {
  ACCESS_TOKEN: 'labcastarr_access_token',
  REFRESH_TOKEN: 'labcastarr_refresh_token',
  USER: 'labcastarr_user'
}

class TokenStorage {
  static setTokens(accessToken: string, refreshToken: string) {
    if (typeof window !== 'undefined') {
      localStorage.setItem(TOKEN_KEYS.ACCESS_TOKEN, accessToken)
      localStorage.setItem(TOKEN_KEYS.REFRESH_TOKEN, refreshToken)
    }
  }

  static getAccessToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem(TOKEN_KEYS.ACCESS_TOKEN)
    }
    return null
  }

  static getRefreshToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem(TOKEN_KEYS.REFRESH_TOKEN)
    }
    return null
  }

  static setUser(user: User) {
    if (typeof window !== 'undefined') {
      localStorage.setItem(TOKEN_KEYS.USER, JSON.stringify(user))
    }
  }

  static getUser(): User | null {
    if (typeof window !== 'undefined') {
      const userData = localStorage.getItem(TOKEN_KEYS.USER)
      return userData ? JSON.parse(userData) : null
    }
    return null
  }

  static clearAll() {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(TOKEN_KEYS.ACCESS_TOKEN)
      localStorage.removeItem(TOKEN_KEYS.REFRESH_TOKEN)
      localStorage.removeItem(TOKEN_KEYS.USER)
    }
  }

  static hasValidTokens(): boolean {
    const accessToken = this.getAccessToken()
    const refreshToken = this.getRefreshToken()
    return !!(accessToken && refreshToken)
  }

  static isAccessTokenExpired(): boolean {
    const token = this.getAccessToken()
    if (!token) return true

    try {
      // Decode JWT payload without verification (just read exp claim)
      const payload = JSON.parse(atob(token.split('.')[1]))
      const exp = payload.exp * 1000 // Convert to milliseconds
      const bufferMs = 5 * 60 * 1000 // 5 minutes buffer
      return Date.now() >= (exp - bufferMs)
    } catch {
      return true // If we can't parse, consider expired
    }
  }

  static isRefreshTokenExpired(): boolean {
    const token = this.getRefreshToken()
    if (!token) return true

    try {
      // Decode JWT payload without verification (just read exp claim)
      const payload = JSON.parse(atob(token.split('.')[1]))
      const exp = payload.exp * 1000 // Convert to milliseconds
      return Date.now() >= exp
    } catch {
      return true // If we can't parse, consider expired
    }
  }
}

// Custom API request function that includes JWT token
async function authenticatedApiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const accessToken = TokenStorage.getAccessToken()

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
    ...options.headers,
  }

  // Add Authorization header if we have an access token
  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`
  }

  const API_BASE_URL = getApiBaseUrl()
  const response = await fetch(`${API_BASE_URL}/v1${endpoint}`, {
    ...options,
    headers,
    credentials: 'same-origin',
  })

  if (!response.ok) {
    let errorData
    try {
      errorData = await response.json()
    } catch {
      errorData = { message: `HTTP ${response.status}: ${response.statusText}` }
    }
    throw new Error(errorData.message || `HTTP error! status: ${response.status}`)
  }

  const contentType = response.headers.get('content-type')
  if (contentType && contentType.includes('application/json')) {
    return response.json()
  }

  return response.text() as unknown as T
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)

  // Memoized refresh function for activity detection
  const refreshToken = useCallback(async () => {
    try {
      setIsRefreshing(true)
      const refreshTokenValue = TokenStorage.getRefreshToken()

      if (!refreshTokenValue) {
        throw new Error('No refresh token available')
      }

      const response = await fetch(`${getApiBaseUrl()}/v1/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
        },
        body: JSON.stringify({ refresh_token: refreshTokenValue }),
      })

      if (!response.ok) {
        throw new Error('Token refresh failed')
      }

      const data = await response.json()

      // Update stored tokens - use new refresh token if provided, otherwise keep existing (backward compatibility)
      const newRefreshToken = data.refresh_token || refreshTokenValue
      TokenStorage.setTokens(data.access_token, newRefreshToken)

      // Log token rotation for debugging
      if (data.refresh_token) {
        console.debug('Token rotated: new refresh token received')
      }
    } catch (error) {
      console.error('Token refresh error:', error)
      throw error
    } finally {
      setIsRefreshing(false)
    }
  }, [])

  // Activity-based token refresh (every 5 minutes of activity)
  useActivityDetection(
    user ? refreshToken : undefined,
    5 * 60 * 1000 // Refresh on activity every 5 minutes
  )

  // Check for existing auth on mount
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        // Check if we have stored tokens
        if (!TokenStorage.hasValidTokens()) {
          setIsLoading(false)
          return
        }

        // Try to get current user with existing token
        const backendUser = await authenticatedApiRequest<any>('/auth/me')
        const currentUser = transformUserData(backendUser)
        setUser(currentUser)
        TokenStorage.setUser(currentUser)
      } catch (error) {
        console.error('Failed to initialize auth:', error)
        // Clear invalid tokens
        TokenStorage.clearAll()
      } finally {
        setIsLoading(false)
      }
    }

    initializeAuth()
  }, [])

  // Auto-refresh token functionality
  // Refresh at 80% of token lifetime (60 min * 0.8 = 48 min)
  useEffect(() => {
    if (!user) return

    const TOKEN_LIFETIME_MINUTES = 60 // Should match backend jwt_access_token_expire_minutes
    const REFRESH_PERCENTAGE = 0.8 // Refresh at 80% of token lifetime
    const refreshIntervalMs = TOKEN_LIFETIME_MINUTES * REFRESH_PERCENTAGE * 60 * 1000

    const refreshInterval = setInterval(async () => {
      try {
        await refreshToken()
      } catch (error) {
        console.error('Auto-refresh failed:', error)
        // If refresh fails, log out the user
        await logout()
      }
    }, refreshIntervalMs) // Refresh every 48 minutes (access token expires in 60)

    return () => clearInterval(refreshInterval)
  }, [user])

  // REMOVED: Window focus refresh was too aggressive
  // This was triggering refreshes on every click between DevTools and page,
  // causing state loss and poor UX. The auto-refresh timer (every 48 min) is sufficient.
  //
  // useEffect(() => {
  //   const handleFocus = async () => {
  //     if (user && TokenStorage.hasValidTokens()) {
  //       try {
  //         await refreshToken()
  //       } catch (error) {
  //         console.error('Focus refresh failed:', error)
  //         await logout()
  //       }
  //     }
  //   }
  //
  //   window.addEventListener('focus', handleFocus)
  //   return () => window.removeEventListener('focus', handleFocus)
  // }, [user])

  const login = async (credentials: LoginRequest) => {
    try {
      setIsLoading(true)

      // Call backend login endpoint directly
      const apiUrl = getApiBaseUrl()
      console.log('Login API URL:', apiUrl) // Debug logging for Safari troubleshooting

      const response = await fetch(`${apiUrl}/v1/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
        },
        body: JSON.stringify(credentials),
      })

      if (!response.ok) {
        const errorData = await response.json()

        // Handle different error formats
        let errorMessage = 'Login failed'
        if (typeof errorData.detail === 'string') {
          errorMessage = errorData.detail
        } else if (Array.isArray(errorData.detail)) {
          // Handle FastAPI validation errors (array format)
          errorMessage = errorData.detail.map((err: any) => err.msg).join(', ')
        } else if (errorData.message) {
          errorMessage = errorData.message
        }

        throw new Error(errorMessage)
      }

      const data = await response.json()

      // Store tokens and user data
      TokenStorage.setTokens(data.access_token, data.refresh_token)
      const transformedUser = transformUserData(data.user)
      TokenStorage.setUser(transformedUser)
      setUser(transformedUser)
    } catch (error) {
      console.error('Login error:', error)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async () => {
    try {
      const refreshTokenValue = TokenStorage.getRefreshToken()

      if (refreshTokenValue) {
        // Call backend logout endpoint
        await authenticatedApiRequest('/auth/logout', {
          method: 'POST',
          body: JSON.stringify({ refresh_token: refreshTokenValue }),
        })
      }
    } catch (error) {
      console.error('Logout error:', error)
      // Continue with logout even if backend call fails
    } finally {
      // Clear local storage and state
      TokenStorage.clearAll()
      setUser(null)
    }
  }

  const value: AuthContextType = {
    user,
    isLoading,
    isRefreshing,
    isAuthenticated: !!user,
    login,
    logout,
    refreshToken,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

// Hook to get the current access token
export function useAccessToken() {
  return TokenStorage.getAccessToken()
}

// Export token storage for use in API client
export { TokenStorage, authenticatedApiRequest }
```

Updating performTokenRefresh to store the new refresh token:

```typescript
/**
 * API client for LabCastARR backend communication
 */
import {
  User,
  Channel,
  Episode,
  Tag,
  Event,
  ApiResponse,
  PaginatedResponse,
  CreateEpisodeRequest,
  UpdateEpisodeRequest,
  ChannelSettingsRequest,
  EpisodeStatus,
  HealthResponse,
  DetailedHealthResponse,
  LoginRequest,
  RegisterRequest,
  AuthResponse,
  CreateTagRequest,
  UpdateTagRequest,
  UserProfileRequest,
  PasswordChangeRequest,
  EpisodeSearchParams,
  EventFilterParams,
  EventType,
  EventStatus,
  ChannelCreateRequest,
  ChannelUpdateRequest,
  ChannelStatistics,
  FeedValidationResponse,
  FeedInfoResponse,
  SearchRequest,
  SearchResponse,
  SearchSuggestion,
  TagSuggestionsResponse,
} from "@/types"
import { errorLogger } from "./error-logging"
import { getApiBaseUrl, logApiConfig } from "./api-url"

// Log API configuration on load for debugging (especially useful in production)
if (typeof window !== "undefined") {
  logApiConfig()
}

const API_BASE_URL = getApiBaseUrl()
const API_KEY =
  process.env.NEXT_PUBLIC_API_KEY || "dev-secret-key-change-in-production"

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public response?: unknown
  ) {
    super(message)
    this.name = "ApiError"
  }
}

// Security utilities
const sanitizeInput = (input: string): string => {
  // Basic input sanitization
  return input
    .replace(/[<>]/g, "") // Remove basic HTML characters
    .replace(/javascript:/gi, "") // Remove javascript: protocol
    .replace(/on\w+=/gi, "") // Remove event handlers
    .trim()
    .slice(0, 1000) // Limit length
}

const validateUrl = (url: string): boolean => {
  try {
    const parsed = new URL(url)
    return parsed.protocol === "http:" || parsed.protocol === "https:"
  } catch {
    return false
  }
}

// Token storage utility for client-side access
const getAccessToken = (): string | null => {
  if (typeof window !== "undefined") {
    return localStorage.getItem("labcastarr_access_token")
  }
  return null
}

// Global refresh promise to prevent duplicate refresh attempts
let refreshPromise: Promise<string | null> | null = null

/**
 * Perform token refresh with deduplication
 * Returns the new access token or null if refresh failed
 */
async function performTokenRefresh(): Promise<string | null> {
  const refreshToken =
    typeof window !== "undefined"
      ? localStorage.getItem("labcastarr_refresh_token")
      : null

  if (!refreshToken) {
    return null
  }

  try {
    const response = await fetch(`${API_BASE_URL}/v1/auth/refresh`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })

    if (response.ok) {
      const refreshData = await response.json()
      // Update the stored access token and refresh token (if provided)
      if (typeof window !== "undefined") {
        localStorage.setItem(
          "labcastarr_access_token",
          refreshData.access_token
        )
        // Store new refresh token if provided, otherwise keep existing (backward compatibility)
        if (refreshData.refresh_token) {
          localStorage.setItem(
            "labcastarr_refresh_token",
            refreshData.refresh_token
          )
        }
      }
      return refreshData.access_token
    }

    return null
  } catch (error) {
    console.error("Token refresh error:", error)
    return null
  }
}

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  // Validate endpoint
  if (!endpoint || typeof endpoint !== "string") {
    throw new ApiError(400, "Invalid endpoint")
  }

  // Sanitize endpoint
  const sanitizedEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`
  const url = `${API_BASE_URL}${sanitizedEndpoint}`

  // Validate constructed URL
  if (!validateUrl(url)) {
    throw new ApiError(400, "Invalid URL")
  }

  // Prepare secure headers
  const secureHeaders: HeadersInit = {
    "X-API-Key": API_KEY,
    "X-Requested-With": "XMLHttpRequest", // CSRF protection
    ...options.headers,
  }

  // Add JWT token if available (for authenticated endpoints)
  const accessToken = getAccessToken()
  if (
    accessToken &&
    !endpoint.includes("/auth/login") &&
    !endpoint.includes("/auth/refresh")
  ) {
    secureHeaders["Authorization"] = `Bearer ${accessToken}`
  }

  // Don't set Content-Type for FormData (let browser set it with boundary)
  if (!(options.body instanceof FormData)) {
    secureHeaders["Content-Type"] = "application/json"
  }

  const response = await fetch(url, {
    headers: secureHeaders,
    credentials: "same-origin", // Only send cookies to same origin
    ...options,
  })

  if (!response.ok) {
    let errorData
    try {
      errorData = await response.json()
    } catch {
      errorData = { message: `HTTP ${response.status}: ${response.statusText}` }
    }

    // Handle authentication errors with optimized refresh logic
    if (
      response.status === 401 &&
      accessToken &&
      !endpoint.includes("/auth/")
    ) {
      // Use cached refresh promise to prevent multiple simultaneous refreshes
      if (!refreshPromise) {
        refreshPromise = performTokenRefresh()
      }

      try {
        const newAccessToken = await refreshPromise
        refreshPromise = null // Reset cache after completion

        if (newAccessToken) {
          // Retry the original request with new token
          const retryHeaders = {
            ...secureHeaders,
            Authorization: `Bearer ${newAccessToken}`,
          }
          const retryResponse = await fetch(url, {
            ...options,
            headers: retryHeaders,
            credentials: "same-origin",
          })

          if (retryResponse.ok) {
            const contentType = retryResponse.headers.get("content-type")
            if (contentType && contentType.includes("application/json")) {
              return retryResponse.json()
            }
            return retryResponse.text() as unknown as T
          }
        } else {
          // Refresh failed, clear tokens and redirect to login
          if (typeof window !== "undefined") {
            localStorage.removeItem("labcastarr_access_token")
            localStorage.removeItem("labcastarr_refresh_token")
            localStorage.removeItem("labcastarr_user")
          }
        }
      } catch (refreshError) {
        refreshPromise = null // Reset cache on error
        // Clear tokens on refresh failure
        if (typeof window !== "undefined") {
          localStorage.removeItem("labcastarr_access_token")
          localStorage.removeItem("labcastarr_refresh_token")
          localStorage.removeItem("labcastarr_user")
        }
        console.error("Token refresh failed:", refreshError)
      }
    }

    // Log API errors with security context
    errorLogger.logApiError(
      sanitizedEndpoint,
      response.status,
      errorData.message || `HTTP error! status: ${response.status}`,
      errorData
    )

    throw new ApiError(
      response.status,
      errorData.message || `HTTP error! status: ${response.status}`,
      errorData
    )
  }

  // Handle different response types
  const contentType = response.headers.get("content-type")
  if (contentType && contentType.includes("application/json")) {
    return response.json()
  }

  return response.text() as unknown as T
}

// Authentication API
export const authApi = {
  async login(data: LoginRequest): Promise<AuthResponse> {
    const response = await apiRequest<ApiResponse<AuthResponse>>(
      "/auth/login",
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    )
    return response.data
  },

  async register(data: RegisterRequest): Promise<AuthResponse> {
    const response = await apiRequest<ApiResponse<AuthResponse>>(
      "/auth/register",
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    )
    return response.data
  },

  async logout(): Promise<void> {
    await apiRequest<void>("/auth/logout", {
      method: "POST",
    })
  },

  async getCurrentUser(): Promise<User> {
    const response = await apiRequest<ApiResponse<User>>("/auth/me")
    return response.data
  },

  async refreshToken(): Promise<AuthResponse> {
    const response = await apiRequest<ApiResponse<AuthResponse>>(
      "/auth/refresh",
      {
        method: "POST",
      }
    )
    return response.data
  },
}

// User API
export const userApi = {
  async getProfile(): Promise<User> {
    const response = await apiRequest<ApiResponse<User>>("/v1/users/profile")
    return response.data
  },

  async updateProfile(data: UserProfileRequest): Promise<User> {
    const response = await apiRequest<ApiResponse<User>>("/v1/users/profile", {
      method: "PUT",
      body: JSON.stringify(data),
    })
    return response.data
  },

  async changePassword(data: PasswordChangeRequest): Promise<void> {
    await apiRequest<void>("/v1/users/password", {
      method: "PUT",
      body: JSON.stringify(data),
    })
  },

  async deleteAccount(): Promise<void> {
    await apiRequest<void>("/v1/users/profile", {
      method: "DELETE",
    })
  },
}

// Health API
export const healthApi = {
  async check(): Promise<HealthResponse> {
    return apiRequest<HealthResponse>("/health/")
  },

  async checkDatabase(): Promise<HealthResponse> {
    return apiRequest<HealthResponse>("/health/db")
  },

  async checkDetailed(): Promise<DetailedHealthResponse> {
    return apiRequest<DetailedHealthResponse>("/health/detailed")
  },
}

// Episode API
export const episodeApi = {
  async getAll(
    channelId: number,
    params?: Omit<EpisodeSearchParams, "channelId">
  ): Promise<PaginatedResponse<Episode>> {
    const searchParams = new URLSearchParams({
      channel_id: channelId.toString(),
      page: (params?.page ?? 1).toString(),
      page_size: (params?.pageSize ?? 50).toString(),
    })

    if (params?.query) searchParams.set("q", params.query)
    if (params?.status) searchParams.set("status", params.status)
    if (params?.tags?.length) searchParams.set("tags", params.tags.join(","))
    if (params?.startDate) searchParams.set("start_date", params.startDate)
    if (params?.endDate) searchParams.set("end_date", params.endDate)

    const response = await apiRequest<PaginatedResponse<Episode>>(
      `/v1/episodes/?${searchParams.toString()}`
    )
    return response
  },

  async getById(id: number): Promise<Episode> {
    const response = await apiRequest<Episode>(`/v1/episodes/${id}`)
    return response
  },

  async create(data: CreateEpisodeRequest): Promise<Episode> {
    const response = await apiRequest<Episode>("/v1/episodes/", {
      method: "POST",
      body: JSON.stringify({
        channel_id: data.channel_id,
        video_url: sanitizeInput(data.video_url),
        tags: data.tags || [],
      }),
    })
    return response
  },

  async update(id: number, data: UpdateEpisodeRequest): Promise<Episode> {
    const response = await apiRequest<Episode>(`/v1/episodes/${id}`, {
      method: "PUT",
      body: JSON.stringify({
        title: data.title,
        description: data.description,
        keywords: data.keywords,
        tags: data.tags,
      }),
    })
    return response
  },

  async delete(id: number): Promise<void> {
    await apiRequest<void>(`/v1/episodes/${id}`, {
      method: "DELETE",
    })
  },

  async updateStatus(id: number, status: EpisodeStatus): Promise<Episode> {
    const response = await apiRequest<ApiResponse<Episode>>(
      `/v1/episodes/${id}/status`,
      {
        method: "PUT",
        body: JSON.stringify({ status }),
      }
    )
    return response.data
  },

  async getStatus(
    id: number
  ): Promise<{ status: EpisodeStatus; progress?: number }> {
    const response = await apiRequest<
      ApiResponse<{ status: EpisodeStatus; progress?: number }>
    >(`/v1/episodes/${id}/status`)
    return response.data
  },

  async getByStatus(status: EpisodeStatus): Promise<Episode[]> {
    const response = await apiRequest<ApiResponse<Episode[]>>(
      `/v1/episodes/by-status?status=${status}`
    )
    return response.data
  },

  async analyzeYouTubeVideo(videoUrl: string): Promise<{
    video_id: string
    title: string
    description: string
    duration_seconds?: number
    thumbnail_url?: string
    uploader?: string
    view_count: number
    publication_date?: string
    keywords: string[]
    video_url: string
    availability?: string
  }> {
    const response = await apiRequest<{
      video_id: string
      title: string
      description: string
      duration_seconds?: number
      thumbnail_url?: string
      uploader?: string
      view_count: number
      publication_date?: string
      keywords: string[]
      video_url: string
      availability?: string
    }>("/v1/episodes/analyze", {
      method: "POST",
      body: JSON.stringify({ video_url: sanitizeInput(videoUrl) }),
    })
    return response
  },

  async getProgress(id: number): Promise<{
    episode_id: number
    status: string
    percentage: string
    speed: string
    eta: string
    downloaded_bytes: number
    total_bytes: number
    error_message?: string
    started_at?: string
    completed_at?: string
    updated_at: string
  }> {
    const response = await apiRequest<{
      episode_id: number
      status: string
      percentage: string
      speed: string
      eta: string
      downloaded_bytes: number
      total_bytes: number
      error_message?: string
      started_at?: string
      completed_at?: string
      updated_at: string
    }>(`/v1/episodes/${id}/progress`)
    return response
  },

  async favorite(
    id: number
  ): Promise<{
    message: string
    data: { episode_id: number; is_favorited: boolean }
  }> {
    const response = await apiRequest<{
      message: string
      data: { episode_id: number; is_favorited: boolean }
    }>(`/v1/episodes/${id}/favorite`, { method: "POST" })
    return response
  },

  async unfavorite(
    id: number
  ): Promise<{
    message: string
    data: { episode_id: number; is_favorited: boolean }
  }> {
    const response = await apiRequest<{
      message: string
      data: { episode_id: number; is_favorited: boolean }
    }>(`/v1/episodes/${id}/favorite`, { method: "DELETE" })
    return response
  },

  async redownload(
    id: number
  ): Promise<{ message: string; data: { episode_id: number } }> {
    const response = await apiRequest<{
      message: string
      data: { episode_id: number }
    }>(`/v1/episodes/${id}/retry`, { method: "POST" })
    return response
  },

  async getCount(channelId: number = 1): Promise<{
    success: boolean
    channel_id: number
    episode_count: number
    message: string
  }> {
    const response = await apiRequest<{
      success: boolean
      channel_id: number
      episode_count: number
      message: string
    }>(`/v1/episodes/stats/count?channel_id=${channelId}`)
    return response
  },

  async bulkDeleteAll(
    channelId: number = 1,
    options: {
      dryRun?: boolean
      confirmToken?: string
      timeout?: number
      maxRetries?: number
    } = {}
  ): Promise<{
    success: boolean
    total_episodes: number
    deleted_episodes: number
    failed_episodes: number
    deleted_files: number
    failed_files: number
    partial_completion: boolean
    error_message?: string
    failed_episode_details?: Array<{
      episode_id: number
      title: string
      errors: string[]
    }>
    message: string
    channel_id: number
    dry_run: boolean
    timestamp: string
  }> {
    const {
      dryRun = false,
      confirmToken,
      timeout = 300000, // 5 minutes default
      maxRetries = 3,
    } = options

    // Build query parameters
    const params = new URLSearchParams({
      channel_id: channelId.toString(),
      dry_run: dryRun.toString(),
    })

    if (confirmToken) {
      params.set("confirm_token", confirmToken)
    }

    const endpoint = `/v1/episodes/actions/bulk-delete-all?${params.toString()}`

    // Retry logic with exponential backoff
    let lastError: Error | null = null
    let retryDelay = 1000 // Start with 1 second

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        const response = await apiRequest<{
          success: boolean
          total_episodes: number
          deleted_episodes: number
          failed_episodes: number
          deleted_files: number
          failed_files: number
          partial_completion: boolean
          error_message?: string
          failed_episode_details?: Array<{
            episode_id: number
            title: string
            errors: string[]
          }>
          message: string
          channel_id: number
          dry_run: boolean
          timestamp: string
        }>(endpoint, {
          method: "DELETE",
          signal: AbortSignal.timeout(timeout),
        })

        return response
      } catch (error) {
        lastError = error as Error
        const isApiError = error instanceof ApiError
        const isNetworkError =
          error instanceof TypeError && error.message.includes("fetch")
        const isTimeoutError =
          error instanceof DOMException && error.name === "TimeoutError"

        // Log the error with context
        errorLogger.logApiError(
          endpoint,
          isApiError ? (error as ApiError).status : 0,
          `Bulk deletion attempt ${attempt}/${maxRetries} failed: ${error.message}`,
          {
            attempt,
            maxRetries,
            channelId,
            dryRun,
            errorType: isApiError
              ? "api"
              : isNetworkError
              ? "network"
              : isTimeoutError
              ? "timeout"
              : "unknown",
          }
        )

        // Determine if we should retry
        const shouldRetry =
          attempt < maxRetries &&
          (isNetworkError ||
            isTimeoutError ||
            (isApiError &&
              [408, 429, 500, 502, 503, 504].includes(
                (error as ApiError).status
              )))

        if (!shouldRetry) {
          // Don't retry for client errors (400-499) except 408 (timeout) and 429 (rate limit)
          break
        }

        if (attempt < maxRetries) {
          // Wait before retrying with exponential backoff
          await new Promise((resolve) => setTimeout(resolve, retryDelay))
          retryDelay *= 2 // Double the delay for next attempt
        }
      }
    }

    // If we get here, all retries failed
    if (lastError instanceof ApiError) {
      // Enhanced error information for API errors
      const errorData = lastError.response as any
      throw new ApiError(
        lastError.status,
        `Bulk deletion failed after ${maxRetries} attempts: ${lastError.message}`,
        {
          ...errorData,
          attempts: maxRetries,
          finalError: true,
          channelId,
          dryRun,
        }
      )
    } else {
      // Network or other errors
      throw new Error(
        `Bulk deletion failed after ${maxRetries} attempts: ${
          lastError?.message || "Unknown error"
        }. ` + "Please check your internet connection and try again."
      )
    }
  },
}

// Channel API
export const channelApi = {
  async getAll(params?: {
    user_id?: number
    search?: string
    limit?: number
  }): Promise<Channel[]> {
    const searchParams = new URLSearchParams()
    if (params?.user_id) searchParams.set("user_id", params.user_id.toString())
    if (params?.search) searchParams.set("search", params.search)
    if (params?.limit) searchParams.set("limit", params.limit.toString())

    const query = searchParams.toString() ? `?${searchParams.toString()}` : ""
    return apiRequest<Channel[]>(`/v1/channels/${query}`)
  },

  async getById(id: number): Promise<Channel> {
    return apiRequest<Channel>(`/v1/channels/${id}`)
  },

  async create(data: ChannelCreateRequest): Promise<Channel> {
    return apiRequest<Channel>("/v1/channels/", {
      method: "POST",
      body: JSON.stringify(data),
    })
  },

  async update(id: number, data: ChannelUpdateRequest): Promise<Channel> {
    return apiRequest<Channel>(`/v1/channels/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    })
  },

  async delete(id: number): Promise<{ message: string }> {
    return apiRequest<{ message: string }>(`/v1/channels/${id}`, {
      method: "DELETE",
    })
  },

  async getStatistics(id: number): Promise<ChannelStatistics> {
    return apiRequest<ChannelStatistics>(`/v1/channels/${id}/statistics`)
  },

  async uploadImage(
    id: number,
    file: File
  ): Promise<{
    message: string
    image_url: string
    filename: string
    file_size: number
  }> {
    const formData = new FormData()
    formData.append("file", file)

    return apiRequest<{
      message: string
      image_url: string
      filename: string
      file_size: number
    }>(`/v1/channels/${id}/upload-image`, {
      method: "POST",
      body: formData,
    })
  },

  getImageUrl(id: number): string {
    return `${API_BASE_URL}/v1/channels/${id}/image.png`
  },
}

// RSS Feed API
export const feedApi = {
  async getRssFeed(channelId: number, limit?: number): Promise<string> {
    const params = limit ? `?limit=${limit}` : ""
    return apiRequest<string>(`/v1/feeds/${channelId}/feed.xml${params}`)
  },

  async validateFeed(channelId: number): Promise<FeedValidationResponse> {
    return apiRequest<FeedValidationResponse>(
      `/v1/feeds/${channelId}/validate`,
      {
        method: "POST",
      }
    )
  },

  async getFeedInfo(channelId: number): Promise<FeedInfoResponse> {
    return apiRequest<FeedInfoResponse>(`/v1/feeds/${channelId}/info`)
  },

  async getAllFeeds(): Promise<FeedInfoResponse[]> {
    return apiRequest<FeedInfoResponse[]>("/v1/feeds/")
  },
}

// Search API
export const searchApi = {
  async searchEpisodes(request: SearchRequest): Promise<SearchResponse> {
    return apiRequest<SearchResponse>("/v1/episodes/search", {
      method: "POST",
      body: JSON.stringify(request),
    })
  },

  async getSearchSuggestions(
    channelId: number,
    query: string,
    limit = 5
  ): Promise<SearchSuggestion[]> {
    const params = new URLSearchParams({
      channel_id: channelId.toString(),
      query,
      limit: limit.toString(),
    })
    return apiRequest<SearchSuggestion[]>(
      `/v1/episodes/search/suggestions?${params.toString()}`
    )
  },

  async getTrendingSearches(
    channelId: number,
    limit = 10
  ): Promise<SearchSuggestion[]> {
    const params = new URLSearchParams({
      channel_id: channelId.toString(),
      limit: limit.toString(),
    })
    return apiRequest<SearchSuggestion[]>(
      `/v1/episodes/search/trending?${params.toString()}`
    )
  },

  async getAvailableFilters(
    channelId: number
  ): Promise<Record<string, Array<{ value: string | number; count: number }>>> {
    return apiRequest<
      Record<string, Array<{ value: string | number; count: number }>>
    >(`/v1/episodes/filters/${channelId}`)
  },

  async rebuildSearchIndex(channelId?: number): Promise<{ message: string }> {
    const params = channelId ? `?channel_id=${channelId}` : ""
    return apiRequest<{ message: string }>(
      `/v1/episodes/search/rebuild${params}`,
      {
        method: "POST",
      }
    )
  },

  async getTagSuggestions(
    channelId: number,
    query: string,
    limit = 10
  ): Promise<TagSuggestionsResponse> {
    const params = new URLSearchParams({
      channel_id: channelId.toString(),
      query,
      limit: limit.toString(),
    })
    return apiRequest<TagSuggestionsResponse>(
      `/v1/tags/suggestions?${params.toString()}`
    )
  },
}

// Tag API
export const tagApi = {
  async getAll(
    channelId: number
  ): Promise<{ tags: Tag[]; total_count: number; channel_id: number }> {
    return apiRequest<{ tags: Tag[]; total_count: number; channel_id: number }>(
      `/v1/tags/?channel_id=${channelId}`
    )
  },

  async getById(id: number): Promise<Tag> {
    return apiRequest<Tag>(`/v1/tags/${id}`)
  },

  async create(channelId: number, data: CreateTagRequest): Promise<Tag> {
    return apiRequest<Tag>("/v1/tags/", {
      method: "POST",
      body: JSON.stringify({ channel_id: channelId, ...data }),
    })
  },

  async update(id: number, data: UpdateTagRequest): Promise<Tag> {
    return apiRequest<Tag>(`/v1/tags/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    })
  },

  async delete(id: number): Promise<{ message: string; tag_id: number }> {
    return apiRequest<{ message: string; tag_id: number }>(`/v1/tags/${id}`, {
      method: "DELETE",
    })
  },

  async getEpisodeTags(episodeId: number): Promise<Tag[]> {
    const response = await apiRequest<Episode>(`/v1/episodes/${episodeId}`)
    return response.tags || []
  },

  async addToEpisode(episodeId: number, tagIds: number[]): Promise<Episode> {
    return await apiRequest<Episode>(`/v1/episodes/${episodeId}/tags`, {
      method: "POST",
      body: JSON.stringify(tagIds),
    })
  },

  async removeFromEpisode(
    episodeId: number,
    tagIds: number[]
  ): Promise<Episode> {
    return await apiRequest<Episode>(`/v1/episodes/${episodeId}/tags`, {
      method: "DELETE",
      body: JSON.stringify(tagIds),
    })
  },

  async replaceEpisodeTags(
    episodeId: number,
    tagIds: number[]
  ): Promise<Episode> {
    return await apiRequest<Episode>(`/v1/episodes/${episodeId}/tags`, {
      method: "PUT",
      body: JSON.stringify(tagIds),
    })
  },
}

// Event API
export const eventApi = {
  async getAll(
    channelId: number,
    params?: Omit<EventFilterParams, "channelId">
  ): Promise<PaginatedResponse<Event>> {
    const searchParams = new URLSearchParams({
      channel_id: channelId.toString(),
      page: (params?.page ?? 1).toString(),
      page_size: (params?.pageSize ?? 100).toString(),
    })

    if (params?.eventType) searchParams.set("event_type", params.eventType)
    if (params?.status) searchParams.set("status", params.status)
    if (params?.startDate) searchParams.set("start_date", params.startDate)
    if (params?.endDate) searchParams.set("end_date", params.endDate)

    const response = await apiRequest<ApiResponse<PaginatedResponse<Event>>>(
      `/v1/events?${searchParams.toString()}`
    )
    return response.data
  },

  async getById(id: number): Promise<Event> {
    const response = await apiRequest<ApiResponse<Event>>(`/v1/events/${id}`)
    return response.data
  },

  async getByEpisode(episodeId: number): Promise<Event[]> {
    const response = await apiRequest<ApiResponse<Event[]>>(
      `/v1/episodes/${episodeId}/events`
    )
    return response.data
  },

  async getByType(eventType: EventType): Promise<Event[]> {
    const response = await apiRequest<ApiResponse<Event[]>>(
      `/v1/events/by-type?type=${eventType}`
    )
    return response.data
  },

  async getByStatus(status: EventStatus): Promise<Event[]> {
    const response = await apiRequest<ApiResponse<Event[]>>(
      `/v1/events/by-status?status=${status}`
    )
    return response.data
  },

  async cleanup(olderThanDays: number): Promise<{ deleted: number }> {
    const response = await apiRequest<ApiResponse<{ deleted: number }>>(
      "/v1/events/cleanup",
      {
        method: "POST",
        body: JSON.stringify({ older_than_days: olderThanDays }),
      }
    )
    return response.data
  },
}

// Export security utilities for external use
export { ApiError, sanitizeInput, validateUrl }
```

Adding expiration check to apiRequest. Creating a helper function to check token expiration:

```typescript
/**
 * API client for LabCastARR backend communication
 */
import {
  User,
  Channel,
  Episode,
  Tag,
  Event,
  ApiResponse,
  PaginatedResponse,
  CreateEpisodeRequest,
  UpdateEpisodeRequest,
  ChannelSettingsRequest,
  EpisodeStatus,
  HealthResponse,
  DetailedHealthResponse,
  LoginRequest,
  RegisterRequest,
  AuthResponse,
  CreateTagRequest,
  UpdateTagRequest,
  UserProfileRequest,
  PasswordChangeRequest,
  EpisodeSearchParams,
  EventFilterParams,
  EventType,
  EventStatus,
  ChannelCreateRequest,
  ChannelUpdateRequest,
  ChannelStatistics,
  FeedValidationResponse,
  FeedInfoResponse,
  SearchRequest,
  SearchResponse,
  SearchSuggestion,
  TagSuggestionsResponse,
} from "@/types"
import { errorLogger } from "./error-logging"
import { getApiBaseUrl, logApiConfig } from "./api-url"

// Log API configuration on load for debugging (especially useful in production)
if (typeof window !== "undefined") {
  logApiConfig()
}

const API_BASE_URL = getApiBaseUrl()
const API_KEY =
  process.env.NEXT_PUBLIC_API_KEY || "dev-secret-key-change-in-production"

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public response?: unknown
  ) {
    super(message)
    this.name = "ApiError"
  }
}

// Security utilities
const sanitizeInput = (input: string): string => {
  // Basic input sanitization
  return input
    .replace(/[<>]/g, "") // Remove basic HTML characters
    .replace(/javascript:/gi, "") // Remove javascript: protocol
    .replace(/on\w+=/gi, "") // Remove event handlers
    .trim()
    .slice(0, 1000) // Limit length
}

const validateUrl = (url: string): boolean => {
  try {
    const parsed = new URL(url)
    return parsed.protocol === "http:" || parsed.protocol === "https:"
  } catch {
    return false
  }
}

// Token storage utility for client-side access
const getAccessToken = (): string | null => {
  if (typeof window !== "undefined") {
    return localStorage.getItem("labcastarr_access_token")
  }
  return null
}

// Check if access token is expired or expiring soon
const isAccessTokenExpired = (): boolean => {
  const token = getAccessToken()
  if (!token) return true

  try {
    // Decode JWT payload without verification (just read exp claim)
    const payload = JSON.parse(atob(token.split(".")[1]))
    const exp = payload.exp * 1000 // Convert to milliseconds
    const bufferMs = 5 * 60 * 1000 // 5 minutes buffer
    return Date.now() >= exp - bufferMs
  } catch {
    return true // If we can't parse, consider expired
  }
}

// Global refresh promise to prevent duplicate refresh attempts
let refreshPromise: Promise<string | null> | null = null

/**
 * Perform token refresh with deduplication
 * Returns the new access token or null if refresh failed
 */
async function performTokenRefresh(): Promise<string | null> {
  const refreshToken =
    typeof window !== "undefined"
      ? localStorage.getItem("labcastarr_refresh_token")
      : null

  if (!refreshToken) {
    return null
  }

  try {
    const response = await fetch(`${API_BASE_URL}/v1/auth/refresh`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })

    if (response.ok) {
      const refreshData = await response.json()
      // Update the stored access token and refresh token (if provided)
      if (typeof window !== "undefined") {
        localStorage.setItem(
          "labcastarr_access_token",
          refreshData.access_token
        )
        // Store new refresh token if provided, otherwise keep existing (backward compatibility)
        if (refreshData.refresh_token) {
          localStorage.setItem(
            "labcastarr_refresh_token",
            refreshData.refresh_token
          )
        }
      }
      return refreshData.access_token
    }

    return null
  } catch (error) {
    console.error("Token refresh error:", error)
    return null
  }
}

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  // Validate endpoint
  if (!endpoint || typeof endpoint !== "string") {
    throw new ApiError(400, "Invalid endpoint")
  }

  // Sanitize endpoint
  const sanitizedEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`
  const url = `${API_BASE_URL}${sanitizedEndpoint}`

  // Validate constructed URL
  if (!validateUrl(url)) {
    throw new ApiError(400, "Invalid URL")
  }

  // Prepare secure headers
  const secureHeaders: HeadersInit = {
    "X-API-Key": API_KEY,
    "X-Requested-With": "XMLHttpRequest", // CSRF protection
    ...options.headers,
  }

  // Add JWT token if available (for authenticated endpoints)
  const accessToken = getAccessToken()
  if (
    accessToken &&
    !endpoint.includes("/auth/login") &&
    !endpoint.includes("/auth/refresh")
  ) {
    secureHeaders["Authorization"] = `Bearer ${accessToken}`
  }

  // Don't set Content-Type for FormData (let browser set it with boundary)
  if (!(options.body instanceof FormData)) {
    secureHeaders["Content-Type"] = "application/json"
  }

  const response = await fetch(url, {
    headers: secureHeaders,
    credentials: "same-origin", // Only send cookies to same origin
    ...options,
  })

  if (!response.ok) {
    let errorData
    try {
      errorData = await response.json()
    } catch {
      errorData = { message: `HTTP ${response.status}: ${response.statusText}` }
    }

    // Handle authentication errors with optimized refresh logic
    if (
      response.status === 401 &&
      accessToken &&
      !endpoint.includes("/auth/")
    ) {
      // Use cached refresh promise to prevent multiple simultaneous refreshes
      if (!refreshPromise) {
        refreshPromise = performTokenRefresh()
      }

      try {
        const newAccessToken = await refreshPromise
        refreshPromise = null // Reset cache after completion

        if (newAccessToken) {
          // Retry the original request with new token
          const retryHeaders = {
            ...secureHeaders,
            Authorization: `Bearer ${newAccessToken}`,
          }
          const retryResponse = await fetch(url, {
            ...options,
            headers: retryHeaders,
            credentials: "same-origin",
          })

          if (retryResponse.ok) {
            const contentType = retryResponse.headers.get("content-type")
            if (contentType && contentType.includes("application/json")) {
              return retryResponse.json()
            }
            return retryResponse.text() as unknown as T
          }
        } else {
          // Refresh failed, clear tokens and redirect to login
          if (typeof window !== "undefined") {
            localStorage.removeItem("labcastarr_access_token")
            localStorage.removeItem("labcastarr_refresh_token")
            localStorage.removeItem("labcastarr_user")
          }
        }
      } catch (refreshError) {
        refreshPromise = null // Reset cache on error
        // Clear tokens on refresh failure
        if (typeof window !== "undefined") {
          localStorage.removeItem("labcastarr_access_token")
          localStorage.removeItem("labcastarr_refresh_token")
          localStorage.removeItem("labcastarr_user")
        }
        console.error("Token refresh failed:", refreshError)
      }
    }

    // Log API errors with security context
    errorLogger.logApiError(
      sanitizedEndpoint,
      response.status,
      errorData.message || `HTTP error! status: ${response.status}`,
      errorData
    )

    throw new ApiError(
      response.status,
      errorData.message || `HTTP error! status: ${response.status}`,
      errorData
    )
  }

  // Handle different response types
  const contentType = response.headers.get("content-type")
  if (contentType && contentType.includes("application/json")) {
    return response.json()
  }

  return response.text() as unknown as T
}

// Authentication API
export const authApi = {
  async login(data: LoginRequest): Promise<AuthResponse> {
    const response = await apiRequest<ApiResponse<AuthResponse>>(
      "/auth/login",
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    )
    return response.data
  },

  async register(data: RegisterRequest): Promise<AuthResponse> {
    const response = await apiRequest<ApiResponse<AuthResponse>>(
      "/auth/register",
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    )
    return response.data
  },

  async logout(): Promise<void> {
    await apiRequest<void>("/auth/logout", {
      method: "POST",
    })
  },

  async getCurrentUser(): Promise<User> {
    const response = await apiRequest<ApiResponse<User>>("/auth/me")
    return response.data
  },

  async refreshToken(): Promise<AuthResponse> {
    const response = await apiRequest<ApiResponse<AuthResponse>>(
      "/auth/refresh",
      {
        method: "POST",
      }
    )
    return response.data
  },
}

// User API
export const userApi = {
  async getProfile(): Promise<User> {
    const response = await apiRequest<ApiResponse<User>>("/v1/users/profile")
    return response.data
  },

  async updateProfile(data: UserProfileRequest): Promise<User> {
    const response = await apiRequest<ApiResponse<User>>("/v1/users/profile", {
      method: "PUT",
      body: JSON.stringify(data),
    })
    return response.data
  },

  async changePassword(data: PasswordChangeRequest): Promise<void> {
    await apiRequest<void>("/v1/users/password", {
      method: "PUT",
      body: JSON.stringify(data),
    })
  },

  async deleteAccount(): Promise<void> {
    await apiRequest<void>("/v1/users/profile", {
      method: "DELETE",
    })
  },
}

// Health API
export const healthApi = {
  async check(): Promise<HealthResponse> {
    return apiRequest<HealthResponse>("/health/")
  },

  async checkDatabase(): Promise<HealthResponse> {
    return apiRequest<HealthResponse>("/health/db")
  },

  async checkDetailed(): Promise<DetailedHealthResponse> {
    return apiRequest<DetailedHealthResponse>("/health/detailed")
  },
}

// Episode API
export const episodeApi = {
  async getAll(
    channelId: number,
    params?: Omit<EpisodeSearchParams, "channelId">
  ): Promise<PaginatedResponse<Episode>> {
    const searchParams = new URLSearchParams({
      channel_id: channelId.toString(),
      page: (params?.page ?? 1).toString(),
      page_size: (params?.pageSize ?? 50).toString(),
    })

    if (params?.query) searchParams.set("q", params.query)
    if (params?.status) searchParams.set("status", params.status)
    if (params?.tags?.length) searchParams.set("tags", params.tags.join(","))
    if (params?.startDate) searchParams.set("start_date", params.startDate)
    if (params?.endDate) searchParams.set("end_date", params.endDate)

    const response = await apiRequest<PaginatedResponse<Episode>>(
      `/v1/episodes/?${searchParams.toString()}`
    )
    return response
  },

  async getById(id: number): Promise<Episode> {
    const response = await apiRequest<Episode>(`/v1/episodes/${id}`)
    return response
  },

  async create(data: CreateEpisodeRequest): Promise<Episode> {
    const response = await apiRequest<Episode>("/v1/episodes/", {
      method: "POST",
      body: JSON.stringify({
        channel_id: data.channel_id,
        video_url: sanitizeInput(data.video_url),
        tags: data.tags || [],
      }),
    })
    return response
  },

  async update(id: number, data: UpdateEpisodeRequest): Promise<Episode> {
    const response = await apiRequest<Episode>(`/v1/episodes/${id}`, {
      method: "PUT",
      body: JSON.stringify({
        title: data.title,
        description: data.description,
        keywords: data.keywords,
        tags: data.tags,
      }),
    })
    return response
  },

  async delete(id: number): Promise<void> {
    await apiRequest<void>(`/v1/episodes/${id}`, {
      method: "DELETE",
    })
  },

  async updateStatus(id: number, status: EpisodeStatus): Promise<Episode> {
    const response = await apiRequest<ApiResponse<Episode>>(
      `/v1/episodes/${id}/status`,
      {
        method: "PUT",
        body: JSON.stringify({ status }),
      }
    )
    return response.data
  },

  async getStatus(
    id: number
  ): Promise<{ status: EpisodeStatus; progress?: number }> {
    const response = await apiRequest<
      ApiResponse<{ status: EpisodeStatus; progress?: number }>
    >(`/v1/episodes/${id}/status`)
    return response.data
  },

  async getByStatus(status: EpisodeStatus): Promise<Episode[]> {
    const response = await apiRequest<ApiResponse<Episode[]>>(
      `/v1/episodes/by-status?status=${status}`
    )
    return response.data
  },

  async analyzeYouTubeVideo(videoUrl: string): Promise<{
    video_id: string
    title: string
    description: string
    duration_seconds?: number
    thumbnail_url?: string
    uploader?: string
    view_count: number
    publication_date?: string
    keywords: string[]
    video_url: string
    availability?: string
  }> {
    const response = await apiRequest<{
      video_id: string
      title: string
      description: string
      duration_seconds?: number
      thumbnail_url?: string
      uploader?: string
      view_count: number
      publication_date?: string
      keywords: string[]
      video_url: string
      availability?: string
    }>("/v1/episodes/analyze", {
      method: "POST",
      body: JSON.stringify({ video_url: sanitizeInput(videoUrl) }),
    })
    return response
  },

  async getProgress(id: number): Promise<{
    episode_id: number
    status: string
    percentage: string
    speed: string
    eta: string
    downloaded_bytes: number
    total_bytes: number
    error_message?: string
    started_at?: string
    completed_at?: string
    updated_at: string
  }> {
    const response = await apiRequest<{
      episode_id: number
      status: string
      percentage: string
      speed: string
      eta: string
      downloaded_bytes: number
      total_bytes: number
      error_message?: string
      started_at?: string
      completed_at?: string
      updated_at: string
    }>(`/v1/episodes/${id}/progress`)
    return response
  },

  async favorite(
    id: number
  ): Promise<{
    message: string
    data: { episode_id: number; is_favorited: boolean }
  }> {
    const response = await apiRequest<{
      message: string
      data: { episode_id: number; is_favorited: boolean }
    }>(`/v1/episodes/${id}/favorite`, { method: "POST" })
    return response
  },

  async unfavorite(
    id: number
  ): Promise<{
    message: string
    data: { episode_id: number; is_favorited: boolean }
  }> {
    const response = await apiRequest<{
      message: string
      data: { episode_id: number; is_favorited: boolean }
    }>(`/v1/episodes/${id}/favorite`, { method: "DELETE" })
    return response
  },

  async redownload(
    id: number
  ): Promise<{ message: string; data: { episode_id: number } }> {
    const response = await apiRequest<{
      message: string
      data: { episode_id: number }
    }>(`/v1/episodes/${id}/retry`, { method: "POST" })
    return response
  },

  async getCount(channelId: number = 1): Promise<{
    success: boolean
    channel_id: number
    episode_count: number
    message: string
  }> {
    const response = await apiRequest<{
      success: boolean
      channel_id: number
      episode_count: number
      message: string
    }>(`/v1/episodes/stats/count?channel_id=${channelId}`)
    return response
  },

  async bulkDeleteAll(
    channelId: number = 1,
    options: {
      dryRun?: boolean
      confirmToken?: string
      timeout?: number
      maxRetries?: number
    } = {}
  ): Promise<{
    success: boolean
    total_episodes: number
    deleted_episodes: number
    failed_episodes: number
    deleted_files: number
    failed_files: number
    partial_completion: boolean
    error_message?: string
    failed_episode_details?: Array<{
      episode_id: number
      title: string
      errors: string[]
    }>
    message: string
    channel_id: number
    dry_run: boolean
    timestamp: string
  }> {
    const {
      dryRun = false,
      confirmToken,
      timeout = 300000, // 5 minutes default
      maxRetries = 3,
    } = options

    // Build query parameters
    const params = new URLSearchParams({
      channel_id: channelId.toString(),
      dry_run: dryRun.toString(),
    })

    if (confirmToken) {
      params.set("confirm_token", confirmToken)
    }

    const endpoint = `/v1/episodes/actions/bulk-delete-all?${params.toString()}`

    // Retry logic with exponential backoff
    let lastError: Error | null = null
    let retryDelay = 1000 // Start with 1 second

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        const response = await apiRequest<{
          success: boolean
          total_episodes: number
          deleted_episodes: number
          failed_episodes: number
          deleted_files: number
          failed_files: number
          partial_completion: boolean
          error_message?: string
          failed_episode_details?: Array<{
            episode_id: number
            title: string
            errors: string[]
          }>
          message: string
          channel_id: number
          dry_run: boolean
          timestamp: string
        }>(endpoint, {
          method: "DELETE",
          signal: AbortSignal.timeout(timeout),
        })

        return response
      } catch (error) {
        lastError = error as Error
        const isApiError = error instanceof ApiError
        const isNetworkError =
          error instanceof TypeError && error.message.includes("fetch")
        const isTimeoutError =
          error instanceof DOMException && error.name === "TimeoutError"

        // Log the error with context
        errorLogger.logApiError(
          endpoint,
          isApiError ? (error as ApiError).status : 0,
          `Bulk deletion attempt ${attempt}/${maxRetries} failed: ${error.message}`,
          {
            attempt,
            maxRetries,
            channelId,
            dryRun,
            errorType: isApiError
              ? "api"
              : isNetworkError
              ? "network"
              : isTimeoutError
              ? "timeout"
              : "unknown",
          }
        )

        // Determine if we should retry
        const shouldRetry =
          attempt < maxRetries &&
          (isNetworkError ||
            isTimeoutError ||
            (isApiError &&
              [408, 429, 500, 502, 503, 504].includes(
                (error as ApiError).status
              )))

        if (!shouldRetry) {
          // Don't retry for client errors (400-499) except 408 (timeout) and 429 (rate limit)
          break
        }

        if (attempt < maxRetries) {
          // Wait before retrying with exponential backoff
          await new Promise((resolve) => setTimeout(resolve, retryDelay))
          retryDelay *= 2 // Double the delay for next attempt
        }
      }
    }

    // If we get here, all retries failed
    if (lastError instanceof ApiError) {
      // Enhanced error information for API errors
      const errorData = lastError.response as any
      throw new ApiError(
        lastError.status,
        `Bulk deletion failed after ${maxRetries} attempts: ${lastError.message}`,
        {
          ...errorData,
          attempts: maxRetries,
          finalError: true,
          channelId,
          dryRun,
        }
      )
    } else {
      // Network or other errors
      throw new Error(
        `Bulk deletion failed after ${maxRetries} attempts: ${
          lastError?.message || "Unknown error"
        }. ` + "Please check your internet connection and try again."
      )
    }
  },
}

// Channel API
export const channelApi = {
  async getAll(params?: {
    user_id?: number
    search?: string
    limit?: number
  }): Promise<Channel[]> {
    const searchParams = new URLSearchParams()
    if (params?.user_id) searchParams.set("user_id", params.user_id.toString())
    if (params?.search) searchParams.set("search", params.search)
    if (params?.limit) searchParams.set("limit", params.limit.toString())

    const query = searchParams.toString() ? `?${searchParams.toString()}` : ""
    return apiRequest<Channel[]>(`/v1/channels/${query}`)
  },

  async getById(id: number): Promise<Channel> {
    return apiRequest<Channel>(`/v1/channels/${id}`)
  },

  async create(data: ChannelCreateRequest): Promise<Channel> {
    return apiRequest<Channel>("/v1/channels/", {
      method: "POST",
      body: JSON.stringify(data),
    })
  },

  async update(id: number, data: ChannelUpdateRequest): Promise<Channel> {
    return apiRequest<Channel>(`/v1/channels/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    })
  },

  async delete(id: number): Promise<{ message: string }> {
    return apiRequest<{ message: string }>(`/v1/channels/${id}`, {
      method: "DELETE",
    })
  },

  async getStatistics(id: number): Promise<ChannelStatistics> {
    return apiRequest<ChannelStatistics>(`/v1/channels/${id}/statistics`)
  },

  async uploadImage(
    id: number,
    file: File
  ): Promise<{
    message: string
    image_url: string
    filename: string
    file_size: number
  }> {
    const formData = new FormData()
    formData.append("file", file)

    return apiRequest<{
      message: string
      image_url: string
      filename: string
      file_size: number
    }>(`/v1/channels/${id}/upload-image`, {
      method: "POST",
      body: formData,
    })
  },

  getImageUrl(id: number): string {
    return `${API_BASE_URL}/v1/channels/${id}/image.png`
  },
}

// RSS Feed API
export const feedApi = {
  async getRssFeed(channelId: number, limit?: number): Promise<string> {
    const params = limit ? `?limit=${limit}` : ""
    return apiRequest<string>(`/v1/feeds/${channelId}/feed.xml${params}`)
  },

  async validateFeed(channelId: number): Promise<FeedValidationResponse> {
    return apiRequest<FeedValidationResponse>(
      `/v1/feeds/${channelId}/validate`,
      {
        method: "POST",
      }
    )
  },

  async getFeedInfo(channelId: number): Promise<FeedInfoResponse> {
    return apiRequest<FeedInfoResponse>(`/v1/feeds/${channelId}/info`)
  },

  async getAllFeeds(): Promise<FeedInfoResponse[]> {
    return apiRequest<FeedInfoResponse[]>("/v1/feeds/")
  },
}

// Search API
export const searchApi = {
  async searchEpisodes(request: SearchRequest): Promise<SearchResponse> {
    return apiRequest<SearchResponse>("/v1/episodes/search", {
      method: "POST",
      body: JSON.stringify(request),
    })
  },

  async getSearchSuggestions(
    channelId: number,
    query: string,
    limit = 5
  ): Promise<SearchSuggestion[]> {
    const params = new URLSearchParams({
      channel_id: channelId.toString(),
      query,
      limit: limit.toString(),
    })
    return apiRequest<SearchSuggestion[]>(
      `/v1/episodes/search/suggestions?${params.toString()}`
    )
  },

  async getTrendingSearches(
    channelId: number,
    limit = 10
  ): Promise<SearchSuggestion[]> {
    const params = new URLSearchParams({
      channel_id: channelId.toString(),
      limit: limit.toString(),
    })
    return apiRequest<SearchSuggestion[]>(
      `/v1/episodes/search/trending?${params.toString()}`
    )
  },

  async getAvailableFilters(
    channelId: number
  ): Promise<Record<string, Array<{ value: string | number; count: number }>>> {
    return apiRequest<
      Record<string, Array<{ value: string | number; count: number }>>
    >(`/v1/episodes/filters/${channelId}`)
  },

  async rebuildSearchIndex(channelId?: number): Promise<{ message: string }> {
    const params = channelId ? `?channel_id=${channelId}` : ""
    return apiRequest<{ message: string }>(
      `/v1/episodes/search/rebuild${params}`,
      {
        method: "POST",
      }
    )
  },

  async getTagSuggestions(
    channelId: number,
    query: string,
    limit = 10
  ): Promise<TagSuggestionsResponse> {
    const params = new URLSearchParams({
      channel_id: channelId.toString(),
      query,
      limit: limit.toString(),
    })
    return apiRequest<TagSuggestionsResponse>(
      `/v1/tags/suggestions?${params.toString()}`
    )
  },
}

// Tag API
export const tagApi = {
  async getAll(
    channelId: number
  ): Promise<{ tags: Tag[]; total_count: number; channel_id: number }> {
    return apiRequest<{ tags: Tag[]; total_count: number; channel_id: number }>(
      `/v1/tags/?channel_id=${channelId}`
    )
  },

  async getById(id: number): Promise<Tag> {
    return apiRequest<Tag>(`/v1/tags/${id}`)
  },

  async create(channelId: number, data: CreateTagRequest): Promise<Tag> {
    return apiRequest<Tag>("/v1/tags/", {
      method: "POST",
      body: JSON.stringify({ channel_id: channelId, ...data }),
    })
  },

  async update(id: number, data: UpdateTagRequest): Promise<Tag> {
    return apiRequest<Tag>(`/v1/tags/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    })
  },

  async delete(id: number): Promise<{ message: string; tag_id: number }> {
    return apiRequest<{ message: string; tag_id: number }>(`/v1/tags/${id}`, {
      method: "DELETE",
    })
  },

  async getEpisodeTags(episodeId: number): Promise<Tag[]> {
    const response = await apiRequest<Episode>(`/v1/episodes/${episodeId}`)
    return response.tags || []
  },

  async addToEpisode(episodeId: number, tagIds: number[]): Promise<Episode> {
    return await apiRequest<Episode>(`/v1/episodes/${episodeId}/tags`, {
      method: "POST",
      body: JSON.stringify(tagIds),
    })
  },

  async removeFromEpisode(
    episodeId: number,
    tagIds: number[]
  ): Promise<Episode> {
    return await apiRequest<Episode>(`/v1/episodes/${episodeId}/tags`, {
      method: "DELETE",
      body: JSON.stringify(tagIds),
    })
  },

  async replaceEpisodeTags(
    episodeId: number,
    tagIds: number[]
  ): Promise<Episode> {
    return await apiRequest<Episode>(`/v1/episodes/${episodeId}/tags`, {
      method: "PUT",
      body: JSON.stringify(tagIds),
    })
  },
}

// Event API
export const eventApi = {
  async getAll(
    channelId: number,
    params?: Omit<EventFilterParams, "channelId">
  ): Promise<PaginatedResponse<Event>> {
    const searchParams = new URLSearchParams({
      channel_id: channelId.toString(),
      page: (params?.page ?? 1).toString(),
      page_size: (params?.pageSize ?? 100).toString(),
    })

    if (params?.eventType) searchParams.set("event_type", params.eventType)
    if (params?.status) searchParams.set("status", params.status)
    if (params?.startDate) searchParams.set("start_date", params.startDate)
    if (params?.endDate) searchParams.set("end_date", params.endDate)

    const response = await apiRequest<ApiResponse<PaginatedResponse<Event>>>(
      `/v1/events?${searchParams.toString()}`
    )
    return response.data
  },

  async getById(id: number): Promise<Event> {
    const response = await apiRequest<ApiResponse<Event>>(`/v1/events/${id}`)
    return response.data
  },

  async getByEpisode(episodeId: number): Promise<Event[]> {
    const response = await apiRequest<ApiResponse<Event[]>>(
      `/v1/episodes/${episodeId}/events`
    )
    return response.data
  },

  async getByType(eventType: EventType): Promise<Event[]> {
    const response = await apiRequest<ApiResponse<Event[]>>(
      `/v1/events/by-type?type=${eventType}`
    )
    return response.data
  },

  async getByStatus(status: EventStatus): Promise<Event[]> {
    const response = await apiRequest<ApiResponse<Event[]>>(
      `/v1/events/by-status?status=${status}`
    )
    return response.data
  },

  async cleanup(olderThanDays: number): Promise<{ deleted: number }> {
    const response = await apiRequest<ApiResponse<{ deleted: number }>>(
      "/v1/events/cleanup",
      {
        method: "POST",
        body: JSON.stringify({ older_than_days: olderThanDays }),
      }
    )
    return response.data
  },
}

// Export security utilities for external use
export { ApiError, sanitizeInput, validateUrl }
```

```typescript
/**
 * API client for LabCastARR backend communication
 */
import {
  User,
  Channel,
  Episode,
  Tag,
  Event,
  ApiResponse,
  PaginatedResponse,
  CreateEpisodeRequest,
  UpdateEpisodeRequest,
  ChannelSettingsRequest,
  EpisodeStatus,
  HealthResponse,
  DetailedHealthResponse,
  LoginRequest,
  RegisterRequest,
  AuthResponse,
  CreateTagRequest,
  UpdateTagRequest,
  UserProfileRequest,
  PasswordChangeRequest,
  EpisodeSearchParams,
  EventFilterParams,
  EventType,
  EventStatus,
  ChannelCreateRequest,
  ChannelUpdateRequest,
  ChannelStatistics,
  FeedValidationResponse,
  FeedInfoResponse,
  SearchRequest,
  SearchResponse,
  SearchSuggestion,
  TagSuggestionsResponse,
} from "@/types"
import { errorLogger } from "./error-logging"
import { getApiBaseUrl, logApiConfig } from "./api-url"

// Log API configuration on load for debugging (especially useful in production)
if (typeof window !== "undefined") {
  logApiConfig()
}

const API_BASE_URL = getApiBaseUrl()
const API_KEY =
  process.env.NEXT_PUBLIC_API_KEY || "dev-secret-key-change-in-production"

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public response?: unknown
  ) {
    super(message)
    this.name = "ApiError"
  }
}

// Security utilities
const sanitizeInput = (input: string): string => {
  // Basic input sanitization
  return input
    .replace(/[<>]/g, "") // Remove basic HTML characters
    .replace(/javascript:/gi, "") // Remove javascript: protocol
    .replace(/on\w+=/gi, "") // Remove event handlers
    .trim()
    .slice(0, 1000) // Limit length
}

const validateUrl = (url: string): boolean => {
  try {
    const parsed = new URL(url)
    return parsed.protocol === "http:" || parsed.protocol === "https:"
  } catch {
    return false
  }
}

// Token storage utility for client-side access
const getAccessToken = (): string | null => {
  if (typeof window !== "undefined") {
    return localStorage.getItem("labcastarr_access_token")
  }
  return null
}

// Check if access token is expired or expiring soon
const isAccessTokenExpired = (): boolean => {
  const token = getAccessToken()
  if (!token) return true

  try {
    // Decode JWT payload without verification (just read exp claim)
    const payload = JSON.parse(atob(token.split(".")[1]))
    const exp = payload.exp * 1000 // Convert to milliseconds
    const bufferMs = 5 * 60 * 1000 // 5 minutes buffer
    return Date.now() >= exp - bufferMs
  } catch {
    return true // If we can't parse, consider expired
  }
}

// Global refresh promise to prevent duplicate refresh attempts
let refreshPromise: Promise<string | null> | null = null

/**
 * Perform token refresh with deduplication
 * Returns the new access token or null if refresh failed
 */
async function performTokenRefresh(): Promise<string | null> {
  const refreshToken =
    typeof window !== "undefined"
      ? localStorage.getItem("labcastarr_refresh_token")
      : null

  if (!refreshToken) {
    return null
  }

  try {
    const response = await fetch(`${API_BASE_URL}/v1/auth/refresh`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })

    if (response.ok) {
      const refreshData = await response.json()
      // Update the stored access token and refresh token (if provided)
      if (typeof window !== "undefined") {
        localStorage.setItem(
          "labcastarr_access_token",
          refreshData.access_token
        )
        // Store new refresh token if provided, otherwise keep existing (backward compatibility)
        if (refreshData.refresh_token) {
          localStorage.setItem(
            "labcastarr_refresh_token",
            refreshData.refresh_token
          )
        }
      }
      return refreshData.access_token
    }

    return null
  } catch (error) {
    console.error("Token refresh error:", error)
    return null
  }
}

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  // Validate endpoint
  if (!endpoint || typeof endpoint !== "string") {
    throw new ApiError(400, "Invalid endpoint")
  }

  // Sanitize endpoint
  const sanitizedEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`
  const url = `${API_BASE_URL}${sanitizedEndpoint}`

  // Validate constructed URL
  if (!validateUrl(url)) {
    throw new ApiError(400, "Invalid URL")
  }

  // Prepare secure headers
  const secureHeaders: HeadersInit = {
    "X-API-Key": API_KEY,
    "X-Requested-With": "XMLHttpRequest", // CSRF protection
    ...options.headers,
  }

  // Add JWT token if available (for authenticated endpoints)
  // Check if token is expired and refresh proactively before making request
  let accessToken = getAccessToken()
  if (
    accessToken &&
    !endpoint.includes("/auth/login") &&
    !endpoint.includes("/auth/refresh")
  ) {
    // Proactive refresh if token is expired or expiring soon
    if (isAccessTokenExpired()) {
      // Attempt refresh before making the request
      const newAccessToken = await performTokenRefresh()
      if (newAccessToken) {
        accessToken = newAccessToken
      } else {
        // Refresh failed, clear tokens
        if (typeof window !== "undefined") {
          localStorage.removeItem("labcastarr_access_token")
          localStorage.removeItem("labcastarr_refresh_token")
          localStorage.removeItem("labcastarr_user")
        }
      }
    }

    if (accessToken) {
      secureHeaders["Authorization"] = `Bearer ${accessToken}`
    }
  }

  // Don't set Content-Type for FormData (let browser set it with boundary)
  if (!(options.body instanceof FormData)) {
    secureHeaders["Content-Type"] = "application/json"
  }

  const response = await fetch(url, {
    headers: secureHeaders,
    credentials: "same-origin", // Only send cookies to same origin
    ...options,
  })

  if (!response.ok) {
    let errorData
    try {
      errorData = await response.json()
    } catch {
      errorData = { message: `HTTP ${response.status}: ${response.statusText}` }
    }

    // Handle authentication errors with optimized refresh logic
    if (
      response.status === 401 &&
      accessToken &&
      !endpoint.includes("/auth/")
    ) {
      // Use cached refresh promise to prevent multiple simultaneous refreshes
      if (!refreshPromise) {
        refreshPromise = performTokenRefresh()
      }

      try {
        const newAccessToken = await refreshPromise
        refreshPromise = null // Reset cache after completion

        if (newAccessToken) {
          // Retry the original request with new token
          const retryHeaders = {
            ...secureHeaders,
            Authorization: `Bearer ${newAccessToken}`,
          }
          const retryResponse = await fetch(url, {
            ...options,
            headers: retryHeaders,
            credentials: "same-origin",
          })

          if (retryResponse.ok) {
            const contentType = retryResponse.headers.get("content-type")
            if (contentType && contentType.includes("application/json")) {
              return retryResponse.json()
            }
            return retryResponse.text() as unknown as T
          }
        } else {
          // Refresh failed, clear tokens and redirect to login
          if (typeof window !== "undefined") {
            localStorage.removeItem("labcastarr_access_token")
            localStorage.removeItem("labcastarr_refresh_token")
            localStorage.removeItem("labcastarr_user")
          }
        }
      } catch (refreshError) {
        refreshPromise = null // Reset cache on error
        // Clear tokens on refresh failure
        if (typeof window !== "undefined") {
          localStorage.removeItem("labcastarr_access_token")
          localStorage.removeItem("labcastarr_refresh_token")
          localStorage.removeItem("labcastarr_user")
        }
        console.error("Token refresh failed:", refreshError)
      }
    }

    // Log API errors with security context
    errorLogger.logApiError(
      sanitizedEndpoint,
      response.status,
      errorData.message || `HTTP error! status: ${response.status}`,
      errorData
    )

    throw new ApiError(
      response.status,
      errorData.message || `HTTP error! status: ${response.status}`,
      errorData
    )
  }

  // Handle different response types
  const contentType = response.headers.get("content-type")
  if (contentType && contentType.includes("application/json")) {
    return response.json()
  }

  return response.text() as unknown as T
}

// Authentication API
export const authApi = {
  async login(data: LoginRequest): Promise<AuthResponse> {
    const response = await apiRequest<ApiResponse<AuthResponse>>(
      "/auth/login",
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    )
    return response.data
  },

  async register(data: RegisterRequest): Promise<AuthResponse> {
    const response = await apiRequest<ApiResponse<AuthResponse>>(
      "/auth/register",
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    )
    return response.data
  },

  async logout(): Promise<void> {
    await apiRequest<void>("/auth/logout", {
      method: "POST",
    })
  },

  async getCurrentUser(): Promise<User> {
    const response = await apiRequest<ApiResponse<User>>("/auth/me")
    return response.data
  },

  async refreshToken(): Promise<AuthResponse> {
    const response = await apiRequest<ApiResponse<AuthResponse>>(
      "/auth/refresh",
      {
        method: "POST",
      }
    )
    return response.data
  },
}

// User API
export const userApi = {
  async getProfile(): Promise<User> {
    const response = await apiRequest<ApiResponse<User>>("/v1/users/profile")
    return response.data
  },

  async updateProfile(data: UserProfileRequest): Promise<User> {
    const response = await apiRequest<ApiResponse<User>>("/v1/users/profile", {
      method: "PUT",
      body: JSON.stringify(data),
    })
    return response.data
  },

  async changePassword(data: PasswordChangeRequest): Promise<void> {
    await apiRequest<void>("/v1/users/password", {
      method: "PUT",
      body: JSON.stringify(data),
    })
  },

  async deleteAccount(): Promise<void> {
    await apiRequest<void>("/v1/users/profile", {
      method: "DELETE",
    })
  },
}

// Health API
export const healthApi = {
  async check(): Promise<HealthResponse> {
    return apiRequest<HealthResponse>("/health/")
  },

  async checkDatabase(): Promise<HealthResponse> {
    return apiRequest<HealthResponse>("/health/db")
  },

  async checkDetailed(): Promise<DetailedHealthResponse> {
    return apiRequest<DetailedHealthResponse>("/health/detailed")
  },
}

// Episode API
export const episodeApi = {
  async getAll(
    channelId: number,
    params?: Omit<EpisodeSearchParams, "channelId">
  ): Promise<PaginatedResponse<Episode>> {
    const searchParams = new URLSearchParams({
      channel_id: channelId.toString(),
      page: (params?.page ?? 1).toString(),
      page_size: (params?.pageSize ?? 50).toString(),
    })

    if (params?.query) searchParams.set("q", params.query)
    if (params?.status) searchParams.set("status", params.status)
    if (params?.tags?.length) searchParams.set("tags", params.tags.join(","))
    if (params?.startDate) searchParams.set("start_date", params.startDate)
    if (params?.endDate) searchParams.set("end_date", params.endDate)

    const response = await apiRequest<PaginatedResponse<Episode>>(
      `/v1/episodes/?${searchParams.toString()}`
    )
    return response
  },

  async getById(id: number): Promise<Episode> {
    const response = await apiRequest<Episode>(`/v1/episodes/${id}`)
    return response
  },

  async create(data: CreateEpisodeRequest): Promise<Episode> {
    const response = await apiRequest<Episode>("/v1/episodes/", {
      method: "POST",
      body: JSON.stringify({
        channel_id: data.channel_id,
        video_url: sanitizeInput(data.video_url),
        tags: data.tags || [],
      }),
    })
    return response
  },

  async update(id: number, data: UpdateEpisodeRequest): Promise<Episode> {
    const response = await apiRequest<Episode>(`/v1/episodes/${id}`, {
      method: "PUT",
      body: JSON.stringify({
        title: data.title,
        description: data.description,
        keywords: data.keywords,
        tags: data.tags,
      }),
    })
    return response
  },

  async delete(id: number): Promise<void> {
    await apiRequest<void>(`/v1/episodes/${id}`, {
      method: "DELETE",
    })
  },

  async updateStatus(id: number, status: EpisodeStatus): Promise<Episode> {
    const response = await apiRequest<ApiResponse<Episode>>(
      `/v1/episodes/${id}/status`,
      {
        method: "PUT",
        body: JSON.stringify({ status }),
      }
    )
    return response.data
  },

  async getStatus(
    id: number
  ): Promise<{ status: EpisodeStatus; progress?: number }> {
    const response = await apiRequest<
      ApiResponse<{ status: EpisodeStatus; progress?: number }>
    >(`/v1/episodes/${id}/status`)
    return response.data
  },

  async getByStatus(status: EpisodeStatus): Promise<Episode[]> {
    const response = await apiRequest<ApiResponse<Episode[]>>(
      `/v1/episodes/by-status?status=${status}`
    )
    return response.data
  },

  async analyzeYouTubeVideo(videoUrl: string): Promise<{
    video_id: string
    title: string
    description: string
    duration_seconds?: number
    thumbnail_url?: string
    uploader?: string
    view_count: number
    publication_date?: string
    keywords: string[]
    video_url: string
    availability?: string
  }> {
    const response = await apiRequest<{
      video_id: string
      title: string
      description: string
      duration_seconds?: number
      thumbnail_url?: string
      uploader?: string
      view_count: number
      publication_date?: string
      keywords: string[]
      video_url: string
      availability?: string
    }>("/v1/episodes/analyze", {
      method: "POST",
      body: JSON.stringify({ video_url: sanitizeInput(videoUrl) }),
    })
    return response
  },

  async getProgress(id: number): Promise<{
    episode_id: number
    status: string
    percentage: string
    speed: string
    eta: string
    downloaded_bytes: number
    total_bytes: number
    error_message?: string
    started_at?: string
    completed_at?: string
    updated_at: string
  }> {
    const response = await apiRequest<{
      episode_id: number
      status: string
      percentage: string
      speed: string
      eta: string
      downloaded_bytes: number
      total_bytes: number
      error_message?: string
      started_at?: string
      completed_at?: string
      updated_at: string
    }>(`/v1/episodes/${id}/progress`)
    return response
  },

  async favorite(
    id: number
  ): Promise<{
    message: string
    data: { episode_id: number; is_favorited: boolean }
  }> {
    const response = await apiRequest<{
      message: string
      data: { episode_id: number; is_favorited: boolean }
    }>(`/v1/episodes/${id}/favorite`, { method: "POST" })
    return response
  },

  async unfavorite(
    id: number
  ): Promise<{
    message: string
    data: { episode_id: number; is_favorited: boolean }
  }> {
    const response = await apiRequest<{
      message: string
      data: { episode_id: number; is_favorited: boolean }
    }>(`/v1/episodes/${id}/favorite`, { method: "DELETE" })
    return response
  },

  async redownload(
    id: number
  ): Promise<{ message: string; data: { episode_id: number } }> {
    const response = await apiRequest<{
      message: string
      data: { episode_id: number }
    }>(`/v1/episodes/${id}/retry`, { method: "POST" })
    return response
  },

  async getCount(channelId: number = 1): Promise<{
    success: boolean
    channel_id: number
    episode_count: number
    message: string
  }> {
    const response = await apiRequest<{
      success: boolean
      channel_id: number
      episode_count: number
      message: string
    }>(`/v1/episodes/stats/count?channel_id=${channelId}`)
    return response
  },

  async bulkDeleteAll(
    channelId: number = 1,
    options: {
      dryRun?: boolean
      confirmToken?: string
      timeout?: number
      maxRetries?: number
    } = {}
  ): Promise<{
    success: boolean
    total_episodes: number
    deleted_episodes: number
    failed_episodes: number
    deleted_files: number
    failed_files: number
    partial_completion: boolean
    error_message?: string
    failed_episode_details?: Array<{
      episode_id: number
      title: string
      errors: string[]
    }>
    message: string
    channel_id: number
    dry_run: boolean
    timestamp: string
  }> {
    const {
      dryRun = false,
      confirmToken,
      timeout = 300000, // 5 minutes default
      maxRetries = 3,
    } = options

    // Build query parameters
    const params = new URLSearchParams({
      channel_id: channelId.toString(),
      dry_run: dryRun.toString(),
    })

    if (confirmToken) {
      params.set("confirm_token", confirmToken)
    }

    const endpoint = `/v1/episodes/actions/bulk-delete-all?${params.toString()}`

    // Retry logic with exponential backoff
    let lastError: Error | null = null
    let retryDelay = 1000 // Start with 1 second

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        const response = await apiRequest<{
          success: boolean
          total_episodes: number
          deleted_episodes: number
          failed_episodes: number
          deleted_files: number
          failed_files: number
          partial_completion: boolean
          error_message?: string
          failed_episode_details?: Array<{
            episode_id: number
            title: string
            errors: string[]
          }>
          message: string
          channel_id: number
          dry_run: boolean
          timestamp: string
        }>(endpoint, {
          method: "DELETE",
          signal: AbortSignal.timeout(timeout),
        })

        return response
      } catch (error) {
        lastError = error as Error
        const isApiError = error instanceof ApiError
        const isNetworkError =
          error instanceof TypeError && error.message.includes("fetch")
        const isTimeoutError =
          error instanceof DOMException && error.name === "TimeoutError"

        // Log the error with context
        errorLogger.logApiError(
          endpoint,
          isApiError ? (error as ApiError).status : 0,
          `Bulk deletion attempt ${attempt}/${maxRetries} failed: ${error.message}`,
          {
            attempt,
            maxRetries,
            channelId,
            dryRun,
            errorType: isApiError
              ? "api"
              : isNetworkError
              ? "network"
              : isTimeoutError
              ? "timeout"
              : "unknown",
          }
        )

        // Determine if we should retry
        const shouldRetry =
          attempt < maxRetries &&
          (isNetworkError ||
            isTimeoutError ||
            (isApiError &&
              [408, 429, 500, 502, 503, 504].includes(
                (error as ApiError).status
              )))

        if (!shouldRetry) {
          // Don't retry for client errors (400-499) except 408 (timeout) and 429 (rate limit)
          break
        }

        if (attempt < maxRetries) {
          // Wait before retrying with exponential backoff
          await new Promise((resolve) => setTimeout(resolve, retryDelay))
          retryDelay *= 2 // Double the delay for next attempt
        }
      }
    }

    // If we get here, all retries failed
    if (lastError instanceof ApiError) {
      // Enhanced error information for API errors
      const errorData = lastError.response as any
      throw new ApiError(
        lastError.status,
        `Bulk deletion failed after ${maxRetries} attempts: ${lastError.message}`,
        {
          ...errorData,
          attempts: maxRetries,
          finalError: true,
          channelId,
          dryRun,
        }
      )
    } else {
      // Network or other errors
      throw new Error(
        `Bulk deletion failed after ${maxRetries} attempts: ${
          lastError?.message || "Unknown error"
        }. ` + "Please check your internet connection and try again."
      )
    }
  },
}

// Channel API
export const channelApi = {
  async getAll(params?: {
    user_id?: number
    search?: string
    limit?: number
  }): Promise<Channel[]> {
    const searchParams = new URLSearchParams()
    if (params?.user_id) searchParams.set("user_id", params.user_id.toString())
    if (params?.search) searchParams.set("search", params.search)
    if (params?.limit) searchParams.set("limit", params.limit.toString())

    const query = searchParams.toString() ? `?${searchParams.toString()}` : ""
    return apiRequest<Channel[]>(`/v1/channels/${query}`)
  },

  async getById(id: number): Promise<Channel> {
    return apiRequest<Channel>(`/v1/channels/${id}`)
  },

  async create(data: ChannelCreateRequest): Promise<Channel> {
    return apiRequest<Channel>("/v1/channels/", {
      method: "POST",
      body: JSON.stringify(data),
    })
  },

  async update(id: number, data: ChannelUpdateRequest): Promise<Channel> {
    return apiRequest<Channel>(`/v1/channels/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    })
  },

  async delete(id: number): Promise<{ message: string }> {
    return apiRequest<{ message: string }>(`/v1/channels/${id}`, {
      method: "DELETE",
    })
  },

  async getStatistics(id: number): Promise<ChannelStatistics> {
    return apiRequest<ChannelStatistics>(`/v1/channels/${id}/statistics`)
  },

  async uploadImage(
    id: number,
    file: File
  ): Promise<{
    message: string
    image_url: string
    filename: string
    file_size: number
  }> {
    const formData = new FormData()
    formData.append("file", file)

    return apiRequest<{
      message: string
      image_url: string
      filename: string
      file_size: number
    }>(`/v1/channels/${id}/upload-image`, {
      method: "POST",
      body: formData,
    })
  },

  getImageUrl(id: number): string {
    return `${API_BASE_URL}/v1/channels/${id}/image.png`
  },
}

// RSS Feed API
export const feedApi = {
  async getRssFeed(channelId: number, limit?: number): Promise<string> {
    const params = limit ? `?limit=${limit}` : ""
    return apiRequest<string>(`/v1/feeds/${channelId}/feed.xml${params}`)
  },

  async validateFeed(channelId: number): Promise<FeedValidationResponse> {
    return apiRequest<FeedValidationResponse>(
      `/v1/feeds/${channelId}/validate`,
      {
        method: "POST",
      }
    )
  },

  async getFeedInfo(channelId: number): Promise<FeedInfoResponse> {
    return apiRequest<FeedInfoResponse>(`/v1/feeds/${channelId}/info`)
  },

  async getAllFeeds(): Promise<FeedInfoResponse[]> {
    return apiRequest<FeedInfoResponse[]>("/v1/feeds/")
  },
}

// Search API
export const searchApi = {
  async searchEpisodes(request: SearchRequest): Promise<SearchResponse> {
    return apiRequest<SearchResponse>("/v1/episodes/search", {
      method: "POST",
      body: JSON.stringify(request),
    })
  },

  async getSearchSuggestions(
    channelId: number,
    query: string,
    limit = 5
  ): Promise<SearchSuggestion[]> {
    const params = new URLSearchParams({
      channel_id: channelId.toString(),
      query,
      limit: limit.toString(),
    })
    return apiRequest<SearchSuggestion[]>(
      `/v1/episodes/search/suggestions?${params.toString()}`
    )
  },

  async getTrendingSearches(
    channelId: number,
    limit = 10
  ): Promise<SearchSuggestion[]> {
    const params = new URLSearchParams({
      channel_id: channelId.toString(),
      limit: limit.toString(),
    })
    return apiRequest<SearchSuggestion[]>(
      `/v1/episodes/search/trending?${params.toString()}`
    )
  },

  async getAvailableFilters(
    channelId: number
  ): Promise<Record<string, Array<{ value: string | number; count: number }>>> {
    return apiRequest<
      Record<string, Array<{ value: string | number; count: number }>>
    >(`/v1/episodes/filters/${channelId}`)
  },

  async rebuildSearchIndex(channelId?: number): Promise<{ message: string }> {
    const params = channelId ? `?channel_id=${channelId}` : ""
    return apiRequest<{ message: string }>(
      `/v1/episodes/search/rebuild${params}`,
      {
        method: "POST",
      }
    )
  },

  async getTagSuggestions(
    channelId: number,
    query: string,
    limit = 10
  ): Promise<TagSuggestionsResponse> {
    const params = new URLSearchParams({
      channel_id: channelId.toString(),
      query,
      limit: limit.toString(),
    })
    return apiRequest<TagSuggestionsResponse>(
      `/v1/tags/suggestions?${params.toString()}`
    )
  },
}

// Tag API
export const tagApi = {
  async getAll(
    channelId: number
  ): Promise<{ tags: Tag[]; total_count: number; channel_id: number }> {
    return apiRequest<{ tags: Tag[]; total_count: number; channel_id: number }>(
      `/v1/tags/?channel_id=${channelId}`
    )
  },

  async getById(id: number): Promise<Tag> {
    return apiRequest<Tag>(`/v1/tags/${id}`)
  },

  async create(channelId: number, data: CreateTagRequest): Promise<Tag> {
    return apiRequest<Tag>("/v1/tags/", {
      method: "POST",
      body: JSON.stringify({ channel_id: channelId, ...data }),
    })
  },

  async update(id: number, data: UpdateTagRequest): Promise<Tag> {
    return apiRequest<Tag>(`/v1/tags/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    })
  },

  async delete(id: number): Promise<{ message: string; tag_id: number }> {
    return apiRequest<{ message: string; tag_id: number }>(`/v1/tags/${id}`, {
      method: "DELETE",
    })
  },

  async getEpisodeTags(episodeId: number): Promise<Tag[]> {
    const response = await apiRequest<Episode>(`/v1/episodes/${episodeId}`)
    return response.tags || []
  },

  async addToEpisode(episodeId: number, tagIds: number[]): Promise<Episode> {
    return await apiRequest<Episode>(`/v1/episodes/${episodeId}/tags`, {
      method: "POST",
      body: JSON.stringify(tagIds),
    })
  },

  async removeFromEpisode(
    episodeId: number,
    tagIds: number[]
  ): Promise<Episode> {
    return await apiRequest<Episode>(`/v1/episodes/${episodeId}/tags`, {
      method: "DELETE",
      body: JSON.stringify(tagIds),
    })
  },

  async replaceEpisodeTags(
    episodeId: number,
    tagIds: number[]
  ): Promise<Episode> {
    return await apiRequest<Episode>(`/v1/episodes/${episodeId}/tags`, {
      method: "PUT",
      body: JSON.stringify(tagIds),
    })
  },
}

// Event API
export const eventApi = {
  async getAll(
    channelId: number,
    params?: Omit<EventFilterParams, "channelId">
  ): Promise<PaginatedResponse<Event>> {
    const searchParams = new URLSearchParams({
      channel_id: channelId.toString(),
      page: (params?.page ?? 1).toString(),
      page_size: (params?.pageSize ?? 100).toString(),
    })

    if (params?.eventType) searchParams.set("event_type", params.eventType)
    if (params?.status) searchParams.set("status", params.status)
    if (params?.startDate) searchParams.set("start_date", params.startDate)
    if (params?.endDate) searchParams.set("end_date", params.endDate)

    const response = await apiRequest<ApiResponse<PaginatedResponse<Event>>>(
      `/v1/events?${searchParams.toString()}`
    )
    return response.data
  },

  async getById(id: number): Promise<Event> {
    const response = await apiRequest<ApiResponse<Event>>(`/v1/events/${id}`)
    return response.data
  },

  async getByEpisode(episodeId: number): Promise<Event[]> {
    const response = await apiRequest<ApiResponse<Event[]>>(
      `/v1/episodes/${episodeId}/events`
    )
    return response.data
  },

  async getByType(eventType: EventType): Promise<Event[]> {
    const response = await apiRequest<ApiResponse<Event[]>>(
      `/v1/events/by-type?type=${eventType}`
    )
    return response.data
  },

  async getByStatus(status: EventStatus): Promise<Event[]> {
    const response = await apiRequest<ApiResponse<Event[]>>(
      `/v1/events/by-status?status=${status}`
    )
    return response.data
  },

  async cleanup(olderThanDays: number): Promise<{ deleted: number }> {
    const response = await apiRequest<ApiResponse<{ deleted: number }>>(
      "/v1/events/cleanup",
      {
        method: "POST",
        body: JSON.stringify({ older_than_days: olderThanDays }),
      }
    )
    return response.data
  },
}

// Export security utilities for external use
export { ApiError, sanitizeInput, validateUrl }
```

Updating initializeAuth to refresh the token before validation (critical fix):

```typescriptreact
'use client'

import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react'
import { User, LoginRequest } from '@/types'
import { authApi } from '@/lib/api'
import { getApiBaseUrl } from '@/lib/api-url'
import { useActivityDetection } from '@/hooks/use-activity-detection'

// Transform backend user data (snake_case) to frontend format (camelCase)
function transformUserData(backendUser: any): User {
  return {
    id: backendUser.id,
    name: backendUser.name,
    email: backendUser.email,
    isAdmin: backendUser.is_admin,
    createdAt: backendUser.created_at,
    updatedAt: backendUser.updated_at
  }
}

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isRefreshing: boolean
  isAuthenticated: boolean
  login: (credentials: LoginRequest) => Promise<void>
  logout: () => Promise<void>
  refreshToken: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

// Token storage utilities
const TOKEN_KEYS = {
  ACCESS_TOKEN: 'labcastarr_access_token',
  REFRESH_TOKEN: 'labcastarr_refresh_token',
  USER: 'labcastarr_user'
}

class TokenStorage {
  static setTokens(accessToken: string, refreshToken: string) {
    if (typeof window !== 'undefined') {
      localStorage.setItem(TOKEN_KEYS.ACCESS_TOKEN, accessToken)
      localStorage.setItem(TOKEN_KEYS.REFRESH_TOKEN, refreshToken)
    }
  }

  static getAccessToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem(TOKEN_KEYS.ACCESS_TOKEN)
    }
    return null
  }

  static getRefreshToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem(TOKEN_KEYS.REFRESH_TOKEN)
    }
    return null
  }

  static setUser(user: User) {
    if (typeof window !== 'undefined') {
      localStorage.setItem(TOKEN_KEYS.USER, JSON.stringify(user))
    }
  }

  static getUser(): User | null {
    if (typeof window !== 'undefined') {
      const userData = localStorage.getItem(TOKEN_KEYS.USER)
      return userData ? JSON.parse(userData) : null
    }
    return null
  }

  static clearAll() {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(TOKEN_KEYS.ACCESS_TOKEN)
      localStorage.removeItem(TOKEN_KEYS.REFRESH_TOKEN)
      localStorage.removeItem(TOKEN_KEYS.USER)
    }
  }

  static hasValidTokens(): boolean {
    const accessToken = this.getAccessToken()
    const refreshToken = this.getRefreshToken()
    return !!(accessToken && refreshToken)
  }

  static isAccessTokenExpired(): boolean {
    const token = this.getAccessToken()
    if (!token) return true

    try {
      // Decode JWT payload without verification (just read exp claim)
      const payload = JSON.parse(atob(token.split('.')[1]))
      const exp = payload.exp * 1000 // Convert to milliseconds
      const bufferMs = 5 * 60 * 1000 // 5 minutes buffer
      return Date.now() >= (exp - bufferMs)
    } catch {
      return true // If we can't parse, consider expired
    }
  }

  static isRefreshTokenExpired(): boolean {
    const token = this.getRefreshToken()
    if (!token) return true

    try {
      // Decode JWT payload without verification (just read exp claim)
      const payload = JSON.parse(atob(token.split('.')[1]))
      const exp = payload.exp * 1000 // Convert to milliseconds
      return Date.now() >= exp
    } catch {
      return true // If we can't parse, consider expired
    }
  }
}

// Custom API request function that includes JWT token
async function authenticatedApiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const accessToken = TokenStorage.getAccessToken()

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
    ...options.headers,
  }

  // Add Authorization header if we have an access token
  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`
  }

  const API_BASE_URL = getApiBaseUrl()
  const response = await fetch(`${API_BASE_URL}/v1${endpoint}`, {
    ...options,
    headers,
    credentials: 'same-origin',
  })

  if (!response.ok) {
    let errorData
    try {
      errorData = await response.json()
    } catch {
      errorData = { message: `HTTP ${response.status}: ${response.statusText}` }
    }
    throw new Error(errorData.message || `HTTP error! status: ${response.status}`)
  }

  const contentType = response.headers.get('content-type')
  if (contentType && contentType.includes('application/json')) {
    return response.json()
  }

  return response.text() as unknown as T
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)

  // Memoized refresh function for activity detection
  const refreshToken = useCallback(async () => {
    try {
      setIsRefreshing(true)
      const refreshTokenValue = TokenStorage.getRefreshToken()

      if (!refreshTokenValue) {
        throw new Error('No refresh token available')
      }

      const response = await fetch(`${getApiBaseUrl()}/v1/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
        },
        body: JSON.stringify({ refresh_token: refreshTokenValue }),
      })

      if (!response.ok) {
        throw new Error('Token refresh failed')
      }

      const data = await response.json()

      // Update stored tokens - use new refresh token if provided, otherwise keep existing (backward compatibility)
      const newRefreshToken = data.refresh_token || refreshTokenValue
      TokenStorage.setTokens(data.access_token, newRefreshToken)

      // Log token rotation for debugging
      if (data.refresh_token) {
        console.debug('Token rotated: new refresh token received')
      }
    } catch (error) {
      console.error('Token refresh error:', error)
      throw error
    } finally {
      setIsRefreshing(false)
    }
  }, [])

  // Activity-based token refresh (every 5 minutes of activity)
  useActivityDetection(
    user ? refreshToken : undefined,
    5 * 60 * 1000 // Refresh on activity every 5 minutes
  )

  // Check for existing auth on mount
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        // Check if we have stored tokens
        if (!TokenStorage.hasValidTokens()) {
          setIsLoading(false)
          return
        }

        const refreshTokenValue = TokenStorage.getRefreshToken()

        // CRITICAL: Refresh token BEFORE validation if refresh token exists
        // This allows inactive users to return after hours/days and stay logged in
        if (refreshTokenValue) {
          try {
            await refreshToken()
          } catch (refreshError) {
            // Refresh failed - refresh token expired or invalid
            console.error('Token refresh failed on initialization:', refreshError)
            TokenStorage.clearAll()
            setIsLoading(false)
            return
          }
        }

        // Now validate with fresh access token
        const backendUser = await authenticatedApiRequest<any>('/auth/me')
        const currentUser = transformUserData(backendUser)
        setUser(currentUser)
        TokenStorage.setUser(currentUser)
      } catch (error) {
        console.error('Failed to initialize auth:', error)
        // Clear invalid tokens
        TokenStorage.clearAll()
      } finally {
        setIsLoading(false)
      }
    }

    initializeAuth()
  }, [refreshToken])

  // Auto-refresh token functionality
  // Refresh at 80% of token lifetime (60 min * 0.8 = 48 min)
  useEffect(() => {
    if (!user) return

    const TOKEN_LIFETIME_MINUTES = 60 // Should match backend jwt_access_token_expire_minutes
    const REFRESH_PERCENTAGE = 0.8 // Refresh at 80% of token lifetime
    const refreshIntervalMs = TOKEN_LIFETIME_MINUTES * REFRESH_PERCENTAGE * 60 * 1000

    const refreshInterval = setInterval(async () => {
      try {
        await refreshToken()
      } catch (error) {
        console.error('Auto-refresh failed:', error)
        // If refresh fails, log out the user
        await logout()
      }
    }, refreshIntervalMs) // Refresh every 48 minutes (access token expires in 60)

    return () => clearInterval(refreshInterval)
  }, [user])

  // REMOVED: Window focus refresh was too aggressive
  // This was triggering refreshes on every click between DevTools and page,
  // causing state loss and poor UX. The auto-refresh timer (every 48 min) is sufficient.
  //
  // useEffect(() => {
  //   const handleFocus = async () => {
  //     if (user && TokenStorage.hasValidTokens()) {
  //       try {
  //         await refreshToken()
  //       } catch (error) {
  //         console.error('Focus refresh failed:', error)
  //         await logout()
  //       }
  //     }
  //   }
  //
  //   window.addEventListener('focus', handleFocus)
  //   return () => window.removeEventListener('focus', handleFocus)
  // }, [user])

  const login = async (credentials: LoginRequest) => {
    try {
      setIsLoading(true)

      // Call backend login endpoint directly
      const apiUrl = getApiBaseUrl()
      console.log('Login API URL:', apiUrl) // Debug logging for Safari troubleshooting

      const response = await fetch(`${apiUrl}/v1/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
        },
        body: JSON.stringify(credentials),
      })

      if (!response.ok) {
        const errorData = await response.json()

        // Handle different error formats
        let errorMessage = 'Login failed'
        if (typeof errorData.detail === 'string') {
          errorMessage = errorData.detail
        } else if (Array.isArray(errorData.detail)) {
          // Handle FastAPI validation errors (array format)
          errorMessage = errorData.detail.map((err: any) => err.msg).join(', ')
        } else if (errorData.message) {
          errorMessage = errorData.message
        }

        throw new Error(errorMessage)
      }

      const data = await response.json()

      // Store tokens and user data
      TokenStorage.setTokens(data.access_token, data.refresh_token)
      const transformedUser = transformUserData(data.user)
      TokenStorage.setUser(transformedUser)
      setUser(transformedUser)
    } catch (error) {
      console.error('Login error:', error)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async () => {
    try {
      const refreshTokenValue = TokenStorage.getRefreshToken()

      if (refreshTokenValue) {
        // Call backend logout endpoint
        await authenticatedApiRequest('/auth/logout', {
          method: 'POST',
          body: JSON.stringify({ refresh_token: refreshTokenValue }),
        })
      }
    } catch (error) {
      console.error('Logout error:', error)
      // Continue with logout even if backend call fails
    } finally {
      // Clear local storage and state
      TokenStorage.clearAll()
      setUser(null)
    }
  }

  const value: AuthContextType = {
    user,
    isLoading,
    isRefreshing,
    isAuthenticated: !!user,
    login,
    logout,
    refreshToken,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

// Hook to get the current access token
export function useAccessToken() {
  return TokenStorage.getAccessToken()
}

// Export token storage for use in API client
export { TokenStorage, authenticatedApiRequest }
```

Adding the smart window focus handler:

```typescriptreact
'use client'

import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react'
import { User, LoginRequest } from '@/types'
import { authApi } from '@/lib/api'
import { getApiBaseUrl } from '@/lib/api-url'
import { useActivityDetection } from '@/hooks/use-activity-detection'

// Transform backend user data (snake_case) to frontend format (camelCase)
function transformUserData(backendUser: any): User {
  return {
    id: backendUser.id,
    name: backendUser.name,
    email: backendUser.email,
    isAdmin: backendUser.is_admin,
    createdAt: backendUser.created_at,
    updatedAt: backendUser.updated_at
  }
}

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isRefreshing: boolean
  isAuthenticated: boolean
  login: (credentials: LoginRequest) => Promise<void>
  logout: () => Promise<void>
  refreshToken: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

// Token storage utilities
const TOKEN_KEYS = {
  ACCESS_TOKEN: 'labcastarr_access_token',
  REFRESH_TOKEN: 'labcastarr_refresh_token',
  USER: 'labcastarr_user'
}

class TokenStorage {
  static setTokens(accessToken: string, refreshToken: string) {
    if (typeof window !== 'undefined') {
      localStorage.setItem(TOKEN_KEYS.ACCESS_TOKEN, accessToken)
      localStorage.setItem(TOKEN_KEYS.REFRESH_TOKEN, refreshToken)
    }
  }

  static getAccessToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem(TOKEN_KEYS.ACCESS_TOKEN)
    }
    return null
  }

  static getRefreshToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem(TOKEN_KEYS.REFRESH_TOKEN)
    }
    return null
  }

  static setUser(user: User) {
    if (typeof window !== 'undefined') {
      localStorage.setItem(TOKEN_KEYS.USER, JSON.stringify(user))
    }
  }

  static getUser(): User | null {
    if (typeof window !== 'undefined') {
      const userData = localStorage.getItem(TOKEN_KEYS.USER)
      return userData ? JSON.parse(userData) : null
    }
    return null
  }

  static clearAll() {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(TOKEN_KEYS.ACCESS_TOKEN)
      localStorage.removeItem(TOKEN_KEYS.REFRESH_TOKEN)
      localStorage.removeItem(TOKEN_KEYS.USER)
    }
  }

  static hasValidTokens(): boolean {
    const accessToken = this.getAccessToken()
    const refreshToken = this.getRefreshToken()
    return !!(accessToken && refreshToken)
  }

  static isAccessTokenExpired(): boolean {
    const token = this.getAccessToken()
    if (!token) return true

    try {
      // Decode JWT payload without verification (just read exp claim)
      const payload = JSON.parse(atob(token.split('.')[1]))
      const exp = payload.exp * 1000 // Convert to milliseconds
      const bufferMs = 5 * 60 * 1000 // 5 minutes buffer
      return Date.now() >= (exp - bufferMs)
    } catch {
      return true // If we can't parse, consider expired
    }
  }

  static isRefreshTokenExpired(): boolean {
    const token = this.getRefreshToken()
    if (!token) return true

    try {
      // Decode JWT payload without verification (just read exp claim)
      const payload = JSON.parse(atob(token.split('.')[1]))
      const exp = payload.exp * 1000 // Convert to milliseconds
      return Date.now() >= exp
    } catch {
      return true // If we can't parse, consider expired
    }
  }
}

// Custom API request function that includes JWT token
async function authenticatedApiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const accessToken = TokenStorage.getAccessToken()

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
    ...options.headers,
  }

  // Add Authorization header if we have an access token
  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`
  }

  const API_BASE_URL = getApiBaseUrl()
  const response = await fetch(`${API_BASE_URL}/v1${endpoint}`, {
    ...options,
    headers,
    credentials: 'same-origin',
  })

  if (!response.ok) {
    let errorData
    try {
      errorData = await response.json()
    } catch {
      errorData = { message: `HTTP ${response.status}: ${response.statusText}` }
    }
    throw new Error(errorData.message || `HTTP error! status: ${response.status}`)
  }

  const contentType = response.headers.get('content-type')
  if (contentType && contentType.includes('application/json')) {
    return response.json()
  }

  return response.text() as unknown as T
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)

  // Memoized refresh function for activity detection
  const refreshToken = useCallback(async () => {
    try {
      setIsRefreshing(true)
      const refreshTokenValue = TokenStorage.getRefreshToken()

      if (!refreshTokenValue) {
        throw new Error('No refresh token available')
      }

      const response = await fetch(`${getApiBaseUrl()}/v1/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
        },
        body: JSON.stringify({ refresh_token: refreshTokenValue }),
      })

      if (!response.ok) {
        throw new Error('Token refresh failed')
      }

      const data = await response.json()

      // Update stored tokens - use new refresh token if provided, otherwise keep existing (backward compatibility)
      const newRefreshToken = data.refresh_token || refreshTokenValue
      TokenStorage.setTokens(data.access_token, newRefreshToken)

      // Log token rotation for debugging
      if (data.refresh_token) {
        console.debug('Token rotated: new refresh token received')
      }
    } catch (error) {
      console.error('Token refresh error:', error)
      throw error
    } finally {
      setIsRefreshing(false)
    }
  }, [])

  // Activity-based token refresh (every 5 minutes of activity)
  useActivityDetection(
    user ? refreshToken : undefined,
    5 * 60 * 1000 // Refresh on activity every 5 minutes
  )

  // Check for existing auth on mount
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        // Check if we have stored tokens
        if (!TokenStorage.hasValidTokens()) {
          setIsLoading(false)
          return
        }

        const refreshTokenValue = TokenStorage.getRefreshToken()

        // CRITICAL: Refresh token BEFORE validation if refresh token exists
        // This allows inactive users to return after hours/days and stay logged in
        if (refreshTokenValue) {
          try {
            await refreshToken()
          } catch (refreshError) {
            // Refresh failed - refresh token expired or invalid
            console.error('Token refresh failed on initialization:', refreshError)
            TokenStorage.clearAll()
            setIsLoading(false)
            return
          }
        }

        // Now validate with fresh access token
        const backendUser = await authenticatedApiRequest<any>('/auth/me')
        const currentUser = transformUserData(backendUser)
        setUser(currentUser)
        TokenStorage.setUser(currentUser)
      } catch (error) {
        console.error('Failed to initialize auth:', error)
        // Clear invalid tokens
        TokenStorage.clearAll()
      } finally {
        setIsLoading(false)
      }
    }

    initializeAuth()
  }, [refreshToken])

  // Auto-refresh token functionality
  // Refresh at 80% of token lifetime (60 min * 0.8 = 48 min)
  useEffect(() => {
    if (!user) return

    const TOKEN_LIFETIME_MINUTES = 60 // Should match backend jwt_access_token_expire_minutes
    const REFRESH_PERCENTAGE = 0.8 // Refresh at 80% of token lifetime
    const refreshIntervalMs = TOKEN_LIFETIME_MINUTES * REFRESH_PERCENTAGE * 60 * 1000

    const refreshInterval = setInterval(async () => {
      try {
        await refreshToken()
      } catch (error) {
        console.error('Auto-refresh failed:', error)
        // If refresh fails, log out the user
        await logout()
      }
    }, refreshIntervalMs) // Refresh every 48 minutes (access token expires in 60)

    return () => clearInterval(refreshInterval)
  }, [user, refreshToken])

  // Smart window focus handler - refreshes token when user returns to tab
  // Only refreshes if token is expired/expiring soon, prevents excessive refreshes
  useEffect(() => {
    if (!user) return

    let lastFocusRefresh = 0
    const MIN_FOCUS_REFRESH_INTERVAL = 5 * 60 * 1000 // 5 minutes

    const handleFocus = async () => {
      // Only refresh if enough time has passed since last focus refresh
      const now = Date.now()
      if (now - lastFocusRefresh < MIN_FOCUS_REFRESH_INTERVAL) {
        return
      }

      // Only refresh if token is expired or expiring soon
      if (!TokenStorage.hasValidTokens() || !TokenStorage.isAccessTokenExpired()) {
        return
      }

      try {
        await refreshToken()
        lastFocusRefresh = now
      } catch (error) {
        // Refresh failed, but don't log out immediately
        // Let the next API call or initialization handle it
        console.warn('Focus refresh failed:', error)
      }
    }

    window.addEventListener('focus', handleFocus)
    return () => window.removeEventListener('focus', handleFocus)
  }, [user, refreshToken])

  // REMOVED: Window focus refresh was too aggressive
  // This was triggering refreshes on every click between DevTools and page,
  // causing state loss and poor UX. The auto-refresh timer (every 48 min) is sufficient.
  //
  // useEffect(() => {
  //   const handleFocus = async () => {
  //     if (user && TokenStorage.hasValidTokens()) {
  //       try {
  //         await refreshToken()
  //       } catch (error) {
  //         console.error('Focus refresh failed:', error)
  //         await logout()
  //       }
  //     }
  //   }
  //
  //   window.addEventListener('focus', handleFocus)
  //   return () => window.removeEventListener('focus', handleFocus)
  // }, [user])

  const login = async (credentials: LoginRequest) => {
    try {
      setIsLoading(true)

      // Call backend login endpoint directly
      const apiUrl = getApiBaseUrl()
      console.log('Login API URL:', apiUrl) // Debug logging for Safari troubleshooting

      const response = await fetch(`${apiUrl}/v1/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
        },
        body: JSON.stringify(credentials),
      })

      if (!response.ok) {
        const errorData = await response.json()

        // Handle different error formats
        let errorMessage = 'Login failed'
        if (typeof errorData.detail === 'string') {
          errorMessage = errorData.detail
        } else if (Array.isArray(errorData.detail)) {
          // Handle FastAPI validation errors (array format)
          errorMessage = errorData.detail.map((err: any) => err.msg).join(', ')
        } else if (errorData.message) {
          errorMessage = errorData.message
        }

        throw new Error(errorMessage)
      }

      const data = await response.json()

      // Store tokens and user data
      TokenStorage.setTokens(data.access_token, data.refresh_token)
      const transformedUser = transformUserData(data.user)
      TokenStorage.setUser(transformedUser)
      setUser(transformedUser)
    } catch (error) {
      console.error('Login error:', error)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async () => {
    try {
      const refreshTokenValue = TokenStorage.getRefreshToken()

      if (refreshTokenValue) {
        // Call backend logout endpoint
        await authenticatedApiRequest('/auth/logout', {
          method: 'POST',
          body: JSON.stringify({ refresh_token: refreshTokenValue }),
        })
      }
    } catch (error) {
      console.error('Logout error:', error)
      // Continue with logout even if backend call fails
    } finally {
      // Clear local storage and state
      TokenStorage.clearAll()
      setUser(null)
    }
  }

  const value: AuthContextType = {
    user,
    isLoading,
    isRefreshing,
    isAuthenticated: !!user,
    login,
    logout,
    refreshToken,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

// Hook to get the current access token
export function useAccessToken() {
  return TokenStorage.getAccessToken()
}

// Export token storage for use in API client
export { TokenStorage, authenticatedApiRequest }
```

Adding mousedown and click events to activity detection:

```typescript
import { useEffect, useRef, useCallback } from "react"

/**
 * Activity detection events to monitor
 *
 * Events that indicate user engagement:
 * - keypress: User is actively typing/interacting
 * - scroll: User is reading/browsing content
 * - touchstart: Mobile user is interacting with UI
 * - mousedown: User is clicking (more reliable than click)
 * - click: User is clicking buttons/links
 *
 * Note: mousemove is intentionally excluded as it's too noisy
 */
const ACTIVITY_EVENTS = [
  "keypress",
  "scroll",
  "touchstart",
  "mousedown",
  "click",
] as const

/**
 * Hook to detect user activity and trigger callbacks
 *
 * @param onActivity - Callback function to execute when activity is detected
 * @param debounceMs - Minimum time between activity callbacks (default: 60000ms = 1 minute)
 * @returns Object with isActive state and manual trigger function
 */
export function useActivityDetection(
  onActivity?: () => void,
  debounceMs: number = 60000
) {
  const lastActivityRef = useRef<number>(Date.now())
  const timeoutRef = useRef<NodeJS.Timeout>()

  const handleActivity = useCallback(() => {
    const now = Date.now()
    const timeSinceLastActivity = now - lastActivityRef.current

    // Only trigger if enough time has passed since last activity
    if (timeSinceLastActivity >= debounceMs) {
      lastActivityRef.current = now
      onActivity?.()
    }

    // Clear existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }

    // Set new timeout to detect inactivity
    timeoutRef.current = setTimeout(() => {
      // User is inactive
    }, debounceMs)
  }, [onActivity, debounceMs])

  useEffect(() => {
    // Add event listeners for activity detection
    ACTIVITY_EVENTS.forEach((event) => {
      window.addEventListener(event, handleActivity, { passive: true })
    })

    // Cleanup
    return () => {
      ACTIVITY_EVENTS.forEach((event) => {
        window.removeEventListener(event, handleActivity)
      })
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [handleActivity])

  return {
    manualTrigger: handleActivity,
  }
}
```

Reviewing the apiRequest function to ensure the async flow is correct:

Checking for lint errors and verifying the implementation:

All implementation tasks are complete. Summary:

## Implementation Summary

### Backend Changes (Solution 2: Refresh Token Rotation)

1. Updated `RefreshTokenResponse` schema to include optional `refresh_token` field
2. Modified `refresh_token` endpoint to:
   - Extract `remember_me` claim from existing refresh token
   - Create new refresh token with same claims
   - Use extended expiration (90 days) if `remember_me=True`
   - Return new refresh token in response

### Frontend Changes

**Solution 4: Token Expiration Check Utilities**

- Added `isAccessTokenExpired()` and `isRefreshTokenExpired()` methods to `TokenStorage` class
- Added `isAccessTokenExpired()` helper in `api.ts` for proactive refresh

**Solution 2: Refresh Token Rotation (Frontend)**

- Added `RefreshTokenResponse` interface to types
- Updated `refreshToken()` in auth-context to store new refresh token
- Updated `performTokenRefresh()` in api.ts to store new refresh token
- Both handle backward compatibility (keep existing token if backend doesn't return new one)

**Solution 4: Proactive Refresh in API Calls**

- Integrated expiration check in `apiRequest()` function
- Proactively refreshes token before API calls if expired/expiring soon

**Solution 3: Pre-Validation Refresh (CRITICAL)**

- Modified `initializeAuth()` to refresh token BEFORE `/auth/me` validation
- Allows inactive users to return after hours/days and stay logged in
- Added proper error handling for refresh failures

**Solution 6: Smart Window Focus Handler**

- Added window focus handler that refreshes token when user returns to tab
- Only refreshes if token is expired/expiring soon
- Prevents excessive refreshes with 5-minute minimum interval
- Handles errors gracefully (doesn't log out immediately)

**Solution 5: Improved Activity Detection**

- Added `mousedown` and `click` events to activity detection
- Better captures user interactions for token refresh

## Expected Behavior

- Inactive users: Can close browser and return after hours/days and stay logged in (if refresh token valid)
- Active users: Tokens refresh automatically during activity
- Tab switching: Token refreshes when returning to tab if expired
- API calls: Proactive refresh prevents 401 errors
- Long sessions: Refresh token rotation extends session lifetime with regular activity

All changes maintain backward compatibility and include error handling. The implementation follows the plan and addresses the login persistence issues.
