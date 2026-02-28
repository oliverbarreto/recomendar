# Implementation Plan: Fix Audio Language Selection & Add Quality Preferences

## Executive Summary

This plan addresses the YouTube audio download language selection failure and adds quality preference functionality. The root cause is that yt-dlp format metadata doesn't
reliably populate the `language` field for composite format IDs (dubbed tracks), requiring enhanced format detection and quality-based filtering.

## Problem Analysis

### Current Issues

1.  **Language Selection Fails**: `_select_format_by_language()` returns None despite Spanish tracks being available

    - Format metadata lacks `language` field for composite IDs (`140-2`, `251-6`, etc.)
    - Only checks `fmt.get('language')` which is unreliable
    - Logs show: "No format found with language 'es', will use fallback"

2.  **No Quality Control**: Downloads default to best quality, wasting bandwidth and storage

    - User wants `low`, `medium`, `high` quality options (default: `low`)
    - No bitrate-based filtering exists

3.  **Format String Limitation**: `_build_format_string()` relies on yt-dlp's language filtering which doesn't work for composite formats

### Test Data Confirms Issue

From `yt-dlp -F` output, Spanish audio tracks exist:

```
139-7   m4a   audio only [es] Spanish, low, m4a_dash (49k)
140-2   m4a   audio only [es] Spanish, medium, m4a_dash (129k)
249-1   webm  audio only [es] Spanish, low, webm_dash (47k)
251-4   webm  audio only [es] Spanish, medium, webm_dash (132k)
```

But `_select_format_by_language()` can't find them because:

- Format IDs are composite (`140-2` not `140`)
- `language` field may be missing or in different format
- No fallback to parse format note or description

## Implementation Plan

### Phase 1: Fix Language Detection (Backend Core)

#### 1.1 Enhance `_select_format_by_language()` Method

**File**: `/Users/oliver/local/dev/labcastarr/backend/app/infrastructure/services/youtube_service.py`

**Changes** (lines 371-438):

```python
def _select_format_by_language(self, info_dict: Dict[str, Any], preferred_language: str, preferred_quality: Optional[str] = None) -> Optional[str]:
    """
    Select best audio format matching preferred language and quality

    Enhanced to:
    1. Parse composite format IDs (e.g., 140-2 for dubbed tracks)
    2. Extract language from multiple metadata sources
    3. Filter by quality (bitrate ranges)
    4. Maintain format priority: m4a > mp3 (iTunes/Spotify compatible)

    Args:
        info_dict: yt-dlp info dictionary
        preferred_language: ISO 639-1 language code (e.g., 'es', 'en')
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

    # Step 1: Filter by language (enhanced detection)
    matching_formats = []

    for fmt in audio_formats:
        # Check multiple language sources
        lang = self._extract_format_language(fmt)

        if lang and lang.lower() == preferred_language.lower():
            matching_formats.append(fmt)

    if not matching_formats:
        logger.info(f"No format found with language '{preferred_language}' using enhanced detection")
        return None

    logger.info(f"Found {len(matching_formats)} format(s) with language '{preferred_language}'")

    # Step 2: Filter by quality if specified
    if preferred_quality:
        quality_filtered = self._filter_by_quality(matching_formats, preferred_quality)
        if quality_filtered:
            matching_formats = quality_filtered
        else:
            logger.warning(f"No {preferred_quality} quality formats found, using all available")

    # Step 3: Apply format priority (m4a > mp3)
    for ext_priority in ['m4a', 'mp3']:
        candidates = [f for f in matching_formats if f.get('ext') == ext_priority]

        if not candidates:
            continue

        # Sort by audio bitrate (descending)
        candidates_sorted = sorted(
            candidates,
            key=lambda f: f.get('abr', 0) or 0,
            reverse=True
        )

        best_format = candidates_sorted[0]
        format_id = best_format.get('format_id')

        logger.info(
            f"Selected format {format_id} for language '{preferred_language}' "
            f"(quality: {preferred_quality or 'best'}): "
            f"ext={best_format.get('ext')}, "
            f"abr={best_format.get('abr', 'unknown')} kbps"
        )

        return format_id

    logger.info(f"No m4a/mp3 format found with language '{preferred_language}'")
    return None

def _extract_format_language(self, fmt: Dict[str, Any]) -> Optional[str]:
    """
    Extract language from format metadata using multiple sources

    Checks (in order):
    1. Direct 'language' field
    2. 'language_preference' or 'lang' fields
    3. Parse from 'format_note' or 'format' string (e.g., "[es] Spanish")
    4. Parse from 'format_id' for multi-audio tracks

    Args:
        fmt: yt-dlp format dictionary

    Returns:
        ISO 639-1 language code or None
    """
    # 1. Direct language field
    lang = fmt.get('language')
    if lang and lang != 'none':
        return lang.strip()

    # 2. Alternative language fields
    lang = fmt.get('lang') or fmt.get('language_preference')
    if lang and lang != 'none':
        return str(lang).strip()

    # 3. Parse from format_note (e.g., "Spanish, medium")
    format_note = fmt.get('format_note', '')
    if format_note:
        # Common language names in format notes
        lang_map = {
            'spanish': 'es',
            'english': 'en',
            'french': 'fr',
            'german': 'de',
            'italian': 'it',
            'portuguese': 'pt',
            'japanese': 'ja',
            'korean': 'ko',
            'chinese': 'zh',
            'russian': 'ru',
            'arabic': 'ar'
        }

        note_lower = format_note.lower()
        for lang_name, lang_code in lang_map.items():
            if lang_name in note_lower:
                logger.debug(f"Extracted language '{lang_code}' from format_note: {format_note}")
                return lang_code

    # 4. Parse from format string (e.g., "139 - [es] Spanish")
    format_str = fmt.get('format', '')
    if format_str:
        # Look for [xx] pattern (ISO language code)
        import re
        lang_match = re.search(r'\[([a-z]{2})\]', format_str.lower())
        if lang_match:
            lang_code = lang_match.group(1)
            logger.debug(f"Extracted language '{lang_code}' from format string: {format_str}")
            return lang_code

    # 5. Check if this is a multi-audio track format (composite ID like "140-2")
    format_id = fmt.get('format_id', '')
    if '-' in format_id and format_id.split('-')[1].isdigit():
        # Composite format ID indicates alternate audio track
        # These are typically dubbed tracks, but we can't determine language without metadata
        logger.debug(f"Detected multi-audio track format {format_id}, but no language metadata")

    return None

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
        logger.warning(f"Invalid quality '{quality}', must be 'low', 'medium', or 'high'")
        return formats

    min_br, max_br = bitrate_ranges[quality]

    filtered = []
    for fmt in formats:
        abr = fmt.get('abr', 0) or 0
        if min_br <= abr < max_br:
            filtered.append(fmt)

    logger.debug(f"Filtered {len(formats)} formats to {len(filtered)} formats for quality '{quality}'")
    return filtered
```

