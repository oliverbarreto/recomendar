# Flask to Modern Stack Migration Strategy

## Architecture Overview

This project will be a transformation from a Flask monolith to a clean, decoupled architecture:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Next.js 15    │    │   FastAPI        │    │   SQLite        │
│   Frontend      │◄──►│   Backend        │◄──►│   (Async)       │
│                 │    │                  │    │                 │
│ • TypeScript    │    │ • Python 3.11+   │    │ • SQLModel      │
│ • React 19      │    │ • Async/Await    │    │ • Alembic       │
│ • ShadCN        │    │ • Pydantic v2    │    │                 │
│ • TailwindCSS   │    │ • Background     │    │                 │
│ • ShadCN        │    │ • Tasks          │    │                 │
│ • Server Actions│    │ ---------------- │    │                 │
│ •               │    │ • YT-DLP         │    │                 │
│ •               │    │ • PodGen: RSS/XML│    │                 │
│ •               │    │   Feed           │    │                 │
│ •               │    │ • Media Storage  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │
         │                        │
         ▼                        ▼
┌─────────────────┐    ┌──────────────────┐
│  RSS/XML Feed   │    │  Media Storage   │
│  (Next.js API)  │    │  (Local Files)   │
└─────────────────┘    └──────────────────┘
```


---

## Backend Architecture (FastAPI)

### Backend Project Structure

```
backend/
├── static/                   # Media files storage.
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── core/                 # Core configurations, dependencies, and utilities for the backend.
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── dependencies.py
│   ├── domain/               # Core business logic, entities, repositories, exceptions
│   │   ├── __init__.py
│   │   ├── entities/         # Business entities.
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── channel.py
│   │   │   └── episode.py
│   │   └── repositories/     # Abstract repositories (Interfaces)
│   │   │   ├── __init__.py
│   │   │   ├── user_repository.py
│   │   │   ├── channel_repository.py
│   │   │   └── episode_repository.py
│   │   └── exceptions/   # Domain-specific exceptions.
│   │          ├── __init__.py
│   │          └── base.py
│   ├── application/          # Use cases and services.
│   │   ├── __init__.py
│   │   ├── services/         # Business Logic - Services (Implementations)
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── youtube_service.py
│   │   │   ├── podcast_service.py
│   │   │   └── transcript_service.py
│   │   └── use_cases/        # Business logic - Use Cases
│   │   │   ├── __init__.py
│   │   │   ├── user_auth_use_cases.py
│   │   │   ├── user_profile_use_cases.py
│   │   │   ├── channel_use_cases.py
│   │   │   └── episode_use_cases.py
│   │   │   └── podcast_use_cases.py
│   │   │   └── transcript_use_cases.py
│   ├── infrastructure/       # Implementation details, interactions with databases, cloud SDKs, frameworks, and repositories.
│   │   ├── __init__.py
│   │   ├── database/         # Database models.
│   │   │   ├── __init__.py
│   │   │   ├── connection.py
│   │   │   ├── models.py     
│   │   ├── repositories/     # Repository pattern - Concrete implementations - Data Access Objects.
│   │   │   ├── __init__.py
│   │   │   ├── youtube_repository.py
│   │   │   └── transcript_repository.py
│   │   │   └── sql_user_repository.py
│   │   └── background/         # Background tasks.
│   │       ├── __init__.py
│   │       └── tasks.py
│   ├── presentation/           # Entry points for API requests (routers by version) and schemas definitions.
│   │   ├── __init__.py
│   │   ├── api/                 # API layer
│   │   │   ├── __init__.py
│   │   │   ├── v1/              # API versioning
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py
│   │   │   │   ├── episodes.py
│   │   │   │   ├── channels.py
│   │   │   │   └── users.py
│   │   │   └── dependencies.py
│   │   ├── schemas/              # API schemas (Pydantic)
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── episode.py
│   │   │   ├── channel.py
│   │   │   └── user.py
├── tests/                    # Contains all automated tests, mirroring the src/ structure where applicable.
├── alembic/                  # Database migrations.
├── requirements.txt          # Python dependencies
├── pyproject.toml            # Project metadata
├── .env.example              # Environment variables example
├── .env                      # Environment variables
├── .gitignore                # Git ignore file
├── README.md                 # Project README
├── LICENSE                   # Project license
└── Dockerfile
```

#### Key Directory Descriptions for the Backend

- `backend/`: Contains the main application source code.
- `backend/app/`: Contains the main application source code.
- `backend/app/core/`: Contains the core configurations, dependencies, and utilities for the backend.
- `backend/app/domain/`: Contains the core business logic, entities, repositories, exceptions.
- `backend/app/application/`: Contains the use cases and services.
- `backend/app/infrastructure/`: Contains the implementation details, interactions with databases, cloud SDKs, frameworks, and repositories.
- `backend/app/presentation/`: Contains the entry points for API requests (routers by version) and schemas definitions.


### API Reference

#### PODGEN API (file `/project-docs/docs/backend-libs-itunes-xml-feed.md`)

- The PODGEN API is used to generate the RSS/XML feed for the podcast.
- The PODGEN API is used to generate the podcast feed URL.
- The PODGEN API is used to generate the podcast feed URL.


#### YT-DLP API (file `/project-docs/docs/backend-libs-yt-dlp.md`)

- The YT-DLP API is used to download the audio and video files from YouTube.
- The YT-DLP API is used to download the video thumbnail from YouTube.
- The YT-DLP API is used to download the video transcript from YouTube.

#### Database  (file `/project-docs/docs/backend-fastapi-db-sql.md`)

- The database is a SQLite database.
- The database is used to store the user, channel, and episode data.
- We will use async sessions with SQLAlchemy (file `/project-docs/docs/backend-fastapi-db-async-sessions-sqlalchemy.md`)

#### File Storage 

- The file storage is done locally in the `backend/static/` directory.

#### Background Tasks (file `/project-docs/docs/backend-fastapi-background-tasks.md`)

- The background tasks are used to process the episodes and update the database.


### Backend Technology Stack

| Category             | Technology                | Version / Details                | Description / Purpose                                      | Justification                                                                                                |
| :------------------- | :------------------------ | :------------------------------- | :--------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------- |
| **Languages**        | Python                    | 3.11.8 (or latest 3.11.x/3.12.x) | Primary language for backend API development.              | Mature, extensive libraries, strong AI/ML ecosystem, excellent for web backends with FastAPI.                |
| **Frameworks**       | FastAPI                   | Latest (e.g., 0.110.x)           | Modern, fast (high-performance) web framework for building APIs. | High performance, async support, automatic data validation & serialization (Pydantic), great DX.             |
| **Databases**        | SQLite                    | Bundled with Python              | File-based relational database.                              | Simple setup, sufficient for homelab/few users, good async support with `aiosqlite`.                         |
| **ORM / DB Driver**  | SQLModel                  | Latest                           | Python ORM that combines Pydantic and SQLAlchemy.          | Modern, reduces boilerplate, excellent type safety, integrates perfectly with FastAPI, async-first.          |
|                      | `aiosqlite`               | Latest                           | Async SQLite driver for Python.                            | Required for async operations with SQLite.                                                                   |
| **Migrations**       | Alembic                   | Latest                           | Database migration tool for SQLAlchemy (and thus SQLModel). | Robust schema migration management.                                                                          |
| **Data Validation**  | Pydantic                  | Bundled with FastAPI/SQLModel    | Data validation and settings management using Python type hints. | Core to FastAPI and SQLModel for request/response validation and data structuring.                         |
| **Async Server**     | Uvicorn                   | Latest                           | ASGI server for FastAPI.                                   | High-performance ASGI server, standard for FastAPI.                                                          |
| **YouTube Processing**| `yt-dlp`                  | Latest                           | Command-line program to download videos/audio from YouTube & other sites. | Powerful, actively maintained, feature-rich for metadata and audio extraction. Used via `asyncio.subprocess`. |
| **Transcript**       | `youtube-transcript-api`  | Latest                           | Python API to fetch YouTube transcripts.                   | Simple, direct way to get YouTube-generated transcripts.                                                     |
| **Podcast Generation**| `podgen`                  | Latest                           | Python library for generating podcast RSS feeds.             | Specifically designed for creating podcast feeds, familiar from the old app.                                 |
| **Background Tasks** | FastAPI `BackgroundTasks` | Bundled with FastAPI             | For running operations after returning a response.         | Simple way to offload non-blocking tasks like YouTube processing.                                            |
| **Real-time (Backend)**| `sse-starlette`           | Latest                           | Server-Sent Events (SSE) utilities for Starlette/FastAPI.  | To push real-time processing status updates to the frontend.                                                 |
| **Testing**          | Pytest                    | Latest                           | Python testing framework.                                  | Powerful and flexible for unit and integration tests.                                                        |
|                      | `httpx`                   | Latest                           | Async HTTP client for Python (for testing FastAPI).        | For making async requests to the API during tests.                                                           |
| **Logging**          | Python `logging` module   | Bundled with Python              | Standard logging library for Python applications.          | Provides a flexible framework for emitting log messages from Python programs, essential for monitoring and debugging. |
| **Linting/Formatting**| Ruff (Recommended)        | Latest                           | Extremely fast Python linter and formatter (can replace Black, Flake8, isort). | Speed, comprehensive checks, auto-fixing.                                                                    |
|                      | Black (Alternative)       | Latest                           | Opinionated Python code formatter.                         | Ensures consistent code style if Ruff is not chosen for formatting.                                          |
| **Dependency Mgt.**  | Poetry (Recommended)      | Latest                           | Tool for dependency management and packaging in Python.    | Modern, robust dependency resolution and virtual environment management.                                     |
| **Containerization** | Docker                    | Latest                           | For creating a consistent deployment environment.          | Standard for containerizing applications.                                                                    |

### Logging (file `/project-docs/docs/backend-fastapi-loggin-best-practice.md`)

- Use Python’s `logging` module with **`logging.config.dictConfig()`** for structured, JSON-based logging. 
- Use JSON or structured logging formats to ensure compatibility with log aggregation and monitoring tools like ELK Stack, Splunk, or Datadog.
- Since FastAPI often runs with Uvicorn, configure Uvicorn's logging to work seamlessly with your application’s logs.
```bash
uvicorn app:app --log-config logging.yaml
```
- Adopt appropriate logging levels to categorize log entries:
  - DEBUG: Detailed diagnostic information.
  - INFO: General operational events.
  - WARNING: Unusual situations that aren’t errors.
  - ERROR: Issues that disrupt normal operation.
  - CRITICAL: Severe problems that require immediate attention.
- Ensure that personally identifiable information (PII) and sensitive data are not logged. Mask or redact such information if necessary.
- Create custom middleware to log HTTP requests and responses.
- Add context to log entries using structured fields like `request_id` or `user_id`.
- Use tools like `logging.handlers.RotatingFileHandler` to rotate log files and prevent them from growing indefinitely.
- Send logs to external monitoring systems for real-time analysis. (OPTIONAL: maybe Sentry or similar)


### Data Models (file `/project-docs/docs/backend-fastapi-data-models.md`)

#### Relationships and Indexes

As a summary, the data models defined next will be used to create the database schema with the following relationships and indexes:

- **User → Channel**: One-to-many relationship with cascade delete
- **Channel → Episode**: One-to-many relationship with cascade delete
- **Episode → Transcript**: One-to-one relationship with cascade delete
- **Episode → Audio File**: One-to-one relationship with cascade delete
- **Optimized Indexes**: Strategic indexing for common queries
- **Data Integrity**: Foreign key constraints and validation rules


#### 1. User Entity

##### **1.1. Concept:**
Represents an individual who registers for the application, logs in, and owns a podcast channel.

##### **1.2. Backend - SQLModel Definition (`models/user.py`)**
```python
from typing import TYPE_CHECKING, Optional
from sqlmodel import Field, SQLModel, Relationship
import datetime

