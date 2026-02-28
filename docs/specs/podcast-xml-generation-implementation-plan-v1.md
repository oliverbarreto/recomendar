# Podcast XML Generation Implementation Plan v1

## Overview

This document outlines the comprehensive plan to enhance the RSS feed generation in LabCastARR to support full iTunes compliance and improved podcast distribution. The implementation includes database schema changes, backend service enhancements, frontend UI updates, and complete RSS feed optimization.

## Current State Analysis

### Database Schema (Current)
- ✅ `ChannelModel`: Has `explicit_content` (Boolean, default: False) and `website_url` fields
- ✅ `EpisodeModel`: Has core fields (`duration_seconds`, `audio_file_path`, `youtube_channel`, etc.)
- ❌ Missing: `media_file_size` field in episodes
- ❌ Missing: Episode numbering/positioning logic

### Frontend (Current)
- ✅ Settings interface with Channel tab exists
- ❌ Missing: Explicit content toggle in settings
- ❌ Missing: Website URL as required field
- ❌ Missing: Enhanced RSS feed information display

### Backend (Current)
- ✅ Basic RSS feed generation with PodGen
- ❌ Hard-coded media size as 0
- ❌ No episode numbering based on database position
- ❌ No episode subtitles with YouTube channel info
- ❌ Episodes don't inherit channel image
- ❌ Description formatting lacks proper handling of line breaks/markdown

## Requirements Implementation

### 1. Database Schema Changes

#### 1.1 Episode Model Enhancement
**File**: `backend/app/infrastructure/database/models/episode.py`

Add new field:
```python
# Media file information
media_file_size = Column(Integer, default=0)  # Size in bytes
```

#### 1.2 Channel Model Validation Enhancement
**File**: `backend/app/infrastructure/database/models/channel.py`

Update field constraints:
```python
# Make website_url required for RSS compliance
website_url = Column(String(500), nullable=False)  # Changed from nullable=True
# Update explicit_content default to True (as per requirements)
explicit_content = Column(Boolean, default=True)  # Changed from False
```

### 2. Domain Layer Updates

#### 2.1 Episode Entity Enhancement
**File**: `backend/app/domain/entities/episode.py`

Add fields and methods:
```python
@dataclass
class Episode:
    # ... existing fields ...
    media_file_size: Optional[int] = 0

    def get_episode_number(self, episodes_list: List['Episode']) -> int:
        """Calculate episode number based on position in created_at order"""
        sorted_episodes = sorted(episodes_list, key=lambda x: x.created_at or datetime.min)
        return sorted_episodes.index(self) + 1

    def generate_subtitle(self) -> str:
        """Generate episode subtitle from YouTube channel info"""
        return f"by {self.youtube_channel}" if self.youtube_channel else ""

    def format_description_for_rss(self) -> str:
        """Format description preserving line breaks and basic formatting"""
        if not self.description:
            return ""

        # Preserve line breaks by converting to HTML breaks
        formatted = self.description.replace('\n\n', '<br/><br/>')
        formatted = formatted.replace('\n', '<br/>')

        # Keep basic markdown-like formatting
        return formatted
```

#### 2.2 Channel Entity Enhancement
**File**: `backend/app/domain/entities/channel.py`

Update validation:
```python
def __post_init__(self):
    # ... existing validation ...

    # Validate website_url is required
    if not self.website_url or len(self.website_url.strip()) < 1:
        raise ValueError("Website URL is required for iTunes compliance")

    # Update explicit_content default
    if self.explicit_content is None:
        self.explicit_content = True
```

### 3. Infrastructure Layer Updates

#### 3.1 Media File Size Calculation Service
**New File**: `backend/app/infrastructure/services/media_file_service.py`

```python
import os
from typing import Optional
from pathlib import Path

class MediaFileService:
    """Service for media file operations"""

    def calculate_file_size(self, file_path: str) -> int:
        """Calculate media file size in bytes"""
        try:
            if os.path.exists(file_path):
                return os.path.getsize(file_path)
            return 0
        except (OSError, IOError):
            return 0

    def update_episode_file_size(self, episode_id: int, file_path: str) -> int:
        """Update episode with calculated file size"""
        file_size = self.calculate_file_size(file_path)
        # Update database record
        # Implementation depends on repository pattern
        return file_size
```

