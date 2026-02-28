# File Upload Episode Creation - Implementation Plan v2

## Overview
Add capability for users to create episodes by uploading audio files directly from their computer, maintaining a similar multi-step UX to the current YouTube-based workflow.

## Architecture Analysis

### Current YouTube Workflow
1. User enters YouTube URL → Metadata extraction (title, description, duration, thumbnail)
2. Preview step → User adds tags
3. Create episode → Background download/processing
4. Progress tracking → Completion

### Proposed File Upload Workflow
1. User selects audio file → Client-side validation + metadata extraction
2. Preview step → User fills in episode details (title, description, publication date, tags)
3. Upload + Create episode → Streaming upload with progress tracking
4. Server-side processing → File validation, metadata extraction, storage
5. Completion → Episode ready immediately (no background download needed)

---

## Key Design Decisions

### 1. Schema Architecture
- **`EpisodeCreateFromUpload`**: Pydantic schema for API request validation (NOT a database model)
- **`Episode` entity**: Unified domain entity for both YouTube and uploaded episodes
- **`EpisodeModel`**: Single database table with `source_type` field to distinguish sources
- **No separate table**: Both YouTube and uploaded episodes use the same infrastructure

### 2. Audio Format Strategy
- **Accept**: MP3, M4A, WAV, OGG, FLAC (user convenience)
- **Store**: MP3 or M4A only (iTunes/Spotify compatibility)
- **Conversion**: Auto-convert WAV/OGG/FLAC → MP3 using FFmpeg
- **Preserve**: MP3 and M4A stored as-is (already iTunes compatible)

### 3. Event Logging & Error Management
Following existing patterns from `event_service.py` and `youtube_service.py`:
- Structured logging with `log_user_action()`, `log_system_event()`, `log_error_event()`
- Custom exception hierarchy mirroring `YouTubeExtractionError` pattern
- Performance tracking with duration metrics
- Comprehensive error context with traceback
- All upload operations logged as business events

---

## Implementation Tasks

### **Phase 1: Backend Infrastructure**

#### Task 1.1: Custom Exception Classes
- **File**: `backend/app/infrastructure/services/upload_service.py` (new file)
- **Purpose**: Create upload-specific exception hierarchy
- **Implementation**:
  - Create base `UploadError` exception class
  - Create `FileValidationError` for invalid formats or corrupted files
  - Create `FileSizeLimitError` for files exceeding size limits
  - Create `FileConversionError` for FFmpeg conversion failures
  - Create `DuplicateEpisodeError` for title conflicts
- **Pattern**: Mirror `YouTubeExtractionError` and `YouTubeDownloadError` structure
- **Success Criteria**:
  - All exceptions inherit from `UploadError` base class
  - Exceptions include descriptive error messages
  - Exception hierarchy matches existing YouTube service pattern

---

#### Task 1.2: Update Episode Schema for Upload
- **File**: `backend/app/presentation/schemas/episode_schemas.py`
- **Purpose**: Add Pydantic schema for validating file upload requests
- **Implementation**:
  - Add `EpisodeCreateFromUpload` schema class
  - Fields: `channel_id`, `title`, `description`, `publication_date`, `tags`
  - Add validators for title (non-empty, max length)
  - Add validator for tags (max 10, max length 50 each)
  - Note: `audio_file: UploadFile` handled separately in endpoint
- **Success Criteria**:
  - Schema validates all required fields
  - Validation errors return clear messages
  - Compatible with FastAPI Form data handling

---

#### Task 1.3: File Validation Service
- **File**: `backend/app/infrastructure/services/media_file_service.py` (expand existing)
- **Purpose**: Validate uploaded audio files comprehensively
- **Implementation**:
  - Add `validate_audio_file()` method using `python-magic` for MIME type detection
  - Add `extract_audio_metadata()` method using `mutagen` for duration/bitrate
  - Add `validate_file_size()` method to check against max size limit
  - Add `sanitize_filename()` method to remove dangerous characters
  - Define `ALLOWED_MIME_TYPES` mapping (audio/mpeg, audio/mp4, audio/wav, etc.)
  - Raise `FileValidationError` for invalid files with specific error context
