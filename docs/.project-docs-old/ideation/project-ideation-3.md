# Project Ideation 3

## Prompt:

After this complete analysis, and before creating an actual implementation plan, let's clarify some aspects:

- i would like your recommendation on which ORM/Driver to use: sqlalchemy vs sqlmodel with pros and cons. SQLmodel is more modern, do you have enough knowledge to recommend it over SQLalchemy ?
- I think we should use yt-dlp as the library to use for extracting metadata and audio files from youtube videos.
- I want to give youtube-transcript-api a chance and try its implementation before commiting to use an external and paid service like SUPADATA.AI
-  Let's use FastAPI's StaticFiles to serve directories, there is no need to provide more fine-grained auth control on file level, only on api
- We also don't need for libraries like next-auth for social logins, we only need to allow secure user/password for users since the app will be hosted in a homelab environment, it's not intended to be a SaaS app.
- I preffer to take advantage of Nextjs capabilities to use Server Side Events (SSE) instead of using polling from the frontend. No websockets.
- We will take advantage of SQLite async since we don't expect the app to serve thousands of users, just a few, and i don't think it's a limination. However, as you said, our new modular and decoupled approach will allow us to easily change it for something better.
- We also need to create the marketing pages using a modern style with use of nice and smooth animations 


## Response:

---

# Implementation Plan

Okay, here are the detailed implementation plans for the FastAPI backend and the Next.js frontend. These plans are designed to be followed by an AI assistant for implementation, breaking down the work into manageable phases and tasks.

## FastAPI Backend Implementation Plan

**Overall Goal:** Create a robust, asynchronous FastAPI backend to manage users, podcast channels, YouTube video processing (metadata, audio, transcripts), and serve podcast XML feeds.

**Core Technologies:** FastAPI, SQLModel (with async SQLite), `yt-dlp`, `youtube-transcript-api`, Pydantic, Alembic.

---

**Phase 0: Project Setup & Core Infrastructure**

1.  **Task 0.1: Initialize Python Project**
    *   Use Poetry (or PDM) to initialize a new Python project.
    *   Add initial dependencies: `fastapi`, `uvicorn[standard]`, `sqlmodel`, `alembic`, `python-dotenv`, `aiosqlite`.
2.  **Task 0.2: Basic FastAPI Application Structure**
    *   Create `main.py` with a basic FastAPI app instance.
    *   Set up a `core` directory for configuration (`core/config.py`).
    *   Set up an `app` directory with subdirectories: `models`, `schemas`, `services`, `api` (for routers), `db`.
3.  **Task 0.3: Configuration Management**
    *   In `core/config.py`, create a Pydantic `Settings` class (inheriting from `BaseSettings`) to load environment variables (e.g., `DATABASE_URL`, `SECRET_KEY`, `TOKEN_EXPIRATION_SECONDS`, `MEDIA_STORAGE_PATH`).
    *   Create a `.env.example` file.
4.  **Task 0.4: Database Setup (SQLModel & Async SQLite)**
    *   In `db/session.py`:
        *   Define the async database engine using `create_async_engine` with `aiosqlite`.
        *   Implement an async session dependency (`get_async_session`) for FastAPI.
        *   Function `create_db_and_tables` to initialize tables (for early dev, migrations will handle later).
    *   In `main.py`, call `create_db_and_tables` on startup (for initial development).
5.  **Task 0.5: Alembic Integration for Migrations**
    *   Initialize Alembic: `alembic init alembic`.
    *   Configure `alembic/env.py` for async SQLite and SQLModel:
        *   Set `target_metadata` to `SQLModel.metadata`.
        *   Use async SQLAlchemy URL.
    *   Create an initial migration.

---

**Phase 1: Authentication & User Management**

1.  **Task 1.1: User Model**
    *   In `models/user.py`, define the `User` SQLModel class: `id`, `name` (unique), `email` (unique), `hashed_password`, `is_admin` (default False), `date_created`, `date_modified`. Include relationship to `Channel` (one-to-one, define later).
2.  **Task 1.2: User Schemas**
    *   In `schemas/user.py`, define Pydantic schemas:
        *   `UserCreate`: for registration (name, email, password).
        *   `UserRead`: for returning user data (id, name, email, is_admin).
        *   `UserUpdate`: for updating profile (name, email - optional).
