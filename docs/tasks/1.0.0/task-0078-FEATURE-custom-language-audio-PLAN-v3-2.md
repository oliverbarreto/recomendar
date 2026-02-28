# Implementation Plan: Fix Audio Language Selection & Add Quality Preferences

## Executive Summary

This plan fixes the YouTube audio language selection bug and adds quality control (low/medium/high) for audio downloads. The root cause is that yt-dlp doesn't populate the `language` field for composite format IDs (dubbed tracks like `140-2`), requiring enhanced format detection that parses multiple metadata sources.

## Root Cause Analysis

### Why Spanish Audio Isn't Downloading

**Current Implementation** (`youtube_service.py` line 397):

```python
matching_formats = [
    fmt for fmt in audio_formats
    if fmt.get('language', '').lower() == preferred_language.lower()
]
```

**The Problem**:

- YouTube multi-audio videos use composite format IDs: `140-2` (Spanish m4a, 129k), `139-7` (Spanish m4a, 49k)
- yt-dlp **doesn't populate** the `language` field for these formats
- Language info exists in other fields: `format_note` = "Spanish, medium" or `format` = "[es] Spanish"
- Current code only checks `fmt.get('language')` which returns `None`

**Evidence from yt-dlp output**:

```
140-2   m4a   audio only [es] Spanish, medium, m4a_dash (129k)
```

The `[es]` and "Spanish" text is in the format string/note, NOT in the `language` field.

## Solution Architecture

### Core Fix: Enhanced Language Detection

Create `_extract_format_language()` method that checks multiple sources:

1. **Direct `language` field** (works for some videos)
2. **Parse `format_note`** (e.g., "Spanish, medium" → extract "spanish" → map to "es")
3. **Parse `format` string** (e.g., "[es] Spanish" → extract "es" via regex)
4. **Detect composite IDs** (`140-2` indicates alternate audio track)

### New Feature: Quality Selection

Add bitrate-based quality filtering:

- **Low**: < 70 kbps (fast downloads, small files) - **DEFAULT**
- **Medium**: 70-150 kbps (balanced)
- **High**: > 150 kbps (best quality)

Format priority remains: m4a > mp3 (podcast compatibility)

## Implementation Steps

### Phase 1: Backend Core Fix (4-6 hours)

#### File: `backend/app/infrastructure/services/youtube_service.py`

**1.1 Add `_extract_format_language()` method** (new, ~60 lines after line 438):

```python
def _extract_format_language(self, fmt: Dict[str, Any]) -> Optional[str]:
    """
    Extract language from format metadata using multiple sources

    Checks (in order):
    1. Direct 'language' field
    2. Parse from 'format_note' (e.g., "Spanish, medium")
    3. Parse from 'format' string (e.g., "[es] Spanish")

    Args:
        fmt: yt-dlp format dictionary

    Returns:
        ISO 639-1 language code or None
    """
    import re

    # 1. Direct language field
    lang = fmt.get('language')
    if lang and lang != 'none':
        return lang.strip()

    # 2. Parse from format_note
    format_note = fmt.get('format_note', '')
    if format_note:
        lang_map = {
            'spanish': 'es', 'english': 'en', 'french': 'fr',
            'german': 'de', 'italian': 'it', 'portuguese': 'pt',
            'japanese': 'ja', 'chinese': 'zh', 'arabic': 'ar',
            'dutch': 'nl', 'hindi': 'hi', 'polish': 'pl',
            'indonesian': 'id'
        }
        note_lower = format_note.lower()
        for lang_name, lang_code in lang_map.items():
            if lang_name in note_lower:
                logger.debug(f"Extracted '{lang_code}' from format_note: {format_note}")
                return lang_code

    # 3. Parse from format string (e.g., "139 - [es] Spanish")
    format_str = fmt.get('format', '')
    if format_str:
        lang_match = re.search(r'\[([a-z]{2})\]', format_str.lower())
        if lang_match:
            lang_code = lang_match.group(1)
            logger.debug(f"Extracted '{lang_code}' from format: {format_str}")
            return lang_code

    return None
```

**1.2 Add `_filter_by_quality()` method** (new, ~35 lines after `_extract_format_language`):

