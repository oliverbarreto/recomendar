# Task 0078: FEATURE - Custom Language Audio: Allow downloading media file in to create episodes in other languages

- Session File: @task-0078-FEATURE-custom-language-audio-full-session-1.md
- IDE: Claude Code
- Date: 2026-02-08
- Model: Claude Opus 4.5

## Prompt (Plan Mode)

We want to add a new feature that allows the user to create podcast episodes in a different language than the original audio track of the youtube video.

Besides the language, there are also options to download different qualities of the audio file, for available languages. We should add an option to set the preffered quality for the audio file to be downloaded. The system should try to download the audio file in the specified quality. If not possible, the system should then try to download the audio file in superior quality. If the preffered quality is not available, then the system should try to download the audio file in the requested language in qualities lower than the preffered quality.

We need to put in place a new process to download the audio file in the specified language and quality in the background using Celery tasks. This system should consider the following aspects:

- it should allow identifying the best quality available for the specified language
- it should compare the preffered quality with the best quality available for the specified language
- it should determine if the preffered quality is available for the specified language
- it should determine if it is not possible to download the audio file in the specified language and quality, then it should try to download the audio file in the requested language in qualities lower than the preffered quality.
- if no option is available it should fallback to the original language and quality.
- The system should generate events and use the system we already have in place to notify the user of events of the download process.
- in the case of the "quick add" modal, the modal should have a checkbox that when selected, it will show a dropdown with the list of languages codes and another one with the preffered quality of the audio file: low (default), medium, or high. If the checkbox is not selected, the system should download the audio file in the original language and best quality available using yt-dlp best-quality option.

This feature should be available in the "quick add" modal and in the "add episode from youtube video" multi-step form. Therefore, we should add to the UI, two new dropdown menus to allow the user to select the language and the preffered quality of the audio file to be downloaded using dropdown options.

