<div align="center">
  <a href="https://oliverbarreto.com">
    <img src="https://www.oliverbarreto.com/images/site-logo.png" />
  </a>
</div>
</br>
</br>
<div align="center">
  <h1>LabcastARR | A podcast channel for your Homelab</h1>
  <strong>This app will let you create a podcast channel for your Homelab by creating episodes from YouTube videos or uploading your own audio files</strong>
  </br>
  </br>
  <p>Created with ❤️ by Oliver Barreto</p>
</div>

</br>
</br>

## Features

- 🎥 **YouTube to Podcast**: Convert YouTube videos to podcast episodes automatically
- 🎵 **Audio File Upload**: Upload your own audio files (MP3, M4A, WAV, OGG, FLAC)
- 🎥 **Follow YouTube Channels and Discover Videos**: Follow YouTube channels and discover new videos automatically and create episodes from them.
- 🔄 **Automatic Conversion**: Unsupported formats are automatically converted to podcast-compatible MP3
- 📡 **RSS Feed Generation**: iTunes and Spotify compatible podcast RSS feeds
- 🏷️ **Episode Management**: Tag, organize, and manage your podcast episodes
- 🔐 **Secure Authentication**: JWT-based authentication with refresh tokens
- 📊 **Event Logging**: Comprehensive logging for user actions and system events
- 🐳 **Docker Support**: Easy deployment with Docker Compose

## Technology Stack

- **Frontend:** Next.js 15 + React + TypeScript + TailwindCSS v4 + ShadCN UI + Node 20+
- **Backend:** FastAPI + Python 3.12+ + uv (dependency management)
- **Database:** SQLite + SQLAlchemy
- **Development:** Docker + Docker Compose

## Project Structure

```
/LabCastARR
  /backend                 # FastAPI backend application
    Dockerfile              # Backend Docker configuration
  /frontend                # Next.js frontend application
    Dockerfile              # Frontend Docker configuration
  /docs                    # Documentation
  /scripts                 # Scripts
  /web                     # Legacy Flask app (reference)
  docker-compose.dev.yml   # Development Docker Compose
  docker-compose.prod.yml  # Production Docker Compose
  .env.development         # Development Environment variables
  .env.development.example # Development Environment variables template
  .env.production          # Production Environment variables
  .env.production.example  # Production Environment variables template
  README.md                # README file
  CLAUDE.md                # Claude.md file
```

## Getting Started

### Prerequisites

