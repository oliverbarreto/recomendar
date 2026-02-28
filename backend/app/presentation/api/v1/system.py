"""
System management API endpoints
"""
from fastapi import APIRouter, Depends
from typing import Dict, Any
import logging

from app.application.services.initialization_service import InitializationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/initialization-status")
async def get_initialization_status() -> Dict[str, Any]:
    """
    Get the current initialization status of the system
    """
    try:
        initialization_service = InitializationService()
        status = await initialization_service.get_initialization_status()

        return {
            "status": "success",
            "data": status
        }

    except Exception as e:
        logger.error(f"Error getting initialization status: {e}")
        return {
            "status": "error",
            "error": str(e),
            "data": None
        }


@router.post("/initialize")
async def force_initialization() -> Dict[str, Any]:
    """
    Force re-initialization of default data (for testing/debugging)

    Warning: This will create default user/channel if they don't exist.
    Only use on development/test environments.
    """
    try:
        initialization_service = InitializationService()
        result = await initialization_service.ensure_default_data()

        return {
            "status": "success",
            "data": result
        }

    except Exception as e:
        logger.error(f"Error during forced initialization: {e}")
        return {
            "status": "error",
            "error": str(e),
            "data": None
        }