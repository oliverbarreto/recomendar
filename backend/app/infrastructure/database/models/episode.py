"""
Episode SQLAlchemy model
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Index, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.infrastructure.database.connection import Base


class EpisodeModel(Base):
    """
    SQLAlchemy model for Episode entity
    """
    __tablename__ = "episodes"

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False)
    video_id = Column(String(14), nullable=False, index=True)  # 14 chars: yt_/up_ (3) + ID (11)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    publication_date = Column(DateTime, nullable=False)
    audio_file_path = Column(String(1000))
    video_url = Column(String(500))
    thumbnail_url = Column(String(500))
    duration_seconds = Column(Integer)
    keywords = Column(JSON)  # Stored as JSON array
    status = Column(String(20), default="pending", index=True)
    retry_count = Column(Integer, default=0)
    download_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # YouTube channel information
    youtube_channel = Column(String(255))  # Full channel name
    youtube_channel_id = Column(String(255), index=True)  # YouTube channel ID
    youtube_channel_url = Column(String(500))  # Channel URL

    # User preferences
    is_favorited = Column(Boolean, default=False, index=True)

    # Media file information
    media_file_size = Column(Integer, default=0)  # Size in bytes

    # Upload source tracking
    source_type = Column(String(20), default="youtube", index=True)  # "youtube" or "upload"
    original_filename = Column(String(500))  # Original filename for uploaded files

    # Audio language and quality preferences
    audio_language = Column(String(10), nullable=True)  # Actual downloaded language (ISO 639-1)
    audio_quality = Column(String(20), nullable=True)  # Actual downloaded quality tier
    requested_language = Column(String(10), nullable=True)  # What user originally requested
    requested_quality = Column(String(20), nullable=True)  # What user originally requested

    # Relationships
    channel = relationship("ChannelModel", back_populates="episodes")
    tags = relationship("TagModel", secondary="episode_tags", back_populates="episodes")
    events = relationship("EventModel", back_populates="episode", cascade="all, delete-orphan")
    
    # Composite unique constraint and performance indexes
    __table_args__ = (
        Index('idx_episode_channel_video', 'channel_id', 'video_id', unique=True),
        Index('idx_episode_publication_date', 'publication_date'),
        Index('idx_episode_status', 'status'),
        Index('idx_episode_channel_status', 'channel_id', 'status'),
        Index('idx_episode_created_at', 'created_at'),
        Index('idx_episode_download_date', 'download_date'),
        Index('idx_episode_youtube_channel_id', 'youtube_channel_id'),
        Index('idx_episode_is_favorited', 'is_favorited'),
        Index('idx_episode_favorited_channel', 'channel_id', 'is_favorited'),
        Index('idx_episode_source_type', 'source_type'),
    )
    
    def __repr__(self):
        return f"<EpisodeModel(id={self.id}, title='{self.title[:50]}...', channel_id={self.channel_id}, status='{self.status}')>"