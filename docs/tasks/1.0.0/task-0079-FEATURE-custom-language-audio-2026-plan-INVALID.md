# Implementation Plan: Custom Language & Audio Quality Selection for YouTube Downloads

## Context

LabCastARR currently downloads YouTube audio using a single hardcoded yt-dlp format string (`bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio`) that always fetches the best available quality in the original language, then converts to MP3 at 192kbps. There's no ability for users to choose a different language track or control audio quality.

Additionally, two separate download paths exist: the direct UI flow uses FastAPI `BackgroundTasks` with an asyncio.Queue-based `DownloadService`, while the subscription videos flow uses Celery tasks with `CeleryDownloadService`. The user wants to standardize both paths on Celery.

**Goal:** Add language/quality selection to all episode creation flows, build smart quality fallback logic, and unify the download infrastructure on Celery.

---

## Phase 1: Backend Data Layer

### 1.1 Alembic Migration

**Create:** `backend/alembic/versions/<auto>_add_audio_language_quality_to_episodes.py`

Add 4 nullable columns to `episodes` table:

- `audio_language` String(10) - actual downloaded language (ISO 639-1 or null)
- `audio_quality` String(20) - actual downloaded quality tier ("low"/"medium"/"high" or null)
- `requested_language` String(10) - what user originally requested
- `requested_quality` String(20) - what user originally requested

All nullable for backward compatibility. No indexes needed (informational, not query filters).

### 1.2 Update Episode DB Model

**Modify:** `backend/app/infrastructure/database/models/episode.py`

Add the 4 new columns after `original_filename`.

### 1.3 Update Episode Domain Entity

**Modify:** `backend/app/domain/entities/episode.py`

- Add 4 optional fields: `audio_language`, `audio_quality`, `requested_language`, `requested_quality`
- Add `set_audio_preferences(requested_language, requested_quality, actual_language, actual_quality)` method
- Update `create_episode()` factory to accept optional `requested_language` and `requested_quality`

### 1.4 Update Episode Repository Mapper

**Modify:** `backend/app/infrastructure/repositories/episode_repository.py`

Map the 4 new columns in both `_model_to_entity` and `_entity_to_model`.

### 1.5 Update API Schemas

**Modify:** `backend/app/presentation/schemas/episode_schemas.py`

- `EpisodeCreate`: add optional `audio_language` (max_length=10) and `audio_quality` (pattern `^(low|medium|high)$`)
- `EpisodeResponse`: add all 4 new fields, update `from_entity()`

**Modify:** `backend/app/presentation/schemas/youtube_video_schemas.py` (or wherever `CreateEpisodeFromVideoRequest` lives)

- Add optional `audio_language` and `audio_quality` fields

---

## Phase 2: Audio Format Selection Service (New)

### 2.1 Audio Quality Value Object

**Create:** `backend/app/domain/value_objects/audio_quality.py`

```python
class AudioQualityTier(Enum):
    LOW = "low"        # 0-70 kbps
    MEDIUM = "medium"  # 70-150 kbps
    HIGH = "high"      # 150+ kbps
```

Methods: `from_bitrate(abr)`, `bitrate_range`, `preferred_yt_dlp_quality` (low→'64', medium→'128', high→'192').

### 2.2 Audio Format Selection Service

**Create:** `backend/app/infrastructure/services/audio_format_selection_service.py`

Core service that analyzes yt-dlp format lists and builds optimal format selector strings.

**Input:** yt-dlp formats list, requested_language, requested_quality
**Output:** `AudioFormatSelectionResult` with:

- `format_selector` - yt-dlp format string
- `preferred_quality_kbps` - FFmpeg post-processor quality
- `actual_language`, `actual_quality` - what will actually be downloaded
- `fallback_occurred`, `fallback_reason` - fallback tracking

**Fallback chain:**

1. Find audio formats matching requested language + quality bitrate range
2. If none: try higher quality in same language
3. If none: try lower quality in same language
4. If no language track at all: fallback to original language + best quality (current behavior)

