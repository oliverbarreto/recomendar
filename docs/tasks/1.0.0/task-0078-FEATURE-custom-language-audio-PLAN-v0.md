# Implementation Plan: Multi-Language Audio Track Support for LabCastARR

## Overview

Add support for downloading YouTube videos with user-specified audio language preferences. This feature allows users to:

- Set a preferred audio language in settings (applies to all episode creation methods)
- Override language per-episode in the Quick Add modal
- See which language was downloaded via UI indicators
- Receive notifications when preferred language is unavailable (falls back to original)

## User Decisions

1. **Scope**: Apply preferred language to ALL methods (UI + Celery tasks)
2. **UI Design**: Checkbox + dropdown in quick add (checkbox reveals language selector)
3. **Fallback**: Download original + notify user when preferred language unavailable
4. **Data Model**: Store both preferred_audio_language (requested) AND actual_audio_language (downloaded)

## Technical Approach

### Language Codes

- Use ISO 639-1 (2-letter codes): en, es, fr, de, it, pt, ja, ko, zh, ru, ar
- Special code: "original" (default) = no language preference, download original track
- Store as lowercase in database, display as uppercase in UI

### yt-dlp Integration Strategy

- Modify format string to include language preference: `bestaudio[language=es]/bestaudio/best[height<=480]`
- Extract actual language from yt-dlp metadata: `info_dict['language']` or `info_dict['audio_languages']`
- Fallback chain: preferred language → original (any language) → fail

---

## Phase 1: Backend - Data Model & Database

### 1.1 UserSettings Domain Entity

**File**: `backend/app/domain/entities/user_settings.py`

Add field:

```python
preferred_audio_language: str = "original"  # Default: no preference
```

### 1.2 UserSettings Database Model

**File**: `backend/app/infrastructure/database/models/user_settings.py`

Add column:

```python
preferred_audio_language = Column(String(10), nullable=False, server_default='original')
```

### 1.3 Episode Domain Entity

**File**: `backend/app/domain/entities/episode.py`

Add fields:

```python
preferred_audio_language: Optional[str] = None  # What user requested
actual_audio_language: Optional[str] = None     # What was actually downloaded
```

### 1.4 Episode Database Model

**File**: `backend/app/infrastructure/database/models/episode.py`

Add columns:

```python
preferred_audio_language = Column(String(10), nullable=True)  # NULL for existing episodes
actual_audio_language = Column(String(10), nullable=True)     # NULL for existing episodes
```

### 1.5 Alembic Migration

**Create new migration**: `backend/alembic/versions/`

```bash
cd backend
uv run alembic revision --autogenerate -m "add audio language fields to user_settings and episodes"
```

Migration should:

- Add `preferred_audio_language` to `user_settings` table (default: 'original')
- Add `preferred_audio_language` to `episodes` table (nullable)
- Add `actual_audio_language` to `episodes` table (nullable)
- Backfill existing episodes: set both to 'original' or NULL (recommend NULL for clarity)

### 1.6 UserSettings Schema

**File**: `backend/app/presentation/schemas/user_settings_schemas.py`

Update request schema:

```python
class UserSettingsUpdateRequest(BaseModel):
    preferred_audio_language: Optional[str] = None
    # Validate: "original" or valid ISO 639-1 code
```

Update response schema:

```python
class UserSettingsResponse(BaseModel):
    preferred_audio_language: str
```

### 1.7 Episode Schema

**File**: `backend/app/presentation/schemas/episode_schemas.py`

Update `EpisodeCreate`:

```python
class EpisodeCreate(BaseModel):
    preferred_audio_language: Optional[str] = None  # Override user setting
```

Update `EpisodeResponse`:

```python
class EpisodeResponse(BaseModel):
    preferred_audio_language: Optional[str] = None
    actual_audio_language: Optional[str] = None
```

---

## Phase 2: Backend - yt-dlp Integration

### 2.1 YouTubeService Modifications

**File**: `backend/app/infrastructure/services/youtube_service.py`

#### Modify `download_audio()` method (lines 160-209)

Add `preferred_language` parameter:

```python
async def download_audio(
    self,
    url: str,
    output_path: Optional[Path] = None,
    progress_callback: Optional[Callable] = None,
    preferred_language: Optional[str] = None  # NEW
) -> Path:
```

