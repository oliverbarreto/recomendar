# LabCastARR Backend Architecture

**Document Version:** 1.0
**Last Updated:** 2026-01-29

---

## Table of Contents

1. [Overview](#overview)
2. [Directory Structure](#directory-structure)
3. [Clean Architecture Implementation](#clean-architecture-implementation)
4. [Core Layer](#core-layer)
5. [Domain Layer](#domain-layer)
6. [Application Layer](#application-layer)
7. [Infrastructure Layer](#infrastructure-layer)
8. [Presentation Layer](#presentation-layer)
9. [External Service Integrations](#external-service-integrations)
10. [Data Flow Examples](#data-flow-examples)
11. [Key Files Reference](#key-files-reference)

---

## Overview

The LabCastARR backend is built with **FastAPI** following **Clean Architecture** (also known as Hexagonal Architecture or Ports & Adapters). This architecture ensures:

- **Separation of concerns** - Each layer has a specific responsibility
- **Testability** - Business logic can be tested without frameworks
- **Framework independence** - Core logic doesn't depend on FastAPI or SQLAlchemy
- **Flexibility** - External services can be swapped without affecting business logic

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Web Framework | FastAPI | REST API, async support |
| ORM | SQLAlchemy (async) | Database abstraction |
| Database | SQLite (WAL mode) | Data persistence |
| Migrations | Alembic | Schema versioning |
| Validation | Pydantic | Request/response validation |
| Task Queue | Celery + Redis | Background processing |
| YouTube Integration | yt-dlp | Metadata & audio extraction |
| Audio Processing | FFmpeg | Format conversion |
| RSS Generation | PodGen | iTunes-compatible feeds |
| Package Manager | uv | Dependency management |

---

## Directory Structure

```
backend/
├── app/
│   ├── main.py                          # FastAPI application entry point
│   │
│   ├── core/                            # Cross-cutting concerns
│   │   ├── config.py                    # Application settings (Pydantic)
│   │   ├── dependencies.py              # FastAPI dependency injection
│   │   ├── auth.py                      # Authentication utilities
│   │   ├── security.py                  # Security middleware
│   │   ├── jwt.py                       # JWT token management
│   │   ├── validation.py                # Common validators
│   │   ├── logging.py                   # Logging configuration
│   │   └── middleware/
│   │       └── logging_middleware.py    # Request logging
│   │
│   ├── domain/                          # DOMAIN LAYER (Business Logic)
│   │   ├── entities/                    # Domain entities
│   │   │   ├── user.py
│   │   │   ├── channel.py
│   │   │   ├── episode.py
│   │   │   ├── tag.py
│   │   │   ├── followed_channel.py
│   │   │   ├── youtube_video.py
│   │   │   ├── notification.py
│   │   │   ├── celery_task_status.py
│   │   │   ├── event.py
│   │   │   └── user_settings.py
│   │   │
│   │   ├── repositories/                # Repository interfaces (ports)
│   │   │   ├── base.py
│   │   │   ├── user_repository.py
│   │   │   ├── channel_repository.py
│   │   │   ├── episode_repository.py
│   │   │   ├── tag_repository.py
│   │   │   ├── followed_channel_repository.py
│   │   │   ├── youtube_video_repository.py
│   │   │   ├── notification_repository.py
│   │   │   ├── event_repository.py
│   │   │   ├── search_repository.py
│   │   │   └── user_settings_repository.py
│   │   │
│   │   ├── services/                    # Domain services (business rules)
│   │   │   ├── feed_generation_service.py
│   │   │   ├── video_discovery_strategy.py
│   │   │   ├── youtube_metadata_service.py
│   │   │   └── channel_discovery_service.py
│   │   │
│   │   └── value_objects/               # Value objects (immutable)
│   │       ├── email.py
│   │       ├── duration.py
│   │       └── video_id.py
│   │
│   ├── application/                     # APPLICATION LAYER (Use Cases)
│   │   └── services/
│   │       ├── episode_service.py
│   │       ├── channel_service.py
│   │       ├── tag_service.py
│   │       ├── bulk_tag_service.py
│   │       ├── search_service.py
│   │       ├── event_service.py
│   │       ├── followed_channel_service.py
│   │       ├── youtube_video_service.py
│   │       ├── notification_service.py
│   │       ├── celery_task_status_service.py
│   │       ├── user_settings_service.py
│   │       ├── upload_processing_service.py
│   │       ├── metadata_processing_service.py
│   │       ├── url_validation_service.py
│   │       ├── initialization_service.py
│   │       ├── user_migration_service.py
│   │       └── metrics_service.py
│   │
│   ├── infrastructure/                  # INFRASTRUCTURE LAYER (External)
│   │   ├── database/
│   │   │   ├── connection.py            # Database session management
│   │   │   └── models/                  # SQLAlchemy ORM models
│   │   │       ├── user.py
│   │   │       ├── channel.py
│   │   │       ├── episode.py
│   │   │       ├── tag.py
│   │   │       ├── followed_channel.py
│   │   │       ├── youtube_video.py
│   │   │       ├── notification.py
│   │   │       ├── celery_task_status.py
│   │   │       ├── event.py
│   │   │       └── user_settings.py
│   │   │
│   │   ├── repositories/                # Repository implementations
│   │   │   ├── base_repository_impl.py
│   │   │   ├── user_repository_impl.py
│   │   │   ├── channel_repository_impl.py
│   │   │   ├── episode_repository_impl.py
│   │   │   ├── tag_repository_impl.py
│   │   │   ├── followed_channel_repository_impl.py
│   │   │   ├── youtube_video_repository_impl.py
│   │   │   ├── notification_repository_impl.py
│   │   │   ├── event_repository_impl.py
│   │   │   ├── search_repository_impl.py
│   │   │   └── user_settings_repository_impl.py
│   │   │
│   │   ├── services/                    # External service implementations
│   │   │   ├── youtube_service.py              # yt-dlp wrapper
│   │   │   ├── youtube_metadata_service_impl.py
│   │   │   ├── youtube_rss_service.py          # YouTube RSS feeds
│   │   │   ├── download_service.py             # Audio download
│   │   │   ├── celery_download_service.py      # Async download
│   │   │   ├── upload_service.py               # File upload handling
│   │   │   ├── file_service.py                 # File operations
│   │   │   ├── media_file_service.py           # Media processing
│   │   │   ├── feed_generation_service_impl.py # PodGen wrapper
│   │   │   ├── channel_discovery_service_impl.py
│   │   │   ├── rss_discovery_strategy.py       # RSS-based discovery
│   │   │   ├── ytdlp_discovery_strategy.py     # yt-dlp discovery
│   │   │   ├── itunes_validator.py             # Feed validation
│   │   │   └── logging_service.py
│   │   │
│   │   ├── tasks/                       # Celery background tasks
│   │   │   ├── channel_check_tasks.py
│   │   │   ├── channel_check_rss_tasks.py
│   │   │   ├── download_episode_task.py
│   │   │   ├── create_episode_from_video_task.py
│   │   │   └── backfill_channel_task.py
│   │   │
│   │   ├── celery_app.py                # Celery configuration
│   │   ├── celery_config.py             # Celery settings
│   │   └── celery_beat_schedule.py      # Scheduled tasks
│   │
│   └── presentation/                    # PRESENTATION LAYER (API)
│       ├── api/
│       │   ├── health.py                # Health check endpoint
│       │   └── v1/
│       │       ├── router.py            # Main API router
│       │       ├── auth.py              # Authentication endpoints
│       │       ├── users.py             # User management
│       │       ├── channels.py          # Channel CRUD
│       │       ├── episodes.py          # Episode CRUD + upload
│       │       ├── tags.py              # Tag management
│       │       ├── search.py            # Search endpoint
│       │       ├── feeds.py             # RSS feeds
│       │       ├── media.py             # Media streaming
│       │       ├── followed_channels.py # Subscriptions
│       │       ├── youtube_videos.py    # Discovered videos
│       │       ├── notifications.py     # Notifications
│       │       ├── celery_tasks.py      # Task status
│       │       ├── events.py            # Event log
│       │       ├── shortcuts.py         # iOS Shortcuts
│       │       └── system.py            # System info
│       │
│       └── schemas/                     # Pydantic schemas
│           ├── auth_schemas.py
│           ├── user_schemas.py
│           ├── channel_schemas.py
│           ├── episode_schemas.py
│           ├── tag_schemas.py
│           ├── feed_schemas.py
│           ├── followed_channel_schemas.py
│           ├── youtube_video_schemas.py
│           ├── notification_schemas.py
│           ├── celery_task_status_schemas.py
│           ├── event_schemas.py
│           ├── search_schemas.py
│           └── user_settings_schemas.py
│
├── alembic/                             # Database migrations
│   ├── versions/                        # Migration files (14 versions)
│   └── env.py                           # Alembic configuration
│
├── data/                                # SQLite database files
├── media/                               # Downloaded audio files
├── feeds/                               # Generated RSS feeds
├── logs/                                # Application logs
│
├── pyproject.toml                       # Python project configuration
├── uv.lock                              # Dependency lock file
├── alembic.ini                          # Alembic settings
├── Dockerfile                           # Production container
├── Dockerfile.dev                       # Development container
└── startup.sh                           # Container startup script
```

---

## Clean Architecture Implementation

### Layer Dependency Rules

```
┌─────────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                          │
│  FastAPI routes, Pydantic schemas                               │
│  Depends on: Application Layer                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     APPLICATION LAYER                           │
│  Use cases, orchestration services                              │
│  Depends on: Domain Layer (interfaces)                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       DOMAIN LAYER                              │
│  Entities, repository interfaces, domain services               │
│  Depends on: Nothing (pure business logic)                      │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────────┐
│                   INFRASTRUCTURE LAYER                          │
│  Repository implementations, external services, Celery tasks    │
│  Implements: Domain interfaces                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Key Principle:** Dependencies point inward. The domain layer has no knowledge of databases, external APIs, or web frameworks.

---

## Core Layer

The core layer contains cross-cutting concerns used across all layers.

### Configuration (`core/config.py`)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application
    environment: str = "development"
    debug: bool = False

    # Database
    database_url: str = "sqlite:///./data/labcastarr-dev.db"

    # Security
    api_key_secret: str
    jwt_secret_key: str
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 30

    # External services
    redis_url: str = "redis://localhost:6379/0"

    # File handling
    media_path: str = "./media"
    feeds_path: str = "./feeds"
    max_upload_file_size_mb: int = 500
    allowed_upload_formats: list = ["mp3", "m4a", "wav", "ogg", "flac"]
    target_audio_quality: str = "192"

    # Download settings
    max_concurrent_downloads: int = 3
    download_timeout_minutes: int = 30

    class Config:
        env_file = ".env"

settings = Settings()
```

### Dependency Injection (`core/dependencies.py`)

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

def get_episode_repository(
    db: AsyncSession = Depends(get_db)
) -> EpisodeRepository:
    return EpisodeRepositoryImpl(db)

def get_episode_service(
    repo: EpisodeRepository = Depends(get_episode_repository),
    download_service: DownloadService = Depends(get_download_service),
) -> EpisodeService:
    return EpisodeService(repo, download_service)
```

### JWT Management (`core/jwt.py`)

```python
from jose import jwt, JWTError
from datetime import datetime, timedelta

def create_access_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(
        minutes=settings.jwt_access_token_expire_minutes
    )
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "access"
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")

def create_refresh_token(user_id: int, remember_me: bool = False) -> str:
    days = 90 if remember_me else settings.jwt_refresh_token_expire_days
    expire = datetime.utcnow() + timedelta(days=days)
    # ...

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
        return payload
    except JWTError:
        raise InvalidTokenError()
```

---

## Domain Layer

The domain layer contains pure business logic with no external dependencies.

### Domain Entities

Entities are Python dataclasses representing core business objects:

```python
# domain/entities/episode.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from enum import Enum

class EpisodeStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class Episode:
    id: Optional[int]
    channel_id: int
    title: str
    description: Optional[str]
    video_url: Optional[str]
    video_id: Optional[str]
    thumbnail_url: Optional[str]
    audio_file_path: Optional[str]
    duration: Optional[int]
    status: EpisodeStatus
    source_type: str  # "youtube" or "upload"
    publication_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    tags: List["Tag"] = None

    @classmethod
    def create_from_youtube(
        cls,
        channel_id: int,
        video_url: str,
        title: str,
        description: str = None,
    ) -> "Episode":
        """Factory method for YouTube episodes"""
        return cls(
            id=None,
            channel_id=channel_id,
            title=title,
            description=description,
            video_url=video_url,
            video_id=extract_video_id(video_url),
            status=EpisodeStatus.PENDING,
            source_type="youtube",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            # ...
        )

    @classmethod
    def create_from_upload(
        cls,
        channel_id: int,
        title: str,
        audio_file_path: str,
        duration: int,
    ) -> "Episode":
        """Factory method for uploaded episodes"""
        return cls(
            # ...
            status=EpisodeStatus.COMPLETED,
            source_type="upload",
        )
```

### YouTubeVideo State Machine

```python
# domain/entities/youtube_video.py
from dataclasses import dataclass
from enum import Enum

class VideoState(str, Enum):
    PENDING_REVIEW = "pending_review"
    REVIEWED = "reviewed"
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    EPISODE_CREATED = "episode_created"
    DISCARDED = "discarded"

@dataclass
class YouTubeVideo:
    id: Optional[int]
    video_id: str
    followed_channel_id: int
    title: str
    state: VideoState
    episode_id: Optional[int]
    # ...

    # State transition methods with validation
    def mark_as_reviewed(self) -> None:
        if self.state != VideoState.PENDING_REVIEW:
            raise InvalidStateTransitionError(
                f"Cannot mark as reviewed from state {self.state}"
            )
        self.state = VideoState.REVIEWED
        self.reviewed_at = datetime.utcnow()

    def queue_for_episode_creation(self) -> None:
        if self.state not in [VideoState.PENDING_REVIEW, VideoState.REVIEWED]:
            raise InvalidStateTransitionError(
                f"Cannot queue from state {self.state}"
            )
        self.state = VideoState.QUEUED

    def mark_as_downloading(self) -> None:
        if self.state != VideoState.QUEUED:
            raise InvalidStateTransitionError(...)
        self.state = VideoState.DOWNLOADING

    def mark_as_episode_created(self, episode_id: int) -> None:
        if self.state != VideoState.DOWNLOADING:
            raise InvalidStateTransitionError(...)
        self.state = VideoState.EPISODE_CREATED
        self.episode_id = episode_id

    def discard(self) -> None:
        if self.state in [VideoState.EPISODE_CREATED, VideoState.DISCARDED]:
            raise InvalidStateTransitionError(...)
        self.state = VideoState.DISCARDED
```

### Repository Interfaces

Repository interfaces define contracts for data access:

```python
# domain/repositories/episode_repository.py
from abc import ABC, abstractmethod
from typing import Optional, List
from domain.entities.episode import Episode

class EpisodeRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[Episode]:
        """Get episode by ID"""
        pass

    @abstractmethod
    async def get_by_channel(
        self,
        channel_id: int,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Episode]:
        """Get episodes for a channel with optional filtering"""
        pass

    @abstractmethod
    async def get_by_video_id(self, video_id: str) -> Optional[Episode]:
        """Get episode by YouTube video ID"""
        pass

    @abstractmethod
    async def save(self, episode: Episode) -> Episode:
        """Create or update episode"""
        pass

    @abstractmethod
    async def delete(self, id: int) -> bool:
        """Delete episode by ID"""
        pass

    @abstractmethod
    async def count_by_channel(self, channel_id: int) -> int:
        """Count episodes in channel"""
        pass
```

### Domain Services

Domain services contain business logic that doesn't belong to a single entity:

```python
# domain/services/video_discovery_strategy.py
from abc import ABC, abstractmethod
from typing import List
from domain.entities.youtube_video import YouTubeVideo
from domain.entities.followed_channel import FollowedChannel

class VideoDiscoveryStrategy(ABC):
    """
    Strategy pattern interface for video discovery.
    Allows different discovery methods (RSS, yt-dlp, API).
    """

    @abstractmethod
    async def discover_new_videos(
        self,
        followed_channel: FollowedChannel,
        max_videos: int = 50
    ) -> List[YouTubeVideo]:
        """
        Discover new videos from a YouTube channel.

        Args:
            followed_channel: The channel to check
            max_videos: Maximum videos to fetch

        Returns:
            List of new YouTubeVideo entities (not yet in database)
        """
        pass
```

```python
# domain/services/youtube_metadata_service.py
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

class YouTubeMetadataService(ABC):
    """Interface for YouTube metadata extraction"""

    @abstractmethod
    async def extract_video_metadata(self, video_url: str) -> Dict:
        """Extract metadata from a single video URL"""
        pass

    @abstractmethod
    async def extract_channel_metadata(self, channel_url: str) -> Dict:
        """Extract channel metadata from URL"""
        pass

    @abstractmethod
    async def list_channel_videos(
        self,
        channel_id: str,
        max_videos: int = 50
    ) -> List[Dict]:
        """List videos from a channel"""
        pass
```

### Value Objects

Value objects are immutable and defined by their attributes:

```python
# domain/value_objects/video_id.py
from dataclasses import dataclass
import re

@dataclass(frozen=True)
class VideoId:
    """YouTube video ID value object with validation"""
    value: str

    def __post_init__(self):
        if not self._is_valid(self.value):
            raise ValueError(f"Invalid YouTube video ID: {self.value}")

    @staticmethod
    def _is_valid(video_id: str) -> bool:
        # YouTube video IDs are 11 characters
        return bool(re.match(r'^[a-zA-Z0-9_-]{11}$', video_id))

    @classmethod
    def from_url(cls, url: str) -> "VideoId":
        """Extract video ID from various YouTube URL formats"""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return cls(match.group(1))
        raise ValueError(f"Cannot extract video ID from URL: {url}")
```

---

## Application Layer

Application services orchestrate use cases by coordinating domain entities and repository calls.

### Episode Service

```python
# application/services/episode_service.py
from typing import Optional, List
from domain.entities.episode import Episode, EpisodeStatus
from domain.repositories.episode_repository import EpisodeRepository

class EpisodeService:
    def __init__(
        self,
        episode_repository: EpisodeRepository,
        channel_repository: ChannelRepository,
        download_service: DownloadService,
        feed_service: FeedGenerationService,
        event_service: EventService,
    ):
        self._episodes = episode_repository
        self._channels = channel_repository
        self._download = download_service
        self._feed = feed_service
        self._events = event_service

    async def create_from_youtube(
        self,
        channel_id: int,
        video_url: str,
        title: str,
        description: Optional[str] = None,
        tags: List[str] = None,
        user_id: int = None,
    ) -> Episode:
        """
        Create episode from YouTube URL.
        Orchestrates: validation, entity creation, persistence, download queueing.
        """
        # 1. Validate channel exists
        channel = await self._channels.get_by_id(channel_id)
        if not channel:
            raise ChannelNotFoundError(channel_id)

        # 2. Check for duplicate
        existing = await self._episodes.get_by_video_url(video_url)
        if existing:
            raise DuplicateEpisodeError(video_url)

        # 3. Create domain entity
        episode = Episode.create_from_youtube(
            channel_id=channel_id,
            video_url=video_url,
            title=title,
            description=description,
        )

        # 4. Persist
        episode = await self._episodes.save(episode)

        # 5. Queue download task
        await self._download.queue_download(
            episode_id=episode.id,
            user_id=user_id,
            channel_id=channel_id,
        )

        # 6. Log event
        await self._events.log_episode_created(episode, user_id)

        return episode

    async def create_from_upload(
        self,
        channel_id: int,
        title: str,
        file_path: str,
        duration: int,
        file_size: int,
        original_filename: str,
        user_id: int,
    ) -> Episode:
        """
        Create episode from uploaded file.
        File is already processed - just create entity and update feed.
        """
        episode = Episode.create_from_upload(
            channel_id=channel_id,
            title=title,
            audio_file_path=file_path,
            duration=duration,
        )
        episode.media_file_size = file_size
        episode.original_filename = original_filename

        episode = await self._episodes.save(episode)

        # Regenerate RSS feed
        await self._feed.regenerate_feed(channel_id)

        await self._events.log_upload_completed(episode, user_id)

        return episode

    async def get_by_id(self, episode_id: int) -> Optional[Episode]:
        return await self._episodes.get_by_id(episode_id)

    async def list_by_channel(
        self,
        channel_id: int,
        status: Optional[str] = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[List[Episode], int]:
        offset = (page - 1) * size
        episodes = await self._episodes.get_by_channel(
            channel_id=channel_id,
            status=status,
            limit=size,
            offset=offset,
        )
        total = await self._episodes.count_by_channel(channel_id)
        return episodes, total

    async def delete(self, episode_id: int, user_id: int) -> bool:
        episode = await self._episodes.get_by_id(episode_id)
        if not episode:
            raise EpisodeNotFoundError(episode_id)

        # Delete audio file
        if episode.audio_file_path:
            await self._delete_audio_file(episode.audio_file_path)

        # Delete from database
        await self._episodes.delete(episode_id)

        # Regenerate feed
        await self._feed.regenerate_feed(episode.channel_id)

        await self._events.log_episode_deleted(episode, user_id)

        return True
```

### Followed Channel Service

```python
# application/services/followed_channel_service.py
class FollowedChannelService:
    def __init__(
        self,
        followed_channel_repo: FollowedChannelRepository,
        youtube_video_repo: YouTubeVideoRepository,
        metadata_service: YouTubeMetadataService,
        notification_service: NotificationService,
    ):
        self._channels = followed_channel_repo
        self._videos = youtube_video_repo
        self._metadata = metadata_service
        self._notifications = notification_service

    async def follow_channel(
        self,
        user_id: int,
        channel_url: str,
        auto_approve: bool = False,
        auto_approve_channel_id: int = None,
    ) -> FollowedChannel:
        """
        Follow a YouTube channel.
        Extracts metadata and queues initial backfill.
        """
        # Extract channel metadata using yt-dlp
        metadata = await self._metadata.extract_channel_metadata(channel_url)

        # Check for existing subscription
        existing = await self._channels.get_by_youtube_id_and_user(
            metadata["channel_id"], user_id
        )
        if existing:
            raise ChannelAlreadyFollowedError(channel_url)

        # Create entity
        channel = FollowedChannel(
            user_id=user_id,
            youtube_channel_id=metadata["channel_id"],
            youtube_channel_name=metadata["channel_name"],
            youtube_channel_url=channel_url,
            thumbnail_url=metadata.get("thumbnail_url"),
            auto_approve=auto_approve,
            auto_approve_channel_id=auto_approve_channel_id,
        )

        channel = await self._channels.save(channel)

        # Queue backfill task
        from infrastructure.tasks.backfill_channel_task import backfill_followed_channel
        task = backfill_followed_channel.delay(channel.id, max_videos=20)
        channel.last_backfill_task_id = task.id
        await self._channels.save(channel)

        return channel

    async def trigger_check(
        self,
        channel_id: int,
        user_id: int,
        use_rss: bool = False
    ) -> str:
        """Trigger video discovery check"""
        channel = await self._channels.get_by_id(channel_id)
        if not channel:
            raise ChannelNotFoundError(channel_id)

        # Queue appropriate task
        if use_rss:
            from infrastructure.tasks.channel_check_rss_tasks import (
                check_followed_channel_for_new_videos_rss
            )
            task = check_followed_channel_for_new_videos_rss.delay(
                channel_id, user_id
            )
        else:
            from infrastructure.tasks.channel_check_tasks import (
                check_followed_channel_for_new_videos
            )
            task = check_followed_channel_for_new_videos.delay(
                channel_id, user_id
            )

        # Update channel with task ID
        channel.last_check_task_id = task.id
        await self._channels.save(channel)

        return task.id
```

---

## Infrastructure Layer

The infrastructure layer implements domain interfaces and handles external services.

### Repository Implementation

```python
# infrastructure/repositories/episode_repository_impl.py
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from domain.repositories.episode_repository import EpisodeRepository
from domain.entities.episode import Episode
from infrastructure.database.models.episode import EpisodeModel

class EpisodeRepositoryImpl(EpisodeRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, id: int) -> Optional[Episode]:
        result = await self._session.execute(
            select(EpisodeModel)
            .where(EpisodeModel.id == id)
            .options(selectinload(EpisodeModel.tags))
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def save(self, episode: Episode) -> Episode:
        if episode.id:
            # Update existing
            model = await self._get_model(episode.id)
            self._update_model(model, episode)
        else:
            # Create new
            model = self._to_model(episode)
            self._session.add(model)

        await self._session.commit()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def delete(self, id: int) -> bool:
        result = await self._session.execute(
            delete(EpisodeModel).where(EpisodeModel.id == id)
        )
        await self._session.commit()
        return result.rowcount > 0

    # Mapping methods
    def _to_entity(self, model: EpisodeModel) -> Episode:
        """Convert SQLAlchemy model to domain entity"""
        return Episode(
            id=model.id,
            channel_id=model.channel_id,
            title=model.title,
            description=model.description,
            video_url=model.video_url,
            status=EpisodeStatus(model.status),
            source_type=model.source_type,
            # ... map all fields
        )

    def _to_model(self, entity: Episode) -> EpisodeModel:
        """Convert domain entity to SQLAlchemy model"""
        return EpisodeModel(
            channel_id=entity.channel_id,
            title=entity.title,
            # ... map all fields
        )
```

### Database Models

```python
# infrastructure/database/models/episode.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from infrastructure.database.connection import Base

class EpisodeModel(Base):
    __tablename__ = "episodes"

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    video_url = Column(String(500))
    video_id = Column(String(50), unique=True, index=True)
    thumbnail_url = Column(String(500))
    audio_file_path = Column(String(500))
    duration = Column(Integer)
    status = Column(String(50), default="pending", index=True)
    source_type = Column(String(20), default="youtube", index=True)
    original_filename = Column(String(255))
    media_file_size = Column(Integer)
    publication_date = Column(DateTime)
    download_date = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    channel = relationship("ChannelModel", back_populates="episodes")
    tags = relationship("TagModel", secondary="episode_tags", back_populates="episodes")
```

---

## External Service Integrations

### yt-dlp Integration

```python
# infrastructure/services/youtube_metadata_service_impl.py
import yt_dlp
from domain.services.youtube_metadata_service import YouTubeMetadataService

class YouTubeMetadataServiceImpl(YouTubeMetadataService):
    """Implementation using yt-dlp for YouTube metadata extraction"""

    def __init__(self):
        self._ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }

    async def extract_video_metadata(self, video_url: str) -> Dict:
        """Extract metadata from YouTube video URL"""
        opts = {
            **self._ydl_opts,
            'skip_download': True,
        }

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(video_url, download=False)

        return {
            'video_id': info.get('id'),
            'title': info.get('title'),
            'description': info.get('description'),
            'duration': info.get('duration'),
            'thumbnail_url': info.get('thumbnail'),
            'channel_id': info.get('channel_id'),
            'channel_name': info.get('channel'),
            'upload_date': info.get('upload_date'),
            'view_count': info.get('view_count'),
            'like_count': info.get('like_count'),
        }

    async def extract_channel_metadata(self, channel_url: str) -> Dict:
        """Extract channel metadata from YouTube channel URL"""
        opts = {
            **self._ydl_opts,
            'extract_flat': True,
            'playlist_items': '0',  # Don't fetch videos
        }

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(channel_url, download=False)

        return {
            'channel_id': info.get('channel_id') or info.get('id'),
            'channel_name': info.get('channel') or info.get('title'),
            'channel_url': info.get('channel_url') or channel_url,
            'thumbnail_url': info.get('thumbnail'),
            'description': info.get('description'),
        }

    async def list_channel_videos(
        self,
        channel_id: str,
        max_videos: int = 50
    ) -> List[Dict]:
        """List recent videos from a YouTube channel"""
        channel_url = f"https://www.youtube.com/channel/{channel_id}/videos"

        opts = {
            **self._ydl_opts,
            'extract_flat': True,
            'playlist_items': f'1-{max_videos}',
        }

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(channel_url, download=False)

        videos = []
        for entry in info.get('entries', []):
            videos.append({
                'video_id': entry.get('id'),
                'title': entry.get('title'),
                'url': entry.get('url'),
                'duration': entry.get('duration'),
            })

        return videos
```

### YouTube RSS Service

```python
# infrastructure/services/youtube_rss_service.py
import aiohttp
import xml.etree.ElementTree as ET
from typing import List, Dict

class YouTubeRSSService:
    """Service for fetching YouTube channel RSS feeds"""

    RSS_URL_TEMPLATE = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

    async def fetch_channel_feed(self, channel_id: str) -> List[Dict]:
        """
        Fetch recent videos from YouTube RSS feed.
        Returns last 10-15 videos (YouTube's RSS limit).
        """
        url = self.RSS_URL_TEMPLATE.format(channel_id=channel_id)

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise YouTubeRSSError(f"Failed to fetch RSS: {response.status}")
                content = await response.text()

        return self._parse_feed(content)

    def _parse_feed(self, xml_content: str) -> List[Dict]:
        """Parse Atom XML feed"""
        root = ET.fromstring(xml_content)
        ns = {
            'atom': 'http://www.w3.org/2005/Atom',
            'yt': 'http://www.youtube.com/xml/schemas/2015',
            'media': 'http://search.yahoo.com/mrss/',
        }

        videos = []
        for entry in root.findall('atom:entry', ns):
            video_id = entry.find('yt:videoId', ns).text
            title = entry.find('atom:title', ns).text
            published = entry.find('atom:published', ns).text

            videos.append({
                'video_id': video_id,
                'title': title,
                'url': f'https://www.youtube.com/watch?v={video_id}',
                'published': published,
            })

        return videos
```

### Download Service (Audio Extraction)

```python
# infrastructure/services/download_service.py
import yt_dlp
import os
from pathlib import Path

class DownloadService:
    """Service for downloading audio from YouTube videos"""

    def __init__(self, media_path: str):
        self._media_path = Path(media_path)

    async def download_audio(
        self,
        video_url: str,
        channel_id: int,
        episode_id: int,
    ) -> str:
        """
        Download audio from YouTube video.
        Returns path to downloaded file.
        """
        output_dir = self._media_path / f"channel_{channel_id}"
        output_dir.mkdir(parents=True, exist_ok=True)

        output_template = str(output_dir / f"episode_{episode_id}.%(ext)s")

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        # Find the downloaded file
        output_path = output_dir / f"episode_{episode_id}.mp3"
        if not output_path.exists():
            raise DownloadError(f"Download failed: file not found")

        return str(output_path.relative_to(self._media_path.parent))

    async def queue_download(
        self,
        episode_id: int,
        user_id: int,
        channel_id: int,
    ) -> str:
        """Queue download task via Celery"""
        from infrastructure.tasks.download_episode_task import download_episode
        task = download_episode.delay(episode_id, user_id, channel_id)
        return task.id
```

### FFmpeg Integration (Audio Conversion)

```python
# infrastructure/services/media_file_service.py
import subprocess
import os
from pathlib import Path

class MediaFileService:
    """Service for audio file processing with FFmpeg"""

    CONVERTIBLE_FORMATS = ['wav', 'ogg', 'flac']
    TARGET_FORMAT = 'mp3'
    TARGET_BITRATE = '192k'

    async def process_upload(
        self,
        source_path: str,
        target_dir: str,
        target_filename: str,
    ) -> tuple[str, int, int]:
        """
        Process uploaded audio file.
        Converts to MP3 if necessary.

        Returns: (file_path, duration_seconds, file_size_bytes)
        """
        source = Path(source_path)
        extension = source.suffix.lower().lstrip('.')

        if extension in self.CONVERTIBLE_FORMATS:
            # Convert to MP3
            target_path = Path(target_dir) / f"{target_filename}.mp3"
            await self._convert_to_mp3(source, target_path)
        else:
            # Copy as-is (MP3, M4A)
            target_path = Path(target_dir) / f"{target_filename}.{extension}"
            shutil.copy2(source, target_path)

        duration = await self._get_duration(target_path)
        file_size = target_path.stat().st_size

        return str(target_path), duration, file_size

    async def _convert_to_mp3(self, source: Path, target: Path) -> None:
        """Convert audio file to MP3 using FFmpeg"""
        cmd = [
            'ffmpeg',
            '-i', str(source),
            '-vn',  # No video
            '-acodec', 'libmp3lame',
            '-ab', self.TARGET_BITRATE,
            '-ar', '44100',  # Sample rate
            '-y',  # Overwrite
            str(target)
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise ConversionError(f"FFmpeg error: {stderr.decode()}")

    async def _get_duration(self, file_path: Path) -> int:
        """Get audio duration using FFprobe"""
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(file_path)
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await process.communicate()

        return int(float(stdout.decode().strip()))
```

### RSS Feed Generation (PodGen)

```python
# infrastructure/services/feed_generation_service_impl.py
from podgen import Podcast, Episode as PodgenEpisode, Media
from domain.services.feed_generation_service import FeedGenerationService

class FeedGenerationServiceImpl(FeedGenerationService):
    """RSS feed generation using PodGen library"""

    def __init__(self, feeds_path: str, base_url: str):
        self._feeds_path = Path(feeds_path)
        self._base_url = base_url

    async def generate_feed(
        self,
        channel: Channel,
        episodes: List[Episode]
    ) -> str:
        """
        Generate iTunes-compatible RSS feed for a channel.
        Returns path to generated feed file.
        """
        podcast = Podcast(
            name=channel.title,
            description=channel.description or "",
            website=channel.website_url or self._base_url,
            explicit=channel.explicit,
            language=channel.language or "en",
        )

        if channel.author_name:
            podcast.authors = [Person(channel.author_name, channel.author_email)]

        if channel.image_url:
            podcast.image = channel.image_url

        # Add episodes
        for episode in episodes:
            if episode.status != EpisodeStatus.COMPLETED:
                continue

            media_url = f"{self._base_url}/v1/media/episodes/{episode.id}/audio"

            pe = PodgenEpisode(
                title=episode.title,
                summary=episode.description or "",
                publication_date=episode.publication_date,
            )

            pe.media = Media(
                media_url,
                size=episode.media_file_size,
                type="audio/mpeg",
                duration=timedelta(seconds=episode.duration or 0),
            )

            if episode.thumbnail_url:
                pe.image = episode.thumbnail_url

            podcast.episodes.append(pe)

        # Write feed to file
        feed_dir = self._feeds_path / f"channel_{channel.id}"
        feed_dir.mkdir(parents=True, exist_ok=True)
        feed_path = feed_dir / "feed.xml"

        podcast.rss_file(str(feed_path))

        return str(feed_path)

    async def regenerate_feed(self, channel_id: int) -> str:
        """Regenerate feed after episode changes"""
        channel = await self._channel_repo.get_by_id(channel_id)
        episodes = await self._episode_repo.get_by_channel(channel_id)
        return await self.generate_feed(channel, episodes)
```

---

## Presentation Layer

### API Routes

```python
# presentation/api/v1/episodes.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from presentation.schemas.episode_schemas import EpisodeCreate, EpisodeResponse

router = APIRouter(prefix="/episodes", tags=["Episodes"])

@router.post("/", response_model=EpisodeResponse, status_code=201)
async def create_episode(
    data: EpisodeCreate,
    service: EpisodeService = Depends(get_episode_service),
    current_user: User = Depends(get_current_user),
):
    """Create episode from YouTube URL"""
    try:
        episode = await service.create_from_youtube(
            channel_id=data.channel_id,
            video_url=data.video_url,
            title=data.title,
            description=data.description,
            user_id=current_user.id,
        )
        return EpisodeResponse.from_entity(episode)
    except DuplicateEpisodeError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.post("/upload", response_model=EpisodeResponse, status_code=201)
async def upload_episode(
    channel_id: int = Form(...),
    title: str = Form(...),
    description: str = Form(None),
    audio_file: UploadFile = File(...),
    upload_service: UploadProcessingService = Depends(get_upload_service),
    episode_service: EpisodeService = Depends(get_episode_service),
    current_user: User = Depends(get_current_user),
):
    """Upload audio file to create episode"""
    # Validate file
    await upload_service.validate_file(audio_file)

    # Process upload
    file_path, duration, file_size = await upload_service.process_upload(
        audio_file, channel_id
    )

    # Create episode
    episode = await episode_service.create_from_upload(
        channel_id=channel_id,
        title=title,
        file_path=file_path,
        duration=duration,
        file_size=file_size,
        original_filename=audio_file.filename,
        user_id=current_user.id,
    )

    return EpisodeResponse.from_entity(episode)
```

### Pydantic Schemas

```python
# presentation/schemas/episode_schemas.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class EpisodeCreate(BaseModel):
    channel_id: int = Field(..., gt=0)
    video_url: str = Field(..., min_length=10)
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=5000)
    tags: Optional[List[str]] = Field(default_factory=list, max_items=10)

class EpisodeResponse(BaseModel):
    id: int
    channel_id: int
    title: str
    description: Optional[str]
    video_url: Optional[str]
    thumbnail_url: Optional[str]
    duration: Optional[int]
    status: str
    source_type: str
    publication_date: Optional[datetime]
    tags: List[TagResponse]

    @classmethod
    def from_entity(cls, entity: Episode) -> "EpisodeResponse":
        return cls(
            id=entity.id,
            channel_id=entity.channel_id,
            title=entity.title,
            # ... map all fields
        )

    class Config:
        from_attributes = True
```

---

## Data Flow Examples

### YouTube Episode Creation

```
1. API Request
   POST /v1/episodes
   Body: {channel_id, video_url, title}
          │
          ▼
2. Presentation Layer (episodes.py)
   - Validates request with Pydantic
   - Calls EpisodeService.create_from_youtube()
          │
          ▼
3. Application Layer (episode_service.py)
   - Validates channel exists (via repository)
   - Checks for duplicates
   - Creates Episode entity
   - Saves via repository
   - Queues Celery download task
          │
          ▼
4. Infrastructure Layer
   ├── EpisodeRepositoryImpl: Saves to SQLite
   └── DownloadService: Queues Celery task
          │
          ▼
5. Celery Worker (download_episode_task.py)
   - Uses yt-dlp to download audio
   - Converts to MP3 via FFmpeg
   - Updates episode status
   - Regenerates RSS feed via PodGen
```

### Video Discovery Flow

```
1. Celery Beat Trigger (every 30 min)
          │
          ▼
2. scheduled_check_all_channels_rss task
   - Queries all followed channels
   - Queues individual check tasks
          │
          ▼
3. check_followed_channel_for_new_videos_rss task
          │
          ▼
4. RSSDiscoveryStrategy
   ├── YouTubeRSSService: Fetches RSS feed
   ├── YouTubeMetadataService: Gets metadata for new videos
   └── YouTubeVideoRepository: Saves new videos
          │
          ▼
5. NotificationService
   - Creates user notification
```

---

## Key Files Reference

### Configuration & Entry Points

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI application setup |
| `app/core/config.py` | Application settings |
| `app/core/dependencies.py` | Dependency injection |
| `app/infrastructure/celery_app.py` | Celery configuration |

### Domain Layer

| File | Purpose |
|------|---------|
| `domain/entities/episode.py` | Episode entity with status |
| `domain/entities/youtube_video.py` | YouTubeVideo with state machine |
| `domain/repositories/*.py` | Repository interfaces |
| `domain/services/video_discovery_strategy.py` | Discovery interface |

### External Service Integration

| File | External Service |
|------|-----------------|
| `infrastructure/services/youtube_metadata_service_impl.py` | yt-dlp metadata |
| `infrastructure/services/youtube_rss_service.py` | YouTube RSS feeds |
| `infrastructure/services/download_service.py` | yt-dlp audio download |
| `infrastructure/services/media_file_service.py` | FFmpeg conversion |
| `infrastructure/services/feed_generation_service_impl.py` | PodGen RSS |

### Celery Tasks

| File | Purpose |
|------|---------|
| `infrastructure/tasks/download_episode_task.py` | Audio download |
| `infrastructure/tasks/channel_check_tasks.py` | yt-dlp discovery |
| `infrastructure/tasks/channel_check_rss_tasks.py` | RSS discovery |
| `infrastructure/tasks/create_episode_from_video_task.py` | Episode creation |
| `infrastructure/tasks/backfill_channel_task.py` | Historical videos |

---

**End of Document**
