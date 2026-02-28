"""
Celery Beat schedule configuration for periodic tasks

This file defines the periodic schedule for checking followed channels.
The schedule is dynamically updated based on user preferences in the database.
"""
from celery.schedules import crontab

# Base beat schedule
# This will be dynamically updated based on user settings
# For now, we define a default daily check schedule
beat_schedule = {
    # Scheduled RSS channel check task (system-triggered)
    # This task runs every 30 minutes and checks if current time matches any user's
    # preferred check time in their timezone. It queries the database for all users
    # and their timezone/frequency preferences, then queues RSS check tasks for channels
    # that need checking based on user settings (daily/weekly) and time matching.
    # Uses RSS method (fast, 5-10s per channel) instead of yt-dlp (30-60s).
    "scheduled-channel-check-rss": {
        "task": "app.infrastructure.tasks.channel_check_tasks.scheduled_check_all_channels_rss",
        "schedule": crontab(minute='*/30'),  # Every 30 minutes (supports per-user timezone preferences)
        "options": {"queue": "channel_checks"},
    },

    # Legacy yt-dlp-based periodic check (DEPRECATED - commented out)
    # The new RSS-based task above is faster and more efficient.
    # Keeping this for reference only.
    # "periodic-channel-check": {
    #     "task": "app.infrastructure.tasks.channel_check_tasks.periodic_check_all_channels",
    #     "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM UTC
    #     "options": {"queue": "channel_checks"},
    # },
}

# Note: In a production system, you might want to make this more dynamic
# by reading from the database and updating the schedule at runtime.
# For now, we'll use a single daily task that queries user preferences
# and queues appropriate tasks based on their settings.







