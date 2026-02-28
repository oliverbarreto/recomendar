# Connection Refused Error - Fix and Diagnosis

🤖 **Issue:** `kombu.exceptions.OperationalError: [Errno 111] Connection refused`

---

## Problem

The error occurs when trying to trigger "Check for New Videos" or "Backfill Videos" because:

1. **Redis is not running** - Celery needs Redis as a message broker
2. **Celery worker is not running** - No worker to process the tasks
3. **Wrong exception type** - The code was catching `ConnectionError` but Kombu raises `OperationalError`

---

## Solution Applied

### 1. Updated Exception Handling

**Files Modified:**
- `backend/app/application/services/followed_channel_service.py`
- `backend/app/presentation/api/v1/followed_channels.py`

**Changes:**
- Added catch for `OperationalError` by checking exception message
- Return HTTP 503 with clear message: "Task queue is temporarily unavailable. Please ensure Redis and Celery worker are running."

---

## How to Verify Services Are Running

### Check All Services

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml ps
```

**Expected Output:**
```
NAME                          STATUS              PORTS
labcastarr-backend-1          Up (healthy)        0.0.0.0:8000->8000/tcp
labcastarr-celery-beat-1      Up                  
labcastarr-celery-worker-1    Up                  
labcastarr-frontend-1         Up                  0.0.0.0:3000->3000/tcp
labcastarr-redis-1            Up (healthy)        0.0.0.0:6379->6379/tcp
```

### Check Redis Specifically

```bash
# Test Redis connection
docker exec labcastarr-redis-1 redis-cli ping
```

**Expected Output:** `PONG`

### Check Celery Worker

```bash
# View Celery worker logs
docker compose --env-file .env.production -f docker-compose.prod.yml logs celery-worker
```

**Expected Output:** Should show worker started and connected to Redis

### Check Celery Beat

```bash
# View Celery beat logs
docker compose --env-file .env.production -f docker-compose.prod.yml logs celery-beat
```

**Expected Output:** Should show beat scheduler started

---

## Troubleshooting

### If Redis is Not Running

```bash
# Start Redis
docker compose --env-file .env.production -f docker-compose.prod.yml up redis -d

# Verify it's running
docker compose --env-file .env.production -f docker-compose.prod.yml ps redis
```

### If Celery Worker is Not Running

```bash
# Start Celery worker
docker compose --env-file .env.production -f docker-compose.prod.yml up celery-worker -d

# Verify it's running
docker compose --env-file .env.production -f docker-compose.prod.yml ps celery-worker

# Check logs for errors
docker compose --env-file .env.production -f docker-compose.prod.yml logs celery-worker
```

### If Celery Beat is Not Running

```bash
# Start Celery beat
docker compose --env-file .env.production -f docker-compose.prod.yml up celery-beat -d

# Verify it's running
docker compose --env-file .env.production -f docker-compose.prod.yml ps celery-beat
```

### Start All Services

```bash
# Start all services
docker compose --env-file .env.production -f docker-compose.prod.yml up -d

# Or rebuild and start
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d
```

---

## Test After Fix

### 1. Verify Services Are Running

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml ps
```

All services should show "Up" or "Up (healthy)"

### 2. Test Celery Connection

```bash
docker exec labcastarr-celery-worker-1 uv run python -c "
from app.infrastructure.tasks.channel_check_tasks import test_task
result = test_task.delay('Test from Docker!')
print(f'Task ID: {result.id}')
print(f'Task State: {result.state}')
"
```

**Expected Output:**
```
Task ID: <some-uuid>
Task State: PENDING
```

### 3. Test in UI

1. Navigate to `/subscriptions`
2. Follow a YouTube channel
3. Click context menu → "Check for New Videos"

**Expected Result:**
- ✅ Toast notification: "Check task queued successfully"
- ✅ No error in browser console
- ✅ After a few moments, videos appear in "Videos" tab

---

## Error Messages

### Before Fix
```
Failed to trigger check: [Errno 111] Connection refused
```

### After Fix (if Redis/Celery not running)
```
Task queue is temporarily unavailable. Please ensure Redis and Celery worker are running.
```

### After Fix (if Redis/Celery are running)
```
Check task queued successfully
```

---

## Common Issues

### Issue: Services keep restarting

**Check logs:**
```bash
docker compose --env-file .env.production -f docker-compose.prod.yml logs
```

**Common causes:**
- Redis connection string incorrect in `.env.production`
- Port conflicts (6379 already in use)
- Memory issues

### Issue: Celery worker can't connect to Redis

**Check Redis URL:**
```bash
# In .env.production, should have:
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

**Note:** Use `redis://redis:6379/0` (service name) not `redis://localhost:6379/0` in Docker

### Issue: Tasks queue but don't execute

**Check Celery worker logs:**
```bash
docker compose --env-file .env.production -f docker-compose.prod.yml logs -f celery-worker
```

**Look for:**
- Worker connected to broker
- Tasks registered
- No error messages

---

## Environment Variables

Ensure these are set in `.env.production`:

```env
# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

---

## Next Steps

1. **Verify all services are running** using the commands above
2. **Test the feature** in the UI
3. **Check logs** if any issues persist
4. **Report back** with results

---

**Status:** ✅ Code fix applied - waiting for services to be running for testing





