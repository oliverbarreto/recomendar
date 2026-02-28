"""
Followed Channel API Request/Response Schemas
"""
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional
from datetime import datetime


class FollowedChannelCreateRequest(BaseModel):
    """Request schema for following a channel"""
    channel_url: str = Field(..., description="YouTube channel URL (supports various formats)")
    auto_approve: bool = Field(default=False, description="Enable auto-approve for new videos")
    auto_approve_channel_id: Optional[int] = Field(
        default=None,
        description="Target podcast channel ID for auto-approval (required if auto_approve is true)"
    )
    
    @model_validator(mode='after')
    def validate_auto_approve_channel(self):
        """Validate that auto_approve_channel_id is provided when auto_approve is enabled"""
        if self.auto_approve and not self.auto_approve_channel_id:
            raise ValueError('auto_approve_channel_id is required when auto_approve is enabled')
        return self
    
    class Config:
        # Allow extra fields to be ignored (in case frontend sends undefined values)
        extra = "ignore"


class FollowedChannelUpdateRequest(BaseModel):
    """Request schema for updating followed channel settings"""
    auto_approve: Optional[bool] = Field(default=None, description="Enable/disable auto-approve")
    auto_approve_channel_id: Optional[int] = Field(
        default=None,
        description="Target podcast channel ID for auto-approval (required if auto_approve is true)"
    )
    
    @model_validator(mode='after')
    def validate_auto_approve_channel(self):
        """Validate that auto_approve_channel_id is provided when auto_approve is enabled"""
        if self.auto_approve and not self.auto_approve_channel_id:
            raise ValueError('auto_approve_channel_id is required when auto_approve is enabled')
        return self


class FollowedChannelResponse(BaseModel):
    """Response schema for followed channel data"""
    id: int = Field(..., description="Followed channel ID")
    user_id: int = Field(..., description="User ID who is following the channel")
    youtube_channel_id: str = Field(..., description="YouTube channel ID")
    youtube_channel_name: str = Field(..., description="YouTube channel name")
    youtube_channel_url: str = Field(..., description="YouTube channel URL")
    thumbnail_url: Optional[str] = Field(default=None, description="Channel thumbnail URL")
    youtube_channel_description: Optional[str] = Field(default=None, description="Channel description")
    auto_approve: bool = Field(default=False, description="Auto-approve enabled")
    auto_approve_channel_id: Optional[int] = Field(default=None, description="Target podcast channel ID")
    last_checked: Optional[datetime] = Field(default=None, description="Last check timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


class FollowedChannelWithStatsResponse(FollowedChannelResponse):
    """Response schema for followed channel with statistics"""
    pending_videos_count: int = Field(default=0, description="Number of videos pending review")
    reviewed_videos_count: int = Field(default=0, description="Number of reviewed videos")
    episode_created_count: int = Field(default=0, description="Number of videos with episodes created")
    total_videos_count: int = Field(default=0, description="Total number of videos")


class BackfillRequest(BaseModel):
    """Request schema for triggering channel backfill"""
    year: Optional[int] = Field(
        default=None,
        ge=2000,
        le=2100,
        description="Year to backfill (None for all years)"
    )
    max_videos: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of videos to fetch"
    )


class BackfillResponse(BaseModel):
    """Response schema for backfill task"""
    status: str = Field(..., description="Task status")
    task_id: str = Field(..., description="Celery task ID")
    followed_channel_id: int = Field(..., description="Followed channel ID")
    year: Optional[int] = Field(default=None, description="Year being backfilled")
    max_videos: int = Field(..., description="Maximum videos to fetch")
    message: str = Field(..., description="Status message")

