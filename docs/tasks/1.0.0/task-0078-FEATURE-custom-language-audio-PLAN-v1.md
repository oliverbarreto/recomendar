# Fix Plan: Language-Specific Audio Format Selection with Quality Prioritization

## Problem Summary

The custom language audio feature is **partially working** but has a critical flaw in format selection:

- ✅ Language preference is correctly saved to database
- ✅ Language preference is passed to download service
- ✅ Service attempts to download in selected language
- ❌ **Service fails to select proper quality when language-specific audio is available**

## Current Issue

When YouTube videos have multiple audio tracks in different languages with quality labels (low/medium/high), the current implementation:

1. Uses format string: `bestaudio[language=es][ext=m4a]/...` which yt-dlp cannot properly interpret with quality
2. Falls back to explicit format selection via `_select_format_by_language()`
3. **Bug**: `_select_format_by_language()` returns the **first match** without considering bitrate/quality

### Example from User's Test

Video has Spanish audio available:

```
139-2   m4a   49k  [es] Spanish, low       ← Current code would select this
140-2   m4a   129k [es] Spanish, medium    ← Should select this (best quality in preferred format)
249-7   webm  49k  [es] Spanish, low
251-6   webm  140k [es] Spanish, medium
```

**Current behavior**: Selects first m4a match (139-2 @ 49k - "low")
**Expected behavior**: Select highest quality m4a match (140-2 @ 129k - "medium")

## Root Cause Analysis

### File: `backend/app/infrastructure/services/youtube_service.py`

#### Bug Location: `_select_format_by_language()` (lines 360-400)

```python
# Current implementation - FLAWED
for ext_priority in ['m4a', 'mp3', None]:
    for fmt in audio_formats:
        fmt_lang = fmt.get('language', '').lower()
        fmt_ext = fmt.get('ext', '')

        if fmt_lang == preferred_language.lower():
            if ext_priority is None or fmt_ext == ext_priority:
                format_id = fmt.get('format_id')
                return format_id  # ← Returns FIRST match, not BEST match!
```

**Problem**: Returns immediately upon finding first format that matches language + extension, ignoring:

- Audio bitrate (abr)
- Quality label (format_note)
- Other quality indicators

## Solution Design

### Strategy: Quality-Aware Format Selection

Modify `_select_format_by_language()` to:

1. **Collect all formats** matching language + extension
2. **Sort by quality** (audio bitrate descending)
3. **Select highest quality** match

### Quality Prioritization Logic

**Extension Priority** (in order):

1. `m4a` - Most compatible with podcast RSS feeds
2. `mp3` - Universal compatibility
3. `webm` - Acceptable fallback

**Within each extension**:

- Sort by `abr` (audio bitrate) descending
- Higher bitrate = better quality
- Typical values: 128-160k (high), 64-96k (medium), 32-48k (low)

**Quality Thresholds**:

- Prefer formats with `abr >= 96k` (medium quality or better)
- Accept formats with `abr >= 48k` (low quality) if nothing better
- Reject formats with `abr < 32k` (very low quality)

## Implementation Plan

### Step 1: Enhance `_select_format_by_language()` Method

**Location**: `backend/app/infrastructure/services/youtube_service.py:360-400`

**Changes**:

```python
def _select_format_by_language(self, info_dict: Dict[str, Any], preferred_language: str) -> Optional[str]:
    """
    Select best audio format matching preferred language
    Prioritizes by: extension preference, then audio quality (bitrate)
    """
    if 'formats' not in info_dict:
        logger.warning("No formats found in video info")
        return None

    audio_formats = [f for f in info_dict['formats'] if f.get('acodec') != 'none']

    if not audio_formats:
        logger.warning("No audio formats found")
        return None

    # Filter formats matching preferred language
    matching_formats = [
        fmt for fmt in audio_formats
        if fmt.get('language', '').lower() == preferred_language.lower()
    ]

    if not matching_formats:
        logger.info(f"No format found with language '{preferred_language}', will use fallback")
        return None

    logger.info(f"Found {len(matching_formats)} format(s) with language '{preferred_language}'")

    # Try extension priorities: m4a > mp3 > webm > any
    for ext_priority in ['m4a', 'mp3', 'webm', None]:
        # Filter by extension
        if ext_priority:
            candidates = [f for f in matching_formats if f.get('ext') == ext_priority]
        else:
            candidates = matching_formats

        if not candidates:
            continue

        # Sort by audio bitrate (descending) - higher is better
        # Handle missing abr values by treating as 0
        candidates_sorted = sorted(
            candidates,
            key=lambda f: f.get('abr', 0) or 0,
            reverse=True
        )

        # Select best quality format
        best_format = candidates_sorted[0]
        format_id = best_format.get('format_id')

        logger.info(
            f"Selected format {format_id} for language '{preferred_language}': "
            f"ext={best_format.get('ext')}, "
            f"abr={best_format.get('abr', 'unknown')} kbps, "
            f"quality={best_format.get('format_note', 'unknown')}"
        )

        return format_id

    # Should not reach here, but safety fallback
    logger.warning(f"Failed to select format for language '{preferred_language}'")
    return None
```

### Step 2: Enhanced Logging for Format Details

