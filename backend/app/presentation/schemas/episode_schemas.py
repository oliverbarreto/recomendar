"""
Episode API schemas for request/response validation
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from app.domain.entities.episode import EpisodeStatus


class EpisodeStatusEnum(str, Enum):
    """Episode status for API responses"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class EpisodeCreate(BaseModel):
    """Schema for creating new episodes"""
    channel_id: int = Field(..., gt=0, description="Channel ID to associate episode with")
    video_url: str = Field(..., min_length=1, max_length=2048, description="YouTube video URL")
    tags: Optional[List[str]] = Field(default=[], description="Optional tags for the episode")
    audio_language: Optional[str] = Field(default=None, max_length=10, description="Preferred audio language (ISO 639-1)")
    audio_quality: Optional[str] = Field(default=None, pattern="^(low|medium|high)$", description="Preferred audio quality tier")
    
    @validator('video_url')
    def validate_url(cls, v):
        if not v.strip():
            raise ValueError('URL cannot be empty')
        return v.strip()
    
    @validator('tags')
    def validate_tags(cls, v):
        if v is None:
            return []
        
        # Limit number of tags
        if len(v) > 10:
            raise ValueError('Maximum 10 tags allowed')
        
        # Validate individual tags
        validated_tags = []
        for tag in v:
            if isinstance(tag, str):
                clean_tag = tag.strip()
                if len(clean_tag) > 50:
                    raise ValueError('Tag length cannot exceed 50 characters')
                if clean_tag:
                    validated_tags.append(clean_tag)
        
        return validated_tags


class EpisodeCreateFromUpload(BaseModel):
    """Schema for creating episodes from uploaded audio files"""
    channel_id: int = Field(..., gt=0, description="Channel ID to associate episode with")
    title: str = Field(..., min_length=1, max_length=500, description="Episode title")
    description: Optional[str] = Field(None, max_length=5000, description="Episode description")
    publication_date: Optional[datetime] = Field(None, description="Publication date (defaults to now)")
    tags: Optional[List[str]] = Field(default=[], description="Optional tags for the episode")
    
    @validator('title')
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()
    
    @validator('tags')
    def validate_tags(cls, v):
        if v is None:
            return []
        
        # Limit number of tags
        if len(v) > 10:
            raise ValueError('Maximum 10 tags allowed')
        
        # Validate individual tags
        validated_tags = []
        for tag in v:
            if isinstance(tag, str):
                clean_tag = tag.strip()
                if len(clean_tag) > 50:
                    raise ValueError('Tag length cannot exceed 50 characters')
                if clean_tag:
                    validated_tags.append(clean_tag)
        
        return validated_tags
    
    @validator('publication_date', pre=True)
    def validate_publication_date(cls, v):
        if v is None:
            return datetime.utcnow()
        return v