if TYPE_CHECKING:
    from .channel import Channel  # Forward reference for type hinting

class UserBase(SQLModel):
    name: str = Field(index=True, unique=True, max_length=50)
    email: str = Field(index=True, unique=True, max_length=120)
    is_admin: bool = Field(default=False)

class User(UserBase, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str = Field(max_length=255) # Increased length for modern hashes

    date_created: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    date_modified: datetime.datetime = Field(default_factory=datetime.datetime.utcnow, sa_column_kwargs={"onupdate": datetime.datetime.utcnow})

    # Relationship: One-to-One with Channel
    channel: Optional["Channel"] = Relationship(back_populates="user", sa_relationship_kwargs={"uselist": False})

class UserCreate(UserBase): # For registration payload
    password: str

class UserRead(UserBase): # For API responses
    id: int
    date_created: datetime.datetime
    date_modified: datetime.datetime
    # Potentially add channel_id or basic channel info if frequently needed

class UserUpdate(SQLModel): # For profile updates
    name: Optional[str] = Field(default=None, max_length=50)
    email: Optional[str] = Field(default=None, max_length=120)

# Note: SQLModel automatically makes User table=True a Pydantic model too.
# UserCreate and UserRead are explicitly defined for clarity and distinct fields.
```

##### **1.3. Backend - API Payload Schemas (Pydantic - `schemas/auth.py`, `schemas/user.py`)**
These are largely covered by `UserCreate`, `UserRead`, `UserUpdate` within the SQLModel definition. Additional specific auth-related schemas:

```python
# schemas/auth.py
from pydantic import BaseModel, EmailStr

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel): # For JWT payload content
    username: Optional[str] = None # Or user_id: Optional[int] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str