#### Update `_download_audio_sync()` method (lines 211-260)

1. Build language-aware format string:

```python
def _build_format_string(self, preferred_language: Optional[str]) -> str:
    """Build yt-dlp format string with language preference."""
    if not preferred_language or preferred_language == "original":
        # Original behavior: download best audio regardless of language
        return 'bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio/best[height<=480]'

    # Try preferred language first, then fall back to any audio
    return (
        f'bestaudio[language={preferred_language}][ext=m4a]/'
        f'bestaudio[language={preferred_language}][ext=mp3]/'
        f'bestaudio[language={preferred_language}]/'
        f'bestaudio[ext=m4a]/'
        f'bestaudio[ext=mp3]/'
        f'bestaudio/best[height<=480]'
    )
```

2. Update ydl_opts before download:

```python
format_string = self._build_format_string(preferred_language)
download_opts = {**self.ydl_opts, 'format': format_string}
```

3. Extract actual language after download:

```python
info = ydl.extract_info(url, download=False)
actual_language = self._extract_actual_language(info)
```

#### Add helper method `_extract_actual_language()`

```python
def _extract_actual_language(self, info_dict: dict) -> str:
    """Extract the actual audio language from yt-dlp metadata.

    Returns:
        ISO 639-1 language code or 'original' if unknown
    """
    # Try various metadata fields
    if 'language' in info_dict and info_dict['language']:
        return info_dict['language'].lower()

    if 'audio_languages' in info_dict and info_dict['audio_languages']:
        # Return first audio language if multiple
        return info_dict['audio_languages'][0].lower()

    # Check requested format info
    if 'requested_formats' in info_dict:
        for fmt in info_dict['requested_formats']:
            if 'language' in fmt and fmt['language']:
                return fmt['language'].lower()

    # Fallback: assume original if unknown
    return 'original'
```

#### Update return value

Modify `download_audio()` to return tuple: `(audio_path: Path, actual_language: str)`

### 2.2 Update \_parse_metadata() method

**File**: `backend/app/infrastructure/services/youtube_service.py` (lines 295-319)

Add language extraction to metadata:

```python
def _parse_metadata(self, info: dict) -> dict:
    # ... existing code ...

    # Extract available audio languages
    available_languages = []
    if 'subtitles' in info:
        available_languages = list(info['subtitles'].keys())

    metadata['available_audio_languages'] = available_languages
    metadata['default_audio_language'] = info.get('language', 'unknown')

    return metadata
```

---

## Phase 3: Backend - Services & API

### 3.1 UserSettingsService

**File**: `backend/app/application/services/user_settings_service.py`

Add method:

```python
async def update_preferred_audio_language(
    self,
    user_id: int,
    language: str
) -> UserSettings:
    """Update preferred audio language.

    Args:
        language: ISO 639-1 code or "original"

    Raises:
        ValueError: If language code is invalid
    """
    # Validate language code
    valid_languages = ['original', 'en', 'es', 'fr', 'de', 'it', 'pt', 'ja', 'ko', 'zh', 'ru', 'ar']
    if language not in valid_languages:
        raise ValueError(f"Invalid language code: {language}")

    settings = await self.get_user_settings(user_id)
    settings.preferred_audio_language = language
    return await self.user_settings_repository.update(settings)
```

### 3.2 Update UserSettings API Endpoint

**File**: `backend/app/presentation/api/v1/users.py`

Update PUT `/users/settings` endpoint (lines 292-369):

- Already handles generic field updates, should work automatically
- Add validation for language codes

Add new endpoint for language list:

```python
@router.get("/languages", response_model=List[LanguageOption])
async def get_available_languages():
    """Get list of supported audio languages for downloads."""
    return [
        {"code": "original", "name": "Original (no preference)"},
        {"code": "en", "name": "English"},
        {"code": "es", "name": "Spanish"},
        {"code": "fr", "name": "French"},
        {"code": "de", "name": "German"},
        {"code": "it", "name": "Italian"},
        {"code": "pt", "name": "Portuguese"},
        {"code": "ja", "name": "Japanese"},
        {"code": "ko", "name": "Korean"},
        {"code": "zh", "name": "Chinese"},
        {"code": "ru", "name": "Russian"},
        {"code": "ar", "name": "Arabic"},
    ]
```

