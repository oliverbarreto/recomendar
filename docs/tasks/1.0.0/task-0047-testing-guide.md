# Follow Channel Feature - Testing Guide

🤖 Quick reference guide for testing the Follow Channel feature.

---

## Prerequisites

Ensure all Docker services are running:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d
```

Verify services are healthy:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml ps
```

Expected output:
- ✅ redis (healthy)
- ✅ backend (healthy)
- ✅ celery-worker (running)
- ✅ celery-beat (running)
- ✅ frontend (running)

---

## Test Scenarios

### 1. Follow a YouTube Channel

**Steps:**
1. Navigate to `/subscriptions` page
2. Click "Follow Channel" button
3. Enter a YouTube channel URL (e.g., `https://www.youtube.com/@channelname`)
4. Click "Follow"

**Expected Result:**
- ✅ Toast notification: "Channel followed successfully"
- ✅ Channel appears in "Followed Channels" tab
- ✅ Backfill task is automatically queued
- ✅ After a few moments, videos appear in "Videos" tab

---

### 2. Check for New Videos

**Steps:**
1. Go to "Followed Channels" tab
2. Click the three-dot menu on a channel card
3. Select "Check for New Videos"

**Expected Result:**
- ✅ Toast notification: "Check task queued successfully"
- ✅ After task completes, new videos appear in "Videos" tab
- ✅ "Last checked" timestamp updates

---

### 3. Backfill Historical Videos

**Steps:**
1. Go to "Followed Channels" tab
2. Click the three-dot menu on a channel card
3. Select "Backfill Videos"
4. Enter year (optional) and max videos (default: 20)
5. Click "Start Backfill"

**Expected Result:**
- ✅ Toast notification: "Backfill task queued successfully"
- ✅ Historical videos appear in "Videos" tab
- ✅ Videos are in "pending_review" state

---

### 4. Create Episode from Video

**Steps:**
1. Go to "Videos" tab
2. Find a video in "pending_review" or "reviewed" state
3. Click "Create Episode" button on video card
4. Select target podcast channel
5. Click "Create Episode"

**Expected Result:**
- ✅ Toast notification: "Episode creation queued"
- ✅ Video state changes to "downloading"
- ✅ After download completes, video state changes to "episode_created"
- ✅ Episode appears in the selected podcast channel

---

### 5. Test Auto-Approve

**Steps:**
1. Go to "Followed Channels" tab
2. Click the three-dot menu on a channel card
3. Select "Settings"
4. Enable "Auto-approve all episodes"
5. Select target podcast channel
6. Click "Save Settings"
7. Trigger "Check for New Videos"

**Expected Result:**
- ✅ Toast notification: "Channel settings updated successfully"
- ✅ Badge shows "Auto-approve enabled" on channel card
- ✅ New videos automatically create episodes (skip review)
- ✅ Videos go directly to "downloading" → "episode_created" state

---

### 6. Test Error Handling (Connection Errors)

**Steps:**
1. Stop Celery worker:
   ```bash
   docker stop labcastarr-celery-worker-1
   ```
2. Try to trigger "Check for New Videos"

**Expected Result:**
- ✅ Toast notification: "Task queue is temporarily unavailable..."
- ✅ No crash or unhandled error
- ✅ User can continue using the app

**Recovery:**
1. Restart Celery worker:
   ```bash
   docker start labcastarr-celery-worker-1
   ```
2. Tasks should automatically retry

---

### 7. Test Empty States

**Steps:**
1. Follow a channel that has no new videos
2. Navigate to "Videos" tab

**Expected Result:**
- ✅ Shows "No videos found. Try adjusting your filters."
- ✅ No error message
- ✅ No 404 error in browser console

---

### 8. Test Video State Transitions

**Steps:**
1. Find a video in "pending_review" state
2. Click "Mark as Reviewed"
3. Verify state changes to "reviewed"
4. Click "Discard"
5. Verify state changes to "discarded"

**Expected Result:**
- ✅ State transitions work correctly
- ✅ Toast notifications for each action
- ✅ Video list updates immediately

---

### 9. Test Notification Bell

**Steps:**
1. Have some videos in "pending_review" state
2. Check the notification bell in the header

**Expected Result:**
- ✅ Badge shows count of pending videos
- ✅ Clicking bell navigates to `/subscriptions?filter=pending`
- ✅ Count updates when videos are reviewed/discarded

---

### 10. Test Periodic Checks (Celery Beat)

**Steps:**
1. Wait for Celery Beat to run periodic check (configured schedule)
2. Check Celery Beat logs:
   ```bash
   docker compose --env-file .env.production -f docker-compose.prod.yml logs celery-beat
   ```

**Expected Result:**
- ✅ Logs show "Running periodic check for all channels"
- ✅ Check tasks are queued for all followed channels
- ✅ New videos are discovered automatically

---

## Monitoring Commands

### View Logs

```bash
# All services
docker compose --env-file .env.production -f docker-compose.prod.yml logs -f

# Celery worker only
docker compose --env-file .env.production -f docker-compose.prod.yml logs -f celery-worker

# Celery beat only
docker compose --env-file .env.production -f docker-compose.prod.yml logs -f celery-beat

# Backend only
docker compose --env-file .env.production -f docker-compose.prod.yml logs -f backend
```

### Check Service Status

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml ps
```

### Test Celery Connection

```bash
docker exec labcastarr-celery-worker-1 uv run python -c "
from app.infrastructure.tasks.channel_check_tasks import test_task
result = test_task.delay('Test from Docker!')
print(f'Task ID: {result.id}')
print(f'Task State: {result.state}')
"
```

### Check Redis

```bash
docker exec labcastarr-redis-1 redis-cli ping
# Expected output: PONG
```

---

## Common Issues

### Issue: "Connection refused" errors

**Cause:** Celery worker or Redis is not running

**Solution:**
```bash
# Check if services are running
docker compose --env-file .env.production -f docker-compose.prod.yml ps

# Restart services if needed
docker compose --env-file .env.production -f docker-compose.prod.yml restart celery-worker redis
```

---

### Issue: Videos not appearing after check

**Cause:** Task may have failed or channel has no new videos

**Solution:**
1. Check Celery worker logs for errors
2. Verify channel URL is correct
3. Check if channel actually has new videos

---

### Issue: "Not Found" error on Videos tab

**Cause:** This should be fixed now, but if it persists:

**Solution:**
1. Check browser console for actual error
2. Verify backend is running and accessible
3. Check backend logs for errors

---

## Success Indicators

After testing, you should see:

- ✅ Channels can be followed without errors
- ✅ Videos are discovered and displayed
- ✅ Episodes can be created from videos
- ✅ Auto-approve works correctly
- ✅ Error messages are clear and helpful
- ✅ Empty states are handled gracefully
- ✅ Celery tasks retry on failure
- ✅ Periodic checks run automatically

---

## Reporting Issues

If you encounter any issues, please provide:

1. **Error message** (from toast notification or console)
2. **Steps to reproduce**
3. **Expected behavior**
4. **Actual behavior**
5. **Logs** (backend, celery-worker, celery-beat)
6. **Browser console errors** (if applicable)

---

**Happy Testing! 🎉**