**Language filtering:** Use yt-dlp `language` field on formats. Filter `vcodec == 'none'` (audio-only).
**Quality filtering:** Map tier to bitrate range, filter by `abr` field.

---

## Phase 3: Modify Existing Services

### 3.1 Update YouTubeService

**Modify:** `backend/app/infrastructure/services/youtube_service.py`

Update `download_audio()` signature:

```python
async def download_audio(
    self, url, output_path=None, progress_callback=None,
    audio_language=None, audio_quality=None
) -> tuple[str, dict]:  # (file_path, format_info)
```

Logic:

1. Call `extract_info(url, download=False)` to get formats
2. Pass to `AudioFormatSelectionService.select_format()`
3. Override `ydl_opts['format']` with returned `format_selector`
4. Override FFmpeg `preferredquality` with returned value
5. Download and return `(file_path, format_info_dict)`

When `audio_language` and `audio_quality` are both None, maintain current behavior exactly (no format analysis step).

Update `get_audio_formats()` to include `language` field.
Update `_parse_metadata()` to include `formats` list in output.

### 3.2 Update CeleryDownloadService

**Modify:** `backend/app/infrastructure/services/celery_download_service.py`

Add `audio_language` and `audio_quality` params to `download_episode()`. Pass them to `youtube_service.download_audio()`. After download, call `episode.set_audio_preferences()` with actual results.

### 3.3 Update DownloadService (FastAPI version - transitional)

**Modify:** `backend/app/infrastructure/services/download_service.py`

Add `audio_language` and `audio_quality` params to `queue_download()` and `_download_episode_task()`. This keeps Path 1 working during transition before Phase 6 (Celery migration).

---

## Phase 4: Celery Task Updates

### 4.1 Update download_episode task

**Modify:** `backend/app/infrastructure/tasks/download_episode_task.py`

Add `audio_language` and `audio_quality` params. Pass to `CeleryDownloadService.download_episode()`.

### 4.2 Update create_episode_from_youtube_video task

**Modify:** `backend/app/infrastructure/tasks/create_episode_from_video_task.py`

Add `audio_language` and `audio_quality` params. Pass to `download_episode.apply_async()` kwargs.

---

## Phase 5: API Endpoint Changes

### 5.1 Update POST /v1/episodes/

**Modify:** `backend/app/presentation/api/v1/episodes.py` (line 274)

Pass `episode_data.audio_language` and `episode_data.audio_quality` through to the download path.

Also update `EpisodeService.create_from_youtube_url()` to store `requested_language` and `requested_quality` on the episode entity at creation time.

### 5.2 Update POST /v1/youtube-videos/{id}/create-episode

**Modify:** `backend/app/presentation/api/v1/youtube_videos.py`

Pass `request.audio_language` and `request.audio_quality` to the Celery task.

### 5.3 Update related application services

**Modify:** `backend/app/application/services/episode_service.py` - add params to `create_from_youtube_url()`

---

## Phase 6: Migrate Path 1 (Direct UI) to Celery

### 6.1 Replace BackgroundTasks with Celery in create_episode endpoint

**Modify:** `backend/app/presentation/api/v1/episodes.py`

Replace:

```python
background_tasks.add_task(_isolated_download_queue, download_service, episode_id)
```

With:

```python
from app.infrastructure.tasks.download_episode_task import download_episode
download_episode.apply_async(
    args=(episode_id,),
    kwargs={'channel_id': ..., 'audio_language': ..., 'audio_quality': ...}
)
```

Remove `BackgroundTasks` and `DownloadService` dependencies from the endpoint. Remove `_isolated_download_queue()` helper.

### 6.2 Update retry/redownload endpoint

**Modify:** `backend/app/presentation/api/v1/episodes.py`

Replace `download_service.queue_download()` with `download_episode.apply_async()`, re-using original `requested_language`/`requested_quality` from the episode.

### 6.3 Progress tracking

The `GET /v1/episodes/{id}/progress` endpoint already has a database fallback path (when no in-memory progress exists). After Celery migration, this fallback will be the primary path. Episode status (PENDING/PROCESSING/COMPLETED/FAILED) is updated by `CeleryDownloadService` in the DB, so the endpoint will continue to work.