**Location**: `backend/app/infrastructure/services/youtube_service.py:338-358`

Update `_log_available_formats()` to include quality information:

```python
def _log_available_formats(self, info_dict: Dict[str, Any], format_string: str) -> None:
    """Log all available audio formats with quality details"""
    logger.info(f"Using format string: {format_string}")

    if 'formats' in info_dict:
        audio_formats = [f for f in info_dict['formats'] if f.get('acodec') != 'none']
        logger.info(f"Found {len(audio_formats)} audio format(s):")

        # Group by language for clearer logging
        by_language = {}
        for fmt in audio_formats:
            lang = fmt.get('language', 'unknown')
            if lang not in by_language:
                by_language[lang] = []
            by_language[lang].append(fmt)

        # Log formats grouped by language
        for lang, formats in by_language.items():
            logger.info(f"  Language '{lang}': {len(formats)} format(s)")
            for fmt in formats[:5]:  # Limit to 5 per language
                logger.debug(
                    f"    Format {fmt.get('format_id')}: "
                    f"ext={fmt.get('ext')}, "
                    f"abr={fmt.get('abr', 'unknown')} kbps, "
                    f"acodec={fmt.get('acodec')}, "
                    f"quality={fmt.get('format_note', 'N/A')}"
                )
```

### Step 3: Improve Fallback Logic

If no format matches the preferred language, the current code already falls back to original audio. This is correct behavior.

However, we should add a quality threshold check:

- If only very low quality (< 32k abr) is available in preferred language
- Consider falling back to original high-quality audio
- But still honor user's language preference as primary priority

**Decision**: Keep current behavior (always prefer user's language choice, even if lower quality) but log the quality tradeoff.

## Testing Strategy

### Test Case 1: Video with Multiple Language Qualities

**Video**: qxxnRMT9C-8 (from user's test)

**Available formats**:

- Spanish: 49k (low), 129k (medium)
- English: Higher quality

**Expected**:

- Selects Spanish 129k (medium quality m4a)
- Logs show quality selection process
- Database: `preferred_audio_language='es'`, `actual_audio_language='es'`

### Test Case 2: Video with Only Low Quality in Preferred Language

**Setup**: Video with only 48k Spanish audio

**Expected**:

- Selects Spanish 48k (accepts low quality)
- No fallback notification (language available)
- Logs show quality accepted

### Test Case 3: Video with No Preferred Language

**Setup**: Video with only English audio

**Expected**:

- Falls back to English (original)
- Notification sent to user
- Database: `preferred_audio_language='es'`, `actual_audio_language='en'`

### Test Case 4: Video with Multiple Extensions in Preferred Language

**Available formats**:

- Spanish m4a: 128k
- Spanish webm: 140k
- Spanish mp3: 96k

**Expected**:

- Selects Spanish m4a 128k (extension priority over bitrate)
- Logs explain why m4a chosen over higher bitrate webm

## Files to Modify

### Primary Change

- **backend/app/infrastructure/services/youtube_service.py**
  - Lines 360-400: `_select_format_by_language()` - Rewrite with quality-aware selection
  - Lines 338-358: `_log_available_formats()` - Enhance with quality details and grouping

## Implementation Checklist

- [ ] Rewrite `_select_format_by_language()` with quality prioritization
- [ ] Enhance `_log_available_formats()` with grouped language display
- [ ] Test with video qxxnRMT9C-8 (Spanish audio available)
- [ ] Verify format 140-2 (129k m4a Spanish) is selected over 139-2 (49k)
- [ ] Check logs show quality selection reasoning
- [ ] Verify database saves correct actual_audio_language
- [ ] Test fallback case (no Spanish audio available)
- [ ] Verify notification sent when fallback occurs

## Expected Log Output After Fix

```
INFO: Starting download for URL: ... with preferred language: es
INFO: Using language-aware format string for es
INFO: Using format string: bestaudio[language=es][ext=m4a]/...
INFO: Found 4 audio format(s):
INFO:   Language 'es': 4 format(s)
DEBUG:   Format 139-2: ext=m4a, abr=49 kbps, acodec=mp4a.40.5, quality=Spanish, low
DEBUG:   Format 140-2: ext=m4a, abr=129 kbps, acodec=mp4a.40.2, quality=Spanish, medium
DEBUG:   Format 249-7: ext=webm, abr=49 kbps, acodec=opus, quality=Spanish, low
DEBUG:   Format 251-6: ext=webm, abr=140 kbps, acodec=opus, quality=Spanish, medium
INFO: Found 4 format(s) with language 'es'
INFO: Selected format 140-2 for language 'es': ext=m4a, abr=129 kbps, quality=Spanish, medium
INFO: Using explicit format selection: 140-2
```

## Success Criteria

✅ Spanish audio (format 140-2, 129k) is downloaded
✅ Database shows: `preferred_audio_language='es'`, `actual_audio_language='es'`
✅ Logs clearly show quality-based selection process
✅ User sees "ES" language pill in UI (not "EN")
✅ No fallback notification (language was available)

## Notes

- This fix builds on the previous repository mapping fix
- No database schema changes needed
- No frontend changes needed
- Only modifies format selection logic in youtube_service.py
- Maintains backward compatibility with original audio selection
