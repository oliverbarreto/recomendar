# Fix Custom Language/Audio Quality Download Errors - Implementation Plan

**Date**: 2026-02-09
**Priority**: CRITICAL
**Agent ID**: a87eb74 (for resuming)

## Error Summary

### Error 1: Spanish Audio Download Fails ❌ CRITICAL
- **Symptom**: "Requested format is not available"
- **Root Cause**: `remote_components` incorrectly nested in `extractor_args['jsc']` instead of top-level
- **Impact**: Only 31 formats accessible (not 121), Spanish formats unavailable
- **Priority**: Fix FIRST (blocks entire feature)

### Error 2: Progress Shows "Downloading 0%" Forever ⚠️ HIGH
- **Symptom**: UI stuck at 0% despite successful download
- **Root Cause**: Progress callbacks not persisted to database/Redis
- **Impact**: Poor UX, users think downloads are stuck
- **Priority**: Fix SECOND (feature works but UX is broken)

---

## Implementation Plan

### Phase 1: Fix Error 1 - Spanish Audio Download (CRITICAL)

**Estimated Time**: 35 minutes

#### Step 1.1: Move `remote_components` to Top-Level
**File**: `backend/app/infrastructure/services/youtube_service.py`

**Line 44-77**: Update `self.ydl_opts` initialization
```python
self.ydl_opts = {
    'quiet': True,
    'no_warnings': True,
    'remote_components': 'ejs:github',  # MOVED FROM LINE 70
    'format': 'bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio/best[height<=480]',
    # ... rest of config ...
    'extractor_args': {
        'youtube': {
            'player_client': ['android', 'web'],
            'skip': ['hls', 'dash']
        }
        # REMOVE 'jsc' section entirely (lines 69-72)
    },
}
```

**Line 165-176**: Update `_extract_metadata_sync()`
```python
def _extract_metadata_sync(self, url: str) -> Dict[str, Any]:
    opts = {
        'quiet': True,
        'no_warnings': True,
        'remote_components': 'ejs:github',  # MOVED FROM extractor_args
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)
```

#### Step 1.2: Fix Shallow Copy Bug
**File**: `backend/app/infrastructure/services/youtube_service.py`

**Line 1**: Add import
```python
import copy
```

**Line 207**: Change to deep copy
```python
download_opts = copy.deepcopy(self.ydl_opts)
```

#### Step 1.3: Test Error 1 Fix
```bash
# Rebuild containers
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d

# Test Spanish audio download
# Video: https://www.youtube.com/watch?v=I_w81rptxkc
# Settings: Language=Spanish, Quality=Low
```

**Expected Logs**:
```
[youtube] [jsc:deno] Solving JS challenges using deno
[youtube] I_w81rptxkc: Downloading m3u8 information
Total formats available: 121
Found 50+ audio/language formats out of 121 total
Selected HLS format 91-13 (256x144) for low quality
[download] 100% of 151.97MiB
Successfully downloaded audio
```

**Success Criteria**:
- ✅ Logs show 121 formats (not 31)
- ✅ Spanish language detected
- ✅ Download completes successfully
- ✅ Database shows `actual_language='es'`, `actual_quality='low'`

---

### Phase 2: Fix Error 2 - Progress Tracking (HIGH)

**Estimated Time**: 75 minutes

#### Step 2.1: Database Migration
**File**: `backend/alembic/versions/[XXX]_add_download_progress.py` (NEW)

```python
"""Add download progress tracking

Revision ID: XXX
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('episodes', sa.Column('download_progress_percentage', sa.Integer(), nullable=True))
    op.add_column('episodes', sa.Column('download_speed', sa.String(50), nullable=True))
    op.add_column('episodes', sa.Column('download_eta', sa.String(50), nullable=True))

def downgrade():
    op.drop_column('episodes', 'download_eta')
    op.drop_column('episodes', 'download_speed')
    op.drop_column('episodes', 'download_progress_percentage')
```

#### Step 2.2: Update Domain Entity
**File**: `backend/app/domain/entities/episode.py`

Add fields:
```python
download_progress_percentage: Optional[int] = None
download_speed: Optional[str] = None
download_eta: Optional[str] = None

def update_download_progress(self, percentage: int, speed: str = None, eta: str = None):
    """Update download progress information"""
    self.download_progress_percentage = percentage
    self.download_speed = speed
    self.download_eta = eta
```

#### Step 2.3: Update Database Model
**File**: `backend/app/infrastructure/database/models/episode.py`