### 6.4 Mark DownloadService as deprecated

Add deprecation comment to `backend/app/infrastructure/services/download_service.py`. The `get_download_service` dependency can remain but won't be used by the create/retry endpoints.

---

## Phase 7: Frontend UI Changes

### 7.1 Update TypeScript Types

**Modify:** `frontend/src/types/episode.ts` and `frontend/src/types/index.ts`

Add to `CreateEpisodeRequest` / `EpisodeCreate`:

- `audio_language?: string | null`
- `audio_quality?: string | null`

Add to `CreateEpisodeFromVideoRequest`:

- `audio_language?: string | null`
- `audio_quality?: string | null`

Add to `Episode` interface:

- `audio_language`, `audio_quality`, `requested_language`, `requested_quality` (all `string | null`)

### 7.2 Create AudioOptionsSelector Component (Shared)

**Create:** `frontend/src/components/features/episodes/audio-options-selector.tsx`

Reusable component with:

- Optional "Custom audio options" checkbox (`showToggle` prop)
- Language dropdown: "Original (default)", "English", "Spanish"
- Quality dropdown: "Low (up to 70 kbps)" (pre-selected), "Medium (70-150 kbps)", "High (150+ kbps)"

When checkbox is unchecked (or `showToggle=false` and no values set), `audio_language` and `audio_quality` are `null` → backend uses current default behavior (original language, best quality).

When checkbox is checked, defaults to language="default" and quality="low" as specified.

Uses ShadCN: `Select`, `SelectTrigger`, `SelectValue`, `SelectContent`, `SelectItem`, `Checkbox`, `Label`.

### 7.3 Update Quick Add Dialog

**Modify:** `frontend/src/components/features/episodes/quick-add-dialog.tsx`

- Add state: `audioLanguage`, `audioQuality`
- Add `<AudioOptionsSelector showToggle={true} />` between URL input and footer
- Pass values in `episodeApi.create()` call
- Reset state on dialog close

### 7.4 Update Add Episode Form (Multi-step)

**Modify:** `frontend/src/components/features/episodes/add-episode-form.tsx`

- Add state and `<AudioOptionsSelector showToggle={true} />` in Step 1 below URL input
- Pass values in `handleCreateEpisode()`

### 7.5 Update Video List Create Episode Dialog

**Modify:** `frontend/src/components/features/subscriptions/video-list.tsx`

- Add state and `<AudioOptionsSelector showToggle={true} />` below channel selector in create episode dialog (~line 617)
- Pass values in `createEpisodeMutation.mutateAsync()` call
- Reset audio state when dialog closes
- Same for bulk create dialog (~line 676)

### 7.6 Update API Clients

**Modify:** `frontend/src/lib/api.ts` - pass new fields in `episodeApi.create()`
**Modify:** `frontend/src/lib/api-client.ts` - pass new fields in `createEpisode()` and `createEpisodeFromVideo()`

Hooks (`use-episodes.ts`, `use-youtube-videos.ts`) require no changes - they pass through the typed request objects.

---

## Phase 8: Event & Notification Enhancements

### 8.1 Enrich download events

**Modify:** `backend/app/infrastructure/services/celery_download_service.py`

- `download_started` event: include `requested_language`, `requested_quality`
- `download_completed` event: include `actual_language`, `actual_quality`, `fallback_occurred`, `fallback_reason`

### 8.2 Fallback notification

After successful download in `CeleryDownloadService`, if `fallback_occurred`, create a user notification:

- Title: "Audio Quality Fallback"
- Message: "Requested [lang]/[quality], downloaded [actual_lang]/[actual_quality]: [reason]"
- Type: `EPISODE_CREATED` (reuse existing type)

---

## Verification Plan

### Backend

```bash
cd backend
uv run alembic upgrade head                    # Apply migration
uv run fastapi dev app/main.py                 # Start dev server
# Test: POST /v1/episodes/ with audio_language/audio_quality → verify episode created with fields
# Test: POST /v1/episodes/ without audio fields → verify backward compatibility
# Test: POST /v1/youtube-videos/{id}/create-episode with audio fields
```

