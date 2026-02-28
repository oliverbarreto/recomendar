#!/usr/bin/env python3
"""
Simple test script to verify Celery is working

This script sends a test task to Celery and waits for the result.
Usage:
    uv run python test_celery.py
"""
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.infrastructure.celery_app import celery_app
from app.infrastructure.tasks.channel_check_tasks import test_task

if __name__ == "__main__":
    print("🤖 Sending test task to Celery...")
    
    # Send task asynchronously
    result = test_task.delay("Hello World from Celery Test!")
    
    print(f"✅ Task sent! Task ID: {result.id}")
    print("⏳ Waiting for result (max 10 seconds)...")
    
    try:
        # Wait for result with timeout
        task_result = result.get(timeout=10)
        print(f"✅ Task completed! Result: {task_result}")
    except Exception as e:
        print(f"❌ Error getting task result: {e}")
        print(f"Task state: {result.state}")
        sys.exit(1)