Add columns:
```python
download_progress_percentage: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
download_speed: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
download_eta: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
```

#### Step 2.4: Persist Progress in Celery Task
**File**: `backend/app/infrastructure/services/celery_download_service.py`

Update `progress_hook` (around line 324):
```python
# Track last database update to avoid excessive writes
last_db_update = {'percentage': -1}

def progress_hook(d):
    try:
        progress.update_progress(d)

        # Persist to database every 5% to reduce writes
        if d.get('status') == 'downloading':
            percentage_str = d.get('_percent_str', '0%').strip()
            try:
                percentage = int(float(percentage_str.replace('%', '')))

                # Update every 5% milestone
                if percentage % 5 == 0 and percentage != last_db_update['percentage']:
                    # Run async update in background
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)

                    loop.create_task(self._persist_progress(
                        episode_id,
                        percentage,
                        d.get('_speed_str', 'N/A'),
                        d.get('_eta_str', 'N/A')
                    ))
                    last_db_update['percentage'] = percentage
            except (ValueError, AttributeError):
                pass
    except Exception as e:
        logger.warning(f"Progress callback error: {e}")
```

Add helper method:
```python
async def _persist_progress(self, episode_id: int, percentage: int, speed: str, eta: str):
    """Persist download progress to database"""
    try:
        episode = await self.episode_repository.get_by_id(episode_id)
        if episode:
            episode.update_download_progress(percentage, speed, eta)
            await self.episode_repository.update(episode)
            logger.debug(f"Updated episode {episode_id} progress: {percentage}%")
    except Exception as e:
        logger.error(f"Failed to persist progress for episode {episode_id}: {e}")
```

#### Step 2.5: Update Progress API Endpoint
**File**: `backend/app/presentation/api/v1/episodes.py`

Update GET progress endpoint:
```python
@router.get("/{episode_id}/progress")
async def get_episode_progress(
    episode_id: int,
    episode_repository: EpisodeRepository = Depends(get_episode_repository)
) -> Dict[str, Any]:
    """Get real-time download progress from database"""
    episode = await episode_repository.get_by_id(episode_id)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    progress_percentage = episode.download_progress_percentage or 0

    # Map episode status to task status
    status_map = {
        EpisodeStatus.PENDING: "queued",
        EpisodeStatus.PROCESSING: "processing",
        EpisodeStatus.COMPLETED: "completed",
        EpisodeStatus.FAILED: "failed",
    }
    task_status = status_map.get(episode.status, "unknown")

    # Override percentage for completed episodes
    if task_status == "completed":
        progress_percentage = 100

    return {
        "episode_id": episode_id,
        "status": task_status,
        "percentage": f"{progress_percentage}%",
        "speed": episode.download_speed or "N/A",
        "eta": episode.download_eta or "N/A",
        "error_message": None if task_status != "failed" else "Download failed"
    }
```

#### Step 2.6: Test Error 2 Fix
```bash
# Apply migration
docker exec labcastarr-backend-1 uv run alembic upgrade head

# Rebuild containers
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d

# Test download with progress tracking
# Watch frontend UI and database:
watch -n 1 'docker exec labcastarr-backend-1 uv run python -c "
from app.infrastructure.database.connection import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text(\"SELECT id, title, status, download_progress_percentage FROM episodes WHERE id = 7\"))
    print(list(result))
"'
```

**Success Criteria**:
- ✅ Frontend shows "Downloading 5%... 15%... 35%... 100%"
- ✅ Database column updates every 5%
- ✅ No "Downloading 0%" forever
- ✅ Progress resets to 0% when new download starts

---

## Testing Strategy

### Test Case 1: Spanish Audio Download (Error 1)
- **URL**: https://www.youtube.com/watch?v=I_w81rptxkc
- **Settings**: Language=Spanish, Quality=Low
- **Expected**: Format 91-13 selected, download succeeds
- **Verify**: `ffprobe` shows Spanish audio track

### Test Case 2: English Audio Download (Baseline)
- **URL**: https://www.youtube.com/watch?v=zQ1POHiR8m8
- **Settings**: Language=English, Quality=Medium
- **Expected**: Format 140 selected (DASH audio-only)
- **Verify**: Faster download than HLS (audio-only vs combined)

### Test Case 3: Progress Tracking (Error 2)
- **URL**: Any video (>100MB for longer download)
- **Settings**: Default
- **Verify**:
  - Frontend updates every 5 seconds
  - Database shows 0%, 5%, 10%, ..., 100%
  - UI shows final "Completed ✓" state

