# Database Migration Plan for Production Deployment

## Executive Summary

The production database needs to migrate through **14 Alembic migrations** to bring it from the old schema to the current codebase schema. The most critical migration is **210e7d798b58** which transforms all `video_id` values by adding prefixes (`yt_` or `up_`). This transformation is **irreversible** and affects all existing episodes.

**Recommendation**: **Test migrations on a local copy first**, then apply to production with a verified backup.

---

## Current State Analysis

### Production Database

- **Location**: `backend/data/labcastarr.db`
- **Backup**: SQL file backup exists
- **Media Files**: `backend/media/` (preserved, not affected by migrations)
- **Schema Version**: Unknown (needs verification)
- **Contains**: User config, channel settings, episodes, downloaded audio files

### Migration Chain Required

14 migrations total from initial schema to current HEAD (`36ae9abb89c6`):

1. `79b4815371be` - Initial schema
2. `138dbddf3ea3` - Add media_file_size
3. `d6d8d07b41e3` - Add video_id index
4. `a1b2c3d4e5f6` - Add source_type and original_filename
5. `b2c3d4e5f6g7` - Make video_id nullable
6. **`210e7d798b58` - Transform video IDs to prefixed format** ⚠️ **CRITICAL**
7. `f1a2b3c4d5e6` - Add follow channel feature
8. `g7h8i9j0k1l2` - Add Celery task status
9. `h9i0j1k2l3m4` - Add notifications table
10. `37bd0516b334` - Add executed_by to notifications
11. `9fb1bc92c905` - Add check time to user settings
12. `7d0e08ad4b92` - Ensure user settings defaults
13. `7f7abf5fdf3f` - Add timezone to user settings
14. `36ae9abb89c6` - Add YouTube channel description

---

## Approach Analysis: Local Copy vs Direct Production

### Option A: Test on Local Copy First (RECOMMENDED)

**Process**:

1. Copy production database to local development environment
2. Run Alembic migrations on the copy
3. Verify data integrity and application functionality
4. Document any issues or data inconsistencies
5. Apply same migrations to production with confidence

**Pros**:

- ✅ **Zero risk to production data** - Original data untouched during testing
- ✅ **Catch migration errors** before they affect production
- ✅ **Verify data transformations** - Can inspect video_id transformation results
- ✅ **Test application compatibility** - Ensure app works with migrated schema
- ✅ **Rollback practice** - Can test downgrade procedures safely
- ✅ **Timing estimate** - Know exactly how long production migration will take
- ✅ **Validate backup/restore** - Can test restore procedures from backup

**Cons**:

- ⏱️ Extra time investment (2-4 hours total)
- 💾 Requires local storage for database copy
- 🔄 Two-step process (test locally, then production)

**Time Estimate**:

- Local testing: 1-2 hours
- Production migration: 30 minutes (after successful local test)
- **Total: 2-3 hours**

---

### Option B: Direct Production Migration

**Process**:

1. Take production system offline
2. Create verified backup
3. Run Alembic migrations directly on production database
4. Verify migrations succeeded
5. Bring system back online

**Pros**:

- ⚡ Faster deployment if everything works perfectly
- 🎯 Single execution path
- 💾 No need for local database copy

**Cons**:

- ❌ **High risk** - Any migration failure affects production data
- ❌ **No rehearsal** - First run is on live data
- ❌ **Unknown issues** - Data-specific problems only discovered during production migration
- ❌ **Downtime uncertainty** - Can't predict how long migration will take
- ❌ **Rollback complexity** - Critical migration 210e7d798b58 is irreversible
- ❌ **Stress and pressure** - Must troubleshoot issues in real-time on production
- ❌ **Data loss risk** - If backup is invalid or incomplete

**Time Estimate**:

- Best case: 30-45 minutes
- If issues occur: 2-6 hours of downtime
- **Risk: High**

---

## Recommendation: Option A (Test Local Copy First)

**Rationale**:

1. **Critical transformation migration** - Migration 210e7d798b58 transforms ALL video_id values and is irreversible
2. **User data preservation** - Production contains valuable user configuration and episodes
3. **Unknown current state** - Don't know which migrations (if any) have already been applied
4. **Peace of mind** - Small time investment prevents catastrophic data loss
5. **Professional standard** - Industry best practice for database migrations

**Risk Assessment**:

- **Option A Risk**: Low (production data never at risk during testing)
- **Option B Risk**: High (one mistake = data loss, extended downtime)

---

## Critical Migration Details

### Migration 210e7d798b58 - Video ID Transformation ⚠️

**What It Does**:

