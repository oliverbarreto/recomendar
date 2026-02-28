# Error 1 Fixed: Spanish Audio Download Ready for Testing

**Date**: 2026-02-09
**Status**: ✅ DEPLOYED - Ready for Testing
**Priority**: CRITICAL

---

## What Was Fixed

### Root Cause
The `remote_components` configuration was incorrectly nested under `extractor_args['jsc']` instead of being a top-level yt-dlp option. This prevented:
- JavaScript challenge solving
- HLS multi-language manifest (m3u8) access
- Spanish audio format detection

### Changes Applied

#### 1. Moved `remote_components` to Top-Level
**File**: `backend/app/infrastructure/services/youtube_service.py`

**Before** (Lines 69-72):
```python
'extractor_args': {
    'youtube': {...},
    'jsc': {
        'remote_components': 'ejs:github'  # WRONG LOCATION
    }
}
```

**After** (Line 47):
```python
self.ydl_opts = {
    'quiet': True,
    'no_warnings': True,
    'remote_components': 'ejs:github',  # TOP LEVEL ✅
    # ... rest of config
}
```

#### 2. Updated Format Extraction
**File**: `backend/app/infrastructure/services/youtube_service.py`

**Lines 165-172**:
```python
def _extract_metadata_sync(self, url: str) -> Dict[str, Any]:
    opts = {
        'quiet': True,
        'no_warnings': True,
        'remote_components': 'ejs:github',  # TOP LEVEL ✅
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)
```

#### 3. Fixed Shallow Copy Bug
**File**: `backend/app/infrastructure/services/youtube_service.py`

**Line 1**: Added `import copy`
**Line 199**: Changed from `.copy()` to `.deepcopy()`

---

## Expected Behavior After Fix

### Before Fix (❌ BROKEN)
```bash
[2026-02-09 16:46:56] Total formats available: 31
[2026-02-09 16:46:56] Found 5 audio/language formats out of 31 total
[2026-02-09 16:46:56] Language 'es' not available, falling back to default
[2026-02-09 16:46:56] Format selection: format=249, quality=64kbps, fallback=True
[2026-02-09 16:46:59] ERROR: Requested format is not available
```

### After Fix (✅ EXPECTED)
```bash
[2026-02-09] [youtube] [jsc:deno] Solving JS challenges using deno
[2026-02-09] [youtube] I_w81rptxkc: Downloading m3u8 information
[2026-02-09] Total formats available: 121
[2026-02-09] Found 50+ audio/language formats out of 121 total
[2026-02-09] Selected HLS format 91-13 (256x144) for low quality
[2026-02-09] [download] 100% of 151.97MiB at 6.45MiB/s
[2026-02-09] Successfully downloaded audio for URL: ...
```

---

## Testing Instructions

### Test Case 1: Spanish Audio, Low Quality ⭐ PRIMARY TEST
**Video URL**: `https://www.youtube.com/watch?v=I_w81rptxkc`
**Settings**:
- Language: **Spanish**
- Quality: **Low**

**Steps**:
1. Open frontend: http://localhost:3000
2. Click "Quick Add" (or "Add Episode")
3. Paste URL: `https://www.youtube.com/watch?v=I_w81rptxkc`
4. Enable "Custom Audio Options"
5. Select:
   - Language: **Spanish**
   - Quality: **Low**
6. Click "Create Episode"

**Watch Backend Logs**:
```bash
docker compose --env-file .env.production -f docker-compose.prod.yml logs celery-worker -f
```

**Success Criteria** ✅:
- Log shows: `[youtube] [jsc:deno] Solving JS challenges using deno`
- Log shows: `Total formats available: 121` (NOT 31)
- Log shows: `Found 50+ audio/language formats` (NOT 5)
- Log shows: `Selected HLS format 91-13`
- Download completes successfully
- Episode status changes to "Completed ✓"

**Failure Indicators** ❌:
- Log shows: `Total formats available: 31` → remote_components not working
- Log shows: `Language 'es' not available` → Spanish formats not detected
- Error: `Requested format is not available` → Wrong format selected

### Test Case 2: Spanish Audio, Medium Quality
**Video URL**: `https://www.youtube.com/watch?v=0t_DD5568RA`
**Settings**:
- Language: **Spanish**
- Quality: **Medium**

