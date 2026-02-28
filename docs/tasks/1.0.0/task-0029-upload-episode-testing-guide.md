# File Upload Episode Creation - Testing Guide

## Overview
This guide provides step-by-step instructions for testing the file upload feature in both development and production environments.

---

## Prerequisites

### 1. Verify FFmpeg Installation
FFmpeg is required for audio conversion (WAV, OGG, FLAC → MP3).

```bash
# Check if FFmpeg is installed
ffmpeg -version

# If not installed on macOS:
brew install ffmpeg

# If not installed on Ubuntu/Debian:
sudo apt-get update && sudo apt-get install ffmpeg
```

### 2. Apply Database Migration

**Development Environment:**
```bash
cd backend
# If using uv (recommended)
uv run alembic upgrade head

# Or if using traditional Python
python -m alembic upgrade head
```

**Production Environment:**
The migration will be applied automatically when the Docker container starts.

---

## Testing Environments

### Development Environment Testing

**Start the development environment:**
```bash
# From project root
docker compose --env-file .env.development -f docker-compose.dev.yml up --build
```

**Access the application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Production Environment Testing

**Start the production environment:**
```bash
# From project root
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d
```

**Access the application:**
- Frontend: https://your-domain.com (or configured domain)
- Backend API: https://your-domain.com/api
- API Docs: https://your-domain.com/api/docs

**Stop services:**
```bash
# Development
docker compose -f docker-compose.dev.yml down

# Production
docker compose -f docker-compose.prod.yml down
```

---

## Test Cases

### Test Case 1: Upload Valid MP3 File ✅

**Objective**: Verify MP3 files upload without conversion

**Steps**:
1. Navigate to "Add New Episode" page
2. Click "Upload Audio File" tab
3. Drag and drop or select a valid MP3 file (< 500MB)
4. Verify file preview shows correct name and size
5. Click "Next"
6. Fill in episode details:
   - Title: "Test MP3 Episode"
   - Description: "Testing MP3 upload"
   - Publication Date: Today's date
   - Tags: "test", "mp3"
7. Click "Upload Episode"
8. Verify upload progress shows
9. Verify success message appears
10. Navigate to episodes list
11. Verify episode appears with status "completed"

**Expected Results**:
- ✅ File uploads successfully
- ✅ No conversion occurs (MP3 stored as-is)
- ✅ Episode created with status "completed"
- ✅ Episode appears in RSS feed
- ✅ Audio file playable in browser

---

### Test Case 2: Upload WAV File with Conversion ✅

**Objective**: Verify WAV files are converted to MP3

**Steps**:
1. Upload a valid WAV file (< 500MB)
2. Fill in episode details
3. Submit upload
4. Monitor backend logs for conversion messages

**Expected Results**:
- ✅ File uploads successfully
- ✅ FFmpeg conversion occurs (WAV → MP3)
- ✅ Converted file stored in media directory
- ✅ Episode duration extracted correctly
- ✅ File size reduced after conversion
- ✅ Audio quality preserved

**Verification**:
```bash
# Check backend logs for conversion
docker compose -f docker-compose.dev.yml logs backend | grep -i "ffmpeg\|conversion"

# Verify file format
file backend/media/channel_1/*.mp3
```

---

### Test Case 3: File Size Limit Error ❌

**Objective**: Verify files > 500MB are rejected

**Steps**:
1. Attempt to upload a file > 500MB
2. Observe error message

**Expected Results**:
- ❌ Upload rejected before processing
- ❌ Error message: "File size exceeds maximum allowed size of 500MB"
- ❌ HTTP 413 Payload Too Large
- ❌ No file stored on server
- ❌ No database record created

---

### Test Case 4: Invalid File Format Error ❌

**Objective**: Verify non-audio files are rejected

**Steps**:
1. Attempt to upload a .txt, .pdf, or .jpg file
2. Observe error message

**Expected Results**:
- ❌ Upload rejected immediately
- ❌ Error message: "Invalid file format. Allowed formats: MP3, M4A, WAV, OGG, FLAC"
- ❌ HTTP 400 Bad Request
- ❌ No file stored on server

---

### Test Case 5: Duplicate Title Error ❌

**Objective**: Verify duplicate episode titles are rejected

