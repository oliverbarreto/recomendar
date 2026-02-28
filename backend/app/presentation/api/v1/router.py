"""
Main API v1 router that combines all endpoint routers
"""
from fastapi import APIRouter

from .episodes import router as episodes_router
from .media import router as media_router
from .feeds import router as feeds_router
from .channels import router as channels_router
from .search import router as search_router
from .tags import router as tags_router
from .system import router as system_router
from .auth import router as auth_router
from .users import router as users_router
from .shortcuts import router as shortcuts_router
from .followed_channels import router as followed_channels_router
from .youtube_videos import router as youtube_videos_router
from .celery_tasks import router as celery_tasks_router
from .notifications import router as notifications_router

# Create main v1 router
v1_router = APIRouter(prefix="/v1")

# Include all sub-routers
v1_router.include_router(auth_router)
v1_router.include_router(users_router)
v1_router.include_router(episodes_router)
v1_router.include_router(media_router)
v1_router.include_router(feeds_router)
v1_router.include_router(channels_router)
v1_router.include_router(search_router)
v1_router.include_router(tags_router)
v1_router.include_router(system_router)
v1_router.include_router(shortcuts_router)  # iOS Shortcuts integration
v1_router.include_router(followed_channels_router)  # Follow channel feature
v1_router.include_router(youtube_videos_router)  # YouTube videos feature
v1_router.include_router(celery_tasks_router)  # Celery task status tracking
v1_router.include_router(notifications_router)  # Notifications feature

# Health check endpoint
@v1_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "api_version": "v1"
    }