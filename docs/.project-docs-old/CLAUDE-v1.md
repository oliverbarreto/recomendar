# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LabCastARR is a full-stack web application (a podcast channel for your Homelab) that converts YouTube videos to podcast episodes and creates podcast RSS feeds (XML compatible with iTunes and Spotify). 

It's built as a monorepo with separate frontend and backend services.

**Technology Stack:**
- **Frontend:** In directory `frontend/`: Next.js 15 + React + TypeScript + TailwindCSS v4 + ShadCN UI + Node 20+
- **Backend:** In directory `backend/`: FastAPI + Python 3.12+, SQLite (Async - aiosqlite), SQLAlchemy + Alembic, + uv (Python package mannager). 
IMPORTANT: sqlite data in `backend/data` directory.
IMPORTANT: The old monolithic flask app is in directory`web/` just for reference, DO NOT USE.
- **Media Processing**: PyTubeFix for YouTube audio extraction. Media files will be stored in directory `backend/media/channel_*/`.
- **RSS Generation**: PodGen library for podcast RSS feed creation. RSS feed will be stored in directory `backend/feeds/channel_*/`.
- **Deployment:** Docker + Docker Compose 

## Key Features and Workflows

**Key Workflows**: 
- Add a new episode: provide a YouTube URL in the frontend → Metadata extraction → Audio processing → RSS feed generation and distribution in the backend.
- List all episodes in a channel and full management capabilities for organizing, searching, and distributing podcast content across multiple channels.
- Serve RSS feeds for podcasting with iTunes compliance.
- Serve media files for podcast streaming.

## Development Commands

### Local Backend Development
```bash
cd backend #(always start here)
uv sync                                  # Install/sync dependencies
uv run fastapi dev app/main.py           # Development server with hot reload
uv run fastapi run app/main.py           # Production server
uv run alembic revision --autogenerate   # Generate database migrations
uv run alembic upgrade head              # Apply database migrations
```

**Note**: Local development uses the same configuration as Docker development via symlink:
- `backend/.env.local` → `.env.development` (symlinked for consistency)

### Local Frontend Development
```bash
cd frontend
npm install                              # Install dependencies
npm run dev                              # Development server with hot reload
npm run build                            # Build for production
npm run start                            # Start production server
npm run lint                             # Run ESLint
```

### Docker Development (Recommended)

We have multiple Docker Compose files:

  - docker-compose.yml (base configuration)
  - docker-compose.prod.yml (production overrides)
  - docker-compose.dev.yml (development overrides)

For Production, we should run: `docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d`. Which combines:

  1. Base config (docker-compose.yml)
  2. Production overrides (docker-compose.prod.yml) - which includes our fixes:
    - env_file: .env.production
    - Production environment variables
    - Production-specific settings
  
Running `docker-compose.prod.yml`:
  - ✅ Added env_file: .env.production
  - ✅ Added NEXT_PUBLIC_API_KEY environment variable
  - ✅ Production-specific configurations

Running `docker-compose.yml` only:
  - ❌ Uses default .env file (development settings)
  - ❌ Missing NEXT_PUBLIC_API_KEY
  - ❌ Wrong environment variables
  - ❌ IMPORTANT: Do not run for production: `docker-compose up --build -d`


### Docker Compose Commands
```bash
# Development with hot reload
docker compose -f docker-compose.dev.yml up --build

# Production mode: you should run:
docker compose -f docker-compose.prod.yml up --build -d

# IMPORTANT: Testing in production: Docker production container will not see code changes in real-time. Since we're running in production mode with a built Docker image, the changes won't take effect until the container is rebuilt. WE HAVE TO RESTART AND REBUILD DOCKER CONTAINERS TO PICK UP THE CHANGES.

# Stop services (development)
docker compose -f docker-compose.dev.yml down

# Stop services (production)
docker compose -f docker-compose.prod.yml down
```


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
- Database URL: `sqlite:///./data/labcastarr.db` (stored in `backend/data/`)
- Alembic for migrations: `cd backend && uv run alembic upgrade head`
- Fresh database setup: Delete database files and run `uv run alembic upgrade head` or use SQLAlchemy's `create_all()`

### Key Dependencies
- **Backend:** fastapi, sqlalchemy, alembic, yt-dlp, pydantic-settings, aiosqlite, uvicorn, python-multipart
- **Frontend:** next, @tanstack/react-query, shadcn, radix-ui, tailwindcss v4, react-hook-form, zod, sonner

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

Key environment variables in `backend/.env`:
- `DATABASE_URL=sqlite:///./data/labcastarr.db` - Database path (must be in data/ directory)
- `API_KEY_SECRET=dev-secret-key-change-in-production` - API authentication key
- `MEDIA_PATH=./media` - Path for downloaded audio files
- `FEEDS_PATH=./feeds` - Path for RSS feed files
- `CORS_ORIGINS=["http://localhost:3000"]` - Frontend CORS origin

Frontend environment variables:
- `NEXT_PUBLIC_API_URL=http://localhost:8000` - Backend API URL for client-side requests

## Access Points - Development
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Access Points - Production (Docker)
- Frontend: https://labcastarr.oliverbarreto.com
- RSS Feed: https://labcastarr-api.oliverbarreto.com/v1/feeds/1/feed.xml
- Media Files: https://labcastarr-api.oliverbarreto.com/v1/media/episodes/{id}/audio
- RSS feed URL for Apple Podcasts submission: https://labcastarr-api.oliverbarreto.com/v1/feeds/1/feed.xml


## Common Issues & Solutions

### Database Path Issues
- Database must be located in `backend/data/labcastarr.db`, not in backend root
- If database appears in wrong location, check `DATABASE_URL` environment variable
- For fresh start: `rm -f backend/labcastarr.db* && rm -f backend/data/labcastarr.db*`

### API Integration Issues
- Ensure TypeScript interfaces use snake_case to match backend response format
- All API calls require `X-API-Key` header
- Frontend port conflicts: Next.js may use alternate ports (3001, 3002) if 3000 is taken

### YouTube Integration
- Video analysis endpoint: `POST /v1/episodes/analyze` with `{"video_url": "..."}`
- Episode creation: `POST /v1/episodes` with `{"channel_id": 1, "video_url": "...", "tags": []}`
- Progress polling: `GET /v1/episodes/{id}/progress` for download status