**Expected**:
- Format `93-12` or `94-12` selected (360p or 480p Spanish)
- Download completes successfully
- Database shows: `actual_language='es'`, `actual_quality='medium'`

### Test Case 3: Default Settings (Baseline)
**Video URL**: `https://www.youtube.com/watch?v=zQ1POHiR8m8`
**Settings**:
- Language: **Original (default)**
- Quality: **Medium**

**Expected**:
- Format `140` selected (DASH audio-only, 129kbps)
- Faster download than HLS (audio-only vs combined)
- Download completes successfully

---

## Verification Checklist

### ✅ Pre-Deployment Verification
- [x] Docker containers rebuilt
- [x] yt-dlp version confirmed: `2026.02.04`
- [x] Deno installed and working
- [x] Code changes applied correctly

### ⏳ Post-Testing Verification
- [ ] Test Case 1 passed (Spanish Low)
- [ ] Test Case 2 passed (Spanish Medium)
- [ ] Test Case 3 passed (Default Medium)
- [ ] Database shows `actual_language='es'`
- [ ] Database shows `actual_quality='low/medium'`
- [ ] No "Requested format is not available" errors

---

## Database Verification

After successful download, check database:

```bash
docker exec labcastarr-backend-1 uv run python -c "
from app.infrastructure.database.connection import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text('''
        SELECT id, title, video_id, status,
               requested_language, requested_quality,
               actual_language, actual_quality,
               fallback_occurred
        FROM episodes
        WHERE video_id IN ('I_w81rptxkc', '0t_DD5568RA', 'zQ1POHiR8m8')
        ORDER BY id DESC
    '''))
    for row in result:
        print(f'ID={row[0]}, Title={row[1][:30]}, Status={row[3]}')
        print(f'  Requested: {row[4]}/{row[5]}')
        print(f'  Actual: {row[6]}/{row[7]}, Fallback: {row[8]}')
        print()
"
```

**Expected Output**:
```
ID=8, Title=TONY ROBBINS ON..., Status=completed
  Requested: es/low
  Actual: es/low, Fallback: False

ID=9, Title=What Your Doctor..., Status=completed
  Requested: es/medium
  Actual: es/medium, Fallback: False

ID=7, Title=Godfather of AI..., Status=completed
  Requested: None/None
  Actual: None/None, Fallback: False
```

---

## Troubleshooting

### Problem: Still showing 31 formats
**Solution**: Check that remote_components is at top-level, not in extractor_args

### Problem: "Requested format is not available"
**Solution**: Check logs for format selection - should be `91-13`, not `249`

### Problem: Spanish not detected
**Solution**: Verify JS challenge solving logs: `[jsc:deno] Solving JS challenges`

### Problem: Download never starts
**Likely Cause**: Error 2 (progress tracking) - check next phase of fixes

---

## Next Steps

### If Test Succeeds ✅
1. Mark Error 1 as **RESOLVED**
2. Proceed to **Phase 2: Fix Error 2** (Progress Tracking)
3. Update documentation with Spanish audio availability

### If Test Fails ❌
1. Share full Celery worker logs
2. Check yt-dlp version: `docker exec labcastarr-backend-1 uv run yt-dlp --version`
3. Verify deno installed: `docker exec labcastarr-backend-1 deno --version`
4. Resume Plan agent (ID: `a87eb74`) for further analysis

---

## Files Modified

1. ✅ `backend/app/infrastructure/services/youtube_service.py`
   - Added `import copy` (line 1)
   - Moved `remote_components` to top-level (line 47)
   - Updated `_extract_metadata_sync()` (lines 165-172)
   - Changed to `deepcopy()` (line 199)

2. ✅ `backend/Dockerfile` (unchanged - already has deno)

3. ✅ `backend/pyproject.toml` (unchanged - already has yt-dlp 2026.2.4)

---

## Deployment Status

- **Backend Container**: ✅ Rebuilt and Running
- **Celery Worker**: ✅ Rebuilt and Running
- **yt-dlp Version**: ✅ 2026.02.04
- **Deno Version**: ✅ 2.6.8
- **Remote Components**: ✅ Configured

**System Ready for Testing!** 🚀

Please test with Spanish audio download and report results.
