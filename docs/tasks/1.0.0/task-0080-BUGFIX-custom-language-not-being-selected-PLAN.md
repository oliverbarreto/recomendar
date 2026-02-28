# Implementation Plan: Fix: YouTube Multi-Language Audio Download

Here is Claude's plan:

## Context

The custom language/quality audio download feature is broken. When a user requests Spanish audio for a YouTube video, the system fails to find Spanish tracks and even the English fallback fails with "Requested format is not available". This has been going back and forth for days. The fix addresses 4 distinct bugs identified through analysis of the code and Celery worker logs.

## Root Causes

### Bug 1 (CRITICAL): Missing `web_safari` player client — HLS formats never discovered

- **File**: `youtube_service.py:66-70`
- Base opts use `player_client: ['android', 'web']`
- HLS/m3u8 formats (containing multi-language audio like `91-0` for Spanish) are ONLY returned by the `web_safari` player client
- Terminal yt-dlp shows `Downloading web safari player API JSON` — that's how it finds HLS formats
- In Docker, without `web_safari`: 31 formats (no HLS). With it: 100+ formats including all language variants
- **Evidence**: Celery logs show `Found 5 audio/language formats out of 31 total` — all HLS formats are missing

### Bug 2 (CRITICAL): Mismatched yt-dlp options between format analysis and download

- **File**: `youtube_service.py:214-216` vs `youtube_service.py:256-261`
- Format analysis uses `_extract_metadata_sync()` with **minimal options** (no player_client → yt-dlp defaults)
- Download uses deep-copied `self.ydl_opts` with **restricted** `player_client: ['android', 'web']`
- Format found during analysis may not exist during download → "Requested format is not available"
- **Evidence**: Format 249 selected during analysis, but download fails because download opts use different player clients

### Bug 3: Dockerfile.dev missing deno

- **File**: `backend/Dockerfile.dev:4`
- Production Dockerfile installs deno; dev Dockerfile does not
- `remote_components: 'ejs:github'` requires deno for HLS JS challenge solving

### Bug 4: No download fallback when specific format fails

- When selected format download fails, error propagates and episode creation fails completely
- Should retry with default format selector (`bestaudio[ext=m4a]/bestaudio`) as safety net

## Implementation Plan

### Step 1: Fix `Dockerfile.dev` — Add deno installation

**File**: `backend/Dockerfile.dev`

Add deno installation to match production Dockerfile:

```dockerfile
RUN apt-get update && apt-get install -y curl ffmpeg libmagic1 unzip && \
    curl -fsSL https://deno.land/install.sh | sh && \
    mv /root/.deno/bin/deno /usr/local/bin/ && \
    rm -rf /var/lib/apt/lists/*
```

### Step 2: Rewrite `youtube_service.py` — Consistent options + web_safari + fallback

**File**: `backend/app/infrastructure/services/youtube_service.py`

#### 2a: New helper `_build_format_extraction_opts(include_hls: bool)`

Builds yt-dlp options suitable for BOTH format analysis AND download. When `include_hls=True`:

- Adds `web_safari` to `player_client` list
- Removes `skip: ['hls', 'dash']`
- Includes `remote_components: 'ejs:github'`

When `include_hls=False` (default downloads without language/quality):

- Uses `player_client: ['android', 'web']` with `skip: ['hls', 'dash']` (faster, current behavior)

```python
def _build_format_extraction_opts(self, include_hls: bool = False) -> dict:
    """Build consistent yt-dlp options for format extraction and download."""
    opts = copy.deepcopy(self.ydl_opts)
    if include_hls:
        # Add web_safari to discover HLS multi-language formats
        opts['extractor_args']['youtube']['player_client'] = ['android', 'web', 'web_safari']
        # Remove HLS/DASH skip to allow these format types
        if 'skip' in opts['extractor_args']['youtube']:
            del opts['extractor_args']['youtube']['skip']
    return opts
```

#### 2b: New helper `_extract_info_with_opts_sync(url, opts)`

Extracts info using the SAME options that will be used for download (not minimal opts).

```python
def _extract_info_with_opts_sync(self, url: str, opts: dict) -> dict:
    """Extract video info using the provided opts (same opts used for download)."""
    extract_opts = copy.deepcopy(opts)
    # Don't actually download, just extract info
    with yt_dlp.YoutubeDL(extract_opts) as ydl:
        return ydl.extract_info(url, download=False)
```

#### 2c: Rewrite `download_audio()` method

Key changes:

1. Build opts ONCE with `_build_format_extraction_opts(include_hls=True)` when language/quality requested
2. Extract formats using those SAME opts (not `_extract_metadata_sync`)
3. Pass formats to `AudioFormatSelectionService`
4. Set selected format_id in those SAME opts
5. Download with those SAME opts
6. **If download fails**, retry with default format selector as fallback

