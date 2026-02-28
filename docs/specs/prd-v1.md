# LabCastARR

## 1. Objective & Scope

Objective:
Build a self-hosted application that allows users to download audio tracks from YouTube videos and create a personal podcast channel, consumable by popular podcast apps (Spotify, Apple Podcast, etc.).

Scope:
- Support download of single videos only (no playlists).
- `video_id` is the unique identifier of the video in Youtube and of episodes in our app.
- No length restriction on videos.
- Support `.mp3` and `.m4a` formats only (to avoid conversion complexity).
- Once downloaded, audio files are static (no reprocessing if metadata/tags change on YouTube).
- Prevent duplicate downloads:
  - The system must detect if a video already exists (by the `video_id` extrated from the youtube url).
  - Attempts to redownload must return an informative response referencing the existing episode.
- Only global channel artwork will be supported in the RSS feed (episode-specific artwork may be added in the future - DO NOT IMPLEMEMENT NOW).

Target Users:
- Users who want to create a personal podcast channel from YouTube videos.


## 2. Architecture & Communication
The app is a monorepo comprised by a frontend and a backend: 

- The frontend (`frontend/`) will be a next web application that will allow users to upload an url of a youtube video that will be passed to the backend. The backend is responsible for downloading the audio files from Youtube (using a library called yt-dlp). The web app will also allow the user to list all the audio files that have been downloaded. It will also allow otehr CRUD operations like delete audio files and the podcast feed. 

- The backend (`backend/`) will be a FastAPI application that will handle the requests from the frontend and will be responsible for downloading the audio files from Youtube, processing them and returning the results to the frontend. The backend will also be responsible for creating the podcast feed (RSS) that can be used by most popular podcast applications.

- The old monolithic flask app is located in the `web/` folder and is only for reference and will be removed later.

**Example of Project Structure following a clean architecture approach:**
```
/LabCastARR
  /docs (documentation folder)
  /web (old monolithic flask app for reference)
  /backend
    /app
      /api
      /core
      /models
      /schemas
      /services
      /utils
      /static
        /feeds (folder to store the podcast xml feed RSS/XML file)
        /media (folder to store the audio files)
      /tests
      main.py
    Dockerfile
    requirements.txt
  /frontend
    /src
      app/
        (api)/            # Route Handlers (if needed)
        (web)/
          components/     # Page-specific, non-shared components
          episodes/
            [id]/
              page.tsx    # RSC for episode page
              actions.ts  # Server Actions for this route
          settings/
            page.tsx      # RSC for settings page
            actions.ts    # Server Actions for this route
          ...
        layout.tsx
        global.css
      components/             # Global, shared React components (e.g., Button, Input)
        ui/
      core/                   # 💎 THE CORE: Framework-agnostic logic
        domain/
          entities/       # e.g., user.ts, product.ts (types/classes)
          repositories/   # e.g., user-repository.ts (interfaces/abstract classes)
        use-cases/          # e.g., get-user-profile.ts, create-product.ts
      infra/                  # ⚙️ IMPLEMENTATIONS: The messy real world
        database/           # Prisma schema, Drizzle kit, etc.
        providers/          # Concrete repository implementations
          prisma/
            prisma-user-repository.ts
        services/           # External API clients (e.g., Stripe, Sentry)
      lib/                  # Shared utilities, constants, config
        db.ts               # Prisma/Drizzle client instance
        utils.ts
      hooks/
      types/
      config/
      tests/
    next.config.js
    package.json
    Dockerfile
  .env
  docker-compose.yml
  README.md
```

- Frontend ↔ Backend communication:
     - Frontend calls backend REST endpoints directly.
     - No reverse proxy required for local use.
     - Backend must configure proper CORS policy.
- Download jobs:
     - Use FastAPI BackgroundTasks only.
     - Potential future upgrade: Celery/RQ for scalability (DO NOT IMPLEMEMENT NOW).
- Progress updates:
     - Implement polling for progress status.
     - WebSockets may be added in the future (DO NOT IMPLEMEMENT NOW).
