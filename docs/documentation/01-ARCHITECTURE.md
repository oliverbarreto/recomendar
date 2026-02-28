# LabCastARR Architecture Documentation

**Document Version:** 1.0
**Last Updated:** 2026-01-29

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Monorepo Structure](#monorepo-structure)
3. [Backend Architecture](#backend-architecture)
4. [Frontend Architecture](#frontend-architecture)
5. [Data Flow](#data-flow)
6. [Design Patterns](#design-patterns)
7. [Key Architectural Decisions](#key-architectural-decisions)

---

## System Overview

LabCastARR is built as a monorepo containing two main services:

1. **Backend (FastAPI)** - REST API, business logic, data persistence, background tasks
2. **Frontend (Next.js)** - User interface, client-side state management

### High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Next.js 15 Frontend                               │   │
│  │  ┌───────────┐  ┌───────────────┐  ┌─────────────────────────────┐ │   │
│  │  │ App Router│  │ React Query   │  │ ShadCN UI + TailwindCSS v4 │ │   │
│  │  │ (Pages)   │  │ (Data Fetch)  │  │ (Components)                │ │   │
│  │  └───────────┘  └───────────────┘  └─────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTP (REST API)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API LAYER                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    FastAPI Backend                                   │   │
│  │  ┌───────────┐  ┌───────────────┐  ┌───────────────────────────┐   │   │
│  │  │ API Routes│  │ Pydantic      │  │ Authentication (JWT)      │   │   │
│  │  │ (v1)      │  │ Schemas       │  │ + API Key                 │   │   │
│  │  └───────────┘  └───────────────┘  └───────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          APPLICATION LAYER                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                 Application Services (Use Cases)                     │   │
│  │  • EpisodeService      • FollowedChannelService                     │   │
│  │  • ChannelService      • YouTubeVideoService                        │   │
│  │  • TagService          • NotificationService                        │   │
│  │  • SearchService       • CeleryTaskStatusService                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            DOMAIN LAYER                                      │
│  ┌──────────────┐  ┌──────────────────┐  ┌────────────────────────────┐   │
│  │   Entities   │  │ Domain Services  │  │ Repository Interfaces      │   │
│  │  • Episode   │  │ • FeedGeneration │  │ • EpisodeRepository        │   │
│  │  • Channel   │  │ • VideoDiscovery │  │ • ChannelRepository        │   │
│  │  • User      │  │ • YouTubeMetadata│  │ • FollowedChannelRepo      │   │
│  │  • Tag       │  │   Strategy       │  │ • YouTubeVideoRepo         │   │
│  │  • YouTubeVideo│                    │  │                            │   │
│  └──────────────┘  └──────────────────┘  └────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        INFRASTRUCTURE LAYER                                  │
│  ┌────────────────┐  ┌─────────────────┐  ┌──────────────────────────┐    │
│  │  SQLAlchemy    │  │ External        │  │ Celery Tasks             │    │
│  │  Repositories  │  │ Services        │  │ • channel_check_tasks    │    │
│  │  • Async/Sync  │  │ • yt-dlp        │  │ • download_episode_task  │    │
│  │  • SQLite DB   │  │ • FFmpeg        │  │ • create_episode_task    │    │
│  │                │  │ • YouTube RSS   │  │ • backfill_channel_task  │    │
│  └────────────────┘  └─────────────────┘  └──────────────────────────┘    │
│          │                    │                      │                      │
│          ▼                    ▼                      ▼                      │
│  ┌────────────────┐  ┌─────────────────┐  ┌──────────────────────────┐    │
│  │   SQLite DB    │  │   YouTube       │  │        Redis             │    │
│  │   (WAL mode)   │  │   (Internet)    │  │   (Message Broker)       │    │
│  └────────────────┘  └─────────────────┘  └──────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Monorepo Structure

```
labcastarr/
├── backend/                          # FastAPI Backend Application
│   ├── app/                          # Main application code
│   │   ├── main.py                   # FastAPI entry point
│   │   ├── core/                     # Core configuration
│   │   ├── domain/                   # Domain layer
│   │   ├── application/              # Application layer
│   │   ├── infrastructure/           # Infrastructure layer
│   │   └── presentation/             # API layer
│   ├── alembic/                      # Database migrations
│   ├── data/                         # SQLite database files
│   ├── media/                        # Downloaded audio files
│   ├── feeds/                        # Generated RSS feeds
│   ├── logs/                         # Application logs
│   ├── Dockerfile                    # Production Dockerfile
│   ├── Dockerfile.dev                # Development Dockerfile
│   ├── pyproject.toml                # Python dependencies
│   └── startup.sh                    # Container startup script
│
├── frontend/                         # Next.js Frontend Application
│   ├── src/
│   │   ├── app/                      # App Router pages
│   │   ├── components/               # React components
│   │   ├── hooks/                    # Custom React hooks
│   │   ├── lib/                      # Utilities
│   │   └── types/                    # TypeScript definitions
│   ├── Dockerfile                    # Production Dockerfile
│   ├── Dockerfile.dev                # Development Dockerfile
│   └── package.json                  # Node.js dependencies
│
├── docs/                             # Documentation
│   ├── documentation/                # Main documentation
│   ├── specs/                        # Feature specifications
│   └── tasks/                        # Task files
│
├── scripts/                          # Utility scripts
│
├── .env.development                  # Development environment
├── .env.production                   # Production environment
├── .env.pre                          # Pre-production environment
├── docker-compose.dev.yml            # Development Docker setup
├── docker-compose.prod.yml           # Production Docker setup
├── docker-compose.pre.yml            # Pre-production Docker setup
├── CLAUDE.md                         # AI assistant instructions
└── README.md                         # Project README
```

---

## Backend Architecture

The backend follows **Clean Architecture** (also known as Hexagonal Architecture) with four distinct layers:

### Layer Structure

```
backend/app/
├── presentation/              # Layer 1: Presentation (outermost)
│   ├── api/v1/               # FastAPI routers
│   └── schemas/              # Pydantic request/response models
│
├── application/              # Layer 2: Application (use cases)
│   └── services/             # Application services (orchestration)
│
├── domain/                   # Layer 3: Domain (core business logic)
│   ├── entities/             # Domain entities (dataclasses)
│   ├── repositories/         # Repository interfaces (abstractions)
│   ├── services/             # Domain services (business rules)
│   └── value_objects/        # Value objects (immutable data)
│
├── infrastructure/           # Layer 4: Infrastructure (outermost)
│   ├── database/
│   │   ├── models/           # SQLAlchemy ORM models
│   │   └── connection.py     # Database connection management
│   ├── repositories/         # Repository implementations
│   ├── services/             # External service implementations
│   └── tasks/                # Celery background tasks
│
└── core/                     # Cross-cutting concerns
    ├── config.py             # Application configuration
    ├── dependencies.py       # FastAPI dependency injection
    ├── auth.py               # Authentication utilities
    ├── security.py           # Security middleware
    └── jwt.py                # JWT token management
```

### Dependency Direction

Dependencies flow **inward** - outer layers depend on inner layers, never the reverse:

```
Presentation → Application → Domain ← Infrastructure
                    ↓             ↑
                    └─────────────┘
                    (via interfaces)
```

### Layer Responsibilities

#### 1. Presentation Layer (`presentation/`)

- **Purpose**: Handle HTTP requests/responses
- **Components**:
  - API routes (`api/v1/*.py`) - 13+ routers with 50+ endpoints
  - Pydantic schemas (`schemas/*.py`) - Request/response validation

**Key Files:**
- `api/v1/router.py` - Main router combining all endpoints
- `api/v1/episodes.py` - Episode CRUD endpoints (largest: 56KB)
- `api/v1/followed_channels.py` - Channel subscription endpoints
- `api/v1/youtube_videos.py` - Discovered video management
- `api/health.py` - Health check endpoint

#### 2. Application Layer (`application/services/`)

- **Purpose**: Orchestrate use cases, coordinate domain services
- **No business logic** - Only coordination and orchestration

**Services (21 total):**
| Service | Responsibility |
|---------|---------------|
| `episode_service.py` | Episode CRUD, YouTube download coordination |
| `channel_service.py` | Podcast channel management |
| `followed_channel_service.py` | YouTube channel subscriptions |
| `youtube_video_service.py` | Discovered video management |
| `notification_service.py` | User notification management |
| `celery_task_status_service.py` | Background task tracking |
| `tag_service.py` | Tag CRUD operations |
| `search_service.py` | Episode search functionality |
| `upload_processing_service.py` | File upload handling |
| `feed_generation_service.py` | RSS feed orchestration |

#### 3. Domain Layer (`domain/`)

- **Purpose**: Core business logic, completely framework-agnostic
- **No dependencies** on FastAPI, SQLAlchemy, or external services

**Entities (10 total):**
| Entity | Purpose |
|--------|---------|
| `episode.py` | Podcast episode with status tracking |
| `channel.py` | Podcast channel configuration |
| `user.py` | User authentication data |
| `followed_channel.py` | YouTube channel subscription |
| `youtube_video.py` | Discovered video with state machine |
| `notification.py` | User notification |
| `celery_task_status.py` | Task status tracking |
| `tag.py` | Episode categorization |
| `event.py` | Audit log entry |
| `user_settings.py` | User preferences |

**Repository Interfaces:**
- Define contracts for data access
- Located in `domain/repositories/`
- Implementations in `infrastructure/repositories/`

**Domain Services:**
| Service | Purpose |
|---------|---------|
| `feed_generation_service.py` | RSS feed generation rules |
| `video_discovery_strategy.py` | Video discovery interface (Strategy pattern) |
| `youtube_metadata_service.py` | Metadata extraction interface |

**Value Objects:**
- `email.py` - Email validation
- `duration.py` - Duration handling
- `video_id.py` - YouTube video ID validation

#### 4. Infrastructure Layer (`infrastructure/`)

- **Purpose**: External systems integration
- **Implements** domain interfaces

**Database (`infrastructure/database/`):**
- `connection.py` - SQLite async connection (WAL mode)
- `models/` - SQLAlchemy ORM models (14 tables)

**Repository Implementations (`infrastructure/repositories/`):**
- Implement domain repository interfaces
- Use SQLAlchemy for data access
- Convert between ORM models and domain entities

**External Services (`infrastructure/services/`):**
| Service | Purpose |
|---------|---------|
| `youtube_service.py` | YouTube metadata extraction (yt-dlp) |
| `youtube_rss_service.py` | YouTube RSS feed fetching |
| `download_service.py` | Audio download management |
| `upload_service.py` | File upload handling |
| `media_file_service.py` | Media file processing |
| `feed_generation_service_impl.py` | RSS feed generation (PodGen) |
| `rss_discovery_strategy.py` | RSS-based video discovery |
| `ytdlp_discovery_strategy.py` | yt-dlp-based video discovery |

**Celery Tasks (`infrastructure/tasks/`):**
| Task | Purpose |
|------|---------|
| `channel_check_tasks.py` | yt-dlp video discovery |
| `channel_check_rss_tasks.py` | RSS video discovery + scheduled checks |
| `download_episode_task.py` | Audio download |
| `create_episode_from_video_task.py` | Episode creation from discovered video |
| `backfill_channel_task.py` | Historical video discovery |

---

## Frontend Architecture

### Directory Structure

```
frontend/src/
├── app/                           # Next.js 15 App Router
│   ├── layout.tsx                 # Root layout (providers)
│   ├── page.tsx                   # Home page
│   ├── login/                     # Authentication
│   ├── setup/                     # Initial setup
│   ├── channel/                   # Channel dashboard
│   ├── episodes/                  # Episode management
│   │   ├── add/                   # Add episode (method selection)
│   │   ├── add-from-youtube/      # YouTube URL form
│   │   ├── add-from-upload/       # File upload form
│   │   └── [id]/                  # Episode detail
│   ├── subscriptions/             # YouTube subscriptions
│   │   ├── channels/              # Followed channels
│   │   └── videos/                # Discovered videos
│   ├── search/                    # Advanced search
│   ├── settings/                  # User settings
│   └── activity/                  # Event log
│
├── components/
│   ├── ui/                        # ShadCN UI components (30+)
│   ├── features/                  # Feature-specific components
│   │   ├── episodes/              # Episode components
│   │   ├── channels/              # Channel components
│   │   ├── subscriptions/         # Subscription components
│   │   ├── tags/                  # Tag components
│   │   ├── search/                # Search components
│   │   ├── settings/              # Settings components
│   │   ├── activity/              # Activity components
│   │   └── notifications/         # Notification components
│   ├── layout/                    # Layout components
│   │   ├── main-layout.tsx        # Main app layout
│   │   ├── header.tsx             # Top navigation
│   │   ├── sidepanel.tsx          # Side navigation
│   │   └── notification-bell.tsx  # Notification dropdown
│   ├── providers/                 # React context providers
│   │   ├── auth-provider.tsx      # JWT authentication
│   │   ├── query-provider.tsx     # React Query setup
│   │   └── theme-provider.tsx     # Theme management
│   └── shared/                    # Shared utilities
│
├── hooks/                         # Custom React hooks
│   ├── use-episodes.ts            # Episode queries/mutations
│   ├── use-channels.ts            # Channel queries/mutations
│   ├── use-followed-channels.ts   # Subscription management
│   ├── use-youtube-videos.ts      # Discovered videos
│   ├── use-notifications.ts       # Notification queries
│   ├── use-task-status.ts         # Celery task polling
│   ├── use-search.ts              # Search functionality
│   └── use-activity-detection.ts  # Activity detection
│
├── lib/                           # Utilities
│   ├── api.ts                     # API client with auth
│   ├── query-client.ts            # React Query config
│   └── utils.ts                   # General utilities
│
└── types/                         # TypeScript definitions
    └── episode.ts                 # Episode types
```

### State Management

The frontend uses **React Query** (@tanstack/react-query) for server state:

- **Queries**: Data fetching with caching
- **Mutations**: Data modifications with optimistic updates
- **Query Invalidation**: Automatic cache refresh after mutations

**Custom Hooks Pattern:**

```typescript
// Example: use-episodes.ts
export function useEpisodes(channelId: number) {
  return useQuery({
    queryKey: ['episodes', channelId],
    queryFn: () => fetchEpisodes(channelId),
  });
}

export function useCreateEpisode() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createEpisode,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['episodes'] });
    },
  });
}
```

### API Client Configuration

```typescript
// lib/api.ts
const api = {
  get: async (url: string) => {
    const response = await fetch(`${BASE_URL}${url}`, {
      headers: {
        'X-API-Key': API_KEY,
        'Authorization': `Bearer ${accessToken}`,
      },
    });
    return response.json();
  },
  // ... post, put, delete methods
};
```

---

## Data Flow

### Episode Creation from YouTube URL

```
┌─────────────┐     ┌──────────────┐     ┌────────────────┐     ┌───────────────┐
│  Frontend   │────▶│   API Route  │────▶│ Application    │────▶│ Domain        │
│  Form       │     │ /v1/episodes │     │ EpisodeService │     │ Episode Entity│
└─────────────┘     └──────────────┘     └────────────────┘     └───────────────┘
                            │                     │
                            │                     ▼
                            │            ┌────────────────┐
                            │            │ Infrastructure │
                            │            │ • YouTubeService│
                            │            │ • Repository    │
                            │            └────────────────┘
                            │                     │
                            │                     ▼
                            │            ┌────────────────┐
                            │            │  Celery Task   │
                            │            │ download_episode│
                            │            └────────────────┘
                            │                     │
                            ▼                     ▼
                    ┌──────────────┐     ┌────────────────┐
                    │   Response   │     │  SQLite DB     │
                    │   (JSON)     │     │  + Media Files │
                    └──────────────┘     └────────────────┘
```

### YouTube Channel Discovery

```
┌─────────────────┐
│  Celery Beat    │ (Every 30 min)
│  Scheduler      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌────────────────────┐
│ scheduled_check │────▶│ RSS Discovery      │
│ _all_channels   │     │ Strategy           │
└─────────────────┘     └─────────┬──────────┘
                                  │
                                  ▼
                        ┌────────────────────┐
                        │ YouTube RSS Feed   │
                        │ (External)         │
                        └─────────┬──────────┘
                                  │
                                  ▼
                        ┌────────────────────┐
                        │ yt-dlp Metadata    │
                        │ (for new videos)   │
                        └─────────┬──────────┘
                                  │
                                  ▼
                        ┌────────────────────┐
                        │ YouTubeVideo       │
                        │ Repository         │
                        │ (Save to DB)       │
                        └─────────┬──────────┘
                                  │
                                  ▼
                        ┌────────────────────┐
                        │ Notification       │
                        │ Created            │
                        └────────────────────┘
```

---

## Design Patterns

### 1. Repository Pattern

**Purpose**: Abstract data access

```python
# Domain (Interface)
class EpisodeRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[Episode]: ...

# Infrastructure (Implementation)
class EpisodeRepositoryImpl(EpisodeRepository):
    async def get_by_id(self, id: int) -> Optional[Episode]:
        result = await session.execute(select(EpisodeModel).where(...))
        return self._to_entity(result.scalar_one_or_none())
```

### 2. Strategy Pattern

**Purpose**: Interchangeable video discovery algorithms

```python
# Domain (Interface)
class VideoDiscoveryStrategy(ABC):
    @abstractmethod
    async def discover_new_videos(
        self, channel: FollowedChannel, max_videos: int
    ) -> List[YouTubeVideo]: ...

# Infrastructure (Implementations)
class RSSDiscoveryStrategy(VideoDiscoveryStrategy):
    # Fast: Uses YouTube RSS feeds

class YtdlpDiscoveryStrategy(VideoDiscoveryStrategy):
    # Comprehensive: Uses yt-dlp channel listing
```

### 3. State Machine Pattern

**Purpose**: Valid state transitions for YouTubeVideo

```
pending_review → reviewed → queued → downloading → episode_created
       │             │
       └──── discarded ────┘
```

### 4. Service Layer Pattern

**Purpose**: Orchestrate use cases

```python
class EpisodeService:
    def __init__(
        self,
        episode_repository: EpisodeRepository,
        download_service: DownloadService,
    ):
        self._repo = episode_repository
        self._download = download_service

    async def create_episode(self, data: CreateEpisodeDTO) -> Episode:
        # Orchestration logic
        episode = Episode.create(...)
        await self._repo.save(episode)
        await self._download.queue_download(episode.id)
        return episode
```

### 5. Dependency Injection

**Purpose**: Loose coupling via FastAPI's DI

```python
# core/dependencies.py
def get_episode_service(
    db: AsyncSession = Depends(get_db),
) -> EpisodeService:
    repo = EpisodeRepositoryImpl(db)
    return EpisodeService(repo)

# API route usage
@router.get("/episodes/{id}")
async def get_episode(
    id: int,
    service: EpisodeService = Depends(get_episode_service),
):
    return await service.get_episode(id)
```

---

## Key Architectural Decisions

### 1. Clean Architecture

**Decision**: Implement Clean Architecture with 4 layers
**Rationale**:
- Separation of concerns
- Testability (domain logic testable without framework)
- Framework independence
- Easy to swap implementations

### 2. SQLite with WAL Mode

**Decision**: Use SQLite instead of PostgreSQL
**Rationale**:
- Simple deployment for homelab use case
- No external database server needed
- WAL mode provides good concurrency
- Suitable for single-server deployment

### 3. Celery for Background Tasks

**Decision**: Use Celery + Redis for background processing
**Rationale**:
- YouTube downloads can take minutes
- Non-blocking API responses
- Retry mechanisms for failed downloads
- Scheduled tasks (Celery Beat) for periodic checks

### 4. React Query for State Management

**Decision**: Use React Query instead of Redux/Zustand
**Rationale**:
- Server state is primary concern
- Built-in caching and invalidation
- Less boilerplate than Redux
- Optimistic updates support

### 5. Monorepo Structure

**Decision**: Keep frontend and backend in single repository
**Rationale**:
- Simplified version control
- Coordinated deployments
- Shared types possible (future)
- Single Docker Compose configuration

---

**End of Document**