```python
def _filter_by_quality(self, formats: List[Dict[str, Any]], quality: str) -> List[Dict[str, Any]]:
    """
    Filter formats by quality based on bitrate ranges

    Quality Mapping:
    - 'low': < 70 kbps (fast downloads, smaller files)
    - 'medium': 70-150 kbps (balanced quality/size)
    - 'high': > 150 kbps (best audio quality)

    Args:
        formats: List of format dictionaries
        quality: Quality level ('low', 'medium', 'high')

    Returns:
        Filtered list of formats matching quality tier
    """
    bitrate_ranges = {
        'low': (0, 70),
        'medium': (70, 150),
        'high': (150, float('inf'))
    }

    if quality not in bitrate_ranges:
        logger.warning(f"Invalid quality '{quality}', must be low/medium/high")
        return formats

    min_br, max_br = bitrate_ranges[quality]

    filtered = []
    for fmt in formats:
        abr = fmt.get('abr', 0) or 0
        if min_br <= abr < max_br:
            filtered.append(fmt)

    logger.debug(f"Filtered {len(formats)} → {len(filtered)} formats for quality '{quality}'")
    return filtered
```

**1.3 Update `_select_format_by_language()` method** (modify lines 371-438):

```python
def _select_format_by_language(
    self,
    info_dict: Dict[str, Any],
    preferred_language: str,
    preferred_quality: Optional[str] = None  # NEW PARAMETER
) -> Optional[str]:
    """
    Select best audio format matching preferred language and quality

    Args:
        info_dict: yt-dlp info dictionary
        preferred_language: ISO 639-1 language code
        preferred_quality: Optional quality ('low', 'medium', 'high')

    Returns:
        Format ID string if found, None otherwise
    """
    if 'formats' not in info_dict:
        logger.warning("No formats found in video info")
        return None

    audio_formats = [f for f in info_dict['formats'] if f.get('acodec') != 'none']

    if not audio_formats:
        logger.warning("No audio formats found")
        return None

    # Step 1: Filter by language (ENHANCED)
    matching_formats = []
    for fmt in audio_formats:
        lang = self._extract_format_language(fmt)  # Use enhanced detection
        if lang and lang.lower() == preferred_language.lower():
            matching_formats.append(fmt)

    if not matching_formats:
        logger.info(f"No format found with language '{preferred_language}'")
        return None

    logger.info(f"Found {len(matching_formats)} format(s) with language '{preferred_language}'")

    # Step 2: Filter by quality if specified (NEW)
    if preferred_quality:
        quality_filtered = self._filter_by_quality(matching_formats, preferred_quality)
        if quality_filtered:
            matching_formats = quality_filtered
        else:
            logger.warning(f"No {preferred_quality} quality formats, using all")

    # Step 3: Apply format priority (m4a > mp3)
    for ext_priority in ['m4a', 'mp3']:
        candidates = [f for f in matching_formats if f.get('ext') == ext_priority]

        if not candidates:
            continue

        # Sort by bitrate (descending)
        candidates_sorted = sorted(
            candidates,
            key=lambda f: f.get('abr', 0) or 0,
            reverse=True
        )

        best_format = candidates_sorted[0]
        format_id = best_format.get('format_id')

        logger.info(
            f"Selected format {format_id} for '{preferred_language}' "
            f"(quality: {preferred_quality or 'best'}): "
            f"ext={best_format.get('ext')}, abr={best_format.get('abr')} kbps"
        )

        return format_id

    logger.info(f"No m4a/mp3 format found with language '{preferred_language}'")
    return None
```

**1.4 Update `download_audio()` signature** (modify lines 160-166):

Add `preferred_quality` parameter:

```python
async def download_audio(
    self,
    url: str,
    output_path: Optional[str] = None,
    progress_callback: Optional[Callable] = None,
    preferred_language: Optional[str] = None,
    preferred_quality: Optional[str] = None  # NEW
) -> tuple[str, str]:
```

Update logger call (line 183):

```python
logger.info(f"Starting download for URL: {url} with language: {preferred_language}, quality: {preferred_quality}")
```

Update executor call (lines 205-211):

```python
audio_path, actual_language = await loop.run_in_executor(
    None,
    self._download_audio_sync,
    url,
    download_opts,
    preferred_language,
    preferred_quality  # NEW
)
```

**1.5 Update `_download_audio_sync()` signature** (modify lines 220-231):

