# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LabCastARR is a full-stack web application (a podcast channel for your Homelab) that creates podcast episodes from YouTube videos or uploaded audio files, and generates podcast RSS feeds (XML compatible with iTunes and Spotify).

It's built as a monorepo with separate frontend and backend services.

**Technology Stack:**

- **Frontend:** In directory `frontend/`: Next.js 15 + React + TypeScript + TailwindCSS v4 + ShadCN UI + Node 20+
- **Backend:** In directory `backend/`: FastAPI + Python 3.12+, SQLite (Async - aiosqlite), SQLAlchemy + Alembic, + uv (Python package mannager).
  IMPORTANT: sqlite data in `backend/data` directory.
  IMPORTANT: The old monolithic flask app is in directory`web/` just for reference, DO NOT USE.
- **Celery:** We also use Celery for background tasks of the feature that allows the user to follow YouTube channels to search/monitor for new episodes (downloads metadata, not media files) and then allow the user to create episodes in the podcast channel from these YouTube videos.
- **Media Processing**: PyTubeFix for YouTube audio extraction, FFmpeg for audio format conversion. Media files will be stored in directory `backend/media/channel_*/`.
- **File Upload**: Supports MP3, M4A, WAV, OGG, FLAC audio files (max 500MB). Automatic conversion to podcast-compatible formats using FFmpeg.
- **RSS Generation**: PodGen library for podcast RSS feed creation. RSS feed will be stored in directory `backend/feeds/channel_*/`.
- **Deployment:** Docker + Docker Compose (see `DEPLOYMENT.md` for detailed instructions)

## Key Features and Workflows

**Key Workflows**:

- **Add episode from YouTube**: Provide a YouTube URL in the frontend (Add New Episode) → Metadata extraction → Audio processing → Episode creation → RSS feed generation and distribution in the backend.
- **Add episode from file upload**: Upload audio file (MP3, M4A, WAV, OGG, FLAC) using drag-and-drop or file picker → User fills in episode details (title, description, tags, publication date) → Client-side validation → Streaming upload → Server-side validation → Format conversion (if needed using FFmpeg) → Podcast Episode creation → RSS feed update.

  - **Supported formats for file upload:**
    - ✅ **MP3** - Stored as-is (no conversion)
    - ✅ **M4A** - Stored as-is (no conversion)
    - ✅ **WAV** - Converted to MP3
    - ✅ **OGG** - Converted to MP3
    - ✅ **FLAC** - Converted to MP3
  - **File Upload Limits:**
    - Maximum file size: 500MB
    - Automatic format conversion for podcast compatibility
    - Client-side validation for faster feedback
    - Streaming upload for large files

- **Episode Management**: List all episodes in a channel with full management capabilities for organizing, searching, and distributing podcast content across multiple channels.
- **RSS Feed Distribution**: Serve iTunes and Spotify compatible RSS feeds for podcasting.
- **Media Streaming**: Serve media files for podcast streaming.
- **Follow Channel and Discover Videos**: Allow the user to follow YouTube channels in `/subscriptions/channels` page → User triggers video discovery using one of two methods:
  - **RSS Feed Method** (Fast ~5-10s): Uses YouTube RSS feeds to find latest 10-15 videos
  - **yt-dlp Full Method** (Slow ~30-60s): Uses yt-dlp to comprehensively scan latest 50 videos
    → Celery task executes chosen discovery method → New videos displayed in `/subscriptions/videos` page → User can create podcast episodes from discovered videos. Both methods support auto-approve workflow for automatic episode creation. See `docs/documentation/TECHNICAL-ANALYSIS-FEATURE-follow-channels-architecture.md` for detailed architecture.
- **Settings**: Allow the user to configure the podcast channel (title, description, tags, publication date, etc.) and the RSS feed (title, description, tags, publication date, etc.).

## Development Commands

** IMPORTANT NOTE**: Local development uses environment-specific configurations for backend and frontend:

- Development: Uses `.env.development` or `backend/.env.local` (symlinked for consistency)
- Production: Uses `.env.production` with production database and settings

