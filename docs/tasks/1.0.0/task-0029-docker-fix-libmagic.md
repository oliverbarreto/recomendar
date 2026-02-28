# Docker Development Environment - libmagic Fix

## Issue

When starting the development environment with Docker Compose, the backend container was failing with the following error:

```
ImportError: failed to find libmagic.  Check your installation
```

This error occurred because the `python-magic` library requires the system library `libmagic1` to be installed, but it was missing from the Docker container.

## Root Cause

The file upload feature implementation added `python-magic` as a dependency for MIME type detection, but the corresponding system library (`libmagic1`) was not installed in the Docker image.

## Solution

Updated the backend `Dockerfile` to install `libmagic1` alongside other system dependencies:

**File**: `backend/Dockerfile`

```dockerfile
# Before:
RUN apt-get update && apt-get install -y curl ffmpeg && rm -rf /var/lib/apt/lists/*

# After:
RUN apt-get update && apt-get install -y curl ffmpeg libmagic1 && rm -rf /var/lib/apt/lists/*
```

## Verification

1. **Rebuilt the Docker image**:
   ```bash
   cd "/Users/oliver/Library/Mobile Documents/com~apple~CloudDocs/dev/webaps/labcastarr"
   docker compose -f docker-compose.dev.yml down
   docker compose --env-file .env.development -f docker-compose.dev.yml build --no-cache backend-dev
   ```

2. **Started the containers**:
   ```bash
   docker compose --env-file .env.development -f docker-compose.dev.yml up -d
   ```

3. **Verified backend is running**:
   ```bash
   docker logs labcastarr-dev-backend-dev-1
   # No libmagic errors in logs
   
   curl -sL http://localhost:8000/health
   # Response: {"status":"healthy","service":"LabCastARR API","version":"0.1.0","timestamp":"..."}
   ```

4. **Verified frontend is running**:
   ```bash
   docker logs labcastarr-dev-frontend-dev-1
   # Next.js running on http://localhost:3000
   ```

## Status

✅ **FIXED** - Both backend and frontend containers are running successfully in development environment.

## Related Files

- `backend/Dockerfile` - Updated to include `libmagic1`
- `backend/app/infrastructure/services/media_file_service.py` - Uses `python-magic` for MIME type detection
- `backend/app/application/services/upload_processing_service.py` - Uses media file service for upload processing

## Testing

The fix was tested by:
1. Building the Docker image from scratch (no cache)
2. Starting the development environment
3. Verifying no import errors in backend logs
4. Testing the health endpoint
5. Confirming both containers are healthy

## Notes

- This fix is required for both development and production Docker environments
- The same `Dockerfile` is used for both environments, so the fix applies to both
- `libmagic1` is a small library (~100KB) and adds minimal overhead to the image
- This dependency is essential for the file upload feature to work correctly

---

**Fixed by**: AI Assistant  
**Date**: October 18, 2025  
**Related Task**: task-0029-upload-episode-plan-v2.md