- **Success Criteria**:
  - Invalid MIME types rejected with clear error
  - Files exceeding size limit rejected before processing
  - Duration and bitrate extracted successfully from valid files
  - Filenames sanitized (no path traversal characters)
  - All validation errors logged with structured logging

---

#### Task 1.4: Upload Processing Service with Event Logging
- **File**: Create `backend/app/application/services/upload_processing_service.py`
- **Purpose**: Process uploaded files with streaming, conversion, and comprehensive logging
- **Implementation**:
  - Create `UploadProcessingService` class
  - Add `process_uploaded_episode()` main method
  - Implement `_stream_file_to_disk()` for memory-efficient file writing
  - Implement `_convert_and_store()` for FFmpeg MP3 conversion
  - Implement `_move_to_storage()` for iTunes-compatible files
  - Log upload start, completion, and errors via `EventService`
  - Track processing duration and file sizes
  - Use structured logging for all operations
- **Format Conversion Logic**:
  - MP3/M4A: Move directly to storage (no conversion)
  - WAV/FLAC/OGG: Convert to MP3 using FFmpeg
  - Log conversion operations as system events
- **Success Criteria**:
  - Files up to 500MB upload without memory overflow
  - Streaming write uses 8KB chunks
  - FFmpeg conversion succeeds with quality settings (VBR ~190 kbps)
  - All operations logged with `log_user_action()` and `log_system_event()`
  - Temp files cleaned up after processing
  - Duration metrics captured for performance analysis

---

#### Task 1.5: File Upload Endpoint with Error Handling
- **File**: `backend/app/presentation/api/v1/episodes.py`
- **Purpose**: Create HTTP endpoint for file uploads with comprehensive error handling
- **Implementation**:
  - Add `POST /v1/episodes/upload` endpoint
  - Accept `multipart/form-data` with fields: `channel_id`, `title`, `description`, `publication_date`, `tags[]`, `audio_file`
  - Validate file size before processing
  - Call `UploadProcessingService.process_uploaded_episode()`
  - Call `EpisodeService.create_from_upload()`
  - Handle exceptions with appropriate HTTP status codes:
    - `FileSizeLimitError` → 413 Payload Too Large
    - `FileValidationError` → 400 Bad Request
    - `FileConversionError` → 422 Unprocessable Entity
    - `DuplicateEpisodeError` → 409 Conflict
    - Generic errors → 500 Internal Server Error
  - Return detailed error responses with error codes
  - Log all endpoint errors with traceback
- **Success Criteria**:
  - Endpoint accepts multipart uploads correctly
  - All error types return appropriate status codes
  - Error responses include error code and helpful message
  - 201 Created returned with episode JSON on success
  - File size validation happens before streaming upload

---

#### Task 1.6: Episode Service Updates
- **File**: `backend/app/application/services/episode_service.py`
- **Purpose**: Add method to create episodes from uploaded files
- **Implementation**:
  - Add `create_from_upload()` method
  - Check for duplicate titles in channel using repository
  - Create `Episode` entity with:
    - `source_type="upload"`
    - `status=EpisodeStatus.COMPLETED` (immediate completion)
    - `video_id=VideoId("uploaded")` (placeholder)
    - `original_filename` stored
    - `media_file_size` calculated
  - Associate tags if provided
  - Save to repository
  - Log episode creation event
- **Duplicate Detection**: Query repository for existing episode with same title in channel
- **Success Criteria**:
  - Episodes created with status "completed" immediately
  - Duplicate titles detected and rejected
  - Tags associated correctly
  - Episode appears in RSS feed immediately
  - Creation logged with `log_user_action()`

---

#### Task 1.7: Database Schema Update
- **File**: `backend/app/infrastructure/database/models/episode.py`
- **Purpose**: Add fields to distinguish upload source
- **Implementation**:
  - Add `source_type` column: String(20), default "youtube", indexed
  - Add `original_filename` column: String(500), nullable
  - Update `__table_args__` to include index on `source_type`
- **Migration**: Create Alembic migration to add these columns
- **Backward Compatibility**: Default value "youtube" for existing episodes
- **Success Criteria**:
  - Migration applies cleanly to existing database
  - Existing episodes have `source_type="youtube"`
  - New uploaded episodes have `source_type="upload"`
  - Index on `source_type` improves query performance
  - No data loss during migration