- Retries:
     - Backend must retry failed downloads up to 3 times per video.
- RSS feed:
     - Always public and accessible without authentication.
     - Must be regenerated automatically whenever episodes are added, updated, or deleted.


## 3. Data & Models

As a summary, the data models defined next will be used to create the database schema with the following relationships and indexes:

- **User → Channel**: One-to-many relationship with cascade delete
- **Channel → Episode**: One-to-many relationship with cascade delete
- **Episode → Tags**: Many-to-many relationship with cascade delete
- **Episode → Events**: One-to-many relationship with cascade delete
- **Optimized Indexes**: Strategic indexing for common queries
- **Data Integrity**: Foreign key constraints and validation rules


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

Channel Settings:
  - Channel Info:
    - Podcast channel name (string)
    - description (string)
    - personal website (URL)  
    - channel image (URL)
    - category (string)
    - language (string)
    - The channel episodes might contain explicit content (boolean),
    - public feed url (URL: created automatically by the backend with the domain set in .env file and the following format: `https://{your_domain}/feeds/{user_name}_feed.xml`)
  - Authoring:
    - author name and email (string)
    - owner name and email (string)

User: even though the app is not a user-based app, we will still need a user model to store the channel information and the episodes information.
  - User:
  - name (string)
  - email (string)
  - password (string)
  - admin (boolean)
  - channel (relationship to Channel)

Channel:
  - name (string)
  - description (string)
  - website (URL)

## 4. Frontend UX
- Frameworks: Next.js 15+, TypeScript, ShadCN v4 UI, TailwindCSS, Lucide Icons, React Query, Zod, react-hook-form.
- Design:
  - Responsive, mobile-first.
  - Dark/light theme toggle (ShadCN theming).
  - Skeleton loaders and placeholders for long operations.
  - Clear error boundaries.
- Notifications:
  - Ephemeral, using ShadCN toast component.
  - No persistence in DB.
- Core pages:
  - /channel: Grid of episodes, search/filter by title, description, author, tags, keywords. It will also have:
    - a search text box to filter the episodes of the /channel page by title, description, author, tags, keywords, etc.
    - It should allow sorting options by title, description, author, tags, keywords, etc.
    - It should allow pagination if there are many audio files.
    - it should sort episodes by date, with the most recent episode at the top.
    - It should have a notification icon to show a log of download events like a navigation or download history log (of the last 24 hours, or week, or 30 days). The log should be a list of events that reflect the status of the downloads like "Downloading audio file from Youtube", "Processing audio file", "Audio file downloaded successfully", "Error downloading audio file", etc. It should also group the events by date and sort by time (most recent at the top). It should also allow the user to clear the log.
   - /episodes/add: Form to submit YouTube URL. Shows placeholder → updates with metadata → updates with download status.
   - /episodes/{id}: Episode details, edit metadata, delete, play audio, link to YouTube.
 - /settings: Manage podcast channel info and tags CRUD.
- User feedback:
  - Show progress (polling backend).
  - Handle failures with retry messaging.


## 5. Backend APIs

**Backend Dependencies:**
We will use `uv` to manage libraries and dependencies for the backend.
- Dependencies are declared in `pyproject.toml` under the `[project.dependencies]` section (and `[project.optional-dependencies]` for development tools if desired).
    - `uv` uses this file to resolve and install packages. You might create a virtual environment using `uv venv` and install dependencies with `uv pip sync pyproject.toml` or `uv pip install -r requirements.txt` if you choose to generate one using `uv pip compile pyproject.toml -o requirements.txt`.
    - `uv` can also manage virtual environments directly.

**Backend Frameworks and libraries:**
Frameworks: FastAPI, SQLAlchemy, Alembic, Pydantic, yt-dlp, PodGen, SQLite.
- The backend will be a FastAPI application that will handle the requests from the frontend and will use the `yt-dlp` library to download the audio files from Youtube and to access metadata about the videos.
- The backend will use a database to store the information about the audio files and the podcast feed, users settings, and about the podcast channel. The database will be a `SQLite` database for simplicity.
- The backend will also use a storage service to store the audio files. The storage service will be a local file system for simplicity. The files will be shared as FastAPI static files.
- The backend will also use a library called `PodGen` to create the podcast feed (RSS) which will be stored in the local file system and will be accesible by Podcast applications via a route served by FastAPI backend.
- **Optional** we will consider the following option: The backend will also use a library called `pydub` to process the audio files (e.g. convert them to mp3 format, normalize the audio, etc.).
  