#### 3.2 Enhanced Feed Generation Service
**File**: `backend/app/infrastructure/services/feed_generation_service_impl.py`

Major enhancements:
```python
def _create_episode(self, episode: Episode, base_url: str, all_episodes: List[Episode]) -> Optional[PodgenEpisode]:
    """Create PodGen episode with enhanced iTunes fields"""
    if not episode.audio_file_path:
        return None

    media_url = f"{base_url}/v1/media/episodes/{episode.id}/audio.mp3"

    # Calculate episode number based on position
    episode_number = episode.get_episode_number(all_episodes)

    # Generate subtitle
    subtitle = episode.generate_subtitle()

    # Format description
    formatted_description = episode.format_description_for_rss()

    # Get media file size
    media_file_service = MediaFileService()
    if not episode.media_file_size:
        file_size = media_file_service.calculate_file_size(episode.audio_file_path)
    else:
        file_size = episode.media_file_size

    try:
        # Create media object with proper size
        media = Media(
            url=media_url,
            size=file_size,
            type=self._get_media_type(episode.audio_file_path),
            duration=timedelta(seconds=episode.duration.seconds) if episode.duration else None
        )

        # Create episode with enhanced fields
        podcast_episode = PodgenEpisode(
            title=episode.title,
            summary=formatted_description,
            media=media,
            publication_date=pub_date
        )

        # Set iTunes-specific enhanced fields
        podcast_episode.subtitle = subtitle
        podcast_episode.position = episode_number

        # Use channel image for episode (if available)
        if hasattr(self, '_channel_image_url') and self._channel_image_url:
            podcast_episode.image = self._channel_image_url

        return podcast_episode

    except Exception as e:
        print(f"Error creating episode {episode.id}: {str(e)}")
        return None

def generate_rss_feed(
    self,
    channel: Channel,
    episodes: List[Episode],
    base_url: str
) -> str:
    """Generate iTunes-compliant RSS feed with enhanced fields"""

    # Store channel image for episode use
    self._channel_image_url = channel.image_url

    # Create podcast object with explicit content setting
    podcast = Podcast(
        name=channel.name,
        description=channel.description,
        website=channel.website_url,  # Now required
        language=channel.language,
        explicit=channel.explicit_content,  # Use channel setting
        category=self._get_category(channel.category, channel.subcategory),
        authors=[Person(
            name=channel.author_name or channel.owner_name,
            email=str(channel.owner_email) if channel.owner_email else None
        )],
        owner=Person(
            name=channel.owner_name or channel.author_name,
            email=str(channel.owner_email) if channel.owner_email else None
        )
    )

    # Set iTunes-specific fields
    if channel.image_url:
        podcast.image = channel.image_url

    if channel.copyright:
        podcast.copyright = channel.copyright

    # Set podcast type
    podcast.podcast_type = channel.podcast_type

    # Add episodes with enhanced metadata
    for ep in episodes:
        if ep.status.value == "completed" and ep.audio_file_path:
            podcast_episode = self._create_episode(ep, base_url, episodes)
            if podcast_episode:
                podcast.episodes.append(podcast_episode)

    return str(podcast)
```

### 4. API Layer Updates

#### 4.1 Channel API Enhancement
**File**: `backend/app/presentation/api/v1/channels.py`

Update validation schemas and endpoints:
```python
from pydantic import BaseModel, validator

class ChannelUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    website_url: str  # Make required
    explicit_content: Optional[bool] = None
    # ... other fields

    @validator('website_url')
    def validate_website_url(cls, v):
        if not v or len(v.strip()) < 1:
            raise ValueError('Website URL is required for iTunes compliance')
        return v

@router.put("/{channel_id}")
async def update_channel(
    channel_id: int,
    update_data: ChannelUpdateRequest,
    db: Session = Depends(get_database_session)
):
    """Update channel with enhanced validation"""
    # Implementation with website_url requirement
```

#### 4.2 Episodes API Enhancement
**File**: `backend/app/presentation/api/v1/episodes.py`

Add file size calculation:
```python
@router.post("/")
async def create_episode(
    episode_data: CreateEpisodeRequest,
    db: Session = Depends(get_database_session)
):
    """Create episode with file size calculation"""
    # After audio processing, calculate and store file size
    media_service = MediaFileService()
    file_size = media_service.calculate_file_size(audio_file_path)

    # Store file_size in episode model
```