---

#### Task 1.8: Configuration Updates
- **File**: `backend/app/core/config.py`
- **Purpose**: Add configuration for file upload feature
- **Implementation**:
  - Add `max_upload_file_size_mb: int = 500`
  - Add `allowed_upload_formats: List[str] = ["mp3", "m4a", "wav", "ogg", "flac"]`
  - Add `target_audio_format: str = "mp3"`
  - Add `target_audio_quality: str = "192"` (kbps for MP3)
  - Add `convert_uploads_to_target: bool = True`
  - Add `preserve_m4a: bool = True` (don't convert M4A files)
- **Environment Variables**: All settings overridable via `.env` file
- **Success Criteria**:
  - Settings load from environment or use defaults
  - File size limit configurable per environment
  - Format conversion toggleable for testing
  - Settings accessible via `settings` instance

---

### **Phase 2: Frontend Implementation**

#### Task 2.1: Frontend Error Types
- **File**: Create `frontend/src/lib/errors.ts`
- **Purpose**: Define typed error classes for upload operations
- **Implementation**:
  - Create `UploadError` base class with `code` property
  - Create `FileSizeError` extending `UploadError`
  - Create `FileFormatError` extending `UploadError`
  - Create `NetworkError` extending `UploadError`
  - Add type-safe error handling utilities
- **Success Criteria**:
  - Error classes match backend error codes
  - TypeScript provides autocomplete for error types
  - Error messages are user-friendly

---

#### Task 2.2: Upload Episode Form Component
- **File**: Create `frontend/src/components/features/episodes/upload-episode-form.tsx`
- **Purpose**: Multi-step form for uploading audio files
- **Implementation**:
  - **Step 1 - File Selection**:
    - Drag-and-drop zone using HTML5 File API
    - File type validation (audio/* only)
    - File size validation (< 500MB)
    - Display file preview (name, size, type)
    - Extract duration using Web Audio API if possible
  - **Step 2 - Episode Details**:
    - Title input (required)
    - Description textarea (optional)
    - Publication date picker (defaults to now)
    - Tags input (reuse existing tag component)
    - File summary display
  - **Step 3 - Upload Progress**:
    - Progress bar with percentage
    - Upload speed indicator (MB/s)
    - ETA calculation
    - Cancel button to abort upload
  - **Step 4 - Success/Error**:
    - Success message with episode details
    - Error message with retry option
    - Link to view episode
- **State Management**: React hooks for step navigation and form data
- **Success Criteria**:
  - UX matches YouTube upload workflow
  - Form validates before submission
  - Steps clearly indicated with progress indicator
  - User can navigate back to correct mistakes
  - All steps responsive on mobile

---

#### Task 2.3: File Upload API Hook
- **File**: `frontend/src/hooks/use-episodes.ts`
- **Purpose**: React Query hook for file upload with progress tracking
- **Implementation**:
  - Add `useUploadEpisode()` mutation hook
  - Use `FormData` to construct multipart request
  - Configure Axios `onUploadProgress` callback
  - Handle upload cancellation via AbortController
  - Parse backend error responses and show appropriate toasts
  - Map error codes to user-friendly messages
- **Error Handling**:
  - 413 → "File too large (max XMB)"
  - 400 → "Invalid file format. Allowed: mp3, m4a, wav, ogg, flac"
  - 409 → "Episode with this title already exists"
  - 422 → "File could not be processed"
  - Network error → "Upload failed. Please check your connection"
- **Success Criteria**:
  - Upload progress updates in real-time
  - Progress percentage accurate
  - Errors display with context (max size, allowed formats)
  - Network interruptions handled gracefully
  - Upload can be cancelled mid-flight

---

#### Task 2.4: File Drag-and-Drop Component
- **File**: Create `frontend/src/components/shared/file-dropzone.tsx`
- **Purpose**: Reusable drag-and-drop file picker
- **Implementation**:
  - Create dropzone with hover state styling
  - Accept only audio MIME types
  - Validate file size on selection
  - Display validation errors immediately
  - Show file preview after selection
  - Allow click-to-browse as alternative
- **Validation**: Client-side pre-validation before upload
- **Success Criteria**:
  - Drag-and-drop works intuitively
  - Visual feedback during drag-over
  - Invalid files rejected with clear message
  - File picker accessible via keyboard
  - Works on mobile (tap to browse)

---

#### Task 2.5: Client-Side Validation
- **File**: `frontend/src/lib/validation.ts`
- **Purpose**: Validate files before upload to save bandwidth
- **Implementation**:
  - Add `validateAudioFile()` function
  - Check file size against limit
  - Check MIME type against allowed list
  - Check file extension matches MIME type
  - Extract duration using Web Audio API (if supported)
  - Return validation result with specific errors
- **Success Criteria**:
  - Invalid files rejected before upload starts
  - Validation errors specific and actionable
  - Duration extracted for preview (if possible)
  - No false negatives (valid files accepted)

---

#### Task 2.6: Episode Creation Page Update
- **File**: `frontend/src/app/episodes/add/page.tsx`
- **Purpose**: Add option to choose upload method
- **Implementation**:
  - Add tabs or toggle to switch between:
    - "From YouTube URL" (existing `AddEpisodeForm`)
    - "Upload Audio File" (new `UploadEpisodeForm`)
  - Preserve existing YouTube workflow
  - Default to YouTube tab (current behavior)
  - Remember user's last choice in localStorage
- **Success Criteria**:
  - Users can easily switch between methods
  - Both workflows accessible from same page
  - No UI regressions in existing YouTube flow
  - Tab state persisted across page reloads

---

#### Task 2.7: Upload Progress UI
- **File**: Within `frontend/src/components/features/episodes/upload-episode-form.tsx` (Step 3)
- **Purpose**: Display real-time upload feedback
- **Implementation**:
  - Progress bar component showing percentage
  - Upload speed calculation (bytes/second → MB/s)
  - ETA calculation based on current speed
  - Cancel button with confirmation dialog
  - Processing spinner after upload completes (during server processing)
  - Error display with retry option
- **Success Criteria**:
  - Progress updates smoothly (no jumps)
  - Speed and ETA calculations accurate
  - Cancel button stops upload immediately
  - User sees feedback during server processing phase
  - Errors clearly displayed with actionable next steps

---

### **Phase 3: Integration & Testing**

#### Task 3.1: Error Scenario Testing
- **Purpose**: Verify all error paths work correctly
- **Test Cases**:
  1. Upload file > 500MB → 413 error with max size in response
  2. Upload .txt file → 400 error with allowed formats
  3. Upload corrupted audio file → 400 error with validation message
  4. Upload duplicate title → 409 error with conflict message
  5. Simulate FFmpeg failure → 422 error with conversion error
  6. Disconnect during upload → Network error, proper cleanup
  7. Cancel upload mid-flight → Request cancelled, temp files cleaned
  8. Upload with special characters in filename → Sanitized correctly
- **Success Criteria**:
  - All errors return correct HTTP status codes
  - Error messages are user-friendly and specific
  - No orphaned files in temp directory
  - No database records for failed uploads
  - All errors logged to event system

---

#### Task 3.2: RSS Feed Compatibility
- **File**: `backend/app/domain/services/feed_generation_service.py`
- **Purpose**: Ensure uploaded episodes appear correctly in RSS feed
- **Implementation**:
  - Verify `<enclosure>` tag includes correct file size
  - Verify MIME type is correct (audio/mpeg for MP3, audio/mp4 for M4A)
  - Verify media URL resolves correctly
  - Test with iTunes Podcast validator
  - Test with Spotify podcast validator
- **Success Criteria**:
  - RSS feed validates with Apple Podcasts
  - RSS feed validates with Spotify
  - Uploaded episodes play in podcast apps
  - File sizes displayed correctly
  - Duration metadata accurate

---

#### Task 3.3: Media Serving
- **File**: `backend/app/presentation/api/v1/media.py`
- **Purpose**: Verify media endpoint serves uploaded files correctly
- **Implementation**:
  - Test Content-Type header matches file format
  - Test Content-Length header accurate
  - Test range requests work (for seeking in podcast players)
  - Test CORS headers present
  - Test file streaming performance
- **Success Criteria**:
  - Uploaded episodes stream correctly in browsers
  - Seeking works in podcast players
  - Large files don't load entirely into memory
  - HTTP 206 Partial Content supported

---

#### Task 3.4: File Management
- **File**: `backend/app/infrastructure/services/file_service.py`
- **Purpose**: Ensure file lifecycle management works
- **Implementation**:
  - Test episode deletion removes uploaded file from disk
  - Test storage path consistency across channels
  - Test no orphaned files after failed uploads
  - Test temp directory cleanup
  - Test file permissions correct
- **Success Criteria**:
  - Delete episode removes audio file
  - No orphaned files accumulate
  - Storage quota warnings work (if implemented)
  - File paths in database match actual files

---

#### Task 3.5: Integration Testing
- **Purpose**: End-to-end workflow testing
- **Test Scenarios**:
  1. **Happy Path - MP3**:
     - Upload valid MP3 file
     - Fill episode details
     - Verify episode created immediately
     - Verify RSS feed includes episode
     - Play episode in podcast app
  2. **Happy Path - WAV Conversion**:
     - Upload large WAV file (100MB+)
     - Verify conversion to MP3
     - Verify file size reduced
     - Verify duration preserved
     - Verify RSS feed correct
  3. **Tag Management**:
     - Upload file with tags
     - Verify tags associated correctly
     - Search by tags
     - Filter episodes by tags
  4. **Multi-Channel**:
     - Upload to different channels
     - Verify files in correct channel directories
     - Verify episodes isolated by channel
  5. **Performance**:
     - Upload multiple files concurrently
     - Verify no resource exhaustion
     - Verify queuing works correctly
- **Success Criteria**:
  - All test scenarios pass
  - No data corruption
  - Performance acceptable (< 30s for 100MB file)
  - Concurrent uploads don't interfere

---

#### Task 3.6: Event Logging Verification
- **Purpose**: Ensure all upload operations are logged
- **Implementation**:
  - Query events API for upload-related events
  - Verify event structure matches schema
  - Verify event details include relevant context
  - Test event filtering and search
- **Events to Verify**:
  - `upload_started` with filename and size
  - `upload_completed` with processing duration
  - `upload_failed` with error details
  - `audio_conversion_started` for non-MP3 files
  - `audio_conversion_completed` with conversion time
  - `episode_created_from_upload` with episode ID
- **Success Criteria**:
  - All operations generate events
  - Events queryable via /v1/events endpoint
  - Event timeline accurate
  - Performance metrics captured
  - Error events include traceback

---

#### Task 3.7: Documentation Updates
- **Files**: `CLAUDE.md`, `README.md`, API documentation
- **Purpose**: Document new upload feature
- **Content**:
  - Upload endpoint API documentation
  - File format requirements and conversion logic
  - Size limitations and configuration
  - Frontend component usage examples
  - Error handling patterns
  - Event logging reference
  - Troubleshooting guide
- **Success Criteria**:
  - API documentation complete and accurate
  - Examples provided for common use cases
  - Configuration options documented
  - Error codes listed with explanations

---

## Event Logging Summary

### User Actions Logged
- **upload_started**: User initiates file upload
- **upload_completed**: File successfully processed and stored
- **upload_failed**: Validation or processing error occurred
- **episode_created_from_upload**: Episode entity created in database

### System Events Logged
- **file_validation**: File format validation completed
- **audio_conversion_started**: FFmpeg conversion initiated
- **audio_conversion_completed**: Conversion successful with duration
- **audio_conversion_failed**: Conversion error with FFmpeg output
- **file_moved**: File moved to final storage location

### Error Events Logged
- **file_size_exceeded**: `FileSizeLimitError` with file size and limit
- **invalid_audio_format**: `FileValidationError` with MIME type
- **conversion_error**: `FileConversionError` with FFmpeg stderr
- **duplicate_episode**: `DuplicateEpisodeError` with existing episode ID

### Performance Metrics Tracked
- Upload processing duration (ms)
- Conversion duration (ms)
- File sizes (before/after conversion)
- Upload speed (bytes/second)

---

## Audio Format Conversion Matrix

| User Uploads | MIME Type  | We Store | RSS Serves | Conversion? | Event Logged               |
| ------------ | ---------- | -------- | ---------- | ----------- | -------------------------- |
| MP3          | audio/mpeg | MP3      | audio/mpeg | ❌ No        | file_moved                 |
| M4A          | audio/mp4  | M4A      | audio/mp4  | ❌ No        | file_moved                 |
| WAV          | audio/wav  | MP3      | audio/mpeg | ✅ Yes       | audio_conversion_completed |
| FLAC         | audio/flac | MP3      | audio/mpeg | ✅ Yes       | audio_conversion_completed |
| OGG          | audio/ogg  | MP3      | audio/mpeg | ✅ Yes       | audio_conversion_completed |

**Conversion Settings**:
- Codec: libmp3lame (FFmpeg)
- Quality: VBR quality 2 (~190 kbps)
- Sample rate: Preserved from original
- Channels: Preserved (mono/stereo)

---

## Technical Specifications

### File Upload Flow
```
1. Client → Server: POST /v1/episodes/upload
   Content-Type: multipart/form-data
   Fields: channel_id, title, description, publication_date, tags[], audio_file

2. Server validates:
   - File size < max_upload_file_size_mb
   - MIME type in allowed_upload_formats
   - Filename sanitized

3. Server processes:
   - Stream file to temp directory (8KB chunks)
   - Validate audio format with python-magic
   - Extract metadata with mutagen
   - Convert to MP3 if needed (FFmpeg)
   - Move to final storage: media/channel_{id}/{sanitized}_{timestamp}.{ext}
   - Calculate file size

4. Server creates episode:
   - Status: "completed" (immediate)
   - Source: "upload"
   - Audio file path set
   - Tags associated

5. Server responds:
   - 201 Created
   - Episode JSON with all metadata

6. Events logged:
   - upload_started, upload_completed, episode_created_from_upload
```

### Database Migration
```sql
-- Add columns to episodes table
ALTER TABLE episodes ADD COLUMN source_type VARCHAR(20) DEFAULT 'youtube';
ALTER TABLE episodes ADD COLUMN original_filename VARCHAR(500);

-- Add index for performance
CREATE INDEX idx_episode_source_type ON episodes(source_type);

-- Update existing episodes (idempotent)
UPDATE episodes SET source_type = 'youtube' WHERE source_type IS NULL;
```

### Environment Configuration
```env
# File upload settings
MAX_UPLOAD_FILE_SIZE_MB=500
ALLOWED_UPLOAD_FORMATS=mp3,m4a,wav,ogg,flac

# Audio processing settings
TARGET_AUDIO_FORMAT=mp3
TARGET_AUDIO_QUALITY=192
CONVERT_UPLOADS_TO_TARGET=true
PRESERVE_M4A=true
```

---

## Success Criteria Summary

### Backend
- ✅ All exceptions follow existing error patterns
- ✅ Event logging uses EventService consistently
- ✅ Structured logging with full context
- ✅ HTTP error codes semantically correct
- ✅ Format conversion automatic and reliable
- ✅ Streaming upload prevents memory overflow
- ✅ Temp files cleaned up properly

### Frontend
- ✅ Error messages specific and actionable
- ✅ Upload progress accurate and smooth
- ✅ Network errors handled gracefully
- ✅ File validation before upload
- ✅ UX matches YouTube workflow quality
- ✅ Responsive on mobile devices

### Integration
- ✅ All error paths tested and working
- ✅ Event logs queryable and complete
- ✅ RSS feed validates with iTunes/Spotify
- ✅ Podcast players stream episodes correctly
- ✅ Performance acceptable for large files
- ✅ No data corruption or orphaned files
- ✅ Documentation complete and accurate

---

## Dependencies

### Backend (All Already Available)
- ✅ `python-multipart` - multipart form data parsing
- ✅ `python-magic` - MIME type detection
- ✅ `mutagen` - audio metadata extraction
- ✅ `aiofiles` - async file I/O
- ⚠️ **FFmpeg** - system dependency for audio conversion (must be installed)

### Frontend (No New Dependencies Required)
- ✅ HTML5 File API (built into browsers)
- ✅ Axios (already in use) - multipart upload
- ✅ React Hook Form (already in use) - form handling
- ⚠️ Optional: `react-dropzone` (if custom implementation too complex)

---

## Estimated Complexity

- **Backend**: 10-12 hours
  - Exception classes: 1 hour
  - Validation service: 2 hours
  - Upload processing service: 4 hours
  - API endpoint: 2 hours
  - Database migration: 1 hour
  - Testing: 2 hours

- **Frontend**: 6-8 hours
  - Error types: 1 hour
  - Upload form component: 3 hours
  - API hook: 1 hour
  - Validation: 1 hour
  - UI polish: 2 hours

- **Integration & Testing**: 6-8 hours
  - Error scenario testing: 2 hours
  - RSS feed validation: 1 hour
  - End-to-end testing: 2 hours
  - Event logging verification: 1 hour
  - Documentation: 2 hours

**Total**: 22-28 hours of development time

---

## Risks & Mitigations

### 1. Large File Memory Issues
- **Risk**: Loading 500MB files into memory crashes server
- **Mitigation**: Use streaming file writes with aiofiles, 8KB chunks
- **Testing**: Upload files up to 500MB, monitor memory usage

### 2. FFmpeg Conversion Failures
- **Risk**: Some audio formats fail to convert
- **Mitigation**: Comprehensive error handling, log FFmpeg stderr, inform user
- **Testing**: Test all supported formats, handle edge cases

### 3. Format Compatibility with Podcast Apps
- **Risk**: Converted files don't play in some podcast players
- **Mitigation**: Use standard MP3 encoding, validate with iTunes/Spotify
- **Testing**: Test playback in Apple Podcasts, Spotify, Overcast, Pocket Casts

### 4. Duplicate File Detection
- **Risk**: Same file uploaded multiple times wastes storage
- **Mitigation**: Check for duplicate titles in channel, optionally add file hash comparison
- **Testing**: Attempt to upload same file twice

### 5. Storage Quota Management
- **Risk**: Disk fills up with uploaded files
- **Mitigation**: Add storage quota warnings, implement cleanup for old episodes
- **Testing**: Monitor disk usage, test cleanup procedures

### 6. Concurrent Upload Performance
- **Risk**: Multiple simultaneous uploads overwhelm server
- **Mitigation**: Implement upload queue if needed, set resource limits
- **Testing**: Simulate concurrent uploads from multiple users

### 7. Network Interruptions During Upload
- **Risk**: Partial uploads leave orphaned temp files
- **Mitigation**: Cleanup temp files on error, periodic temp directory cleanup
- **Testing**: Interrupt uploads at various stages, verify cleanup

---

## Future Enhancements (Out of Scope)

1. **Multi-file Upload**: Upload multiple episodes at once
2. **Resume Upload**: Resume interrupted uploads from checkpoint
3. **Direct URL Import**: Download from external URL instead of local file
4. **Metadata Extraction**: Auto-fill title/description from ID3 tags
5. **Thumbnail Upload**: Allow custom episode artwork upload
6. **Audio Editing**: Trim/normalize audio before saving
7. **File Hash Deduplication**: Detect duplicate files by content hash
8. **Storage Backends**: Support S3/cloud storage for media files
9. **Batch Tagging**: Apply tags to multiple uploaded episodes
10. **Upload Templates**: Save episode metadata as templates

---

## Appendix: File Structure

### New Files Created
```
backend/app/application/services/upload_processing_service.py
frontend/src/components/features/episodes/upload-episode-form.tsx
frontend/src/components/shared/file-dropzone.tsx
frontend/src/lib/errors.ts
frontend/src/lib/validation.ts
```

### Modified Files
```
backend/app/core/config.py
backend/app/infrastructure/services/media_file_service.py
backend/app/application/services/episode_service.py
backend/app/presentation/api/v1/episodes.py
backend/app/presentation/schemas/episode_schemas.py
backend/app/infrastructure/database/models/episode.py
backend/app/domain/entities/episode.py
frontend/src/hooks/use-episodes.ts
frontend/src/app/episodes/add/page.tsx
CLAUDE.md
README.md
```

### Alembic Migration
```
backend/alembic/versions/XXXXXX_add_upload_source_fields.py
```