- Transforms video_id format from `dQw4w9WgXcQ` to `yt_dQw4w9WgXcQ`
- Generates new IDs for uploaded episodes: `up_<random_11_chars>`
- Adds CHECK constraint: video*id must match `yt*%`or`up\_%` pattern
- **This is irreversible** - Original video IDs cannot be recovered

**Impact on Production**:

- All existing YouTube episodes get `yt_` prefix added
- Any uploaded episodes (if they exist) get generated `up_` IDs
- External references to video_ids will break unless updated
- RSS feeds will need regeneration with new video_ids

**Why This Matters**:

- If migration fails mid-transformation, database could be in inconsistent state
- Backup MUST be verified before running this migration
- Application code MUST be compatible with new video_id format

---

### Migration 9fb1bc92c905 - Enum Migration

**What It Does**:

- Migrates `TWICE_WEEKLY` frequency to `DAILY`
- This is also irreversible - original frequency settings lost

**Impact**: Low (unless users specifically configured TWICE_WEEKLY)

---

## Detailed Step-by-Step Plan

### Phase 1: Preparation (Local Environment)

**Step 1.1: Verify Current Production State**

```bash
# Copy production database to local machine
cp backend/data/labcastarr.db backend/data/labcastarr-prod-backup.db

# Check Alembic migration status
cd backend
uv run alembic current
```

**Expected Output**: Shows current migration revision (or none if migrations never run)

**Step 1.2: Create Working Copy**

```bash
# Create a test copy for migration testing
cp backend/data/labcastarr-prod-backup.db backend/data/labcastarr-dev.db

# Ensure .env.development points to dev database
# DATABASE_URL=sqlite:///./data/labcastarr-dev.db
```

---

### Phase 2: Test Migrations Locally

**Step 2.1: Inspect Database Before Migration**

```bash
cd backend

# Check current tables
uv run sqlite3 data/labcastarr-dev.db ".tables"

# Check episode count and sample video_ids
uv run sqlite3 data/labcastarr-dev.db "SELECT COUNT(*), video_id FROM episodes LIMIT 5;"

# Check if alembic_version table exists
uv run sqlite3 data/labcastarr-dev.db "SELECT * FROM alembic_version;"
```

**Step 2.2: Run Alembic Migrations**

```bash
cd backend

# Check what migrations will be applied
uv run alembic history

# Apply all pending migrations
uv run alembic upgrade head
```

**Watch for**:

- Any error messages
- Warnings about data transformations
- Migration execution time (note for production estimate)

**Step 2.3: Verify Migration Success**

```bash
# Verify all migrations applied
uv run alembic current

# Should show: 36ae9abb89c6 (current HEAD)

# Verify video_id transformation
uv run sqlite3 data/labcastarr-dev.db "SELECT video_id FROM episodes LIMIT 5;"
# Should show: yt_dQw4w9WgXcQ format

# Verify new tables exist
uv run sqlite3 data/labcastarr-dev.db ".schema followed_channels"
uv run sqlite3 data/labcastarr-dev.db ".schema youtube_videos"
uv run sqlite3 data/labcastarr-dev.db ".schema notifications"
uv run sqlite3 data/labcastarr-dev.db ".schema celery_task_status"
uv run sqlite3 data/labcastarr-dev.db ".schema user_settings"

# Check data integrity
uv run sqlite3 data/labcastarr-dev.db "SELECT COUNT(*) FROM episodes;"
uv run sqlite3 data/labcastarr-dev.db "SELECT COUNT(*) FROM channels;"
uv run sqlite3 data/labcastarr-dev.db "SELECT COUNT(*) FROM tags;"
```

---

### Phase 3: Application Testing (Local)

**Step 3.1: Start Local Backend with Migrated Database**

```bash
cd backend

# Ensure using dev database
export DATABASE_URL="sqlite:///./data/labcastarr-dev.db"

# Start backend
uv run fastapi dev app/main.py
```

**Step 3.2: Test Critical Functionality**

- [ ] Backend starts without errors
- [ ] API health check responds: `curl http://localhost:8000/health/`
- [ ] Can list channels: `GET /v1/channels`
- [ ] Can list episodes: `GET /v1/episodes?channel_id=1`
- [ ] Episode details load correctly
- [ ] RSS feed generation works: `GET /v1/feeds/{channel_id}/feed.xml`
- [ ] Media files accessible: `GET /v1/media/episodes/{id}/audio`

**Step 3.3: Test Frontend Integration**

```bash
cd frontend

# Start frontend
npm run dev
```

**Test UI**:

- [ ] Homepage loads
- [ ] Episodes list displays
- [ ] Episode details page works
- [ ] Settings page loads
- [ ] No console errors related to video_id format

---

### Phase 4: Document Findings

**Step 4.1: Record Migration Results**

