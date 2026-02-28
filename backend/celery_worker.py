#!/usr/bin/env python3
"""
Celery worker entry point

Run this script to start a Celery worker process.
Usage:
    uv run python celery_worker.py
    or
    celery -A app.infrastructure.celery_app worker --loglevel=info
"""
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from celery import Celery
from app.infrastructure.celery_app import celery_app

if __name__ == "__main__":
    celery_app.worker_main()