### 5. Frontend Updates

#### 5.1 Settings Interface Enhancement
**File**: `frontend/src/components/features/settings/settings-interface.tsx`

Add explicit content and website URL validation:

```typescript
// In Channel tab rendering
<div className="grid gap-4 md:grid-cols-2">
  <div className="space-y-2">
    <Label htmlFor="website">Website URL *</Label>
    <Input
      id="website"
      type="url"
      required
      value={channelData.website}
      onChange={(e) => setChannelData({ ...channelData, website: e.target.value })}
      placeholder="https://your-podcast-website.com"
    />
    <p className="text-sm text-muted-foreground">
      Required for iTunes compliance
    </p>
  </div>

  <div className="space-y-2">
    <Label htmlFor="explicit">Content Rating</Label>
    <Select
      value={channelData.explicit ? "yes" : "no"}
      onValueChange={(value) => setChannelData({
        ...channelData,
        explicit: value === "yes"
      })}
    >
      <SelectTrigger>
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="yes">Explicit Content</SelectItem>
        <SelectItem value="no">Clean Content</SelectItem>
      </SelectContent>
    </Select>
    <p className="text-sm text-muted-foreground">
      Mark if podcast contains explicit language or content
    </p>
  </div>
</div>
```

#### 5.2 Enhanced RSS Feed Information
Add to RSS tab:
```typescript
// Enhanced feed information display
<Card>
  <CardHeader>
    <CardTitle>Feed Enhancement Status</CardTitle>
  </CardHeader>
  <CardContent>
    <div className="grid gap-4 md:grid-cols-2">
      <div className="flex items-center gap-3 p-3 bg-green-50 dark:bg-green-950 rounded-lg">
        <CheckCircle2 className="w-5 h-5 text-green-600" />
        <div>
          <div className="font-medium text-green-800 dark:text-green-200">Episode Numbering</div>
          <div className="text-sm text-green-600 dark:text-green-400">Automatic positioning</div>
        </div>
      </div>
      <div className="flex items-center gap-3 p-3 bg-green-50 dark:bg-green-950 rounded-lg">
        <CheckCircle2 className="w-5 h-5 text-green-600" />
        <div>
          <div className="font-medium text-green-800 dark:text-green-200">Enhanced Metadata</div>
          <div className="text-sm text-green-600 dark:text-green-400">Subtitles & descriptions</div>
        </div>
      </div>
    </div>
  </CardContent>
</Card>
```

#### 5.3 Types Updates
**File**: `frontend/src/types/index.ts`

```typescript
interface Channel {
  id: number
  name: string
  description: string
  website_url: string  // Make required
  explicit_content: boolean
  // ... other fields
}

interface Episode {
  id: number
  title: string
  description: string
  youtube_channel: string
  media_file_size: number
  episode_number?: number  // Calculated field
  subtitle?: string        // Generated field
  // ... other fields
}
```

### 6. Database Migration

#### 6.1 Migration Script
**New File**: `backend/app/infrastructure/database/migrations/005_enhance_rss_feed_fields.py`

```python
"""
Add media_file_size to episodes and update channel constraints
"""

def upgrade():
    # Add media_file_size to episodes
    op.add_column('episodes', sa.Column('media_file_size', sa.Integer(), default=0))

    # Update existing episodes to calculate file sizes
    # This would be done in a separate data migration script

    # Note: website_url constraint change requires careful handling
    # as it's changing from nullable to non-nullable

def downgrade():
    op.drop_column('episodes', 'media_file_size')
```

### 7. File Size Calculation Strategy

Based on the requirements analysis, we recommend **calculating file size once and storing in database** for the following reasons:

#### Advantages:
- ✅ **Performance**: No disk I/O on every feed generation
- ✅ **Reliability**: File size cached even if file moved
- ✅ **Scalability**: Better performance with many episodes
- ✅ **Consistency**: Same size reported across feed generations

#### Implementation Strategy:
1. Calculate file size immediately after audio download completion
2. Store in `media_file_size` field
3. Update size if file is re-processed
4. Fallback to real-time calculation if stored size is 0

