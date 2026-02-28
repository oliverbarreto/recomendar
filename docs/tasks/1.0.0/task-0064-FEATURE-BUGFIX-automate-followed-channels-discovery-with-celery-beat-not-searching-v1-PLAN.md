# Implementation Plan: Fix Celery Beat Auto-Discovery for Followed Channels

## Problem Summary

The auto-discovery scheduled task for followed YouTube channels is not executing at the user-configured time (10:45 Atlantic/Canary). Investigation revealed **two critical issues**:

1. **Fixed Beat Schedule** - Hardcoded to 2:00 AM UTC, ignoring user timezone preferences
2. **Missing Timezone Logic** - Task implementation doesn't use timezone fields even though they exist in the database

## Database Status: ✅ VERIFIED CORRECT

The database **DOES** have all required columns and data:

```sql
-- Actual schema (CONFIRMED):
CREATE TABLE user_settings (
    id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    subscription_check_frequency VARCHAR(12) NOT NULL,
    preferred_check_hour INTEGER DEFAULT '2' NOT NULL,
    preferred_check_minute INTEGER DEFAULT '0' NOT NULL,
    timezone VARCHAR(100) DEFAULT 'Europe/Madrid' NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    PRIMARY KEY (id)
);

-- Actual user data (CONFIRMED):
user_id=1, frequency=DAILY, timezone=Atlantic/Canary, hour=10, minute=45
```

**Database is NOT the issue** - schema is correct, migrations already applied, user settings are properly saved.

## Root Cause Analysis

### Issue #1: Fixed Beat Schedule (DESIGN FLAW)

- Current schedule: `crontab(hour=2, minute=0)` → Fixed at 2:00 AM UTC
- User configured: 10:45 Atlantic/Canary → Expects 10:45 UTC (Atlantic/Canary is UTC+0 in winter)
- Gap: 8 hours 45 minutes difference
- Task only runs once per day at wrong time, so no events appear at user's configured time

### Issue #2: Task Logic Ignores Timezone (IMPLEMENTATION GAP)

- Task reads `subscription_check_frequency` ("daily" or "weekly") ✅
- Task **DOES NOT** read `preferred_check_hour`, `preferred_check_minute`, or `timezone` ❌
- Task simply checks if `last_checked` timestamp is older than frequency threshold (24h or 7d) ❌
- No code exists to match current time against user's preferred check time in their timezone ❌

## Implementation Strategy

We'll use **Option B: Frequent Check with Timezone Logic** (simpler and more maintainable):

- Run Celery Beat task frequently (every 30 minutes)
- In each execution, check if current time matches ANY user's preferred check time in their timezone
- Only queue channel checks when time matches user preference
- Avoids complexity of dynamic beat schedule management

---

## Phase 1: Update Beat Schedule

**File:** `backend/app/infrastructure/celery_beat_schedule.py`

### Task 1.1: Change Schedule from Daily to Every 30 Minutes

**Current code (lines 12-22):**

```python
beat_schedule = {
    "scheduled-channel-check-rss": {
        "task": "app.infrastructure.tasks.channel_check_tasks.scheduled_check_all_channels_rss",
        "schedule": crontab(hour=2, minute=0),  # 2 AM UTC daily
        "options": {"queue": "channel_checks"},
    },
}
```

**New code:**

```python
beat_schedule = {
    "scheduled-channel-check-rss": {
        "task": "app.infrastructure.tasks.channel_check_tasks.scheduled_check_all_channels_rss",
        "schedule": crontab(minute='*/30'),  # Every 30 minutes
        "options": {"queue": "channel_checks"},
    },
}
```

**Rationale:**

- Running every 30 minutes allows the task to check if current time matches user preferences
- Provides maximum 30-minute delay from user's configured check time
- Simpler than managing dynamic per-user schedules
- Performance overhead is minimal (task filters users efficiently)

**Testing alternative:** For faster testing, use `crontab(minute='*')` (every minute)

---

## Phase 2: Implement Timezone-Aware Task Logic