```

#### 2. Channel Entity

##### **2.1. Concept:**
Represents a user's podcast channel, containing all the metadata required for generating the podcast XML feed.

##### **2.2. Backend - SQLModel Definition (`models/channel.py`)**
```python
from typing import TYPE_CHECKING, Optional, List
from sqlmodel import Field, SQLModel, Relationship
import datetime

if TYPE_CHECKING:
    from .user import User
    from .episode import Episode # Forward reference

class ChannelBase(SQLModel):
    name: str = Field(index=True, max_length=255)
    description: str = Field(default="", max_length=4000) # Max for iTunes
    website: Optional[str] = Field(default=None, max_length=255)
    explicit: bool = Field(default=False)
    image_url_path: Optional[str] = Field(default=None, max_length=512) # Local path, to be converted to absolute URL for client
    copyright_text: Optional[str] = Field(default=None, max_length=255)
    language: str = Field(default="en", max_length=10) # e.g., en, en-US, es
    category: str = Field(default="Technology", max_length=100) # iTunes category
    authors: Optional[str] = Field(default=None, max_length=255)
    authors_email: Optional[str] = Field(default=None, max_length=100) # Not in feed, but useful
    owner_name: Optional[str] = Field(default=None, max_length=255) # For iTunes owner
    owner_email: Optional[str] = Field(default=None, max_length=100) # For iTunes owner

class Channel(ChannelBase, table=True):
    __tablename__ = "channels"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", unique=True, index=True) # One-to-One

    date_created: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    date_modified: datetime.datetime = Field(default_factory=datetime.datetime.utcnow, sa_column_kwargs={"onupdate": datetime.datetime.utcnow})

    # Relationship: One-to-One with User
    user: Optional["User"] = Relationship(back_populates="channel")
    # Relationship: One-to-Many with Episode
    episodes: List["Episode"] = Relationship(back_populates="channel")

class ChannelRead(ChannelBase): # For API responses
    id: int
    user_id: int
    image_url: Optional[str] = None # Absolute URL constructed by the API
    feed_url: Optional[str] = None  # Absolute URL to the podcast feed, constructed by API
    date_created: datetime.datetime
    date_modified: datetime.datetime

class ChannelUpdate(SQLModel): # For channel updates
    name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None, max_length=4000)
    website: Optional[str] = Field(default=None, max_length=255)
    explicit: Optional[bool] = None
    copyright_text: Optional[str] = Field(default=None, max_length=255)
    language: Optional[str] = Field(default=None, max_length=10)
    category: Optional[str] = Field(default=None, max_length=100)
    authors: Optional[str] = Field(default=None, max_length=255)
    authors_email: Optional[str] = Field(default=None, max_length=100)
    owner_name: Optional[str] = Field(default=None, max_length=255)
    owner_email: Optional[str] = Field(default=None, max_length=100)
    # image_url_path is updated via a separate image upload endpoint
```

##### **2.3. Backend - API Payload Schemas (Pydantic - `schemas/channel.py`)**
Largely covered by `ChannelRead` and `ChannelUpdate` in the SQLModel definitions. `ChannelCreate` is not directly exposed via API as channels are typically created automatically during user registration.



#### 3. Episode Entity

##### **3.1. Concept:**
Represents a single podcast episode, usually derived from a YouTube video, including its metadata, audio file reference, and processing status.

##### **3.2. Backend - SQLModel Definition (`models/episode.py`)**
```python
from typing import TYPE_CHECKING, Optional, List as PyList # PyList to avoid conflict with Relationship's List
from sqlmodel import Field, SQLModel, Relationship, Column, JSON # For keywords
import datetime

if TYPE_CHECKING:
    from .channel import Channel # Forward reference

