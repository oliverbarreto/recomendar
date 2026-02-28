# Production Environment - Database Migration Fix

## Issue

When running the production environment with Docker, the frontend was unable to load episodes, showing "Failed to load episodes" with `[object Object]` error.

**Error in logs**:
```
no such column: episodes.source_type
```

## Root Cause

The database migration for the file upload feature was created but **never applied** to the production database. The code was trying to query the new columns (`source_type` and `original_filename`) that didn't exist in the database schema.

### Why This Happened

1. Migration file was created: `backend/alembic/versions/a1b2c3d4e5f6_add_source_type_and_original_filename_to_episodes.py`
2. Code was deployed with references to the new columns
3. Migration was NOT applied to the database
4. Database schema was out of sync with the code

## Solution Applied

Applied the pending database migration inside the running Docker container:

```bash
# Check current migration version
docker exec labcastarr-backend-1 uv run alembic current
# Output: d6d8d07b41e3

# Check available migrations
docker exec labcastarr-backend-1 uv run alembic history
# Output showed: d6d8d07b41e3 -> a1b2c3d4e5f6 (head), Add source_type and original_filename to episodes

# Apply the migration
docker exec labcastarr-backend-1 uv run alembic upgrade head
# Output: Running upgrade d6d8d07b41e3 -> a1b2c3d4e5f6

# Verify migration was applied
docker exec labcastarr-backend-1 uv run alembic current
# Output: a1b2c3d4e5f6 (head)
```

## Verification

### 1. Verified columns exist in database:
```bash
docker exec labcastarr-backend-1 uv run python -c "
from sqlalchemy import create_engine, inspect
engine = create_engine('sqlite:///./data/labcastarr.db')
inspector = inspect(engine)
columns = inspector.get_columns('episodes')
for col in columns:
    if col['name'] in ['source_type', 'original_filename']:
        print(f\"{col['name']}: {col['type']}\")"
```

**Output**:
```
source_type: VARCHAR(20)
original_filename: VARCHAR(500)
```

### 2. Tested API endpoint:
```bash
curl -s -H "X-API-Key: <key>" "http://localhost:8000/v1/episodes/?channel_id=1&skip=0&limit=5"
```

**Result**: ✅ Successfully returned 5 episodes with all fields including `source_type` and `original_filename`

### 3. Checked backend logs:
```
status_code: 200
content_length: 15484
Request completed successfully
```

## Status

✅ **FIXED** - Episodes are now loading correctly in both the API and frontend.

## Important Notes

### For Future Deployments

1. **Always apply migrations before deploying new code** that depends on schema changes
2. **Check migration status** in each environment:
   ```bash
   docker exec <container> uv run alembic current
   ```
3. **Apply pending migrations**:
   ```bash
   docker exec <container> uv run alembic upgrade head
   ```

### Migration Applied To

- ✅ Production environment (labcastarr-backend-1)
- ⚠️ **TODO**: Verify development environment also has this migration applied

### What the Migration Does

The migration adds two new columns to the `episodes` table:
- `source_type` (VARCHAR(20), default: "youtube") - Distinguishes between YouTube and uploaded episodes
- `original_filename` (VARCHAR(500), nullable) - Stores the original filename for uploaded audio files

It also creates an index on `source_type` for better query performance.

## Related Files

- Migration file: `backend/alembic/versions/a1b2c3d4e5f6_add_source_type_and_original_filename_to_episodes.py`
- Database model: `backend/app/infrastructure/database/models/episode.py`
- Domain entity: `backend/app/domain/entities/episode.py`
- Upload service: `backend/app/application/services/upload_processing_service.py`

---

**Fixed by**: AI Assistant  
**Date**: October 18, 2025  
**Environment**: Production (Docker)  
**Related Task**: task-0029-upload-episode-plan-v2.md