**Key Changes**:

- Add `preferred_quality` parameter to `_select_format_by_language()`
- Implement `_extract_format_language()` to check multiple metadata sources
- Implement `_filter_by_quality()` for bitrate-based quality filtering
- Parse format notes, format strings, and composite format IDs
- Maintain format priority (m4a > mp3) and fallback logic

#### 1.2 Update `_download_audio_sync()` Method

**File**: `/Users/oliver/local/dev/labcastarr/backend/app/infrastructure/services/youtube_service.py`

**Changes** (lines 220-302):

```python
def _download_audio_sync(self, url: str, opts: Dict[str, Any], preferred_language: Optional[str] = None, preferred_quality: Optional[str] = None) -> tuple[str, str]:
    """
    Synchronous audio download with language and quality preferences

    Args:
        url: YouTube video URL
        opts: yt-dlp options dictionary
        preferred_language: Preferred audio language (ISO 639-1 code or "original")
        preferred_quality: Preferred audio quality ('low', 'medium', 'high')

    Returns:
        Tuple of (audio file path, actual language downloaded)
    """
    info = None

    with yt_dlp.YoutubeDL(opts) as ydl:
        # Get video info to determine final filename and language
        info = ydl.extract_info(url, download=False)

        # Log available formats for debugging
        if info and 'formats' in info:
            self._log_available_formats(info, opts.get('format', 'unknown'))

        # Try explicit format selection if preferences specified
        if (preferred_language and preferred_language != "original") or preferred_quality:
            format_id = self._select_format_by_language(
                info,
                preferred_language or 'en',  # Default to English if only quality specified
                preferred_quality
            )

            if format_id:
                # Update options to use specific format
                opts = opts.copy()
                opts['format'] = format_id
                logger.info(f"Using explicit format selection: {format_id} (language: {preferred_language}, quality: {preferred_quality})")

                # Recreate YoutubeDL with updated options
                with yt_dlp.YoutubeDL(opts) as ydl_specific:
                    ydl_specific.download([url])
            else:
                # Fall back to format string-based selection
                logger.info(f"No exact match found, falling back to format string (language: {preferred_language}, quality: {preferred_quality})")
                ydl.download([url])
        else:
            ydl.download([url])

    # ... rest of method unchanged ...
```

#### 1.3 Update `download_audio()` Method Signature

**File**: `/Users/oliver/local/dev/labcastarr/backend/app/infrastructure/services/youtube_service.py`

**Changes** (lines 160-218):

```python
async def download_audio(
    self,
    url: str,
    output_path: Optional[str] = None,
    progress_callback: Optional[Callable] = None,
    preferred_language: Optional[str] = None,
    preferred_quality: Optional[str] = None  # NEW PARAMETER
) -> tuple[str, str]:
    """
    Download audio file from YouTube with language and quality preferences

    Args:
        url: YouTube video URL
        output_path: Custom output path (optional)
        progress_callback: Callback for progress updates
        preferred_language: Preferred audio language (ISO 639-1 code or "original")
        preferred_quality: Preferred audio quality ('low', 'medium', 'high')

    Returns:
        Tuple of (path to downloaded audio file, actual language downloaded)

    Raises:
        YouTubeDownloadError: If download fails
    """
    try:
        logger.info(f"Starting download for URL: {url} with language: {preferred_language}, quality: {preferred_quality}")

        # ... rest of method updated to pass preferred_quality ...

        audio_path, actual_language = await loop.run_in_executor(
            None,
            self._download_audio_sync,
            url,
            download_opts,
            preferred_language,
            preferred_quality  # Pass quality preference
        )
```

