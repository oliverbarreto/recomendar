# Task 0029: Upload Episode 1

## Prompt


i would like analyze how to implement a new important feature: i want to allow the user to create a new episode by dreictly uploading a file from his computer. The file must be a media file that we must be sure it is valid, and we also must utilize a form to allow the user add the data needed in order to create the episode. We should keep the workflow as close as we can to the user experience we have when we create an epsidode with the multi-step form to create an episode out of a Youtube video url downloading the metadata needed and the audio.

Thinkhard about all neccesary steps to implement this features and then draft a detailed implementation plan with successs criteria and small tasks to be implemented later.

---

### Result

I'll analyze the current episode creation workflow and design a comprehensive implementation plan for file upload-based episode creation.
Read add-episode-form.tsx, episodes.py
Read episode_service.py
Read episode_schemas.py, media_file_service.py
Read youtube_service.py
Grep "mutagen|python-magic" (in /Users/oliver/Library/Mobile Documents/com~apple~CloudDocs/dev/webaps/labcastarr/backend)
⎿
4 lines of output
Read episode.py, episode.py
Grep "class.*Form|const.*Form" (in /Users/oliver/Library/Mobile Documents/com~apple~CloudDocs/dev/webaps/labcastarr/frontend/src/components/features/episodes)
⎿
6 lines of output
Read episode-form.tsx, download_service.py
Grep "FILE_UPLOAD|file.*upload|multipart" (in /Users/oliver/Library/Mobile Documents/com~apple~CloudDocs/dev/webaps/labcastarr/backend)
⎿
4 lines of output
Read config.py
Based on my comprehensive analysis of the codebase, I've developed a detailed implementation plan for adding file upload-based episode creation. Let me present this plan:
Plan Mode
⎿
Stayed in plan mode


---

## Prompt

The first thing i noted from your plan is that you proposed a new schema `EpisodeCreateFromUpload` instead of using the current Episode model we got. Is this a schema to process and validate the request, or is it a new model in the database ? I think it is not but i want you to confirm it.

---

### Result

You're absolutely correct to ask for clarification! EpisodeCreateFromUpload is a Pydantic schema for request validation, NOT a new database model. Let me clarify the distinction:
Schema vs Model
Pydantic Schema (for API requests/responses)
File: backend/app/presentation/schemas/episode_schemas.py
Purpose: Validate incoming HTTP requests and serialize responses
Example: EpisodeCreateFromUpload would validate the multipart form data when users upload files
Lives in the presentation layer
Database Model (SQLAlchemy)
File: backend/app/infrastructure/database/models/episode.py
Purpose: Represents the database table structure
Example: EpisodeModel - the existing table remains the same structure
Lives in the infrastructure layer
Domain Entity
File: backend/app/domain/entities/episode.py
Purpose: Core business logic representation
Example: Episode - the existing entity remains the same
Lives in the domain layer
What Actually Changes
✅ New Schema (Presentation Layer)
# backend/app/presentation/schemas/episode_schemas.py

class EpisodeCreateFromUpload(BaseModel):
    """Schema for creating episodes from uploaded audio files"""
    channel_id: int
    title: str
    description: Optional[str]
    publication_date: Optional[datetime]
    tags: Optional[List[str]]
    # Note: audio_file is handled separately as UploadFile in the endpoint
✅ Extended Database Model (Minor addition)
# backend/app/infrastructure/database/models/episode.py
# Just add 2 new optional columns to existing EpisodeModel:

class EpisodeModel(Base):
    # ... all existing fields ...
    
    # NEW FIELDS:
    source_type = Column(String(20), default="youtube")  # "youtube" or "upload"
    original_filename = Column(String(500), nullable=True)  # User's original filename
✅ Extended Domain Entity (Minor addition)
# backend/app/domain/entities/episode.py
# Just add 2 new optional fields to existing Episode dataclass:

@dataclass
class Episode:
    # ... all existing fields ...
    
    # NEW FIELDS:
    source_type: str = "youtube"  # "youtube" or "upload"
    original_filename: Optional[str] = None  # User's original filename
