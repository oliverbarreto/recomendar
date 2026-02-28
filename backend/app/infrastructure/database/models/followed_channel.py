"""
FollowedChannel SQLAlchemy model

Represents a YouTube channel that a user is following for new video discovery.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index, UniqueConstraint, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.infrastructure.database.connection import Base


class FollowedChannelModel(Base):
    """
    SQLAlchemy model for FollowedChannel entity
    
    Represents a YouTube channel that a user has subscribed to follow.
    The system will periodically check this channel for new videos.
    """
    __tablename__ = "followed_channels"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    youtube_channel_id = Column(String(255), nullable=False, index=True)  # YouTube channel ID (UCxxxxx or @handle)
    youtube_channel_name = Column(String(255), nullable=False)
    youtube_channel_url = Column(String(500), nullable=False)
    thumbnail_url = Column(String(500))
    youtube_channel_description = Column(Text, nullable=True)  # Channel description from YouTube

    # Auto-approve settings
    auto_approve = Column(Boolean, default=False, nullable=False)
    auto_approve_channel_id = Column(Integer, ForeignKey("channels.id"), nullable=True)  # Target podcast channel
    
    # Tracking
    last_checked = Column(DateTime, nullable=True)  # Timestamp of last check for new videos
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Task tracking for UI feedback
    last_check_task_id = Column(String(255), nullable=True, index=True)  # Celery task ID for last check operation
    last_backfill_task_id = Column(String(255), nullable=True, index=True)  # Celery task ID for last backfill operation
    
    # Relationships
    user = relationship("UserModel", back_populates="followed_channels")
    auto_approve_channel = relationship("ChannelModel", foreign_keys=[auto_approve_channel_id])
    youtube_videos = relationship("YouTubeVideoModel", back_populates="followed_channel", cascade="all, delete-orphan")

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('youtube_channel_id', 'user_id', name='uq_followed_channel_user'),
        Index('idx_followed_channel_user_id', 'user_id'),
        Index('idx_followed_channel_youtube_id', 'youtube_channel_id'),
        Index('idx_followed_channel_last_checked', 'last_checked'),
        Index('idx_followed_channel_last_check_task', 'last_check_task_id'),
        Index('idx_followed_channel_last_backfill_task', 'last_backfill_task_id'),
    )

    def __repr__(self):
        return f"<FollowedChannelModel(id={self.id}, youtube_channel_id='{self.youtube_channel_id}', user_id={self.user_id})>"







