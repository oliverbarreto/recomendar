# Task 0029 - Upload Episode Feature: Audio Playback Fix

**Date**: October 19, 2025  
**Status**: 🔧 IN PROGRESS  
**Priority**: HIGH

## Problem Summary

Uploaded episodes are created successfully and files are stored correctly in the backend, but audio playback fails in the browser with the error:
```
NotSupportedError: Failed to load because no supported source was found.
```

### Root Cause Analysis

1. **Frontend Type Mismatch**: The `Episode` interface defines `video_id: string` (required), but uploaded episodes return `video_id: null` from the backend.

2. **Audio URL Generation Logic**: The `getEpisodeAudioUrl()` method in `api-client.ts` checks for `video_id` existence. When `video_id` is `null` (uploaded episodes), it falls back to the deprecated integer ID endpoint.

3. **Component Implementation Issue**: The `audio-player.tsx` component passes `episode.id` (integer) instead of the full `episode` object to `getEpisodeAudioUrl()`, triggering the deprecated fallback path.

4. **Backend Endpoint Mismatch**: The frontend tries to use `/by-video-id/` endpoint for all episodes, but uploaded episodes don't have a `video_id`, causing the audio source to fail.

### Evidence
- ✅ Episode creation works
- ✅ File upload and storage works
- ✅ File deletion works
- ❌ Audio playback fails with "no supported source" error
- ⚠️ Console shows: "DEPRECATED: Using integer ID for audio URL"

---

## Implementation Plan

### Phase 1: Fix TypeScript Type Definitions

#### Task 1.1: Update Episode Interface
**File**: `frontend/src/types/index.ts`

**Current**:
```typescript
export interface Episode {
  id: number
  channel_id: number
  video_id: string  // ❌ Required, but uploaded episodes have null
  // ...
}
```

**Change to**:
```typescript
export interface Episode {
  id: number
  channel_id: number
  video_id: string | null  // ✅ Optional for uploaded episodes
  // ...
}
```

**Verification**: Run TypeScript compiler to check for type errors
```bash
cd frontend && npm run build
```

---

### Phase 2: Fix Frontend Audio URL Generation

#### Task 2.1: Update API Client Logic
**File**: `frontend/src/lib/api-client.ts`

**Current Logic** (lines 154-165):
```typescript
getEpisodeAudioUrl(episodeOrId: Episode | number): string {
  if (typeof episodeOrId === 'object' && episodeOrId.video_id) {
    // Uses /by-video-id/ endpoint
  }
  // Falls back to deprecated integer ID endpoint
}
```

**Change to**:
```typescript
getEpisodeAudioUrl(episodeOrId: Episode | number): string {
  // If Episode object is passed
  if (typeof episodeOrId === 'object') {
    // For YouTube episodes with video_id, use permanent video_id-based URL
    if (episodeOrId.video_id) {
      const channelId = episodeOrId.channel_id || 1
      return `${this.baseUrl}/media/episodes/by-video-id/${episodeOrId.video_id}/audio?channel_id=${channelId}`
    }
    
    // For uploaded episodes (no video_id), use integer ID endpoint
    // This is the CORRECT approach for uploaded episodes
    return `${this.baseUrl}/media/episodes/${episodeOrId.id}/audio`
  }

  // Fallback for legacy integer ID calls (DEPRECATED for YouTube episodes only)
  console.warn('DEPRECATED: Using integer ID for audio URL. Please pass Episode object instead.')
  return `${this.baseUrl}/media/episodes/${episodeOrId}/audio`
}
```

**Rationale**: 
- YouTube episodes use permanent `video_id`-based URLs (cache-friendly)
- Uploaded episodes use integer ID endpoint (no video_id available)
- Both approaches are valid for their respective use cases

---

#### Task 2.2: Fix Audio Player Component
**File**: `frontend/src/components/features/episodes/audio-player.tsx`

**Current** (line 66):
```typescript
const audioUrl = apiClient.getEpisodeAudioUrl(episode.id)  // ❌ Passing integer
```

**Change to**:
```typescript
const audioUrl = apiClient.getEpisodeAudioUrl(episode)  // ✅ Passing Episode object
```

**Verification**: Check that the component receives the full episode object and passes it correctly.

---

#### Task 2.3: Fix Episode Detail Download Handler
**File**: `frontend/src/components/features/episodes/episode-detail.tsx`

**Current** (line 209):
```typescript
const downloadUrl = `${getApiBaseUrl()}/v1/media/episodes/by-video-id/${episode.video_id}/audio`
```

**Change to**:
```typescript
const handleDownloadAudio = () => {
  if (!episode || !episode.audio_file_path) {
    toast.error('Audio file not available')
    return
  }

  // Use video_id-based URL for YouTube episodes, integer ID for uploaded episodes
  const downloadUrl = episode.video_id
    ? `${getApiBaseUrl()}/v1/media/episodes/by-video-id/${episode.video_id}/audio`
    : `${getApiBaseUrl()}/v1/media/episodes/${episode.id}/audio`
    
  const link = document.createElement('a')
  link.href = downloadUrl
  link.download = `${episode.title}.mp3`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}
```

---

### Phase 3: Backend Improvements (Optional)

#### Task 3.1: Conditional Deprecation Warning
**File**: `backend/app/presentation/api/v1/media.py`

**Current** (lines 252-256):
```python
# Log deprecation warning for ALL integer ID uses
logger.warning(
    f"DEPRECATED: Integer ID endpoint accessed for episode {episode_id}. "
    "Please use /episodes/by-video-id/{video_id}/audio for permanent URLs."
)
```

