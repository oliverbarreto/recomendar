# Testing Celery with Docker

This guide will help you test that Celery is properly configured and working with Docker.

## Prerequisites

1. Docker Desktop is running
2. Docker Compose is installed
3. Environment file `.env.development` exists (or create one based on `.env.example`)

## Quick Test Script

Run the automated test script:

```bash
./scripts/test_celery_docker.sh
```

This script will:
1. Start Redis service
2. Start Celery worker
3. Test Celery connection
4. Send a test task and wait for result

## Manual Testing

### Step 1: Start Services

Start Redis and Celery worker:

```bash
docker compose --env-file .env.development -f docker-compose.dev.yml up -d redis celery-worker-dev
```

Wait a few seconds for services to start, then check logs:

```bash
docker compose --env-file .env.development -f docker-compose.dev.yml logs celery-worker-dev
```

You should see Celery worker starting up.

### Step 2: Test Celery Connection

Test that the worker is responding:

```bash
docker compose --env-file .env.development -f docker-compose.dev.yml exec celery-worker-dev \
    uv run celery -A app.infrastructure.celery_app inspect ping
```

Expected output:
```
-> celery@<hostname>: OK
```

### Step 3: Send Test Task

Run the test script inside the backend container:

```bash
docker compose --env-file .env.development -f docker-compose.dev.yml exec backend-dev \
    uv run python test_celery.py
```

Or manually test with Python:

```bash
docker compose --env-file .env.development -f docker-compose.dev.yml exec backend-dev \
    uv run python -c "
from app.infrastructure.tasks.channel_check_tasks import test_task
result = test_task.delay('Hello from Docker!')
print(f'Task ID: {result.id}')
print(f'Result: {result.get(timeout=10)}')
"
```

Expected output:
```
🤖 Sending test task to Celery...
✅ Task sent! Task ID: <uuid>
⏳ Waiting for result (max 10 seconds)...
✅ Task completed! Result: {'status': 'success', 'message': 'Hello from Docker!', 'task_id': '<uuid>'}
```

### Step 4: Check Worker Logs

Check that the task was processed:

```bash
docker compose --env-file .env.development -f docker-compose.dev.yml logs celery-worker-dev | tail -20
```

You should see log entries showing the task was received and processed.

## Troubleshooting

### Redis Connection Error

If you see connection errors:
1. Verify Redis is running: `docker compose --env-file .env.development -f docker-compose.dev.yml ps redis`
2. Check Redis logs: `docker compose --env-file .env.development -f docker-compose.dev.yml logs redis`
3. Verify `REDIS_URL` environment variable is set correctly

### Celery Worker Not Starting

1. Check worker logs: `docker compose --env-file .env.development -f docker-compose.dev.yml logs celery-worker-dev`
2. Verify all dependencies are installed (celery, redis packages)
3. Check that the celery_app.py file can be imported

### Task Not Processing

1. Verify worker is running: Check logs for "ready" message
2. Check Redis connection: Worker should connect to Redis on startup
3. Verify task is registered: Check logs for task registration messages

## Cleanup

Stop the test services:

```bash
docker compose --env-file .env.development -f docker-compose.dev.yml stop redis celery-worker-dev
```

Remove services (optional):

```bash
docker compose --env-file .env.development -f docker-compose.dev.yml down redis celery-worker-dev
```







