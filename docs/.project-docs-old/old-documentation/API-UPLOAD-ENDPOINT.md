# File Upload API Endpoint Documentation

## Overview

The File Upload API endpoint allows users to create podcast episodes by uploading audio files directly, as an alternative to extracting audio from YouTube videos.

**Endpoint**: `POST /api/v1/episodes/upload`

**Content-Type**: `multipart/form-data`

**Authentication**: Required (X-API-Key header)

---

## Request Parameters

### Form Data Fields

| Field              | Type          | Required | Description                                     | Constraints                                                     |
| ------------------ | ------------- | -------- | ----------------------------------------------- | --------------------------------------------------------------- |
| `channel_id`       | integer       | Yes      | ID of the channel to associate the episode with | Must be > 0                                                     |
| `title`            | string        | Yes      | Episode title                                   | 1-500 characters                                                |
| `description`      | string        | No       | Episode description                             | Max 5000 characters                                             |
| `publication_date` | string        | No       | Publication date in ISO format                  | ISO 8601 format (YYYY-MM-DDTHH:MM:SS), defaults to current time |
| `tags`             | array[string] | No       | List of tags for the episode                    | Max 10 tags, each max 50 characters                             |
| `audio_file`       | file          | Yes      | Audio file to upload                            | See supported formats below                                     |

### Supported Audio Formats

| Format | MIME Type                                | Max Size | Conversion               |
| ------ | ---------------------------------------- | -------- | ------------------------ |
| MP3    | `audio/mpeg`                             | 500MB    | ❌ No (stored as-is)      |
| M4A    | `audio/mp4`, `audio/x-m4a`               | 500MB    | ❌ No (stored as-is)      |
| WAV    | `audio/wav`, `audio/x-wav`, `audio/wave` | 500MB    | ✅ Yes (converted to MP3) |
| OGG    | `audio/ogg`                              | 500MB    | ✅ Yes (converted to MP3) |
| FLAC   | `audio/flac`, `audio/x-flac`             | 500MB    | ✅ Yes (converted to MP3) |

---

## Request Example

### cURL

```bash
curl -X POST "http://localhost:8000/api/v1/episodes/upload" \
  -H "X-API-Key: your-api-key-here" \
  -F "channel_id=1" \
  -F "title=My Awesome Podcast Episode" \
  -F "description=This is a great episode about technology" \
  -F "publication_date=2025-10-18T12:00:00" \
  -F "tags=technology" \
  -F "tags=podcast" \
  -F "audio_file=@/path/to/audio.mp3"
```

### JavaScript (Fetch API)

```javascript
const formData = new FormData();
formData.append('channel_id', '1');
formData.append('title', 'My Awesome Podcast Episode');
formData.append('description', 'This is a great episode about technology');
formData.append('publication_date', '2025-10-18T12:00:00');
formData.append('tags', 'technology');
formData.append('tags', 'podcast');
formData.append('audio_file', audioFile); // File object from input

const response = await fetch('http://localhost:8000/api/v1/episodes/upload', {
  method: 'POST',
  headers: {
    'X-API-Key': 'your-api-key-here'
  },
  body: formData
});

const episode = await response.json();
```

### Python (requests)

```python
import requests

url = "http://localhost:8000/api/v1/episodes/upload"
headers = {
    "X-API-Key": "your-api-key-here"
}
data = {
    "channel_id": 1,
    "title": "My Awesome Podcast Episode",
    "description": "This is a great episode about technology",
    "publication_date": "2025-10-18T12:00:00",
    "tags": ["technology", "podcast"]
}
files = {
    "audio_file": open("/path/to/audio.mp3", "rb")
}

response = requests.post(url, headers=headers, data=data, files=files)
episode = response.json()
```

---

## Response

### Success Response (201 Created)

```json
{
  "id": 42,
  "channel_id": 1,
  "title": "My Awesome Podcast Episode",
  "description": "This is a great episode about technology",
  "publication_date": "2025-10-18T12:00:00Z",
  "audio_file_path": "channel_1/audio_1729252800.123456.mp3",
  "video_url": "",
  "thumbnail_url": "",
  "duration": 3600,
  "keywords": [],
  "status": "completed",
  "retry_count": 0,
  "download_date": "2025-10-18T12:00:00Z",
  "media_file_size": 52428800,
  "source_type": "upload",
  "original_filename": "audio.mp3",
  "tags": [
    {
      "id": 1,
      "name": "technology",
      "channel_id": 1
    },
    {
      "id": 2,
      "name": "podcast",
      "channel_id": 1
    }
  ]
}
```

### Response Fields