- Migration execution time: **\_** seconds
- Any errors encountered: **\_**
- Data transformation verification: ✅ / ❌
- Application functionality: ✅ / ❌
- Issues discovered: **\_**

**Step 4.2: Create Migration Checklist**
Based on local testing, create production-specific checklist with:

- Expected downtime duration
- Pre-migration verification steps
- Post-migration verification steps
- Rollback procedure (if needed)

---

### Phase 5: Production Migration (After Successful Local Test)

**Step 5.1: Pre-Migration Backup**

```bash
# On production server
cd /path/to/labcastarr/backend

# Stop all services
docker compose -f docker-compose.prod.yml down

# Create backup with timestamp
cp data/labcastarr.db data/labcastarr-backup-$(date +%Y%m%d-%H%M%S).db

# Verify backup integrity
sqlite3 data/labcastarr-backup-*.db "PRAGMA integrity_check;"
# Should output: ok

# Verify backup is complete
sqlite3 data/labcastarr-backup-*.db "SELECT COUNT(*) FROM episodes;"
# Compare with original database
```

**Step 5.2: Verify Current Migration State**

```bash
# Check current Alembic version
docker compose -f docker-compose.prod.yml run --rm backend uv run alembic current

# If output is empty, database has never been migrated with Alembic
# If output shows revision, note it down
```

**Step 5.3: Run Production Migrations**

```bash
# Apply all migrations
docker compose -f docker-compose.prod.yml run --rm backend uv run alembic upgrade head

# Monitor output carefully for any errors
```

**Step 5.4: Verify Migration Success**

```bash
# Check final migration state
docker compose -f docker-compose.prod.yml run --rm backend uv run alembic current
# Should show: 36ae9abb89c6

# Verify data integrity
docker compose -f docker-compose.prod.yml run --rm backend uv run sqlite3 data/labcastarr.db "SELECT COUNT(*) FROM episodes;"

# Check video_id format
docker compose -f docker-compose.prod.yml run --rm backend uv run sqlite3 data/labcastarr.db "SELECT video_id FROM episodes LIMIT 5;"
```

**Step 5.5: Start Services and Verify**

```bash
# Start all services
docker compose --env-file .env.production -f docker-compose.prod.yml up -d

# Wait for services to be healthy
docker compose -f docker-compose.prod.yml ps

# Test API health
curl https://api.yourdomain.com/health/

# Test episodes endpoint
curl https://api.yourdomain.com/v1/episodes?channel_id=1 \
  -H "X-API-Key: YOUR_API_KEY"

# Test RSS feed
curl https://api.yourdomain.com/v1/feeds/1/feed.xml
```

**Step 5.6: Test Critical User Workflows**

