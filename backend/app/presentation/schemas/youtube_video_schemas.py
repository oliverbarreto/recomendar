"""
YouTube Video API Request/Response Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class YouTubeVideoStateEnum(str, Enum):
    """YouTube video state enum for API"""
    PENDING_REVIEW = "pending_review"
    REVIEWED = "reviewed"
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    EPISODE_CREATED = "episode_created"
    DISCARDED = "discarded"


class YouTubeVideoResponse(BaseModel):
    """Response schema for YouTube video data"""
    id: int = Field(..., description="YouTube video database ID")
    video_id: str = Field(..., description="YouTube video ID")
    followed_channel_id: int = Field(..., description="Followed channel ID")
    title: str = Field(..., description="Video title")
    description: Optional[str] = Field(default=None, description="Video description")
    url: str = Field(..., description="YouTube video URL")
    thumbnail_url: Optional[str] = Field(default=None, description="Video thumbnail URL")
    publish_date: Optional[datetime] = Field(default=None, description="Video publish date")
    duration: Optional[int] = Field(default=None, description="Video duration in seconds")
    view_count: Optional[int] = Field(default=None, description="View count")
    like_count: Optional[int] = Field(default=None, description="Like count")
    comment_count: Optional[int] = Field(default=None, description="Comment count")
    state: str = Field(..., description="Video state")
    episode_id: Optional[int] = Field(default=None, description="Linked episode ID if created")
    reviewed_at: Optional[datetime] = Field(default=None, description="When video was reviewed")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


class YouTubeVideoListFilters(BaseModel):
    """Query parameters for listing YouTube videos"""
    state: Optional[str] = Field(
        default=None,
        description="Filter by state (pending_review, reviewed, episode_created, etc.)"
    )
    followed_channel_id: Optional[int] = Field(
        default=None,
        description="Filter by followed channel ID"
    )
    search: Optional[str] = Field(
        default=None,
        description="Search query (searches title and description)"
    )
    skip: int = Field(default=0, ge=0, description="Number of videos to skip")
    limit: int = Field(default=50, ge=1, le=100, description="Maximum number of videos to return")


class CreateEpisodeFromVideoRequest(BaseModel):
    """Request schema for creating an episode from a video"""
    channel_id: int = Field(..., gt=0, description="Podcast channel ID to create episode in")
    audio_language: Optional[str] = Field(default=None, description="Preferred audio language (ISO 639-1)")
    audio_quality: Optional[str] = Field(default=None, description="Preferred audio quality tier (low/medium/high)")


class CreateEpisodeFromVideoResponse(BaseModel):
    """Response schema for episode creation task"""
    status: str = Field(..., description="Task status")
    task_id: str = Field(..., description="Celery task ID")
    youtube_video_id: int = Field(..., description="YouTube video ID")
    channel_id: int = Field(..., description="Podcast channel ID")
    episode_id: Optional[int] = Field(default=None, description="Created episode ID (if available)")
    message: str = Field(..., description="Status message")


class YouTubeVideoStatsResponse(BaseModel):
    """Response schema for video statistics"""
    pending_review: int = Field(default=0, description="Count of videos pending review")
    reviewed: int = Field(default=0, description="Count of reviewed videos")
    queued: int = Field(default=0, description="Count of queued videos")
    downloading: int = Field(default=0, description="Count of videos being downloaded")
    episode_created: int = Field(default=0, description="Count of videos with episodes created")
    discarded: int = Field(default=0, description="Count of discarded videos")
    total: int = Field(default=0, description="Total count of videos")


class YouTubeVideoWithChannelResponse(YouTubeVideoResponse):
    """Response schema for YouTube video with channel information"""
    followed_channel: Optional[dict] = Field(
        default=None,
        description="Followed channel information"
    )


class BulkActionType(str, Enum):
    """Bulk action types"""
    REVIEW = "review"
    DISCARD = "discard"
    CREATE_EPISODE = "create_episode"


class BulkActionRequest(BaseModel):
    """Request schema for bulk actions on videos"""
    video_ids: List[int] = Field(..., min_length=1, description="List of video IDs to perform action on")
    action: BulkActionType = Field(..., description="Action to perform")
    channel_id: Optional[int] = Field(default=None, description="Channel ID (required for create_episode action)")
    audio_language: Optional[str] = Field(default=None, description="Preferred audio language (ISO 639-1)")
    audio_quality: Optional[str] = Field(default=None, description="Preferred audio quality tier (low/medium/high)")


class BulkActionResult(BaseModel):
    """Result for a single video in bulk action"""
    video_id: int = Field(..., description="Video ID")
    success: bool = Field(..., description="Whether the action succeeded")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    task_id: Optional[str] = Field(default=None, description="Celery task ID (for create_episode action)")


class BulkActionResponse(BaseModel):
    """Response schema for bulk actions"""
    action: str = Field(..., description="Action performed")
    total: int = Field(..., description="Total number of videos")
    successful: int = Field(..., description="Number of successful operations")
    failed: int = Field(..., description="Number of failed operations")
    results: List[BulkActionResult] = Field(..., description="Detailed results for each video")