class EpisodeBase(SQLModel):
    youtube_url: str = Field(max_length=512)
    video_id: str = Field(index=True, max_length=30) # e.g., YouTube video ID
    title: str = Field(max_length=255)
    description: Optional[str] = Field(default=None, max_length=4000) # iTunes summary
    subtitle: Optional[str] = Field(default=None, max_length=255) # iTunes subtitle
    # summary field removed, description can be used for iTunes summary.
    # Subtitle is a shorter, punchier version for some podcast clients.
    author: Optional[str] = Field(default=None, max_length=255) # YouTube channel name / video uploader
    original_thumbnail_url: Optional[str] = Field(default=None, max_length=512) # URL from YouTube
    saved_thumbnail_path: Optional[str] = Field(default=None, max_length=512) # Local path
    published_at: Optional[datetime.datetime] = None # YouTube video publish date
    keywords: Optional[PyList[str]] = Field(default=None, sa_column=Column(JSON)) # Store as JSON array in DB
    duration_seconds: Optional[int] = None
    audio_file_path: Optional[str] = Field(default=None, max_length=512) # Local path to audio file
    audio_file_size_bytes: Optional[int] = None
    is_downloaded: bool = Field(default=False)
    transcript: Optional[str] = Field(default=None) # Can be lengthy
    processing_status: str = Field(default="pending", index=True, max_length=30) # e.g., pending, processing_metadata, downloading_audio, completed, failed
    error_message: Optional[str] = Field(default=None, max_length=512)

class Episode(EpisodeBase, table=True):
    __tablename__ = "episodes"

    id: Optional[int] = Field(default=None, primary_key=True)
    channel_id: int = Field(foreign_key="channels.id", index=True)

    date_created: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    date_modified: datetime.datetime = Field(default_factory=datetime.datetime.utcnow, sa_column_kwargs={"onupdate": datetime.datetime.utcnow})

    # Relationship: Many-to-One with Channel
    channel: Optional["Channel"] = Relationship(back_populates="episodes")

class EpisodeCreatePayload(SQLModel): # Payload for submitting a new YouTube URL
    youtube_url: str

class EpisodeRead(EpisodeBase): # For API responses
    id: int
    channel_id: int
    thumbnail_url: Optional[str] = None # Absolute URL to saved thumbnail, constructed by API
    audio_url: Optional[str] = None # Absolute URL to audio file, constructed by API
    date_created: datetime.datetime
    date_modified: datetime.datetime

class EpisodeProcessingStatusUpdate(SQLModel): # For SSE messages
    episode_id: int
    processing_status: str
    progress_percentage: Optional[float] = None # e.g., for download
    message: Optional[str] = None # General message or error details
    title: Optional[str] = None # Useful to show title in notifications
```

##### **3.3. Backend - API Payload Schemas (Pydantic - `schemas/episode.py`)**
Covered by `EpisodeCreatePayload`, `EpisodeRead`, and `EpisodeProcessingStatusUpdate` in the SQLModel definitions.

```typescript
export enum ProcessingStatus {
  PENDING = "pending",
  PROCESSING_METADATA = "processing_metadata",
  DOWNLOADING_THUMBNAIL = "downloading_thumbnail",
  DOWNLOADING_AUDIO = "downloading_audio",
  FETCHING_TRANSCRIPT = "fetching_transcript",
  COMPLETED = "completed",
  FAILED = "failed",
}

export interface Episode {
  id: number;
  channelId: number;
  youtubeUrl: string;
  videoId: string;
  title: string;
  description?: string | null;
  subtitle?: string | null;
  author?: string | null;
  thumbnailUrl?: string | null; // Absolute URL to our served thumbnail
  publishedAt?: string | null; // ISO datetime string from YouTube
  keywords?: string[] | null;
  durationSeconds?: number | null;
  audioUrl?: string | null; // Absolute URL to our served audio
  isDownloaded: boolean;
  transcript?: string | null;
  processingStatus: ProcessingStatus;
  errorMessage?: string | null;
  dateCreated: string; // ISO datetime string
  dateModified: string; // ISO datetime string
}

export interface EpisodeCreateData {
  youtubeUrl: string;
}

// For SSE messages from backend to frontend
export interface EpisodeStatusUpdateMessage {
  episode_id: number; // Snake_case from Python backend
  processing_status: ProcessingStatus;
  progress_percentage?: number | null;
  message?: string | null;
  title?: string | null; // To display in UI notifications
}
```

---


## Frontend Architecture (Next.js 15)

### Frontend Project Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── globals.css
│   │   ├── (marketing)/           # Routes for marketing pages
│   │   │   ├── about/page.tsx     # Static page
│   │   │   ├── contact/page.tsx   # Static page
│   │   │   ├── privacy/page.tsx   # Static page
│   │   │   └── terms/page.tsx     # Static page
│   │   │   └── page.tsx           # Main marketing page
│   │   │   └── layout.tsx         # Main marketing layout (sidebar, navbar)
│   │   ├── (auth)/              # Routes for unauthenticated users
│   │   │   ├── login/page.tsx
│   │   │   ├── register/page.tsx
│   │   │   ├── password-reset/
│   │   │   │   ├── request/page.tsx
│   │   │   │   └── [token]/page.tsx
│   │   │   └── layout.tsx       # Layout for auth pages
│   │   ├── dashboard/           # Routes for authenticated users
│   │   │   ├── settings/
│   │   │   │   ├── profile/page.tsx
│   │   │   │   ├── password/page.tsx
│   │   │   │   ├── channel/page.tsx
│   │   │   │   └── layout.tsx     # Layout for settings section
│   │   │   ├── episodes/
│   │   │   │   ├── add/page.tsx   # Page to add new episode
│   │   │   │   └── [id]/page.tsx  # Optional: Detailed view of a single episode
│   │   │   ├── page.tsx           # Main dashboard (episode list)
│   │   │   └── layout.tsx         # Main authenticated layout (sidebar, navbar)
│   ├── components/
│   │   ├── ui/                    # ShadCN or similar primitive UI components
│   │   ├── forms/
│   │   │   ├── AddEpisodeForm.tsx
│   │   │   ├── ChannelSettingsForm.tsx
│   │   │   ├── AuthForm.tsx          # Combined or individual login/reg forms
│   │   │   ├── ProfileForm.tsx
│   │   │   └── PasswordChangeForm.tsx
│   │   ├── episode/
│   │   │   ├── EpisodeCard.tsx
│   │   │   ├── EpisodeList.tsx
│   │   │   └── EpisodeProcessingStatus.tsx # Displays SSE updates
│   │   └── layout/
│   │       ├── Navbar.tsx
│   │       ├── Sidebar.tsx
│   │       └── Footer.tsx         # For marketing pages
│   ├── lib/
│   │   ├── apiClient.ts           # Fetches data from FastAPI backend
│   │   ├── authClient.ts          # Handles client-side auth logic (token storage, context updates)
│   │   ├── zodSchemas.ts          # Zod schemas for form validation
│   │   └── utils.ts
│   ├── hooks/
│   │   ├── useAuth.ts             # Provides auth state and actions
│   │   ├── useEpisodes.ts         # Manages episode data (fetching, deleting, state for SSE updates)
│   │   └── useSSEConnection.ts    # Manages the EventSource connection
│   ├── contexts/
│   │   └── AuthContext.tsx        # React context for authentication state
│   └── types/
│       └── index.ts               # TypeScript type definitions (API responses, etc.)
├── public/                        # Static assets (images, favicons)
├── tailwind.config.js
├── tsconfig.json
├── next.config.js
└── Dockerfile
```