The feature should also be available for the case of the videos identified for followed channels (https://labcastarr.oliverbarreto.com/subscriptions/videos). In this case, the video cards should have a new option in the drop down menu (bellow "create episode" option) to download the audio file in the specified language and quality. This should show a similar modal as the one used for the "quick add" form to select the language and preffered quality of the audio file to be downloaded.

For quality, we should have the following options for the user (low, medium, high) but we need to handle it in terms of bitrate when using "yt-dlp" library: "Low" (0 to 70 kbps), "Medium" (70 to 150 kbps), "High" (150 to inf kbps), with the default option being "Low".

For the language, we should use the ISO 639-1 code for the language and show a dropdown with the list of languages codes, eg: default, en, es, fr, ... However, we do not want to list all languages code in the standard. Only show the dropdown options with english and spanish for now.

It is important that we have a clear understanding of the current codebase and the current workflows we have in place that add an episode to the podcast channel from a youtube video, and how we download the audio media file. We currently have two parallel workflows capable of downloading media files from youtube videos and creating a podcast episode:

1. when the user utilizes the UI, I believe that the frontend directly calls FastAPI endpoint which utilizes FastAPI background tasks to conduct all the required steps.

2. when the user selects "create episode" in a video in the subscriptions/videos page, the system will download the audio media file in the specified language and quality using Celery tasks.

IMPORTNAT: We want to standardize the process of downloading the audio media file using "yt-dlp" library in the background using Celery tasks. We should create a new service to handle this process, including managing the selection of the best quality available for the specified language (if any), selecting the format to be downloaded, downloading the audio media file in the specified language and quality using "yt-dlp" library, creating events of the process and notifying the user of the events.

TASKS:

Explore the current codebase to analyze the current workflows we have in place that add an episode to the podcast channel, how we download the audio media file, and how we should download the media.

We should analyze what needs to be modified in the logic, the data model, the UI and the architecture involved to use Celery tasks to download the audio file of a video in the background.

If you need to add more questions to have a better understanding of the current codebase, do so.

Do not create any code yet, we have to focus on fully understanding the feature and create detailed implementation plan with the steps needed to implement this new feature.

---

         Claude Code v2.1.37

▗ ▗ ▖ ▖ Opus 4.6 · Claude Pro
~/local/dev/labcastarr
▘▘ ▝▝ Opus 4.6 is here · $50 free extra usage · /extra-usage to enable

❯ /prime

❯ # Context Prime

> Follow the instructions to understand the context of the project.

## Run the following commands to understand the project folder and files structure:

- tree -L 5 -I 'web|node_modules'
- git ls-files  


## Read the following files to understand the project:

> Read the following files and nothing else.

- README.md
- backend/pyproject.toml
- frontend/package.json  


⏺ I'll prime the context by running the commands and reading the files in parallel.

⏺ Read 1 file (ctrl+o to expand)

⏺ Context primed. Here's a summary of the project:

LabCastARR — A full-stack podcast channel app for homelabs that converts YouTube videos and uploaded audio files into podcast episodes
with RSS feed generation.

Stack

- Frontend: Next.js 15 + React 19 + TypeScript + TailwindCSS v4 + ShadCN UI + React Query v5
- Backend: FastAPI + Python 3.12+ + SQLAlchemy + SQLite (async/aiosqlite) + Alembic migrations
- Background Tasks: Celery + Redis (YouTube channel monitoring/video discovery)
- Media: yt-dlp (YouTube extraction), FFmpeg (audio conversion), PodGen (RSS feeds)
- Deployment: Docker Compose (dev/pre/prod configurations)

Architecture

- Backend follows Clean Architecture (domain → application → infrastructure → presentation)
- 14 Alembic migration versions tracking schema evolution
- Frontend uses App Router with feature-based component organization

Key Files (tracked)

- ~200+ source files across backend/frontend
- Backend services cover: episodes, channels, uploads, YouTube metadata, RSS feeds, notifications, Celery tasks, user settings
- Frontend components organized into: features (episodes, channels, subscriptions, settings), shared, layout, UI (ShadCN)

Ready for your next task.

❯  
We want to add a new feature that allows the user to create podcast episodes in a different language than the original audio  
track of the youtube video.

Besides the language, there are also options to download different qualities of the audio file, for available languages. We  
should add an option to set the preffered quality for the audio file to be downloaded. The system should try to download the  
audio file in the specified quality. If not possible, the system should then try to download the audio file in superior quality.  
If the preffered quality is not available, then the system should try to download the audio file in the requested language in  
qualities lower than the preffered quality.

We need to put in place a new process to download the audio file in the specified language and quality in the background using  
Celery tasks. This system should consider the following aspects:

- it should allow identifying the best quality available for the specified language
- it should compare the preffered quality with the best quality available for the specified language
- it should determine if the preffered quality is available for the specified language
- it should determine if it is not possible to download the audio file in the specified language and quality, then it should try  
  to download the audio file in the requested language in qualities lower than the preffered quality.
- if no option is available it should fallback to the original language and quality.
- The system should generate events and use the system we already have in place to notify the user of events of the download  
  process.
- in the case of the "quick add" modal, the modal should have a checkbox that when selected, it will show a dropdown with the  
  list of languages codes and another one with the preffered quality of the audio file: low (default), medium, or high. If the  
  checkbox is not selected, the system should download the audio file in the original language and best quality available using  
  yt-dlp best-quality option.  


This feature should be available in the "quick add" modal and in the "add episode from youtube video" multi-step form. Therefore,
we should add to the UI, two new dropdown menus to allow the user to select the language and the preffered quality of the audio  
file to be downloaded using dropdown options.

The feature should also be available for the case of the videos identified for followed channels  
(https://labcastarr.oliverbarreto.com/subscriptions/videos). In this case, the video cards should have a new option in the drop  
down menu (bellow "create episode" option) to download the audio file in the specified language and quality. This should show a  
similar modal as the one used for the "quick add" form to select the language and preffered quality of the audio file to be  
downloaded.

For quality, we should have the following options for the user (low, medium, high) but we need to handle it in terms of bitrate  
when using "yt-dlp" library: "Low" (0 to 70 kbps), "Medium" (70 to 150 kbps), "High" (150 to inf kbps), with the default option  
being "Low".

For the language, we should use the ISO 639-1 code for the language and show a dropdown with the list of languages codes, eg:  
default, en, es, fr, ... However, we do not want to list all languages code in the standard. Only show the dropdown options with  
english and spanish for now.

It is important that we have a clear understanding of the current codebase and the current workflows we have in place that add an
episode to the podcast channel from a youtube video, and how we download the audio media file. We currently have two parallel  
workflows capable of downloading media files from youtube videos and creating a podcast episode:

1. when the user utilizes the UI, I believe that the frontend directly calls FastAPI endpoint which utilizes FastAPI background  
   tasks to conduct all the required steps.  

2. when the user selects "create episode" in a video in the subscriptions/videos page, the system will download the audio media  
   file in the specified language and quality using Celery tasks.  


IMPORTNAT: We want to standardize the process of downloading the audio media file using "yt-dlp" library in the background using  
Celery tasks. We should create a new service to handle this process, including managing the selection of the best quality  
available for the specified language (if any), selecting the format to be downloaded, downloading the audio media file in the  
specified language and quality using "yt-dlp" library, creating events of the process and notifying the user of the events.

TASKS:

Explore the current codebase to analyze the current workflows we have in place that add an episode to the podcast channel, how we
download the audio media file, and how we should download the media.

We should analyze what needs to be modified in the logic, the data model, the UI and the architecture involved to use Celery  
tasks to download the audio file of a video in the background.

If you need to add more questions to have a better understanding of the current codebase, do so.

Do not create any code yet, we have to focus on fully understanding the feature and create detailed implementation plan with the  
steps needed to implement this new feature.

⏺ I'll start by launching 3 Explore agents in parallel to thoroughly understand the current codebase from different angles.

⏺ 3 Explore agents finished (ctrl+o to expand)
├─ Explore backend download workflow · 19 tool uses · 94.4k tokens
│ ⎿  Done
├─ Explore frontend episode UI · 20 tool uses · 80.7k tokens
│ ⎿  Done
└─ Explore data model and events · 29 tool uses · 65.0k tokens
⎿  Done

⏺ Excellent research from all three agents. Now let me read a few critical files to deepen my understanding before designing the plan.

⏺ Read 3 files (ctrl+o to expand)

⏺ Now let me read the remaining critical files - the quick add dialog, the episode API endpoint, and the download_episode_task.

⏺ Read 3 files (ctrl+o to expand)

⏺ Let me check the \_isolated_download_queue function and the download_service.py to understand the FastAPI background task path
completely.

⏺ Read 3 files (ctrl+o to expand)

⏺ Now I have a thorough understanding of the codebase. Let me launch the Plan agent to design the implementation.

⏺ Plan(Design implementation plan)
⎿  Done (40 tool uses · 149.2k tokens · 3m 44s)

⏺ Now I have comprehensive research from all agents and have read the critical files. Let me write the final plan.

⏺ Updated plan
⎿  /plan to preview

⏺ The plan is written. Here's a summary of what it covers:

8 Phases across backend and frontend:

1. Data layer - Alembic migration + 4 new nullable columns on episodes
2. New AudioFormatSelectionService - Smart format selection with fallback chain
3. Service modifications - YouTubeService, CeleryDownloadService, DownloadService
4. Celery task updates - Pass language/quality through task chain
5. API endpoints - Accept new optional params on episode creation
6. Celery migration - Replace FastAPI BackgroundTasks with Celery for Path 1
7. Frontend UI - New shared AudioOptionsSelector component used in Quick Add, Add Form, and Video List
8. Events/notifications - Fallback tracking and user notifications

Key design decisions:

- Checkbox toggle with "Custom audio options" (off by default = current behavior)
- When enabled: language defaults to "Original", quality defaults to "Low"
- 4-step fallback: preferred quality → higher quality → lower quality → original language/best
- 2 new files: audio_quality.py value object + audio_format_selection_service.py
- All existing episodes unaffected (nullable columns, optional params)

────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
Ready to code?

Here is Claude's plan:
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
Implementation Plan: Custom Language & Audio Quality Selection for YouTube Downloads

Context

LabCastARR currently downloads YouTube audio using a single hardcoded yt-dlp format string
(bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio) that always fetches the best available quality in the original language, then
converts to MP3 at 192kbps. There's no ability for users to choose a different language track or control audio quality.

Additionally, two separate download paths exist: the direct UI flow uses FastAPI BackgroundTasks with an asyncio.Queue-based
DownloadService, while the subscription videos flow uses Celery tasks with CeleryDownloadService. The user wants to standardize both
paths on Celery.

Goal: Add language/quality selection to all episode creation flows, build smart quality fallback logic, and unify the download
infrastructure on Celery.

---

Phase 1: Backend Data Layer

1.1 Alembic Migration

Create: backend/alembic/versions/<auto>\_add_audio_language_quality_to_episodes.py

Add 4 nullable columns to episodes table:

- audio_language String(10) - actual downloaded language (ISO 639-1 or null)
- audio_quality String(20) - actual downloaded quality tier ("low"/"medium"/"high" or null)
- requested_language String(10) - what user originally requested
- requested_quality String(20) - what user originally requested

All nullable for backward compatibility. No indexes needed (informational, not query filters).

1.2 Update Episode DB Model

Modify: backend/app/infrastructure/database/models/episode.py

Add the 4 new columns after original_filename.

1.3 Update Episode Domain Entity

Modify: backend/app/domain/entities/episode.py

- Add 4 optional fields: audio_language, audio_quality, requested_language, requested_quality
- Add set_audio_preferences(requested_language, requested_quality, actual_language, actual_quality) method
- Update create_episode() factory to accept optional requested_language and requested_quality

  1.4 Update Episode Repository Mapper

Modify: backend/app/infrastructure/repositories/episode_repository.py

Map the 4 new columns in both \_model_to_entity and \_entity_to_model.

1.5 Update API Schemas

Modify: backend/app/presentation/schemas/episode_schemas.py

- EpisodeCreate: add optional audio_language (max_length=10) and audio_quality (pattern ^(low|medium|high)$)
- EpisodeResponse: add all 4 new fields, update from_entity()

Modify: backend/app/presentation/schemas/youtube_video_schemas.py (or wherever CreateEpisodeFromVideoRequest lives)

- Add optional audio_language and audio_quality fields

---

Phase 2: Audio Format Selection Service (New)

2.1 Audio Quality Value Object

Create: backend/app/domain/value_objects/audio_quality.py

class AudioQualityTier(Enum):
LOW = "low" # 0-70 kbps
MEDIUM = "medium" # 70-150 kbps
HIGH = "high" # 150+ kbps

Methods: from_bitrate(abr), bitrate_range, preferred_yt_dlp_quality (low→'64', medium→'128', high→'192').

2.2 Audio Format Selection Service

Create: backend/app/infrastructure/services/audio_format_selection_service.py

Core service that analyzes yt-dlp format lists and builds optimal format selector strings.

Input: yt-dlp formats list, requested_language, requested_quality
Output: AudioFormatSelectionResult with:

- format_selector - yt-dlp format string
- preferred_quality_kbps - FFmpeg post-processor quality
- actual_language, actual_quality - what will actually be downloaded
- fallback_occurred, fallback_reason - fallback tracking

Fallback chain:

1. Find audio formats matching requested language + quality bitrate range
2. If none: try higher quality in same language
3. If none: try lower quality in same language
4. If no language track at all: fallback to original language + best quality (current behavior)

Language filtering: Use yt-dlp language field on formats. Filter vcodec == 'none' (audio-only).
Quality filtering: Map tier to bitrate range, filter by abr field.

---

Phase 3: Modify Existing Services

3.1 Update YouTubeService

Modify: backend/app/infrastructure/services/youtube_service.py

Update download_audio() signature:
async def download_audio(
self, url, output_path=None, progress_callback=None,
audio_language=None, audio_quality=None
) -> tuple[str, dict]: # (file_path, format_info)

Logic:

1. Call extract_info(url, download=False) to get formats
2. Pass to AudioFormatSelectionService.select_format()
3. Override ydl_opts['format'] with returned format_selector
4. Override FFmpeg preferredquality with returned value
5. Download and return (file_path, format_info_dict)

When audio_language and audio_quality are both None, maintain current behavior exactly (no format analysis step).

Update get_audio_formats() to include language field.
Update \_parse_metadata() to include formats list in output.

3.2 Update CeleryDownloadService

Modify: backend/app/infrastructure/services/celery_download_service.py

Add audio_language and audio_quality params to download_episode(). Pass them to youtube_service.download_audio(). After download, call
episode.set_audio_preferences() with actual results.

3.3 Update DownloadService (FastAPI version - transitional)

Modify: backend/app/infrastructure/services/download_service.py

Add audio_language and audio_quality params to queue_download() and \_download_episode_task(). This keeps Path 1 working during
transition before Phase 6 (Celery migration).

---

Phase 4: Celery Task Updates

4.1 Update download_episode task

Modify: backend/app/infrastructure/tasks/download_episode_task.py

Add audio_language and audio_quality params. Pass to CeleryDownloadService.download_episode().

4.2 Update create_episode_from_youtube_video task

Modify: backend/app/infrastructure/tasks/create_episode_from_video_task.py

Add audio_language and audio_quality params. Pass to download_episode.apply_async() kwargs.

---

Phase 5: API Endpoint Changes

5.1 Update POST /v1/episodes/

Modify: backend/app/presentation/api/v1/episodes.py (line 274)

Pass episode_data.audio_language and episode_data.audio_quality through to the download path.

Also update EpisodeService.create_from_youtube_url() to store requested_language and requested_quality on the episode entity at
creation time.

5.2 Update POST /v1/youtube-videos/{id}/create-episode

Modify: backend/app/presentation/api/v1/youtube_videos.py

Pass request.audio_language and request.audio_quality to the Celery task.

5.3 Update related application services

Modify: backend/app/application/services/episode_service.py - add params to create_from_youtube_url()

---

Phase 6: Migrate Path 1 (Direct UI) to Celery

6.1 Replace BackgroundTasks with Celery in create_episode endpoint

Modify: backend/app/presentation/api/v1/episodes.py

Replace:
background_tasks.add_task(\_isolated_download_queue, download_service, episode_id)
With:
from app.infrastructure.tasks.download_episode_task import download_episode
download_episode.apply_async(
args=(episode_id,),
kwargs={'channel_id': ..., 'audio_language': ..., 'audio_quality': ...}
)

Remove BackgroundTasks and DownloadService dependencies from the endpoint. Remove \_isolated_download_queue() helper.

6.2 Update retry/redownload endpoint

Modify: backend/app/presentation/api/v1/episodes.py

Replace download_service.queue_download() with download_episode.apply_async(), re-using original requested_language/requested_quality
from the episode.

6.3 Progress tracking

The GET /v1/episodes/{id}/progress endpoint already has a database fallback path (when no in-memory progress exists). After Celery
migration, this fallback will be the primary path. Episode status (PENDING/PROCESSING/COMPLETED/FAILED) is updated by
CeleryDownloadService in the DB, so the endpoint will continue to work.

6.4 Mark DownloadService as deprecated

Add deprecation comment to backend/app/infrastructure/services/download_service.py. The get_download_service dependency can remain but
won't be used by the create/retry endpoints.

---

Phase 7: Frontend UI Changes

7.1 Update TypeScript Types

Modify: frontend/src/types/episode.ts and frontend/src/types/index.ts

Add to CreateEpisodeRequest / EpisodeCreate:

- audio_language?: string | null
- audio_quality?: string | null

Add to CreateEpisodeFromVideoRequest:

- audio_language?: string | null
- audio_quality?: string | null

Add to Episode interface:

- audio_language, audio_quality, requested_language, requested_quality (all string | null)

  7.2 Create AudioOptionsSelector Component (Shared)

Create: frontend/src/components/features/episodes/audio-options-selector.tsx

Reusable component with:

- Optional "Custom audio options" checkbox (showToggle prop)
- Language dropdown: "Original (default)", "English", "Spanish"
- Quality dropdown: "Low (up to 70 kbps)" (pre-selected), "Medium (70-150 kbps)", "High (150+ kbps)"

When checkbox is unchecked (or showToggle=false and no values set), audio_language and audio_quality are null → backend uses current
default behavior (original language, best quality).

When checkbox is checked, defaults to language="default" and quality="low" as specified.

Uses ShadCN: Select, SelectTrigger, SelectValue, SelectContent, SelectItem, Checkbox, Label.

7.3 Update Quick Add Dialog

Modify: frontend/src/components/features/episodes/quick-add-dialog.tsx

- Add state: audioLanguage, audioQuality
- Add <AudioOptionsSelector showToggle={true} /> between URL input and footer
- Pass values in episodeApi.create() call
- Reset state on dialog close

  7.4 Update Add Episode Form (Multi-step)

Modify: frontend/src/components/features/episodes/add-episode-form.tsx

- Add state and <AudioOptionsSelector showToggle={true} /> in Step 1 below URL input
- Pass values in handleCreateEpisode()

  7.5 Update Video List Create Episode Dialog

Modify: frontend/src/components/features/subscriptions/video-list.tsx

- Add state and <AudioOptionsSelector showToggle={true} /> below channel selector in create episode dialog (~line 617)
- Pass values in createEpisodeMutation.mutateAsync() call
- Reset audio state when dialog closes
- Same for bulk create dialog (~line 676)

  7.6 Update API Clients

Modify: frontend/src/lib/api.ts - pass new fields in episodeApi.create()
Modify: frontend/src/lib/api-client.ts - pass new fields in createEpisode() and createEpisodeFromVideo()

Hooks (use-episodes.ts, use-youtube-videos.ts) require no changes - they pass through the typed request objects.

---

Phase 8: Event & Notification Enhancements

8.1 Enrich download events

Modify: backend/app/infrastructure/services/celery_download_service.py

- download_started event: include requested_language, requested_quality
- download_completed event: include actual_language, actual_quality, fallback_occurred, fallback_reason

  8.2 Fallback notification

After successful download in CeleryDownloadService, if fallback_occurred, create a user notification:

- Title: "Audio Quality Fallback"
- Message: "Requested [lang]/[quality], downloaded [actual_lang]/[actual_quality]: [reason]"
- Type: EPISODE_CREATED (reuse existing type)

---

Verification Plan

Backend

cd backend
uv run alembic upgrade head # Apply migration
uv run fastapi dev app/main.py # Start dev server

# Test: POST /v1/episodes/ with audio_language/audio_quality → verify episode created with fields

# Test: POST /v1/episodes/ without audio fields → verify backward compatibility

# Test: POST /v1/youtube-videos/{id}/create-episode with audio fields

Frontend

cd frontend
npm run lint # Lint check
npx tsc --noEmit # Type check
npm run dev # Start dev server

# Test: Quick Add → toggle custom options → verify dropdowns → submit

# Test: Add from YouTube page → verify audio options on Step 1

# Test: Subscriptions/Videos → Create Episode → verify audio options in dialog

Integration (Docker)

docker compose --env-file .env.development -f docker-compose.dev.yml up --build

# Test full flow: Quick Add with custom language/quality → verify Celery task picks up → episode completed with correct fields

# Test fallback: Request Spanish track on English-only video → verify fallback notification

---

Key Files Summary
Area: Migration
File: backend/alembic/versions/<new>
Change: New: 4 columns
────────────────────────────────────────
Area: DB Model
File: backend/app/infrastructure/database/models/episode.py
Change: Add 4 columns
────────────────────────────────────────
Area: Domain
File: backend/app/domain/entities/episode.py
Change: Add 4 fields + method
────────────────────────────────────────
Area: Value Object
File: backend/app/domain/value_objects/audio_quality.py
Change: New file
────────────────────────────────────────
Area: Format Service
File: backend/app/infrastructure/services/audio_format_selection_service.py
Change: New file
────────────────────────────────────────
Area: YouTube Service
File: backend/app/infrastructure/services/youtube_service.py
Change: Add lang/quality to download_audio
────────────────────────────────────────
Area: Celery Download
File: backend/app/infrastructure/services/celery_download_service.py
Change: Add lang/quality params + fallback notification
────────────────────────────────────────
Area: Download Task
File: backend/app/infrastructure/tasks/download_episode_task.py
Change: Add lang/quality params
────────────────────────────────────────
Area: Create Task
File: backend/app/infrastructure/tasks/create_episode_from_video_task.py
Change: Add lang/quality params
────────────────────────────────────────
Area: Episode API
File: backend/app/presentation/api/v1/episodes.py
Change: Migrate to Celery + add params
────────────────────────────────────────
Area: Video API
File: backend/app/presentation/api/v1/youtube_videos.py
Change: Add params
────────────────────────────────────────
Area: Schemas
File: backend/app/presentation/schemas/episode_schemas.py
Change: Add fields
────────────────────────────────────────
Area: Episode Service
File: backend/app/application/services/episode_service.py
Change: Add params
────────────────────────────────────────
Area: Repo Mapper
File: backend/app/infrastructure/repositories/episode_repository.py
Change: Map new fields
────────────────────────────────────────
Area: Types
File: frontend/src/types/episode.ts, frontend/src/types/index.ts
Change: Add fields
────────────────────────────────────────
Area: UI Component
File: frontend/src/components/features/episodes/audio-options-selector.tsx
Change: New file
────────────────────────────────────────
Area: Quick Add
File: frontend/src/components/features/episodes/quick-add-dialog.tsx
Change: Add audio options
────────────────────────────────────────
Area: Add Form
File: frontend/src/components/features/episodes/add-episode-form.tsx
Change: Add audio options
────────────────────────────────────────
Area: Video List
File: frontend/src/components/features/subscriptions/video-list.tsx
Change: Add audio options to create dialog
────────────────────────────────────────
Area: API Client
File: frontend/src/lib/api.ts, frontend/src/lib/api-client.ts
Change: Pass new fields
Implementation Order

1. Phase 1 (Data layer) → 2 (Format service) → 3 (Service updates) → 4 (Celery tasks) → 5 (API endpoints)
2. Phase 6 (Celery migration) - can be done after Phase 5
3. Phase 7 (Frontend) - depends on Phase 5
4. Phase 8 (Events) - can be done alongside Phase 3

Risk Notes

- yt-dlp language tracks: Not all YouTube videos have language metadata on audio formats. The format selection service must gracefully
  handle this (fallback to default behavior).
- Celery migration: After Phase 6, Redis + Celery must be running for ANY episode creation (not just subscription videos). Docker dev
  environment already has this, but local dev without Docker needs celery -A app.infrastructure.celery_app worker.
- Progress tracking: After Celery migration, the in-memory progress tracking via DownloadService is gone. The existing DB-based
  fallback in the progress endpoint handles this, but granular percentage tracking is lost (only status transitions remain).
  ╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌

Claude has written up a plan and is ready to execute. Would you like to proceed?

1. Yes, clear context and auto-accept edits (shift+tab)
2. Yes, auto-accept edits
3. Yes, manually approve edits
   ❯ 4. Type here to tell Claude what to change

ctrl-g to edit in VS Code · ~/.claude/plans/delegated-squishing-nova.md