**File:** `backend/app/infrastructure/tasks/channel_check_tasks.py`

### Task 2.1: Add Timezone Matching Logic

**Location:** Function `scheduled_check_all_channels_rss()` around lines 397-414

**Current logic (simplified):**

```python
for user in all_users:
    user_settings = await user_settings_repo.get_or_create_default(user.id)
    frequency = user_settings.subscription_check_frequency.value

    # Calculate threshold (24h for daily, 7d for weekly)
    now = datetime.utcnow()
    if frequency == "daily":
        threshold = now - timedelta(days=1)
    elif frequency == "weekly":
        threshold = now - timedelta(days=7)

    # Queue channels if last_checked < threshold
    for channel in user_channels:
        if channel.last_checked is None or channel.last_checked < threshold:
            queue_task()
```

**New logic (with timezone awareness):**

```python
from zoneinfo import ZoneInfo
from datetime import datetime, timezone, timedelta

for user in all_users:
    user_settings = await user_settings_repo.get_or_create_default(user.id)
    frequency = user_settings.subscription_check_frequency.value

    # Get user's timezone and preferred check time
    user_tz = ZoneInfo(user_settings.timezone)
    preferred_hour = user_settings.preferred_check_hour
    preferred_minute = user_settings.preferred_check_minute

    # Get current time in user's timezone
    now_utc = datetime.now(timezone.utc)
    now_user_tz = now_utc.astimezone(user_tz)

    # Check if current time matches user's preferred check time
    # Allow 30-minute window since task runs every 30 minutes
    current_hour = now_user_tz.hour
    current_minute = now_user_tz.minute

    time_matches = (
        current_hour == preferred_hour and
        abs(current_minute - preferred_minute) < 30
    )

    if not time_matches:
        # Not the right time for this user
        logger.debug(
            f"User {user.id} check time {preferred_hour:02d}:{preferred_minute:02d} "
            f"does not match current time {current_hour:02d}:{current_minute:02d} "
            f"in timezone {user_settings.timezone}"
        )
        continue  # Skip this user

    # Time matches! Now check frequency threshold
    if frequency == "daily":
        threshold = now_utc - timedelta(days=1)
    elif frequency == "weekly":
        threshold = now_utc - timedelta(days=7)
    else:
        threshold = now_utc - timedelta(days=1)

    # Queue channels if last_checked < threshold
    for channel in user_channels:
        if channel.last_checked is None or channel.last_checked < threshold:
            logger.info(
                f"Queueing channel {channel.id} ({channel.youtube_channel_name}) "
                f"for user {user.id} - scheduled check at "
                f"{preferred_hour:02d}:{preferred_minute:02d} {user_settings.timezone}"
            )
            check_followed_channel_for_new_videos_rss.apply_async(
                args=(channel.id,),
                kwargs={'executed_by': 'system'}
            )
        else:
            logger.debug(
                f"Channel {channel.id} already checked recently at {channel.last_checked}"
            )
```

### Task 2.2: Update Imports

Add timezone import at the top of the file:

```python
from zoneinfo import ZoneInfo
```

### Task 2.3: Add Error Handling for Invalid Timezones

Wrap timezone conversion in try-except:

```python
try:
    user_tz = ZoneInfo(user_settings.timezone)
except Exception as e:
    logger.warning(
        f"Invalid timezone '{user_settings.timezone}' for user {user.id}, "
        f"falling back to UTC: {str(e)}"
    )
    user_tz = ZoneInfo("UTC")
```

### Task 2.4: Update Task Logging

Add logging at the start of the task to show when it runs:

```python
@shared_task(name="scheduled_check_all_channels_rss")
def scheduled_check_all_channels_rss():
    """
    Scheduled task to check all followed channels for new videos using RSS method.
    Runs every 30 minutes and checks if current time matches any user's preferred check time.
    """
    logger.info("=" * 80)
    logger.info("Starting scheduled channel check (RSS method)")
    logger.info(f"Current UTC time: {datetime.now(timezone.utc)}")
    logger.info("=" * 80)

    # ... rest of task logic
```

