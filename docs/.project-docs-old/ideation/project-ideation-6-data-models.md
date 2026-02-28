# Data Models

## Prompt used to generate this file
```markdown
Lets now focus on Data Models. Conduct the analysis and provide your output for both, backend and frontend:

1. Define the main objects/concepts the application works with. Repeat subsection for each key entity.
2. Define API payload schemas here only if they are distinct from core entities AND not fully detailed under the API endpoint definitions in the API Reference section. Prefer detailing request/response schemas directly with their APIs where possible. This section is for complex, reusable payload structures that might be used across multiple internal APIs or differ significantly from core persisted entities
3. If using a database, define table structures or document database schemas. repeat as needed
```

---

Okay, let's define the data models for the backend (FastAPI with SQLModel) and the corresponding structures for the frontend (Next.js with TypeScript).

For each key entity, we'll cover:
1.  **Concept:** A brief description of what the entity represents.
2.  **Backend - SQLModel Definition:** The table structure and ORM model using SQLModel (Python). This also serves as a base Pydantic schema.
3.  **Backend - API Payload Schemas (Pydantic):** Specific Pydantic schemas for API requests and responses, especially where they differ from the direct SQLModel (e.g., for creation, updates, or read views that omit certain fields or add computed ones).
4.  **Frontend - TypeScript Definitions:** Corresponding TypeScript interfaces or types for use in the Next.js application.

---

## 1. User Entity

### **1.1. Concept:**
Represents an individual who registers for the application, logs in, and owns a podcast channel.

### **1.2. Backend - SQLModel Definition (`models/user.py`)**
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

### **1.3. Backend - API Payload Schemas (Pydantic - `schemas/auth.py`, `schemas/user.py`)**
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

### **1.4. Frontend - TypeScript Definitions (`types/user.ts` or `types/index.ts`)**
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

---

## 2. Channel Entity

### **2.1. Concept:**
Represents a user's podcast channel, containing all the metadata required for generating the podcast XML feed.

### **2.2. Backend - SQLModel Definition (`models/channel.py`)**
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

### **2.3. Backend - API Payload Schemas (Pydantic - `schemas/channel.py`)**
Largely covered by `ChannelRead` and `ChannelUpdate` in the SQLModel definitions. `ChannelCreate` is not directly exposed via API as channels are typically created automatically during user registration.

### **2.4. Frontend - TypeScript Definitions (`types/channel.ts` or `types/index.ts`)**
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

---

## 3. Episode Entity

### **3.1. Concept:**
Represents a single podcast episode, usually derived from a YouTube video, including its metadata, audio file reference, and processing status.

### **3.2. Backend - SQLModel Definition (`models/episode.py`)**
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

### **3.3. Backend - API Payload Schemas (Pydantic - `schemas/episode.py`)**
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

### **3.4. Frontend - TypeScript Definitions (`types/episode.ts` or `types/index.ts`)**
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

#### **Key fields in the frontend `Episode` interface and their mapping to the backend `EpisodeRead` schema:**

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


---

This detailed breakdown should provide a clear definition for the data models and schemas across both the backend and frontend, facilitating consistent data handling and API interactions.