#### Code Example:
```python
# In episode processing service
def process_episode_audio(episode_id: int, audio_file_path: str):
    # ... audio processing ...

    # Calculate and store file size
    media_service = MediaFileService()
    file_size = media_service.calculate_file_size(audio_file_path)

    # Update episode record
    episode_repo.update_file_size(episode_id, file_size)
```

## Implementation Task List

### Phase 1: Database & Domain Layer (Foundation)
1. **[CRITICAL]** Add `media_file_size` field to Episode model
2. **[CRITICAL]** Update Channel model constraints (website_url required, explicit_content default)
3. **[CRITICAL]** Enhance Episode domain entity with helper methods
4. **[CRITICAL]** Enhance Channel domain entity validation
5. **[MEDIUM]** Create MediaFileService for file size operations

### Phase 2: Backend Services (Core Logic)
6. **[CRITICAL]** Enhance FeedGenerationServiceImpl with all new RSS features
7. **[CRITICAL]** Add episode numbering logic based on created_at order
8. **[CRITICAL]** Implement episode subtitle generation from YouTube channel
9. **[CRITICAL]** Add description formatting with line break preservation
10. **[CRITICAL]** Implement media file size calculation and storage

### Phase 3: API Layer (Interface)
11. **[HIGH]** Update Channel API validation for required website_url
12. **[HIGH]** Update Episode API to calculate file size on creation
13. **[MEDIUM]** Add new RSS feed information endpoints
14. **[LOW]** Add feed regeneration endpoint with enhanced metadata

### Phase 4: Frontend (User Interface)
15. **[HIGH]** Add explicit content toggle to Channel settings
16. **[HIGH]** Make website URL required field with validation
17. **[HIGH]** Update TypeScript types for new fields
18. **[MEDIUM]** Enhance RSS feed information display
19. **[LOW]** Add feed enhancement status indicators

### Phase 5: Testing & Validation (Quality Assurance)
20. **[HIGH]** Test RSS feed generation with all new fields
21. **[HIGH]** Validate iTunes compliance with feed validators
22. **[HIGH]** Test file size calculation accuracy
23. **[MEDIUM]** Test episode numbering with various scenarios
24. **[MEDIUM]** Test description formatting with various content types

### Phase 6: Documentation & Deployment (Finalization)
25. **[MEDIUM]** Update API documentation for new fields
26. **[MEDIUM]** Create user guide for new settings
27. **[LOW]** Add RSS feed example documentation
28. **[LOW]** Performance testing with large episode lists

## Risk Mitigation

### Database Migration Risks
- **Risk**: Making website_url required could break existing channels
- **Mitigation**: Update existing null values to default placeholder before constraint change

### File Size Calculation Performance
- **Risk**: Calculating file sizes for many episodes could be slow
- **Mitigation**: Implement async calculation with background job processing

### RSS Feed Validation
- **Risk**: New RSS format might not validate correctly
- **Mitigation**: Implement comprehensive testing with iTunes Feed Validator

## Success Criteria

### Technical Requirements
- ✅ All episodes have episode numbers based on position
- ✅ All episodes have subtitles with YouTube channel info
- ✅ All episodes use channel image
- ✅ Media objects include correct file sizes
- ✅ Descriptions preserve formatting and line breaks
- ✅ Channel explicit content setting propagates to episodes
- ✅ Website URL is required and validated

### User Experience Requirements
- ✅ Settings interface allows easy explicit content configuration
- ✅ Website URL validation prevents invalid feeds
- ✅ RSS feed validates against iTunes standards
- ✅ Feed generation performance remains acceptable (<2 seconds)

### Business Requirements
- ✅ RSS feeds are fully iTunes compliant
- ✅ Feeds work with all major podcast platforms
- ✅ Enhanced metadata improves discoverability
- ✅ Professional appearance increases subscriber retention

## Post-Implementation Considerations

### Performance Monitoring
- Monitor RSS feed generation time
- Track file size calculation performance
- Monitor database query performance with new fields

### User Feedback Integration
- Collect feedback on new settings interface
- Monitor RSS feed validator results
- Track podcast platform acceptance rates

### Future Enhancements
- Consider season/series support for enhanced iTunes compliance
- Implement episode artwork support
- Add chapter markers support
- Consider transcript integration

---

**Document Version**: v1.0
**Last Updated**: 2025-09-15
**Status**: Draft - Pending Implementation