---

## Phase 3: Testing & Validation

### Task 3.1: Rebuild and Restart Docker Containers

Apply all changes to the running system:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml down
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d
```

### Task 3.2: Verify Celery Beat Schedule

Check Celery Beat logs to confirm new schedule is loaded:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml logs celery-beat-prod -f
```

Expected log output:

```
[...] beat: Starting...
[...] Scheduler: Sending due task scheduled-channel-check-rss (...)
```

Task should appear every 30 minutes.

### Task 3.3: Monitor Task Execution

Check Celery Worker logs during execution:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml logs celery-worker-prod -f
```

Expected log output:

```
[...] Task app.infrastructure.tasks.channel_check_tasks.scheduled_check_all_channels_rss[...] received
[...] Starting scheduled channel check (RSS method)
[...] Current UTC time: 2025-12-02 10:45:00+00:00
[...] User 1 check time 10:45 matches current time 10:45 in timezone Atlantic/Canary
[...] Queueing channel 1 (SoloFonseca) for user 1 - scheduled check at 10:45 Atlantic/Canary
[...] Queueing channel 2 (t3dotgg) for user 1 - scheduled check at 10:45 Atlantic/Canary
[...] Task app.infrastructure.tasks.channel_check_rss_tasks.check_followed_channel_for_new_videos_rss[...] received
```

### Task 3.4: Verify Activity Page Shows Events

At the configured check time (10:45):

1. Open Activity page in UI
2. Should see new events:
   - "Channel search started" for each followed channel
   - "Channel search completed" with video count
3. Verify "Executed By" column shows "System" (not "User")
4. Verify timestamps match expected check time

### Task 3.5: Test Different Scenarios

**Scenario 1: Daily frequency**

- User has daily frequency, check time 10:45
- At 10:45: Channels should be checked
- At 10:45 next day: Channels should be checked again (>24h since last check)
- At 10:45 same day (2 hours later): Channels should NOT be checked (<24h since last check)

**Scenario 2: Weekly frequency**

- User has weekly frequency, check time 10:45
- At 10:45: Channels should be checked
- At 10:45 next day: Channels should NOT be checked (<7d since last check)
- At 10:45 after 7 days: Channels should be checked again (>7d since last check)

**Scenario 3: Multiple users with different timezones**

- User A: 10:45 Atlantic/Canary
- User B: 14:00 America/New_York
- At 10:45 UTC: Only User A's channels checked
- At 19:00 UTC (14:00 EST): Only User B's channels checked

### Task 3.6: Performance Testing

Monitor system performance with frequent task runs:

```bash
# Check CPU and memory usage
docker stats

# Monitor database query performance
docker compose --env-file .env.production -f docker-compose.prod.yml logs backend-prod | grep "SELECT"
```

Ensure:

- Task completes within 1-2 seconds when no time matches
- Task completes within 10-30 seconds when queuing channels
- No database locks or performance degradation

---

## Phase 4: Documentation Updates

### Task 4.1: Update CLAUDE.md

Add section explaining scheduled check behavior:

**Location:** After "Follow Channel and Discover Videos" section

```markdown
### Scheduled Automatic Video Discovery

The system automatically checks followed YouTube channels for new videos based on user preferences:

- **Check Frequency**: Daily or Weekly (configured in Settings)
- **Check Time**: Preferred hour and minute (configured in Settings)
- **Timezone**: User's timezone (e.g., Atlantic/Canary, America/New_York)

**How it works:**

1. Celery Beat task runs every 30 minutes
2. For each user, system calculates current time in their timezone
3. If current time matches user's preferred check time (±30 minute window):
   - System queues channel check tasks for that user's followed channels
   - Only checks channels that haven't been checked within frequency threshold
   - Creates notifications with `executed_by='system'`
4. Users see "System" in the "Executed By" column in Activity page

**Example:**