**Steps**:
1. Upload an episode with title "Test Episode"
2. Attempt to upload another episode with same title "Test Episode"
3. Observe error message

**Expected Results**:
- ❌ Second upload rejected
- ❌ Error message: "Episode with this title already exists in this channel"
- ❌ HTTP 409 Conflict
- ❌ First episode remains unchanged

---

### Test Case 6: Corrupted Audio File Error ❌

**Objective**: Verify corrupted audio files are rejected

**Steps**:
1. Create a fake audio file:
   ```bash
   echo "fake audio data" > fake.mp3
   ```
2. Attempt to upload the fake file
3. Observe error message

**Expected Results**:
- ❌ Upload rejected during validation
- ❌ Error message: "Failed to validate audio file" or "File could not be processed"
- ❌ HTTP 400 Bad Request or 422 Unprocessable Entity
- ❌ No file stored on server

---

### Test Case 7: Network Interruption During Upload 🔄

**Objective**: Verify graceful handling of network interruptions

**Steps**:
1. Start uploading a large file (100MB+)
2. Interrupt network connection mid-upload
3. Observe error handling

**Expected Results**:
- ❌ Upload fails with network error
- ❌ Error message: "Network error. Please check your connection."
- ❌ Temp files cleaned up on server
- ❌ No orphaned database records
- ✅ User can retry upload

---

### Test Case 8: Cancel Upload Mid-Flight 🔄

**Objective**: Verify upload can be cancelled

**Steps**:
1. Start uploading a large file
2. Click "Cancel" button during upload
3. Verify cleanup

**Expected Results**:
- ✅ Upload cancelled immediately
- ✅ Temp files removed from server
- ✅ No database record created
- ✅ User returned to form

---

### Test Case 9: Upload with Tags ✅

**Objective**: Verify tags are associated correctly

**Steps**:
1. Upload an audio file
2. Add multiple tags: "tech", "podcast", "interview"
3. Submit upload
4. Verify tags in episode details

**Expected Results**:
- ✅ Episode created successfully
- ✅ All tags associated with episode
- ✅ Tags searchable/filterable
- ✅ Tags appear in episode list

---

### Test Case 10: Upload M4A File (No Conversion) ✅

**Objective**: Verify M4A files stored without conversion

**Steps**:
1. Upload a valid M4A file
2. Verify no conversion occurs (preserve_m4a = true)

**Expected Results**:
- ✅ File uploads successfully
- ✅ No conversion occurs (M4A stored as-is)
- ✅ Episode playable in iTunes/Apple Podcasts
- ✅ MIME type: audio/mp4

---

### Test Case 11: Upload FLAC File with Conversion ✅

**Objective**: Verify FLAC files converted to MP3

**Steps**:
1. Upload a valid FLAC file
2. Monitor conversion process

**Expected Results**:
- ✅ File uploads successfully
- ✅ FFmpeg conversion occurs (FLAC → MP3)
- ✅ Audio quality preserved
- ✅ File size reduced significantly

---

### Test Case 12: Upload OGG File with Conversion ✅

**Objective**: Verify OGG files converted to MP3

**Steps**:
1. Upload a valid OGG file
2. Monitor conversion process

**Expected Results**:
- ✅ File uploads successfully
- ✅ FFmpeg conversion occurs (OGG → MP3)
- ✅ Audio quality preserved

---

### Test Case 13: Special Characters in Filename 🔒

**Objective**: Verify filename sanitization

**Steps**:
1. Upload a file with special characters: `test/../../../etc/passwd.mp3`
2. Verify filename is sanitized

**Expected Results**:
- ✅ File uploads successfully
- ✅ Filename sanitized: `test_etc_passwd.mp3`
- ✅ No path traversal vulnerability
- ✅ File stored in correct directory

---

### Test Case 14: Concurrent Uploads 🔄

**Objective**: Verify multiple simultaneous uploads

**Steps**:
1. Open multiple browser tabs
2. Start uploading different files simultaneously
3. Monitor server performance

**Expected Results**:
- ✅ All uploads process successfully
- ✅ No resource exhaustion
- ✅ No file conflicts
- ✅ Each episode created correctly

---

### Test Case 15: Large File Upload (500MB) ⏱️

**Objective**: Verify maximum file size handling