### Frontend

```bash
cd frontend
npm run lint                                    # Lint check
npx tsc --noEmit                               # Type check
npm run dev                                     # Start dev server
# Test: Quick Add → toggle custom options → verify dropdowns → submit
# Test: Add from YouTube page → verify audio options on Step 1
# Test: Subscriptions/Videos → Create Episode → verify audio options in dialog
```

### Integration (Docker)

```bash
docker compose --env-file .env.development -f docker-compose.dev.yml up --build
# Test full flow: Quick Add with custom language/quality → verify Celery task picks up → episode completed with correct fields
# Test fallback: Request Spanish track on English-only video → verify fallback notification
```

---

## Key Files Summary

| Area            | File                                                                    | Change                                          |
| --------------- | ----------------------------------------------------------------------- | ----------------------------------------------- |
| Migration       | `backend/alembic/versions/<new>`                                        | New: 4 columns                                  |
| DB Model        | `backend/app/infrastructure/database/models/episode.py`                 | Add 4 columns                                   |
| Domain          | `backend/app/domain/entities/episode.py`                                | Add 4 fields + method                           |
| Value Object    | `backend/app/domain/value_objects/audio_quality.py`                     | **New file**                                    |
| Format Service  | `backend/app/infrastructure/services/audio_format_selection_service.py` | **New file**                                    |
| YouTube Service | `backend/app/infrastructure/services/youtube_service.py`                | Add lang/quality to download_audio              |
| Celery Download | `backend/app/infrastructure/services/celery_download_service.py`        | Add lang/quality params + fallback notification |
| Download Task   | `backend/app/infrastructure/tasks/download_episode_task.py`             | Add lang/quality params                         |
| Create Task     | `backend/app/infrastructure/tasks/create_episode_from_video_task.py`    | Add lang/quality params                         |
| Episode API     | `backend/app/presentation/api/v1/episodes.py`                           | Migrate to Celery + add params                  |
| Video API       | `backend/app/presentation/api/v1/youtube_videos.py`                     | Add params                                      |
| Schemas         | `backend/app/presentation/schemas/episode_schemas.py`                   | Add fields                                      |
| Episode Service | `backend/app/application/services/episode_service.py`                   | Add params                                      |
| Repo Mapper     | `backend/app/infrastructure/repositories/episode_repository.py`         | Map new fields                                  |
| Types           | `frontend/src/types/episode.ts`, `frontend/src/types/index.ts`          | Add fields                                      |
| UI Component    | `frontend/src/components/features/episodes/audio-options-selector.tsx`  | **New file**                                    |
| Quick Add       | `frontend/src/components/features/episodes/quick-add-dialog.tsx`        | Add audio options                               |
| Add Form        | `frontend/src/components/features/episodes/add-episode-form.tsx`        | Add audio options                               |
| Video List      | `frontend/src/components/features/subscriptions/video-list.tsx`         | Add audio options to create dialog              |
| API Client      | `frontend/src/lib/api.ts`, `frontend/src/lib/api-client.ts`             | Pass new fields                                 |

## Implementation Order

1. Phase 1 (Data layer) → 2 (Format service) → 3 (Service updates) → 4 (Celery tasks) → 5 (API endpoints)
2. Phase 6 (Celery migration) - can be done after Phase 5
3. Phase 7 (Frontend) - depends on Phase 5
4. Phase 8 (Events) - can be done alongside Phase 3

## Risk Notes

- **yt-dlp language tracks**: Not all YouTube videos have language metadata on audio formats. The format selection service must gracefully handle this (fallback to default behavior).
- **Celery migration**: After Phase 6, Redis + Celery must be running for ANY episode creation (not just subscription videos). Docker dev environment already has this, but local dev without Docker needs `celery -A app.infrastructure.celery_app worker`.
- **Progress tracking**: After Celery migration, the in-memory progress tracking via `DownloadService` is gone. The existing DB-based fallback in the progress endpoint handles this, but granular percentage tracking is lost (only status transitions remain).
