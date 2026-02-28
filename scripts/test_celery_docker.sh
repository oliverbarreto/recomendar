#!/bin/bash
# Test script to verify Celery is working with Docker

set -e

echo "🤖 Testing Celery with Docker..."
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Start Redis
echo -e "${YELLOW}Step 1: Starting Redis...${NC}"
docker compose --env-file .env.development -f docker-compose.dev.yml up -d redis
sleep 5

# Step 2: Start Celery worker
echo -e "${YELLOW}Step 2: Starting Celery worker...${NC}"
docker compose --env-file .env.development -f docker-compose.dev.yml up -d celery-worker-dev
sleep 5

# Step 3: Test Celery connection
echo -e "${YELLOW}Step 3: Testing Celery connection...${NC}"
docker compose --env-file .env.development -f docker-compose.dev.yml exec -T celery-worker-dev \
    uv run celery -A app.infrastructure.celery_app inspect ping || {
    echo -e "${RED}❌ Celery worker is not responding${NC}"
    echo "Checking logs..."
    docker compose --env-file .env.development -f docker-compose.dev.yml logs celery-worker-dev
    exit 1
}

echo -e "${GREEN}✅ Celery worker is responding!${NC}"
echo ""

# Step 4: Send test task
echo -e "${YELLOW}Step 4: Sending test task...${NC}"
docker compose --env-file .env.development -f docker-compose.dev.yml exec -T backend-dev \
    uv run python -c "
from app.infrastructure.tasks.channel_check_tasks import test_task
result = test_task.delay('Hello from Docker!')
print(f'✅ Task sent! Task ID: {result.id}')
print('⏳ Waiting for result...')
task_result = result.get(timeout=10)
print(f'✅ Task completed! Result: {task_result}')
"

echo ""
echo -e "${GREEN}✅ All tests passed! Celery is working correctly.${NC}"
echo ""
echo "To stop the services, run:"
echo "  docker compose --env-file .env.development -f docker-compose.dev.yml stop redis celery-worker-dev"







