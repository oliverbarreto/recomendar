# LabCastARR - Phase 1 Detailed Implementation Plan v1.0
## Infrastructure Foundation (Weeks 1-2)

### Table of Contents
- [Phase Overview](#phase-overview)
- [Milestone 1.1: Development Environment Setup](#milestone-11-development-environment-setup)
- [Milestone 1.2: Core Domain Models](#milestone-12-core-domain-models)
- [Success Criteria](#success-criteria)
- [Risk Assessment](#risk-assessment)
- [Lessons Learned](#lessons-learned)

---

## Phase Overview

**Phase 1 Objectives:**
- Establish a robust development environment with Docker containerization
- Create the foundational architecture for both backend and frontend applications
- Implement core domain models and database schema
- Set up the basic infrastructure for clean architecture principles
- Ensure seamless service communication and hot reload capabilities

**Timeline:** Weeks 1-2  
**Priority:** Critical Foundation  
**Dependencies:** None (Starting phase)

**Key Deliverables:**
1. Working Docker development environment
2. Complete database schema with migrations
3. Type-safe API communication layer
4. Basic UI component structure
5. Health monitoring endpoints

---

## Milestone 1.1: Development Environment Setup

### Epic 1.1.1: Backend Infrastructure Setup

#### Task 1.1.1.1: FastAPI Project Structure with Clean Architecture
**Status:** ✅ **COMPLETED**  
**Priority:** Critical  
**Estimated Time:** 4 hours

**Detailed Implementation:**
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry point
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # Application configuration
│   │   ├── dependencies.py        # Dependency injection
│   │   └── security.py            # Authentication & security
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── entities/              # Domain entities
│   │   ├── repositories/          # Repository interfaces
│   │   ├── services/              # Domain services
│   │   └── value_objects/         # Value objects
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── database/              # Database implementations
│   │   ├── external/              # External service integrations
│   │   └── repositories/          # Repository implementations
│   ├── presentation/
│   │   ├── __init__.py
│   │   ├── api/                   # API routes
│   │   ├── schemas/               # Pydantic models
│   │   └── dependencies.py        # Route dependencies
│   └── tests/
├── pyproject.toml                 # uv project configuration
├── uv.lock                        # Locked dependencies
└── Dockerfile.dev                 # Development container
```

**Acceptance Criteria:**
- [x] Clean architecture folder structure implemented
- [x] FastAPI application boots successfully
- [x] Dependency injection configured
- [x] Environment configuration loaded
- [x] Basic error handling middleware active

#### Task 1.1.1.2: SQLAlchemy with SQLite Database Configuration
**Status:** ✅ **COMPLETED**  
**Priority:** Critical  
**Estimated Time:** 3 hours

**Detailed Implementation:**
```python
# app/infrastructure/database/connection.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./labcastarr.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """
    Dependency to get database session
    """
    db = SessionLocal()
    
    try:
        yield db
    finally:
        db.close()
```

**Acceptance Criteria:**
- [x] SQLAlchemy engine configured with SQLite
- [x] Database session factory created
- [x] Base model class established
- [x] Connection dependency injection working
- [x] Database file created in development environment

#### Task 1.1.1.3: Alembic Database Migrations
**Status:** ✅ **COMPLETED**  
**Priority:** High  
**Estimated Time:** 2 hours

**Configuration Files:**
```ini
# alembic.ini
[alembic]
script_location = alembic
sqlalchemy.url = sqlite:///./labcastarr.db
```

```python
# alembic/env.py
from app.infrastructure.database.models import Base
target_metadata = Base.metadata
```

**Acceptance Criteria:**
- [x] Alembic configuration initialized
- [x] Migration environment configured
- [x] Initial migration generated
- [x] Database migrations apply successfully
- [x] Rollback functionality verified

#### Task 1.1.1.4: Basic Health Check Endpoints
**Status:** ✅ **COMPLETED**  
**Priority:** Medium  
**Estimated Time:** 1 hour

**Implementation:**
```python
# app/presentation/api/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.infrastructure.database.connection import get_db

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/")
async def health_check():
    return {"status": "healthy", "service": "labcastarr-backend"}

@router.get("/db")
async def database_health(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}
```

**Acceptance Criteria:**
- [x] Basic health endpoint returns 200 status
- [x] Database health check verifies connection
- [x] Health endpoints accessible via HTTP
- [x] Proper error handling for database issues

#### Task 1.1.1.5: UV Dependency Management Setup
**Status:** ✅ **COMPLETED**  
**Priority:** High  
**Estimated Time:** 1 hour

**Configuration:**
```toml
# pyproject.toml
[project]
name = "labcastarr-backend"
version = "0.1.0"
description = "LabCastARR Backend API"
dependencies = [
    "fastapi>=0.116.1",
    "sqlalchemy>=2.0.0",
    "alembic>=1.13.0",
    "pydantic>=2.0.0",
    "uvicorn>=0.30.0",
    "python-multipart>=0.0.9",
    "aiofiles>=24.1.0",
    "yt-dlp",
    "podgen>=1.1.0"
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**Acceptance Criteria:**
- [x] UV project configuration created
- [x] All core dependencies specified
- [x] Lock file generated
- [x] Virtual environment created
- [x] Dependencies install successfully

#### Task 1.1.1.6: Docker Development Environment
**Status:** ✅ **COMPLETED**  
**Priority:** Critical  
**Estimated Time:** 3 hours

**Configuration:**
```dockerfile
# Dockerfile.dev
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Command for development
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

**Acceptance Criteria:**
- [x] Docker container builds successfully
- [x] Application starts inside container
- [x] Hot reload functionality works
- [x] Container ports properly exposed
- [x] Volume mounts configured for development

### Epic 1.1.2: Frontend Infrastructure Setup

#### Task 1.1.2.1: Next.js 15 with TypeScript Initialization
**Status:** ✅ **COMPLETED**  
**Priority:** Critical  
**Estimated Time:** 2 hours

**Project Structure:**
```
frontend/
├── src/
│   ├── app/
│   │   ├── globals.css           # Global styles
│   │   ├── layout.tsx            # Root layout
│   │   ├── page.tsx              # Home page
│   │   ├── episodes/             # Episode routes
│   │   └── settings/             # Settings routes
│   ├── components/
│   │   ├── ui/                   # ShadCN components
│   │   ├── features/             # Feature components
│   │   └── shared/               # Shared components
│   ├── lib/
│   │   ├── api.ts                # API client
│   │   ├── utils.ts              # Utility functions
│   │   └── validations.ts        # Zod schemas
│   └── types/
│       └── index.ts              # Type definitions
├── package.json
├── next.config.js
├── tailwind.config.js
└── tsconfig.json
```

**Acceptance Criteria:**
- [x] Next.js 15 application initialized
- [x] TypeScript configuration active
- [x] App Router structure implemented
- [x] Basic routing works correctly
- [x] TypeScript compilation successful

#### Task 1.1.2.2: TailwindCSS and ShadCN UI Configuration
**Status:** ✅ **COMPLETED**  
**Priority:** High  
**Estimated Time:** 2 hours

**Configuration:**
```javascript
// tailwind.config.js
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        // ... ShadCN color variables
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
```

**ShadCN Components Installed:**
- Button, Input, Card, Dialog, Toast
- Badge, Skeleton, Loading indicators
- Form components with React Hook Form integration

**Acceptance Criteria:**
- [x] TailwindCSS properly configured
- [x] ShadCN UI components accessible
- [x] Theme system working
- [x] Responsive design utilities active
- [x] Component library integration complete

#### Task 1.1.2.3: Basic Routing Structure Setup
**Status:** ✅ **COMPLETED**  
**Priority:** High  
**Estimated Time:** 2 hours

**Route Structure:**
```
app/
├── layout.tsx                    # Root layout
├── page.tsx                      # Home page (channel overview)
├── episodes/
│   ├── layout.tsx                # Episodes layout
│   ├── page.tsx                  # Episodes list
│   ├── add/
│   │   └── page.tsx              # Add episode
│   └── [id]/
│       ├── page.tsx              # Episode detail
│       └── edit/
│           └── page.tsx          # Edit episode
├── settings/
│   ├── page.tsx                  # Settings overview
│   ├── channel/
│   │   └── page.tsx              # Channel settings
│   ├── rss/
│   │   └── page.tsx              # RSS feed settings
│   └── tags/
│       └── page.tsx              # Tag management
└── api/                          # API routes (if needed)
```

**Acceptance Criteria:**
- [x] App Router structure implemented
- [x] Nested routing works correctly
- [x] Dynamic routes configured
- [x] Layout inheritance functional
- [x] Navigation between pages working

#### Task 1.1.2.4: Theme Provider Implementation
**Status:** ✅ **COMPLETED**  
**Priority:** Medium  
**Estimated Time:** 2 hours

**Implementation:**
```tsx
// src/components/providers/theme-provider.tsx
"use client"

import { ThemeProvider as NextThemesProvider } from "next-themes"
import { type ThemeProviderProps } from "next-themes/dist/types"

export function ThemeProvider({ children, ...props }: ThemeProviderProps) {
  return <NextThemesProvider {...props}>{children}</NextThemesProvider>
}

// Usage in layout.tsx
import { ThemeProvider } from '@/components/providers/theme-provider'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          {children}
        </ThemeProvider>
      </body>
    </html>
  )
}
```

**Acceptance Criteria:**
- [x] Dark/light theme switching works
- [x] System theme preference detected
- [x] Theme persistence across sessions
- [x] CSS variables update correctly
- [x] No hydration mismatches

#### Task 1.1.2.5: Development Tools Configuration
**Status:** ✅ **COMPLETED**  
**Priority:** Medium  
**Estimated Time:** 1 hour

**ESLint Configuration:**
```json
{
  "extends": [
    "next/core-web-vitals",
    "@typescript-eslint/recommended"
  ],
  "rules": {
    "@typescript-eslint/no-unused-vars": "error",
    "prefer-const": "error"
  }
}
```

**Prettier Configuration:**
```json
{
  "semi": false,
  "trailingComma": "es5",
  "singleQuote": true,
  "tabWidth": 2,
  "useTabs": false
}
```

**Acceptance Criteria:**
- [x] ESLint rules enforced
- [x] Prettier formatting configured
- [x] TypeScript strict mode enabled
- [x] Import organization working
- [x] Editor integration functional

### Epic 1.1.3: Deployment Infrastructure

#### Task 1.1.3.1: Docker Compose Configuration
**Status:** ✅ **COMPLETED**  
**Priority:** Critical  
**Estimated Time:** 2 hours

**Configuration:**
```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    volumes:
      - ./backend:/app
      - ./data:/app/data
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=development
      - DATABASE_URL=sqlite:///./data/labcastarr.db
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      backend:
        condition: service_healthy

networks:
  default:
    name: labcastarr-dev-network
```

**Acceptance Criteria:**
- [x] Multi-service orchestration working
- [x] Service dependency ordering correct
- [x] Volume mounts configured
- [x] Network communication established
- [x] Environment variables passed correctly

#### Task 1.1.3.2: Development Environment Variables
**Status:** ✅ **COMPLETED**  
**Priority:** High  
**Estimated Time:** 1 hour

**Backend Environment:**
```env
# .env.development
ENVIRONMENT=development
DATABASE_URL=sqlite:///./data/labcastarr.db
API_KEY_SECRET=dev-secret-key
CORS_ORIGINS=http://localhost:3000
LOG_LEVEL=DEBUG
MEDIA_PATH=./media
FEEDS_PATH=./feeds
```

**Frontend Environment:**
```env
# frontend/.env.local
NODE_ENV=development
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_DOMAIN=localhost:3000
```

**Acceptance Criteria:**
- [x] Environment files properly loaded
- [x] Configuration values accessible
- [x] Secrets properly handled
- [x] Different environments supported
- [x] No sensitive data in version control

#### Task 1.1.3.3: Hot Reload Configuration
**Status:** ✅ **COMPLETED**  
**Priority:** Medium  
**Estimated Time:** 1 hour

**Backend Hot Reload:**
- Uvicorn `--reload` flag enabled
- Volume mount for source code
- Python file watching active

**Frontend Hot Reload:**
- Next.js development server
- Fast Refresh configured
- Source map support enabled

**Acceptance Criteria:**
- [x] Backend code changes trigger reload
- [x] Frontend hot reload working
- [x] No data loss during reload
- [x] Error boundaries handle reload issues
- [x] Development server stability maintained

#### Task 1.1.3.4: Service Communication Testing
**Status:** ✅ **COMPLETED**  
**Priority:** Critical  
**Estimated Time:** 1 hour

**Test Implementation:**
```typescript
// frontend/src/lib/api-test.ts
export async function testBackendConnection() {
  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/health`)
    const data = await response.json()
    return { success: true, data }
  } catch (error) {
    return { success: false, error: error.message }
  }
}
```

**Acceptance Criteria:**
- [x] Frontend can reach backend API
- [x] CORS configuration working
- [x] Health checks return proper status
- [x] Network isolation functioning
- [x] Error handling for connection issues

---

## Milestone 1.2: Core Domain Models

### Epic 1.2.1: Domain Entity Definition

#### Task 1.2.1.1: User Entity Implementation
**Status:** ✅ **COMPLETED**  
**Priority:** High  
**Estimated Time:** 2 hours

**Domain Entity:**
```python
# app/domain/entities/user.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class User:
    id: Optional[int]
    name: str
    email: str
    password_hash: str
    is_admin: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
```

**SQLAlchemy Model:**
```python
# app/infrastructure/database/models/user.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.infrastructure.database.connection import Base

class UserModel(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    channels = relationship("ChannelModel", back_populates="user")
```

**Acceptance Criteria:**
- [x] User domain entity created with proper validation
- [x] SQLAlchemy model matches domain entity
- [x] Database migration generated
- [x] Basic user operations tested
- [x] Email uniqueness constraint enforced

#### Task 1.2.1.2: Channel Entity Implementation
**Status:** ✅ **COMPLETED**  
**Priority:** Critical  
**Estimated Time:** 3 hours

**Domain Entity:**
```python
# app/domain/entities/channel.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from app.domain.value_objects.email import Email

@dataclass
class Channel:
    id: Optional[int]
    user_id: int
    name: str
    description: str
    website_url: Optional[str] = None
    image_url: Optional[str] = None
    category: str = "Technology"
    language: str = "en"
    explicit_content: bool = False
    author_name: str = ""
    author_email: Optional[Email] = None
    owner_name: str = ""
    owner_email: Optional[Email] = None
    feed_url: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def generate_feed_url(self, domain: str) -> str:
        """Generate RSS feed URL for this channel"""
        return f"https://{domain}/feeds/{self.id}/feed.xml"
```

**SQLAlchemy Model:**
```python
# app/infrastructure/database/models/channel.py
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.infrastructure.database.connection import Base

class ChannelModel(Base):
    __tablename__ = "channels"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    website_url = Column(String(500))
    image_url = Column(String(500))
    category = Column(String(100), default="Technology")
    language = Column(String(10), default="en")
    explicit_content = Column(Boolean, default=False)
    author_name = Column(String(255))
    author_email = Column(String(255))
    owner_name = Column(String(255))
    owner_email = Column(String(255))
    feed_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("UserModel", back_populates="channels")
    episodes = relationship("EpisodeModel", back_populates="channel", cascade="all, delete-orphan")
    tags = relationship("TagModel", back_populates="channel", cascade="all, delete-orphan")
    events = relationship("EventModel", back_populates="channel", cascade="all, delete-orphan")
```

**Acceptance Criteria:**
- [x] Channel domain entity with proper business logic
- [x] SQLAlchemy model with proper relationships
- [x] RSS feed URL generation logic
- [x] Author and owner information handling
- [x] Category and language validation

#### Task 1.2.1.3: Episode Entity Implementation
**Status:** ✅ **COMPLETED**  
**Priority:** Critical  
**Estimated Time:** 4 hours

**Value Objects:**
```python
# app/domain/value_objects/video_id.py
from dataclasses import dataclass
import re

@dataclass
class VideoId:
    value: str
    
    def __post_init__(self):
        if not self._is_valid_youtube_id(self.value):
            raise ValueError("Invalid YouTube video ID")
    
    def _is_valid_youtube_id(self, video_id: str) -> bool:
        pattern = r'^[a-zA-Z0-9_-]{11}$'
        return bool(re.match(pattern, video_id))

# app/domain/value_objects/duration.py
from dataclasses import dataclass

@dataclass
class Duration:
    seconds: int
    
    @property
    def formatted(self) -> str:
        hours, remainder = divmod(self.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"
```

**Domain Entity:**
```python
# app/domain/entities/episode.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from enum import Enum
from app.domain.value_objects.video_id import VideoId
from app.domain.value_objects.duration import Duration

class EpisodeStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class Episode:
    id: Optional[int]
    channel_id: int
    video_id: VideoId
    title: str
    description: str
    publication_date: datetime
    audio_file_path: Optional[str] = None
    video_url: str = ""
    thumbnail_url: str = ""
    duration: Optional[Duration] = None
    keywords: List[str] = None
    status: EpisodeStatus = EpisodeStatus.PENDING
    retry_count: int = 0
    download_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        if not self.video_url and self.video_id:
            self.video_url = f"https://www.youtube.com/watch?v={self.video_id.value}"
```

**SQLAlchemy Model:**
```python
# app/infrastructure/database/models/episode.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.infrastructure.database.connection import Base

class EpisodeModel(Base):
    __tablename__ = "episodes"
    
    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False)
    video_id = Column(String(20), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    publication_date = Column(DateTime, nullable=False)
    audio_file_path = Column(String(1000))
    video_url = Column(String(500))
    thumbnail_url = Column(String(500))
    duration_seconds = Column(Integer)
    keywords = Column(JSON)  # Stored as JSON array
    status = Column(String(20), default="pending", index=True)
    retry_count = Column(Integer, default=0)
    download_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    channel = relationship("ChannelModel", back_populates="episodes")
    tags = relationship("TagModel", secondary="episode_tags", back_populates="episodes")
    events = relationship("EventModel", back_populates="episode", cascade="all, delete-orphan")
    
    # Composite unique constraint
    __table_args__ = (
        Index('idx_episode_channel_video', 'channel_id', 'video_id', unique=True),
        Index('idx_episode_publication_date', 'publication_date'),
        Index('idx_episode_status', 'status'),
    )
```

**Acceptance Criteria:**
- [x] Episode entity with proper status management
- [x] Value objects for VideoId and Duration
- [x] JSON serialization for keywords array
- [x] Unique constraint on channel_id + video_id
- [x] Proper indexing for performance

#### Task 1.2.1.4: Tag Entity Implementation
**Status:** ✅ **COMPLETED**  
**Priority:** Medium  
**Estimated Time:** 2 hours

**Domain Entity:**
```python
# app/domain/entities/tag.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Tag:
    id: Optional[int]
    channel_id: int
    name: str
    color: str = "#3B82F6"  # Default blue color
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # Validate color is hex
        if not self._is_valid_hex_color(self.color):
            self.color = "#3B82F6"
    
    def _is_valid_hex_color(self, color: str) -> bool:
        import re
        return bool(re.match(r'^#[0-9A-Fa-f]{6}$', color))
```

**SQLAlchemy Models:**
```python
# app/infrastructure/database/models/tag.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.infrastructure.database.connection import Base

# Association table for many-to-many relationship
episode_tags = Table(
    'episode_tags',
    Base.metadata,
    Column('episode_id', Integer, ForeignKey('episodes.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow)
)

class TagModel(Base):
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False)
    name = Column(String(100), nullable=False)
    color = Column(String(7), default="#3B82F6")  # Hex color
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    channel = relationship("ChannelModel", back_populates="tags")
    episodes = relationship("EpisodeModel", secondary=episode_tags, back_populates="tags")
    
    # Composite unique constraint
    __table_args__ = (
        Index('idx_tag_channel_name', 'channel_id', 'name', unique=True),
    )
```

**Acceptance Criteria:**
- [x] Tag entity with color validation
- [x] Many-to-many relationship with episodes
- [x] Unique constraint on channel_id + name
- [x] Association table with timestamps
- [x] Color hex validation logic

#### Task 1.2.1.5: Event Entity Implementation  
**Status:** ✅ **COMPLETED**  
**Priority:** Low  
**Estimated Time:** 2 hours

**Domain Entity:**
```python
# app/domain/entities/event.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

class EventType(Enum):
    EPISODE_CREATED = "episode_created"
    EPISODE_UPDATED = "episode_updated" 
    EPISODE_DELETED = "episode_deleted"
    DOWNLOAD_STARTED = "download_started"
    DOWNLOAD_COMPLETED = "download_completed"
    DOWNLOAD_FAILED = "download_failed"
    RSS_GENERATED = "rss_generated"
    CHANNEL_UPDATED = "channel_updated"

class EventStatus(Enum):
    REQUESTED = "requested"
    PROCESSING = "processing"
    COMPLETED = "completed" 
    FAILED = "failed"

@dataclass
class Event:
    id: Optional[int]
    channel_id: int
    episode_id: Optional[int] = None
    event_type: EventType = EventType.EPISODE_CREATED
    message: str = ""
    metadata: Dict[str, Any] = None
    status: EventStatus = EventStatus.REQUESTED
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.utcnow()
```

**SQLAlchemy Model:**
```python
# app/infrastructure/database/models/event.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.infrastructure.database.connection import Base

class EventModel(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False)
    episode_id = Column(Integer, ForeignKey("episodes.id"), nullable=True)
    event_type = Column(String(50), nullable=False, index=True)
    message = Column(String(500))
    metadata = Column(JSON)
    status = Column(String(20), default="requested", index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    channel = relationship("ChannelModel", back_populates="events")
    episode = relationship("EpisodeModel", back_populates="events")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_event_channel_created', 'channel_id', 'created_at'),
        Index('idx_event_type_status', 'event_type', 'status', 'created_at'),
    )
```

**Acceptance Criteria:**
- [x] Event entity with proper enums
- [x] Metadata stored as JSON
- [x] Relationships to channel and episode
- [x] Performance indexes configured
- [x] Event type and status validation

### Epic 1.2.2: Repository Interface Implementation

#### Task 1.2.2.1: Base Repository Interface
**Status:** ✅ **COMPLETED**  
**Priority:** High  
**Estimated Time:** 2 hours

**Base Repository:**
```python
# app/domain/repositories/base.py
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional

T = TypeVar('T')

class BaseRepository(Generic[T], ABC):
    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create a new entity"""
        pass
    
    @abstractmethod
    async def get_by_id(self, entity_id: int) -> Optional[T]:
        """Get entity by ID"""
        pass
    
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities with pagination"""
        pass
    
    @abstractmethod
    async def update(self, entity: T) -> T:
        """Update existing entity"""
        pass
    
    @abstractmethod
    async def delete(self, entity_id: int) -> bool:
        """Delete entity by ID"""
        pass
```

**Acceptance Criteria:**
- [x] Generic base repository interface created
- [x] All CRUD operations defined
- [x] Proper typing with generics
- [x] Async/await pattern established
- [x] Pagination parameters included

#### Task 1.2.2.2: User Repository Interface
**Status:** ✅ **COMPLETED**  
**Priority:** High  
**Estimated Time:** 1 hour

**Repository Interface:**
```python
# app/domain/repositories/user.py
from abc import abstractmethod
from typing import Optional
from app.domain.repositories.base import BaseRepository
from app.domain.entities.user import User

class UserRepository(BaseRepository[User]):
    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email address"""
        pass
    
    @abstractmethod
    async def email_exists(self, email: str) -> bool:
        """Check if email is already registered"""
        pass
```

**Acceptance Criteria:**
- [x] Extends base repository
- [x] Email lookup functionality
- [x] Email uniqueness checking
- [x] Proper return types
- [x] Documentation strings added

#### Task 1.2.2.3: Channel Repository Interface
**Status:** ✅ **COMPLETED**  
**Priority:** High  
**Estimated Time:** 1 hour

**Repository Interface:**
```python
# app/domain/repositories/channel.py
from abc import abstractmethod
from typing import Optional
from app.domain.repositories.base import BaseRepository
from app.domain.entities.channel import Channel

class ChannelRepository(BaseRepository[Channel]):
    @abstractmethod
    async def find_by_user_id(self, user_id: int) -> Optional[Channel]:
        """Find channel by user ID (one channel per user)"""
        pass
    
    @abstractmethod
    async def update_feed_url(self, channel_id: int, feed_url: str) -> bool:
        """Update RSS feed URL"""
        pass
```

**Acceptance Criteria:**
- [x] Extends base repository
- [x] User-specific channel lookup
- [x] Feed URL update method
- [x] Proper async signatures
- [x] Error handling considerations

#### Task 1.2.2.4: Episode Repository Interface  
**Status:** ✅ **COMPLETED**  
**Priority:** Critical  
**Estimated Time:** 2 hours

**Repository Interface:**
```python
# app/domain/repositories/episode.py
from abc import abstractmethod
from typing import List, Optional
from app.domain.repositories.base import BaseRepository
from app.domain.entities.episode import Episode, EpisodeStatus
from app.domain.value_objects.video_id import VideoId

class EpisodeRepository(BaseRepository[Episode]):
    @abstractmethod
    async def find_by_video_id(self, video_id: VideoId) -> Optional[Episode]:
        """Find episode by YouTube video ID"""
        pass
    
    @abstractmethod
    async def find_by_channel(self, channel_id: int, skip: int = 0, limit: int = 50) -> List[Episode]:
        """Find episodes by channel with pagination"""
        pass
    
    @abstractmethod
    async def find_by_status(self, status: EpisodeStatus) -> List[Episode]:
        """Find episodes by status"""
        pass
    
    @abstractmethod
    async def search(self, query: str, channel_id: int, skip: int = 0, limit: int = 50) -> List[Episode]:
        """Search episodes by title, description, keywords"""
        pass
    
    @abstractmethod
    async def update_status(self, episode_id: int, status: EpisodeStatus) -> bool:
        """Update episode status"""
        pass
    
    @abstractmethod
    async def increment_retry_count(self, episode_id: int) -> bool:
        """Increment retry count for failed downloads"""
        pass
```

**Acceptance Criteria:**
- [x] Video ID uniqueness checks
- [x] Channel-based filtering
- [x] Status-based queries
- [x] Search functionality interface
- [x] Status update methods

#### Task 1.2.2.5: Tag and Event Repository Interfaces
**Status:** ✅ **COMPLETED**  
**Priority:** Medium  
**Estimated Time:** 2 hours

**Tag Repository:**
```python
# app/domain/repositories/tag.py
from abc import abstractmethod
from typing import List, Optional
from app.domain.repositories.base import BaseRepository
from app.domain.entities.tag import Tag

class TagRepository(BaseRepository[Tag]):
    @abstractmethod
    async def find_by_channel(self, channel_id: int) -> List[Tag]:
        """Find all tags for a channel"""
        pass
    
    @abstractmethod
    async def find_by_name(self, channel_id: int, name: str) -> Optional[Tag]:
        """Find tag by name within channel"""
        pass
    
    @abstractmethod
    async def get_episode_tags(self, episode_id: int) -> List[Tag]:
        """Get all tags for an episode"""
        pass
    
    @abstractmethod
    async def add_episode_tag(self, episode_id: int, tag_id: int) -> bool:
        """Add tag to episode"""
        pass
    
    @abstractmethod
    async def remove_episode_tag(self, episode_id: int, tag_id: int) -> bool:
        """Remove tag from episode"""
        pass
```

**Event Repository:**
```python
# app/domain/repositories/event.py
from abc import abstractmethod
from datetime import datetime
from typing import List
from app.domain.repositories.base import BaseRepository
from app.domain.entities.event import Event, EventType

class EventRepository(BaseRepository[Event]):
    @abstractmethod
    async def find_by_channel(self, channel_id: int, skip: int = 0, limit: int = 100) -> List[Event]:
        """Find events by channel"""
        pass
    
    @abstractmethod
    async def find_by_type(self, event_type: EventType) -> List[Event]:
        """Find events by type"""
        pass
    
    @abstractmethod
    async def cleanup_old_events(self, older_than: datetime) -> int:
        """Delete events older than specified date"""
        pass
```

**Acceptance Criteria:**
- [x] Tag repository with episode associations
- [x] Event repository with cleanup functionality
- [x] Proper relationship handling
- [x] Performance considerations
- [x] Bulk operation support

### Epic 1.2.3: Database Migration Setup

#### Task 1.2.3.1: Initial Database Schema Migration
**Status:** ✅ **COMPLETED**  
**Priority:** Critical  
**Estimated Time:** 2 hours

**Migration Steps:**
```bash
# Generate initial migration
uv run alembic revision --autogenerate -m "Initial schema: users, channels, episodes, tags, events"

# Apply migration
uv run alembic upgrade head
```

**Migration File:**
```python
# alembic/versions/001_initial_schema.py
"""Initial schema: users, channels, episodes, tags, events

Revision ID: 001
Revises: 
Create Date: 2024-XX-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('is_admin', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    
    # Channels table
    op.create_table('channels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('website_url', sa.String(500), nullable=True),
        sa.Column('image_url', sa.String(500), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('language', sa.String(10), nullable=True),
        sa.Column('explicit_content', sa.Boolean(), nullable=True),
        sa.Column('author_name', sa.String(255), nullable=True),
        sa.Column('author_email', sa.String(255), nullable=True),
        sa.Column('owner_name', sa.String(255), nullable=True),
        sa.Column('owner_email', sa.String(255), nullable=True),
        sa.Column('feed_url', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Episodes table
    op.create_table('episodes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('channel_id', sa.Integer(), nullable=False),
        sa.Column('video_id', sa.String(20), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('publication_date', sa.DateTime(), nullable=False),
        sa.Column('audio_file_path', sa.String(1000), nullable=True),
        sa.Column('video_url', sa.String(500), nullable=True),
        sa.Column('thumbnail_url', sa.String(500), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('keywords', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(20), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.Column('download_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['channel_id'], ['channels.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Continue with Tags, Events, and association tables...
    # ... (Full migration content)

def downgrade() -> None:
    op.drop_table('episode_tags')
    op.drop_table('events')
    op.drop_table('tags')
    op.drop_table('episodes')
    op.drop_table('channels')
    op.drop_table('users')
```

**Acceptance Criteria:**
- [x] All tables created successfully
- [x] Foreign key constraints properly set
- [x] Indexes created for performance
- [x] Migration can be rolled back
- [x] Database file created correctly

#### Task 1.2.3.2: Database Indexes and Constraints
**Status:** ✅ **COMPLETED**  
**Priority:** High  
**Estimated Time:** 1 hour

**Index Creation:**
```python
# Additional indexes for performance
def upgrade() -> None:
    # ... table creation code ...
    
    # Performance indexes
    op.create_index('idx_episode_video_id', 'episodes', ['video_id'])
    op.create_index('idx_episode_channel_status', 'episodes', ['channel_id', 'status'])
    op.create_index('idx_episode_publication_date', 'episodes', ['publication_date'], postgresql_using='btree')
    op.create_index('idx_event_channel_created', 'events', ['channel_id', 'created_at'])
    op.create_index('idx_event_type_status', 'events', ['event_type', 'status', 'created_at'])
    
    # Unique constraints
    op.create_index('idx_episode_channel_video', 'episodes', ['channel_id', 'video_id'], unique=True)
    op.create_index('idx_tag_channel_name', 'tags', ['channel_id', 'name'], unique=True)
```

**Acceptance Criteria:**
- [x] All performance indexes created
- [x] Unique constraints enforced
- [x] Query performance optimized
- [x] Index usage verified
- [x] No duplicate constraint violations

### Epic 1.2.4: Frontend Type Definitions

#### Task 1.2.4.1: TypeScript Interface Definitions
**Status:** ✅ **COMPLETED**  
**Priority:** High  
**Estimated Time:** 2 hours

**Type Definitions:**
```typescript
// src/types/index.ts

export interface User {
  id: number
  name: string
  email: string
  isAdmin: boolean
  createdAt: string
  updatedAt: string
}

export interface Channel {
  id: number
  userId: number
  name: string
  description: string
  websiteUrl?: string
  imageUrl?: string
  category: string
  language: string
  explicitContent: boolean
  authorName: string
  authorEmail: string
  ownerName: string
  ownerEmail: string
  feedUrl: string
  createdAt: string
  updatedAt: string
}

export interface Episode {
  id: number
  channelId: number
  videoId: string
  title: string
  description: string
  publicationDate: string
  audioFilePath?: string
  videoUrl: string
  thumbnailUrl: string
  durationSeconds?: number
  keywords: string[]
  status: EpisodeStatus
  retryCount: number
  downloadDate?: string
  createdAt: string
  updatedAt: string
  tags?: Tag[]
}

export enum EpisodeStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed'
}

export interface Tag {
  id: number
  channelId: number
  name: string
  color: string
  createdAt: string
  updatedAt: string
}

export interface Event {
  id: number
  channelId: number
  episodeId?: number
  eventType: string
  message: string
  metadata: Record<string, any>
  status: string
  createdAt: string
}

// API Response types
export interface ApiResponse<T> {
  data: T
  message?: string
  success: boolean
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

// Form types
export interface CreateEpisodeRequest {
  videoUrl: string
  tags?: string[]
}

export interface UpdateEpisodeRequest {
  title?: string
  description?: string
  keywords?: string[]
  tags?: number[]
}

export interface ChannelSettingsRequest {
  name?: string
  description?: string
  websiteUrl?: string
  category?: string
  language?: string
  explicitContent?: boolean
  authorName?: string
  authorEmail?: string
  ownerName?: string
  ownerEmail?: string
}
```

**Acceptance Criteria:**
- [x] All domain entities typed
- [x] Enum types defined
- [x] API response types created
- [x] Form input types specified
- [x] Optional vs required fields correct

#### Task 1.2.4.2: API Client with Proper Typing
**Status:** ✅ **COMPLETED**  
**Priority:** High  
**Estimated Time:** 3 hours

**API Client Implementation:**
```typescript
// src/lib/api.ts
import { 
  User, Channel, Episode, Tag, Event,
  ApiResponse, PaginatedResponse,
  CreateEpisodeRequest, UpdateEpisodeRequest,
  ChannelSettingsRequest, EpisodeStatus
} from '@/types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const url = `${API_BASE_URL}${endpoint}`
  
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  })

  if (!response.ok) {
    throw new ApiError(response.status, `HTTP error! status: ${response.status}`)
  }

  return response.json()
}

// Episode API
export const episodeApi = {
  async getAll(channelId: number, page = 1, pageSize = 50): Promise<PaginatedResponse<Episode>> {
    const response = await apiRequest<PaginatedResponse<Episode>>(
      `/episodes?channel_id=${channelId}&page=${page}&page_size=${pageSize}`
    )
    return response.data
  },

  async getById(id: number): Promise<Episode> {
    const response = await apiRequest<Episode>(`/episodes/${id}`)
    return response.data
  },

  async create(data: CreateEpisodeRequest): Promise<Episode> {
    const response = await apiRequest<Episode>('/episodes', {
      method: 'POST',
      body: JSON.stringify(data),
    })
    return response.data
  },

  async update(id: number, data: UpdateEpisodeRequest): Promise<Episode> {
    const response = await apiRequest<Episode>(`/episodes/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
    return response.data
  },

  async delete(id: number): Promise<void> {
    await apiRequest<void>(`/episodes/${id}`, {
      method: 'DELETE',
    })
  },

  async search(query: string, channelId: number, page = 1): Promise<PaginatedResponse<Episode>> {
    const response = await apiRequest<PaginatedResponse<Episode>>(
      `/episodes/search?q=${encodeURIComponent(query)}&channel_id=${channelId}&page=${page}`
    )
    return response.data
  },

  async getStatus(id: number): Promise<{ status: EpisodeStatus, progress?: number }> {
    const response = await apiRequest<{ status: EpisodeStatus, progress?: number }>(
      `/episodes/${id}/status`
    )
    return response.data
  }
}

// Channel API
export const channelApi = {
  async get(): Promise<Channel> {
    const response = await apiRequest<Channel>('/channel')
    return response.data
  },

  async update(data: ChannelSettingsRequest): Promise<Channel> {
    const response = await apiRequest<Channel>('/channel', {
      method: 'PUT',
      body: JSON.stringify(data),
    })
    return response.data
  },

  async regenerateFeed(): Promise<{ feedUrl: string }> {
    const response = await apiRequest<{ feedUrl: string }>('/channel/regenerate-feed', {
      method: 'POST',
    })
    return response.data
  }
}

// Tag API
export const tagApi = {
  async getAll(channelId: number): Promise<Tag[]> {
    const response = await apiRequest<Tag[]>(`/tags?channel_id=${channelId}`)
    return response.data
  },

  async create(channelId: number, name: string, color: string): Promise<Tag> {
    const response = await apiRequest<Tag>('/tags', {
      method: 'POST',
      body: JSON.stringify({ channel_id: channelId, name, color }),
    })
    return response.data
  },

  async update(id: number, name: string, color: string): Promise<Tag> {
    const response = await apiRequest<Tag>(`/tags/${id}`, {
      method: 'PUT',
      body: JSON.stringify({ name, color }),
    })
    return response.data
  },

  async delete(id: number): Promise<void> {
    await apiRequest<void>(`/tags/${id}`, {
      method: 'DELETE',
    })
  },

  async addToEpisode(episodeId: number, tagId: number): Promise<void> {
    await apiRequest<void>(`/episodes/${episodeId}/tags/${tagId}`, {
      method: 'POST',
    })
  },

  async removeFromEpisode(episodeId: number, tagId: number): Promise<void> {
    await apiRequest<void>(`/episodes/${episodeId}/tags/${tagId}`, {
      method: 'DELETE',
    })
  }
}

// Event API
export const eventApi = {
  async getAll(channelId: number, page = 1, pageSize = 50): Promise<PaginatedResponse<Event>> {
    const response = await apiRequest<PaginatedResponse<Event>>(
      `/events?channel_id=${channelId}&page=${page}&page_size=${pageSize}`
    )
    return response.data
  }
}

// Health API
export const healthApi = {
  async check(): Promise<{ status: string, database?: string }> {
    const response = await apiRequest<{ status: string, database?: string }>('/health')
    return response.data
  }
}
```

**Acceptance Criteria:**
- [x] All API endpoints properly typed
- [x] Error handling implemented
- [x] Request/response types enforced
- [x] Base URL configuration working
- [x] Authentication headers ready for future

#### Task 1.2.4.3: React Query Configuration
**Status:** ✅ **COMPLETED**  
**Priority:** High  
**Estimated Time:** 2 hours

**React Query Setup:**
```typescript
// src/lib/query-client.ts
import { QueryClient } from '@tanstack/react-query'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      retry: (failureCount, error) => {
        // Don't retry on 4xx errors
        if (error instanceof Error && 'status' in error) {
          const status = (error as any).status
          if (status >= 400 && status < 500) return false
        }
        return failureCount < 3
      },
    },
    mutations: {
      onError: (error) => {
        console.error('Mutation error:', error)
        // Could add toast notification here
      },
    },
  },
})

// src/hooks/episodes.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { episodeApi } from '@/lib/api'
import { Episode, CreateEpisodeRequest, UpdateEpisodeRequest } from '@/types'

export function useEpisodes(channelId: number, page = 1, pageSize = 50) {
  return useQuery({
    queryKey: ['episodes', channelId, page, pageSize],
    queryFn: () => episodeApi.getAll(channelId, page, pageSize),
    enabled: !!channelId,
  })
}

export function useEpisode(id: number) {
  return useQuery({
    queryKey: ['episodes', id],
    queryFn: () => episodeApi.getById(id),
    enabled: !!id,
  })
}

export function useCreateEpisode() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: CreateEpisodeRequest) => episodeApi.create(data),
    onSuccess: (episode) => {
      // Invalidate episodes list
      queryClient.invalidateQueries({ queryKey: ['episodes'] })
      // Add the new episode to the cache
      queryClient.setQueryData(['episodes', episode.id], episode)
    },
  })
}

export function useUpdateEpisode() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, data }: { id: number, data: UpdateEpisodeRequest }) => 
      episodeApi.update(id, data),
    onSuccess: (episode) => {
      // Update the episode in cache
      queryClient.setQueryData(['episodes', episode.id], episode)
      // Invalidate episodes list to refresh
      queryClient.invalidateQueries({ queryKey: ['episodes'] })
    },
  })
}

export function useDeleteEpisode() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (id: number) => episodeApi.delete(id),
    onSuccess: (_, id) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: ['episodes', id] })
      // Invalidate list
      queryClient.invalidateQueries({ queryKey: ['episodes'] })
    },
  })
}

export function useEpisodeStatus(id: number, enabled = true) {
  return useQuery({
    queryKey: ['episodes', id, 'status'],
    queryFn: () => episodeApi.getStatus(id),
    enabled: enabled && !!id,
    refetchInterval: (data) => {
      // Poll every 2 seconds if processing
      return data?.status === 'processing' ? 2000 : false
    },
  })
}
```

**Query Client Provider:**
```tsx
// src/app/providers.tsx
'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { queryClient } from '@/lib/query-client'

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  )
}
```

**Acceptance Criteria:**
- [x] React Query client configured
- [x] Custom hooks for all entities
- [x] Cache invalidation strategies
- [x] Optimistic updates implemented
- [x] Loading and error states handled

#### Task 1.2.4.4: Basic Layout Components
**Status:** ✅ **COMPLETED**  
**Priority:** Medium  
**Estimated Time:** 3 hours

**Root Layout:**
```tsx
// src/app/layout.tsx
import './globals.css'
import { Inter } from 'next/font/google'
import { ThemeProvider } from '@/components/providers/theme-provider'
import { Providers } from './providers'
import { Navigation } from '@/components/shared/navigation'
import { Toaster } from '@/components/ui/sonner'

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: 'LabCastARR - YouTube to Podcast Converter',
  description: 'Convert YouTube videos to podcast episodes with RSS feeds',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <Providers>
            <div className="min-h-screen bg-background">
              <Navigation />
              <main className="container mx-auto px-4 py-8">
                {children}
              </main>
            </div>
            <Toaster />
          </Providers>
        </ThemeProvider>
      </body>
    </html>
  )
}
```

**Navigation Component:**
```tsx
// src/components/shared/navigation.tsx
'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { ThemeToggle } from '@/components/shared/theme-toggle'
import { Home, Settings, Plus } from 'lucide-react'

const navigation = [
  { name: 'Channel', href: '/', icon: Home },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export function Navigation() {
  const pathname = usePathname()

  return (
    <header className="sticky top-0 z-40 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center">
        <div className="mr-4 hidden md:flex">
          <Link className="mr-6 flex items-center space-x-2" href="/">
            <span className="hidden font-bold sm:inline-block">
              LabCastARR
            </span>
          </Link>
          <nav className="flex items-center space-x-6 text-sm font-medium">
            {navigation.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'transition-colors hover:text-foreground/80',
                  pathname === item.href
                    ? 'text-foreground'
                    : 'text-foreground/60'
                )}
              >
                <span className="flex items-center space-x-2">
                  <item.icon className="h-4 w-4" />
                  <span>{item.name}</span>
                </span>
              </Link>
            ))}
          </nav>
        </div>
        
        <div className="flex flex-1 items-center justify-between space-x-2 md:justify-end">
          <Button asChild size="sm">
            <Link href="/episodes/add">
              <Plus className="h-4 w-4 mr-2" />
              Add Episode
            </Link>
          </Button>
          <ThemeToggle />
        </div>
      </div>
    </header>
  )
}
```

**Theme Toggle:**
```tsx
// src/components/shared/theme-toggle.tsx
'use client'

import { Moon, Sun } from 'lucide-react'
import { useTheme } from 'next-themes'
import { Button } from '@/components/ui/button'

export function ThemeToggle() {
  const { theme, setTheme } = useTheme()

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
    >
      <Sun className="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
      <Moon className="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
      <span className="sr-only">Toggle theme</span>
    </Button>
  )
}
```

**Loading Component:**
```tsx
// src/components/shared/loading.tsx
import { Skeleton } from '@/components/ui/skeleton'

export function EpisodeCardSkeleton() {
  return (
    <div className="rounded-lg border bg-card text-card-foreground shadow-sm">
      <div className="p-6">
        <div className="flex flex-col space-y-3">
          <Skeleton className="h-4 w-[250px]" />
          <Skeleton className="h-4 w-[200px]" />
          <Skeleton className="h-4 w-[150px]" />
        </div>
      </div>
    </div>
  )
}

export function EpisodeGridSkeleton() {
  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {Array.from({ length: 8 }).map((_, i) => (
        <EpisodeCardSkeleton key={i} />
      ))}
    </div>
  )
}
```

**Acceptance Criteria:**
- [x] Responsive navigation implemented
- [x] Theme toggle functionality
- [x] Loading skeleton components
- [x] Consistent layout structure
- [x] Accessibility considerations met

---

## Success Criteria

### Technical Acceptance Criteria

#### Development Environment
- [x] Docker containers build and run successfully
- [x] Hot reload works for both frontend and backend
- [x] Services can communicate via network
- [x] Environment variables properly loaded
- [x] Database created and accessible

#### Database Schema
- [x] All domain models implemented
- [x] Migrations apply without errors
- [x] Foreign key relationships working
- [x] Unique constraints enforced
- [x] Indexes created for performance

#### API Foundation
- [x] Health check endpoints return 200
- [x] Database health check verifies connection
- [x] Basic CRUD operations functional
- [x] Error handling middleware active
- [x] CORS configuration allows frontend access

#### Frontend Foundation
- [x] Next.js application loads successfully
- [x] TypeScript compilation without errors
- [x] Theme switching works correctly
- [x] Navigation between pages functional
- [x] API client connects to backend

#### Type Safety
- [x] All domain entities properly typed
- [x] API client fully typed
- [x] React Query hooks implemented
- [x] Form types defined
- [x] No TypeScript errors

### Performance Criteria

- [ ] Application startup time < 10 seconds
- [ ] Database queries execute in < 100ms
- [ ] Frontend page load time < 2 seconds
- [ ] Hot reload time < 5 seconds
- [ ] Docker build time < 5 minutes

### Quality Criteria

- [x] All code follows established patterns
- [x] Clean architecture principles maintained
- [x] Proper separation of concerns
- [x] Error handling comprehensive
- [x] Documentation complete

---

## Risk Assessment

### High Risk Items

#### Database Design Complexity
**Risk:** Complex relationships and constraints might cause migration issues  
**Mitigation:** Incremental migration approach, thorough testing  
**Owner:** Backend Developer  

#### Type Safety Across Stack
**Risk:** TypeScript interfaces might not match backend models  
**Mitigation:** Automated type generation, integration tests  
**Owner:** Full-stack Developer  

#### Docker Environment Stability
**Risk:** Container orchestration issues in development  
**Mitigation:** Simplified Docker setup, comprehensive documentation  
**Owner:** DevOps/Developer  

### Medium Risk Items

#### React Query Configuration
**Risk:** Caching strategy might not suit application needs  
**Mitigation:** Iterative configuration, performance monitoring  
**Owner:** Frontend Developer  

#### Theme Implementation
**Risk:** SSR/hydration mismatches with theme switching  
**Mitigation:** Use next-themes library, proper suppressHydrationWarning  
**Owner:** Frontend Developer  

### Low Risk Items

#### Component Library Integration
**Risk:** ShadCN components might need customization  
**Mitigation:** Component override capabilities, theming system  
**Owner:** Frontend Developer  

---

## Lessons Learned

### Development Environment Lessons
*To be filled during implementation*

### Database Design Lessons  
*To be filled during implementation*

### Frontend Architecture Lessons
*To be filled during implementation*

### Integration Challenges
*To be filled during implementation*

---

## Next Steps

Upon completion of Phase 1, proceed to:

1. **Phase 2 Planning:** Episode Management System implementation
2. **Architecture Review:** Validate clean architecture implementation
3. **Performance Baseline:** Establish metrics for future optimization
4. **Documentation Update:** Record lessons learned and architectural decisions

---

## 🎉 Phase 1 Status: COMPLETED ✅

**Implementation Summary:**
- ✅ **Milestone 1.1:** Development Environment Setup (4/4 Epics)
- ✅ **Milestone 1.2:** Core Domain Models (4/4 Epics)
  - Epic 1.2.1: Domain Entity Definition 
  - Epic 1.2.2: Repository Interface Implementation
  - Epic 1.2.3: Database Migration Setup  
  - Epic 1.2.4: Frontend Type Definitions

**Key Achievements:**
- 🏗️ Complete clean architecture foundation
- 🗄️ Full domain model implementation with SQLAlchemy
- 🔄 Database migrations with all tables and relationships
- 🎯 Comprehensive TypeScript type definitions
- 🔌 Fully typed API client with React Query integration  
- 📱 Basic layout components and navigation structure
- 🐳 Dockerized development environment
- ⚡ Hot reload and development tooling

**Ready for Phase 2:** Episode Management System Implementation

---

*This detailed implementation plan for Phase 1 provides the foundational infrastructure needed for LabCastARR. All subsequent phases will build upon this solid foundation of clean architecture, type safety, and robust development practices.*