- User sets: "Daily at 10:45 Atlantic/Canary"
- System converts to UTC (same as Atlantic/Canary in winter)
- Every day between 10:30-10:59 UTC, task runs and checks if time matches
- At 10:45 UTC, channels are queued for checking
- Notifications appear in Activity page with "System" badge
```

### Task 4.2: Update Technical Analysis Document

**File:** `docs/documentation/TECHNICAL-ANALYSIS-FEATURE-follow-channels-architecture.md`

Add section on Scheduled Discovery Architecture:

````markdown
## Scheduled Discovery Architecture

### Beat Schedule Configuration

**File:** `backend/app/infrastructure/celery_beat_schedule.py`

The beat schedule runs every 30 minutes to support per-user timezone preferences:

```python
beat_schedule = {
    "scheduled-channel-check-rss": {
        "task": "app.infrastructure.tasks.channel_check_tasks.scheduled_check_all_channels_rss",
        "schedule": crontab(minute='*/30'),  # Every 30 minutes
        "options": {"queue": "channel_checks"},
    },
}
```
````

### Timezone-Aware Task Logic

The task implementation matches current time against each user's preferred check time:

1. Get all users from database
2. For each user:
   - Read timezone, preferred_check_hour, preferred_check_minute from user_settings
   - Calculate current time in user's timezone
   - Check if current hour/minute matches preferred check time (±30 minute window)
   - If match: Query followed channels and check frequency threshold
   - Queue check tasks with `executed_by='system'`
3. Skip users whose check time doesn't match current time

This allows multiple users with different timezones to have their channels checked at their preferred times.

````

### Task 4.3: Create Troubleshooting Guide

**New file:** `docs/documentation/TROUBLESHOOTING-SCHEDULED-DISCOVERY.md`

```markdown
# Troubleshooting Scheduled Video Discovery

## Common Issues

### Issue: No events appear at configured check time

**Symptoms:**
- User configured check time in Settings
- No notifications appear in Activity page at expected time
- No "System" events visible

**Diagnosis:**
1. Check Celery Beat logs:
   ```bash
   docker compose logs celery-beat-prod -f
````

Should show task running every 30 minutes

2. Check Celery Worker logs:

   ```bash
   docker compose logs celery-worker-prod -f
   ```

   Look for "Starting scheduled channel check" messages

3. Verify user settings in database:
   ```bash
   sqlite3 backend/data/labcastarr.db "SELECT * FROM user_settings WHERE user_id=1"
   ```
   Check: preferred_check_hour, preferred_check_minute, timezone

**Solutions:**

- Ensure database migrations applied: `cd backend && uv run alembic upgrade head`
- Verify timezone is valid (e.g., "Atlantic/Canary", not invalid strings)
- Check frequency setting (daily = 24h, weekly = 7d between checks)
- Verify channels have not been checked too recently

### Issue: Channels checked too frequently

**Symptoms:**

- Channels checked multiple times per day when "Daily" is selected
- Multiple "System" notifications appearing

**Diagnosis:**
Check `last_checked` timestamps in database:

```bash
sqlite3 backend/data/labcastarr.db "SELECT id, youtube_channel_name, last_checked FROM followed_channels"
```

**Solutions:**

- Ensure task logic includes frequency threshold check
- Verify `last_checked` is being updated after each check
- Check for multiple instances of Celery Beat running

### Issue: Wrong timezone

**Symptoms:**

- Checks happen at unexpected times
- Time offset from configured check time

**Diagnosis:**

1. Verify user timezone setting matches expected value
2. Check server time: `docker exec <container> date`
3. Verify timezone calculation in logs

**Solutions:**

- Use correct IANA timezone names (e.g., "America/New_York", not "EST")
- Ensure Python `zoneinfo` library is available
- Check daylight saving time transitions

````

---

## Phase 5: Rollback Plan

If issues occur after deployment, here's how to rollback:

### Task 5.1: Revert Beat Schedule

**File:** `backend/app/infrastructure/celery_beat_schedule.py`

Change back to original daily schedule:

```python
beat_schedule = {
    "scheduled-channel-check-rss": {
        "task": "app.infrastructure.tasks.channel_check_tasks.scheduled_check_all_channels_rss",
        "schedule": crontab(hour=2, minute=0),  # Back to 2 AM UTC daily
        "options": {"queue": "channel_checks"},
    },
}
````