Add schema:

```python
class LanguageOption(BaseModel):
    code: str
    name: str
```

### 3.3 EpisodeService Modifications

**File**: `backend/app/application/services/episode_service.py`

Update `create_from_youtube_url()` method (lines 81-140):

1. Accept `preferred_audio_language` parameter
2. If not provided, fetch from user settings:

```python
async def create_from_youtube_url(
    self,
    channel_id: int,
    video_url: str,
    tags: List[str],
    user_id: int,
    preferred_audio_language: Optional[str] = None,  # NEW
) -> Episode:
    # If no language specified, get from user settings
    if preferred_audio_language is None:
        user_settings = await self.user_settings_service.get_user_settings(user_id)
        preferred_audio_language = user_settings.preferred_audio_language

    # ... existing metadata extraction ...

    # Create episode with language preference
    episode = await self.metadata_processing_service.process_youtube_metadata(
        # ... existing params ...
        preferred_audio_language=preferred_audio_language,
    )

    # ... rest of method ...
```

### 3.4 MetadataProcessingService

**File**: `backend/app/application/services/metadata_processing_service.py`

Update `process_youtube_metadata()` (lines 31-105):

```python
async def process_youtube_metadata(
    self,
    # ... existing params ...
    preferred_audio_language: Optional[str] = None,  # NEW
) -> Episode:
    # ... existing processing ...

    episode = Episode(
        # ... existing fields ...
        preferred_audio_language=preferred_audio_language,
        actual_audio_language=None,  # Will be set after download
    )

    return episode
```

### 3.5 DownloadService Modifications

**File**: `backend/app/infrastructure/services/download_service.py`

Update `_download_episode_task()` (lines 401-581):

1. Pass language to YouTubeService:

```python
async def _download_episode_task(self, episode_id: int):
    # ... get episode ...

    # Download with language preference
    audio_path, actual_language = await self.youtube_service.download_audio(
        url=episode.youtube_video_url,
        progress_callback=progress.update,
        preferred_language=episode.preferred_audio_language  # NEW
    )

    # ... process file ...

    # Update episode with actual language
    episode.actual_audio_language = actual_language

    # Check if fallback occurred (preferred != actual)
    if episode.preferred_audio_language and \
       episode.preferred_audio_language != "original" and \
       episode.preferred_audio_language != actual_language:
        # Create notification about language fallback
        await self._notify_language_fallback(episode)

    # ... rest of method ...
```

2. Add notification helper:

```python
async def _notify_language_fallback(self, episode: Episode):
    """Create notification when preferred language was unavailable."""
    notification_service = NotificationService(
        notification_repository=self.notification_repository,
        user_repository=self.user_repository,
    )

    await notification_service.create_notification(
        user_id=episode.channel.user_id,  # Get from channel
        title=f"Language fallback for '{episode.title}'",
        message=(
            f"Requested {episode.preferred_audio_language.upper()} audio, "
            f"but downloaded {episode.actual_audio_language.upper()} instead. "
            f"The preferred language was not available for this video."
        ),
        notification_type="warning",
        metadata={
            "episode_id": episode.id,
            "preferred_language": episode.preferred_audio_language,
            "actual_language": episode.actual_audio_language,
        }
    )
```

### 3.6 CeleryDownloadService Modifications

**File**: `backend/app/infrastructure/services/celery_download_service.py`

Apply same changes as DownloadService:

- Pass `preferred_audio_language` to `youtube_service.download_audio()` (line ~340)
- Store `actual_audio_language` in episode (line ~350)
- Create notification on language fallback (line ~355)

### 3.7 Update Episodes API Endpoint

**File**: `backend/app/presentation/api/v1/episodes.py`

Update POST `/episodes/` (lines 274-381):

```python
@router.post("/", response_model=EpisodeResponse)
async def create_episode(
    request: EpisodeCreate,
    current_user: User = Depends(get_current_user),
):
    episode = await episode_service.create_from_youtube_url(
        channel_id=request.channel_id,
        video_url=request.video_url,
        tags=request.tags or [],
        user_id=current_user.id,
        preferred_audio_language=request.preferred_audio_language,  # NEW
    )
```

### 3.8 Update Celery Task

**File**: `backend/app/infrastructure/tasks/create_episode_from_video_task.py`