3.  **Task 1.3: Password Hashing Utilities**
    *   In `core/security.py`:
        *   `hash_password(password: str) -> str`
        *   `verify_password(plain_password: str, hashed_password: str) -> bool`
4.  **Task 1.4: JWT Utilities**
    *   In `core/security.py` (or a new `auth.py`):
        *   `create_access_token(data: dict, expires_delta: timedelta | None = None) -> str`
        *   `verify_access_token(token: str) -> dict | None` (decodes token, handles expiration/errors).
        *   `oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")`.
5.  **Task 1.5: Authentication Service (`services/auth_service.py`)**
    *   `async register_user(db: AsyncSession, user_create: UserCreate) -> User`: Hashes password, creates `User`, creates default `Channel` (stub for now).
    *   `async authenticate_user(db: AsyncSession, name: str, password: str) -> User | None`: Verifies user.
    *   `async get_current_user(db: AsyncSession, token: str = Depends(oauth2_scheme)) -> User`: Decodes token, fetches user.
    *   `async get_current_active_user(...)`: Add checks if user is active if needed.
6.  **Task 1.6: User Service (`services/user_service.py`)**
    *   `async get_user_by_name(db: AsyncSession, name: str) -> User | None`
    *   `async get_user_by_email(db: AsyncSession, email: str) -> User | None`
    *   `async update_user_profile(db: AsyncSession, user: User, user_update: UserUpdate) -> User`
7.  **Task 1.7: Authentication API Router (`api/v1/auth.py`)**
    *   `POST /token` (Login): Takes `OAuth2PasswordRequestForm`, uses `authenticate_user`, returns JWT.
    *   `POST /register`: Uses `register_user`, returns `UserRead`.
8.  **Task 1.8: User API Router (`api/v1/users.py`)**
    *   `GET /me`: Uses `get_current_user`, returns `UserRead`.
    *   `PUT /me`: Uses `get_current_user`, `update_user_profile`, returns `UserRead`.

---

**Phase 2: Channel Management**

1.  **Task 2.1: Channel Model**
    *   In `models/channel.py`, define the `Channel` SQLModel class: `id`, `user_id` (FK to `User.id`, unique), `name`, `description`, `website`, `explicit` (bool), `image_url` (str, path to local file), `copyright`, `language`, `category`, `authors`, `authors_email`, `owner`, `owner_email`, `date_created`, `date_modified`.
    *   Define relationship to `User` and `Episode` (one-to-many, define `Episode` later).
    *   Update `User` model with `channel: "Channel" = Relationship(back_populates="user")`.
2.  **Task 2.2: Channel Schemas**
    *   In `schemas/channel.py`:
        *   `ChannelCreate`: (not directly used by API if created on user reg).
        *   `ChannelRead`: for returning channel data.
        *   `ChannelUpdate`: for updating channel info (all fields optional).
3.  **Task 2.3: File Service (`services/file_service.py`) - Initial for Logos**
    *   `async save_uploaded_file(upload_file: UploadFile, destination_dir: str, filename_prefix: str) -> str`: Saves file, returns relative path. Needs `python-multipart`.
    *   `async delete_file(file_path: str)`: Deletes a file.
4.  **Task 2.4: Channel Service (`services/channel_service.py`)**
    *   `async create_default_channel(db: AsyncSession, user: User) -> Channel`: Creates and links a default channel. Called during user registration.
    *   `async get_channel_by_user_id(db: AsyncSession, user_id: int) -> Channel | None`
    *   `async update_channel_info(db: AsyncSession, channel: Channel, channel_update: ChannelUpdate) -> Channel`
    *   `async update_channel_image(db: AsyncSession, channel: Channel, image_file: UploadFile, file_service: FileService) -> Channel`: Uses `file_service` to save new image, updates `image_url`, deletes old image.
5.  **Task 2.5: Channel API Router (`api/v1/channels.py` or extend `users.py`)**
    *   `GET /me/channel`: Gets current user's channel.
    *   `PUT /me/channel`: Updates current user's channel info.
    *   `POST /me/channel/image`: Uploads/updates channel image.

---

**Phase 3: YouTube & Transcript Services Integration**