**Core Endpoints:**
EPISODES:
- POST /episodes → Submit YouTube URL, create download task.
- GET /episodes → List episodes.
- GET /episodes/{id} → Get episode details.
- PUT /episodes/{id} → Update metadata.
- DELETE /episodes/{id} → Delete episode (must also delete associated audio file).

SETTINGS:
- GET /settings → Get channel settings.
- PUT /settings → Update channel settings.

TAGS:
- GET /tags → List tags.
- POST /tags → Create tag.
- PUT /tags/{id} → Update tag.
- DELETE /tags/{id} → Delete tag.

FEEDS:
- GET /feeds/feed.xml → Get current Public RSS feed (This endpoint is public, no auth, and will serve the xml file stored in the file system. The file is updated when we add/remove an episode from the channel - eg: https://yourdomain.com/feeds/feed.xml).
- POST /feeds/regenerate → Force regeneration of feed.

STATISTICS:
- GET /events → Retrieve recent events (last 30 days).
- GET /health → Health check.
- GET /metrics → Metrics endpoint.

**API Behavior**
	- Consistent response schema:
```json
{ 
    "status": "success|error", 
    "data": {}, 
    "error": { "code": "ERR_CODE", "message": "..." } 
}
```

**Common error codes:**
    - ERR_INVALID_URL
    - ERR_VIDEO_UNAVAILABLE
    - ERR_DOWNLOAD_FAILED
    - ERR_DUPLICATE_VIDEO

**Auto-cleanup:**
    - Audio files must be deleted when episodes are deleted.


## 6. Security
- Authentication:
     - Initially: API Key (via `Authorization: Bearer <token>`).
 	- Future-proof: Evaluate JWT support for better frontend integration.
- Static files:
  - Serve only `/media` folder.
- Transport:
  - HTTPS mandatory for RSS feed consumption by Spotify/Apple. The application must be able to provide a `https` endpoint behind a reverse proxy like Nginx Proxy Manager, to allow Apple Podcast and Spotify to access the podcast feed.

- Logging:
  - Audit logs for all user actions (downloads, deletions, settings changes).


## 7. Deployment
- The app should use a `.env` file at root project folder to manage environment variables for both frontend and backend (eg: the domain name of the published RSS feed, the podcast channel name, description, author, the API KEY used by the frontend and backend, etc.).
- The app should use a `.env.example` file to show the required environment variables for both frontend and backend.
- For production, the app should be Containerized with Docker + Docker Compose (single docker-compose.yml file for both frontend and backend and individual Dockerfile files for each service). For development, the app should be run locally with the frontend and backend running independently.
- Docker Compose should use Persistent mounted volumes for database and media files.
- Must support ARM64 (Apple silicon friendly).


## 8. Observability & Maintenance
- Logging:
     - Structured JSON logs.
     - Event tracing from user action → event → log.
- Metrics:
  - Expose /metrics for Prometheus scraping.
- Retention:
  - Events stored for 30 days, auto-cleanup after expiration.


## 9. Out of Scope (Future Considerations)
- WebSocket-based real-time updates.
- Multi-user authentication.
- JWT authentication.
- Rate limiting.
- Episode-specific artwork.
- Audio normalization/conversion (e.g., pydub).
- Playlist downloads.
- Cloud storage backends (S3, etc.).


## 10. Expected Important Features & Workflows

### Frontend User Experience & Features
- The frontend should allow users to:
  - Upload a youtube video url to download the audio file.
  - List all the audio files that have been downloaded.
  - Search episodes by title, description, author, tags, keywords, etc.
  - Delete episodes and their associated audio files.
  - Assign, change and remove multiple tags to an episode.
  - Edit the metadata of an episode (title, description, author, date, duration, tags, keyworkds, etc.). The initial metadata is downloaded by the backend using a library, in this case `yt-dlp`.
  - View the progress of the audio files that are being downloaded.
  - View the latest events (what episodes were downloaded, what episodes were deleted, what episodes were edited, etc.) like a navigation history log of the last 24 hours
  - View and manage user settings (podcast channel name, description, author, tags, etc.).
  - View and manage the podcast feed (RSS).

### Workflow of adding an episode
- The frontend should have the following flow for adding an episode:
  - Must have a route to add an episode that uses a youtube video url using a simple post request with the url of the video that we want to download.
    - The page should have a form with a single input field for the youtube video url and a submit button.
    - The backend should validate the url and return an error message if the url is not valid. It should also extract the `youtube_video_id` from the url and return an error message if the `youtube_video_id` is not valid.
    - After sending the request to the backend, it should first redirect to the homepage with the list of videos of the channel and show a loading indicator while the audio file is being downloaded. The process of downloading a videos has two main parts:
      - We should extract the metadata of the video (title, description, author, etc.)
      - We must download as a background task in the backend the best audio track available for the video.
      - The front end should add a place holder component for the video right after we reqeust the download.
      - After the backend acceeses the metadata of the video, it should update the place holder with a "video card" component: thumbnail, title, description, author, date, duration, tags, keyworkds, etc. It should also show a loading indicator to show that the audio file is being downloaded.
      - It should communicate with the backend using websockets to get real time updates about the progress of the download.
      - Once the audio file has been downloaded, it should update the "video card" component to show that the audio file is available for playback and download.
      - The "video card" should have a play button to play the audio file using an HTML5 audio player.
    - The frontend should handle the request to the backend to periodically query the status of the download until it is completed or failed. It should show a success message when the audio file has been downloaded successfully. It should show an error message when the audio file could not be downloaded.

### Workflow of viewing an episode on the frontend
  - The frontend should use the API route to get an episode information by id and then show a full page with the the episode information from the stored metatada. The page should have:
    - It should include buttons to edit/delete the episode info.
    - The episode page should also have an HTML5 audio player to play the audio file (sotored in the backend as static file).
    - It should also have a play in youtube button to link the episode with the original video in Youtube.
    - The information of the video is first extracted by the backend using the yt-dlp library and then stored in the database. The page should have allow the user to use a form to edit the metadata of the episode: title, description, author, date, duration, tags, keyworkds, etc.
    - It should allow the user to add/remove tags to the episode.


### Backend Functionality
- The backend should have the following functionalities:
  - The backend should handle the requests from the frontend and return the appropriate responses and utilize background tasks for long running tasks.
  - The backend should use the `yt-dlp` library to download the audio files from Youtube and get the metadata about the videos.
  - The backend should use the `PodGen` library to create the podcast feed (RSS) that will be accesible by Podcast applications.
  - The backend should store the metadata of the audio file in a `SQLite` database.
  - The backend should use the local file system to store the audio files. It should create a folder called `media` inside the `static` files folder in the backend to store and share the audio files (eg: "https://labcastarr.oliverbarreto.com/static/media/yLjAI19z1xU.m4a").
  - The backend should register all events requested by the user in the database to allow an endpoint to get the latest events like a navigation history.
  - The backend should allow the frontend to get real time updates about the progress of the download.
  - the backend should provide an endpoint to check the health of the backend.
  - the backend should provide an endpoint to get the metrics of the backend (for monitoring purposes).
  - the backend should model:
    - channel settings
    - episodes (created from Youtuve videos which result in metadata of the video and the audio file downloaded into the local file system)
    - tags associated to episodes (many to many relationship)
    - events (for navigation history): id, type, message, timestamp, status (requested, processing, downloading, completed, failed)
    - users (for authentication purposes, even if it is a single user app)
    - ...
  - **Optional** process the audio file using the pydub library (e.g. convert to mp3 format, normalize the audio, etc.).



