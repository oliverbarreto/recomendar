# FEATURES 

- In Settings page, tags tab, the number o episodes associated to each tag are not showing up, we always have 0. Fix it

- We need to make a change in the model, when we extract the metadata from the youtube video we have to also extract and add to the database, the Channel Name of the Youtube Channel that published the video. 

Think hard to analyze all necessary changes to the model, logic in the frontend and the backend api (thoroughly revise routes that need to be updated), services/repositories, types in the frontend and backend, components affected (eg: episode-card.tsx), props, etc.

https://www.youtube.com/watch?v=Kr3Sh2PKA8Y

---

BUGFIX:


---


## /prime results

```
⏺ Project Context Summary

LabCastARR is a full-stack podcast management application that converts YouTube videos to
podcast episodes and generates RSS feeds.

Project Structure

- Frontend: Next.js 15 + React + TypeScript + TailwindCSS v4 + ShadCN UI
- Backend: FastAPI + Python 3.12+ with Clean Architecture (hexagonal)
- Database: SQLite with SQLAlchemy + Alembic migrations
- Media Processing: yt-dlp for YouTube audio extraction, PodGen for RSS feeds
- Development: Docker Compose setup with hot-reload support

Key Directories

├── backend/                # FastAPI backend with Clean Architecture
│   ├── app/
│   │   ├── domain/         # Business logic, entities, repositories
│   │   ├── application/    # Use cases and application services
│   │   ├── infrastructure/ # Data access, external services
│   │   └── presentation/   # API routes and schemas
│   ├── data/               # SQLite database storage
│   ├── media/              # Downloaded audio files
│   └── feeds/              # Generated RSS feeds
├── frontend/               # Next.js React application
│   └── src/
│       ├── components/     # UI components (ShadCN + custom)
│       ├── hooks/          # React Query API hooks
│       └── lib/            # Utilities and API client
├── web/                    # Legacy OLD Flask app (reference only, will be removed later)
└── docs/                   # Project documentation and tasks
└── .env                    # Project environment variables
└── .env.example            # Project environment variables template
└── docker-compose.yml      # Project Docker Compose file
└── docker-compose.dev.yml  # Project Docker Compose file for development
└── README.md               # Project README file


Core Features

- YouTube video analysis and audio extraction
- Multi-channel podcast management
- Episode organization with tagging and search
- RSS feed generation (iTunes/Spotify compatible)
- Real-time progress tracking for downloads

Development Workflow

- Backend: cd backend && uv run fastapi dev app/main.py (port 8000)
- Frontend: cd frontend && npm run dev (port 3000)
- Docker: docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

The project follows modern development practices with TypeScript, async/await patterns, Clean
Architecture principles, and comprehensive API documentation at /docs.
```