### Phase 2: Database Schema Changes

#### 2.1 Create Alembic Migration

**File**: `/Users/oliver/local/dev/labcastarr/backend/alembic/versions/XXXXXX_add_audio_quality_fields.py`

```python
"""add audio quality fields to episodes and user_settings

Revision ID: XXXXXX
Revises: 349f33ec2697
Create Date: 2025-12-08 XX:XX:XX
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = 'XXXXXX'
down_revision: Union[str, None] = '349f33ec2697'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Add audio quality fields"""
    # Add quality preference to user_settings
    op.add_column('user_settings',
        sa.Column('preferred_audio_quality', sa.String(length=10), server_default='low', nullable=False)
    )

    # Add quality tracking to episodes
    op.add_column('episodes',
        sa.Column('requested_audio_quality', sa.String(length=10), nullable=True)
    )
    op.add_column('episodes',
        sa.Column('actual_audio_quality', sa.String(length=10), nullable=True)
    )

def downgrade() -> None:
    """Remove audio quality fields"""
    op.drop_column('user_settings', 'preferred_audio_quality')
    op.drop_column('episodes', 'actual_audio_quality')
    op.drop_column('episodes', 'requested_audio_quality')
```

**Rationale**:

- `preferred_audio_quality` in `user_settings`: Default quality for all downloads (default: 'low' for faster downloads)
- `requested_audio_quality` in `episodes`: What user requested for this specific episode
- `actual_audio_quality` in `episodes`: What was actually downloaded (for fallback tracking)

#### 2.2 Update Domain Entities

**File**: `/Users/oliver/local/dev/labcastarr/backend/app/domain/entities/episode.py`

**Changes** (lines 62-64):

```python
# Audio language tracking (existing)
preferred_audio_language: Optional[str] = None
actual_audio_language: Optional[str] = None

# Audio quality tracking (NEW)
requested_audio_quality: Optional[str] = None  # What user requested ('low', 'medium', 'high')
actual_audio_quality: Optional[str] = None     # What was actually downloaded
```

**File**: `/Users/oliver/local/dev/labcastarr/backend/app/domain/entities/user_settings.py`

**Changes** (lines 26-27):

```python
preferred_audio_language: str = "original"      # Existing
preferred_audio_quality: str = "low"           # NEW - default to low for faster downloads

def update_preferred_audio_quality(self, quality: str) -> None:
    """
    Update preferred audio quality for downloads

    Args:
        quality: Quality level ('low', 'medium', 'high')
    """
    valid_qualities = ['low', 'medium', 'high']
    if quality not in valid_qualities:
        raise ValueError(f"Invalid quality: {quality}. Must be one of: {', '.join(valid_qualities)}")

    self.preferred_audio_quality = quality
    self.updated_at = datetime.utcnow()
```

#### 2.3 Update Database Models

**File**: `/Users/oliver/local/dev/labcastarr/backend/app/infrastructure/database/models/episode.py`

Add columns:

```python
requested_audio_quality = Column(String(10), nullable=True)
actual_audio_quality = Column(String(10), nullable=True)
```

**File**: `/Users/oliver/local/dev/labcastarr/backend/app/infrastructure/database/models/user_settings.py`

Add column:

```python
preferred_audio_quality = Column(String(10), server_default='low', nullable=False)
```

### Phase 3: Service Layer Updates

#### 3.1 Update Episode Service

**File**: `/Users/oliver/local/dev/labcastarr/backend/app/application/services/episode_service.py`

**Changes** (lines 84-157):

```python
async def create_from_youtube_url(
    self,
    channel_id: int,
    video_url: str,
    user_id: int,
    tags: Optional[List[str]] = None,
    preferred_audio_language: Optional[str] = None,
    preferred_audio_quality: Optional[str] = None  # NEW PARAMETER
) -> Episode:
    """
    Create episode from YouTube URL with language and quality preferences

    Args:
        channel_id: Channel to associate episode with
        video_url: YouTube video URL
        user_id: ID of user creating the episode
        tags: Optional tags for episode
        preferred_audio_language: Optional language preference (overrides user setting)
        preferred_audio_quality: Optional quality preference (overrides user setting)

    Returns:
        Created Episode entity
    """
    try:
        logger.info(f"Creating episode from YouTube URL: {video_url}")
        logger.info(f"Preferences - Language: {preferred_audio_language}, Quality: {preferred_audio_quality}")

        # Get user settings for defaults
        user_settings = await self.user_settings_service.get_user_settings(user_id)

        # Apply preferences (provided > user setting > default)
        if preferred_audio_language is None:
            preferred_audio_language = user_settings.preferred_audio_language

        if preferred_audio_quality is None:
            preferred_audio_quality = user_settings.preferred_audio_quality

        logger.info(f"Final preferences - Language: {preferred_audio_language}, Quality: {preferred_audio_quality}")

        # ... existing validation and metadata extraction ...

        # Process metadata with both language and quality preferences
        episode = self.metadata_service.process_youtube_metadata(
            channel_id=channel_id,
            metadata=metadata,
            tags=tags,
            preferred_audio_language=preferred_audio_language,
            preferred_audio_quality=preferred_audio_quality  # Pass quality
        )

        # ... rest of method unchanged ...
```

