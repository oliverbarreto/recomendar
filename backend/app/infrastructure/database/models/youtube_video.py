"""
YouTubeVideo SQLAlchemy model

Represents a discovered YouTube video from a followed channel.
Videos are stored separately from episodes until the user decides to create an episode.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.infrastructure.database.connection import Base


class YouTubeVideoState(enum.Enum):
    """State of a YouTube video in the discovery workflow"""
    PENDING_REVIEW = "pending_review"
    REVIEWED = "reviewed"
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    EPISODE_CREATED = "episode_created"
    DISCARDED = "discarded"


class YouTubeVideoModel(Base):
    """
    SQLAlchemy model for YouTubeVideo entity
    
    Represents a video discovered from a followed YouTube channel.
    Videos start in 'pending_review' state and transition through states
    as the user reviews and creates episodes from them.
    """
    __tablename__ = "youtube_videos"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(String(255), nullable=False, unique=True, index=True)  # YouTube video ID (11 chars)
    followed_channel_id = Column(Integer, ForeignKey("followed_channels.id"), nullable=False, index=True)
    
    # Video metadata from YouTube
    title = Column(String(500), nullable=False)
    description = Column(Text)
    url = Column(String(500), nullable=False)
    thumbnail_url = Column(String(500))
    publish_date = Column(DateTime, nullable=False, index=True)
    
    # Video statistics
    duration = Column(Integer)  # Duration in seconds
    view_count = Column(Integer)
    like_count = Column(Integer)
    comment_count = Column(Integer)
    
    # Raw metadata JSON from yt-dlp
    metadata_json = Column(Text)  # Full yt-dlp metadata as JSON string
    
    # Video state and workflow
    # Store enum as string value (e.g., "pending_review") not enum name (e.g., "PENDING_REVIEW")
    state = Column(String(50), nullable=False, default="pending_review", index=True)
    episode_id = Column(Integer, ForeignKey("episodes.id"), nullable=True)  # Link to created episode
    
    # Timestamps
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    followed_channel = relationship("FollowedChannelModel", back_populates="youtube_videos")
    episode = relationship("EpisodeModel", foreign_keys=[episode_id])

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('video_id', name='uq_youtube_video_id'),
        Index('idx_youtube_video_followed_channel', 'followed_channel_id'),
        Index('idx_youtube_video_state', 'state'),
        Index('idx_youtube_video_publish_date', 'publish_date'),
        Index('idx_youtube_video_channel_state', 'followed_channel_id', 'state'),
        Index('idx_youtube_video_episode_id', 'episode_id'),
    )

    def __repr__(self):
        return f"<YouTubeVideoModel(id={self.id}, video_id='{self.video_id}', state='{self.state.value}')>"







