"""
Health check API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.dependencies import get_database_session
from app.core.config import settings
from typing import Dict, Any
from datetime import datetime

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint
    """
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/db")
async def database_health_check(db: Session = Depends(get_database_session)) -> Dict[str, Any]:
    """
    Database connectivity health check
    """
    try:
        # Test database connection
        result = db.execute(text("SELECT 1"))
        result.fetchone()
        
        return {
            "status": "healthy",
            "database": "connected",
            "database_url": settings.database_url.split("://")[0] + "://***",  # Hide credentials
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get("/detailed")
async def detailed_health_check(db: Session = Depends(get_database_session)) -> Dict[str, Any]:
    """
    Detailed health check with all system components
    """
    health_data = {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }
    
    # Check database
    try:
        db.execute(text("SELECT 1"))
        health_data["components"]["database"] = {
            "status": "healthy",
            "type": settings.database_url.split("://")[0]
        }
    except Exception as e:
        health_data["status"] = "degraded"
        health_data["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check file system paths
    import os
    try:
        media_exists = os.path.exists(settings.media_path) or settings.media_path == "./media"
        feeds_exists = os.path.exists(settings.feeds_path) or settings.feeds_path == "./feeds"
        
        health_data["components"]["filesystem"] = {
            "status": "healthy" if media_exists and feeds_exists else "degraded",
            "media_path": settings.media_path,
            "feeds_path": settings.feeds_path,
            "media_accessible": media_exists,
            "feeds_accessible": feeds_exists
        }
        
        if not (media_exists and feeds_exists):
            health_data["status"] = "degraded"
            
    except Exception as e:
        health_data["status"] = "degraded"
        health_data["components"]["filesystem"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    return health_data