"""
Celery application configuration and initialization
"""
import os
from celery import Celery
from app.core.config import settings

# Get broker and result backend URLs
# Support REDIS_URL environment variable (used in Docker) or fallback to config
redis_url = os.getenv("REDIS_URL") or settings.redis_url
broker_url = settings.celery_broker_url or redis_url
result_backend = settings.celery_result_backend or redis_url

# Create Celery app instance
celery_app = Celery(
    "labcastarr",
    broker=broker_url,
    backend=result_backend,
    include=[
        "app.infrastructure.tasks.channel_check_tasks",
        "app.infrastructure.tasks.channel_check_rss_tasks",
        "app.infrastructure.tasks.backfill_channel_task",
        "app.infrastructure.tasks.create_episode_from_video_task",
        "app.infrastructure.tasks.download_episode_task",
    ],
)

# Configure Celery settings
celery_app.conf.update(
    task_serializer=settings.celery_task_serializer,
    result_serializer=settings.celery_result_serializer,
    accept_content=settings.celery_accept_content,
    timezone=settings.celery_timezone,
    enable_utc=settings.celery_enable_utc,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    result_expires=3600,  # 1 hour
)

# Import beat schedule configuration
from app.infrastructure.celery_beat_schedule import beat_schedule

celery_app.conf.beat_schedule = beat_schedule

# Explicitly import task modules to ensure they're registered
# This ensures tasks are discovered even if include list has issues
import app.infrastructure.tasks.channel_check_tasks  # noqa: F401
import app.infrastructure.tasks.channel_check_rss_tasks  # noqa: F401
import app.infrastructure.tasks.backfill_channel_task  # noqa: F401
import app.infrastructure.tasks.create_episode_from_video_task  # noqa: F401
import app.infrastructure.tasks.download_episode_task  # noqa: F401

