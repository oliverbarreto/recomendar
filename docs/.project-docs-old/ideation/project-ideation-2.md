# Project Ideation 2

## Prompt:

Now that we have a deep understanding of how the project is structured i want you to analyze and how to go about changing the architecture of the app to build it from scratch (reusing only if needed) to create:

1. frontend using Nextjs v15 with app router and react 19 application
2. backend using FastAPI latest version

The important aspect is that we should also try to take advantage of the architecture change to create more modular and decoupled code, and separate concerns since there are files/classes that "do too many things", using an approach not fully strict, but more aligned with clean architecure and SOLID principles. "SOLID, but simplified in a practical way".

I now provide you some guidelines for each part:

## Frontend
- Let's use Nextjs app capabilities to move the use of github to host the user xml feed page for iTunes Podcast. The app now will have a requirement to have https communications with a domain. We can use for example Xnignx Proxy Manager as a reverse proxy to provide HTTP with a Let's Encrypt certificate. 
- The frontend now will need to use the backend in async mode, and provide a better management of creating a video, by showing indication to the user tha the video has been sent to the server, and that it is processing, and finally, when the server has finnished extracting the audio, and the file is fully ready, notifying that it finnished.

## Backend
- We need to analyze current state of the art of python libraries to extract the audio, and metadata to add to the database, from the youtube video (eg: https://github.com/yt-dlp/yt-dlp, or https://github.com/juanbindez/pytubefix)
- if the extraction api does not allow it, we need to find a way to also pull the video transcript, we can use a separate api for that (eg: https://supadata.ai). 
- we have to store audio files locally using FastAPI server
- take advantage of FastAPI async capabilities
- The data model should also be revised to improve, and use SQLite but using async capabilities

@web 

## Response:

This is an excellent goal! Migrating your Flask/SQLite application to a modern Next.js frontend and a FastAPI backend, while focusing on modularity and clean architecture principles, will set you up for better scalability, maintainability, and developer experience.

Here's a detailed analysis and a proposed approach for this architectural transformation:

**I. Guiding Principles & Overall Architecture**

*   **Decoupling:** The frontend (Next.js) and backend (FastAPI) will be completely separate applications communicating via a well-defined REST API (or GraphQL, though REST is often simpler to start with for this kind of migration).
*   **Modularity (Backend):** We'll break down the FastAPI backend into logical services or modules, each responsible for a specific domain (e.g., users, YouTube interaction, podcast generation). This aligns with the Single Responsibility Principle (SRP).
*   **Async All The Way (Backend):** FastAPI excels at asynchronous operations. We'll leverage this for all I/O-bound tasks: interacting with external APIs (YouTube, transcript services), database operations (async SQLite), and file system access.
*   **Clear API Contract:** Define API endpoints, request/response schemas (using Pydantic in FastAPI) early on. This contract will guide both frontend and backend development.
*   **HTTPS by Default:** As you've noted, HTTPS is a requirement. The backend or Next.js will serve the XML feed directly, and a reverse proxy (like Nginx Proxy Manager) will handle SSL termination.
*   **SOLID, Simplified:**
    *   **SRP:** Each class/module in the backend will have one primary responsibility.
    *   **OCP (Open/Closed Principle):** Design services to be extensible without modifying existing code (e.g., adding a new transcript provider).
    *   **LSP (Liskov Substitution Principle):** Less critical at this stage but good to keep in mind for class hierarchies if they emerge.
    *   **ISP (Interface Segregation Principle):** Define focused interfaces (ABCs or Protocols in Python) for services if needed, especially for test mocking.
    *   **DIP (Dependency Inversion Principle):** FastAPI's dependency injection system will be heavily used. Services will depend on abstractions (like a database session provider or other service interfaces) rather than concrete implementations.

**II. Backend Refactoring (FastAPI)**

The backend will be the new source of truth for data and business logic.

**A. Project Setup & Core (FastAPI):**

1.  **Initialize Project:** Use a modern Python project manager like Poetry or PDM.
2.  **FastAPI Core:**
    *   Main application instance.
    *   Routers for different domains (e.g., `users_router.py`, `episodes_router.py`).
3.  **Configuration:**
    *   Use Pydantic's `BaseSettings` to load configuration from environment variables (similar to your current `.env` approach). This will include database URLs, API keys, storage paths, etc.
4.  **Database (Async SQLite):**
    *   **ORM/Driver:**
        *   **SQLModel:** Built on Pydantic and SQLAlchemy, offers a great developer experience for FastAPI, naturally async.
        *   **SQLAlchemy 2.0+:** Has mature async support with `aiosqlite`.
        *   **Tortoise ORM:** Another popular async ORM.
    *   **Connection Management:** Set up async database session management for dependency injection in FastAPI.
    *   **Migrations:** Use Alembic (even with SQLModel, as it uses SQLAlchemy under the hood) in its async configuration to manage schema changes.

**B. Data Models & Schemas:**

1.  **Pydantic Schemas:** Define Pydantic models for:
    *   API request bodies (e.g., `UserCreate`, `EpisodeCreatePayload`).
    *   API response bodies (e.g., `UserResponse`, `EpisodeResponse`).
    *   Configuration models.
2.  **ORM Models (e.g., using SQLModel or SQLAlchemy):**
    *   Revisit `User`, `Channel`, `Episode` models from your Flask app.
    *   **User:** `id`, `name`, `email`, `hashed_password`, `is_admin`, `date_created`, `date_modified`.
    *   **Channel:** `id`, `user_id` (FK), `name`, `description`, `website`, `explicit`, `image_url` (path to locally stored image), `copyright`, `language`, `category`, `authors`, `authors_email`, `owner`, `owner_email`, `date_created`, `date_modified`.
        *   The `feed_url` will now be a dynamically generated URL from your FastAPI app (e.g., `https://yourdomain.com/api/v1/podcasts/{user_id}/feed.xml`).
    *   **Episode:** `id`, `channel_id` (FK), `youtube_url`, `video_id`, `title`, `description`, `subtitle`, `summary`, `author`, `thumbnail_url` (path to locally stored thumbnail), `published_at` (from YouTube), `keywords`, `duration_seconds`, `audio_file_path` (local path), `audio_file_size`, `is_downloaded`, `transcript` (TEXT field, nullable), `date_created`, `date_modified`.
        *   `mediaurl` becomes a dynamic URL from your FastAPI app serving the local audio file.

**C. YouTube & Transcript Services:**

1.  **YouTube Library Selection:**
    *   **`yt-dlp`:** Very powerful, actively maintained, and can extract extensive metadata and download streams. It's often preferred for its robustness and feature set. It can be used as a CLI tool (subprocess call) or potentially has Python bindings/wrappers.
    *   **`pytubefix`:** You're familiar with it. If it meets your needs for metadata and audio stream access and is easier to integrate directly in Python, it's a viable option. Re-assess its current capabilities and maintenance.
2.  **Transcript Service:**
    *   **`youtube-transcript-api` (Python library):** Often a good first choice for fetching YouTube-generated transcripts.
    *   **External AI Services (e.g., Supabase Storage with Edge Functions, AssemblyAI, Deepgram):** If higher accuracy or features like speaker diarization are needed, and `youtube-transcript-api` isn't sufficient. This adds external API calls and potential costs.
3.  **Implementation (`youtube_service.py`, `transcript_service.py`):**
    *   Create async functions to:
        *   `get_video_info(youtube_url: str) -> VideoDetailsSchema`: Returns Pydantic schema with title, description, thumbnail URL, duration, publish date, etc.
        *   `download_audio(youtube_url: str, output_path: str) -> DownloadedAudioInfo`: Downloads audio, returns path and filesize.
        *   `get_transcript(video_id: str) -> Optional[str]`: Fetches and returns the transcript.
    *   These services will be injectable dependencies.

**D. File Storage & Serving Service (`file_service.py`):**

1.  **Local Storage:**
    *   Define a base storage path in your configuration (e.g., `/media/audio`, `/media/thumbnails`).
    *   Service functions:
        *   `async save_audio_file(video_id: str, audio_data: bytes) -> str: ` (returns file path)
        *   `async save_thumbnail(video_id: str, image_url: str) -> str:` (downloads and saves thumbnail, returns local path)
2.  **Serving Files:**
    *   FastAPI's `StaticFiles` can be used to serve directories.
    *   Alternatively, create dedicated streaming endpoints if more control is needed (e.g., for auth on media).
    *   Example: `/media/audio/{video_id}.m4a`, `/media/thumbnails/{video_id}.jpg`.

**E. Podcast XML Generation Service (`podcast_service.py`):**

1.  **Adapt `podgen` Logic:**
    *   Reuse the core logic from your `helpers.py`'s `create_rss` function.
    *   The service method `async generate_podcast_xml(user: User) -> str:` will:
        *   Fetch the user's `Channel` and all their `Episode` data from the database (async query).
        *   Populate `podgen.Podcast` and `podgen.Episode` objects.
            *   Media URLs for episodes will now point to your FastAPI backend's serving endpoint (e.g., `https://yourdomain.com/media/audio/{episode.video_id}.m4a`).
            *   Channel image URL will point to the backend-served image.
        *   Return the XML string (`p.rss_str()`).
2.  This service will be used by an API endpoint to serve the feed.

**F. Business Logic Services / Use Cases:**

1.  **`AuthService` / `UserService` (`user_service.py`):**
    *   `async register_user(user_data: UserCreateSchema) -> UserResponseSchema`: Handles user creation, password hashing, default channel creation.
    *   `async login_user(form_data: OAuth2PasswordRequestForm) -> TokenSchema`: Handles login, JWT generation.
    *   `async get_current_user(token: str = Depends(oauth2_scheme)) -> User`: Authentication dependency.
    *   `async update_channel_info(user: User, channel_data: ChannelUpdateSchema) -> ChannelResponseSchema`: Updates channel details. Also re-generates the podcast XML or clears a cache if you implement caching for the XML.
    *   `async update_channel_image(user: User, image_file: UploadFile) -> ChannelResponseSchema`: Saves new image, updates `Channel.image_url`.
2.  **`EpisodeProcessingService` (`episode_service.py`):**
    *   `async submit_new_episode_task(youtube_url: str, user: User) -> TaskStatusSchema`:
        *   Validates URL.
        *   Creates an initial `Episode` record in DB with "processing" status (or a separate task tracking table).
        *   Launches a background task (FastAPI's `BackgroundTasks`) to do the actual work:
            *   Call `youtube_service.get_video_info`.
            *   Call `youtube_service.download_audio` (or get stream and save via `file_service`).
            *   Call `file_service.save_thumbnail`.
            *   Call `transcript_service.get_transcript`.
            *   Update the `Episode` record in the DB with all details, file paths, and "completed" status.
        *   Returns an immediate response with a task ID or episode ID for status polling.
    *   `async get_episode_processing_status(task_id: str_or_episode_id: int) -> TaskStatusSchema`.
    *   `async delete_episode(episode_id: int, user: User)`: Deletes episode record and associated local files.

**G. API Endpoints (FastAPI Routers):**

*   **Auth Router (`/auth`):**
    *   `POST /token` (Login)
    *   `POST /register`
*   **Users Router (`/users`):**
    *   `GET /me`
    *   `PUT /me` (Update profile)
    *   `POST /me/channel` (Update channel info)
    *   `POST /me/channel/image` (Upload channel image)
*   **Episodes Router (`/episodes`):**
    *   `POST /`: Submit new YouTube URL (triggers background processing). Returns task/episode ID.
    *   `GET /{episode_id}/status`: Poll for processing status.
    *   `GET /`: List episodes for the current user's channel.
    *   `DELETE /{episode_id}`: Delete an episode.
*   **Podcast Feed Router (`/podcasts`):**
    *   `GET /{user_id_or_username}/feed.xml`: Generates and returns the podcast XML. This endpoint must be publicly accessible.
*   **Media Serving Router (`/media` - or use `StaticFiles`):**
    *   `GET /audio/{video_id}.m4a`
    *   `GET /thumbnails/{video_id}.jpg`
    *   `GET /channel_logos/{user_id_or_username}.jpg`

**III. Frontend Refactoring (Next.js v15 with App Router, React 19)**

**A. Project Setup:**
    *   `create-next-app` with TypeScript.

**B. API Client Service:**
    *   Create a dedicated module (`lib/apiClient.ts` or similar) to handle all communication with your FastAPI backend. Use `fetch` or a lightweight library like `axios` or `ky`.
    *   Include helper functions for attaching JWT auth headers.

**C. UI Components & Pages (App Router):**
    *   **Layouts:** Root layout, authenticated user layout.
    *   **Pages (Server Components for data fetching, Client Components for interactivity):**
        *   `/`: Marketing/Landing page.
        *   `/login`, `/register`.
        *   `/dashboard` (replaces `/channel`): Main view for logged-in user, lists episodes.
        *   `/dashboard/add-episode`: Form to submit YouTube URL.
        *   `/dashboard/settings/profile`: Update user profile.
        *   `/dashboard/settings/channel`: Update channel details (name, description, etc., upload logo).
        *   Static pages: `/contact`, `/privacy`, etc.
    *   **Reusable Components:** Episode cards, forms, modals, navigation.

**D. Enhanced Video Processing UX:**
1.  **Submission:** User submits YouTube URL on `/dashboard/add-episode`.
2.  **Initial Request:** Frontend calls `POST /api/v1/episodes` on FastAPI.
3.  **Immediate Feedback:**
    *   FastAPI returns a task ID or the new (still processing) episode's ID.
    *   Frontend updates UI to show "Episode submitted, processing..."
4.  **Status Updates (Choose one):**
    *   **Polling:** Frontend periodically calls `GET /api/v1/episodes/{id}/status` every few seconds. Update UI based on status (`processing`, `downloading_audio`, `extracting_transcript`, `completed`, `failed`).
    *   **Server-Sent Events (SSE):** FastAPI can push status updates to the client over an SSE connection. More real-time but slightly more complex to set up.
    *   **WebSockets:** Most complex, but offers bidirectional communication if needed for other features. Probably overkill for just status updates.
5.  **Completion:** When status is "completed," update UI to show the episode as available, perhaps with a notification.

**E. Podcast Feed:**
    *   The Next.js app doesn't generate or host the XML. It will simply link to the FastAPI endpoint (e.g., in the user's channel settings page: "Your feed URL: `https://yourdomain.com/api/v1/podcasts/{user.id}/feed.xml`").

**F. Authentication:**
    *   Use a library like `next-auth` for handling client-side sessions if you need social logins or more complex session management. For JWT from your FastAPI backend, you can manage it manually:
        *   Store JWT in `httpOnly` cookies (more secure) or local storage.
        *   Use React Context or a state management library (Zustand, Jotai) to manage auth state.
        *   Protect routes/pages using middleware or higher-order components.

**IV. Key Architectural Changes & Benefits**

*   **No More GitHub for Feeds:** The FastAPI backend serves the XML directly. This simplifies the architecture by removing a third-party dependency for a core function and gives you more control.
*   **Improved Background Processing:** FastAPI's `BackgroundTasks` and async nature are perfect for handling long-running YouTube downloads and processing without blocking the server or user.
*   **Better UX:** The frontend can provide much richer, real-time (or near real-time) feedback to the user about the status of their video processing.
*   **Modularity & Testability:**
    *   FastAPI services will be smaller, focused, and easier to test in isolation (using dependency injection for mocking).
    *   Clear separation between API layer (routers), business logic (services), and data access.
*   **Scalability:** While SQLite has limits, an async FastAPI application is generally more scalable under I/O load than a synchronous Flask one. If you ever outgrow SQLite, the decoupled service architecture makes it easier to swap out the database layer.
*   **Developer Experience:** Modern tools like Next.js and FastAPI generally offer a better DX with features like hot reloading, strong typing (TypeScript, Python type hints + Pydantic), and active communities.

**V. Migration Steps & Considerations**

1.  **Design Phase:**
    *   Finalize API contract (endpoints, schemas).
    *   Sketch out UI/UX for the new processing flow.
    *   Choose your YouTube/transcript libraries.
2.  **Backend First (Iterative):**
    *   Set up FastAPI project, DB, core auth.
    *   Implement `User` and `Channel` models and CRUD.
    *   Implement the `YouTubeService` and `TranscriptService`.
    *   Implement the `EpisodeProcessingService` with background tasks.
    *   Implement the `PodcastService` and the XML feed endpoint.
    *   Write API tests.
3.  **Frontend Next (Iterative):**
    *   Set up Next.js project.
    *   Implement auth pages (login, register) and API client.
    *   Build out the core dashboard, episode submission, and status update UI.
    *   Implement channel/profile settings.
4.  **Data Migration (If keeping existing data):**
    *   Write a script to export data from your old SQLite DB (Flask app) and import it into the new SQLite DB structure (FastAPI app). Consider any schema changes.
5.  **Deployment:**
    *   Dockerize both FastAPI and Next.js applications.
    *   Configure Nginx Proxy Manager (or similar) for SSL and routing.

This is a significant undertaking, but by breaking it down and focusing on a service-oriented approach in the backend and a component-based approach in the frontend, you can achieve a much more robust and modern application. Remember to iterate and test frequently!