The Key Point
We're NOT creating a separate table or entity type for uploaded episodes. Both YouTube-sourced and upload-sourced episodes:
✅ Use the same Episode entity (domain)
✅ Use the same EpisodeModel table (database)
✅ Use the same repositories
✅ Use the same RSS feed generation
✅ Show up in the same episode list
The only difference is:
YouTube episodes: source_type = "youtube", have video_id, video_url
Uploaded episodes: source_type = "upload", have original_filename, no video_id (will be empty/placeholder)
The different schemas (EpisodeCreate vs EpisodeCreateFromUpload) are just for handling different input formats at the API endpoint level. Does this clarify the architecture? The plan keeps everything unified - just one episode system with a source type flag!

## Prompt

another question, in task 1.7 you define allowd audio formats "  - `allowed_audio_formats: List[str] = ["mp3", "m4a", "wav", "ogg", "flac"]`". Are we allowing all these media types and later converting them to types allowed by iTunes Podcasts rules (mp3, m4a). ?



---

### Result

Excellent question! Yes, that's exactly the strategy, and it's important to clarify this in the plan.

Strategy: Accept Multiple Formats → Convert to iTunes-Compatible Formats
What We Accept (User Upload)
allowed_audio_formats: List[str] = ["mp3", "m4a", "wav", "ogg", "flac"]

What We Store & Serve (RSS Feed)
# Only iTunes/Spotify compatible formats:
- MP3 (audio/mpeg) - most compatible
- M4A (audio/mp4) - also widely supported
The Conversion Flow
User Upload → Validation → Conversion (if needed) → Storage → RSS Feed

WAV file (100MB)  → ✅ Valid → Convert to MP3 → Store as .mp3 → audio/mpeg
FLAC file (80MB)  → ✅ Valid → Convert to MP3 → Store as .mp3 → audio/mpeg  
OGG file (50MB)   → ✅ Valid → Convert to MP3 → Store as .mp3 → audio/mpeg
MP3 file (45MB)   → ✅ Valid → No conversion → Store as .mp3 → audio/mpeg
M4A file (40MB)   → ✅ Valid → No conversion → Store as .m4a → audio/mp4
iTunes Podcast Requirements
According to Apple's podcast specifications:
Supported formats: MP3, M4A (AAC), MOV, MP4, M4V, PDF, EPUB
Recommended for audio: MP3 or M4A
Most compatible: MP3 (works everywhere)
Updated Configuration (More Explicit)
# backend/app/core/config.py

class Settings(BaseSettings):
    # Upload acceptance - what users can upload
    allowed_upload_formats: List[str] = ["mp3", "m4a", "wav", "ogg", "flac"]
    max_upload_file_size_mb: int = 500
    
    # Storage/serving - what we actually store and serve in RSS
    target_audio_format: str = "mp3"  # Convert everything to this
    target_audio_quality: str = "192"  # kbps for MP3 conversion
    
    # Conversion settings
    convert_uploads_to_target: bool = True  # Auto-convert non-mp3/m4a files
    preserve_m4a: bool = True  # Don't convert M4A, keep as-is (it's already iTunes compatible)
Refined Conversion Logic
# backend/app/application/services/upload_processing_service.py

async def process_uploaded_episode(
    self,
    file: UploadFile,
    metadata: Dict
) -> Episode:
    """
    Process uploaded audio file with smart format handling
    """
    file_extension = Path(file.filename).suffix.lower().replace('.', '')
    
    # Determine if conversion is needed
    if file_extension in ['mp3', 'm4a']:
        # Already iTunes compatible - store as-is
        final_format = file_extension
        needs_conversion = False
    else:
        # WAV, FLAC, OGG - convert to MP3 for maximum compatibility
        final_format = 'mp3'
        needs_conversion = True
    
    if needs_conversion:
        # Use FFmpeg to convert to MP3
        await self._convert_to_mp3(temp_file_path, output_path)
    else:
        # Just move the file
        await self._move_file(temp_file_path, output_path)
    
    return episode
Why This Approach?
✅ Pros
User Flexibility: Users can upload whatever audio format they have
Maximum Compatibility: Final files work in all podcast players
Storage Efficiency: WAV/FLAC are uncompressed → MP3 is compressed (smaller storage)
Consistent RSS Feed: Always serve iTunes-compatible formats
⚠️ Cons
Processing Time: Conversion takes time (especially for large WAV files)
CPU Usage: FFmpeg conversion is CPU-intensive
Quality Loss: Transcoding lossy→lossy (OGG→MP3) degrades quality slightly
Implementation Details
Validation Layer (Accept Formats)
# Task 1.3 - File Validation Service
ALLOWED_UPLOAD_FORMATS = ['mp3', 'm4a', 'wav', 'ogg', 'flac']