#### Key Directory Descriptions for the Frontend

- `frontend/`: Contains the main application source code.
- `frontend/src/`: Contains the main application source code.
- `frontend/src/app/`: Contains the main application source code.
- `frontend/src/app/(marketing)/`: Contains the marketing pages.
- `frontend/src/app/(auth)/`: Contains the authentication pages.
- `frontend/src/app/dashboard/`: Contains the dashboard pages.
- `frontend/src/components/`: Contains the components.
- `frontend/src/lib/`: Contains the libraries.
- `frontend/src/hooks/`: Contains the hooks.
- `frontend/src/contexts/`: Contains the contexts.
- `frontend/src/types/`: Contains the types.
- `frontend/public/`: Contains the public assets.

Some aspects to highlight:
- The `(auth)`, `(marketing)`, and `dashboard` route groups are logical.
- SSE connection strategy (direct client-to-FastAPI is preferred over a Next.js proxy for simplicity).
- Explicitly adding pages for profile settings, password change, and potentially a structured settings section.


### Frontend Technology Stack

| Category             | Technology                | Version / Details                     | Description / Purpose                                 | Justification                                                                                                |
| :------------------- | :------------------------ | :------------------------------------ | :---------------------------------------------------- | :----------------------------------------------------------------------------------------------------------- |
| **Languages**        | TypeScript                | ~5.3.x (or latest via Next.js 15)     | Primary language for frontend development.            | Strong typing, improved developer experience, better code maintainability. Standard for modern Next.js.     |
| **Runtime**          | Node.js                   | LTS (e.g., 20.11.1 or latest stable)  | JavaScript runtime for building and developing Next.js. | Required for Next.js. LTS for stability.                                                                   |
| **Frameworks**       | Next.js                   | 15.x (App Router)                     | React framework for server-side rendering, static site generation, routing, etc. | Modern, performant, excellent DX, App Router for new features.                                             |
|                      | React                     | 19.x (or as per Next.js 15)           | Core UI library.                                      | Bundled with Next.js, industry standard for component-based UI.                                              |
| **UI Libraries**     | Tailwind CSS              | ~3.4.x                                | Utility-first CSS framework.                          | Rapid UI development, highly customizable, consistent styling.                                               |
|                      | Shadcn/ui  | Latest                                | Collection of re-usable components built with Radix UI and Tailwind CSS. | Accelerates UI development, accessible, stylable. User can choose this or build custom components.         |
|                      | Framer Motion  | Latest                                | Animation library for React.                          | For creating smooth and modern UI animations as requested.                                                   |
| **State Management** | React Context API         | Bundled with React                    | For simple global state (e.g., auth state).           | Built-in, sufficient for simpler state needs.                                                                |
|                      | Zustand | Latest                                | Lightweight state management libraries.               | For more complex client-side state if Context API becomes cumbersome.                                        |
| **Forms**            | React Hook Form  | Latest                                | Performant, flexible, and extensible forms with easy-to-use validation. | Manages form state and validation efficiently.                                                               |
|                      | Zod                       | Latest                                | TypeScript-first schema declaration and validation.     | For client-side (and potentially shared backend) data validation. Pairs well with React Hook Form.         |
| **API Communication**| Fetch API (Browser)       | N/A                                   | Native browser API for making HTTP requests.          | Built-in, no extra dependencies for basic API calls.                                                         |
|                      | `EventSource` API (Browser)| N/A                                   | Native browser API for Server-Sent Events.            | For real-time status updates from the backend.                                                               |
| **Testing**          | Jest (Recommended)        | Latest                                | JavaScript testing framework.                         | For unit and integration tests of components and utilities. Often configured with Next.js.                   |
|                      | React Testing Library     | Latest                                | Testing utilities for React components.               | Encourages testing components in a user-centric way.                                                         |
|                      | Playwright (Recommended)  | Latest                                | End-to-end testing framework.                         | For testing complete user flows across the application.                                                      |
| **Linting/Formatting**| ESLint                    | Latest                                | Pluggable JavaScript linter.                          | Code quality and consistency. Included with `create-next-app`.                                             |
|                      | Prettier                  | Latest                                | Opinionated code formatter.                           | Consistent code style.                                                                                       |
| **Build Tool**       | Next.js CLI / Webpack/SWC | Bundled                               | Handles building, bundling, and optimization.         | Integrated into Next.js.                                                                                     |
| **Containerization** | Docker                    | Latest                                | For creating a consistent deployment environment.     | Standard for containerizing applications.                                                                    |
| **Monitoring**       | Sentry                    | Latest                                | Application monitoring and error tracking.            | Provides real-time error tracking and performance monitoring, essential for maintaining application health.  |


