"""
Celery Tasks API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, List
import logging

from app.infrastructure.database.connection import get_async_db
from app.core.auth import get_current_user_jwt
from app.application.services.celery_task_status_service import CeleryTaskStatusService
from app.infrastructure.repositories.celery_task_status_repository_impl import CeleryTaskStatusRepository
from app.presentation.schemas.celery_task_status_schemas import (
    CeleryTaskStatusResponse,
    TasksSummaryResponse,
    PurgeTasksRequest,
    PurgeTasksResponse
)
from app.domain.entities.celery_task_status import TaskStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/celery-tasks", tags=["celery-tasks"])


def get_task_status_service(
    session: AsyncSession = Depends(get_async_db)
) -> CeleryTaskStatusService:
    """Dependency to get task status service"""
    repository = CeleryTaskStatusRepository(session)
    return CeleryTaskStatusService(repository)


@router.get(
    "/summary",
    response_model=TasksSummaryResponse,
    responses={
        401: {"description": "Authentication required"},
    }
)
async def get_tasks_summary(
    current_user: Annotated[dict, Depends(get_current_user_jwt)],
    task_status_service: CeleryTaskStatusService = Depends(get_task_status_service),
) -> TasksSummaryResponse:
    """
    Get summary of all tasks grouped by status

    Returns total count and breakdown by status (PENDING, STARTED, SUCCESS, FAILURE, etc.)
    """
    try:
        summary = await task_status_service.get_all_tasks_summary()
        return TasksSummaryResponse(**summary)

    except Exception as e:
        logger.error(f"Failed to get tasks summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tasks summary: {str(e)}"
        )


@router.get(
    "/{task_id}",
    response_model=CeleryTaskStatusResponse,
    responses={
        401: {"description": "Authentication required"},
        404: {"description": "Task not found"},
    }
)
async def get_task_status(
    task_id: str,
    current_user: Annotated[dict, Depends(get_current_user_jwt)],
    task_status_service: CeleryTaskStatusService = Depends(get_task_status_service),
) -> CeleryTaskStatusResponse:
    """
    Get Celery task status by task ID

    Returns the current status, progress, and result of a Celery task.
    """
    try:
        task_status = await task_status_service.get_task_status(task_id)

        if not task_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )

        return CeleryTaskStatusResponse.model_validate(task_status)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}"
        )


@router.post(
    "/revoke/{task_id}",
    responses={
        401: {"description": "Authentication required"},
        404: {"description": "Task not found"},
    }
)
async def revoke_task(
    task_id: str,
    current_user: Annotated[dict, Depends(get_current_user_jwt)],
    task_status_service: CeleryTaskStatusService = Depends(get_task_status_service),
) -> dict:
    """
    Revoke a running or pending Celery task

    Cancels the task execution and updates status to FAILURE.
    Note: Only works for PENDING tasks. Running tasks may not stop immediately.
    """
    try:
        success = await task_status_service.revoke_task(task_id, terminate=False)

        return {
            "success": success,
            "message": f"Task {task_id} has been revoked"
        }

    except Exception as e:
        logger.error(f"Failed to revoke task: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke task: {str(e)}"
        )


@router.post(
    "/purge",
    response_model=PurgeTasksResponse,
    responses={
        401: {"description": "Authentication required"},
        400: {"description": "Invalid status value"},
    }
)
async def purge_tasks(
    request: PurgeTasksRequest,
    current_user: Annotated[dict, Depends(get_current_user_jwt)],
    task_status_service: CeleryTaskStatusService = Depends(get_task_status_service),
) -> PurgeTasksResponse:
    """
    Purge tasks with specific status from database

    Args:
        status: Task status to purge (PENDING, FAILURE, SUCCESS)
        older_than_minutes: Only purge tasks older than this many minutes (optional)

    Returns:
        Count of revoked and deleted tasks
    """
    try:
        # Validate status
        try:
            task_status = TaskStatus(request.status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {request.status}. Must be one of: PENDING, STARTED, PROGRESS, SUCCESS, FAILURE, RETRY"
            )

        result = await task_status_service.purge_tasks_by_status(
            status=task_status,
            older_than_minutes=request.older_than_minutes
        )

        return PurgeTasksResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to purge tasks: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to purge tasks: {str(e)}"
        )