**Steps**:
1. Upload a file close to 500MB
2. Monitor upload progress and server memory

**Expected Results**:
- ✅ File uploads successfully
- ✅ Streaming prevents memory overflow
- ✅ Upload completes in reasonable time (< 5 minutes on good connection)
- ✅ Server memory usage remains stable

---

## RSS Feed Compatibility Testing

### Test RSS Feed Validation

**iTunes Podcast Validator:**
1. Generate RSS feed URL: `http://localhost:8000/api/v1/feeds/channel/1`
2. Visit: https://podba.se/validate/
3. Enter feed URL
4. Verify validation passes

**Spotify Podcast Validator:**
1. Visit: https://podcasters.spotify.com/
2. Submit feed URL
3. Verify validation passes

**Manual RSS Inspection:**
```bash
# Fetch RSS feed
curl http://localhost:8000/api/v1/feeds/channel/1 > feed.xml

# Check for uploaded episodes
grep -A 10 "source_type.*upload" feed.xml

# Verify enclosure tags
grep "<enclosure" feed.xml
```

**Expected Results**:
- ✅ RSS feed validates with iTunes
- ✅ RSS feed validates with Spotify
- ✅ Uploaded episodes appear in feed
- ✅ `<enclosure>` tags have correct:
  - `url`: Points to audio file
  - `length`: File size in bytes
  - `type`: audio/mpeg or audio/mp4
- ✅ Duration metadata accurate

---

## Event Logging Verification

### Check Event Logs

**Query events API:**
```bash
# Get recent upload events
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/events?event_type=upload_started&limit=10"

# Get conversion events
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/events?event_type=audio_conversion_completed&limit=10"
```

**Expected Events**:
- ✅ `upload_started` - with filename and size
- ✅ `upload_completed` - with processing duration
- ✅ `audio_conversion_started` - for non-MP3 files
- ✅ `audio_conversion_completed` - with conversion time
- ✅ `episode_created_from_upload` - with episode ID
- ✅ `upload_failed` - with error details (for failed uploads)

---

## Performance Testing

### Upload Performance Benchmarks

**Test different file sizes:**
```bash
# 10MB file
time curl -X POST -F "channel_id=1" -F "title=Test 10MB" \
  -F "audio_file=@test_10mb.mp3" \
  http://localhost:8000/api/v1/episodes/upload

# 100MB file
time curl -X POST -F "channel_id=1" -F "title=Test 100MB" \
  -F "audio_file=@test_100mb.mp3" \
  http://localhost:8000/api/v1/episodes/upload

# 500MB file
time curl -X POST -F "channel_id=1" -F "title=Test 500MB" \
  -F "audio_file=@test_500mb.mp3" \
  http://localhost:8000/api/v1/episodes/upload
```

**Expected Performance**:
- ✅ 10MB: < 10 seconds
- ✅ 100MB: < 60 seconds
- ✅ 500MB: < 5 minutes
- ✅ Memory usage stable (< 200MB increase)
- ✅ No memory leaks

---

## File Management Testing

### Verify File Storage

**Check file locations:**
```bash
# List uploaded files
ls -lh backend/media/channel_1/

# Check temp directory is clean
ls -lh backend/media/temp/

# Verify file permissions
ls -la backend/media/channel_1/*.mp3
```

**Expected Results**:
- ✅ Files stored in correct channel directory
- ✅ Filenames sanitized and timestamped
- ✅ Temp directory empty after uploads
- ✅ File permissions correct (readable)

### Test Episode Deletion

**Steps**:
1. Upload an episode
2. Delete the episode via UI or API
3. Verify file cleanup

**Expected Results**:
- ✅ Episode removed from database
- ✅ Audio file deleted from disk
- ✅ No orphaned files remain

---

## Docker Environment Testing

### Development Environment

**Test in Docker Dev:**
```bash
# Start development environment
docker compose --env-file .env.development -f docker-compose.dev.yml up --build

# Run tests
docker compose -f docker-compose.dev.yml exec backend pytest tests/

# Check logs
docker compose -f docker-compose.dev.yml logs -f backend
docker compose -f docker-compose.dev.yml logs -f frontend

# Stop environment
docker compose -f docker-compose.dev.yml down
```