#### 3.2 Update Metadata Processing Service

**File**: `/Users/oliver/local/dev/labcastarr/backend/app/application/services/metadata_processing_service.py`

Update `process_youtube_metadata()` to accept and store `preferred_audio_quality`:

```python
def process_youtube_metadata(
    self,
    channel_id: int,
    metadata: Dict[str, Any],
    tags: Optional[List[str]] = None,
    preferred_audio_language: Optional[str] = None,
    preferred_audio_quality: Optional[str] = None  # NEW PARAMETER
) -> Episode:
    """
    Process YouTube metadata into Episode entity

    Args:
        channel_id: Channel ID
        metadata: Metadata from YouTubeService
        tags: Optional tags
        preferred_audio_language: Preferred audio language
        preferred_audio_quality: Preferred audio quality
    """
    # ... existing metadata processing ...

    episode = Episode.create_episode(
        # ... existing parameters ...
        preferred_audio_language=preferred_audio_language,
        requested_audio_quality=preferred_audio_quality  # NEW
    )

    return episode
```

#### 3.3 Update Download Service

**File**: `/Users/oliver/local/dev/labcastarr/backend/app/infrastructure/services/download_service.py`

**Changes** (lines 443-459):

```python
# Download audio with timeout, language, and quality preferences
try:
    download_task = self.youtube_service.download_audio(
        episode.video_url,
        output_path=None,
        progress_callback=progress_hook,
        preferred_language=episode.preferred_audio_language,
        preferred_quality=episode.requested_audio_quality  # NEW - pass quality preference
    )

    file_path, actual_language = await asyncio.wait_for(
        download_task,
        timeout=self.download_timeout
    )

    # Update episode with actual language downloaded
    episode.actual_audio_language = actual_language

    # Detect actual quality from downloaded file (NEW)
    episode.actual_audio_quality = await self._detect_audio_quality(file_path)

    logger.info(
        f"Downloaded audio for episode {episode_id}: "
        f"language={actual_language}, "
        f"quality={episode.actual_audio_quality}"
    )
```

Add helper method:

```python
async def _detect_audio_quality(self, file_path: str) -> str:
    """
    Detect audio quality from file bitrate

    Args:
        file_path: Path to audio file

    Returns:
        Quality tier ('low', 'medium', 'high')
    """
    try:
        from mutagen import File as MutagenFile

        audio = MutagenFile(file_path)
        if audio and audio.info:
            bitrate = getattr(audio.info, 'bitrate', 0) / 1000  # Convert to kbps

            if bitrate < 70:
                return 'low'
            elif bitrate < 150:
                return 'medium'
            else:
                return 'high'
    except Exception as e:
        logger.warning(f"Failed to detect audio quality: {e}")

    return 'unknown'
```

### Phase 4: API Layer Updates

#### 4.1 Update Episode Schemas

**File**: `/Users/oliver/local/dev/labcastarr/backend/app/presentation/schemas/episode_schemas.py`

**Changes** (lines 20-66):

```python
class EpisodeCreate(BaseModel):
    """Schema for creating new episodes"""
    channel_id: int = Field(..., gt=0)
    video_url: str = Field(..., min_length=1, max_length=2048)
    tags: Optional[List[str]] = Field(default=[])
    preferred_audio_language: Optional[str] = Field(
        default=None,
        description="Preferred audio language (ISO 639-1 code or 'original')"
    )
    preferred_audio_quality: Optional[str] = Field(  # NEW
        default=None,
        description="Preferred audio quality ('low', 'medium', 'high'). If not specified, uses user's setting."
    )

    @validator('preferred_audio_quality')
    def validate_quality(cls, v):
        """Validate quality level"""
        if v is None:
            return v
        valid_qualities = ['low', 'medium', 'high']
        if v not in valid_qualities:
            raise ValueError(f"Invalid quality. Must be one of: {', '.join(valid_qualities)}")
        return v
```

**Changes** (lines 124-169):

```python
class EpisodeResponse(BaseModel):
    """Schema for episode API responses"""
    # ... existing fields ...

    # Audio language tracking (existing)
    preferred_audio_language: Optional[str] = None
    actual_audio_language: Optional[str] = None

    # Audio quality tracking (NEW)
    requested_audio_quality: Optional[str] = None
    actual_audio_quality: Optional[str] = None
```