- [Node.js 20+](https://nodejs.org/)
- [Python 3.12+](https://www.python.org/)
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [Docker](https://www.docker.com/) (optional, for containerized development)
- [FFmpeg](https://ffmpeg.org/) (required for audio file conversion - automatically included in Docker)

### Quick Start for Development with Docker Compose (Recommended)

1. **Clone the repository**

```bash
git clone <repository-url>
cd labcastarr
```

2. **Set up environment variables**

```bash
# Edit .env.development / .env.production with your configuration
cp .env.development.example .env.development
cp .env.production.example .env.production
```

3. **Create necessary API KEYS**

```bash
# Create necessary API KEYS with:
openssl rand -base64 32

# Backend API Key
API_KEY_SECRET=your-api-key-secret-here

# Frontend API Key
NEXT_PUBLIC_API_KEY=your-api-key-secret-here

# JWT Authentication settings
JWT_SECRET_KEY=your-api-key-secret-here
```

4. **Run with Docker Compose**

```bash
# Production mode
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d

# Development mode
docker compose --env-file .env.development -f docker-compose.dev.yml up --build

# Stop services
docker compose -f docker-compose.prod.yml down  # or docker-compose.dev.yml
```

5. **Access the applications Locally**

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Backend API Docs: http://localhost:8000/docs

6. **Access the applications in Production**

⚠️ We need first to configure the Nginx Proxy Manager to point to the correct domains and ports.

- Frontend: https://labcastarr.yourcooldomain.com
- Backend API: https://labcastarr-api.yourcooldomain.com
- Backend API Docs: https://labcastarr-api.yourcooldomain.com/docs

### Local Development (Without Docker)

#### Backend Setup

1. **Navigate to backend directory**

```bash
cd backend
```

2. **Install dependencies with uv**

```bash
uv sync
```

3. **Run FastAPI development server**

```bash
uv run fastapi dev app/main.py
```

The backend will be available at http://localhost:8000

**Note**: Backend automatically uses `.env.development` configuration via symlink for consistency with Docker development.

#### Frontend Setup

1. **Navigate to frontend directory**

```bash
cd frontend
```

2. **Install dependencies**

```bash
npm install
```

3. **Run Next.js development server**

```bash
npm run dev
```

The frontend will be available at http://localhost:3000

## Available Scripts

### Backend Scripts

- `cd backend && uv run fastapi dev app/main.py` - Start development server
- `cd backend && uv run fastapi run app/main.py` - Start production server
- `cd backend && uv sync` - Install/sync dependencies

### Frontend Scripts

- `cd frontend && npm run dev` - Start development server
- `cd frontend && npm run build` - Build for production
- `cd frontend && npm run start` - Start production server
- `cd frontend && npm run lint` - Run ESLint

### Docker Scripts

Production mode: Run both services in production mode

- `docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d`

Development mode: Run in development mode with hot reload

- `docker compose --env-file .env.development -f docker-compose.dev.yml up --build -d`

Stop services

- `docker compose -f docker-compose.dev.yml down` (development)
- `docker compose -f docker-compose.prod.yml down` (production)

## Environment Variables

Copy `.env.example` to `.env` and configure the following variables:

- `ENVIRONMENT` - Application environment (development/production)
- `BACKEND_URL` - Backend API URL
- `FRONTEND_URL` - Frontend application URL
- `NEXT_PUBLIC_API_URL` - Public API URL for frontend

See `.env.example` for a complete list of available configuration options.

## Development Workflow

1. **Backend Development**: Use `uv run fastapi dev app/main.py` for hot-reload development
2. **Frontend Development**: Use `npm run dev` for hot-reload development
3. **Full Stack Development**: Use Docker Compose with development override for integrated development. You have three deployment options for LabCastARR project:

4. ✅ Local Development: `cd backend && uv run fastapi dev app/main.py` + `cd frontend && npm run dev`
5. ✅ Development Docker Compose: `docker compose --env-file .env.development -f docker-compose.dev.yml up --build`
6. ✅ Production Docker Compose: `docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d`
7. ✅ Stop services: `docker compose -f docker-compose.prod.yml down` (production) or `docker compose -f docker-compose.dev.yml down` (development)

8. **API Testing**: Access interactive API documentation at http://localhost:8000/docs

## Creating Podcast Episodes

LabcastARR supports various methods for creating podcast episodes:

### Method 1: From YouTube URL

1. Navigate to "Add New Episode" page
2. Select "From YouTube URL" tab
3. Enter a YouTube video URL
4. The system will:
   - Extract audio from the video
   - Download metadata (title, description, thumbnail)
   - Create a podcast episode automatically

### Method 2: Upload Audio File

1. Navigate to "Add New Episode" page
2. Select "Upload Audio File" tab
3. Drag and drop or select an audio file
4. Supported formats:
   - ✅ **MP3** - Stored as-is (no conversion)
   - ✅ **M4A** - Stored as-is (no conversion)
   - ✅ **WAV** - Converted to MP3
   - ✅ **OGG** - Converted to MP3
   - ✅ **FLAC** - Converted to MP3
5. Fill in episode details (title, description, tags, publication date)
6. Click "Upload Episode"
7. The system will:
   - Validate the file (format, size, integrity)
   - Convert to MP3 if necessary (using FFmpeg)
   - Extract audio metadata (duration, bitrate)
   - Create the podcast episode
   - Make it available in your RSS feed

**File Upload Limits:**

- Maximum file size: 500MB
- Automatic format conversion for podcast compatibility
- Client-side validation for faster feedback
- Streaming upload for large files

### Method 3: Create episodes from new videos in followed channels

1. Navigate to `/subscriptions/channels` page
2. Enter a YouTube valid channel URL
3. Use the UI to review the new videos and create episodes from them. The system will:
   - Search for new videos in the channel
   - Download metadata (title, description, thumbnail)
   - Show the new videos in the `/subscriptions/videos` tab
   - Use the UI to review the new videos and create episodes from them. The system will create a podcast episode automatically and add them to the RSS feed.
# recomendar