**Verify**:
- ✅ FFmpeg available in container
- ✅ File uploads work
- ✅ Conversions work
- ✅ Hot reload works (frontend)
- ✅ Database migrations applied

### Production Environment

**Test in Docker Prod:**
```bash
# Start production environment
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d

# Check container health
docker compose -f docker-compose.prod.yml ps

# Test upload via API
curl -X POST -F "channel_id=1" -F "title=Prod Test" \
  -F "audio_file=@test.mp3" \
  https://your-domain.com/api/v1/episodes/upload

# Check logs
docker compose -f docker-compose.prod.yml logs backend | tail -100

# Stop environment
docker compose -f docker-compose.prod.yml down
```

**Verify**:
- ✅ FFmpeg available in container
- ✅ File uploads work
- ✅ Conversions work
- ✅ HTTPS works
- ✅ Database persists across restarts
- ✅ Media files persist across restarts

---

## Security Testing

### Test Path Traversal Protection

**Attempt malicious filenames:**
```bash
# Test path traversal
curl -X POST -F "channel_id=1" -F "title=Malicious" \
  -F "audio_file=@../../../etc/passwd;filename=../../../etc/passwd.mp3" \
  http://localhost:8000/api/v1/episodes/upload
```

**Expected Results**:
- ✅ Filename sanitized
- ✅ File stored in correct directory
- ✅ No path traversal vulnerability

### Test File Size Limits

**Attempt to bypass size limit:**
```bash
# Create large file
dd if=/dev/zero of=large.mp3 bs=1M count=501

# Attempt upload
curl -X POST -F "channel_id=1" -F "title=Too Large" \
  -F "audio_file=@large.mp3" \
  http://localhost:8000/api/v1/episodes/upload
```

**Expected Results**:
- ❌ Upload rejected
- ❌ HTTP 413 Payload Too Large
- ❌ No file stored

---

## Troubleshooting

### Common Issues

**Issue**: FFmpeg not found
```bash
# Solution: Install FFmpeg in Docker container
# Add to Dockerfile:
RUN apt-get update && apt-get install -y ffmpeg
```

**Issue**: Permission denied writing files
```bash
# Solution: Fix directory permissions
chmod -R 755 backend/media/
chown -R $(whoami) backend/media/
```

**Issue**: Database migration fails
```bash
# Solution: Reset database (development only)
rm backend/data/labcastarr-dev.db
docker compose -f docker-compose.dev.yml up --build
```

**Issue**: Upload fails with "File too large"
```bash
# Solution: Check nginx/proxy settings
# Increase client_max_body_size in nginx.conf
client_max_body_size 500M;
```

---

## Test Results Checklist

### Backend Tests
- [ ] MP3 upload (no conversion)
- [ ] M4A upload (no conversion)
- [ ] WAV upload (with conversion)
- [ ] FLAC upload (with conversion)
- [ ] OGG upload (with conversion)
- [ ] File size limit enforcement
- [ ] Invalid format rejection
- [ ] Duplicate title detection
- [ ] Corrupted file rejection
- [ ] Filename sanitization
- [ ] Temp file cleanup
- [ ] Event logging

### Frontend Tests
- [ ] File drag-and-drop
- [ ] File validation
- [ ] Multi-step form navigation
- [ ] Upload progress display
- [ ] Error message display
- [ ] Tag management
- [ ] Tab switcher (YouTube/Upload)
- [ ] Tab state persistence
- [ ] Mobile responsiveness

### Integration Tests
- [ ] RSS feed includes uploaded episodes
- [ ] iTunes validator passes
- [ ] Spotify validator passes
- [ ] Episode playback in browsers
- [ ] Episode playback in podcast apps
- [ ] Episode deletion removes files
- [ ] Concurrent uploads work
- [ ] Large file uploads work

### Docker Tests
- [ ] Development environment works
- [ ] Production environment works
- [ ] FFmpeg available in containers
- [ ] Database migrations applied
- [ ] Media files persist
- [ ] Hot reload works (dev)
- [ ] HTTPS works (prod)

---

## Sign-Off

**Tested By**: _________________  
**Date**: _________________  
**Environment**: Development / Production  
**All Tests Passed**: Yes / No  
**Issues Found**: _________________  
**Notes**: _________________


