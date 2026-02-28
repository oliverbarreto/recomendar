"""
Celery Task Status Domain Entity

Represents the execution status of a Celery background task.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class TaskStatus(Enum):
    """Task execution status enum"""
    PENDING = "PENDING"
    STARTED = "STARTED"
    PROGRESS = "PROGRESS"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"


@dataclass
class CeleryTaskStatus:
    """
    Domain entity for Celery task status tracking
    
    Attributes:
        id: Database ID
        task_id: Celery task UUID
        task_name: Name of the task (e.g., "check_followed_channel_for_new_videos")
        status: Current task status
        progress: Progress percentage (0-100)
        current_step: Human-readable current step description
        result_json: JSON-encoded task result
        error_message: Error message if task failed
        followed_channel_id: ID of followed channel (for channel tasks)
        youtube_video_id: ID of YouTube video (for episode creation tasks)
        created_at: Task creation timestamp
        updated_at: Last update timestamp
        started_at: Task start timestamp
        completed_at: Task completion timestamp
    """
    task_id: str
    task_name: str
    status: TaskStatus = TaskStatus.PENDING
    id: Optional[int] = None
    progress: int = 0
    current_step: Optional[str] = None
    result_json: Optional[str] = None
    error_message: Optional[str] = None
    followed_channel_id: Optional[int] = None
    youtube_video_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def update_progress(self, progress: int, current_step: Optional[str] = None):
        """Update task progress"""
        self.progress = min(100, max(0, progress))
        self.status = TaskStatus.PROGRESS
        if current_step:
            self.current_step = current_step
        self.updated_at = datetime.utcnow()
    
    def mark_started(self):
        """Mark task as started"""
        self.status = TaskStatus.STARTED
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def mark_success(self, result_json: Optional[str] = None):
        """Mark task as successful"""
        self.status = TaskStatus.SUCCESS
        self.progress = 100
        if result_json:
            self.result_json = result_json
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def mark_failure(self, error_message: str):
        """Mark task as failed"""
        self.status = TaskStatus.FAILURE
        self.error_message = error_message
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def mark_retry(self):
        """Mark task for retry"""
        self.status = TaskStatus.RETRY
        self.updated_at = datetime.utcnow()
    
    def is_running(self) -> bool:
        """Check if task is currently running"""
        return self.status in [TaskStatus.STARTED, TaskStatus.PROGRESS]
    
    def is_completed(self) -> bool:
        """Check if task is completed (success or failure)"""
        return self.status in [TaskStatus.SUCCESS, TaskStatus.FAILURE]