| Field               | Type    | Description                                     |
| ------------------- | ------- | ----------------------------------------------- |
| `id`                | integer | Unique episode ID                               |
| `channel_id`        | integer | Channel ID                                      |
| `title`             | string  | Episode title                                   |
| `description`       | string  | Episode description                             |
| `publication_date`  | string  | Publication date (ISO 8601)                     |
| `audio_file_path`   | string  | Relative path to audio file                     |
| `video_url`         | string  | Empty for uploaded episodes                     |
| `thumbnail_url`     | string  | Empty for uploaded episodes                     |
| `duration`          | integer | Audio duration in seconds                       |
| `keywords`          | array   | Empty for uploaded episodes                     |
| `status`            | string  | Episode status (always "completed" for uploads) |
| `retry_count`       | integer | Always 0 for uploads                            |
| `download_date`     | string  | Upload timestamp                                |
| `media_file_size`   | integer | File size in bytes                              |
| `source_type`       | string  | "upload" for uploaded episodes                  |
| `original_filename` | string  | Original filename of uploaded file              |
| `tags`              | array   | Associated tags                                 |

---

## Error Responses

### 400 Bad Request - Invalid File Format

```json
{
  "detail": {
    "error": "Invalid file format. Only MP3, M4A, WAV, OGG, FLAC files are supported.",
    "code": "INVALID_FILE_FORMAT",
    "allowed_formats": ["mp3", "m4a", "wav", "ogg", "flac"]
  }
}
```

**Causes**:
- File MIME type not in allowed list
- File extension doesn't match content
- Corrupted or invalid audio file

---

### 413 Payload Too Large - File Size Limit

```json
{
  "detail": {
    "error": "File size exceeds maximum allowed size of 500MB",
    "code": "FILE_TOO_LARGE",
    "max_size_mb": 500
  }
}
```

**Causes**:
- File size exceeds 500MB limit
- Request body too large

---

### 422 Unprocessable Entity - Conversion Error

```json
{
  "detail": {
    "error": "Audio conversion failed. FFmpeg output: [error details]",
    "code": "FILE_CONVERSION_ERROR"
  }
}
```

**Causes**:
- FFmpeg conversion failure
- Unsupported audio codec
- Corrupted audio stream

---

### 409 Conflict - Duplicate Episode

```json
{
  "detail": {
    "error": "Episode with title 'My Awesome Podcast Episode' already exists in this channel",
    "code": "DUPLICATE_EPISODE"
  }
}
```

**Causes**:
- Episode with same title already exists in channel
- Case-insensitive title matching

---

### 400 Bad Request - Validation Error

```json
{
  "detail": {
    "error": "Title cannot be empty",
    "code": "VALIDATION_ERROR"
  }
}
```

**Causes**:
- Missing required fields
- Invalid field values (e.g., empty title, invalid date format)
- Tag validation errors (too many tags, tag too long)

---

### 500 Internal Server Error

```json
{
  "detail": {
    "error": "Internal server error",
    "code": "INTERNAL_ERROR"
  }
}
```

**Causes**:
- Unexpected server error
- Database connection issues
- File system errors

---

## Upload Workflow

### Client-Side (Frontend)

1. **File Selection**
   - User drags and drops file or selects via file picker
   - Client validates file size (< 500MB)
   - Client validates MIME type
   - Client extracts audio duration using Web Audio API (if supported)

2. **Episode Details**
   - User fills in title, description, tags, publication date
   - Form validation ensures required fields are present

3. **Upload**
   - FormData constructed with all fields
   - File uploaded via fetch/axios with progress tracking
   - Upload can be cancelled mid-flight

4. **Progress & Completion**
   - Upload progress displayed to user
   - Success: Episode appears in list, user redirected
   - Error: User-friendly error message displayed, retry option

### Server-Side (Backend)

1. **Request Reception**
   - FastAPI receives multipart/form-data request
   - Form fields validated via Pydantic schema
   - File size checked before processing

2. **File Streaming**
   - File streamed to temporary directory
   - Streaming prevents memory overflow for large files
   - Temp file cleaned up on success or error

3. **Validation**
   - MIME type verified using python-magic
   - File size verified
   - Audio metadata extracted using mutagen

4. **Conversion (if needed)**
   - WAV, OGG, FLAC files converted to MP3 using FFmpeg
   - MP3 and M4A files stored as-is (no conversion)
   - Conversion quality: VBR MP3 ~190 kbps

5. **Storage**
   - File moved to final storage location: `media/channel_{id}/`
   - Filename sanitized and timestamped
   - File permissions set correctly