```python
async def download_audio(self, url, output_path=None, progress_callback=None,
                         audio_language=None, audio_quality=None) -> tuple:
    try:
        need_custom_format = bool(audio_language or audio_quality)
        download_opts = self._build_format_extraction_opts(include_hls=need_custom_format)

        format_info = {}
        if need_custom_format:
            try:
                # Step 1: Extract info with the SAME opts we'll use for download
                loop = asyncio.get_event_loop()
                info = await loop.run_in_executor(
                    None, self._extract_info_with_opts_sync, url, download_opts
                )
                formats_list = info.get('formats', [])

                # Step 2: Select format
                format_selection_service = AudioFormatSelectionService()
                selection = format_selection_service.select_format(
                    formats_list, audio_language, audio_quality
                )

                # Step 3: Configure download opts with selected format
                download_opts['format'] = selection.format_selector
                download_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': selection.preferred_quality_kbps,
                }]
                format_info = {
                    'actual_language': selection.actual_language,
                    'actual_quality': selection.actual_quality,
                    'fallback_occurred': selection.fallback_occurred,
                    'fallback_reason': selection.fallback_reason,
                }
                logger.info(f"Format selected: id={selection.format_selector}, ...")

            except Exception as e:
                logger.warning(f"Format selection failed, using defaults: {e}")
                # Reset to default opts (no HLS needed for defaults)
                download_opts = self._build_format_extraction_opts(include_hls=False)
                format_info = {
                    'actual_language': None, 'actual_quality': None,
                    'fallback_occurred': True,
                    'fallback_reason': f"Format analysis error: {e}",
                }

        # Configure output path and progress
        if output_path:
            download_opts['outtmpl'] = output_path
        if progress_callback:
            download_opts['progress_hooks'] = [progress_callback]

        # Step 4: Download (with fallback)
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                None, self._download_audio_sync, url, download_opts
            )
        except YouTubeDownloadError as e:
            if "not available" in str(e).lower() and need_custom_format:
                # FALLBACK: retry with default format
                logger.warning(f"Selected format failed, retrying with defaults: {e}")
                fallback_opts = self._build_format_extraction_opts(include_hls=False)
                if output_path:
                    fallback_opts['outtmpl'] = output_path
                if progress_callback:
                    fallback_opts['progress_hooks'] = [progress_callback]
                result = await loop.run_in_executor(
                    None, self._download_audio_sync, url, fallback_opts
                )
                format_info = {
                    'actual_language': None, 'actual_quality': None,
                    'fallback_occurred': True,
                    'fallback_reason': f"Selected format unavailable, used default: {e}",
                }
            else:
                raise

        return (result, format_info)
    except Exception as e:
        logger.error(f"Failed to download audio from {url}: {e}")
        raise YouTubeDownloadError(f"Download failed: {e}")
```

### Step 3: Improve logging in `audio_format_selection_service.py`

**File**: `backend/app/infrastructure/services/audio_format_selection_service.py`

Improve `_get_audio_formats()` to log a structured summary after processing:

- Total formats, DASH audio count, HLS multi-lang count
- Available languages found (e.g., `{en, es, fr, ar, ...}`)
- Which formats were selected as audio candidates and why

This gives clear diagnostic output without the wall of per-format log lines that make debugging harder.

### Step 4: Keep `_extract_metadata_sync` unchanged

The existing `_extract_metadata_sync()` (used for `extract_metadata()` which fetches video title/description for episode creation) remains unchanged with minimal opts — it doesn't need HLS formats, just metadata.

## Files Modified

| File                                                                    | Change                                                                                                                                               |
| ----------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `backend/Dockerfile.dev`                                                | Add deno installation (match production)                                                                                                             |
| `backend/app/infrastructure/services/youtube_service.py`                | Add `_build_format_extraction_opts()`, add `_extract_info_with_opts_sync()`, rewrite `download_audio()` with consistent opts + web_safari + fallback |
| `backend/app/infrastructure/services/audio_format_selection_service.py` | Improve diagnostic logging with structured summary                                                                                                   |

## Files NOT Modified (verified correct)

- `audio_quality.py` — Quality tiers correct
- `celery_download_service.py` — Passes language/quality correctly
- `download_episode_task.py` — Task parameters correct
- `download_service.py` — FastAPI path mirrors Celery, same fix applies
- `episodes.py` (API) — Sends parameters correctly
- All frontend components — Send language/quality correctly
- `episode.py` (entity) — Four-field architecture correct
- `episode.py` (model) — Database columns correct

## Verification

1. **Rebuild dev Docker images**: `docker compose --env-file .env.development -f docker-compose.dev.yml up --build`
2. **Restart Celery workers** (they don't auto-reload): `docker compose -f docker-compose.dev.yml restart celery-worker-dev celery-beat-dev`
3. **Test: Quick Add with Spanish/Low quality**
   - URL: `https://www.youtube.com/watch?v=0t_DD5568RA`
   - Language: Spanish, Quality: Low
   - Expected: Celery logs show HLS formats discovered (100+ formats), Spanish tracks found, format `91-0` selected, download succeeds
4. **Test: Quick Add with default (no language/quality)**
   - Any YouTube URL
   - Expected: Works as before (fast, skips HLS)
5. **Test: Fallback behavior**
   - Use a video that has no Spanish audio
   - Select Spanish
   - Expected: Falls back to English with notification to user
6. **Check Celery logs** for the structured logging showing each step:
   - `[FORMATS] Total: X, DASH audio: Y, HLS multi-lang: Z`
   - `[FORMATS] Available languages: {en, es, fr, ...}`
   - `[SELECT] Selected format_id=91-0, language=es, quality=low`

---

## Response

task-0080-BUGFIX-custom-language-not-being-selected-PLAN.md
