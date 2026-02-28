# LabCastARR Production Configuration

## 🎯 **Your Specific Setup**

Based on your DNS configuration:
- **Frontend**: `labcastarr.oliverbarreto.com` → port 3000
- **API**: `labcastarr-api.oliverbarreto.com` → port 8000

## 📝 **Step-by-Step Configuration**

### 1. Environment Variables Configuration

Update your `.env` file with these specific values:

```env
# Application Environment
ENVIRONMENT=production
NODE_ENV=production

# Your specific domain configuration
DOMAIN=labcastarr.oliverbarreto.com
BASE_URL=https://labcastarr-api.oliverbarreto.com
FRONTEND_URL=https://labcastarr.oliverbarreto.com
BACKEND_URL=https://labcastarr-api.oliverbarreto.com
NEXT_PUBLIC_API_URL=https://labcastarr-api.oliverbarreto.com
CORS_ORIGINS=["https://labcastarr.oliverbarreto.com"]

# Security (IMPORTANT: Change this!)
API_KEY_SECRET=your-secure-random-key-here

# Database (production uses named volumes)
DATABASE_URL=sqlite:///./data/labcastarr.db
MEDIA_PATH=./media
FEEDS_PATH=./feeds
```

### 2. Nginx Proxy Manager Configuration

Configure **two separate proxy hosts** in your NPM:

#### Frontend Proxy Host
- **Domain Names**: `labcastarr.oliverbarreto.com`
- **Scheme**: `http`
- **Forward Hostname/IP**: `labcastarr_frontend_1` (or container IP)
- **Forward Port**: `3000`
- **SSL**: ✅ Enable with Let's Encrypt
- **Force SSL**: ✅ Yes
- **HTTP/2**: ✅ Yes
- **HSTS Enabled**: ✅ Yes

#### API Proxy Host
- **Domain Names**: `labcastarr-api.oliverbarreto.com`
- **Scheme**: `http`
- **Forward Hostname/IP**: `labcastarr_backend_1` (or container IP)
- **Forward Port**: `8000`
- **SSL**: ✅ Enable with Let's Encrypt
- **Force SSL**: ✅ Yes
- **HTTP/2**: ✅ Yes
- **HSTS Enabled**: ✅ Yes

### 3. Deployment Commands

```bash
# Production mode
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d

# Development mode
docker compose --env-file .env.development -f docker-compose.dev.yml up --build

# Stop services
docker compose -f docker-compose.prod.yml down  # or docker-compose.dev.yml
```


### 4. Final URLs

After deployment, your services will be available at:

- **Frontend Application**: `https://labcastarr.oliverbarreto.com`
- **API Documentation**: `https://labcastarr-api.oliverbarreto.com/docs`
- **API Health Check**: `https://labcastarr-api.oliverbarreto.com/health`
- **RSS Feed**: `https://labcastarr-api.oliverbarreto.com/v1/feeds/1/feed.xml`
- **Media Files**: `https://labcastarr-api.oliverbarreto.com/v1/media/episodes/{id}/audio`

### 5. iTunes Podcast Submission

Submit this RSS feed URL to Apple Podcasts:
```
https://labcastarr-api.oliverbarreto.com/v1/feeds/1/feed.xml
```

## ✅ **Pre-Deployment Checklist**

- [ ] DNS records configured for both domains
- [ ] `.env` file updated with your domains
- [ ] NPM proxy hosts configured with SSL
- [ ] `API_KEY_SECRET` changed from default
- [ ] Docker containers built and running
- [ ] RSS feed accessible via HTTPS
- [ ] Media files downloadable via HTTPS
- [ ] Frontend loads and can communicate with API

## 🔧 **Testing Your Setup**

```bash
# Test frontend
curl -I https://labcastarr.oliverbarreto.com

# Test API health
curl -I https://labcastarr-api.oliverbarreto.com/health

# Test RSS feed
curl -I https://labcastarr-api.oliverbarreto.com/v1/feeds/1/feed.xml

# Test media streaming
curl -I https://labcastarr-api.oliverbarreto.com/v1/media/episodes/1/audio
```

## 🚨 **Important Notes**

1. **CORS Configuration**: The frontend domain is automatically allowed to access the API domain via the `CORS_ORIGINS` setting.

2. **SSL Requirements**: Apple Podcasts **requires** HTTPS for RSS feeds. Your setup with Let's Encrypt certificates via NPM satisfies this requirement.

3. **Media Streaming**: The backend supports HTTP range requests for podcast streaming, which is handled by NPM.

4. **Security**: Change the `API_KEY_SECRET` to a secure random string in production.

5. **Data Persistence**: Production deployment uses Docker named volumes to persist data between container restarts.

## 🔄 **Updates**

To update your production deployment:

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d
```


Your application is now production-ready with proper domain separation and HTTPS support for iTunes podcast distribution! 🎉