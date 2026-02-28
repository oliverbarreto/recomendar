"""
Celery Task Status Application Service

Application service for managing and querying Celery task status.
"""
from typing import Optional, List, Dict, Any
import logging

from app.domain.entities.celery_task_status import CeleryTaskStatus, TaskStatus
from app.infrastructure.repositories.celery_task_status_repository_impl import CeleryTaskStatusRepository
from app.infrastructure.celery_app import celery_app

logger = logging.getLogger(__name__)


class CeleryTaskStatusService:
    """
    Application service for Celery task status management
    
    Handles business logic for tracking and querying task execution status.
    """
    
    def __init__(self, task_status_repository: CeleryTaskStatusRepository):
        """
        Initialize the Celery task status service
        
        Args:
            task_status_repository: Repository for task status
        """
        self.task_status_repository = task_status_repository
    
    async def get_task_status(self, task_id: str) -> Optional[CeleryTaskStatus]:
        """
        Get task status by Celery task ID
        
        Args:
            task_id: Celery task UUID
        
        Returns:
            CeleryTaskStatus entity if found, None otherwise
        """
        try:
            return await self.task_status_repository.get_by_task_id(task_id)
        except Exception as e:
            logger.error(f"Failed to get task status for {task_id}: {e}")
            raise
    
    async def get_channel_task_status(
        self,
        followed_channel_id: int,
        limit: int = 10
    ) -> List[CeleryTaskStatus]:
        """
        Get task statuses for a followed channel
        
        Args:
            followed_channel_id: ID of the followed channel
            limit: Maximum number of statuses to return
        
        Returns:
            List of CeleryTaskStatus entities (most recent first)
        """
        try:
            return await self.task_status_repository.get_by_followed_channel_id(
                followed_channel_id=followed_channel_id,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Failed to get task statuses for channel {followed_channel_id}: {e}")
            raise
    
    async def get_latest_channel_task_status(
        self,
        followed_channel_id: int
    ) -> Optional[CeleryTaskStatus]:
        """
        Get the most recent task status for a followed channel

        Args:
            followed_channel_id: ID of the followed channel

        Returns:
            Most recent CeleryTaskStatus entity if found, None otherwise
        """
        try:
            return await self.task_status_repository.get_latest_by_followed_channel_id(
                followed_channel_id=followed_channel_id
            )
        except Exception as e:
            logger.error(f"Failed to get latest task status for channel {followed_channel_id}: {e}")
            raise

    async def get_all_tasks_summary(self) -> Dict[str, Any]:
        """
        Get summary of all tasks grouped by status

        Returns:
            Dictionary with total count and breakdown by status
        """
        try:
            return await self.task_status_repository.get_summary()
        except Exception as e:
            logger.error(f"Failed to get tasks summary: {e}")
            raise

    async def revoke_task(self, task_id: str, terminate: bool = False) -> bool:
        """
        Revoke a running or pending Celery task

        Args:
            task_id: Celery task UUID
            terminate: If True, terminate task even if it's running (use with caution)

        Returns:
            True if task was revoked successfully
        """
        try:
            # Revoke the task in Celery
            celery_app.control.revoke(task_id, terminate=terminate, signal='SIGTERM')

            # Update task status in database
            task_status = await self.task_status_repository.get_by_task_id(task_id)
            if task_status:
                task_status.status = TaskStatus.FAILURE
                task_status.error_message = "Task manually cancelled by user"
                await self.task_status_repository.update(task_status)

            logger.info(f"Revoked task {task_id} (terminate={terminate})")
            return True
        except Exception as e:
            logger.error(f"Failed to revoke task {task_id}: {e}")
            raise

    async def purge_tasks_by_status(
        self,
        status: TaskStatus,
        older_than_minutes: Optional[int] = None
    ) -> Dict[str, int]:
        """
        Purge tasks with specific status from database

        Args:
            status: Task status to purge (PENDING, FAILURE, SUCCESS)
            older_than_minutes: Only purge tasks older than this many minutes (optional)

        Returns:
            Dictionary with counts of revoked and deleted tasks
        """
        try:
            # Get tasks to purge
            if older_than_minutes:
                tasks = await self.task_status_repository.get_by_status_and_age(
                    status=status,
                    older_than_minutes=older_than_minutes
                )
            else:
                tasks = await self.task_status_repository.get_by_status(status=status)

            # Revoke any PENDING tasks in Celery
            revoked_count = 0
            if status == TaskStatus.PENDING:
                for task in tasks:
                    try:
                        celery_app.control.revoke(task.task_id, terminate=False)
                        revoked_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to revoke task {task.task_id}: {e}")

            # Delete from database
            deleted_count = await self.task_status_repository.delete_by_status(status)

            logger.info(f"Purged {deleted_count} tasks with status {status} (revoked: {revoked_count})")
            return {
                'revoked': revoked_count,
                'deleted': deleted_count
            }
        except Exception as e:
            logger.error(f"Failed to purge tasks by status {status}: {e}")
            raise