class EpisodeUpdate(BaseModel):
    """Schema for updating episodes"""
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=5000)
    keywords: Optional[List[str]] = Field(None, max_items=20)
    tags: Optional[List[int]] = Field(None, max_items=10)
    
    @validator('title')
    def validate_title(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip() if v else None


class EpisodeResponse(BaseModel):
    """Schema for episode API responses"""
    id: int
    channel_id: int
    video_id: str = Field(..., description="Episode ID (yt_* for YouTube, up_* for uploads)")
    title: str
    description: str
    publication_date: datetime
    audio_file_path: Optional[str]
    video_url: str
    thumbnail_url: Optional[str]

    @validator('video_id')
    def validate_video_id_format(cls, v):
        """Validate that video_id follows the yt_* or up_* format"""
        if not v:
            raise ValueError('video_id is required')
        if not (v.startswith('yt_') or v.startswith('up_')):
            raise ValueError('video_id must start with yt_ or up_')
        if len(v) != 14:
            raise ValueError('video_id must be 14 characters (3-char prefix + 11-char ID)')
        return v
    duration_seconds: Optional[int]
    keywords: List[str]
    status: EpisodeStatusEnum
    retry_count: int
    download_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    tags: List[Dict[str, Any]] = []

    # YouTube channel information
    youtube_channel: Optional[str] = None
    youtube_channel_id: Optional[str] = None
    youtube_channel_url: Optional[str] = None

    # User preferences
    is_favorited: bool = False

    # Media file information
    media_file_size: Optional[int] = 0

    # Audio language and quality
    audio_language: Optional[str] = None
    audio_quality: Optional[str] = None
    requested_language: Optional[str] = None
    requested_quality: Optional[str] = None

    # Episode numbering
    episode_number: Optional[int] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
    
    @classmethod
    def from_entity(cls, episode, tags=None, episodes_list=None, total_count=None, skip=0):
        """
        Create response from episode entity
        
        Args:
            episode: Episode entity to convert
            tags: Optional tags (deprecated, use episode.tags)
            episodes_list: List of episodes in current page (for index calculation)
            total_count: Total number of episodes in channel (for episode numbering)
            skip: Pagination offset (number of episodes skipped)
        """
        # Convert tag entities to dictionaries
        episode_tags = []
        if hasattr(episode, 'tags') and episode.tags:
            for tag in episode.tags:
                episode_tags.append({
                    'id': tag.id,
                    'name': tag.name,
                    'color': tag.color,
                    'usage_count': tag.usage_count,
                    'is_system_tag': tag.is_system_tag,
                    'created_at': tag.created_at,
                    'updated_at': tag.updated_at
                })

        # Calculate episode number based on total count and pagination
        # Episodes are ordered by created_at DESC (newest first)
        # Formula: episode_number = total_count - (skip + index_in_current_page)
        episode_number = None
        if total_count is not None and episodes_list is not None:
            try:
                # Find the index of this episode in the current page
                index_in_page = episodes_list.index(episode)
                # Calculate the episode number (oldest episode = #1)
                episode_number = total_count - (skip + index_in_page)
            except (ValueError, AttributeError):
                # If episode not found in list, set to None
                episode_number = None

        return cls(
            id=episode.id,
            channel_id=episode.channel_id,
            video_id=episode.video_id.value,  # Always has value now (yt_* or up_*)
            title=episode.title,
            description=episode.description,
            publication_date=episode.publication_date,
            audio_file_path=episode.audio_file_path,
            video_url=episode.video_url,
            thumbnail_url=episode.thumbnail_url,
            duration_seconds=episode.duration.seconds if episode.duration else None,
            keywords=episode.keywords,
            status=EpisodeStatusEnum(episode.status.value),
            retry_count=episode.retry_count,
            download_date=episode.download_date,
            created_at=episode.created_at,
            updated_at=episode.updated_at,
            tags=episode_tags,
            youtube_channel=episode.youtube_channel,
            youtube_channel_id=episode.youtube_channel_id,
            youtube_channel_url=episode.youtube_channel_url,
            is_favorited=episode.is_favorited,
            media_file_size=episode.media_file_size,
            audio_language=episode.audio_language,
            audio_quality=episode.audio_quality,
            requested_language=episode.requested_language,
            requested_quality=episode.requested_quality,
            episode_number=episode_number
        )


class EpisodeListResponse(BaseModel):
    """Schema for paginated episode list responses"""
    episodes: List[EpisodeResponse]
    total: int
    skip: int
    limit: int
    
    class Config:
        from_attributes = True


class ProgressResponse(BaseModel):
    """Schema for download progress responses"""
    episode_id: int
    status: str
    percentage: str
    speed: str
    eta: str
    downloaded_bytes: int
    total_bytes: int
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    updated_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class EpisodeStatusResponse(BaseModel):
    """Schema for episode status responses"""
    episode_id: int
    status: EpisodeStatusEnum
    retry_count: int
    audio_file_path: Optional[str]
    download_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class MetadataAnalysisRequest(BaseModel):
    """Schema for metadata analysis requests"""
    video_url: str = Field(..., min_length=1, max_length=2048)
    
    @validator('video_url')
    def validate_url(cls, v):
        return v.strip()


class MetadataAnalysisResponse(BaseModel):
    """Schema for metadata analysis responses"""
    video_id: str
    title: str
    description: str
    duration_seconds: Optional[int]
    thumbnail_url: Optional[str]
    uploader: Optional[str]
    view_count: int
    publication_date: Optional[str]
    keywords: List[str]
    video_url: str
    availability: Optional[str]

    # YouTube channel information
    channel: Optional[str] = None  # Full channel name
    channel_id: Optional[str] = None  # YouTube channel ID
    channel_url: Optional[str] = None  # Channel URL
    
    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    """Schema for error responses"""
    error: str
    code: str
    details: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class SuccessResponse(BaseModel):
    """Schema for success responses"""
    message: str
    data: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class EpisodeFilters(BaseModel):
    """Schema for episode filtering parameters"""
    channel_id: int
    status: Optional[EpisodeStatusEnum] = None
    search: Optional[str] = Field(None, max_length=500)
    skip: int = Field(0, ge=0)
    limit: int = Field(50, ge=1, le=100)
    order_by: Optional[str] = Field("created_at", pattern="^(created_at|updated_at|title|publication_date)$")
    order_desc: bool = Field(True)
    
    @validator('search')
    def validate_search(cls, v):
        if v is not None:
            return v.strip() or None
        return None