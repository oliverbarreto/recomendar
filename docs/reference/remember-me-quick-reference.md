# "Remember Me" Functionality - Quick Reference

**Feature**: Extended session duration via "Remember me" checkbox  
**Version**: 1.0  
**Date**: October 18, 2025

---

## 🎯 Quick Overview

The "Remember me" checkbox on the login screen allows users to extend their session duration:

| Session Type | Refresh Token Duration | Use Case                            |
| ------------ | ---------------------- | ----------------------------------- |
| **Standard** | 30 days                | Regular login (checkbox unchecked)  |
| **Extended** | 90 days                | Long-term access (checkbox checked) |

**Note**: Access tokens remain 60 minutes for both session types.

---

## 🔧 Configuration

### Backend Configuration

**File**: `backend/app/core/config.py`

```python
# JWT Authentication settings
jwt_access_token_expire_minutes: int = 60  # Access token (60 minutes)
jwt_refresh_token_expire_days: int = 30  # Standard refresh token (30 days)
jwt_refresh_token_extended_expire_days: int = 90  # Extended refresh token (90 days)
```

### Environment Variables (Optional)

```bash
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30
JWT_REFRESH_TOKEN_EXTENDED_EXPIRE_DAYS=90
```

---

## 💻 API Usage

### Login Endpoint

**Endpoint**: `POST /v1/auth/login`

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "password123",
  "remember_me": true  // Optional, defaults to false
}
```

**Response**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "name": "User Name",
    "email": "user@example.com",
    "is_admin": false
  }
}
```

---

## 🎨 Frontend Usage

### TypeScript Interface

```typescript
interface LoginRequest {
  email: string
  password: string
  remember_me?: boolean  // Optional: Extend session to 90 days
}
```

### Login Example

```typescript
// Login with remember me
await login({ 
  email: 'user@example.com', 
  password: 'password123',
  remember_me: true  // 90-day session
})

// Login without remember me
await login({ 
  email: 'user@example.com', 
  password: 'password123',
  remember_me: false  // 30-day session (or omit the field)
})
```

---

## 🔍 Token Inspection

### Decode Token in Browser Console

```javascript
// Get refresh token from localStorage
const refreshToken = localStorage.getItem('labcastarr_refresh_token');

// Decode token (without verification)
function decodeJWT(token) {
  const base64Url = token.split('.')[1];
  const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
  const jsonPayload = decodeURIComponent(atob(base64).split('').map(c => 
    '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
  ).join(''));
  return JSON.parse(jsonPayload);
}

// Inspect token
const claims = decodeJWT(refreshToken);
console.log('Expires:', new Date(claims.exp * 1000));
console.log('Duration:', (claims.exp - claims.iat) / 86400, 'days');
console.log('Remember me:', claims.remember_me || false);
```

### Token Claims

**Access Token**:
```json
{
  "sub": "1",
  "email": "user@example.com",
  "is_admin": false,
  "jti": "1_1729241837.123456",
  "exp": 1729245437,
  "iat": 1729241837,
  "type": "access",
  "sliding": true
}
```

**Refresh Token** (with remember_me):
```json
{
  "sub": "1",
  "email": "user@example.com",
  "is_admin": false,
  "remember_me": true,
  "exp": 1737017837,
  "iat": 1729241837,
  "type": "refresh"
}
```

---

## 🧪 Testing

### cURL Examples

**Standard Login (30 days)**:
```bash
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "remember_me": false
  }'
```

**Extended Login (90 days)**:
```bash
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "remember_me": true
  }'
```

### Automated Test Script

```bash
python3 scripts/test_remember_me.py
```

---

## 🔒 Security Notes

### Token Lifetimes
- **Access Token**: 60 minutes (short-lived for security)
- **Refresh Token**: 30 or 90 days (based on remember_me)

### Security Best Practices
- ✅ Access tokens expire frequently (60 min)
- ✅ Refresh tokens stored in localStorage
- ✅ HTTPS required in production
- ✅ JWT signatures verified on all requests
- ✅ Token blacklisting supported
- ✅ Users can logout to invalidate tokens

---

## 🐛 Troubleshooting

### Issue: Login returns "Invalid email or password"
**Solution**: Verify credentials match environment configuration

### Issue: Token expires too quickly
**Solution**: Check `jwt_access_token_expire_minutes` configuration

### Issue: Remember me not working
**Solution**: 
1. Verify `remember_me` parameter is being sent
2. Check backend logs for errors
3. Inspect token claims to verify expiration

### Issue: Import error in JWT service
**Solution**: Ensure correct import: `from .config import settings` (not `get_settings`)

---

## 📊 Token Duration Calculation

```python
# Standard session
refresh_token_expire = 30 days = 2,592,000 seconds

# Extended session (remember me)
refresh_token_expire = 90 days = 7,776,000 seconds

# Access token (both)
access_token_expire = 60 minutes = 3,600 seconds
```

---

## 🔄 Token Refresh Flow

```
User Activity
    ↓
Auto-refresh every 48 minutes
    ↓
POST /v1/auth/refresh
    ↓
New access token (60 min)
    ↓
Continue session
    ↓
Repeat until refresh token expires
```

---

## 📝 Code Examples

### Backend: Create Token Pair

```python
from app.core.jwt import get_jwt_service

jwt_service = get_jwt_service()

# Create extended session
tokens = jwt_service.create_token_pair(
    user_id=1,
    additional_claims={"email": "user@example.com"},
    remember_me=True  # 90-day refresh token
)

# Create standard session
tokens = jwt_service.create_token_pair(
    user_id=1,
    additional_claims={"email": "user@example.com"},
    remember_me=False  # 30-day refresh token
)
```

### Frontend: Login Component

```typescript
const handleLogin = async () => {
  try {
    await login({
      email,
      password,
      remember_me: rememberMe  // From checkbox state
    })
    router.push('/')
  } catch (error) {
    console.error('Login failed:', error)
  }
}
```

---

## 📚 Related Documentation

- [Implementation Details](../tasks/task-0038-remember-me-implementation.md)
- [Test Results](../tasks/task-0038-remember-me-test-results.md)
- [Authentication Quick Reference](./authentication-quick-reference.md)

---

## ⚡ Quick Commands

```bash
# Restart backend to apply config changes
docker-compose restart backend-dev

# Check backend logs
docker-compose logs backend-dev --tail 50

# Test login endpoint
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"pass","remember_me":true}'

# Run automated tests
python3 scripts/test_remember_me.py
```

---

**Last Updated**: October 18, 2025  
**Version**: 1.0  
**Maintainer**: Development Team