```python
def _download_audio_sync(
    self,
    url: str,
    opts: Dict[str, Any],
    preferred_language: Optional[str] = None,
    preferred_quality: Optional[str] = None  # NEW
) -> tuple[str, str]:
```

Update format selection call (lines 243-249):

```python
if (preferred_language and preferred_language != "original") or preferred_quality:
    format_id = self._select_format_by_language(
        info,
        preferred_language or 'en',
        preferred_quality  # NEW
    )

    if format_id:
        opts = opts.copy()
        opts['format'] = format_id
        logger.info(f"Using format {format_id} (lang: {preferred_language}, quality: {preferred_quality})")
```

### Phase 2: Database Schema (2 hours)

#### 2.1 Create Migration

**File**: `backend/alembic/versions/XXXXXX_add_audio_quality_fields.py`

```python
"""add audio quality fields

Revision ID: XXXXXX
Revises: 349f33ec2697
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'XXXXXX'
down_revision: Union[str, None] = '349f33ec2697'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # User settings: default quality preference
    op.add_column('user_settings',
        sa.Column('preferred_audio_quality', sa.String(10), server_default='low', nullable=False)
    )

    # Episodes: track requested and actual quality
    op.add_column('episodes',
        sa.Column('requested_audio_quality', sa.String(10), nullable=True)
    )
    op.add_column('episodes',
        sa.Column('actual_audio_quality', sa.String(10), nullable=True)
    )

def downgrade() -> None:
    op.drop_column('user_settings', 'preferred_audio_quality')
    op.drop_column('episodes', 'actual_audio_quality')
    op.drop_column('episodes', 'requested_audio_quality')
```

#### 2.2 Update Domain Entities

**File**: `backend/app/domain/entities/episode.py` (around line 62):

```python
# Audio language tracking (existing)
preferred_audio_language: Optional[str] = None
actual_audio_language: Optional[str] = None

# Audio quality tracking (NEW)
requested_audio_quality: Optional[str] = None
actual_audio_quality: Optional[str] = None
```

**File**: `backend/app/domain/entities/user_settings.py` (around line 26):

```python
preferred_audio_quality: str = "low"  # NEW - default to low for faster downloads

def update_preferred_audio_quality(self, quality: str) -> None:
    """Update preferred audio quality"""
    valid_qualities = ['low', 'medium', 'high']
    if quality not in valid_qualities:
        raise ValueError(f"Invalid quality: {quality}")
    self.preferred_audio_quality = quality
    self.updated_at = datetime.utcnow()
```

#### 2.3 Update Database Models

**File**: `backend/app/infrastructure/database/models/episode.py`:

```python
requested_audio_quality = Column(String(10), nullable=True)
actual_audio_quality = Column(String(10), nullable=True)
```

**File**: `backend/app/infrastructure/database/models/user_settings.py`:

```python
preferred_audio_quality = Column(String(10), server_default='low', nullable=False)
```

### Phase 3: Service Layer (2-3 hours)

#### 3.1 Episode Service

**File**: `backend/app/application/services/episode_service.py` (lines 84-157):

Update signature:

```python
async def create_from_youtube_url(
    self,
    channel_id: int,
    video_url: str,
    user_id: int,
    tags: Optional[List[str]] = None,
    preferred_audio_language: Optional[str] = None,
    preferred_audio_quality: Optional[str] = None  # NEW
) -> Episode:
```

Add quality default logic:

```python
# Get user settings for defaults
user_settings = await self.user_settings_service.get_user_settings(user_id)

# Apply preferences (provided > user setting > default)
if preferred_audio_language is None:
    preferred_audio_language = user_settings.preferred_audio_language

if preferred_audio_quality is None:
    preferred_audio_quality = user_settings.preferred_audio_quality  # NEW

logger.info(f"Preferences - Language: {preferred_audio_language}, Quality: {preferred_audio_quality}")
```

Pass to metadata processing:

```python
episode = self.metadata_service.process_youtube_metadata(
    channel_id=channel_id,
    metadata=metadata,
    tags=tags,
    preferred_audio_language=preferred_audio_language,
    preferred_audio_quality=preferred_audio_quality  # NEW
)
```

#### 3.2 Metadata Processing Service

**File**: `backend/app/application/services/metadata_processing_service.py`:

```python
def process_youtube_metadata(
    self,
    channel_id: int,
    metadata: Dict[str, Any],
    tags: Optional[List[str]] = None,
    preferred_audio_language: Optional[str] = None,
    preferred_audio_quality: Optional[str] = None  # NEW
) -> Episode:
    # ... existing processing ...

    episode = Episode.create_episode(
        # ... existing parameters ...
        preferred_audio_language=preferred_audio_language,
        requested_audio_quality=preferred_audio_quality  # NEW
    )
```

#### 3.3 Download Service

**File**: `backend/app/infrastructure/services/download_service.py` (lines 443-459):

```python
download_task = self.youtube_service.download_audio(
    episode.video_url,
    output_path=None,
    progress_callback=progress_hook,
    preferred_language=episode.preferred_audio_language,
    preferred_quality=episode.requested_audio_quality  # NEW
)

file_path, actual_language = await asyncio.wait_for(download_task, timeout=self.download_timeout)

episode.actual_audio_language = actual_language
episode.actual_audio_quality = await self._detect_audio_quality(file_path)  # NEW
```

Add quality detection helper:

```python
async def _detect_audio_quality(self, file_path: str) -> str:
    """Detect audio quality from file bitrate"""
    try:
        from mutagen import File as MutagenFile
        audio = MutagenFile(file_path)
        if audio and audio.info:
            bitrate = getattr(audio.info, 'bitrate', 0) / 1000  # kbps
            if bitrate < 70:
                return 'low'
            elif bitrate < 150:
                return 'medium'
            else:
                return 'high'
    except Exception as e:
        logger.warning(f"Failed to detect quality: {e}")
    return 'unknown'
```

### Phase 4: API Layer (1-2 hours)

#### 4.1 Schemas

**File**: `backend/app/presentation/schemas/episode_schemas.py`:

```python
class EpisodeCreate(BaseModel):
    channel_id: int = Field(..., gt=0)
    video_url: str = Field(..., min_length=1, max_length=2048)
    tags: Optional[List[str]] = Field(default=[])
    preferred_audio_language: Optional[str] = None
    preferred_audio_quality: Optional[str] = None  # NEW

    @validator('preferred_audio_quality')
    def validate_quality(cls, v):
        if v is None:
            return v
        if v not in ['low', 'medium', 'high']:
            raise ValueError("Must be 'low', 'medium', or 'high'")
        return v

class EpisodeResponse(BaseModel):
    # ... existing fields ...
    preferred_audio_language: Optional[str] = None
    actual_audio_language: Optional[str] = None
    requested_audio_quality: Optional[str] = None  # NEW
    actual_audio_quality: Optional[str] = None     # NEW
```

**File**: `backend/app/presentation/schemas/user_settings_schemas.py`:

```python
class UserSettingsResponse(BaseModel):
    # ... existing fields ...
    preferred_audio_quality: str  # NEW

class UserSettingsUpdate(BaseModel):
    # ... existing fields ...
    preferred_audio_quality: Optional[str] = Field(None, regex="^(low|medium|high)$")
```

#### 4.2 API Endpoints

**File**: `backend/app/presentation/api/v1/episodes.py` (lines 274-407):

```python
@router.post("/", response_model=EpisodeResponse, status_code=201)
async def create_episode(episode_data: EpisodeCreate, ...):
    episode = await episode_service.create_from_youtube_url(
        channel_id=episode_data.channel_id,
        video_url=validation['normalized_url'],
        user_id=channel.user_id,
        tags=episode_data.tags,
        preferred_audio_language=episode_data.preferred_audio_language,
        preferred_audio_quality=episode_data.preferred_audio_quality  # NEW
    )
```

### Phase 5: Frontend (3-4 hours)

#### 5.1 TypeScript Types

**File**: `frontend/src/types/index.ts`:

```typescript
export interface Episode {
  // ... existing ...
  requested_audio_quality: string | null // NEW
  actual_audio_quality: string | null // NEW
}

export interface UserSettings {
  // ... existing ...
  preferred_audio_quality: string // NEW
}

export interface QualityOption {
  value: string
  label: string
  description: string
  bitrate: string
}
```

#### 5.2 API Client

**File**: `frontend/src/lib/api-client.ts`:

```typescript
export const availableQualities: QualityOption[] = [
  {
    value: "low",
    label: "Low Quality",
    description: "Faster downloads, smaller files",
    bitrate: "< 70 kbps",
  },
  {
    value: "medium",
    label: "Medium Quality",
    description: "Balanced quality/size",
    bitrate: "70-150 kbps",
  },
  {
    value: "high",
    label: "High Quality",
    description: "Best audio quality",
    bitrate: "> 150 kbps",
  },
]
```

#### 5.3 Quick Add Dialog

**File**: `frontend/src/components/features/episodes/quick-add-dialog.tsx` (lines 38-228):

Add state:

```typescript
const [useCustomQuality, setUseCustomQuality] = useState(false)
const [selectedQuality, setSelectedQuality] = useState<string>("low")
```

Load settings:

```typescript
useEffect(() => {
  const loadSettings = async () => {
    const settings = await apiClient.getUserSettings()
    setSelectedQuality(settings.preferred_audio_quality || "low")
  }
  loadSettings()
}, [open])
```

Submit with quality:

```typescript
const episode = await episodeApi.create({
  channel_id: channel.id,
  video_url: videoUrl.trim(),
  tags: [],
  preferred_audio_language: useCustomLanguage ? selectedLanguage : undefined,
  preferred_audio_quality: useCustomQuality ? selectedQuality : undefined, // NEW
})
```

Add UI (after language selector):

```tsx
<div className="space-y-3 pt-2">
  <div className="flex items-center space-x-2">
    <Checkbox
      id="custom-quality"
      checked={useCustomQuality}
      onCheckedChange={(checked) => setUseCustomQuality(!!checked)}
    />
    <Label htmlFor="custom-quality">Choose audio quality</Label>
  </div>

  {useCustomQuality && (
    <div className="space-y-2 pl-6">
      <Select value={selectedQuality} onValueChange={setSelectedQuality}>
        <SelectTrigger>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {availableQualities.map((q) => (
            <SelectItem key={q.value} value={q.value}>
              <div className="flex flex-col">
                <span className="font-medium">{q.label}</span>
                <span className="text-xs text-muted-foreground">
                  {q.description} ({q.bitrate})
                </span>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )}
</div>
```

#### 5.4 Settings Interface

**File**: `frontend/src/components/features/settings/settings-interface.tsx` (lines 1418-1547):

Add state:

```typescript
const [preferredAudioQuality, setPreferredAudioQuality] =
  useState<string>("low")
const [originalPreferredAudioQuality, setOriginalPreferredAudioQuality] =
  useState<string>("low")
```

Update change detection:

```typescript
useEffect(() => {
  const changed =
    // ... existing checks ...
    preferredAudioQuality !== originalPreferredAudioQuality // NEW
  setHasUnsavedChanges(changed)
}, [
  /* ... existing deps ..., */ preferredAudioQuality,
  originalPreferredAudioQuality,
])
```

Add UI (after language selector around line 1727):

```tsx
<Separator />
<div>
  <Label htmlFor="preferred-audio-quality">Preferred Audio Quality</Label>
  <Select value={preferredAudioQuality} onValueChange={setPreferredAudioQuality}>
    <SelectTrigger id="preferred-audio-quality">
      <SelectValue />
    </SelectTrigger>
    <SelectContent>
      {availableQualities.map((q) => (
        <SelectItem key={q.value} value={q.value}>
          <div className="flex flex-col py-1">
            <span className="font-medium">{q.label}</span>
            <span className="text-xs text-muted-foreground">
              {q.description} ({q.bitrate})
            </span>
          </div>
        </SelectItem>
      ))}
    </SelectContent>
  </Select>
  <p className="text-sm text-muted-foreground mt-2">
    Lower quality = faster downloads + less disk space
  </p>
</div>
```

## Critical Files Summary

### Backend (Python)

1. `backend/app/infrastructure/services/youtube_service.py` - Core fix + quality filtering
2. `backend/app/domain/entities/episode.py` - Add quality fields
3. `backend/app/domain/entities/user_settings.py` - Add quality preference
4. `backend/app/application/services/episode_service.py` - Pass quality through
5. `backend/app/infrastructure/services/download_service.py` - Detect actual quality
6. `backend/app/presentation/schemas/episode_schemas.py` - API schemas
7. `backend/alembic/versions/XXXXXX_add_audio_quality_fields.py` - Migration

