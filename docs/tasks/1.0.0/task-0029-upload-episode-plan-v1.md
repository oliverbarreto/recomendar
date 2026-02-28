# File Upload Episode Creation - Implementation Plan

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

## Implementation Tasks

### **Phase 1: Backend Infrastructure** 

#### Task 1.1: Update Episode Schema for Upload Source
- **File**: `backend/app/presentation/schemas/episode_schemas.py`
- Add new schema `EpisodeCreateFromUpload`:
  - `channel_id: int`
  - `title: str`
  - `description: Optional[str]`
  - `publication_date: Optional[datetime]`
  - `tags: Optional[List[str]]`
  - `audio_file: UploadFile` (from FastAPI)
- Add source type field to distinguish YouTube vs Upload episodes
- **Success Criteria**: Schema validates uploaded file metadata correctly

#### Task 1.2: File Upload Endpoint
- **File**: `backend/app/presentation/api/v1/episodes.py`
- Create `POST /v1/episodes/upload` endpoint:
  - Accept `multipart/form-data` with audio file + metadata
  - File size limit: 500MB (configurable in settings)
  - Supported formats: MP3, M4A, WAV, OGG, FLAC
  - Real-time upload progress tracking
- **Success Criteria**: Endpoint accepts file uploads and returns 201 with episode data

#### Task 1.3: File Validation Service
- **File**: `backend/app/infrastructure/services/media_file_service.py` (expand existing)
- Add methods:
  - `validate_audio_file(file_path: str) -> Dict[str, Any]`: Check MIME type using `python-magic`
  - `extract_audio_metadata(file_path: str) -> Dict[str, Any]`: Extract duration, bitrate, codec using `mutagen`
  - `validate_file_size(file: UploadFile, max_mb: int) -> bool`
  - `sanitize_filename(filename: str) -> str`: Remove dangerous characters
- **Success Criteria**: Service correctly validates audio files and extracts metadata

#### Task 1.4: Upload Processing Service
- **File**: Create `backend/app/application/services/upload_processing_service.py`
- Implement:
  - `process_uploaded_episode(file: UploadFile, metadata: Dict) -> Episode`
  - Streaming file write to avoid memory overflow
  - Automatic MP3 conversion for non-MP3 files (using FFmpeg)
  - Generate file path: `media/channel_{id}/{sanitized_filename}_{timestamp}.mp3`
  - Calculate file size for RSS feed
- **Success Criteria**: Large files (100MB+) upload without memory issues

#### Task 1.5: Episode Service Updates
- **File**: `backend/app/application/services/episode_service.py`
- Add new method:
  - `create_from_upload(channel_id: int, file_data: UploadFile, metadata: Dict) -> Episode`
  - Validate no duplicate titles within channel
  - Create episode entity with `source_type="upload"`
  - Mark as completed immediately (no download phase)
- **Success Criteria**: Episode created with correct metadata and file association

