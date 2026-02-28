"""
User SQLAlchemy model
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.infrastructure.database.connection import Base


class UserModel(Base):
    """
    SQLAlchemy model for User entity
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    channels = relationship("ChannelModel", back_populates="user", cascade="all, delete-orphan")
    events = relationship("EventModel", back_populates="user", cascade="all, delete-orphan")
    followed_channels = relationship("FollowedChannelModel", back_populates="user", cascade="all, delete-orphan")
    user_settings = relationship("UserSettingsModel", back_populates="user", uselist=False, cascade="all, delete-orphan")
    notifications = relationship("NotificationModel", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<UserModel(id={self.id}, email='{self.email}', name='{self.name}')>"