def validate_audio_file(file_path: str) -> bool:
    """Accept multiple formats for user convenience"""
    mime_type = magic.from_file(file_path, mime=True)
    return mime_type in [
        'audio/mpeg',      # MP3
        'audio/mp4',       # M4A
        'audio/x-m4a',     # M4A variant
        'audio/wav',       # WAV
        'audio/x-wav',     # WAV variant
        'audio/ogg',       # OGG
        'audio/flac',      # FLAC
    ]
Conversion Layer (Normalize to iTunes Formats)
# Task 1.4 - Upload Processing Service
async def _convert_to_mp3(input_path: str, output_path: str):
    """Convert any audio format to MP3 using FFmpeg"""
    cmd = [
        'ffmpeg',
        '-i', input_path,
        '-codec:a', 'libmp3lame',
        '-qscale:a', '2',  # VBR quality (~190 kbps)
        '-y',  # Overwrite output
        output_path
    ]
    # Run FFmpeg conversion
RSS Feed Layer (Serve iTunes-Compatible Formats)
# RSS feed will always have:
<enclosure 
    url="https://api.example.com/media/episodes/123.mp3"
    length="45678901"
    type="audio/mpeg" />
Revised Task 1.4 Description
Task 1.4: Upload Processing Service with Format Conversion
Accept: MP3, M4A, WAV, OGG, FLAC
Process:
MP3/M4A: Store directly (already iTunes compatible)
WAV/FLAC/OGG: Convert to MP3 using FFmpeg
Show conversion progress in upload UI
Calculate final file size after conversion for RSS feed
Success Criteria: All uploaded files result in iTunes-compatible audio
Summary
Yes, we accept multiple formats but intelligently convert them:
User Uploads	We Store	RSS Serves	Conversion?
MP3	MP3	audio/mpeg	❌ No
M4A	M4A	audio/mp4	❌ No
WAV	MP3	audio/mpeg	✅ Yes
FLAC	MP3	audio/mpeg	✅ Yes
OGG	MP3	audio/mpeg	✅ Yes
This gives users maximum flexibility while guaranteeing iTunes/Spotify compatibility in the final RSS feed. Does this clarification help? Should I update the plan document to make this conversion strategy more explicit?


----


## Prompt

@/Users/oliver/Library/Mobile Documents/com~apple~CloudDocs/dev/webaps/labcastarr/docs/tasks/task-0029-upload-episode-plan-v1.md update the plan with these modifications. We also should add proper error management and logging these new events

Modify the plan but create version 2. Do not include actual code, just the implementation plan with detailed tasks with its success criteria, that will be implemented later


---

### Result

Perfect! I've created task-0029-upload-episode-plan-v2.md with comprehensive improvements:
Key Updates in V2
1. Clarified Architecture
Explicitly stated that EpisodeCreateFromUpload is a Pydantic schema, NOT a database model
Unified data model with source_type field to distinguish upload vs YouTube episodes
No separate tables - both episode types use the same infrastructure
2. Audio Format Conversion Strategy
Clear matrix showing what formats we accept vs. what we store
MP3/M4A preserved as-is (already iTunes compatible)
WAV/FLAC/OGG converted to MP3 via FFmpeg
Explicit conversion settings documented
3. Comprehensive Error Management
Custom exception hierarchy mirroring existing YouTubeExtractionError pattern
HTTP status codes for each error type (413, 400, 409, 422, 500)
Frontend error classes with typed error handling
All error scenarios tested in Phase 3
4. Event Logging Integration
User actions: upload_started, upload_completed, upload_failed
System events: file_validation, audio_conversion_started/completed
Error events: file_size_exceeded, invalid_audio_format, conversion_error
Performance metrics: duration, file sizes, upload speed
5. Detailed Task Breakdown
Each task now includes:
Purpose: Why this task exists
Implementation: What needs to be done (without code)
Success Criteria: How to verify it works
Patterns to Follow: References to existing code patterns
6. No Code Included
Only high-level implementation descriptions
References to existing patterns
Focus on what to build, not how to build it
7. Comprehensive Testing Plan
8 error scenarios explicitly listed
RSS feed compatibility testing
Integration test scenarios
Event logging verification
Performance testing
The plan is now ready for implementation with clear success criteria for each task!

---