### Local Backend Development

```bash
cd backend #(always start here)
uv sync                                  # Install/sync dependencies
uv run fastapi dev app/main.py           # Development server with hot reload
uv run fastapi run app/main.py           # Production server
uv run alembic revision --autogenerate   # Generate database migrations
uv run alembic upgrade head              # Apply database migrations
```

### Local Frontend Development

```bash
cd frontend
npm install                              # Install dependencies
npm run dev                              # Development server with hot reload
npm run build                            # Build for production
npm run start                            # Start production server
npm run lint                             # Run ESLint
```

### Docker Compose Development (Recommended)

We have multiple Docker Compose configurations:

- `docker-compose.dev.yml` - Development with hot reload and development database
- `docker-compose.prod.yml` - Production with optimized builds and production database
- `docker-compose.pre.yml` - Pre-Production with same config than production but with different domains
- See `docs/documentation/DEPLOYMENT.md` for detailed deployment instructions

### Docker Compose Commands

**IMPORTANT**: Use the `--env-file` flag to specify which environment configuration to load for variable substitution in compose files.

```bash
# Pre-Production mode
docker compose --env-file .env.pre -f docker-compose.pre.yml up --build -d

# Production mode
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d

# Development mode
docker compose --env-file .env.development -f docker-compose.dev.yml up --build

# Stop services
docker compose -f docker-compose.prod.yml down  # or docker-compose.dev.yml
```

**Important Notes**:

- The `--env-file` flag loads environment variables for `${VAR}` substitution in docker-compose.yml
- The `env_file:` directive in docker-compose.yml loads vars into containers at runtime
- Environment variables are loaded at BUILD time for frontend (Next.js requirement via ARG)
- Production containers require rebuild to pick up code changes since they use built Docker images
- **Always specify `--env-file`** to ensure correct environment variables are loaded

**Alternative (Optional - NOT RECOMMENDED)**: For shorter commands, you can use the `setup-env.sh` script to create a `.env` symlink:

```bash
./scripts/setup-env.sh production  # Creates .env → .env.production
docker compose -f docker-compose.prod.yml up --build -d
```

Note: Symlinks may not work on all systems (especially Windows). The `--env-file` flag is the recommended approach.

## Architecture

### Backend Architecture (Clean Architecture/Hexagonal)

The backend follows Clean Architecture principles with clear separation of concerns:

```
backend/app/
├── main.py                              # FastAPI entry point
├── core/                                # Core configuration and shared utilities
│   ├── config.py                       # Application settings with Pydantic
│   └── dependencies.py                 # FastAPI dependency injection
├── domain/                             # Domain layer (business logic)
│   ├── entities/                       # Domain entities
│   ├── repositories/                   # Repository interfaces
│   ├── services/                       # Domain services
│   └── value_objects/                  # Value objects (Email, VideoId, Duration)
├── application/                        # Application layer (use cases)
│   └── services/                       # Application services
├── infrastructure/                     # Infrastructure layer
│   ├── database/                       # Database models and connection
│   ├── repositories/                   # Repository implementations
│   ├── services/                       # External service implementations
│   └── external/                       # Third-party integrations
└── presentation/                       # Presentation layer
    ├── api/                            # API routes and controllers
    └── schemas/                        # Pydantic request/response schemas
```

**Key Architectural Principles:**

- Domain entities are separate from database models
- Repository pattern for data access abstraction
- Dependency injection through FastAPI's DI system
- Clear separation between business logic and infrastructure

### Frontend Architecture

```
frontend/src/
├── app/                                # Next.js App Router pages
├── components/
│   ├── ui/                            # ShadCN UI components
│   ├── shared/                        # Shared utility components
│   ├── features/                      # Feature-specific components
│   ├── layout/                        # Layout components
│   └── providers/                     # React context providers
├── hooks/                             # Custom React hooks
├── lib/                               # Utility functions and API clients
└── types/                             # TypeScript type definitions
```