**Change to**:
```python
# Get episode first
episode = await episode_service.get_episode(episode_id)
if not episode:
    raise HTTPException(status_code=404, detail="Episode not found")

# Only log deprecation for YouTube episodes (those with video_id)
if episode.video_id:
    logger.warning(
        f"DEPRECATED: Integer ID endpoint accessed for YouTube episode {episode_id}. "
        f"Please use /episodes/by-video-id/{episode.video_id.value}/audio for permanent URLs."
    )
```

**Rationale**: The integer ID endpoint is the CORRECT approach for uploaded episodes, so we shouldn't show deprecation warnings for them.

---

### Phase 4: Testing

#### Test 4.1: Upload New Episode via API
```bash
# Upload a test episode
curl -X POST "https://labcastarr-api.oliverbarreto.com/v1/episodes/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "channel_id=1" \
  -F "title=Test Upload - Audio Playback Fix" \
  -F "description=Testing audio playback for uploaded episodes" \
  -F "audio_file=@/Users/oliver/Downloads/TEST1La4QzGeaaQ.mp3"
```

**Expected Response**:
```json
{
  "id": 29,
  "video_id": null,
  "title": "Test Upload - Audio Playback Fix",
  "audio_file_path": "channel_1/Test_Upload_-_Audio_Playback_Fix_20251019_XXXXXX.mp3",
  "status": "completed"
}
```

---

#### Test 4.2: Verify Audio File is Accessible
```bash
# Get the episode ID from the upload response (e.g., 29)
EPISODE_ID=29

# Test audio endpoint with integer ID (correct for uploaded episodes)
curl -I "https://labcastarr-api.oliverbarreto.com/v1/media/episodes/${EPISODE_ID}/audio"
```

**Expected Response**:
```
HTTP/2 200
content-type: audio/mpeg
content-length: [file_size]
accept-ranges: bytes
```

---

#### Test 4.3: Verify Audio Streaming
```bash
# Download a sample to verify it's playable
curl "https://labcastarr-api.oliverbarreto.com/v1/media/episodes/${EPISODE_ID}/audio" \
  -o /tmp/test_download.mp3

# Verify file is playable (macOS)
afplay /tmp/test_download.mp3
```

---

#### Test 4.4: Test Frontend Playback
1. Navigate to: `https://labcastarr.oliverbarreto.com/channels/1/episodes`
2. Find the uploaded episode
3. Click the play button
4. **Expected**: Audio plays without errors
5. **Check browser console**: No "DEPRECATED" warnings for uploaded episodes
6. **Check Network tab**: Verify the correct URL is being called

---

#### Test 4.5: Test YouTube Episode (Regression Test)
1. Create a YouTube episode (existing functionality)
2. Verify it still uses `/by-video-id/` endpoint
3. Verify audio plays correctly
4. Ensure no regressions in YouTube episode playback

---

#### Test 4.6: Test Download Button
1. Navigate to episode detail page for uploaded episode
2. Click download button
3. **Expected**: File downloads successfully
4. **Verify**: Downloaded file is playable

---

### Phase 5: Deployment

#### Task 5.1: Build Frontend
```bash
cd frontend
npm run build
```

#### Task 5.2: Deploy to Production
```bash
# From project root
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d
```

#### Task 5.3: Verify Deployment
```bash
# Check frontend health
curl https://labcastarr.oliverbarreto.com

# Check backend health
curl https://labcastarr-api.oliverbarreto.com/health
```

---

## Success Criteria

- [ ] TypeScript types updated (`video_id: string | null`)
- [ ] API client handles both YouTube and uploaded episodes correctly
- [ ] Audio player component passes full Episode object
- [ ] Download handler works for both episode types
- [ ] Backend deprecation warning only shows for YouTube episodes
- [ ] Uploaded episode audio plays successfully in browser
- [ ] YouTube episode audio still works (no regression)
- [ ] No console errors during playback
- [ ] Download button works for both episode types
- [ ] All tests pass

---

## Files Modified

### Frontend
- `frontend/src/types/index.ts` - Update Episode interface
- `frontend/src/lib/api-client.ts` - Update audio URL generation logic
- `frontend/src/components/features/episodes/audio-player.tsx` - Pass Episode object
- `frontend/src/components/features/episodes/episode-detail.tsx` - Update download handler

### Backend (Optional)
- `backend/app/presentation/api/v1/media.py` - Conditional deprecation warning

---

## Notes

1. **Why not use video_id for uploaded episodes?**
   - Uploaded episodes don't have YouTube video IDs
   - We could generate UUIDs, but that's over-engineering for now
   - Integer IDs work fine for uploaded episodes since they're not shared externally like RSS feeds

2. **RSS Feed Consideration**
   - RSS feeds should use permanent URLs
   - For uploaded episodes, the integer ID endpoint is stable enough
   - Future enhancement: Add `episode_slug` column for truly permanent URLs

3. **CDN/Caching**
   - YouTube episodes: Use video_id URLs (cache-friendly, permanent)
   - Uploaded episodes: Use integer ID URLs (stable within a channel)

---

## Related Documentation

- **Upload Feature Complete**: `docs/tasks/task-0029-UPLOAD-FEATURE-COMPLETE.md`
- **Video ID Implementation**: `docs/tasks/task-0034-new-id-in-route-to-access-episodes-audio.md`
- **API Documentation**: `docs/documentation/API-UPLOAD-ENDPOINT.md`

---

**Created**: October 19, 2025  
**Last Updated**: October 19, 2025  
**Status**: Ready for Implementation