### Task 5.2: Disable Timezone Logic

Comment out timezone matching logic, keep frequency-only behavior:

```python
# time_matches = (...)  # Comment out
time_matches = True  # Allow all users to be checked
```

### Task 5.3: Restart Services

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml restart celery-beat-prod celery-worker-prod
```

---

## Success Criteria

✅ Database schema verified (all columns exist - ALREADY COMPLETE)
✅ Celery Beat task runs every 30 minutes
✅ Task logs show timezone matching logic working
✅ Channels are queued for checking at user's configured time
✅ Notifications appear in Activity page with "System" badge
✅ "Executed By" column shows "System" for scheduled checks
✅ Frequency thresholds respected (daily = once per 24h, weekly = once per 7d)
✅ Multiple users with different timezones work correctly
✅ No performance degradation from frequent task runs

---

## Critical Files Modified

**Backend:**

1. `backend/app/infrastructure/celery_beat_schedule.py` - Beat schedule frequency
2. `backend/app/infrastructure/tasks/channel_check_tasks.py` - Timezone-aware logic
3. `backend/data/labcastarr.db` - Database schema (via migrations)

**Documentation:** 4. `CLAUDE.md` - Add scheduled discovery explanation 5. `docs/documentation/TECHNICAL-ANALYSIS-FEATURE-follow-channels-architecture.md` - Add architecture section 6. `docs/documentation/TROUBLESHOOTING-SCHEDULED-DISCOVERY.md` - New troubleshooting guide

**Migrations:**

- Already applied ✅ - All required columns exist in database

---

## Implementation Order

Execute phases sequentially:

1. **Phase 1** - Update beat schedule (quick change - 2 minutes)
2. **Phase 2** - Implement timezone logic (core functionality - 20-30 minutes)
3. **Phase 3** - Testing and validation (verify everything works - 30-60 minutes)
4. **Phase 4** - Documentation updates (capture knowledge - 15-20 minutes)
5. **Phase 5** - Rollback plan (safety net - N/A unless needed)

**Estimated Time:**

- Phase 1: 2 minutes
- Phase 2: 20-30 minutes
- Phase 3: 30-60 minutes (includes waiting for scheduled execution)
- Phase 4: 15-20 minutes
- Phase 5: N/A (only if needed)

**Total:** ~1-1.5 hours including testing

---

## Risk Assessment

**Low Risk:**

- Database schema (already correct - no changes needed) ✅
- Beat schedule change (simple cron expression change)
- Documentation updates (no code impact)

**Medium Risk:**

- Timezone logic implementation (new code, needs testing)
- Performance of running task every 30 minutes (should be negligible)

**High Risk:**

- None identified

**Mitigation:**

- Rollback plan documented and tested
- Can revert to original schedule quickly if needed
- Logs will show any errors immediately
- Testing phase validates all scenarios before production use

---

## Next Steps After Implementation

1. **Monitor First Week:**

   - Check logs daily for any errors
   - Verify notifications appear at expected times
   - Gather user feedback

2. **Performance Tuning:**

   - If task takes too long, consider caching user settings
   - Optimize database queries if needed
   - Add database indexes if queries are slow

3. **Future Enhancements:**
   - Add UI to show "Next scheduled check" time
   - Allow users to manually trigger checks without waiting for schedule
   - Support multiple check times per day
   - Add notification preferences (email, push)

---

## End of Plan

This plan addresses both root causes:

1. ✅ Beat schedule will run frequently enough to support user timezones
2. ✅ Task logic will match user's preferred check time in their timezone

**Database is already correct** - no migrations needed.

The user's configuration (10:45 Atlantic/Canary) will work correctly after implementation.
