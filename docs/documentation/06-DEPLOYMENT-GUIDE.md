# LabCastARR Deployment Guide

**Document Version:** 1.0
**Last Updated:** 2026-01-29

---

## Table of Contents

1. [Deployment Options](#deployment-options)
2. [Prerequisites](#prerequisites)
3. [Environment Configuration](#environment-configuration)
4. [Local Development](#local-development)
5. [Docker Development](#docker-development)
6. [Docker Production](#docker-production)
7. [Nginx Proxy Manager Setup](#nginx-proxy-manager-setup)
8. [Database Migrations](#database-migrations)
9. [Monitoring and Maintenance](#monitoring-and-maintenance)
10. [Troubleshooting](#troubleshooting)

---

## Deployment Options

| Option | Use Case | Hot Reload | Database |
|--------|----------|------------|----------|
| Local Development | Active coding | Yes | `labcastarr-dev.db` |
| Docker Development | Full stack testing | Yes (with limitations) | `labcastarr-dev.db` |
| Docker Pre-Production | Pre-release testing | No | Configurable |
| Docker Production | Live deployment | No | `labcastarr.db` |

---

## Prerequisites

### System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| CPU | 2 cores | 4 cores |
| RAM | 2 GB | 4 GB |
| Storage | 10 GB | 50 GB+ (for media) |

### Software Requirements

| Software | Version | Required For |
|----------|---------|--------------|
| Node.js | 20+ | Frontend |
| Python | 3.12+ | Backend |
| uv | Latest | Python package management |
| Docker | Latest | Containerized deployment |
| Docker Compose | Latest | Multi-container orchestration |
| FFmpeg | Latest | Audio conversion |

### Installing Prerequisites

```bash
# macOS (with Homebrew)
brew install node python@3.12 ffmpeg
pip install uv

# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs python3.12 python3.12-venv ffmpeg
pip install uv

# Docker (all platforms)
# Follow https://docs.docker.com/get-docker/
```

---

## Environment Configuration

### Environment Files

| File | Purpose | Contains |
|------|---------|----------|
| `.env.development` | Local/Docker dev | Dev settings |
| `.env.production` | Production deployment | Prod settings |
| `.env.pre` | Pre-production testing | Pre-prod settings |

### Required Variables

```env
# Application
ENVIRONMENT=development|production
NODE_ENV=development|production

# URLs
DOMAIN=yourdomain.com
BASE_URL=https://api.yourdomain.com
FRONTEND_URL=https://yourdomain.com
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_DOMAIN=yourdomain.com

# Database
DATABASE_URL=sqlite:///./data/labcastarr.db

# Security (MUST CHANGE IN PRODUCTION)
API_KEY_SECRET=your-secure-api-key
NEXT_PUBLIC_API_KEY=your-secure-api-key
JWT_SECRET_KEY=your-jwt-secret-key

# CORS
CORS_ORIGINS=["https://yourdomain.com"]
ALLOWED_HOSTS=["localhost","api.yourdomain.com"]

# Paths
MEDIA_PATH=./media
FEEDS_PATH=./feeds

# Redis (for Celery)
REDIS_URL=redis://redis:6379/0
```

### Generating Secrets

```bash
# Generate secure random keys
openssl rand -base64 32  # For API_KEY_SECRET
openssl rand -base64 32  # For JWT_SECRET_KEY
```

### Creating Environment Files

```bash
# From example files
cp .env.development.example .env.development
cp .env.production.example .env.production

# Edit with your values
nano .env.production
```

---

## Local Development

### Without Docker (Recommended for Active Development)

**Terminal 1: Backend**
```bash
cd backend
uv sync                           # Install dependencies
uv run alembic upgrade head       # Apply migrations
uv run fastapi dev app/main.py    # Start with hot reload
```

Backend available at: `http://localhost:8000`
API docs at: `http://localhost:8000/docs`

**Terminal 2: Frontend**
```bash
cd frontend
npm install                       # Install dependencies
npm run dev                       # Start with hot reload
```

Frontend available at: `http://localhost:3000`

**Terminal 3 (Optional): Celery Worker**
```bash
# Start Redis first
docker run -p 6379:6379 redis:alpine

# In another terminal
cd backend
uv run celery -A app.infrastructure.celery_app worker --loglevel=info
```

**Terminal 4 (Optional): Celery Beat**
```bash
cd backend
uv run celery -A app.infrastructure.celery_app beat --loglevel=info
```

---

## Docker Development

### Starting Development Environment

```bash
# Start all services with hot reload
docker compose --env-file .env.development -f docker-compose.dev.yml up --build

# Or run in background
docker compose --env-file .env.development -f docker-compose.dev.yml up --build -d
```

### Services Started

| Service | Port | Description |
|---------|------|-------------|
| `backend-dev` | 8000 | FastAPI with hot reload |
| `frontend-dev` | 3000 | Next.js with hot reload |
| `redis-dev` | 6379 | Message broker |
| `celery-worker-dev` | - | Background tasks |
| `celery-beat-dev` | - | Scheduled tasks |

### Viewing Logs

```bash
# All services
docker compose -f docker-compose.dev.yml logs -f

# Specific service
docker compose -f docker-compose.dev.yml logs backend-dev -f
docker compose -f docker-compose.dev.yml logs frontend-dev -f
docker compose -f docker-compose.dev.yml logs celery-worker-dev -f
```

### Hot Reload Limitations

| Component | Hot Reload | Notes |
|-----------|------------|-------|
| Backend (FastAPI) | Yes | Uses `uvicorn --reload` |
| Frontend (Next.js) | Yes | Uses `npm run dev` |
| Celery Workers | **No** | Requires manual restart |

**Restarting Celery after code changes:**
```bash
docker compose -f docker-compose.dev.yml restart celery-worker-dev celery-beat-dev
```

### Stopping Development

```bash
docker compose -f docker-compose.dev.yml down
```

---

## Docker Production

### Building and Starting Production

```bash
# Build and start all services
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d

# View startup logs
docker compose -f docker-compose.prod.yml logs -f
```

### Production Services

| Service | Internal Port | External Port | Description |
|---------|---------------|---------------|-------------|
| `backend-prod` | 8000 | 8000 | FastAPI production |
| `frontend-prod` | 3000 | 3000 | Next.js production build |
| `redis-prod` | 6379 | - | Message broker (internal) |
| `celery-worker-prod` | - | - | Background tasks |
| `celery-beat-prod` | - | - | Scheduled tasks |

### Health Checks

```bash
# Check container status
docker compose -f docker-compose.prod.yml ps

# Check backend health
curl http://localhost:8000/health/

# Check frontend
curl http://localhost:3000
```

### Updating Production

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d

# Verify health
docker compose -f docker-compose.prod.yml ps
```

### Stopping Production

```bash
docker compose -f docker-compose.prod.yml down
```

### Data Persistence

Production uses Docker named volumes:

| Volume | Purpose | Container Path |
|--------|---------|----------------|
| `labcastarr_data` | SQLite database | `/app/data` |
| `labcastarr_media` | Audio files | `/app/media` |
| `labcastarr_feeds` | RSS feeds | `/app/feeds` |

**Volumes persist across container restarts and rebuilds.**

---

## Nginx Proxy Manager Setup

### Overview

For production deployment with HTTPS, configure two proxy hosts in Nginx Proxy Manager:

### Frontend Proxy Host

| Setting | Value |
|---------|-------|
| Domain | `yourdomain.com` |
| Scheme | `http` |
| Forward Hostname | `labcastarr-frontend-prod-1` or IP |
| Forward Port | `3000` |
| SSL | Let's Encrypt |
| Force SSL | Yes |
| HTTP/2 | Yes |
| HSTS | Yes |

### Backend Proxy Host

| Setting | Value |
|---------|-------|
| Domain | `api.yourdomain.com` |
| Scheme | `http` |
| Forward Hostname | `labcastarr-backend-prod-1` or IP |
| Forward Port | `8000` |
| SSL | Let's Encrypt |
| Force SSL | Yes |
| HTTP/2 | Yes |
| HSTS | Yes |

### Advanced Configuration (Backend)

Add to "Custom Nginx Configuration":

```nginx
# Media streaming support
proxy_set_header Range $http_range;
proxy_set_header If-Range $http_if_range;
proxy_no_cache $http_range $http_if_range;

# Large file upload support
client_max_body_size 500M;

# Timeout for long operations
proxy_read_timeout 300s;
proxy_connect_timeout 75s;
```

### DNS Configuration

Create A records pointing to your server:

```
yourdomain.com      → [Your Server IP]
api.yourdomain.com  → [Your Server IP]
```

---

## Database Migrations

### Checking Migration Status

```bash
# Local
cd backend && uv run alembic current

# Docker
docker exec labcastarr-backend-prod-1 uv run alembic current
```

### Applying Migrations

Migrations are automatically applied on container startup via `startup.sh`.

**Manual migration (if needed):**
```bash
# Docker production
docker exec labcastarr-backend-prod-1 uv run alembic upgrade head

# Local
cd backend && uv run alembic upgrade head
```

### Creating New Migrations

```bash
cd backend

# Auto-generate from model changes
uv run alembic revision --autogenerate -m "description of change"

# Manual migration
uv run alembic revision -m "description of change"
```

### Rolling Back

```bash
# Rollback one migration
uv run alembic downgrade -1

# Rollback to specific revision
uv run alembic downgrade <revision_id>
```

### Backup Before Migration

**Always backup before production migrations:**

```bash
# Create backup
cp backend/data/labcastarr.db backups/labcastarr_$(date +%Y%m%d_%H%M%S).db

# Verify backup integrity
sqlite3 backups/labcastarr_*.db "PRAGMA integrity_check;"
```

---

## Monitoring and Maintenance

### Container Health

```bash
# View all container status
docker compose -f docker-compose.prod.yml ps

# Check specific container logs
docker compose -f docker-compose.prod.yml logs backend-prod --tail=100

# Follow logs in real-time
docker compose -f docker-compose.prod.yml logs -f
```

### Resource Usage

```bash
# Container resource usage
docker stats

# Disk usage
docker system df
```

### Database Maintenance

```bash
# Check database size
du -h backend/data/labcastarr.db

# Integrity check
sqlite3 backend/data/labcastarr.db "PRAGMA integrity_check;"

# Optimize (vacuum)
sqlite3 backend/data/labcastarr.db "VACUUM;"
```

### Log Rotation

Docker logs can grow large. Configure log rotation:

```yaml
# In docker-compose.prod.yml
services:
  backend-prod:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Backup Strategy

```bash
# Backup script (add to cron)
#!/bin/bash
BACKUP_DIR="/backups/labcastarr"
DATE=$(date +%Y%m%d_%H%M%S)

# Stop services briefly for consistent backup
docker compose -f docker-compose.prod.yml stop backend-prod

# Backup database
cp backend/data/labcastarr.db $BACKUP_DIR/labcastarr_$DATE.db

# Backup media (optional - can be large)
tar -czf $BACKUP_DIR/media_$DATE.tar.gz backend/media/

# Restart services
docker compose -f docker-compose.prod.yml start backend-prod

# Keep last 7 daily backups
find $BACKUP_DIR -name "labcastarr_*.db" -mtime +7 -delete
```

---

## Troubleshooting

### Common Issues

#### Environment Variables Not Loading

**Symptom:** Warnings about variables not set

**Solution:** Always use `--env-file` flag:
```bash
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d
```

#### Health Check Failing

**Symptom:** Container shows "unhealthy"

**Check:**
```bash
# Test health endpoint (note trailing slash!)
curl http://localhost:8000/health/

# View backend logs
docker compose -f docker-compose.prod.yml logs backend-prod --tail=50
```

**Common causes:**
- Database migration still running (wait 60 seconds)
- Missing environment variables
- Port conflict

#### Database Locked

**Symptom:** `sqlite3.OperationalError: database is locked`

**Solution:**
```bash
# Stop all services
docker compose -f docker-compose.prod.yml down

# Wait for WAL checkpoint
sleep 5

# Checkpoint manually
sqlite3 backend/data/labcastarr.db "PRAGMA wal_checkpoint(TRUNCATE);"

# Restart
docker compose --env-file .env.production -f docker-compose.prod.yml up -d
```

#### Frontend Can't Connect to Backend

**Symptom:** Network errors in browser

**Check:**
```bash
# Verify environment variable
docker exec labcastarr-frontend-prod-1 env | grep NEXT_PUBLIC_API_URL

# Test backend from frontend container
docker exec labcastarr-frontend-prod-1 curl http://backend-prod:8000/health/
```

**Common causes:**
- Incorrect `NEXT_PUBLIC_API_URL`
- CORS not configured (check `CORS_ORIGINS`)
- Backend not healthy

#### Celery Tasks Not Running

**Symptom:** Background tasks stuck in PENDING

**Check:**
```bash
# Verify Redis is running
docker exec labcastarr-redis-prod-1 redis-cli ping
# Should return: PONG

# Check Celery worker logs
docker compose -f docker-compose.prod.yml logs celery-worker-prod --tail=50
```

**Common causes:**
- Redis not running
- Worker crashed (check logs)
- Code changes not reloaded (restart workers)

### Getting Help

1. Check container logs: `docker compose -f docker-compose.prod.yml logs -f`
2. Check application logs: `backend/logs/`
3. Verify environment: `docker exec <container> env`
4. Test endpoints manually with curl

---

## Quick Reference Commands

```bash
# Development
docker compose --env-file .env.development -f docker-compose.dev.yml up --build
docker compose -f docker-compose.dev.yml down
docker compose -f docker-compose.dev.yml logs -f

# Production
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml logs -f

# Pre-Production
docker compose --env-file .env.pre -f docker-compose.pre.yml up --build -d

# Container access
docker exec -it labcastarr-backend-prod-1 /bin/bash

# Database operations
docker exec labcastarr-backend-prod-1 uv run alembic current
docker exec labcastarr-backend-prod-1 uv run alembic upgrade head

# Restart specific services
docker compose -f docker-compose.prod.yml restart backend-prod
docker compose -f docker-compose.prod.yml restart celery-worker-prod celery-beat-prod
```

---

**End of Document**
