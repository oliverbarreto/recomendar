"""
Channel API Request/Response Schemas
"""
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, Dict, Any
from datetime import datetime


class ChannelCreateRequest(BaseModel):
    """Request schema for creating a channel"""
    user_id: int = Field(..., description="User ID who owns the channel")
    name: str = Field(..., min_length=1, max_length=255, description="Channel name")
    description: str = Field(..., description="Channel description")
    website_url: str = Field(..., description="Channel website URL (required for iTunes compliance)")
    author_name: Optional[str] = Field(default=None, description="Author name")
    author_email: Optional[str] = Field(default=None, description="Author email")

    @validator('website_url')
    def validate_website_url(cls, v):
        if not v or len(v.strip()) < 1:
            raise ValueError('Website URL is required for iTunes compliance')
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "name": "My Tech Podcast",
                "description": "A podcast about the latest in technology and programming",
                "author_name": "John Doe",
                "author_email": "john@example.com"
            }
        }


class ChannelUpdateRequest(BaseModel):
    """Request schema for updating channel settings"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=255, description="Channel name")
    description: Optional[str] = Field(default=None, description="Channel description")
    website_url: Optional[str] = Field(default=None, description="Channel website URL (required for iTunes compliance)")
    image_url: Optional[str] = Field(default=None, description="Channel image URL")
    category: Optional[str] = Field(default=None, description="iTunes category")
    language: Optional[str] = Field(default=None, min_length=2, max_length=2, description="Language code (ISO 639-1)")
    explicit_content: Optional[bool] = Field(default=None, description="Contains explicit content")
    author_name: Optional[str] = Field(default=None, description="Author name")
    author_email: Optional[str] = Field(default=None, description="Author email")
    owner_name: Optional[str] = Field(default=None, description="Owner name")
    owner_email: Optional[str] = Field(default=None, description="Owner email")
    copyright: Optional[str] = Field(default=None, description="Copyright notice")
    podcast_type: Optional[str] = Field(default=None, description="Podcast type (episodic or serial)")
    subcategory: Optional[str] = Field(default=None, description="iTunes subcategory")

    @validator('website_url')
    def validate_website_url(cls, v):
        if v is not None and (not v or len(v.strip()) < 1):
            raise ValueError('Website URL cannot be empty if provided. It is required for iTunes compliance')
        return v.strip() if v else v
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated Tech Podcast",
                "description": "An updated description for the tech podcast",
                "website_url": "https://mytechpodcast.com",
                "image_url": "https://mytechpodcast.com/image.jpg",
                "category": "Technology",
                "language": "en",
                "explicit_content": False,
                "author_name": "John Doe",
                "author_email": "john@example.com",
                "copyright": "© 2024 John Doe"
            }
        }


class ChannelResponse(BaseModel):
    """Response schema for channel data"""
    id: int = Field(..., description="Channel ID")
    user_id: int = Field(..., description="User ID who owns the channel")
    name: str = Field(..., description="Channel name")
    description: str = Field(..., description="Channel description")
    website_url: str = Field(..., description="Channel website URL")
    image_url: Optional[str] = Field(default=None, description="Channel image URL")
    category: str = Field(default="Technology", description="iTunes category")
    language: str = Field(default="en", description="Language code")
    explicit_content: bool = Field(default=True, description="Contains explicit content")
    author_name: str = Field(default="", description="Author name")
    author_email: Optional[str] = Field(default=None, description="Author email")
    owner_name: str = Field(default="", description="Owner name")
    owner_email: Optional[str] = Field(default=None, description="Owner email")
    feed_url: str = Field(default="", description="RSS feed URL")
    feed_last_updated: Optional[datetime] = Field(default=None, description="When feed was last updated")
    feed_validation_score: Optional[float] = Field(default=None, description="iTunes validation score")
    copyright: Optional[str] = Field(default=None, description="Copyright notice")
    podcast_type: str = Field(default="episodic", description="Podcast type")
    subcategory: Optional[str] = Field(default=None, description="iTunes subcategory")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "user_id": 1,
                "name": "My Tech Podcast",
                "description": "A podcast about technology",
                "website_url": "https://mytechpodcast.com",
                "image_url": "https://mytechpodcast.com/image.jpg",
                "category": "Technology",
                "language": "en",
                "explicit_content": False,
                "author_name": "John Doe",
                "author_email": "john@example.com",
                "owner_name": "John Doe",
                "owner_email": "john@example.com",
                "feed_url": "https://mytechpodcast.com/feed.xml",
                "feed_validation_score": 92.5,
                "copyright": "© 2024 John Doe",
                "podcast_type": "episodic",
                "subcategory": None,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T12:45:00Z"
            }
        }


class ChannelSettingsResponse(BaseModel):
    """Detailed channel settings response for RSS feed configuration"""
    id: int = Field(..., description="Channel ID")
    user_id: int = Field(..., description="User ID")
    name: str = Field(..., description="Channel name")
    description: str = Field(..., description="Channel description")
    website_url: Optional[str] = Field(default=None, description="Website URL")
    image_url: Optional[str] = Field(default=None, description="Image URL")
    category: str = Field(..., description="iTunes category")
    language: str = Field(..., description="Language code")
    explicit_content: bool = Field(..., description="Explicit content flag")
    author_name: str = Field(..., description="Author name")
    author_email: Optional[str] = Field(default=None, description="Author email")
    owner_name: str = Field(..., description="Owner name")
    owner_email: Optional[str] = Field(default=None, description="Owner email")
    copyright: Optional[str] = Field(default=None, description="Copyright notice")
    podcast_type: str = Field(..., description="Podcast type (episodic/serial)")
    subcategory: Optional[str] = Field(default=None, description="iTunes subcategory")
    feed_url: str = Field(..., description="RSS feed URL")
    feed_validation_score: Optional[float] = Field(default=None, description="Validation score")
    feed_last_updated: Optional[datetime] = Field(default=None, description="Last feed update")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Update timestamp")
    
    class Config:
        from_attributes = True


class ChannelStatisticsResponse(BaseModel):
    """Channel statistics response"""
    channel_id: int = Field(..., description="Channel ID")
    channel_name: str = Field(..., description="Channel name")
    total_episodes: int = Field(..., description="Total number of episodes")
    published_episodes: int = Field(..., description="Number of published episodes")
    draft_episodes: int = Field(..., description="Number of draft episodes")
    processing_episodes: int = Field(..., description="Number of processing episodes")
    total_duration_seconds: int = Field(..., description="Total duration of all episodes in seconds")
    total_size_bytes: int = Field(..., description="Total size of all episodes in bytes")
    feed_validation_score: Optional[float] = Field(default=None, description="RSS feed validation score")
    feed_last_updated: Optional[datetime] = Field(default=None, description="When feed was last updated")
    latest_episode: Optional[Dict[str, Any]] = Field(default=None, description="Information about latest episode")
    created_at: Optional[datetime] = Field(default=None, description="Channel creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Channel last update timestamp")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "channel_id": 1,
                "channel_name": "My Tech Podcast",
                "total_episodes": 25,
                "published_episodes": 20,
                "draft_episodes": 3,
                "processing_episodes": 2,
                "total_duration_seconds": 72000,
                "total_size_bytes": 1073741824,
                "feed_validation_score": 95.5,
                "latest_episode": {
                    "title": "Latest Episode About AI",
                    "publication_date": "2024-01-15T09:00:00Z",
                    "duration": 3600
                },
                "created_at": "2024-01-01T10:30:00Z",
                "updated_at": "2024-01-15T12:45:00Z"
            }
        }