6. **Episode Creation**
   - Episode entity created in database
   - `source_type` set to "upload"
   - `original_filename` stored for reference
   - Tags associated with episode
   - Status set to "completed" (immediate availability)

7. **RSS Feed Update**
   - RSS feed regenerated to include new episode
   - Episode available in podcast apps immediately

8. **Event Logging**
   - Upload start, completion, conversion events logged
   - Error events logged with details for debugging

---

## Configuration

### Backend Configuration (`backend/app/core/config.py`)

```python
# File Upload settings
max_upload_file_size_mb: int = 500
allowed_upload_formats: List[str] = ["mp3", "m4a", "wav", "ogg", "flac"]
target_audio_format: str = "mp3"
target_audio_quality: str = "192"  # kbps for MP3
convert_uploads_to_target: bool = True
preserve_m4a: bool = True  # Don't convert M4A files
```

### Environment Variables

No additional environment variables required. Uses existing:
- `MEDIA_PATH` - Directory for storing audio files (default: `./media`)
- `TEMP_PATH` - Directory for temporary files (default: `./media/temp`)

---

## Testing

### Manual Testing

See `docs/tasks/task-0029-upload-episode-testing-guide.md` for comprehensive testing guide.

### Quick Test

```bash
# Create a test audio file
ffmpeg -f lavfi -i "sine=frequency=1000:duration=5" test.mp3

# Upload via cURL
curl -X POST "http://localhost:8000/api/v1/episodes/upload" \
  -H "X-API-Key: your-api-key-here" \
  -F "channel_id=1" \
  -F "title=Test Episode" \
  -F "audio_file=@test.mp3"
```

---

## Security Considerations

### File Validation
- ✅ MIME type verification using python-magic (not just extension)
- ✅ File size limits enforced
- ✅ Filename sanitization to prevent path traversal
- ✅ Audio integrity validation using mutagen

### Storage Security
- ✅ Files stored outside web root
- ✅ Timestamped filenames prevent collisions
- ✅ Proper file permissions set
- ✅ Temp files cleaned up on error

### API Security
- ✅ Authentication required (X-API-Key)
- ✅ Rate limiting (if configured)
- ✅ Input validation via Pydantic
- ✅ Error messages don't leak sensitive info

---

## Performance Considerations

### Upload Performance
- **Streaming**: Large files streamed to disk, not loaded into memory
- **Async Processing**: File processing uses async I/O
- **Background Tasks**: Conversion can be moved to background tasks if needed

### Storage Efficiency
- **Automatic Conversion**: Converts large formats (WAV, FLAC) to compressed MP3
- **No Duplicate Conversion**: MP3 and M4A files stored as-is
- **Temp File Cleanup**: Temporary files removed after processing

### Scalability
- **Concurrent Uploads**: Supports multiple simultaneous uploads
- **Resource Management**: FFmpeg processes managed efficiently
- **Database Indexing**: `source_type` field indexed for fast queries

---

## Troubleshooting

### FFmpeg Not Found
**Error**: `FileConversionError: FFmpeg not found`

**Solution**:
```bash
# Install FFmpeg
brew install ffmpeg  # macOS
apt-get install ffmpeg  # Ubuntu/Debian
```

### File Size Limit Exceeded
**Error**: `413 Payload Too Large`

**Solution**:
- Check nginx/proxy settings: `client_max_body_size 500M;`
- Verify backend config: `max_upload_file_size_mb = 500`

### Conversion Fails
**Error**: `422 FILE_CONVERSION_ERROR`

**Solution**:
- Verify FFmpeg installed and in PATH
- Check backend logs for FFmpeg output
- Test FFmpeg manually: `ffmpeg -i input.wav output.mp3`

### Upload Hangs
**Symptom**: Upload never completes

**Solution**:
- Check network connection
- Verify backend is running
- Check backend logs for errors
- Increase timeout settings if needed

---

## Related Documentation

- [Testing Guide](../tasks/task-0029-upload-episode-testing-guide.md)
- [Implementation Plan](../tasks/task-0029-upload-episode-plan-v2.md)
- [Implementation Summary](../tasks/task-0029-upload-episode-implementation-summary.md)
- [Backend Architecture](./FUNCTIONALITY.md)
- [Deployment Guide](./DEPLOYMENT.md)

---

## Changelog

### 2025-10-18 - Initial Release
- Added file upload endpoint
- Support for MP3, M4A, WAV, OGG, FLAC formats
- Automatic format conversion using FFmpeg
- Client-side and server-side validation
- Comprehensive error handling
- Event logging for all upload operations
- Database migration for `source_type` and `original_filename` fields



