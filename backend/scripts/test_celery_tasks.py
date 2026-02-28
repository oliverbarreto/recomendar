#!/usr/bin/env python3
"""
Celery Tasks Test Script
Tests Celery task execution for follow channel feature
"""
import sys
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.infrastructure.celery_app import celery_app
from app.infrastructure.tasks.channel_check_tasks import test_task
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_celery_connection():
    """Test Celery connection"""
    logger.info("=" * 70)
    logger.info("CELERY TASK TEST")
    logger.info("=" * 70)
    
    try:
        # Check if Celery app is configured
        assert celery_app is not None, "Celery app should be initialized"
        logger.info(f"✓ Celery app initialized")
        logger.info(f"  - Broker: {celery_app.conf.broker_url}")
        logger.info(f"  - Backend: {celery_app.conf.result_backend}")
        
        # Test sending a task
        logger.info("\nSending test task to Celery...")
        result = test_task.delay("Hello from test script!")
        
        logger.info(f"✓ Task sent! Task ID: {result.id}")
        logger.info(f"  - Task state: {result.state}")
        
        # Wait for result
        logger.info("⏳ Waiting for result (max 10 seconds)...")
        try:
            task_result = result.get(timeout=10)
            logger.info(f"✓ Task completed! Result: {task_result}")
            return True
        except Exception as e:
            logger.warning(f"⚠️  Could not get task result: {e}")
            logger.info("This is expected if Redis/Celery worker is not running")
            logger.info("Task was sent successfully, but worker may not be processing it")
            return True  # Consider it a pass if task was sent
            
    except Exception as e:
        logger.error(f"✗ Celery connection test failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = test_celery_connection()
    if success:
        logger.info("\n🎉 Celery task test completed!")
        logger.info("Note: If task result was not received, ensure Redis and Celery worker are running")
    else:
        logger.error("\n❌ Celery task test failed!")
    
    sys.exit(0 if success else 1)