#### Task 1.6: Database Schema Update
- **File**: `backend/app/infrastructure/database/models/episode.py`
- Add fields:
  - `source_type: String` (enum: "youtube", "upload")
  - `original_filename: String` (optional, store user's original filename)
- Create Alembic migration
- **Success Criteria**: Migration runs successfully, new fields populated

#### Task 1.7: Configuration Updates
- **File**: `backend/app/core/config.py`
- Add settings:
  - `max_upload_file_size_mb: int = 500`
  - `allowed_audio_formats: List[str] = ["mp3", "m4a", "wav", "ogg", "flac"]`
  - `convert_uploads_to_mp3: bool = True`
- **Success Criteria**: Settings loaded correctly from environment

---

### **Phase 2: Frontend Implementation**

#### Task 2.1: Upload Episode Form Component
- **File**: Create `frontend/src/components/features/episodes/upload-episode-form.tsx`
- Multi-step form structure:
  - **Step 1**: File selection with drag-and-drop zone
    - File validation (size, type)
    - Client-side metadata preview (if browser supports)
  - **Step 2**: Episode details form
    - Title (required)
    - Description (optional, textarea)
    - Publication date (date picker, defaults to now)
    - Tags (same as YouTube flow)
    - File preview (name, size, duration if available)
  - **Step 3**: Upload progress
    - Progress bar with percentage
    - Upload speed indicator
    - Estimated time remaining
  - **Step 4**: Success confirmation
- **Success Criteria**: Form UX matches YouTube flow quality

#### Task 2.2: File Upload API Hook
- **File**: `frontend/src/hooks/use-episodes.ts`
- Add new hook `useUploadEpisode()`:
  - Use `FormData` for multipart upload
  - Track upload progress using Axios/Fetch progress events
  - Handle errors (file too large, invalid format, network issues)
  - Return progress percentage and upload state
- **Success Criteria**: Upload progress updates in real-time

#### Task 2.3: File Drag-and-Drop Component
- **File**: Create `frontend/src/components/shared/file-dropzone.tsx`
- Features:
  - Drag-and-drop zone with visual feedback
  - Click to browse file picker
  - Show file preview after selection
  - Display validation errors
  - Accept only audio files
- Use `react-dropzone` or implement custom
- **Success Criteria**: Intuitive file selection UX

#### Task 2.4: Client-Side Validation
- **File**: `frontend/src/lib/validation.ts`
- Implement:
  - `validateAudioFile(file: File): ValidationResult`
  - Check file size (< 500MB)
  - Check MIME type
  - Check file extension
  - Extract basic metadata using Web Audio API
- **Success Criteria**: Invalid files rejected before upload

#### Task 2.5: Episode Creation Page Update
- **File**: `frontend/src/app/episodes/add/page.tsx`
- Add toggle/tabs to switch between:
  - "From YouTube URL" (existing)
  - "Upload Audio File" (new)
- Update routing if needed
- **Success Criteria**: Users can choose upload method

#### Task 2.6: Upload Progress UI
- **File**: Update `frontend/src/components/features/episodes/upload-episode-form.tsx`
- Implement progress visualization:
  - Linear progress bar with percentage
  - Upload speed (MB/s)
  - Time remaining
  - Cancel button (abort upload)
- **Success Criteria**: User sees real-time upload feedback

---

### **Phase 3: Integration & Testing**

#### Task 3.1: Error Handling
- Backend: Custom exceptions
  - `FileValidationError` (invalid format, corrupted file)
  - `FileSizeLimitError` (exceeds max size)
  - `DuplicateEpisodeError` (title conflict)
- Frontend: User-friendly error messages
  - File format not supported
  - File too large
  - Upload failed (network error)
  - Processing failed (server error)
- **Success Criteria**: All error scenarios display appropriate messages

#### Task 3.2: RSS Feed Compatibility
- **File**: `backend/app/domain/services/feed_generation_service.py`
- Ensure uploaded episodes:
  - Include correct `<enclosure>` tag with file size
  - Use proper MIME type (audio/mpeg for MP3)
  - Generate correct media URL
- Test with iTunes Podcast validator
- **Success Criteria**: RSS feed validates with uploaded episodes

#### Task 3.3: Media Serving
- **File**: `backend/app/presentation/api/v1/media.py`
- Verify media endpoint serves uploaded files correctly:
  - Correct Content-Type header
  - Proper Content-Length
  - Support range requests (for podcast players)
- **Success Criteria**: Uploaded episodes stream correctly in podcast apps

#### Task 3.4: File Management
- **File**: `backend/app/infrastructure/services/file_service.py`
- Ensure:
  - File deletion works for uploaded episodes
  - Storage path consistency
  - No orphaned files after episode deletion
- **Success Criteria**: Delete episode removes uploaded file

#### Task 3.5: Integration Testing
- Test scenarios:
  - Upload MP3 file → Create episode → Verify RSS feed
  - Upload large file (300MB) → Track progress → Complete
  - Upload invalid file → Receive validation error
  - Upload with special characters in filename → Sanitized correctly
  - Upload + tag management → Tags saved correctly
- **Success Criteria**: All integration tests pass

#### Task 3.6: Documentation Updates
- **File**: `CLAUDE.md`, `README.md`
- Document:
  - New upload endpoint API
  - File format requirements
  - Size limitations
  - Frontend component usage
  - Error handling patterns
- **Success Criteria**: Documentation clear and complete

---

## Technical Specifications

### File Upload Flow
```
1. Client → Server: POST /v1/episodes/upload
   - Content-Type: multipart/form-data
   - Fields: channel_id, title, description, publication_date, tags[], audio_file
   
2. Server validates:
   - File size < 500MB
   - MIME type in allowed list
   - Filename sanitized
   
3. Server processes:
   - Stream file to disk (media/channel_X/)
   - Extract metadata (duration, bitrate)
   - Convert to MP3 if needed (FFmpeg)
   - Calculate file size
   
4. Server creates episode:
   - Status: "completed" (immediate)
   - Source: "upload"
   - Audio file path set
   
5. Server responds:
   - 201 Created
   - Episode JSON with all metadata
```

### Database Changes
```sql
ALTER TABLE episodes ADD COLUMN source_type VARCHAR(20) DEFAULT 'youtube';
ALTER TABLE episodes ADD COLUMN original_filename VARCHAR(500);
```

### Configuration
```env
MAX_UPLOAD_FILE_SIZE_MB=500
ALLOWED_AUDIO_FORMATS=mp3,m4a,wav,ogg,flac
CONVERT_UPLOADS_TO_MP3=true
```

---

## Dependencies Required

### Backend
- ✅ `python-multipart` (already in pyproject.toml)
- ✅ `python-magic` (already in pyproject.toml)
- ✅ `mutagen` (already in pyproject.toml)
- ✅ `aiofiles` (already in pyproject.toml)
- FFmpeg (system dependency for audio conversion)

### Frontend
- `react-dropzone` (optional, can use native HTML5)
- No new dependencies strictly required

---

## Success Criteria Summary

### Backend
- ✅ New upload endpoint accepts multipart file uploads
- ✅ File validation rejects invalid files before processing
- ✅ Large files (500MB) upload without memory overflow
- ✅ Uploaded episodes appear in RSS feed correctly
- ✅ Media files serve correctly to podcast players

### Frontend
- ✅ Drag-and-drop file selection works intuitively
- ✅ Multi-step form matches YouTube workflow UX
- ✅ Real-time upload progress displays accurately
- ✅ Error messages are user-friendly and actionable
- ✅ Uploaded episodes display in episode list immediately

### Integration
- ✅ Episode deletion removes uploaded files
- ✅ Tag management works for uploaded episodes
- ✅ RSS feed validates with iTunes
- ✅ Podcast players can stream uploaded episodes
- ✅ No duplicate episodes created

---

## Estimated Complexity

- **Backend**: ~8-10 hours (file handling, validation, streaming upload)
- **Frontend**: ~6-8 hours (form UI, drag-drop, progress tracking)
- **Integration & Testing**: ~4-6 hours (error handling, RSS validation)
- **Total**: ~18-24 hours of development time

## Risks & Mitigations

1. **Large File Memory Issues**
   - Risk: Loading 500MB files into memory crashes server
   - Mitigation: Use streaming file writes with aiofiles

2. **Format Compatibility**
   - Risk: Some audio formats not supported by podcast players
   - Mitigation: Convert all uploads to MP3 using FFmpeg

3. **Duplicate Detection**
   - Risk: Same file uploaded multiple times
   - Mitigation: Check for duplicate titles + file hash comparison

4. **Storage Management**
   - Risk: Disk fills up with uploaded files
   - Mitigation: Add storage quota warnings, cleanup old episodes