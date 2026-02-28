# Task 0047: HOTFIX - Missing Database Columns

## 🚨 **CRITICAL ISSUE FIXED**

### Problem

After adding `last_check_task_id` and `last_backfill_task_id` columns to the `FollowedChannelModel`, the application broke with errors:

```
sqlite3.OperationalError: no such column: followed_channels.last_check_task_id
```

**Symptoms**:
1. ❌ Followed channels page showed "No followed channels yet" even though data existed
2. ❌ Could not add new followed channels
3. ❌ Could not discard videos
4. ❌ All operations involving `FollowedChannelModel` failed

### Root Cause

The Alembic migration was created and stamped, but the actual `ALTER TABLE` statements never executed because:
1. The migration tried to create the `celery_task_status` table which already existed (created by SQLAlchemy)
2. The migration failed before reaching the `ALTER TABLE` statements for `followed_channels`
3. We stamped it as complete without verifying the columns were actually added

### Solution

Manually added the missing columns using SQL:

```sql
ALTER TABLE followed_channels ADD COLUMN last_check_task_id VARCHAR(255);
ALTER TABLE followed_channels ADD COLUMN last_backfill_task_id VARCHAR(255);
```

### Verification

```bash
# Check columns exist
docker exec labcastarr-backend-1 uv run python -c "
from sqlalchemy import text
# ... check PRAGMA table_info(followed_channels) ...
"

# Output:
✅ Successfully added columns

Current columns in followed_channels:
  - id (INTEGER)
  - user_id (INTEGER)
  - youtube_channel_id (VARCHAR(255))
  - youtube_channel_name (VARCHAR(255))
  - youtube_channel_url (VARCHAR(500))
  - thumbnail_url (VARCHAR(500))
  - auto_approve (BOOLEAN)
  - auto_approve_channel_id (INTEGER)
  - last_checked (DATETIME)
  - created_at (DATETIME)
  - updated_at (DATETIME)
  - last_check_task_id (VARCHAR(255))  ✅ NEW
  - last_backfill_task_id (VARCHAR(255))  ✅ NEW
```

### Files Modified

**None** - Only database schema was modified via SQL

### Commands Executed

```bash
# 1. Start services
docker compose --env-file .env.production -f docker-compose.prod.yml up -d

# 2. Add missing columns
docker exec labcastarr-backend-1 uv run python -c "
import asyncio
from app.infrastructure.database.connection import get_async_db
from sqlalchemy import text

async def add_columns():
    async for db in get_async_db():
        await db.execute(text('ALTER TABLE followed_channels ADD COLUMN last_check_task_id VARCHAR(255)'))
        await db.execute(text('ALTER TABLE followed_channels ADD COLUMN last_backfill_task_id VARCHAR(255)'))
        await db.commit()
        break

asyncio.run(add_columns())
"

# 3. Restart backend
docker compose --env-file .env.production -f docker-compose.prod.yml restart backend

# 4. Verify data
docker exec labcastarr-backend-1 uv run python -c "
# ... check followed_channels data ...
"
```

### Impact

**FIXED**:
- ✅ Followed channels page now shows channels correctly
- ✅ Can add new followed channels
- ✅ Can discard videos
- ✅ All operations involving `FollowedChannelModel` work

### Lesson Learned

**Always verify migrations actually executed successfully!**

When a migration fails partway through:
1. ❌ Don't just stamp it as complete
2. ✅ Check the actual database schema
3. ✅ Manually apply missing changes if needed
4. ✅ Verify all expected columns/tables exist

### Prevention

For future migrations:
1. Run migrations in a transaction
2. Add checks to verify schema changes
3. Use `IF NOT EXISTS` clauses where appropriate
4. Test migrations on a copy of production data first

---

**Status**: ✅ **FIXED**
**Date**: 2025-11-14
**Time**: 21:20 UTC
**Impact**: CRITICAL - Restored full functionality





