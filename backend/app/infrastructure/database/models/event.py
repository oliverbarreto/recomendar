"""
Event SQLAlchemy model - Phase 5 Enhanced Version
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.infrastructure.database.connection import Base


class EventModel(Base):
    """
    SQLAlchemy model for Event entity - Phase 5 Enhanced Version
    """
    __tablename__ = "events"
    
    # Core identifiers
    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("channels.id", ondelete="CASCADE"), nullable=False)
    episode_id = Column(Integer, ForeignKey("episodes.id", ondelete="CASCADE"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Event classification
    event_type = Column(String(50), nullable=False, index=True)  # user_action, system_event, etc.
    action = Column(String(100), nullable=False)  # download, upload, delete, etc.
    resource_type = Column(String(50), nullable=False)  # episode, channel, tag, system
    resource_id = Column(String(100), nullable=True)  # flexible identifier
    
    # Event content
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=False, default=dict)  # structured event data
    event_metadata = Column(JSON, nullable=False, default=dict)  # additional context
    
    # Event status and priority
    status = Column(String(20), nullable=False, default="started", index=True)
    severity = Column(String(20), nullable=False, default="info")  # debug, info, warning, error, critical
    
    # Performance tracking
    duration_ms = Column(Integer, nullable=True)  # for timed operations
    
    # Request context
    ip_address = Column(String(45), nullable=True)  # client IP address (IPv4/IPv6)
    user_agent = Column(Text, nullable=True)  # client user agent
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=True)
    
    # Relationships
    channel = relationship("ChannelModel", back_populates="events")
    episode = relationship("EpisodeModel", back_populates="events")
    user = relationship("UserModel", back_populates="events")
    
    # Performance indexes for Phase 5 queries
    __table_args__ = (
        Index('idx_event_channel_created', 'channel_id', 'created_at'),
        Index('idx_event_type_severity', 'event_type', 'severity', 'created_at'),
        Index('idx_event_status_created', 'status', 'created_at'),
        Index('idx_event_resource', 'resource_type', 'resource_id'),
        Index('idx_event_user_created', 'user_id', 'created_at'),
        Index('idx_event_severity_created', 'severity', 'created_at'),
        Index('idx_event_duration', 'duration_ms'),
        # Composite indexes for complex queries
        Index('idx_event_channel_type_status', 'channel_id', 'event_type', 'status'),
        Index('idx_event_cleanup', 'created_at', 'severity'),
        Index('idx_event_performance', 'event_type', 'duration_ms', 'created_at'),
    )
    
    def __repr__(self):
        return f"<EventModel(id={self.id}, event_type='{self.event_type}', status='{self.status}', channel_id={self.channel_id})>"