**Key Frontend Patterns:**

- Uses React Query (@tanstack/react-query) for API state management
- TailwindCSS v4 and ShadCN UI for consistent design system
- Custom hooks for API interactions
- TypeScript with strict mode enabled
- Be careful when calling backend API endpoints from frontend, always use the correct API endpoint and parameters, specially with the trailing slash. Check this before creating the API call.

## Development Guidelines

### Code Style Enforcement

The project uses Cursor rules located in `.cursor/rules/` that enforce:

- Backend: FastAPI best practices, Clean Architecture, async patterns
- Frontend: Functional programming, TypeScript strict mode, ShadCN patterns
- General: No classes unless necessary, descriptive naming, error handling

### API Integration

- Backend API runs on http://localhost:8000 (with docs at /docs)
- Frontend runs on http://localhost:3000
- Frontend API client configuration in `frontend/src/lib/api.ts`
- **IMPORTANT**: Backend uses snake_case field names (e.g., `channel_id`, `video_id`) while frontend TypeScript interfaces should match this format
- API endpoints include YouTube video analysis (`/v1/episodes/analyze`) and episode creation (`/v1/episodes`)
- All API requests require `X-API-Key` header with value from `API_KEY_SECRET` environment variable

### Database

- SQLite database with SQLAlchemy ORM in WAL mode
- **Development**: `sqlite:///./data/labcastarr-dev.db` (stored in `backend/data/`)
- **Production**: `sqlite:///./data/labcastarr.db` (stored in `backend/data/`)
- Environment detection automatically selects appropriate database via `backend/app/core/config.py`
- Alembic for migrations: `cd backend && uv run alembic upgrade head` (`backend/alembic`)
- Fresh database setup: Delete database files and run `uv run alembic upgrade head` or use SQLAlchemy's `create_all()`

### Key Dependencies

- **Backend:** fastapi, sqlalchemy, alembic, yt-dlp, pydantic-settings, aiosqlite, uvicorn, python-multipart, python-magic, mutagen, aiofiles, ffmpeg (system)
- **Frontend:** next, @tanstack/react-query, shadcn, radix-ui, tailwindcss v4, react-hook-form, zod, sonner, react-dropzone

## Testing and Linting

Always run linting after making changes:

```bash
# Frontend linting and type checking
cd frontend && npm run lint
cd frontend && npx tsc --noEmit           # TypeScript type checking

# Backend type checking (if configured)
cd backend && uv run python -m mypy app/
```

## Environment Configuration

### Development Environment (`.env.development`)

**Required Variables**:

- `ENVIRONMENT=development` - Environment identifier
- `DATABASE_URL=sqlite:///./data/labcastarr-dev.db` - Development database
- `API_KEY_SECRET=dev-secret-key-change-in-production` - API authentication key
- `JWT_SECRET_KEY=<your-secret>` - JWT authentication secret
- `CORS_ORIGINS=["http://localhost:3000"]` - Frontend CORS origin
- `BASE_URL=http://localhost:8000` - Backend API URL
- `FRONTEND_URL=http://localhost:3000` - Frontend URL
- `NEXT_PUBLIC_API_URL=http://localhost:8000` - Backend API URL for client-side requests
- `NEXT_PUBLIC_API_KEY=<your-api-key>` - API key for frontend
- `NEXT_PUBLIC_DOMAIN=localhost` - Domain for frontend
- `ALLOWED_HOSTS=["localhost","127.0.0.1","0.0.0.0"]` - Allowed backend hosts

### Production Environment (`.env.production`)

**Required Variables**:

- `ENVIRONMENT=production` - Environment identifier
- `DATABASE_URL=sqlite:///./data/labcastarr.db` - Production database
- `DOMAIN=yourdomain.com` - Production domain configuration
- `BASE_URL=https://api.yourdomain.com` - Production API URL
- `FRONTEND_URL=https://yourdomain.com` - Production frontend URL
- `CORS_ORIGINS=["https://yourdomain.com"]` - Production CORS origins
- `NEXT_PUBLIC_API_URL=https://api.yourdomain.com` - Backend API URL for client-side requests
- `NEXT_PUBLIC_API_KEY=<your-api-key>` - API key for frontend
- `NEXT_PUBLIC_DOMAIN=yourdomain.com` - Domain for frontend
- `ALLOWED_HOSTS=["localhost","127.0.0.1","0.0.0.0","api.yourdomain.com"]` - Allowed backend hosts
- `API_KEY_SECRET=<your-secret>` - API authentication key
- `JWT_SECRET_KEY=<your-secret>` - JWT authentication secret

### Pre-Production Environment (`.env.pre`)

**Required Variables**:

- same variables as production environment, except can be used to test the app in pre-production environment using different domains.
- If we use the same database for production and pre-production, the app won't be able to correctly use the right RSS feed url in Settings panel, since the feed_url is stored in the database and persists from when the channel was created (task-0045-pre-environment-not-working-rss-feed-url.md)

### Common Environment Variables

- `MEDIA_PATH=./media` - Path for downloaded audio files
- `FEEDS_PATH=./feeds` - Path for RSS feed files
- `JWT_SECRET_KEY` - JWT authentication secret
- `API_KEY_SECRET` - API authentication key (use `openssl rand -base64 32` to generate)

## Access Points - Development

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Access Points - Production (Docker)

Configure your production environment URLs via environment variables in `.env.production`:

- Frontend: Set via `FRONTEND_URL`
- Backend API: Set via `BASE_URL` and `NEXT_PUBLIC_API_URL`
- RSS Feed: `{BASE_URL}/v1/feeds/{channel_id}/feed.xml`
- Media Files: `{BASE_URL}/v1/media/episodes/{id}/audio`

## Common Issues & Solutions

### Token Refresh and State Management

**Refresh Strategy**:

- **Automatic token refresh**: Every 48 minutes (80% of 60-min token lifetime) - non-blocking, happens in background
- **Activity-based refresh**: On meaningful user interactions (keypress, scroll, touch) after 5 minutes of inactivity
- **NO window focus refresh**: Removed (was too aggressive, causing state loss and poor UX)

**State Preservation**:

- Token refreshes never unmount components or show blocking spinners
- Multi-step forms and file selections preserved during refresh
- Upload workflows uninterrupted by authentication system
- Only initial auth check shows loading spinner

**Important Note**: Previous versions triggered token refresh on every window focus event (e.g., clicking between DevTools and page), causing form state loss and "Refreshing session..." spinners. This has been fixed - refreshes now happen silently in the background.

### Database Path Issues

- **Development**: Database must be located in `backend/data/labcastarr-dev.db`
- **Production**: Database must be located in `backend/data/labcastarr.db`
- Environment detection automatically selects appropriate database via `backend/app/core/config.py`
- If database appears in wrong location, check `DATABASE_URL` in respective environment file
- For fresh start: `rm -f backend/data/labcastarr*.db*`

### API Integration Issues

- Ensure TypeScript interfaces use snake_case to match backend response format
- All API calls require `X-API-Key` header
- Frontend port conflicts: Next.js may use alternate ports (3001, 3002) if 3000 is taken

### YouTube Integration

- Video analysis endpoint: `POST /v1/episodes/analyze` with `{"video_url": "..."}`
- Episode creation: `POST /v1/episodes` with `{"channel_id": 1, "video_url": "...", "tags": []}`
- Progress polling: `GET /v1/episodes/{id}/progress` for download status

### File Upload Integration

- Upload endpoint: `POST /v1/episodes/upload` with multipart/form-data
- Supported formats: MP3, M4A, WAV, OGG, FLAC (max 500MB)
- **File selection methods**:
  - Drag-and-drop files onto the upload area
  - Click "Browse Files" button to open OS file picker
