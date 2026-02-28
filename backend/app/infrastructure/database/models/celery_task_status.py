"""
Celery Task Status SQLAlchemy model

Tracks the execution status of Celery background tasks for UI feedback.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from datetime import datetime
from app.infrastructure.database.connection import Base


class CeleryTaskStatusModel(Base):
    """
    SQLAlchemy model for tracking Celery task execution status
    
    Stores task metadata, progress, and results for displaying
    real-time feedback to users in the UI.
    """
    __tablename__ = "celery_task_status"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(255), unique=True, nullable=False, index=True)  # Celery task UUID
    task_name = Column(String(255), nullable=False, index=True)  # e.g., "check_followed_channel_for_new_videos"
    
    # Task execution state
    status = Column(String(50), nullable=False, index=True)  # PENDING, STARTED, PROGRESS, SUCCESS, FAILURE, RETRY
    progress = Column(Integer, default=0)  # Progress percentage (0-100)
    current_step = Column(String(255))  # Human-readable current step (e.g., "Discovering videos...")
    
    # Results and errors
    result_json = Column(Text)  # JSON-encoded task result
    error_message = Column(Text)  # Error message if task failed
    
    # Related entity IDs (for linking back to the entity that triggered the task)
    followed_channel_id = Column(Integer, index=True)  # For channel check/backfill tasks
    youtube_video_id = Column(Integer, index=True)  # For episode creation tasks
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Indexes for common queries
    __table_args__ = (
        Index('idx_celery_task_status_task_id', 'task_id'),
        Index('idx_celery_task_status_status', 'status'),
        Index('idx_celery_task_status_followed_channel', 'followed_channel_id'),
        Index('idx_celery_task_status_youtube_video', 'youtube_video_id'),
        Index('idx_celery_task_status_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<CeleryTaskStatusModel(id={self.id}, task_id='{self.task_id}', status='{self.status}')>"





