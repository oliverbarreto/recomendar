#!/usr/bin/env python3
"""
Celery Beat scheduler entry point

Run this script to start the Celery Beat scheduler for periodic tasks.
Usage:
    uv run python celery_beat.py
    or
    celery -A app.infrastructure.celery_app beat --loglevel=info
"""
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.infrastructure.celery_app import celery_app

if __name__ == "__main__":
    celery_app.start(["celery", "beat"])