1.  **Task 3.1: `yt-dlp` Integration Service (`services/youtube_dlp_service.py`)**
    *   Dependencies: (none directly, uses subprocess).
    *   `async get_video_metadata(youtube_url: str) -> dict`:
        *   Uses `asyncio.create_subprocess_exec` to run `yt-dlp --dump-json {youtube_url}`.
        *   Parses JSON output to extract: `video_id`, `title`, `description`, `thumbnail_url` (original), `duration` (seconds), `upload_date`, `uploader` (author), `tags` (keywords).
        *   Return a structured dictionary or Pydantic schema.
    *   `async download_audio(youtube_url: str, output_dir: str, filename_stem: str) -> tuple[str, int]`:
        *   Uses `asyncio.create_subprocess_exec` to run `yt-dlp -x --audio-format m4a -o "{output_dir}/{filename_stem}.%(ext)s" {youtube_url}`.
        *   Determines final filename.
        *   Gets file size.
        *   Returns `(audio_file_path, file_size)`.
2.  **Task 3.2: Transcript Service (`services/transcript_service.py`)**
    *   Dependencies: `youtube-transcript-api`.
    *   `async get_transcript_for_video(video_id: str) -> str | None`:
        *   Uses `YouTubeTranscriptApi.get_transcript(video_id)` asynchronously (ensure library supports or wrap in `run_in_executor`).
        *   Concatenates transcript parts into a single string.
        *   Handles errors (e.g., transcript disabled, no transcript).
3.  **Task 3.3: Schemas for External Data**
    *   In `schemas/external.py` (or similar):
        *   `VideoMetadataYTDLP(BaseModel)`: Pydantic schema for the structured output of `get_video_metadata`.

---

**Phase 4: Episode Processing & Management**

1.  **Task 4.1: Episode Model**
    *   In `models/episode.py`, define `Episode` SQLModel: `id`, `channel_id` (FK to `Channel.id`), `youtube_url`, `video_id`, `title`, `description`, `subtitle` (optional), `summary` (optional, can be description), `author`, `original_thumbnail_url`, `saved_thumbnail_path` (local), `published_at` (datetime from YouTube), `keywords` (list of str, or JSON string), `duration_seconds`, `audio_file_path` (local), `audio_file_size_bytes`, `is_downloaded` (bool), `transcript` (TEXT, nullable), `processing_status` (str: e.g., "pending", "processing", "completed", "failed"), `error_message` (str, nullable), `date_created`, `date_modified`.
    *   Update `Channel` model with `episodes: list["Episode"] = Relationship(back_populates="channel")`.
2.  **Task 4.2: Episode Schemas**
    *   In `schemas/episode.py`:
        *   `EpisodeCreatePayload`: `youtube_url: str`.
        *   `EpisodeRead`: Full episode details for API responses.
        *   `EpisodeProcessingStatus`: `id`, `processing_status`, `error_message`.
3.  **Task 4.3: File Service Extensions (in `services/file_service.py`)**
    *   `async download_and_save_thumbnail(thumbnail_url: str, destination_dir: str, filename_prefix: str) -> str`: Downloads image from URL, saves it, returns relative path. Uses `httpx` for async HTTP GET.
4.  **Task 4.4: SSE Service (`services/sse_service.py`) - Basic Structure**
    *   (Will be fleshed out in Phase 6)
    *   `active_connections: dict[str, Any] = {}` (to store user-specific SSE response objects).
    *   `async send_status_update(user_identifier: str, message: dict)`: Pushes message to a user's SSE connection.
5.  **Task 4.5: Episode Service (`services/episode_service.py`)**
    *   `async submit_new_episode(db: AsyncSession, channel: Channel, payload: EpisodeCreatePayload, background_tasks: BackgroundTasks, sse_service: SSEService) -> EpisodeRead`:
        *   Validate YouTube URL format (basic regex).
        *   Check for existing episode with same `video_id` for that channel.
        *   Create initial `Episode` record with `processing_status="pending"`, `youtube_url`.
        *   Add background task: `process_episode_task(episode_id, channel.user_id, sse_service_ref)`.
        *   Return initial `EpisodeRead`.
    *   `async process_episode_task(episode_id: int, user_id_for_sse: int, sse_service: SSEService)`: (This is the background task function)
        *   Get `db` session. Get `Episode` by `episode_id`.
        *   Update `processing_status="processing_metadata"`. `await sse_service.send_status_update(...)`.
        *   Call `youtube_dlp_service.get_video_metadata`. Handle errors.
        *   Update `processing_status="downloading_thumbnail"`. `await sse_service.send_status_update(...)`.
        *   Call `file_service.download_and_save_thumbnail`. Handle errors.
        *   Update `processing_status="downloading_audio"`. `await sse_service.send_status_update(...)`.
        *   Call `youtube_dlp_service.download_audio`. Handle errors.
        *   Update `processing_status="fetching_transcript"`. `await sse_service.send_status_update(...)`.
        *   Call `transcript_service.get_transcript_for_video`. Handle errors.
        *   Populate all `Episode` fields from results. Set `is_downloaded=True`, `processing_status="completed"`.
        *   On any major error, set `processing_status="failed"`, `error_message`.
        *   Save `Episode` to DB.
        *   `await sse_service.send_status_update(...)` with final status.
    *   `async get_episode(db: AsyncSession, episode_id: int, channel_id: int) -> Episode | None`: (Ensures user owns episode).
    *   `async list_episodes_for_channel(db: AsyncSession, channel_id: int) -> list[Episode]`
    *   `async delete_episode(db: AsyncSession, episode: Episode, file_service: FileService)`: Deletes DB record and associated local files (audio, thumbnail).