### Loggin ()

- We will use standard the `logging` module for logging.
- We will later add `Sentry` for error tracking.

### Data Models (file `/project-docs/docs/frontend-data-models.md`)

#### 1. User Entity

##### **1.1. Concept:**
Represents an individual who registers for the application, logs in, and owns a podcast channel.

##### **1.4. Frontend - TypeScript Definitions (`types/user.ts` or `types/index.ts`)**
```typescript
export interface User {
  id: number;
  name: string;
  email: string;
  isAdmin: boolean;
  dateCreated: string; // ISO datetime string
  dateModified: string; // ISO datetime string
  // channelId?: number; // If needed
}

export interface UserCreateData {
  name: string;
  email: string;
  password: string;
}

export interface UserLoginData {
  username: string; // Corresponds to 'name' or 'email' in backend
  password: string;
}

export interface UserUpdateData {
  name?: string;
  email?: string;
}

export interface AuthToken {
  accessToken: string;
  tokenType: string;
}

export interface PasswordChangeData {
  currentPassword: string;
  newPassword: string;
}

export interface PasswordResetRequestData {
  email: string;
}

export interface PasswordResetData {
  token: string;
  newPassword: string;
}
```

#### 2. Channel Entity

##### **2.1. Concept:**
Represents a user's podcast channel, containing all the metadata required for generating the podcast XML feed.

##### **2.4. Frontend - TypeScript Definitions (`types/channel.ts` or `types/index.ts`)**
```typescript
export interface Channel {
  id: number;
  userId: number;
  name: string;
  description: string;
  website?: string | null;
  explicit: boolean;
  imageUrl?: string | null; // Absolute URL for the channel logo
  feedUrl?: string | null; // Absolute URL for the podcast feed
  copyrightText?: string | null;
  language: string;
  category: string;
  authors?: string | null;
  authorsEmail?: string | null;
  ownerName?: string | null;
  ownerEmail?: string | null;
  dateCreated: string; // ISO datetime string
  dateModified: string; // ISO datetime string
}

export interface ChannelUpdateData {
  name?: string;
  description?: string;
  website?: string | null;
  explicit?: boolean;
  copyrightText?: string | null;
  language?: string;
  category?: string;
  authors?: string | null;
  authorsEmail?: string | null;
  ownerName?: string | null;
  ownerEmail?: string | null;
  // Image is handled by a separate FormData upload
}
```

#### 3. Episode Entity

##### **3.1. Concept:**
Represents a single podcast episode, usually derived from a YouTube video, including its metadata, audio file reference, and processing status.


##### **3.4. Frontend - TypeScript Definitions (`types/episode.ts` or `types/index.ts`)**
```typescript
// This enum was correctly provided before:
export enum ProcessingStatus {
  PENDING = "pending",
  PROCESSING_METADATA = "processing_metadata",
  DOWNLOADING_THUMBNAIL = "downloading_thumbnail",
  DOWNLOADING_AUDIO = "downloading_audio",
  FETCHING_TRANSCRIPT = "fetching_transcript",
  COMPLETED = "completed",
  FAILED = "failed",
}

// THIS IS THE MISSING EPISODE INTERFACE FOR THE FRONTEND
export interface Episode {
  id: number;
  channelId: number;
  youtubeUrl: string;
  videoId: string;
  title: string;
  description?: string | null;
  subtitle?: string | null;
  author?: string | null;
  thumbnailUrl?: string | null; // Absolute URL to our served thumbnail (from saved_thumbnail_path)
  // originalThumbnailUrl?: string | null; // Less likely needed by frontend if we serve our own
  publishedAt?: string | null; // ISO datetime string (from YouTube's publish date)
  keywords?: string[] | null;
  durationSeconds?: number | null;
  audioUrl?: string | null; // Absolute URL to our served audio file
  // audioFileSizeMegaBytes?: number | null; // Could be useful, derived from audio_file_size_bytes
  isDownloaded: boolean; // Indicates if the audio file is available on the server
  transcript?: string | null;
  processingStatus: ProcessingStatus;
  errorMessage?: string | null;
  dateCreated: string; // ISO datetime string (when the record was created in our DB)
  dateModified: string; // ISO datetime string (when the record was last modified in our DB)
}

// This was correctly provided before:
export interface EpisodeCreateData {
  youtubeUrl: string;
}

// This was correctly provided before:
// For SSE messages from backend to frontend
export interface EpisodeStatusUpdateMessage {
  episode_id: number; // Snake_case from Python backend, often converted to camelCase in frontend
  processing_status: ProcessingStatus;
  progress_percentage?: number | null;
  message?: string | null;
  title?: string | null; // To display in UI notifications for context
}
```

##### **Key fields in the frontend `Episode` interface and their mapping to the backend `EpisodeRead` schema:**

*   `id`: `EpisodeRead.id`
*   `channelId`: `EpisodeRead.channel_id`
*   `youtubeUrl`: `EpisodeRead.youtube_url`
*   `videoId`: `EpisodeRead.video_id`
*   `title`: `EpisodeRead.title`
*   `description`: `EpisodeRead.description`
*   `subtitle`: `EpisodeRead.subtitle`
*   `author`: `EpisodeRead.author`
*   `thumbnailUrl`: This will be the absolute URL constructed by the backend based on `EpisodeRead.saved_thumbnail_path` and served via the static file server. The backend's `EpisodeRead` schema should include this transformed `thumbnail_url`.
*   `publishedAt`: `EpisodeRead.published_at`
*   `keywords`: `EpisodeRead.keywords`
*   `durationSeconds`: `EpisodeRead.duration_seconds`
*   `audioUrl`: This will be the absolute URL constructed by the backend based on `EpisodeRead.audio_file_path`. The backend's `EpisodeRead` schema should include this transformed `audio_url`.
*   `isDownloaded`: `EpisodeRead.is_downloaded`
*   `transcript`: `EpisodeRead.transcript`
*   `processingStatus`: `EpisodeRead.processing_status` (ensure the enum values match)
*   `errorMessage`: `EpisodeRead.error_message`
*   `dateCreated`: `EpisodeRead.date_created`
*   `dateModified`: `EpisodeRead.date_modified`