### Test Case 4: Concurrent Downloads
- **Action**: Start 3 downloads simultaneously
- **Verify**: Each tracks progress independently
- **Check**: No database lock errors in logs

---

## Risk Mitigation

### Risk 1: Database Lock from Progress Updates
- **Mitigation**: Update only every 5% (max 20 writes per download)
- **Fallback**: Increase to 10% if locks occur (max 10 writes)
- **WAL Mode**: Already enabled (per CLAUDE.md)

### Risk 2: yt-dlp Version Mismatch
- **Check**: `docker exec labcastarr-backend-1 uv run yt-dlp --version` should show `2026.02.04`
- **Fix**: Run `uv lock --upgrade-package yt-dlp` if outdated

### Risk 3: Deep Copy Performance
- **Impact**: ~1ms overhead per download (negligible)
- **Optimization**: Only deep copy when language/quality specified

---

## Deployment Commands

```bash
# Apply database migration
docker exec labcastarr-backend-1 uv run alembic upgrade head

# Rebuild and restart all services
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d

# Verify yt-dlp version
docker exec labcastarr-backend-1 uv run yt-dlp --version
# Expected: 2026.02.04

# Watch logs during test
docker compose --env-file .env.production -f docker-compose.prod.yml logs celery-worker -f
```

---

## Implementation Checklist

### Phase 1 (Error 1 - Spanish Audio) ✅ PRIORITY 1
- [ ] Move `remote_components` to top-level in `youtube_service.py` (line 44)
- [ ] Update `_extract_metadata_sync()` with `remote_components` (line 165)
- [ ] Add `import copy` and change to `deepcopy` (lines 1, 207)
- [ ] Rebuild Docker containers
- [ ] Test Spanish audio download
- [ ] Verify 121 formats in logs (not 31)
- [ ] Verify Spanish language detected and format selected

### Phase 2 (Error 2 - Progress) ⏳ PRIORITY 2
- [ ] Create Alembic migration for 3 new columns
- [ ] Update domain entity with progress fields
- [ ] Update database model with progress columns
- [ ] Apply migration to database
- [ ] Update `celery_download_service.py` progress_hook
- [ ] Add `_persist_progress()` helper method
- [ ] Update GET progress API endpoint
- [ ] Rebuild Docker containers
- [ ] Test progress tracking end-to-end
- [ ] Verify frontend shows real-time updates

---

## Success Metrics

### Error 1 Fixed
- ✅ Spanish audio downloads complete successfully
- ✅ Database shows `actual_language='es'`
- ✅ Logs show 121 formats available
- ✅ No "Requested format is not available" errors

### Error 2 Fixed
- ✅ Frontend shows progress: 0% → 5% → 10% → ... → 100%
- ✅ No "Downloading 0%" stuck state
- ✅ Database column `download_progress_percentage` updates
- ✅ Download completes and shows "Completed ✓"

---

## Files to Modify

### Phase 1 (3 files)
1. `backend/app/infrastructure/services/youtube_service.py` - Move remote_components, add deepcopy
2. `backend/alembic/versions/[existing]_*.py` - No changes (code only)
3. `backend/Dockerfile` - No changes (already has deno)

### Phase 2 (6 files)
1. `backend/alembic/versions/[NEW]_add_download_progress.py` - Migration
2. `backend/app/domain/entities/episode.py` - Add progress fields/method
3. `backend/app/infrastructure/database/models/episode.py` - Add progress columns
4. `backend/app/infrastructure/repositories/episode_repository.py` - Update mapper
5. `backend/app/infrastructure/services/celery_download_service.py` - Persist progress
6. `backend/app/presentation/api/v1/episodes.py` - Update progress endpoint

---

## Next Steps After Implementation

1. Update user documentation with language availability
2. Add unit tests for `AudioFormatSelectionService`
3. Add integration tests for Spanish audio downloads
4. Monitor production logs for format selection patterns
5. Consider adding language auto-detection based on video metadata

---

## References

- Original feature plan: `/Users/oliver/.claude/plans/delegated-squishing-nova.md`
- Implementation summary: `task-0079-FEATURE-custom-language-audio-2026-implementation-summary.md`
- Solution doc: `task-0079-SOLUTION-spanish-audio-selection.md`
- Agent analysis: Agent ID `a87eb74` (can resume for follow-up work)
