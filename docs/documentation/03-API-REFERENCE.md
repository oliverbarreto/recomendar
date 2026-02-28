# LabCastARR API Reference

**Document Version:** 1.0
**Last Updated:** 2026-01-29
**Base URL:** `http://localhost:8000` (dev) / `https://api.yourdomain.com` (prod)

---

## Table of Contents

1. [Authentication](#authentication)
2. [Common Headers](#common-headers)
3. [Response Formats](#response-formats)
4. [API Endpoints](#api-endpoints)
   - [Health Check](#health-check)
   - [Authentication](#authentication-endpoints)
   - [Channels](#channels-endpoints)
   - [Episodes](#episodes-endpoints)
   - [Tags](#tags-endpoints)
   - [Search](#search-endpoints)
   - [Feeds](#feeds-endpoints)
   - [Media](#media-endpoints)
   - [Followed Channels](#followed-channels-endpoints)
   - [YouTube Videos](#youtube-videos-endpoints)
   - [Notifications](#notifications-endpoints)
   - [Celery Tasks](#celery-tasks-endpoints)
   - [Events](#events-endpoints)
   - [System](#system-endpoints)
5. [Error Handling](#error-handling)

---

## Authentication

All API endpoints (except `/health/` and `/v1/auth/login`) require authentication.

### API Key Authentication

Required for all requests:

```http
X-API-Key: your-api-key-here
```

### JWT Bearer Token

Required for protected endpoints after login:

```http
Authorization: Bearer your-jwt-access-token
```

### Token Expiration

| Token Type | Duration | Refresh Strategy |
|------------|----------|------------------|
| Access Token | 60 minutes | Auto-refresh at 80% (48 min) |
| Refresh Token | 30 days | Activity-based extension |

---

## Common Headers

### Request Headers

| Header | Required | Description |
|--------|----------|-------------|
| `X-API-Key` | Yes | API authentication key |
| `Authorization` | Yes* | Bearer token (after login) |
| `Content-Type` | For POST/PUT | `application/json` or `multipart/form-data` |

### Response Headers

| Header | Description |
|--------|-------------|
| `Content-Type` | `application/json` for API, `audio/mpeg` for media |
| `Accept-Ranges` | `bytes` for media streaming |

---

## Response Formats

### Success Response

```json
{
  "id": 1,
  "field": "value",
  "created_at": "2025-01-15T10:30:00Z"
}
```

### List Response (with pagination)

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "size": 20,
  "pages": 5
}
```

### Error Response

```json
{
  "detail": {
    "error": "Error message",
    "code": "ERROR_CODE"
  }
}
```

---

## API Endpoints

### Health Check

#### GET `/health/`

Check application health status.

**Note:** Trailing slash is required.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00Z",
  "database": "connected",
  "version": "1.0.0"
}
```

---

### Authentication Endpoints

#### POST `/v1/auth/login`

Authenticate user and obtain JWT tokens.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

#### POST `/v1/auth/refresh`

Refresh access token using refresh token.

**Request:**
```json
{
  "refresh_token": "eyJ..."
}
```

**Response (200):**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

#### POST `/v1/auth/logout`

Invalidate current session.

**Response (200):**
```json
{
  "message": "Successfully logged out"
}
```

---

### Channels Endpoints

#### GET `/v1/channels/`

List all channels for authenticated user.

**Response (200):**
```json
[
  {
    "id": 1,
    "title": "My Podcast",
    "description": "A great podcast",
    "author_name": "Host Name",
    "feed_url": "https://api.domain.com/v1/feeds/1/feed.xml",
    "episode_count": 25,
    "created_at": "2025-01-01T00:00:00Z"
  }
]
```

---

#### POST `/v1/channels/`

Create a new podcast channel.

**Request:**
```json
{
  "title": "My New Podcast",
  "description": "Description here",
  "author_name": "Host Name",
  "author_email": "host@example.com",
  "language": "en",
  "category": "Technology"
}
```

**Response (201):**
```json
{
  "id": 1,
  "title": "My New Podcast",
  "feed_url": "https://api.domain.com/v1/feeds/1/feed.xml",
  ...
}
```

---

#### GET `/v1/channels/{channel_id}`

Get channel details.

---

#### PUT `/v1/channels/{channel_id}`

Update channel settings.

---

#### DELETE `/v1/channels/{channel_id}`

Delete channel and all episodes.

---

### Episodes Endpoints

#### GET `/v1/episodes/`

List episodes with optional filters.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `channel_id` | int | Filter by channel |
| `status` | string | Filter by status |
| `page` | int | Page number (default: 1) |
| `size` | int | Page size (default: 20) |

**Response (200):**
```json
{
  "items": [
    {
      "id": 1,
      "channel_id": 1,
      "title": "Episode Title",
      "description": "Description",
      "video_url": "https://youtube.com/watch?v=xxx",
      "thumbnail_url": "https://...",
      "duration": 3600,
      "status": "completed",
      "source_type": "youtube",
      "tags": [{"id": 1, "name": "tech", "color": "#ff0000"}],
      "publication_date": "2025-01-15T10:00:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "size": 20
}
```

---

#### POST `/v1/episodes/analyze`

Analyze YouTube URL and extract metadata.

**Request:**
```json
{
  "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```

**Response (200):**
```json
{
  "title": "Video Title",
  "description": "Video description...",
  "thumbnail_url": "https://...",
  "duration": 212,
  "channel_name": "Channel Name",
  "publish_date": "2025-01-01T00:00:00Z"
}
```

---

#### POST `/v1/episodes/`

Create episode from YouTube URL.

**Request:**
```json
{
  "channel_id": 1,
  "video_url": "https://www.youtube.com/watch?v=xxx",
  "title": "Optional custom title",
  "description": "Optional custom description",
  "tags": ["tech", "podcast"],
  "publication_date": "2025-01-15T10:00:00Z"
}
```

**Response (201):**
```json
{
  "id": 1,
  "channel_id": 1,
  "title": "Episode Title",
  "status": "pending",
  ...
}
```

---

#### POST `/v1/episodes/upload`

Upload audio file to create episode.

**Content-Type:** `multipart/form-data`

**Form Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `channel_id` | int | Yes | Target channel |
| `title` | string | Yes | Episode title |
| `description` | string | No | Episode description |
| `publication_date` | string | No | ISO 8601 date |
| `tags` | string[] | No | Tag names (max 10) |
| `audio_file` | file | Yes | Audio file (max 500MB) |

**Supported Formats:** MP3, M4A, WAV, OGG, FLAC

**Response (201):**
```json
{
  "id": 1,
  "title": "Uploaded Episode",
  "status": "completed",
  "source_type": "upload",
  "original_filename": "podcast.mp3",
  "duration": 1800,
  "media_file_size": 52428800
}
```

---

#### GET `/v1/episodes/{episode_id}`

Get episode details.

---

#### PUT `/v1/episodes/{episode_id}`

Update episode metadata.

---

#### DELETE `/v1/episodes/{episode_id}`

Delete episode and associated files.

---

#### GET `/v1/episodes/{episode_id}/progress`

Get download progress for pending episode.

**Response (200):**
```json
{
  "episode_id": 1,
  "status": "processing",
  "progress": 75,
  "current_step": "Converting audio..."
}
```

---

### Tags Endpoints

#### GET `/v1/tags/`

List all tags for a channel.

**Query Parameters:**
| Parameter | Type | Required |
|-----------|------|----------|
| `channel_id` | int | Yes |

---

#### POST `/v1/tags/`

Create a new tag.

**Request:**
```json
{
  "name": "Technology",
  "color": "#3b82f6",
  "channel_id": 1
}
```

---

#### PUT `/v1/tags/{tag_id}`

Update tag.

---

#### DELETE `/v1/tags/{tag_id}`

Delete tag.

---

#### POST `/v1/tags/bulk`

Bulk assign tags to episodes.

**Request:**
```json
{
  "episode_ids": [1, 2, 3],
  "tag_ids": [1, 2]
}
```

---

### Search Endpoints

#### GET `/v1/search/`

Search episodes with filters.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `q` | string | Search query |
| `channel_id` | int | Filter by channel |
| `status` | string | Filter by status |
| `tags` | string | Comma-separated tag IDs |
| `date_from` | string | Start date (ISO 8601) |
| `date_to` | string | End date (ISO 8601) |
| `min_duration` | int | Min duration (seconds) |
| `max_duration` | int | Max duration (seconds) |
| `page` | int | Page number |
| `size` | int | Page size |

---

### Feeds Endpoints

#### GET `/v1/feeds/{channel_id}/feed.xml`

Get RSS feed for channel.

**Response:** iTunes-compatible XML RSS feed

**Headers:**
```
Content-Type: application/rss+xml
Cache-Control: public, max-age=300
```

---

### Media Endpoints

#### GET `/v1/media/episodes/{episode_id}/audio`

Stream episode audio file.

**Supports:** HTTP Range requests for seeking

**Response Headers:**
```
Content-Type: audio/mpeg
Accept-Ranges: bytes
Content-Length: 52428800
```

---

### Followed Channels Endpoints

#### GET `/v1/followed-channels/`

List all followed YouTube channels.

**Response (200):**
```json
[
  {
    "id": 1,
    "youtube_channel_id": "UCxxx",
    "youtube_channel_name": "Channel Name",
    "youtube_channel_url": "https://youtube.com/channel/UCxxx",
    "thumbnail_url": "https://...",
    "auto_approve": false,
    "auto_approve_channel_id": null,
    "last_checked": "2025-01-15T10:00:00Z",
    "video_count": 25,
    "created_at": "2025-01-01T00:00:00Z"
  }
]
```

---

#### POST `/v1/followed-channels/`

Follow a new YouTube channel.

**Request:**
```json
{
  "url": "https://www.youtube.com/@channelname",
  "auto_approve": false,
  "auto_approve_channel_id": null
}
```

**Response (201):**
```json
{
  "id": 1,
  "youtube_channel_id": "UCxxx",
  "youtube_channel_name": "Channel Name",
  ...
}
```

---

#### PUT `/v1/followed-channels/{id}`

Update followed channel settings (auto-approve).

**Request:**
```json
{
  "auto_approve": true,
  "auto_approve_channel_id": 1
}
```

---

#### DELETE `/v1/followed-channels/{id}`

Unfollow channel and delete associated videos.

**Response:** 204 No Content

---

#### POST `/v1/followed-channels/{id}/check`

Trigger video discovery (yt-dlp method - slow, comprehensive).

**Response (202):**
```json
{
  "task_id": "abc123-def456",
  "message": "Check started"
}
```

---

#### POST `/v1/followed-channels/{id}/check-rss`

Trigger video discovery (RSS method - fast).

**Response (202):**
```json
{
  "task_id": "abc123-def456",
  "message": "RSS check started"
}
```

---

#### POST `/v1/followed-channels/{id}/backfill`

Backfill historical videos.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_videos` | int | 20 | Max videos to fetch |
| `year` | int | current | Filter by year |

**Response (202):**
```json
{
  "task_id": "abc123-def456",
  "message": "Backfill started"
}
```

---

### YouTube Videos Endpoints

#### GET `/v1/youtube-videos/`

List discovered videos with filters.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `followed_channel_id` | int | Filter by channel |
| `state` | string | Filter by state |
| `page` | int | Page number |
| `size` | int | Page size |

**Response (200):**
```json
{
  "items": [
    {
      "id": 1,
      "video_id": "dQw4w9WgXcQ",
      "title": "Video Title",
      "url": "https://youtube.com/watch?v=xxx",
      "thumbnail_url": "https://...",
      "duration": 212,
      "publish_date": "2025-01-01T00:00:00Z",
      "state": "pending_review",
      "episode_id": null,
      "followed_channel": {
        "id": 1,
        "youtube_channel_name": "Channel Name"
      }
    }
  ],
  "total": 50
}
```

**State Values:**
- `pending_review` - Awaiting user action
- `reviewed` - Marked for later
- `queued` - Queued for episode creation
- `downloading` - Creating episode
- `episode_created` - Episode complete
- `discarded` - User discarded

---

#### POST `/v1/youtube-videos/{id}/review`

Mark video as reviewed.

---

#### POST `/v1/youtube-videos/{id}/discard`

Discard video.

---

#### POST `/v1/youtube-videos/{id}/create-episode`

Create episode from video.

**Request:**
```json
{
  "channel_id": 1
}
```

**Response (202):**
```json
{
  "task_id": "abc123-def456",
  "message": "Episode creation started"
}
```

---

### Notifications Endpoints

#### GET `/v1/notifications/`

List user notifications.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `unread_only` | bool | Filter unread |
| `page` | int | Page number |
| `size` | int | Page size |

---

#### GET `/v1/notifications/unread-count`

Get unread notification count.

**Response (200):**
```json
{
  "count": 5
}
```

---

#### POST `/v1/notifications/{id}/read`

Mark notification as read.

---

#### POST `/v1/notifications/mark-all-read`

Mark all notifications as read.

---

#### DELETE `/v1/notifications/{id}`

Delete notification.

---

### Celery Tasks Endpoints

#### GET `/v1/celery-tasks/{task_id}`

Get task status for polling.

**Response (200):**
```json
{
  "task_id": "abc123-def456",
  "task_name": "Check for new videos",
  "status": "PROGRESS",
  "progress": 75,
  "current_step": "Fetching video metadata...",
  "result": null,
  "error_message": null,
  "started_at": "2025-01-15T10:00:00Z",
  "completed_at": null
}
```

**Status Values:**
- `PENDING` - Queued
- `STARTED` - Running
- `PROGRESS` - Running with updates
- `SUCCESS` - Completed
- `FAILURE` - Failed
- `RETRY` - Retrying

---

### Events Endpoints

#### GET `/v1/events/`

List activity events.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `event_type` | string | Filter by type |
| `resource_type` | string | Filter by resource |
| `severity` | string | Filter by severity |
| `date_from` | string | Start date |
| `date_to` | string | End date |
| `page` | int | Page number |
| `size` | int | Page size |

---

### System Endpoints

#### GET `/v1/system/info`

Get system information.

**Response (200):**
```json
{
  "version": "1.0.0",
  "environment": "production",
  "database_size": "45.2 MB",
  "media_storage": "2.5 GB",
  "episode_count": 150,
  "channel_count": 3
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 202 | Accepted (async task queued) |
| 204 | No Content (successful delete) |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (missing/invalid token) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found |
| 409 | Conflict (duplicate resource) |
| 413 | Payload Too Large (file upload) |
| 422 | Unprocessable Entity (conversion error) |
| 500 | Internal Server Error |

### Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Request validation failed |
| `INVALID_FILE_FORMAT` | Unsupported audio format |
| `FILE_TOO_LARGE` | File exceeds 500MB limit |
| `FILE_CONVERSION_ERROR` | FFmpeg conversion failed |
| `DUPLICATE_EPISODE` | Episode already exists |
| `CHANNEL_NOT_FOUND` | Channel does not exist |
| `EPISODE_NOT_FOUND` | Episode does not exist |
| `INVALID_STATE_TRANSITION` | Invalid video state change |

---

**End of Document**