I've updated the `Episode` interface above to reflect what the frontend would typically consume from an API response that corresponds to the backend's `EpisodeRead` schema (which itself should construct the absolute URLs for `thumbnail_url` and `audio_url`).


### State Management (file `/project-docs/ideation/project-ideation-10-state-management.md`)

#### Decision Flow Summary for Developers/AI:

This detailed breakdown should provide clear guidance on how to approach state management throughout the frontend application, leveraging Zustand for global concerns and React's built-in mechanisms for more localized state.

1. Is this state for a single UI element's presentation (e.g., dropdown open)? -> Local State (useState).
2. Is this state for a form's inputs and validation? -> React Hook Form (uses local state internally) + Zod for schemas.
3. Does this state need to be shared between a parent and a few direct children, or within a clearly defined subtree, and isn't needed elsewhere? -> React Context API (if prop drilling is too much) OR Prop Drilling (if simple).
4. Is this user session data (auth, profile)? -> Global State (Zustand authStore).
5. Are these application-wide notifications? -> Global State (Zustand notificationStore).
6. Is this data fetched from the API and used by multiple, unrelated components across different routes? (e.g., the list of all episodes for a user, updated by SSE) -> Global State (Zustand episodeStore).
7. Is the state logic complex and benefits from centralized actions/reducers, even if not used everywhere? -> Consider Global State (Zustand) for better organization.


### Frontend Interactions with Backend (file `/project-docs/ideation/project-ideation-11-frontend-interactions-wtih-backend.md`)

This list covers the primary interactions. As development progresses, more granular or specific internal API calls might emerge, but these form the core contract between the Next.js frontend and the FastAPI backend.


**Frontend Need / User Action**           | **Backend API Endpoint (FastAPI)**                     | **HTTP Method** | **Request Payload (Frontend Sends)**                                 | **Response Payload (Backend Sends)**                                  | **Primary Purpose**                                                                                                |
| :--------------------------------------- | :----------------------------------------------------- | :-------------- | :----------------------------------------------------------------- | :-------------------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------------- |
| **Authentication & Users**               |                                                        |                 |                                                                    |                                                                       |                                                                                                                    |
| User registers a new account             | `/api/v1/auth/register`                                | `POST`          | `UserCreateData` (name, email, password)                           | `UserRead` (user details without password)                            | Create a new user and their default channel.                                                                       |
| User logs in                             | `/api/v1/auth/token`                                   | `POST`          | `FormData` (`username`, `password`) (for OAuth2PasswordRequestForm) | `AuthToken` (access_token, token_type)                                | Authenticate user and issue a JWT.                                                                                 |
| User logs out                            | *No direct API call needed for logout if JWT is client-only. Backend might have an optional endpoint to invalidate server-side session/token if implemented.* | N/A             | N/A                                                                | N/A                                                                   | Client clears JWT.                                                                                                 |
| Fetch current authenticated user's profile | `/api/v1/users/me`                                     | `GET`           | JWT in Authorization header                                        | `UserRead`                                                            | Get details of the logged-in user.                                                                                 |
| Update current user's profile            | `/api/v1/users/me`                                     | `PUT`           | `UserUpdateData` (name, email), JWT in header                      | `UserRead` (updated user details)                                     | Modify user's name or email.                                                                                       |
| User requests password reset             | `/api/v1/auth/password-reset/request`                  | `POST`          | `PasswordResetRequestData` (email)                                 | `200 OK` (generic success message)                                    | Initiate password reset flow by sending an email with a reset token.                                               |
| User resets password with token          | `/api/v1/auth/password-reset/confirm`                  | `POST`          | `PasswordResetData` (token, new_password)                          | `200 OK` (generic success message)                                    | Set a new password using a valid reset token.                                                                      |
| User changes their password (logged in)  | `/api/v1/users/me/password`                            | `PUT`           | `PasswordChangeData` (current_password, new_password), JWT in header | `200 OK` (generic success message)                                    | Allow logged-in user to change their password.                                                                     |
| **Channel Management**                   |                                                        |                 |                                                                    |                                                                       |                                                                                                                    |
| Fetch current user's channel details     | `/api/v1/channels/me`                                  | `GET`           | JWT in Authorization header                                        | `ChannelRead` (includes constructed `image_url` and `feed_url`)       | Get metadata for the logged-in user's podcast channel.                                                             |
| Update current user's channel metadata   | `/api/v1/channels/me`                                  | `PUT`           | `ChannelUpdateData` (name, description, etc.), JWT in header     | `ChannelRead` (updated channel details)                               | Modify textual information of the podcast channel.                                                                 |
| Upload/Change channel logo image         | `/api/v1/channels/me/image`                            | `POST`          | `FormData` (containing the image file), JWT in header              | `ChannelRead` (updated channel details with new `image_url`)          | Upload a new logo for the podcast channel.                                                                         |
| **Episode Management**                   |                                                        |                 |                                                                    |                                                                       |                                                                                                                    |
| Submit a new YouTube URL for processing  | `/api/v1/episodes`                                     | `POST`          | `EpisodeCreateData` (youtube_url), JWT in header                   | `EpisodeRead` (initial episode data with `id` and `processing_status="pending"`) | Start the background process of converting a YouTube video to a podcast episode.                                     |
| Fetch list of episodes for user's channel| `/api/v1/episodes`                                     | `GET`           | JWT in Authorization header                                        | `List[EpisodeRead]` (includes constructed `thumbnail_url`, `audio_url`) | Get all episodes associated with the user's channel.                                                               |
| Fetch details of a specific episode      | `/api/v1/episodes/{episode_id}`                        | `GET`           | JWT in Authorization header                                        | `EpisodeRead`                                                         | Get detailed information for a single episode (might be redundant if list provides all).                           |
| Delete an episode                        | `/api/v1/episodes/{episode_id}`                        | `DELETE`        | JWT in Authorization header                                        | `204 No Content` or success message                                   | Remove an episode and its associated files.                                                                        |
| **Real-time Status Updates (SSE)**       |                                                        |                 |                                                                    |                                                                       |                                                                                                                    |
| Connect to episode status stream         | `/api/v1/episodes/status-stream`                       | `GET`           | JWT (likely via cookie for `EventSource` or query param if necessary) | `text/event-stream` (SSE messages of type `EpisodeStatusUpdateMessage`) | Establish a connection to receive real-time updates on episode processing.                                         |
| **Podcast Feed (Public, No Auth)**       |                                                        |                 |                                                                    |                                                                       |                                                                                                                    |
| Access a user's public podcast XML feed  | `/api/v1/podcasts/{user_identifier}/feed.xml`          | `GET`           | None                                                               | `application/xml` (the podcast RSS feed)                              | Allow podcast clients and users to fetch the generated podcast feed. (`user_identifier` could be user ID or username). |
| **Static Media Serving (Public/Semi-Public)** |                                                     |                 |                                                                    |                                                                       |                                                                                                                    |
| Access a downloaded episode audio file   | `/media/audio/{video_id}.m4a` (example path)         | `GET`           | None                                                               | Audio file (`audio/mp4` or similar)                                   | Serve the processed audio file for an episode.                                                                     |
| Access a saved episode thumbnail         | `/media/thumbnails/{video_id}.jpg` (example path)      | `GET`           | None                                                               | Image file (`image/jpeg` or similar)                                  | Serve the downloaded thumbnail for an episode.                                                                     |
| Access a channel logo                    | `/media/channel_logos/{user_identifier}.jpg` (example) | `GET`           | None                                                               | Image file (`image/jpeg` or similar)                                  | Serve the uploaded logo for a channel.                                                                             |

