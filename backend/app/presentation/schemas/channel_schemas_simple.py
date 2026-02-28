"""
Simplified Channel API Request/Response Schemas for existing database
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
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


class ChannelUpdateRequest(BaseModel):
    """Request schema for updating channel settings"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=255, description="Channel name")
    description: Optional[str] = Field(default=None, description="Channel description")
    website_url: Optional[str] = Field(default=None, description="Channel website URL")
    image_url: Optional[str] = Field(default=None, description="Channel image URL")
    category: Optional[str] = Field(default=None, description="iTunes category")
    language: Optional[str] = Field(default=None, min_length=2, max_length=2, description="Language code (ISO 639-1)")
    explicit_content: Optional[bool] = Field(default=None, description="Contains explicit content")
    author_name: Optional[str] = Field(default=None, description="Author name")
    author_email: Optional[str] = Field(default=None, description="Author email")
    owner_name: Optional[str] = Field(default=None, description="Owner name")
    owner_email: Optional[str] = Field(default=None, description="Owner email")


class ChannelResponse(BaseModel):
    """Response schema for channel data (using existing database fields only)"""
    id: int = Field(..., description="Channel ID")
    user_id: int = Field(..., description="User ID who owns the channel")
    name: str = Field(..., description="Channel name")
    description: Optional[str] = Field(default=None, description="Channel description")
    website_url: str = Field(..., description="Channel website URL")
    image_url: Optional[str] = Field(default=None, description="Channel image URL")
    category: Optional[str] = Field(default="Technology", description="iTunes category")
    language: Optional[str] = Field(default="en", description="Language code")
    explicit_content: Optional[bool] = Field(default=False, description="Contains explicit content")
    author_name: Optional[str] = Field(default="", description="Author name")
    author_email: Optional[str] = Field(default=None, description="Author email")
    owner_name: Optional[str] = Field(default="", description="Owner name")
    owner_email: Optional[str] = Field(default=None, description="Owner email")
    feed_url: Optional[str] = Field(default="", description="RSS feed URL")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    
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
    unique_youtube_channels: int = Field(..., description="Number of unique YouTube channels")
    feed_validation_score: Optional[float] = Field(default=None, description="RSS feed validation score")
    feed_last_updated: Optional[datetime] = Field(default=None, description="When feed was last updated")
    latest_episode: Optional[dict] = Field(default=None, description="Information about latest episode")
    created_at: Optional[datetime] = Field(default=None, description="Channel creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Channel last update timestamp")
    
    class Config:
        from_attributes = True