- [ ] Login works
- [ ] Episodes display correctly
- [ ] Episode playback works
- [ ] RSS feed validates (use https://podba.se/validate/)
- [ ] Media files stream correctly
- [ ] Settings can be modified

---

### Phase 6: Post-Migration Cleanup

**Step 6.1: Monitor for Issues**

- Check backend logs: `docker compose -f docker-compose.prod.yml logs backend -f`
- Check error rates in application
- Monitor user reports

**Step 6.2: Archive Old Backup**

```bash
# After 24-48 hours of stable operation
# Move backup to long-term storage
mv data/labcastarr-backup-*.db /backup/archive/
```

---

## Rollback Procedures

### If Migration Fails During Local Testing

```bash
# Simply restore from backup
rm backend/data/labcastarr-dev.db
cp backend/data/labcastarr-prod-backup.db backend/data/labcastarr-dev.db

# Investigate error messages
# Fix issues in migration scripts if needed
# Retry migration
```

### If Production Migration Fails ⚠️

**CRITICAL: Migration 210e7d798b58 is irreversible**

**If failure occurs BEFORE migration 210e7d798b58**:

```bash
# Stop services
docker compose -f docker-compose.prod.yml down

# Restore from backup
rm backend/data/labcastarr.db
cp backend/data/labcastarr-backup-*.db backend/data/labcastarr.db

# Verify restoration
sqlite3 backend/data/labcastarr.db "PRAGMA integrity_check;"

# Restart with old codebase version (before new features)
# Or fix migration issue and retry
```

**If failure occurs DURING/AFTER migration 210e7d798b58**:

- **Cannot simply restore** - video_id transformation is one-way
- Must restore backup AND revert to old application code
- New features (follow channels, etc.) will not be available
- **Prevention is critical** - hence why local testing is mandatory

---

## Environment Configuration Notes

### Development (.env.development)

```bash
ENVIRONMENT=development
DATABASE_URL=sqlite:///./data/labcastarr-dev.db
```

### Production (.env.production)

```bash
ENVIRONMENT=production
DATABASE_URL=sqlite:///./data/labcastarr.db
```

**Important**: Ensure Docker Compose uses correct environment file:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml up -d
```

---

## Risk Mitigation Summary

| Risk                                 | Mitigation                                           |
| ------------------------------------ | ---------------------------------------------------- |
| Data loss during migration           | Test on local copy first; verified backup            |
| Migration fails mid-execution        | Backup before each attempt; monitor logs             |
| Irreversible video_id transformation | Test locally; verify results before production       |
| Extended downtime                    | Pre-calculate migration time from local test         |
| Application incompatibility          | Test full application with migrated database locally |
| Backup corruption                    | Verify backup integrity with PRAGMA checks           |
| Unknown current migration state      | Check alembic_version table before starting          |

---

## Success Criteria

### Local Testing Success

- [ ] All 14 migrations apply without errors
- [ ] Alembic reports current version: 36ae9abb89c6
- [ ] Episode count unchanged after migration
- [ ] All video*ids have yt* or up\_ prefix
- [ ] Backend starts and responds to API requests
- [ ] Frontend displays episodes correctly
- [ ] RSS feed generates successfully

### Production Migration Success

- [ ] All migrations complete successfully
- [ ] No data loss (episode count matches)
- [ ] Application starts without errors
- [ ] Users can access episodes
- [ ] Media files stream correctly
- [ ] RSS feeds validate
- [ ] No error spikes in logs
- [ ] User workflows function normally

---

## Timeline Estimate

| Phase                              | Duration      | Dependencies          |
| ---------------------------------- | ------------- | --------------------- |
| Phase 1: Preparation               | 15 min        | Database backup copy  |
| Phase 2: Local Migration Test      | 30 min        | Phase 1 complete      |
| Phase 3: Application Testing       | 30 min        | Phase 2 complete      |
| Phase 4: Documentation             | 15 min        | Phase 3 complete      |
| **Total Local Testing**            | **1.5 hours** |                       |
| Phase 5: Production Migration      | 30 min        | Local test successful |
| Phase 6: Post-Migration Monitoring | 1-2 hours     | Production live       |
| **Total**                          | **2-3 hours** |                       |

**Production Downtime**: 30-45 minutes (just Phase 5)

---

## Critical Files to Review Before Migration

1. **backend/alembic/versions/210e7d798b58_transform_video_ids_to_prefixed_format.py**

   - Contains video_id transformation logic
   - Must review upgrade() and downgrade() functions

2. **backend/app/core/config.py**

   - Database URL configuration
   - Environment detection

3. **docker-compose.prod.yml**

   - Ensure database volume mounts are correct
   - Verify Alembic migration command in entrypoint

4. **backend/app/infrastructure/database/models/episode.py**
   - Check video_id column definition
   - Verify CHECK constraint matches migration

---

## Next Steps

1. **Immediate**: Verify production database backup exists and is accessible
2. **Next**: Copy production database to local environment
3. **Then**: Execute Phase 1-4 (local testing)
4. **Finally**: Schedule production migration window after successful local test

**Recommended Production Migration Window**: Off-peak hours (e.g., 2-4 AM local time)

---

## Questions to Answer Before Proceeding

- [ ] Is current production database backup verified and accessible?
- [ ] What is current Alembic migration version in production? (May be none)
- [ ] Are there any uploaded episodes in production? (affects video_id migration)
- [ ] Is there a maintenance window scheduled for production migration?
- [ ] Who will monitor the migration and respond to issues?
- [ ] Is there a communication plan for users about downtime?

---

## Conclusion

**RECOMMENDED APPROACH**: Test on local copy first (Option A)

**Rationale**: The 1.5 hour investment in local testing prevents potentially catastrophic data loss from the irreversible video_id transformation. Production contains valuable user data that cannot be recreated if migration fails.

**Key Success Factor**: Verify backup integrity before ANY migration attempt.

---

Review your answers

● What is the current Alembic migration state of your production database?
→ We have already used alembic in production. Here is the ls in production version: ls backend/alembic/versions
138dbddf3ea3*add_media_file_size_to_episodes_and*.py
210e7d798b58*transform_video_ids_to_prefixed_format.py
79b4815371be_initial_database_schema_with_youtube*.py
a1b2c3d4e5f6_add_source_type_and_original_filename_to_episodes.py
b2c3d4e5f6g7_make_video_id_nullable.py
d6d8d07b41e3_add_video_id_index_and_unique_constraint.py
● Do you have any uploaded episodes (non-YouTube) in production?
→ Have uploaded episodes
● When would you like to perform the production migration?
→ I want to test locally the current code with the migrated production database. Then move to production
