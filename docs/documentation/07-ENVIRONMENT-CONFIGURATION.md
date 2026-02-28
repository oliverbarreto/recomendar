# LabCastARR Environment Configuration

**Document Version:** 1.0
**Last Updated:** 2026-01-29

---

## Table of Contents

1. [Environment Files](#environment-files)
2. [Variable Reference](#variable-reference)
3. [Development Configuration](#development-configuration)
4. [Production Configuration](#production-configuration)
5. [Docker Compose Integration](#docker-compose-integration)
6. [Security Best Practices](#security-best-practices)

---

## Environment Files

### File Structure

```
labcastarr/
├── .env.development           # Development environment
├── .env.development.example   # Development template
├── .env.production            # Production environment
├── .env.production.example    # Production template
├── .env.pre                   # Pre-production environment
└── backend/.env.local         # Backend symlink (optional)
```

### File Purposes

| File | Purpose | Git Tracked |
|------|---------|-------------|
| `.env.development` | Local/Docker dev settings | No (in .gitignore) |
| `.env.development.example` | Template for development | Yes |
| `.env.production` | Production deployment | No (in .gitignore) |
| `.env.production.example` | Template for production | Yes |
| `.env.pre` | Pre-production testing | No (in .gitignore) |

---

## Variable Reference

### Application Settings

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `ENVIRONMENT` | string | Yes | `development` or `production` |
| `NODE_ENV` | string | Yes | `development` or `production` |

### URL Configuration

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `DOMAIN` | string | Prod | Primary domain (e.g., `yourdomain.com`) |
| `BASE_URL` | string | Yes | Backend API URL |
| `FRONTEND_URL` | string | Yes | Frontend URL |
| `BACKEND_URL` | string | Yes | Backend URL (may differ from BASE_URL) |
| `NEXT_PUBLIC_API_URL` | string | Yes | API URL for client-side requests |
| `NEXT_PUBLIC_DOMAIN` | string | Yes | Domain for frontend |

### Database Configuration

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `DATABASE_URL` | string | Yes | SQLite database URL |

**Format:** `sqlite:///./data/labcastarr.db` (production) or `sqlite:///./data/labcastarr-dev.db` (development)

### Security Configuration

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `API_KEY_SECRET` | string | Yes | Backend API authentication key |
| `NEXT_PUBLIC_API_KEY` | string | Yes | Frontend API key (same as backend) |
| `JWT_SECRET_KEY` | string | Yes | JWT token signing key |
| `SHORTCUT_API_KEY` | string | No | iOS Shortcuts API key |

**Security Notes:**
- Generate keys with: `openssl rand -base64 32`
- Never commit actual secrets to version control
- Use different keys for different environments

### CORS and Hosts

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `CORS_ORIGINS` | JSON array | Yes | Allowed CORS origins |
| `ALLOWED_HOSTS` | JSON array | Yes | Allowed backend hosts |

**Format Examples:**
```env
CORS_ORIGINS=["http://localhost:3000"]
CORS_ORIGINS=["https://yourdomain.com"]
ALLOWED_HOSTS=["localhost","127.0.0.1","0.0.0.0"]
ALLOWED_HOSTS=["localhost","api.yourdomain.com"]
```

### File Paths

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `MEDIA_PATH` | string | No | `./media` | Audio file storage |
| `FEEDS_PATH` | string | No | `./feeds` | RSS feed storage |

### Redis Configuration

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `REDIS_URL` | string | Yes* | Redis connection URL |

*Required for Celery background tasks

**Format:** `redis://redis:6379/0` (Docker) or `redis://localhost:6379/0` (local)

### JWT Token Settings

These are set in `backend/app/core/config.py` but can be overridden:

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | int | 60 | Access token lifetime |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | int | 30 | Refresh token lifetime |

---

## Development Configuration

### `.env.development` Example

```env
# ===========================================
# LabCastARR Development Environment
# ===========================================

# Application
ENVIRONMENT=development
NODE_ENV=development

# URLs (Local Development)
DOMAIN=localhost
BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_DOMAIN=localhost

# Database
DATABASE_URL=sqlite:///./data/labcastarr-dev.db

# Security (OK for development - CHANGE IN PRODUCTION)
API_KEY_SECRET=dev-secret-key-change-in-production
NEXT_PUBLIC_API_KEY=dev-secret-key-change-in-production
JWT_SECRET_KEY=dev-jwt-secret-key-change-in-production

# CORS (Allow local frontend)
CORS_ORIGINS=["http://localhost:3000"]
ALLOWED_HOSTS=["localhost","127.0.0.1","0.0.0.0"]

# Redis (Docker service name)
REDIS_URL=redis://redis-dev:6379/0

# Paths
MEDIA_PATH=./media
FEEDS_PATH=./feeds
```

### Backend-Specific Configuration

For local backend development without Docker, you may need a symlink:

```bash
cd backend
ln -s ../.env.development .env.local
```

---

## Production Configuration

### `.env.production` Example

```env
# ===========================================
# LabCastARR Production Environment
# ===========================================

# Application
ENVIRONMENT=production
NODE_ENV=production

# URLs (Production - Replace with your domain)
DOMAIN=yourdomain.com
BASE_URL=https://api.yourdomain.com
FRONTEND_URL=https://yourdomain.com
BACKEND_URL=https://api.yourdomain.com
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_DOMAIN=yourdomain.com

# Database (Production database)
DATABASE_URL=sqlite:///./data/labcastarr.db

# Security (CHANGE THESE - Generate with: openssl rand -base64 32)
API_KEY_SECRET=your-production-api-key-here
NEXT_PUBLIC_API_KEY=your-production-api-key-here
JWT_SECRET_KEY=your-production-jwt-secret-here
SHORTCUT_API_KEY=your-ios-shortcuts-key-here

# CORS (Production frontend only)
CORS_ORIGINS=["https://yourdomain.com"]
ALLOWED_HOSTS=["localhost","127.0.0.1","0.0.0.0","api.yourdomain.com"]

# Redis (Docker service name)
REDIS_URL=redis://redis-prod:6379/0

# Paths (Docker volumes)
MEDIA_PATH=./media
FEEDS_PATH=./feeds
```

### Pre-Production Configuration

For `.env.pre` (testing before production):

```env
# Same as production but with different domains
DOMAIN=pre.yourdomain.com
BASE_URL=https://api-pre.yourdomain.com
FRONTEND_URL=https://pre.yourdomain.com
# ... etc

# Can use production database for testing
# Or use separate database to avoid RSS feed URL issues
DATABASE_URL=sqlite:///./data/labcastarr-pre.db
```

---

## Docker Compose Integration

### How Environment Variables Load

Docker Compose uses two mechanisms for environment variables:

#### 1. `--env-file` Flag (Compose File Substitution)

Loads variables for `${VAR}` substitution in `docker-compose.yml`:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml up
```

Used for:
- Service configurations
- Port mappings
- Image names
- Volume paths

#### 2. `env_file` Directive (Container Environment)

Loads variables into container runtime:

```yaml
# docker-compose.prod.yml
services:
  backend-prod:
    env_file:
      - .env.production
```

Used for:
- Application configuration
- API keys
- Database URLs

### Frontend Build-Time Variables

**Important:** Next.js `NEXT_PUBLIC_*` variables must be available at build time.

```dockerfile
# frontend/Dockerfile
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_API_KEY
ARG NEXT_PUBLIC_DOMAIN

ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NEXT_PUBLIC_API_KEY=${NEXT_PUBLIC_API_KEY}
ENV NEXT_PUBLIC_DOMAIN=${NEXT_PUBLIC_DOMAIN}
```

### Example Docker Compose Section

```yaml
services:
  frontend-prod:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        - NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
        - NEXT_PUBLIC_API_KEY=${NEXT_PUBLIC_API_KEY}
        - NEXT_PUBLIC_DOMAIN=${NEXT_PUBLIC_DOMAIN}
    env_file:
      - .env.production
```

### Verifying Variables

```bash
# Check if compose file can substitute variables
docker compose --env-file .env.production -f docker-compose.prod.yml config

# Check variables inside running container
docker exec labcastarr-backend-prod-1 env | grep -E "DATABASE_URL|API_KEY"
docker exec labcastarr-frontend-prod-1 env | grep NEXT_PUBLIC
```

---

## Security Best Practices

### Secret Generation

```bash
# Generate secure random keys
openssl rand -base64 32

# Example output: Xk9mY2FkMjM0NWFiY2RlZjEyMzQ1Njc4OWFiY2RlZjE=
```

### Secret Management

1. **Never commit secrets** to version control
2. **Use different secrets** for each environment
3. **Rotate secrets** periodically
4. **Use strong secrets** (minimum 32 characters)

### .gitignore Configuration

```gitignore
# Environment files with secrets
.env
.env.local
.env.development
.env.production
.env.pre

# Keep examples
!.env.development.example
!.env.production.example
```

### Environment File Permissions

```bash
# Restrict read access
chmod 600 .env.production
chmod 600 .env.development
```

### Production Checklist

- [ ] All `*_SECRET` and `*_KEY` variables are unique, randomly generated
- [ ] `CORS_ORIGINS` only includes your production domain
- [ ] `ALLOWED_HOSTS` is properly restricted
- [ ] Environment files are not committed to git
- [ ] File permissions are restricted (600)
- [ ] SSL/HTTPS is configured for all production URLs

---

## Variable Loading Order

### Backend (FastAPI)

1. System environment variables
2. `.env` file (if present)
3. Pydantic settings defaults

```python
# backend/app/core/config.py
class Settings(BaseSettings):
    environment: str = "development"
    database_url: str = "sqlite:///./data/labcastarr-dev.db"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

### Frontend (Next.js)

1. Build-time environment (from Dockerfile ARG)
2. Runtime environment
3. `.env.local` (development only)

```typescript
// Access in code
const apiUrl = process.env.NEXT_PUBLIC_API_URL;
```

---

## Troubleshooting

### Variables Not Loading

**Symptom:** Docker Compose warnings about blank variables

**Solution:**
```bash
# Always use --env-file flag
docker compose --env-file .env.production -f docker-compose.prod.yml up
```

### Frontend NEXT_PUBLIC Variables Empty

**Symptom:** Client-side API calls fail

**Cause:** Variables not available at build time

**Solution:** Rebuild the frontend container:
```bash
docker compose --env-file .env.production -f docker-compose.prod.yml build frontend-prod
docker compose --env-file .env.production -f docker-compose.prod.yml up -d
```

### CORS Errors

**Symptom:** Browser console shows CORS policy errors

**Solution:** Verify `CORS_ORIGINS` includes the exact frontend URL:
```env
# Wrong
CORS_ORIGINS=["https://yourdomain.com/"]  # No trailing slash

# Correct
CORS_ORIGINS=["https://yourdomain.com"]
```

### Database Path Issues

**Symptom:** Database in wrong location

**Cause:** `DATABASE_URL` path mismatch

**Solution:** Verify path format:
```env
# Relative to backend/ directory
DATABASE_URL=sqlite:///./data/labcastarr.db

# This creates: backend/data/labcastarr.db
```

---

## Quick Reference

### Development
```env
ENVIRONMENT=development
DATABASE_URL=sqlite:///./data/labcastarr-dev.db
NEXT_PUBLIC_API_URL=http://localhost:8000
CORS_ORIGINS=["http://localhost:3000"]
```

### Production
```env
ENVIRONMENT=production
DATABASE_URL=sqlite:///./data/labcastarr.db
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
CORS_ORIGINS=["https://yourdomain.com"]
```

### Docker Commands
```bash
# Development
docker compose --env-file .env.development -f docker-compose.dev.yml up --build

# Production
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d

# Verify configuration
docker compose --env-file .env.production -f docker-compose.prod.yml config
```

---

**End of Document**
