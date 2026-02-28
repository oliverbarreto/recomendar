# Task: Remove Hardcoded Domain References

**Status**: ✅ COMPLETED
**Date**: 2025-10-02
**Priority**: High
**Category**: Security, Configuration, Refactoring

## Objective

Remove all hardcoded domain references to `labcastarr.oliverbarreto.com` and `labcastarr-api.oliverbarreto.com` from the codebase and replace them with environment variable-driven configuration.

## Problem Statement

The codebase contained hardcoded references to a personal domain (`*.oliverbarreto.com`) in 9 different files across both backend and frontend. This created several issues:

1. **Security Risk**: Personal domain exposure in public codebase
2. **Deployment Inflexibility**: Hard to deploy to different environments
3. **Community Edition Issue**: Makes the project unsuitable for other users
4. **Maintenance Burden**: Changes require code modifications instead of config updates

## Files Modified

### Backend (2 files)
1. ✅ `backend/app/core/config.py`
   - Removed hardcoded `labcastarr-api.oliverbarreto.com` from `allowed_hosts` default
   - Removed hardcoded `https://labcastarr.oliverbarreto.com` from `cors_origins` default

2. ✅ `backend/app/infrastructure/services/feed_generation_service_impl.py`
   - Removed hardcoded fallback URL `https://labcastarr-api.oliverbarreto.com`
   - Now uses `settings.base_url` from configuration with proper logging

### Frontend (7 files)
3. ✅ `frontend/src/lib/api-url.ts` (NEW FILE)
   - Created centralized API URL resolution utility
   - Single source of truth for all API URL determination
   - Smart fallback logic with environment variable support

4. ✅ `frontend/src/lib/api-client.ts`
   - Replaced hardcoded URL logic with centralized utility import
   - Simplified constructor to use `getApiBaseUrl()`

5. ✅ `frontend/src/lib/api.ts`
   - Replaced hardcoded URL logic with centralized utility import
   - Added automatic API config logging on initialization

6. ✅ `frontend/src/contexts/auth-context.tsx`
   - Removed 3 instances of inline `getApiBaseUrl()` functions
   - Imported and used centralized utility

7. ✅ `frontend/src/components/features/channel-dashboard.tsx`
   - Removed inline API URL resolution logic
   - Imported and used centralized utility

8. ✅ `frontend/src/components/features/episodes/episode-detail.tsx`
   - Removed inline API URL resolution logic
   - Imported and used centralized utility

9. ✅ `frontend/src/components/features/episodes/episode-grid.tsx`
   - Removed inline API URL resolution logic
   - Imported and used centralized utility

### Configuration Files (4 files)
10. ✅ `.env.production`
    - Added `NEXT_PUBLIC_FALLBACK_API_URL`
    - Added `ALLOWED_HOSTS`

11. ✅ `.env.development`
    - Added `NEXT_PUBLIC_FALLBACK_API_URL`
    - Added `ALLOWED_HOSTS`

12. ✅ `.env.production.example`
    - Added `NEXT_PUBLIC_FALLBACK_API_URL`
    - Added `ALLOWED_HOSTS`
    - Updated with generic domain examples

13. ✅ `.env.development.example`
    - Added `NEXT_PUBLIC_FALLBACK_API_URL`
    - Added `ALLOWED_HOSTS`

### Documentation (1 file)
14. ✅ `CLAUDE.md`
    - Updated environment configuration section with new variables
    - Changed production access points to use generic configuration examples
    - Improved documentation for deployment flexibility

## New Environment Variables

### Frontend
- `NEXT_PUBLIC_FALLBACK_API_URL`: Optional fallback API URL for HTTPS contexts when `NEXT_PUBLIC_API_URL` is not set

### Backend
- `ALLOWED_HOSTS`: JSON array of allowed backend hostnames (can override defaults)

## Implementation Details

### Centralized API URL Utility (`frontend/src/lib/api-url.ts`)

The new utility provides:
- **Priority-based resolution**: Environment variable → Fallback for HTTPS → localhost default
- **Mixed content prevention**: Automatic HTTPS API calls in HTTPS contexts
- **Debug logging**: `logApiConfig()` helper for troubleshooting
- **Type safety**: Full TypeScript support with proper typing

```typescript
export const getApiBaseUrl = (): string => {
  // 1. Use explicit environment variable if available
  const envApiUrl = process.env.NEXT_PUBLIC_API_URL
  if (envApiUrl) return envApiUrl

  // 2. Mixed content prevention for HTTPS contexts
  if (typeof window !== 'undefined' && window.location.protocol === 'https:') {
    const fallbackUrl = process.env.NEXT_PUBLIC_FALLBACK_API_URL
    if (fallbackUrl) return fallbackUrl
    // Warning logged if no fallback configured
  }

  // 3. Default to localhost for development
  return 'http://localhost:8000'
}
```

### Benefits of This Approach

1. **Single Source of Truth**: All API URL logic in one place
2. **Easy Maintenance**: Changes to URL logic only need to be made once
3. **Deployment Flexibility**: Different deployments can use different URLs via env vars
4. **Security**: No personal domains exposed in code
5. **Community Friendly**: Works for any deployment without code changes
6. **Backward Compatible**: Maintains existing smart fallback behavior

## Verification

Ran comprehensive search to verify all hardcoded references removed:
```bash
grep -r "oliverbarreto.com" backend/app frontend/src --exclude-dir=node_modules --exclude-dir=__pycache__
```
**Result**: No hardcoded domain references found! ✅

## Testing Recommendations

1. **Local Development**
   - Verify frontend connects to `http://localhost:8000`
   - Check console logs show correct API URL resolution
   - Test all API calls (episodes, channels, auth, etc.)

2. **Production Deployment**
   - Set `NEXT_PUBLIC_API_URL` to production API URL
   - Set `NEXT_PUBLIC_FALLBACK_API_URL` to same URL
   - Set `ALLOWED_HOSTS` to include production domain
   - Verify no mixed content warnings in browser console
   - Test all API endpoints

3. **HTTPS/HTTP Contexts**
   - Test that HTTPS pages use HTTPS API URLs
   - Test that HTTP pages use HTTP API URLs
   - Verify mixed content prevention works correctly

## Migration Guide for Existing Deployments

If you have an existing deployment, update your `.env.production` file:

```bash
# Add these new variables to your .env.production
NEXT_PUBLIC_FALLBACK_API_URL=https://api.yourdomain.com
ALLOWED_HOSTS=["localhost","127.0.0.1","0.0.0.0","api.yourdomain.com"]
```

No code changes required! The application will automatically use your configured domains.

## Success Criteria

- ✅ All hardcoded domain references removed from codebase
- ✅ Centralized API URL utility created and implemented
- ✅ Environment configuration updated with new variables
- ✅ Documentation updated to reflect changes
- ✅ Example environment files updated
- ✅ Backend fallback logic uses settings instead of hardcoded URLs
- ✅ All frontend files use centralized utility
- ✅ Verification search confirms no remaining hardcoded references

## Notes

- The personal domain references remain in `.env.production` for your current deployment, but are now easily changeable
- Other users can simply update their environment files without touching code
- The application is now truly deployment-agnostic
- Mixed content security is maintained through smart fallback logic
- Debug logging helps troubleshoot environment-specific issues

## Related Tasks

- Task-0027: Create new Git repo CE edition (parent task)
- Future: Consider moving to a centralized configuration management system

---

**Implementation completed successfully!** The codebase is now free of hardcoded domain references and fully configurable via environment variables.