6.  **Task 4.6: Episode API Router (`api/v1/episodes.py`)**
    *   `POST /`: Submit new YouTube URL. Uses `submit_new_episode`.
    *   `GET /`: List episodes for current user's channel.
    *   `GET /{episode_id}`: Get specific episode details.
    *   `GET /{episode_id}/status`: (May not be needed if SSE is primary, but good for fallback/testing). Returns `EpisodeProcessingStatus`.
    *   `DELETE /{episode_id}`: Delete an episode.

---

**Phase 5: Podcast XML Feed Generation & Serving**

1.  **Task 5.1: Podcast Service (`services/podcast_service.py`)**
    *   Dependencies: `podgen`.
    *   `async generate_podcast_xml_for_user(db: AsyncSession, user_id: int) -> str | None`:
        *   Fetch `User` with their `Channel` and `Episode`s (ensure `Episode`s are ordered, e.g., by `published_at` or `date_created` desc).
        *   If no channel/user, return `None`.
        *   Instantiate `podgen.Podcast`.
        *   Populate podcast-level attributes from `Channel` model (name, description, image_url - make sure it's an absolute URL to your API).
        *   Iterate through `Episode`s:
            *   Create `podgen.Episode`.
            *   Populate attributes: title, summary, media URL (absolute URL to your API's audio serving endpoint), media size, duration (convert `duration_seconds` to `timedelta`), publication date, image (episode thumbnail absolute URL).
        *   Return `podcast.rss_str()`.
2.  **Task 5.2: Podcast Feed API Router (`api/v1/podcasts.py`)**
    *   `GET /{user_identifier}/feed.xml` (use `user_id` or a unique `username`):
        *   Fetch `user_identifier` (e.g., `user_id`).
        *   Call `podcast_service.generate_podcast_xml_for_user`.
        *   If XML string is returned, return `Response(content=xml_string, media_type="application/xml")`.
        *   If `None`, return 404.

---

**Phase 6: Server-Sent Events (SSE) for Real-time Updates**

1.  **Task 6.1: Refine SSE Service (`services/sse_service.py`)**
    *   Modify `active_connections` to store a list or queue of messages if a user has multiple tabs, or manage single connection per user. For simplicity, one connection per `user_identifier` (e.g., user ID) might be enough initially.
    *   The `send_status_update` method should now actually send data via the SSE `Response` object.
2.  **Task 6.2: SSE API Router (`api/v1/sse.py` or extend `episodes.py`)**
    *   `GET /episodes/status-stream`:
        *   Requires authentication (`get_current_user`).
        *   Returns an `EventSourceResponse` (from `sse_starlette.sse`).
        *   Store the `EventSourceResponse` object or a way to yield messages to it in `sse_service.active_connections` keyed by `user.id`.
        *   Periodically send a keep-alive comment or handle client disconnects.
        *   The `episode_service.process_episode_task` will call `sse_service.send_status_update(user_id_for_sse, status_dict)` which then finds the correct `EventSourceResponse` and yields the `json.dumps(status_dict)` to it.

---

**Phase 7: Static File Serving**

1.  **Task 7.1: Configure StaticFiles Middleware**
    *   In `main.py`, mount `StaticFiles` for media directories defined in config (e.g., channel logos, episode thumbnails, episode audio files).
    *   Example: `app.mount("/media", StaticFiles(directory=settings.MEDIA_STORAGE_PATH), name="media")`.
    *   Ensure URLs generated in `PodcastService` and for `Channel.image_url` / `Episode.saved_thumbnail_path` point to these static paths correctly (e.g., `https://yourdomain.com/media/audio/...`).

---

**Phase 8: Testing & Refinement**

1.  **Task 8.1: Unit Tests**
    *   Use `pytest` and `httpx` (for testing FastAPI client).
    *   Write unit tests for services (mocking DB sessions and external calls like `yt-dlp`).
2.  **Task 8.2: Integration Tests**
    *   Test API endpoints, ensuring correct request/response, status codes, and basic data integrity.
3.  **Task 8.3: Error Handling & Logging**
    *   Implement global exception handlers in FastAPI for common errors.
    *   Add structured logging throughout the application.
4.  **Task 8.4: CORS Configuration**
    *   In `main.py`, configure `CORSMiddleware` to allow requests from your Next.js frontend's domain.

---

## Next.js Frontend Implementation Plan

**Overall Goal:** Create a modern, responsive Next.js frontend for users to manage their accounts, channels, submit YouTube videos for podcast conversion, and receive real-time processing updates.

**Core Technologies:** Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS (or preferred CSS solution), SSE.

---

**Phase 0: Project Setup & Core Infrastructure**

1.  **Task 0.1: Initialize Next.js Project**
    *   `npx create-next-app@latest --typescript --eslint --tailwind --app` (adjust based on preferences).
2.  **Task 0.2: Directory Structure**
    *   Establish standard Next.js App Router structure:
        *   `app/`: Main routing, layouts, pages.
        *   `components/`: Reusable UI components.
        *   `lib/`: Utility functions, API client.
        *   `hooks/`: Custom React hooks.
        *   `contexts/`: React context providers.
        *   `styles/`: Global styles.
        *   `public/`: Static assets.
3.  **Task 0.3: Global Styles & Theme**
    *   Set up `styles/globals.css` (or equivalent).
    *   Define a basic theme or color palette if using Tailwind CSS config.
4.  **Task 0.4: API Client (`lib/apiClient.ts`)**
    *   Create a wrapper around `fetch` (or use `axios`).
    *   Functions to handle GET, POST, PUT, DELETE requests to the FastAPI backend.
    *   Base URL from environment variable (`NEXT_PUBLIC_API_URL`).
    *   Function to get and attach JWT from auth context/storage to request headers.

---

**Phase 1: Authentication**

1.  **Task 1.1: Auth Context/Store (`contexts/AuthContext.tsx`)**
    *   React Context to store user object, JWT, loading state, and authentication status.
    *   Functions: `login(credentials)`, `register(data)`, `logout()`. These will use `apiClient`.
    *   Logic to persist/retrieve JWT (e.g., from `httpOnly` cookie if set by backend, or local storage - ensure security considerations).
2.  **Task 1.2: Authentication Pages & Components**
    *   `app/(auth)/login/page.tsx`: Login form component, calls `AuthContext.login`.
    *   `app/(auth)/register/page.tsx`: Registration form component, calls `AuthContext.register`.
    *   Create reusable `Input`, `Button`, `Form` components.
3.  **Task 1.3: Route Protection & Redirects**
    *   Implement client-side redirects based on auth state (e.g., in `AuthContext` or using a custom hook).
    *   Use Next.js Middleware (`middleware.ts`) to protect authenticated routes (e.g., `/dashboard/*`) by checking for JWT cookie/token. Redirect to `/login` if not authenticated.
4.  **Task 1.4: Root Layout Integration**
    *   Wrap `app/layout.tsx`'s children with `AuthProvider`.

---

**Phase 2: Core Layouts & Navigation**

1.  **Task 2.1: Main Authenticated Layout (`app/dashboard/layout.tsx`)**
    *   Includes common UI elements for logged-in users (e.g., sidebar, top navigation bar).
    *   Links to dashboard sections, settings, logout.
2.  **Task 2.2: Navigation Components**
    *   `components/Sidebar.tsx`
    *   `components/Navbar.tsx`
    *   These components should display links conditionally based on auth state.

---

**Phase 3: User & Channel Settings Pages**

1.  **Task 3.1: Profile Settings Page (`app/dashboard/settings/profile/page.tsx`)**
    *   Form to display and update user's name and email.
    *   Fetches current user data using `apiClient`.
    *   Submits updates using `apiClient`.
2.  **Task 3.2: Channel Settings Page (`app/dashboard/settings/channel/page.tsx`)**
    *   Form to display and update channel metadata (name, description, website, explicit, etc.).
    *   Component to upload/change channel logo:
        *   Uses `<input type="file">`.
        *   Shows image preview.
        *   Submits image file (as `FormData`) via `apiClient`.
    *   Displays the current feed URL (read-only, constructed from user data).
    *   Fetches current channel data, submits updates.

---

**Phase 4: Episode Management - Submission & Display**

1.  **Task 4.1: Episode Submission Form (`app/dashboard/add-episode/page.tsx`)**
    *   Input field for YouTube URL.
    *   Submit button.
    *   On submit, calls `apiClient` to `POST /episodes` endpoint on backend.
2.  **Task 4.2: Dashboard/Episode List Page (`app/dashboard/page.tsx`)**
    *   Fetches list of user's episodes from backend (`GET /episodes`).
    *   Displays episodes using `EpisodeCard` components.
    *   Shows initial status for episodes (e.g., "Processing" if `processing_status` from backend indicates).
3.  **Task 4.3: Episode Card Component (`components/EpisodeCard.tsx`)**
    *   Displays episode title, thumbnail, duration, status.
    *   "Delete" button (calls `apiClient` `DELETE /episodes/{id}`).
    *   UI elements to show processing progress/status (will be updated by SSE).
4.  **Task 4.4: State Management for Episodes**
    *   Use `useState`, `useEffect` or a state manager (Zustand/Jotai) to manage the list of episodes and their statuses.

---

**Phase 5: Real-time Episode Processing UX with SSE**

1.  **Task 5.1: SSE Hook/Utility (`hooks/useEpisodeStatusSSE.ts`)**
    *   Takes user identifier or token to potentially pass to SSE connection if needed (or relies on cookie auth for the SSE endpoint).
    *   Establishes an `EventSource` connection to the FastAPI SSE endpoint (`/api/v1/episodes/status-stream`).
    *   Listens for `message` events. Parses JSON data.
    *   Updates a shared state (e.g., in a Zustand store or via a callback) with the new episode status.
    *   Handles connection errors and retries.
    *   Cleans up `EventSource` on component unmount.
2.  **Task 5.2: Integrate SSE Updates into UI**
    *   In `app/dashboard/page.tsx` (or wherever episodes are listed/managed), use the `useEpisodeStatusSSE` hook.
    *   When episode status updates are received, find the corresponding episode in the local state and update its status.
    *   `EpisodeCard.tsx` should reactively display the updated status (e.g., "Downloading audio...", "Completed", "Error: ...").
3.  **Task 5.3: Visual Feedback**
    *   Implement progress bars or spinners for episodes in "processing" states.
    *   Display error messages clearly if `processing_status` is "failed".

---

**Phase 6: Marketing & Static Pages**

1.  **Task 6.1: Create Static Pages**
    *   `app/page.tsx` (Homepage)
    *   `app/about/page.tsx`
    *   `app/contact/page.tsx`
    *   `app/privacy/page.tsx`
    *   `app/terms/page.tsx`
2.  **Task 6.2: Modern Styling and Animations**
    *   Use Tailwind CSS (or chosen solution) to style these pages with a modern look and feel.
    *   Implement subtle, smooth animations/transitions (e.g., on scroll, hover effects) using CSS or a library like Framer Motion if complex animations are desired.
    *   Ensure pages are responsive.

---

**Phase 7: UI/UX Refinements & Testing**

1.  **Task 7.1: Responsive Design**
    *   Thoroughly test all pages and components on various screen sizes (desktop, tablet, mobile).
2.  **Task 7.2: Accessibility (a11y)**
    *   Review for basic accessibility: semantic HTML, keyboard navigation, ARIA attributes where necessary, color contrast.
3.  **Task 7.3: Error Handling**
    *   Display user-friendly error messages from API responses (e.g., using a toast notification system).
    *   Handle network errors gracefully.
4.  **Task 7.4: Forms Enhancements**
    *   Implement client-side form validation (e.g., using `react-hook-form` or Zod) in addition to backend validation.
5.  **Task 7.5: End-to-End (E2E) Testing (Optional but Recommended)**
    *   Set up Playwright or Cypress.
    *   Create E2E tests for critical user flows: registration, login, submitting an episode, viewing status updates, deleting an episode.

This comprehensive plan should guide the AI assistant effectively. Remember that some tasks within phases might be parallelizable.
