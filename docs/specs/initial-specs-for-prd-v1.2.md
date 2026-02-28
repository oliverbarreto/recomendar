# LabCastARR – Requirements Specification (PRD + Tech Spec Hybrid)

## 1. Objective & Scope

Objective:
Build a self-hosted application that allows users to download audio tracks from YouTube videos and create a personal podcast channel, consumable by popular podcast apps (Spotify, Apple Podcast, etc.).

Scope:
- Support single videos only (no playlists).
- No length restriction on videos.
- Support mp3 and m4a formats only (to avoid conversion complexity).
- Once downloaded, audio files are static (no reprocessing if metadata/tags change on YouTube).
- Prevent duplicate downloads:
  - The system must detect if a video already exists.
  - Attempts to redownload must return an informative response referencing the existing episode.
- Only global channel artwork will be supported in the RSS feed (episode-specific artwork may be added in the future).

⸻

## 2. Architecture & Communication
- Frontend ↔ Backend communication:
     - Frontend calls backend REST endpoints directly.
     - No reverse proxy required for local use.
     - Backend must configure proper CORS policy.
- Download jobs:
     - Use FastAPI BackgroundTasks only.
     - Potential future upgrade: Celery/RQ for scalability (DO NOT IMPLEMEMENT NOW).
- Progress updates:
     - Implement polling for progress status.
     - WebSockets may be added in the future.
     - Retries:
     - Backend must retry failed downloads up to 3 times per video.
- RSS feed:
     - Always public and accessible without authentication.
     - Must be regenerated automatically whenever episodes are added, updated, or deleted.

⸻

## 3. Data & Models

Episode Metadata (mandatory fields):
- video_id (string – YouTube ID, unique)
- title (string)
- description (string)
- publication_date (datetime)
- audio_url (string – stored file path)
- video_url (string – YouTube URL)
- thumbnail_url (string)
- duration (int – seconds)
- tags (list of strings, user-assigned, can be empty)
- keywords (list of strings, from YouTube metadata, can be empty)
- download_date (datetime)
- status (enum: pending, processing, completed, failed)
- created_at (timestamp)
- updated_at (timestamp)

Tags
- Created and managed by the user.
- Many-to-many relationship with episodes.

Events: Must record:
    - When a user requests a download.
    - When the backend starts processing.
    - When the download succeeds.
    - When a retry is triggered.
    - When download fails after 3 retries.

Channel Settings
- Global channel information (title, description, image, author, etc.).

⸻

## 4. Frontend UX
- Frameworks: Next.js 15+, TypeScript, ShadCN v4 UI, TailwindCSS, Lucide Icons, React Query, Zod.
- Design:
     - Responsive, mobile-first.
     - Dark/light theme toggle (ShadCN theming).
     - Skeleton loaders and placeholders for long operations.
     - Clear error boundaries.
- Notifications:
     - Ephemeral, using ShadCN toast component.
     - No persistence in DB.
- Core pages:
  - /channel: Grid of episodes, search/filter by title, description, author, tags, keywords.
     - /episodes/add: Form to submit YouTube URL. Shows placeholder → updates with metadata → updates with download status.
     - /episodes/{id}: Episode details, edit metadata, delete, play audio, link to YouTube.
     - /settings: Manage podcast channel info and tags CRUD.
- User feedback:
     - Show progress (polling backend).
     - Handle failures with retry messaging.

⸻

## 5. Backend APIs

Frameworks: FastAPI, SQLAlchemy, Alembic, Pydantic, yt-dlp, PodGen, SQLite.

Core Endpoints:
- POST /episodes → Submit YouTube URL, create download task.
- GET /episodes → List episodes.
- GET /episodes/{id} → Get episode details.
- PUT /episodes/{id} → Update metadata.
- DELETE /episodes/{id} → Delete episode (must also delete associated audio file).
- GET /settings → Get channel settings.
- PUT /settings → Update channel settings.
- GET /tags → List tags.
- POST /tags → Create tag.
- PUT /tags/{id} → Update tag.
- DELETE /tags/{id} → Delete tag.
- GET /feeds/feed.xml → Get current Public RSS feed (This endpoint is public, no auth, and will serve the xml file stored in the file system. The file is updated when we add/remove an episode from the channel - eg: https://yourdomain.com/feeds/feed.xml).
- POST /feeds/regenerate → Force regeneration of feed.
- GET /events → Retrieve recent events (last 30 days).
- GET /health → Health check.
- GET /metrics → Metrics endpoint.

API Behavior
	- Consistent response schema:
```json
{ 
    "status": "success|error", 
    "data": {}, 
    "error": { "code": "ERR_CODE", "message": "..." } 
}
```

- Common error codes:
    - ERR_INVALID_URL
    - ERR_VIDEO_UNAVAILABLE
    - ERR_DOWNLOAD_FAILED
    - ERR_DUPLICATE_VIDEO
- Auto-cleanup:
    - Audio files must be deleted when episodes are deleted.

⸻

## 6. Security
- Authentication:
     - Initially: API Key (via Authorization: Bearer <token>).
 	- Future-proof: Evaluate JWT support for better frontend integration.
- Static files:
  - Serve only /media folder.
- Transport:
  - HTTPS mandatory for RSS feed consumption by Spotify/Apple.
- Logging:
  - Audit logs for all user actions (downloads, deletions, settings changes).

⸻

## 7. Deployment
- Containerized with Docker + Docker Compose.
- Persistent volumes for database and media files.
- Must support ARM64 (Raspberry Pi homelab friendly).
- CI/CD pipeline:
  - Linting, testing, and build stages included.

⸻

## 8. Observability & Maintenance
- Logging:
     - Structured JSON logs.
     - Event tracing from user action → event → log.
- Metrics:
  - Expose /metrics for Prometheus scraping.
- Retention:
  - Events stored for 30 days, auto-cleanup after expiration.

⸻

## 9. Out of Scope (Future Considerations)
- WebSocket-based real-time updates.
- Multi-user authentication.
- Rate limiting.
- Episode-specific artwork.
- Audio normalization/conversion (e.g., pydub).
- Playlist downloads.
- Cloud storage backends (S3, etc.).

⸻