- Automatic format conversion: WAV, OGG, FLAC → MP3 using FFmpeg
- MP3 and M4A files stored as-is (no conversion)
- Client-side validation: File size, MIME type, audio metadata extraction
- Server-side validation: MIME type verification, file size limits, audio integrity
- Streaming upload: Large files handled efficiently with streaming writes
- Error handling: Comprehensive error codes for file size, format, duplicates, conversion failures
- Event logging: Upload start, completion, conversion events, errors
- Database tracking: `source_type` field distinguishes YouTube vs uploaded episodes

### Docker Compose Environment Issues

**Symptom**: Docker Compose warnings about variables not set (defaulting to blank string)

```
level=warning msg="The \"NEXT_PUBLIC_API_URL\" variable is not set. Defaulting to a blank string."
```

**Cause**: Docker Compose doesn't auto-load `.env.production` or `.env.development` for variable substitution

**Solution**: Always use the `--env-file` flag

```bash
# For production
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d

# For development
docker compose --env-file .env.development -f docker-compose.dev.yml up --build
```

**Understanding Docker Compose Environment Variables**:

- `--env-file` flag: Loads vars for `${VAR}` substitution in docker-compose.yml
- `env_file:` directive: Loads vars into containers at runtime
- Both are needed: `--env-file` for compose file, `env_file:` for container environment
- Frontend NEXT*PUBLIC*\* vars must be available at BUILD time (via ARG in Dockerfile)

### Backend JSON Parsing Errors

**Symptom**: `JSONDecodeError: Expecting value: line 1 column 1 (char 0)` when starting backend
**Cause**: `CORS_ORIGINS` or other JSON array variables are empty strings due to missing `--env-file` flag
**Solution**: Use `--env-file` flag as shown above to ensure all environment variables are loaded correctly

### Docker Development Hot Reload Configuration

**Backend Hot Reload Setup**:

- Uses `backend/Dockerfile.dev` with `uvicorn --reload` flag for automatic code reloading
- Volume mount: `./backend:/app:cached` for host-to-container code sync
- Excluded from volume: `/app/.venv` (virtual environment stays in container)
- Environment: `UV_LINK_MODE=copy` - Suppresses hardlinking warnings on macOS Docker Desktop

**Frontend Hot Reload Setup**:

- Uses `frontend/Dockerfile.dev` with `npm run dev` for Next.js hot reload
- Volume mounts:
  - `./frontend:/app:cached` - Host code sync
  - `/app/node_modules` - Excluded (container-managed dependencies)
  - `/app/.next` - Excluded (container-managed Next.js cache)

**Health Check Configuration**:

- Backend health check start_period: 60 seconds (allows time for database initialization)
- Service dependencies: Celery workers wait for backend to be healthy before starting
- Redis is initialized before backend startup (prevents race conditions)

**CRITICAL: Health Check Endpoint Path**:

- The health check endpoint is at: `/health/` (WITH trailing slash)
- FastAPI router creates the endpoint at `/health/` due to prefix + route configuration
- App configured with `redirect_slashes=False`, so requests to `/health` get 404 error
- Development health check MUST use: `http://localhost:8000/health/` (with trailing slash)
- This is automatically configured correctly in docker-compose.dev.yml
- If health check fails, verify the URL ends with `/health/` and NOT `/health`

**Celery Worker Limitation**:

- Celery workers and beat scheduler DO NOT auto-reload on code changes
- Changes to task files require manual container restart: `docker compose -f docker-compose.dev.yml restart celery-worker-dev celery-beat-dev`
- This is a known limitation of Celery; watch-mode would require additional configuration
- Workaround: Use `docker compose -f docker-compose.dev.yml restart` after modifying task files

**Debugging Development Issues**:

- View backend logs: `docker compose -f docker-compose.dev.yml logs backend-dev -f`
- View frontend logs: `docker compose -f docker-compose.dev.yml logs frontend-dev -f`
- View celery logs: `docker compose -f docker-compose.dev.yml logs celery-worker-dev -f`
- Check service health: `docker compose -f docker-compose.dev.yml ps`
- Force rebuild: `docker compose --env-file .env.development -f docker-compose.dev.yml up --build` (without `-d` to see logs)