Update task to fetch and pass user's preferred language:

```python
@shared_task(bind=True, ...)
def create_episode_from_youtube_video(
    self,
    youtube_video_id: int,
    channel_id: int,
):
    # ... existing setup ...

    # Get user's preferred language from settings
    user_settings_service = UserSettingsService(...)
    user_settings = await user_settings_service.get_user_settings(channel.user_id)
    preferred_language = user_settings.preferred_audio_language

    # Create episode with language preference
    episode = await episode_service.create_from_youtube_url(
        channel_id=channel_id,
        video_url=video.url,
        tags=[],
        user_id=channel.user_id,
        preferred_audio_language=preferred_language,  # NEW
    )

    # ... rest of task ...
```

---

## Phase 4: Frontend - Settings UI

### 4.1 TypeScript Types

**File**: `frontend/src/types/index.ts`

Add to UserSettings:

```typescript
interface UserSettings {
  preferred_audio_language: string // ISO 639-1 code or "original"
}

interface UserSettingsUpdateRequest {
  preferred_audio_language?: string
}

interface LanguageOption {
  code: string
  name: string
}
```

### 4.2 API Client

**File**: `frontend/src/lib/api-client.ts`

Add method:

```typescript
async getAvailableLanguages(): Promise<LanguageOption[]> {
  return this.get('/v1/users/languages')
}
```

### 4.3 Settings Component

**File**: `frontend/src/components/features/settings/settings-interface.tsx`

Update Subscriptions tab (after timezone field, ~line 1680):

```typescript
// Add state
const [preferredAudioLanguage, setPreferredAudioLanguage] = useState("original")
const [originalPreferredAudioLanguage, setOriginalPreferredAudioLanguage] =
  useState("original")
const [availableLanguages, setAvailableLanguages] = useState<LanguageOption[]>(
  []
)

// Load languages on mount
useEffect(() => {
  const loadLanguages = async () => {
    const languages = await apiClient.getAvailableLanguages()
    setAvailableLanguages(languages)
  }
  loadLanguages()
}, [])

// Update loadUserSettings to include new field
const loadUserSettings = async () => {
  const settings = await apiClient.getUserSettings()
  setPreferredAudioLanguage(settings.preferred_audio_language)
  setOriginalPreferredAudioLanguage(settings.preferred_audio_language)
  // ... other fields ...
}

// Update hasUnsavedChanges calculation
const hasUnsavedChanges = preferredAudioLanguage !==
  originalPreferredAudioLanguage || (
  // ... other fields ...

  // Add UI field
  <div className="space-y-2">
    <Label htmlFor="preferred-audio-language">
      Preferred Audio Language
      <span className="text-muted-foreground text-sm ml-2">
        (for automatic episode creation)
      </span>
    </Label>
    <Select
      value={preferredAudioLanguage}
      onValueChange={setPreferredAudioLanguage}
    >
      <SelectTrigger id="preferred-audio-language">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {availableLanguages.map((lang) => (
          <SelectItem key={lang.code} value={lang.code}>
            {lang.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
    <p className="text-sm text-muted-foreground">
      Select "Original" to download videos in their original language. Choose a
      specific language to prefer dubbed/translated audio tracks.
    </p>
  </div>
)

// Update handleSaveSettings
const handleSaveSettings = async () => {
  const updateData = {
    preferred_audio_language: preferredAudioLanguage,
    // ... other fields ...
  }
  await apiClient.updateUserSettings(updateData)
  setOriginalPreferredAudioLanguage(preferredAudioLanguage)
  // ... rest ...
}

// Update handleDiscardChanges
const handleDiscardChanges = () => {
  setPreferredAudioLanguage(originalPreferredAudioLanguage)
  // ... other fields ...
}
```

---

## Phase 5: Frontend - Quick Add Modal

### 5.1 Quick Add Dialog Component

**File**: `frontend/src/components/features/episodes/quick-add-dialog.tsx`

Add language selection UI:

```typescript
// Add state
const [useCustomLanguage, setUseCustomLanguage] = useState(false)
const [selectedLanguage, setSelectedLanguage] = useState('original')
const [availableLanguages, setAvailableLanguages] = useState<LanguageOption[]>([])

// Load user's preferred language and available languages
useEffect(() => {
  const loadSettings = async () => {
    const settings = await apiClient.getUserSettings()
    const languages = await apiClient.getAvailableLanguages()

    setSelectedLanguage(settings.preferred_audio_language)
    setAvailableLanguages(languages)
  }

  loadSettings()
}, [])

// Add UI after URL input field
<div className="space-y-2">
  <div className="flex items-center space-x-2">
    <Checkbox
      id="custom-language"
      checked={useCustomLanguage}
      onCheckedChange={(checked) => setUseCustomLanguage(!!checked)}
    />
    <Label htmlFor="custom-language" className="cursor-pointer">
      Download in different language
    </Label>
  </div>

  {useCustomLanguage && (
    <Select
      value={selectedLanguage}
      onValueChange={setSelectedLanguage}
    >
      <SelectTrigger>
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
  )}

  {useCustomLanguage && (
    <p className="text-sm text-muted-foreground">
      If this language is unavailable, the original audio will be downloaded.
    </p>
  )}
</div>

// Update form submission
const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault()

  const episodeData = {
    channel_id: selectedChannel.id,
    video_url: url,
    tags: [],
    preferred_audio_language: useCustomLanguage ? selectedLanguage : undefined,
  }

  await episodeApi.create(episodeData)
  // ... rest ...
}
```

---

## Phase 6: Frontend - Episode Display

### 6.1 Episode Card Component

**File**: `frontend/src/components/features/episodes/episode-card.tsx`

Add language pill overlay (after duration badge, ~line 335):

```typescript
{
  /* Language badge - only show if not original and actual language exists */
}
{
  episode.actual_audio_language &&
    episode.actual_audio_language !== "original" && (
      <div className="absolute bottom-2 left-2 bg-blue-600 text-white text-xs px-2 py-1 rounded font-semibold">
        {episode.actual_audio_language.toUpperCase()}
      </div>
    )
}

{
  /* Show warning badge if fallback occurred */
}
{
  episode.preferred_audio_language &&
    episode.preferred_audio_language !== "original" &&
    episode.actual_audio_language &&
    episode.preferred_audio_language !== episode.actual_audio_language && (
      <div className="absolute top-2 left-2 bg-yellow-500 text-white text-xs px-2 py-1 rounded flex items-center gap-1">
        <AlertTriangle className="h-3 w-3" />
        <span>Fallback</span>
      </div>
    )
}
```

### 6.2 Episode Details Page

**File**: Find episode details page component (likely `frontend/src/app/episodes/[id]/page.tsx`)

Add language info below episode title:

```typescript
<div className="flex items-center gap-4 text-sm text-muted-foreground">
  <div className="flex items-center gap-1">
    <Clock className="h-4 w-4" />
    <span>{formatDate(episode.created_at)}</span>
  </div>

  {/* Add language info */}
  {episode.actual_audio_language &&
    episode.actual_audio_language !== "original" && (
      <div className="flex items-center gap-1">
        <Globe className="h-4 w-4" />
        <span>Audio: {episode.actual_audio_language.toUpperCase()}</span>

        {/* Show if fallback occurred */}
        {episode.preferred_audio_language !== episode.actual_audio_language && (
          <Tooltip>
            <TooltipTrigger>
              <AlertTriangle className="h-4 w-4 text-yellow-500" />
            </TooltipTrigger>
            <TooltipContent>
              Requested {episode.preferred_audio_language.toUpperCase()} but not
              available
            </TooltipContent>
          </Tooltip>
        )}
      </div>
    )}
</div>
```

### 6.3 Update Episode Types

**File**: `frontend/src/types/index.ts`

Update Episode interface:

```typescript
interface Episode {
  // ... existing fields ...
  preferred_audio_language?: string
  actual_audio_language?: string
}
```

---

## Testing Plan

### Backend Tests

1. **UserSettings**: Test language preference CRUD operations
2. **yt-dlp Integration**: Test format string generation with different languages
3. **Download Service**: Test language fallback logic
4. **API Endpoints**: Test episode creation with language parameter
5. **Celery Tasks**: Test automated episode creation with user's preferred language

### Frontend Tests

1. **Settings Page**: Test language dropdown and save/discard
2. **Quick Add Modal**: Test checkbox and language selection
3. **Episode Card**: Test language pill display
4. **Episode Details**: Test language info and fallback indicator

