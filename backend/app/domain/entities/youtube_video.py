"""
YouTubeVideo domain entity

Represents a discovered YouTube video from a followed channel.
Videos are stored separately from episodes until the user decides to create an episode.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class YouTubeVideoState(Enum):
    """State of a YouTube video in the discovery workflow"""
    PENDING_REVIEW = "pending_review"
    REVIEWED = "reviewed"
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    EPISODE_CREATED = "episode_created"
    DISCARDED = "discarded"


@dataclass
class YouTubeVideo:
    """
    YouTubeVideo domain entity representing a video discovered from a followed channel
    
    Videos start in 'pending_review' state and transition through states
    as the user reviews and creates episodes from them.
    """
    id: Optional[int]
    video_id: str  # YouTube video ID (11 chars)
    followed_channel_id: int
    
    # Video metadata from YouTube
    title: str
    description: Optional[str] = None
    url: str = ""
    thumbnail_url: Optional[str] = None
    publish_date: Optional[datetime] = None
    
    # Video statistics
    duration: Optional[int] = None  # Duration in seconds
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    comment_count: Optional[int] = None
    
    # Raw metadata JSON from yt-dlp
    metadata_json: Optional[str] = None  # Full yt-dlp metadata as JSON string
    
    # Video state and workflow
    state: YouTubeVideoState = YouTubeVideoState.PENDING_REVIEW
    episode_id: Optional[int] = None  # Link to created episode
    
    # Timestamps
    reviewed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate and initialize YouTube video"""
        # Validate required fields
        if not self.video_id or len(self.video_id.strip()) < 1:
            raise ValueError("Video ID is required")
        self.video_id = self.video_id.strip()
        
        if self.followed_channel_id <= 0:
            raise ValueError("Valid followed_channel_id is required")
        
        if not self.title or len(self.title.strip()) < 1:
            raise ValueError("Video title is required")
        self.title = self.title.strip()
        
        if not self.url:
            # Generate YouTube URL from video ID
            self.url = f"https://www.youtube.com/watch?v={self.video_id}"
        
        if not self.publish_date:
            self.publish_date = datetime.utcnow()
        
        # Set timestamps
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def mark_as_reviewed(self) -> None:
        """Mark video as reviewed"""
        if self.state != YouTubeVideoState.PENDING_REVIEW:
            raise ValueError(f"Cannot mark as reviewed from state {self.state.value}")
        
        self.state = YouTubeVideoState.REVIEWED
        self.reviewed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def mark_as_discarded(self) -> None:
        """Mark video as discarded"""
        if self.state in [YouTubeVideoState.EPISODE_CREATED, YouTubeVideoState.DISCARDED]:
            raise ValueError(f"Cannot discard video in state {self.state.value}")
        
        self.state = YouTubeVideoState.DISCARDED
        self.reviewed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def queue_for_episode_creation(self) -> None:
        """Queue video for episode creation"""
        if self.state not in [YouTubeVideoState.PENDING_REVIEW, YouTubeVideoState.REVIEWED]:
            raise ValueError(f"Cannot queue from state {self.state.value}")
        
        self.state = YouTubeVideoState.QUEUED
        self.updated_at = datetime.utcnow()
    
    def mark_as_downloading(self) -> None:
        """Mark video as downloading audio"""
        if self.state != YouTubeVideoState.QUEUED:
            raise ValueError(f"Cannot mark as downloading from state {self.state.value}")
        
        self.state = YouTubeVideoState.DOWNLOADING
        self.updated_at = datetime.utcnow()
    
    def mark_as_episode_created(self, episode_id: int) -> None:
        """Mark video as having an episode created"""
        if self.state != YouTubeVideoState.DOWNLOADING:
            raise ValueError(f"Cannot mark as episode created from state {self.state.value}")
        
        if episode_id <= 0:
            raise ValueError("Valid episode_id is required")
        
        self.state = YouTubeVideoState.EPISODE_CREATED
        self.episode_id = episode_id
        self.updated_at = datetime.utcnow()
    
    def update_metadata(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        duration: Optional[int] = None,
        view_count: Optional[int] = None,
        like_count: Optional[int] = None,
        comment_count: Optional[int] = None,
        metadata_json: Optional[str] = None
    ) -> None:
        """
        Update video metadata from YouTube
        
        Args:
            title: Updated video title
            description: Updated video description
            thumbnail_url: Updated thumbnail URL
            duration: Updated duration in seconds
            view_count: Updated view count
            like_count: Updated like count
            comment_count: Updated comment count
            metadata_json: Updated raw metadata JSON
        """
        if title is not None:
            if not title or len(title.strip()) < 1:
                raise ValueError("Video title cannot be empty")
            self.title = title.strip()
        
        if description is not None:
            self.description = description
        
        if thumbnail_url is not None:
            self.thumbnail_url = thumbnail_url.strip() if thumbnail_url else None
        
        if duration is not None:
            if duration < 0:
                raise ValueError("Duration cannot be negative")
            self.duration = duration
        
        if view_count is not None:
            if view_count < 0:
                raise ValueError("View count cannot be negative")
            self.view_count = view_count
        
        if like_count is not None:
            if like_count < 0:
                raise ValueError("Like count cannot be negative")
            self.like_count = like_count
        
        if comment_count is not None:
            if comment_count < 0:
                raise ValueError("Comment count cannot be negative")
            self.comment_count = comment_count
        
        if metadata_json is not None:
            self.metadata_json = metadata_json
        
        self.updated_at = datetime.utcnow()
    
    def can_create_episode(self) -> bool:
        """Check if video can be used to create an episode"""
        return self.state in [YouTubeVideoState.PENDING_REVIEW, YouTubeVideoState.REVIEWED]
    
    def can_be_discarded(self) -> bool:
        """Check if video can be discarded"""
        return self.state in [YouTubeVideoState.PENDING_REVIEW, YouTubeVideoState.REVIEWED]







