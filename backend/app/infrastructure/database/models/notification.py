"""
Notification SQLAlchemy model
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.infrastructure.database.connection import Base


class NotificationModel(Base):
    """
    SQLAlchemy model for Notification entity
    """
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    data_json = Column(JSON, nullable=True)
    read = Column(Boolean, default=False, nullable=False, index=True)
    executed_by = Column(String(20), nullable=False, server_default='user', index=True)  # 'user' or 'system'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("UserModel", back_populates="notifications")
    
    # Composite indexes for efficient queries
    __table_args__ = (
        Index('idx_notification_user_read_created', 'user_id', 'read', 'created_at'),
        Index('idx_notification_user_created', 'user_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<NotificationModel(id={self.id}, user_id={self.user_id}, type='{self.type}', read={self.read})>"