### Integration Tests

1. Create episode with preferred language (happy path)
2. Create episode with unavailable language (fallback path)
3. Verify notification created on fallback
4. Test Celery auto-approve with language preference
5. Test existing episodes without language data (backward compatibility)

### Manual Testing

1. Change preferred language in settings → create episode via Celery → verify language
2. Use quick add with custom language → verify episode has correct language
3. Test with video that has multiple audio tracks
4. Test with video that has only one audio track
5. Verify UI displays correctly on mobile

---

## Critical Files to Modify

### Backend (17 files)

1. `backend/app/domain/entities/user_settings.py` - Add field
2. `backend/app/domain/entities/episode.py` - Add 2 fields
3. `backend/app/infrastructure/database/models/user_settings.py` - Add column
4. `backend/app/infrastructure/database/models/episode.py` - Add 2 columns
5. `backend/alembic/versions/XXXXX_add_audio_language_fields.py` - New migration
6. `backend/app/presentation/schemas/user_settings_schemas.py` - Update schemas
7. `backend/app/presentation/schemas/episode_schemas.py` - Update schemas
8. `backend/app/infrastructure/services/youtube_service.py` - yt-dlp integration
9. `backend/app/application/services/user_settings_service.py` - Add method
10. `backend/app/application/services/episode_service.py` - Accept language param
11. `backend/app/application/services/metadata_processing_service.py` - Pass language
12. `backend/app/infrastructure/services/download_service.py` - Language handling
13. `backend/app/infrastructure/services/celery_download_service.py` - Language handling
14. `backend/app/presentation/api/v1/users.py` - Add endpoint, update PUT
15. `backend/app/presentation/api/v1/episodes.py` - Accept language param
16. `backend/app/infrastructure/tasks/create_episode_from_video_task.py` - Fetch user setting
17. `backend/app/infrastructure/tasks/download_episode_task.py` - Pass language to service

### Frontend (6 files)

1. `frontend/src/types/index.ts` - Add types
2. `frontend/src/lib/api-client.ts` - Add method
3. `frontend/src/components/features/settings/settings-interface.tsx` - Add language field
4. `frontend/src/components/features/episodes/quick-add-dialog.tsx` - Add checkbox + dropdown
5. `frontend/src/components/features/episodes/episode-card.tsx` - Add language pills
6. `frontend/src/app/episodes/[id]/page.tsx` - Add language info (need to locate)

---

## Migration Strategy

### Database Migration

```bash
cd backend
uv run alembic revision --autogenerate -m "add audio language support"
uv run alembic upgrade head
```

### Deployment Steps

1. Deploy backend first (database migration will run automatically)
2. Verify migration successful: check `user_settings` and `episodes` tables
3. Deploy frontend
4. Test with existing episodes (should handle NULL gracefully)
5. Test creating new episodes with language preferences

### Rollback Plan

If issues occur:

```bash
cd backend
uv run alembic downgrade -1  # Rollback migration
```

---

## Open Questions / Considerations

1. **yt-dlp Language Metadata**: Need to verify if yt-dlp reliably provides language info in `info_dict`. May need testing with real videos.

2. **Multi-Audio Track Videos**: Some YouTube videos have multiple audio tracks (original + dubbed versions). yt-dlp should handle this, but need to test.

3. **Performance**: Adding language preference to format string may slightly increase download time (yt-dlp needs to check more formats).

4. **Notification System**: Assuming NotificationService exists and works as expected. Need to verify implementation.

5. **Episode Details Page**: Need to locate the actual episode details component (assumed path may be different).

6. **Language Validation**: Should we validate language codes server-side when creating episodes? Currently relying on client-side validation.

7. **Backward Compatibility**: Existing episodes will have NULL for language fields. UI should handle gracefully (done in conditional rendering).

---

## Success Criteria

✅ User can set preferred audio language in settings
✅ Setting applies to all episode creation methods (UI + Celery)
✅ Quick add modal allows per-episode language override
✅ Episodes display language indicator when not original
✅ User receives notification when preferred language unavailable
✅ Database stores both preferred and actual language
✅ yt-dlp downloads correct language when available
✅ Falls back to original language gracefully
✅ Existing episodes display correctly without language data
✅ All tests pass (unit, integration, manual)
