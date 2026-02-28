"""
Celery Task Status API Request/Response Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class CeleryTaskStatusResponse(BaseModel):
    """Response schema for Celery task status"""
    id: int = Field(..., description="Database ID")
    task_id: str = Field(..., description="Celery task UUID")
    task_name: str = Field(..., description="Task name")
    status: str = Field(..., description="Task status (PENDING, STARTED, PROGRESS, SUCCESS, FAILURE, RETRY)")
    progress: int = Field(default=0, description="Progress percentage (0-100)")
    current_step: Optional[str] = Field(default=None, description="Current step description")
    result_json: Optional[str] = Field(default=None, description="JSON-encoded task result")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    followed_channel_id: Optional[int] = Field(default=None, description="Related followed channel ID")
    youtube_video_id: Optional[int] = Field(default=None, description="Related YouTube video ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    started_at: Optional[datetime] = Field(default=None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")
    
    class Config:
        from_attributes = True


class TasksSummaryResponse(BaseModel):
    """Response schema for tasks summary"""
    total: int = Field(..., description="Total number of tasks")
    by_status: Dict[str, int] = Field(..., description="Task counts grouped by status")


class PurgeTasksRequest(BaseModel):
    """Request schema for purging tasks"""
    status: str = Field(..., description="Task status to purge (PENDING, FAILURE, SUCCESS)")
    older_than_minutes: Optional[int] = Field(
        default=None,
        description="Only purge tasks older than this many minutes"
    )


class PurgeTasksResponse(BaseModel):
    """Response schema for purge operation"""
    revoked: int = Field(..., description="Number of tasks revoked in Celery")
    deleted: int = Field(..., description="Number of tasks deleted from database")

