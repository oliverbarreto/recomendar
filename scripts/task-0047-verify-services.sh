#!/bin/bash
# Verification script for Follow Channel feature services

echo "🤖 Verifying LabCastARR Services..."
echo "=================================="
echo ""

# Check if all services are running
echo "1️⃣ Checking service status..."
docker compose --env-file .env.production -f docker-compose.prod.yml ps
echo ""

# Check Redis
echo "2️⃣ Testing Redis connection..."
REDIS_PING=$(docker exec labcastarr-redis-1 redis-cli ping 2>/dev/null)
if [ "$REDIS_PING" = "PONG" ]; then
    echo "✅ Redis is running and responding"
else
    echo "❌ Redis is not responding"
fi
echo ""

# Check Celery worker
echo "3️⃣ Checking Celery worker..."
CELERY_STATUS=$(docker compose --env-file .env.production -f docker-compose.prod.yml ps celery-worker | grep "Up")
if [ -n "$CELERY_STATUS" ]; then
    echo "✅ Celery worker is running"
    echo "   Last 5 log lines:"
    docker compose --env-file .env.production -f docker-compose.prod.yml logs --tail=5 celery-worker | grep -v "^$"
else
    echo "❌ Celery worker is not running"
fi
echo ""

# Check Celery beat
echo "4️⃣ Checking Celery beat..."
BEAT_STATUS=$(docker compose --env-file .env.production -f docker-compose.prod.yml ps celery-beat | grep "Up")
if [ -n "$BEAT_STATUS" ]; then
    echo "✅ Celery beat is running"
else
    echo "❌ Celery beat is not running"
fi
echo ""

# Check backend
echo "5️⃣ Checking backend API..."
BACKEND_STATUS=$(docker compose --env-file .env.production -f docker-compose.prod.yml ps backend | grep "Up")
if [ -n "$BACKEND_STATUS" ]; then
    echo "✅ Backend is running"
    # Try to hit health endpoint
    HEALTH_CHECK=$(curl -s http://localhost:8000/health 2>/dev/null | grep -o "healthy" || echo "")
    if [ -n "$HEALTH_CHECK" ]; then
        echo "✅ Backend health check passed"
    else
        echo "⚠️  Backend health check failed (might still be starting)"
    fi
else
    echo "❌ Backend is not running"
fi
echo ""

# Check frontend
echo "6️⃣ Checking frontend..."
FRONTEND_STATUS=$(docker compose --env-file .env.production -f docker-compose.prod.yml ps frontend | grep "Up")
if [ -n "$FRONTEND_STATUS" ]; then
    echo "✅ Frontend is running"
else
    echo "❌ Frontend is not running"
fi
echo ""

# Test Celery task
echo "7️⃣ Testing Celery task execution..."
TEST_RESULT=$(docker exec labcastarr-celery-worker-1 uv run python -c "
from app.infrastructure.tasks.channel_check_tasks import test_task
try:
    result = test_task.delay('Verification test')
    print(f'✅ Task queued successfully (ID: {result.id})')
except Exception as e:
    print(f'❌ Task failed: {e}')
" 2>&1)
echo "$TEST_RESULT"
echo ""

# Summary
echo "=================================="
echo "📊 Summary"
echo "=================================="
echo ""
echo "Services that should be running:"
echo "  - Redis (message broker)"
echo "  - Backend (FastAPI)"
echo "  - Celery Worker (task processor)"
echo "  - Celery Beat (scheduler)"
echo "  - Frontend (Next.js)"
echo ""
echo "Access URLs:"
echo "  - Frontend: http://localhost:3000"
echo "  - Backend API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo ""
echo "Next steps:"
echo "  1. Go to http://localhost:3000/subscriptions"
echo "  2. Follow a YouTube channel"
echo "  3. Try 'Check for New Videos' from context menu"
echo "  4. Videos should appear in 'Videos' tab"
echo ""
echo "If any service is not running, check logs:"
echo "  docker compose --env-file .env.production -f docker-compose.prod.yml logs [service-name]"
echo ""



