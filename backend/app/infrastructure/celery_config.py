"""
Celery configuration constants and settings
"""
from datetime import timedelta

# Task routing configuration
task_routes = {
    "app.infrastructure.tasks.channel_check_tasks.*": {"queue": "channel_checks"},
    "app.infrastructure.tasks.backfill_channel_task.*": {"queue": "backfills"},
    "app.infrastructure.tasks.create_episode_from_video_task.*": {"queue": "episode_creation"},
}

# Task retry configuration
task_default_retry_delay = 60  # seconds
task_max_retries = 3

# Worker configuration
worker_pool = "prefork"
worker_concurrency = 4

# Result backend configuration
result_backend_transport_options = {
    "master_name": "mymaster",
    "visibility_timeout": 3600,
}

# Periodic task schedule intervals
CHECK_INTERVALS = {
    "daily": timedelta(days=1),
    "twice_weekly": timedelta(days=3.5),  # Approximately every 3.5 days
    "weekly": timedelta(days=7),
}

# Default check times (UTC)
DEFAULT_CHECK_TIMES = {
    "daily": {"hour": 2, "minute": 0},  # 2 AM UTC
    "twice_weekly": {"hour": 2, "minute": 0},  # 2 AM UTC
    "weekly": {"hour": 2, "minute": 0},  # 2 AM UTC on Monday
}







