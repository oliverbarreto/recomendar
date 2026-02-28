"""
Tag SQLAlchemy model with association table
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, Index, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.infrastructure.database.connection import Base


# Association table for many-to-many relationship between episodes and tags
episode_tags = Table(
    'episode_tags',
    Base.metadata,
    Column('episode_id', Integer, ForeignKey('episodes.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow),
    # Index for performance on association queries
    Index('idx_episode_tags_episode', 'episode_id'),
    Index('idx_episode_tags_tag', 'tag_id'),
    Index('idx_episode_tags_created', 'created_at'),
)


class TagModel(Base):
    """
    SQLAlchemy model for Tag entity
    """
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False)
    name = Column(String(100), nullable=False)
    color = Column(String(7), default="#3B82F6")  # Hex color
    usage_count = Column(Integer, default=0, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    is_system_tag = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    channel = relationship("ChannelModel", back_populates="tags")
    episodes = relationship("EpisodeModel", secondary=episode_tags, back_populates="tags")
    
    # Composite unique constraint and performance indexes
    __table_args__ = (
        Index('idx_tag_channel_name', 'channel_id', 'name', unique=True),
        Index('idx_tag_channel', 'channel_id'),
        Index('idx_tag_name', 'name'),
        Index('idx_tag_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<TagModel(id={self.id}, name='{self.name}', channel_id={self.channel_id}, color='{self.color}', usage_count={self.usage_count})>"