### Frontend (TypeScript)

1. `frontend/src/components/features/episodes/quick-add-dialog.tsx` - Quality selector UI
2. `frontend/src/components/features/settings/settings-interface.tsx` - Default quality setting
3. `frontend/src/types/index.ts` - Type definitions
4. `frontend/src/lib/api-client.ts` - Quality options

## Testing Strategy

### Manual Testing (Most Important)

Test with this video: `https://www.youtube.com/watch?v=hQaN5w3YwtM` (has Spanish audio)

1. **Verify Language Detection Fix**:

   - Create episode with Spanish language via Quick Add Dialog
   - Check logs for: `"Found X format(s) with language 'es'"`
   - Verify format selection: `"Selected format 140-2 for 'es'"`
   - Confirm NO fallback to original language

2. **Verify Quality Selection**:

   - Create episode with low quality → check bitrate < 70 kbps
   - Create episode with medium quality → check bitrate 70-150 kbps
   - Create episode with high quality → check bitrate > 150 kbps

3. **Verify Database Persistence**:
   - Check `requested_audio_quality` matches selection
   - Check `actual_audio_quality` detected from file

### Integration Test Commands

```bash
# Backend
cd backend
uv run alembic upgrade head  # Apply migration
uv run fastapi dev app/main.py  # Start backend

# Frontend
cd frontend
npm run dev  # Start frontend

# Test episode creation
# 1. Open Quick Add Dialog
# 2. Paste: https://www.youtube.com/watch?v=hQaN5w3YwtM
# 3. Check "Download in different language" → Select Spanish
# 4. Check "Choose audio quality" → Select Low
# 5. Submit
# 6. Verify logs show Spanish format selection
# 7. Verify episode downloaded in Spanish (not English)
```

## Deployment

### Local Development

```bash
# 1. Run migration
cd backend
uv run alembic upgrade head

# 2. Restart services
cd ..
docker compose --env-file .env.development -f docker-compose.dev.yml restart backend-dev frontend-dev

# 3. Test with video URL above
```

### Production

```bash
# 1. Backup database
cp backend/data/labcastarr.db backend/data/labcastarr.db.backup

# 2. Run migration
docker compose --env-file .env.production -f docker-compose.prod.yml exec backend-prod uv run alembic upgrade head

# 3. Rebuild and restart
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d
```

## Success Criteria

✅ Spanish audio downloads correctly (no fallback to English)
✅ Quality selection reduces file sizes (low < medium < high)
✅ Database stores requested/actual quality and language
✅ Frontend UI allows quality selection in Quick Add and Settings
✅ Existing episodes work without quality fields (backward compatible)
✅ Logs clearly show format selection reasoning

## Rollback Plan

If issues occur:

```bash
# Rollback database
cd backend
uv run alembic downgrade -1

# Rollback code
git revert <commit-hash>

# Restart services
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d
```

## Timeline Estimate

- Phase 1 (Backend Core): 4-6 hours
- Phase 2 (Database): 2 hours
- Phase 3 (Services): 2-3 hours
- Phase 4 (API): 1-2 hours
- Phase 5 (Frontend): 3-4 hours
- Testing: 2-3 hours

**Total**: 14-20 hours

## Key Insights from Research

From web search analysis ([yt-dlp format selection docs](https://github.com/yt-dlp/yt-dlp/issues/12105), [Python API usage](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py)):

1. **Format String Limitations**: The `[language=XX]` filter in yt-dlp format strings is unreliable for composite format IDs
2. **Explicit Format Selection**: Using specific format IDs (like `140-2`) works better than filter expressions
3. **Metadata Parsing**: Language information often in `format_note` or `format` string, not `language` field
4. **Quality Mapping**: Bitrate ranges are industry-standard for podcast quality tiers

## Sources

- [How to select a specific language for an audio format? · Issue #12105 · yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp/issues/12105)
- [yt-dlp/yt_dlp/YoutubeDL.py at master · yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py)
- [Format Selection in yt-dlp](https://yt-dlp.eknerd.com/docs/advanced%20features/format-selection/)
- [How to Use YT-DLP: Guide and Commands (2025)](https://www.rapidseedbox.com/blog/yt-dlp-complete-guide)
