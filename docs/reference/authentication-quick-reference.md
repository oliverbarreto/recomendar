# Authentication System - Quick Reference Guide

## 🚀 Quick Start

### Login Flow
```typescript
import { useAuth } from '@/contexts/auth-context'

function LoginComponent() {
  const { login, isLoading } = useAuth()
  
  const handleLogin = async () => {
    await login({ 
      email: 'user@example.com', 
      password: 'password' 
    })
    // User is automatically redirected
  }
}
```

### Protected Routes
```typescript
import { useAuth } from '@/contexts/auth-context'

function ProtectedPage() {
  const { user, isAuthenticated } = useAuth()
  
  if (!isAuthenticated) {
    return null // AuthGuard handles redirect
  }
  
  return <div>Welcome {user?.name}</div>
}
```

### Manual Token Refresh
```typescript
const { refreshToken } = useAuth()

// Manually trigger token refresh
await refreshToken()
```

## 🔧 Configuration

### Backend Settings
```python
# backend/app/core/config.py

# Token expiration times
jwt_access_token_expire_minutes: int = 60  # 1 hour
jwt_refresh_token_expire_days: int = 30    # 30 days
```

### Frontend Settings
```typescript
// frontend/src/contexts/auth-context.tsx

const TOKEN_LIFETIME_MINUTES = 60     // Must match backend
const REFRESH_PERCENTAGE = 0.8         // Refresh at 80% lifetime
const ACTIVITY_REFRESH_MS = 5 * 60 * 1000  // 5 minutes
```

## 📡 API Endpoints

### Authentication Endpoints

#### Login
```bash
POST /v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "remember_me": true
}

# Response
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "name": "John Doe",
    "email": "user@example.com",
    "is_admin": false
  }
}
```

#### Refresh Token
```bash
POST /v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ..."
}

# Response
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### Sliding Token Refresh (Activity-Based)
```bash
POST /v1/auth/refresh-sliding
Authorization: Bearer eyJ...

# Response
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### Logout
```bash
POST /v1/auth/logout
Authorization: Bearer eyJ...
Content-Type: application/json

{
  "refresh_token": "eyJ..."
}

# Response
{
  "message": "Successfully logged out",
  "tokens_invalidated": 2
}
```

#### Get Current User
```bash
GET /v1/auth/me
Authorization: Bearer eyJ...

# Response
{
  "id": 1,
  "name": "John Doe",
  "email": "user@example.com",
  "is_admin": false,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

## 🔑 Token Management

### Token Storage
```typescript
// Tokens are stored in localStorage
localStorage.getItem('labcastarr_access_token')
localStorage.getItem('labcastarr_refresh_token')
localStorage.getItem('labcastarr_user')
```

### Token Structure
```typescript
// Access Token Payload (Sliding)
{
  "sub": "1",              // User ID (string)
  "email": "user@example.com",
  "is_admin": false,
  "jti": "1_1729180800.123",  // Unique token ID
  "iat": 1729180800,       // Issued at
  "exp": 1729184400,       // Expires at
  "type": "access",
  "sliding": true          // Sliding token flag
}

// Refresh Token Payload
{
  "sub": "1",
  "email": "user@example.com",
  "is_admin": false,
  "iat": 1729180800,
  "exp": 1731772800,       // Expires after 30 days
  "type": "refresh"
}
```

## 🛡️ Authentication Hooks

### useAuth()
```typescript
const {
  user,              // Current user object or null
  isLoading,         // Initial authentication loading
  isRefreshing,      // Token refresh in progress
  isAuthenticated,   // Boolean authentication status
  login,             // Login function
  logout,            // Logout function
  refreshToken       // Manual refresh function
} = useAuth()
```

### useAccessToken()
```typescript
import { useAccessToken } from '@/contexts/auth-context'

const accessToken = useAccessToken()
// Returns current access token or null
```

## 🔄 Refresh Strategies

### 1. Automatic Time-Based Refresh
- Triggers every 48 minutes (80% of 60-minute token lifetime)
- Prevents token expiration during normal usage
- Background operation, no user interaction required

### 2. Activity-Based Refresh
- Triggers on user activity every 5 minutes
- Monitors: mouse, keyboard, touch, scroll events
- Keeps sessions alive indefinitely for active users

### 3. Window Focus Refresh
- Triggers when user returns to the application
- Ensures token is fresh when user re-engages
- Handles long-idle scenarios

### 4. On-Demand Refresh (API-Triggered)
- Automatic on 401 Unauthorized responses
- Retries original request with new token
- Prevents duplicate refresh requests

## 🎯 Common Use Cases

### Check Authentication Status
```typescript
const { isAuthenticated, user } = useAuth()

if (isAuthenticated) {
  console.log('User is logged in:', user?.email)
} else {
  console.log('User is not logged in')
}
```

### Redirect After Login
```typescript
const router = useRouter()
const { login } = useAuth()

await login(credentials)
router.push('/dashboard')
```

### Logout and Redirect
```typescript
const { logout } = useAuth()
const router = useRouter()

await logout()
router.push('/login')
```

### Protected API Call
```typescript
import { authenticatedApiRequest } from '@/contexts/auth-context'

// Automatically includes Authorization header
const data = await authenticatedApiRequest('/api/protected-endpoint')
```

## 🐛 Troubleshooting

### Issue: "Token expired" errors
**Solution:** Check token expiration settings match between frontend and backend

### Issue: Login form flickers
**Solution:** Ensure `isLoading` and `isRefreshing` states are properly displayed

### Issue: Session expires too quickly
**Solution:** Increase `jwt_access_token_expire_minutes` in backend config

### Issue: Multiple refresh requests
**Solution:** Verify refresh promise caching is working in `api.ts`

### Issue: Activity-based refresh not working
**Solution:** Check `useActivityDetection` hook is properly configured

## 📊 Monitoring

### Key Metrics to Track
- Token refresh success rate
- Average session duration
- Login success/failure rate
- Token expiration frequency
- Refresh request count

### Logging
```typescript
// Frontend console logs
console.log('Login API URL:', apiUrl)
console.error('Login error:', error)
console.error('Token refresh error:', error)

// Backend logs (via EventService)
await event_service.log_user_action(
  action="login",
  message=f"User {user.email} logged in successfully"
)
```

## 🔐 Security Best Practices

1. **Always use HTTPS** - Tokens in localStorage require secure connection
2. **Set strong JWT secret** - Change from default in production
3. **Monitor failed login attempts** - Track via EventService
4. **Regular token rotation** - Automatic via refresh mechanism
5. **Logout on sensitive actions** - Force re-authentication for critical operations

## 📚 Additional Resources

- [Full Implementation Documentation](../tasks/task-0037-bugfix-api-changes-improve-token-refresh-implementation.md)
- [JWT Configuration Guide](./jwt-configuration.md)
- [Security Best Practices](./security.md)

---

**Last Updated:** October 17, 2025  
**Version:** 1.0.0

