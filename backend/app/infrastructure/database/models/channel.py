"""
Channel SQLAlchemy model
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.infrastructure.database.connection import Base


class ChannelModel(Base):
    """
    SQLAlchemy model for Channel entity
    """
    __tablename__ = "channels"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    website_url = Column(String(500), nullable=False)
    image_url = Column(String(500))
    category = Column(String(100), default="Technology")
    language = Column(String(10), default="en")
    explicit_content = Column(Boolean, default=True)
    author_name = Column(String(255))
    author_email = Column(String(255))
    owner_name = Column(String(255))
    owner_email = Column(String(255))
    feed_url = Column(String(500))
    feed_last_updated = Column(DateTime)
    feed_validation_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("UserModel", back_populates="channels")
    episodes = relationship("EpisodeModel", back_populates="channel", cascade="all, delete-orphan")
    tags = relationship("TagModel", back_populates="channel", cascade="all, delete-orphan")
    events = relationship("EventModel", back_populates="channel", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ChannelModel(id={self.id}, name='{self.name}', user_id={self.user_id})>"