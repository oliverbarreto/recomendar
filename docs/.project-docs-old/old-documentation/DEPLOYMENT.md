# LabCastARR Production Deployment Guide

## 🚀 Quick Start

### Development Deployment
```bash
# Start development servers using Docker
docker compose --env-file .env.development -f docker-compose.dev.yml up --build

# Stop development services
docker compose -f docker-compose.dev.yml down  

# Or run locally without Docker
cd backend && uv run fastapi dev app/main.py
cd frontend && npm run dev
```

### Production Deployment
```bash
# Start production deployment
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d

# Stop production deployment
docker compose -f docker-compose.prod.yml down  
```

## 🔧 Configuration

### Environment Variables for Production

Update your `.env` file with your domain configuration:

```env
# Application Environment
ENVIRONMENT=production
NODE_ENV=production

# Production Domain Configuration (Separate domains - RECOMMENDED)
DOMAIN=yourdomain.com                          # Frontend domain
BASE_URL=https://api.yourdomain.com            # API/Backend domain
FRONTEND_URL=https://yourdomain.com            # Frontend URL
BACKEND_URL=https://api.yourdomain.com         # Backend URL
NEXT_PUBLIC_API_URL=https://api.yourdomain.com # Frontend API client URL
CORS_ORIGINS=["https://yourdomain.com"]        # Allow frontend to access API

# Security
API_KEY_SECRET=your-secure-api-key-here

# iOS Shortcut API Key (separate from main API key for security)
SHORTCUT_API_KEY=your-ios-shortcuts-api-secret-here

# JWT Authentication settings
JWT_SECRET_KEY=your-jwt-secret-key-here

# Database (production uses named volumes)
DATABASE_URL=sqlite:///./data/labcastarr.db
```

## 🌐 Nginx Proxy Manager Setup

Configure your existing Nginx Proxy Manager with **two separate proxy hosts**:

### Frontend Proxy Host
- **Domain**: `yourdomain.com` (e.g., `labcastarr.yourdomain.com`)
- **Scheme**: `http`
- **Forward Hostname/IP**: `labcastarr_frontend_1` (or container IP)
- **Forward Port**: `3000`
- **SSL**: Enable with Let's Encrypt
- **Force SSL**: Yes
- **HTTP/2**: Yes
- **HSTS**: Yes

### API/Backend Proxy Host
- **Domain**: `api.yourdomain.com` (e.g., `labcastarr-api.yourdomain.com`)
- **Scheme**: `http`
- **Forward Hostname/IP**: `labcastarr_backend_1` (or container IP)
- **Forward Port**: `8000`
- **SSL**: Enable with Let's Encrypt
- **Force SSL**: Yes
- **HTTP/2**: Yes
- **HSTS**: Yes

### Custom Nginx Configuration (Optional)
For the API proxy host, you can add this advanced configuration for better media streaming:

```nginx
# Enable range requests for media streaming (good for podcast files)
proxy_set_header Range $http_range;
proxy_set_header If-Range $http_if_range;
proxy_no_cache $http_range $http_if_range;

# Increase timeout for large media file uploads
proxy_read_timeout 300s;
proxy_connect_timeout 75s;
```

## 📺 iTunes Podcast Integration

Once deployed, your RSS feeds will be available at:

- **RSS Feed URL**: `https://api.yourdomain.com/v1/feeds/{channel_id}/feed.xml`
- **Media Files**: `https://api.yourdomain.com/v1/media/episodes/{episode_id}/audio`

### Submitting to Apple Podcasts
1. Verify your RSS feed is accessible via HTTPS
2. Test the feed with an RSS validator
3. Submit to Apple Podcasts Connect with your feed URL
4. Configure podcast metadata in the LabCastARR interface

## 📊 API Endpoints

- **Frontend**: `https://yourdomain.com`
- **API Health Check**: `https://api.yourdomain.com/health`
- **API Documentation**: `https://api.yourdomain.com/docs`
- **RSS Feeds**: `https://api.yourdomain.com/v1/feeds/`
- **Media Files**: `https://api.yourdomain.com/v1/media/episodes/{id}/audio`


## 🔒 Security Notes

- Change `API_KEY_SECRET` to a secure random string in production (Use openssl to generate a secure random string, eg: `openssl rand -base64 32`)
- Ensure your domain has proper SSL certificates via NPM
- The application automatically handles CORS for your configured domain
- Media files support range requests for podcast streaming
- RSS feeds include proper caching headers

## 💾 Data Persistence

Production deployment uses named Docker volumes:
- `labcastarr_data`: Database files
- `labcastarr_media`: Audio files
- `labcastarr_feeds`: RSS feed cache

These volumes persist between container restarts and updates.

## 🔄 Updates

To update the production deployment:

```bash
# Pull latest changes
git pull

# Rebuild and restart Production mode
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d

# Rebuild and restartDevelopment mode
docker compose --env-file .env.development -f docker-compose.dev.yml up --build

# Stop services (production/development)
docker compose -f docker-compose.prod.yml down  # or docker-compose.dev.yml
```

## 🐛 Troubleshooting

### Check container status
```bash
docker compose --env-file .env.production -f docker-compose.prod.yml ps
```

### View logs
```bash
# All services
docker compose --env-file .env.production -f docker-compose.prod.yml logs -f

# Specific service
docker compose --env-file .env.production -f docker-compose.prod.yml logs -f backend
docker compose --env-file .env.production -f docker-compose.prod.yml logs -f frontend
```

### Validate RSS feeds
```bash
# Test RSS feed accessibility
curl -I https://api.yourdomain.com/v1/feeds/1/feed.xml

# Test media file streaming
curl -I https://api.yourdomain.com/v1/media/episodes/1/audio

# Test frontend accessibility
curl -I https://yourdomain.com
```

## ✅ **Pre-Deployment Checklist**

- [ ] DNS records configured for both domains
- [ ] Configure your NGINX Proxy Manager proxy hosts configured with SSL
- [ ] `.env.production` file updated with your domains (use `.env.production.example` as a template)
- [ ] Generate and change in `.env.production.example` all secrets (API_KEY_SECRET, SHORTCUT_API_KEY, JWT_SECRET_KEY)
- [ ] Docker containers built and running



## 🚨 **Important Notes**

1. **CORS Configuration**: The frontend domain is automatically allowed to access the API domain via the `CORS_ORIGINS` setting.

2. **SSL Requirements**: Apple Podcasts **requires** HTTPS for RSS feeds. Your setup with Let's Encrypt certificates via NPM satisfies this requirement.

3. **Media Streaming**: The backend supports HTTP range requests for podcast streaming, which is handled by NPM.

4. **Security**: Change all  `API KEYS` to a secure random string in production (`openssl rand -base64 32`).

5. **Data Persistence**: Production deployment uses Docker mounted volumes to persist data between container restarts. Be careful with user permissions and ownership of the mounted volumes. Make sure we do not have copied `.ven` directory in the backend nor the node_modules directory in the `frontend` before building the images with docker.