#### 4.2 Update Episode API Endpoint

**File**: `/Users/oliver/local/dev/labcastarr/backend/app/presentation/api/v1/episodes.py`

**Changes** (lines 274-407):

```python
@router.post("/", response_model=EpisodeResponse, status_code=201)
async def create_episode(
    episode_data: EpisodeCreate,
    background_tasks: BackgroundTasks,
    episode_service: EpisodeService = Depends(get_episode_service),
    url_validator: URLValidationService = Depends(get_url_validation_service),
    download_service: DownloadService = Depends(get_download_service)
):
    """
    Create a new episode from YouTube URL with language and quality preferences
    """
    # ... existing validation ...

    # Create episode with metadata extraction
    episode = await episode_service.create_from_youtube_url(
        channel_id=episode_data.channel_id,
        video_url=validation['normalized_url'],
        user_id=channel.user_id,
        tags=episode_data.tags,
        preferred_audio_language=episode_data.preferred_audio_language,
        preferred_audio_quality=episode_data.preferred_audio_quality  # NEW
    )

    # ... rest unchanged ...
```

#### 4.3 Update User Settings Schemas

**File**: `/Users/oliver/local/dev/labcastarr/backend/app/presentation/schemas/user_settings_schemas.py`

Add quality field:

```python
class UserSettingsResponse(BaseModel):
    """User settings response schema"""
    # ... existing fields ...
    preferred_audio_language: str
    preferred_audio_quality: str  # NEW

class UserSettingsUpdate(BaseModel):
    """User settings update schema"""
    # ... existing fields ...
    preferred_audio_quality: Optional[str] = Field(None, regex="^(low|medium|high)$")
```

### Phase 5: Frontend Updates

#### 5.1 Update TypeScript Types

**File**: `/Users/oliver/local/dev/labcastarr/frontend/src/types/index.ts`

```typescript
export interface Episode {
  // ... existing fields ...
  preferred_audio_language: string | null
  actual_audio_language: string | null
  requested_audio_quality: string | null // NEW
  actual_audio_quality: string | null // NEW
}

export interface UserSettings {
  // ... existing fields ...
  preferred_audio_language: string
  preferred_audio_quality: string // NEW
}

export interface QualityOption {
  // NEW
  value: string
  label: string
  description: string
  bitrate: string
}
```

#### 5.2 Update API Client

**File**: `/Users/oliver/local/dev/labcastarr/frontend/src/lib/api-client.ts`

Add quality options:

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
    description: "Balanced quality and size",
    bitrate: "70-150 kbps",
  },
  {
    value: "high",
    label: "High Quality",
    description: "Best audio quality",
    bitrate: "> 150 kbps",
  },
]