#### **Key Considerations for API Interactions:**

1.  **Authentication:** All private endpoints (related to user-specific data, channel management, episode submission) MUST be protected and require a valid JWT in the `Authorization: Bearer <token>` header. The FastAPI backend will validate this token.
2.  **Error Handling:** The frontend must be prepared to handle various HTTP error codes (400 for bad request/validation errors, 401 for unauthorized, 403 for forbidden, 404 for not found, 500 for server errors) and display appropriate messages to the user. The backend should return error details in a consistent JSON format (e.g., `{"detail": "Error message"}`).
3.  **Data Validation:**
    *   **Backend:** FastAPI (with Pydantic) will perform rigorous validation on all incoming request payloads.
    *   **Frontend:** Client-side validation (e.g., with Zod and React Hook Form) should be implemented to provide immediate feedback to the user before an API call is made, but backend validation is the ultimate source of truth.
4.  **Payload Consistency:** TypeScript types on the frontend (`UserCreateData`, `Episode`, etc.) should closely mirror the Pydantic schemas on the backend (`UserCreate`, `EpisodeRead`, etc.) to ensure smooth data transfer. Small transformations (e.g., snake_case to camelCase) might be handled in the `apiClient.ts`.
5.  **URL Construction for Media/Feeds:**
    *   The backend's `ChannelRead` and `EpisodeRead` response schemas should dynamically construct absolute URLs for `image_url`, `feed_url`, `thumbnail_url`, and `audio_url` by prepending the server's base URL (from config) to the stored relative paths. This makes it easier for the frontend as it doesn't have to guess or build these URLs.
6.  **SSE Connection Management:** The frontend `useSSEConnection.ts` hook will manage the lifecycle of the `EventSource` connection. The backend SSE endpoint needs to handle client authentication for the connection (cookie-based is often easiest for `EventSource` if the main app uses cookie auth for sessions, or a short-lived token via query param can be an alternative if header-based JWT is the primary auth).
7.  **Idempotency:** For operations like `DELETE`, ensure they are idempotent.
8.  **Optimistic Updates:** For actions like deleting an episode or submitting a new one, the frontend might perform optimistic UI updates (e.g., immediately removing an item from a list) and then revert or confirm based on the API response. This is managed in the Zustand store or relevant React hooks.


### Error Handling & Retries on the Frontend (file `/project-docs/ideation/project-ideation-12-error-handling-retries.md`)

#### Summary of Error Handling Flow:

This layered approach ensures that users receive immediate contextual feedback where possible, and a global system catches and notifies about any other errors, while developers get the necessary details for debugging. The retry logic improves resilience against transient network or server issues for appropriate requests.

1. `Component/Hook` initiates an API call via `apiClient.ts`.
2. `apiClient.ts` executes the request.
    - If retry logic is configured for this request type/error:
        - Automatic retries are attempted if initial request fails under specified conditions.
3. If the request ultimately fails (after retries or if no retries for this type):
    - `apiClient.ts` standardizes the error.
    - The promise returned by `apiClient.ts` is rejected with the standardized error.
4. Specific Handling (Optional):
    - The calling component/hook can try...catch this error.
    - If caught, it can update its local state to display context-specific error messages (e.g., inline form errors).
5. Global Handling (Default):
    - If the error is not caught by the component (or is re-thrown), the global error interceptor in `apiClient.ts` catches it.
    - The global interceptor dispatches an action to `notificationStore` to display a user-friendly toast/banner.
    - The global interceptor logs the detailed error to the console and (in production) to a monitoring service.