// Update getUserSettings, updateUserSettings to include quality
```

#### 5.3 Update Quick Add Dialog

**File**: `/Users/oliver/local/dev/labcastarr/frontend/src/components/features/episodes/quick-add-dialog.tsx`

**Changes** (lines 38-228):

```typescript
export function QuickAddDialog({
  open,
  onOpenChange,
  onSuccess,
}: QuickAddDialogProps) {
  const [videoUrl, setVideoUrl] = useState("")
  const [isLoading, setIsLoading] = useState(false)

  // Language preferences (existing)
  const [useCustomLanguage, setUseCustomLanguage] = useState(false)
  const [selectedLanguage, setSelectedLanguage] = useState<string>("original")
  const [availableLanguages, setAvailableLanguages] = useState<
    LanguageOption[]
  >([])

  // Quality preferences (NEW)
  const [useCustomQuality, setUseCustomQuality] = useState(false)
  const [selectedQuality, setSelectedQuality] = useState<string>("low")

  // Load language and quality settings when dialog opens
  useEffect(() => {
    const loadSettings = async () => {
      if (!open) return

      try {
        const [languages, settings] = await Promise.all([
          apiClient.getAvailableLanguages(),
          apiClient.getUserSettings(),
        ])

        setAvailableLanguages(languages)
        setSelectedLanguage(settings.preferred_audio_language || "original")
        setSelectedQuality(settings.preferred_audio_quality || "low") // NEW
      } catch (error) {
        console.error("Failed to load settings:", error)
      }
    }

    loadSettings()
  }, [open])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    // ... existing validation ...

    try {
      setIsLoading(true)

      // ... get channel ...

      // Create episode with language and quality preferences
      const episode = await episodeApi.create({
        channel_id: channel.id,
        video_url: videoUrl.trim(),
        tags: [],
        preferred_audio_language: useCustomLanguage
          ? selectedLanguage
          : undefined,
        preferred_audio_quality: useCustomQuality ? selectedQuality : undefined, // NEW
      })

      toast.success(`Episode "${episode.title}" has been added!`)

      // Reset form
      setVideoUrl("")
      setUseCustomLanguage(false)
      setUseCustomQuality(false) // NEW
      onOpenChange(false)

      if (onSuccess) onSuccess()
    } catch (error: unknown) {
      // ... error handling ...
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Youtube className="h-5 w-5 text-red-600" />
            Quick Add Episode
          </DialogTitle>
          <DialogDescription>
            Paste a YouTube URL to quickly add a new episode with optional
            language and quality preferences.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* YouTube URL Input (existing) */}
          <div className="space-y-2">
            <Label htmlFor="video-url">YouTube URL</Label>
            <Input
              id="video-url"
              type="url"
              placeholder="https://www.youtube.com/watch?v=..."
              value={videoUrl}
              onChange={(e) => setVideoUrl(e.target.value)}
              disabled={isLoading}
            />
          </div>

          {/* Language Selection (existing) */}
          <div className="space-y-3 pt-2">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="custom-language"
                checked={useCustomLanguage}
                onCheckedChange={(checked) => setUseCustomLanguage(!!checked)}
                disabled={isLoading}
              />
              <Label
                htmlFor="custom-language"
                className="text-sm font-normal cursor-pointer"
              >
                Download in different language
              </Label>
            </div>

            {useCustomLanguage && (
              <div className="space-y-2 pl-6">
                <Select
                  value={selectedLanguage}
                  onValueChange={setSelectedLanguage}
                  disabled={isLoading}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select language" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableLanguages.map((lang) => (
                      <SelectItem key={lang.code} value={lang.code}>
                        {lang.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  If this language is unavailable, the original audio will be
                  downloaded.
                </p>
              </div>
            )}
          </div>

          {/* Quality Selection (NEW) */}
          <div className="space-y-3 pt-2">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="custom-quality"
                checked={useCustomQuality}
                onCheckedChange={(checked) => setUseCustomQuality(!!checked)}
                disabled={isLoading}
              />
              <Label
                htmlFor="custom-quality"
                className="text-sm font-normal cursor-pointer"
              >
                Choose audio quality
              </Label>
            </div>

            {useCustomQuality && (
              <div className="space-y-2 pl-6">
                <Select
                  value={selectedQuality}
                  onValueChange={setSelectedQuality}
                  disabled={isLoading}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select quality" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableQualities.map((quality) => (
                      <SelectItem key={quality.value} value={quality.value}>
                        <div className="flex flex-col">
                          <span className="font-medium">{quality.label}</span>
                          <span className="text-xs text-muted-foreground">
                            {quality.description} ({quality.bitrate})
                          </span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  Lower quality downloads faster and saves disk space. If
                  unavailable, closest quality will be used.
                </p>
              </div>
            )}
          </div>

          {/* Submit buttons (existing) */}
          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading} className="gap-2">
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Adding Episode...
                </>
              ) : (
                <>
                  <Plus className="h-4 w-4" />
                  Add Episode
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
```

#### 5.4 Update Settings Interface

**File**: `/Users/oliver/local/dev/labcastarr/frontend/src/components/features/settings/settings-interface.tsx`

**Changes** (lines 1418-1547):

Add quality state management:

```typescript
// Existing language state
const [preferredAudioLanguage, setPreferredAudioLanguage] = useState<string>("original")
const [originalPreferredAudioLanguage, setOriginalPreferredAudioLanguage] = useState<string>("original")

// NEW: Quality state
const [preferredAudioQuality, setPreferredAudioQuality] = useState<string>("low")
const [originalPreferredAudioQuality, setOriginalPreferredAudioQuality] = useState<string>("low")

// Update loadUserSettings to include quality
const loadUserSettings = async () => {
  try {
    setIsLoadingSettings(true)
    const [settings, timezones, languages] = await Promise.all([
      apiClient.getUserSettings(),
      apiClient.getAvailableTimezones(),
      apiClient.getAvailableLanguages()
    ])

    // ... existing state updates ...

    // NEW: Load quality preference
    if (settings?.preferred_audio_quality) {
      setPreferredAudioQuality(settings.preferred_audio_quality)
      setOriginalPreferredAudioQuality(settings.preferred_audio_quality)
    }

    // ... rest unchanged ...
  }
}

// Update hasUnsavedChanges detection
useEffect(() => {
  const changed =
    subscriptionFrequency !== originalFrequency ||
    preferredCheckHour !== originalHour ||
    preferredCheckMinute !== originalMinute ||
    timezone !== originalTimezone ||
    preferredAudioLanguage !== originalPreferredAudioLanguage ||
    preferredAudioQuality !== originalPreferredAudioQuality  // NEW
  setHasUnsavedChanges(changed)
}, [
  subscriptionFrequency, preferredCheckHour, preferredCheckMinute,
  timezone, preferredAudioLanguage, preferredAudioQuality,  // NEW
  originalFrequency, originalHour, originalMinute,
  originalTimezone, originalPreferredAudioLanguage, originalPreferredAudioQuality  // NEW
])

// Update handleSaveSettings
const handleSaveSettings = async () => {
  try {
    setIsSavingSettings(true)
    const updateData = {
      subscription_check_frequency: subscriptionFrequency,
      preferred_check_hour: preferredCheckHour,
      preferred_check_minute: preferredCheckMinute,
      timezone: timezone,
      preferred_audio_language: preferredAudioLanguage,
      preferred_audio_quality: preferredAudioQuality,  // NEW
    }
    await apiClient.updateUserSettings(updateData)

    // Update originals
    setOriginalPreferredAudioQuality(preferredAudioQuality)  // NEW
    // ... rest unchanged ...
  }
}

// Update handleDiscardChanges
const handleDiscardChanges = () => {
  setPreferredAudioQuality(originalPreferredAudioQuality)  // NEW
  // ... rest unchanged ...
}
```

Add quality selector UI (after language selector around line 1727):

```typescript
;<Separator />

{
  /* Preferred Audio Quality Selector */
}
;<div>
  <Label className="mb-3" htmlFor="preferred-audio-quality">
    Preferred Audio Quality
  </Label>
  <Select
    value={preferredAudioQuality}
    onValueChange={setPreferredAudioQuality}
    disabled={isSavingSettings}
  >
    <SelectTrigger id="preferred-audio-quality">
      <SelectValue placeholder="Select quality" />
    </SelectTrigger>
    <SelectContent>
      {availableQualities.map((quality) => (
        <SelectItem key={quality.value} value={quality.value}>
          <div className="flex flex-col py-1">
            <span className="font-medium">{quality.label}</span>
            <span className="text-xs text-muted-foreground">
              {quality.description} ({quality.bitrate})
            </span>
          </div>
        </SelectItem>
      ))}
    </SelectContent>
  </Select>
  <p className="text-sm text-muted-foreground mt-2">
    Select default audio quality for episode downloads. Lower quality means
    faster downloads and less disk space. This applies to all automatic and
    manual episode creation unless overridden.
  </p>
</div>
```

### Phase 6: Testing Strategy

#### 6.1 Backend Unit Tests

**File**: `/Users/oliver/local/dev/labcastarr/backend/tests/test_youtube_service.py`

```python
import pytest
from app.infrastructure.services.youtube_service import YouTubeService

class TestLanguageDetection:
    """Test enhanced language detection"""

    def test_extract_format_language_from_field(self):
        """Test direct language field extraction"""
        service = YouTubeService()
        fmt = {'language': 'es', 'format_id': '140'}
        assert service._extract_format_language(fmt) == 'es'

    def test_extract_format_language_from_note(self):
        """Test language extraction from format_note"""
        service = YouTubeService()
        fmt = {'format_note': 'Spanish, medium', 'format_id': '140-2'}
        assert service._extract_format_language(fmt) == 'es'

    def test_extract_format_language_from_format_string(self):
        """Test language extraction from format string"""
        service = YouTubeService()
        fmt = {'format': '139 - [es] Spanish', 'format_id': '139-7'}
        assert service._extract_format_language(fmt) == 'es'

    def test_composite_format_id_detection(self):
        """Test composite format ID detection"""
        service = YouTubeService()
        fmt = {'format_id': '140-2', 'format_note': 'Spanish'}
        # Should detect composite ID but may not determine language
        lang = service._extract_format_language(fmt)
        assert lang == 'es' or lang is None  # Depends on format_note parsing

class TestQualityFiltering:
    """Test quality-based format filtering"""

    def test_filter_by_quality_low(self):
        """Test low quality filtering (< 70 kbps)"""
        service = YouTubeService()
        formats = [
            {'abr': 49, 'format_id': '139'},
            {'abr': 129, 'format_id': '140'},
            {'abr': 192, 'format_id': '141'}
        ]
        filtered = service._filter_by_quality(formats, 'low')
        assert len(filtered) == 1
        assert filtered[0]['format_id'] == '139'

    def test_filter_by_quality_medium(self):
        """Test medium quality filtering (70-150 kbps)"""
        service = YouTubeService()
        formats = [
            {'abr': 49, 'format_id': '139'},
            {'abr': 129, 'format_id': '140'},
            {'abr': 192, 'format_id': '141'}
        ]
        filtered = service._filter_by_quality(formats, 'medium')
        assert len(filtered) == 1
        assert filtered[0]['format_id'] == '140'

    def test_filter_by_quality_high(self):
        """Test high quality filtering (> 150 kbps)"""
        service = YouTubeService()
        formats = [
            {'abr': 49, 'format_id': '139'},
            {'abr': 129, 'format_id': '140'},
            {'abr': 192, 'format_id': '141'}
        ]
        filtered = service._filter_by_quality(formats, 'high')
        assert len(filtered) == 1
        assert filtered[0]['format_id'] == '141'

class TestIntegratedSelection:
    """Test integrated language + quality selection"""

    def test_select_format_spanish_low_quality(self):
        """Test selecting Spanish audio in low quality"""
        service = YouTubeService()
        info_dict = {
            'formats': [
                {'format_id': '139-7', 'acodec': 'mp4a', 'ext': 'm4a', 'abr': 49, 'language': 'es'},
                {'format_id': '140-2', 'acodec': 'mp4a', 'ext': 'm4a', 'abr': 129, 'language': 'es'},
                {'format_id': '139', 'acodec': 'mp4a', 'ext': 'm4a', 'abr': 49, 'language': 'en'}
            ]
        }
        format_id = service._select_format_by_language(info_dict, 'es', 'low')
        assert format_id == '139-7'  # Spanish, m4a, low bitrate
```

#### 6.2 Integration Tests

Test real YouTube videos with multi-audio tracks:

```python
@pytest.mark.integration
async def test_download_spanish_audio_low_quality():
    """Test downloading Spanish audio in low quality"""
    service = YouTubeService()
    url = "https://www.youtube.com/watch?v=XXXXX"  # Video with Spanish audio

    file_path, actual_lang = await service.download_audio(
        url,
        preferred_language='es',
        preferred_quality='low'
    )

    assert file_path.endswith('.mp3')
    assert actual_lang == 'es'

    # Verify bitrate is low quality
    from mutagen import File as MutagenFile
    audio = MutagenFile(file_path)
    assert audio.info.bitrate / 1000 < 70  # < 70 kbps
```

#### 6.3 Manual Testing Checklist

1.  **Language Detection**:

    - [ ] Test video with Spanish dubbed audio (composite format IDs)
    - [ ] Verify logs show "Found X format(s) with language 'es'"
    - [ ] Verify format selection succeeds (not falling back to original)
    - [ ] Test fallback when requested language unavailable

2.  **Quality Selection**:

    - [ ] Create episode with low quality → verify bitrate < 70 kbps
    - [ ] Create episode with medium quality → verify bitrate 70-150 kbps
    - [ ] Create episode with high quality → verify bitrate > 150 kbps
    - [ ] Test fallback when exact quality unavailable

3.  **Database Persistence**:

    - [ ] Verify `requested_audio_quality` saved correctly
    - [ ] Verify `actual_audio_quality` detected from file
    - [ ] Verify `preferred_audio_quality` in user_settings

4.  **Frontend UI**:

    - [ ] Quality selector in Quick Add Dialog
    - [ ] Quality preference in Settings → Subscriptions
    - [ ] Display quality in episode details
    - [ ] Unsaved changes detection works

5.  **Notifications**:
    - [ ] Language fallback notification works
    - [ ] Quality fallback notification (if implemented)

### Phase 7: Deployment Steps

1.  **Database Migration**:

    ```bash
    cd backend
    uv run alembic upgrade head
    ```

2.  **Backend Deployment**:

    ```bash
    docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d backend-prod
    ```

3.  **Frontend Deployment**:

    ```bash
    docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d frontend-prod
    ```

4.  **Verify Migration**:

    ```bash
    # Check database schema
    sqlite3 backend/data/labcastarr.db "PRAGMA table_info(episodes);"
    sqlite3 backend/data/labcastarr.db "PRAGMA table_info(user_settings);"
    ```

5.  **Smoke Tests**:
    - Create test episode with Spanish audio, low quality
    - Verify download succeeds with correct language and quality
    - Check logs for format selection details

## Critical Implementation Notes

### 1. Backward Compatibility

- Existing episodes without quality fields: default to `None` (acceptable)
- Existing user_settings: migration sets `preferred_audio_quality='low'` as default
- API endpoints: quality parameter optional, falls back to user setting

### 2. Error Handling

- If language + quality combination unavailable → relax quality constraint first, then language
- Always log actual vs requested quality/language for debugging
- Create notifications for significant fallbacks

### 3. Performance Considerations

- Format parsing adds minimal overhead (< 100ms)
- Quality detection from file (mutagen) is fast (< 50ms)
- No impact on download speed (quality affects file size only)

### 4. Future Enhancements

- Add quality auto-detection based on available bandwidth
- Add codec preference (AAC > Opus > Vorbis)
- Add "adaptive quality" mode that adjusts based on storage space

## Success Criteria

✅ Spanish audio downloads succeed with composite format IDs
✅ Quality preference reduces file sizes (low < medium < high)
✅ Database stores requested and actual quality/language
✅ Frontend UI allows quality selection in Quick Add and Settings
✅ Existing episodes continue to work without quality fields
✅ All tests pass (unit, integration, manual)

## Rollback Plan

If issues occur:

1.  **Database Rollback**:

    ```bash
    cd backend
    uv run alembic downgrade -1
    ```

2.  **Code Rollback**:

    ```bash
    git revert <commit-hash>
    ```

3.  **Frontend Rollback**:
    ```bash
    # Redeploy previous frontend version
    docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d frontend-prod
    ```

## Timeline Estimate

- Phase 1 (Backend Core): 4-6 hours
- Phase 2 (Database): 2 hours
- Phase 3 (Services): 2-3 hours
- Phase 4 (API): 1-2 hours
- Phase 5 (Frontend): 3-4 hours
- Phase 6 (Testing): 2-3 hours
- Phase 7 (Deployment): 1 hour

**Total**: 15-21 hours

---
