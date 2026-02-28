# Database Migration Plan for Production Deployment

## Executive Summary

The production database needs to migrate through **14 Alembic migrations** to bring it from the old schema to the current codebase schema. The most critical migration is **210e7d798b58** which transforms all `video_id` values by adding prefixes (`yt_` or `up_`). This transformation is **irreversible** and affects all existing episodes.

**Recommendation**: **Test migrations on a local copy first**, then apply to production with a verified backup.

**GOOD NEWS**: The most critical migration (210e7d798b58 - video_id transformation) has ALREADY been applied to production! The remaining 8 migrations are additive (new tables/columns) with much lower risk.

---

## Current State Analysis

### Production Database

- **Location**: `backend/data/labcastarr.db`
- **Backup**: SQL file backup exists
- **Media Files**: `backend/media/` (preserved, not affected by migrations)
- **Schema Version**: ✅ **CONFIRMED - Already at migration 210e7d798b58** (video_id transformation)
- **Contains**: User config, channel settings, episodes (both YouTube and uploaded), downloaded audio files
- **Migration Status**: Production has 6 migrations applied (up to 210e7d798b58)

### CRITICAL DISCOVERY: Production Already Has Video ID Transformation

**Production Migrations (from ls output)**:

1. ✅ `79b4815371be` - Initial database schema
2. ✅ `138dbddf3ea3` - Add media_file_size
3. ✅ `d6d8d07b41e3` - Add video_id index
4. ✅ `a1b2c3d4e5f6` - Add source_type and original_filename
5. ✅ `b2c3d4e5f6g7` - Make video_id nullable
6. ✅ `210e7d798b58` - Transform video IDs to prefixed format ⚠️

**Current Codebase Has 14 Migrations Total**:

- Production is at migration #6 of 14
- **8 NEW migrations need to be applied** (#7-#14)

### Migration Chain Required

**Production is at**: Migration #6 (`210e7d798b58`)
**Current codebase is at**: Migration #14 (`36ae9abb89c6`)
**Migrations to apply**: 8 new migrations (#7-#14)

**Already Applied in Production** ✅:

1. ✅ `79b4815371be` - Initial schema
2. ✅ `138dbddf3ea3` - Add media_file_size
3. ✅ `d6d8d07b41e3` - Add video_id index
4. ✅ `a1b2c3d4e5f6` - Add source_type and original_filename
5. ✅ `b2c3d4e5f6g7` - Make video_id nullable
6. ✅ **`210e7d798b58` - Transform video IDs to prefixed format** ⚠️ **ALREADY DONE**

**Need to Apply (New Migrations)** ⏳: 7. ⏳ `f1a2b3c4d5e6` - Add follow channel feature 8. ⏳ `g7h8i9j0k1l2` - Add Celery task status 9. ⏳ `h9i0j1k2l3m4` - Add notifications table 10. ⏳ `37bd0516b334` - Add executed_by to notifications 11. ⏳ `9fb1bc92c905` - Add check time to user settings 12. ⏳ `7d0e08ad4b92` - Ensure user settings defaults 13. ⏳ `7f7abf5fdf3f` - Add timezone to user settings 14. ⏳ `36ae9abb89c6` - Add YouTube channel description

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

### ✅ Migration 210e7d798b58 - Video ID Transformation (ALREADY APPLIED)

**Status**: ✅ **This migration has ALREADY been applied to production!**

**What It Did**:

- Transformed video_id format from `dQw4w9WgXcQ` to `yt_dQw4w9WgXcQ`
- Generated new IDs for uploaded episodes: `up_<random_11_chars>`
- Added CHECK constraint: video*id must match `yt*%`or`up\_%` pattern

**Why This Matters**:

- ✅ Production data has already been transformed successfully
- ✅ Most dangerous migration is behind us
- ✅ Remaining migrations are much lower risk (additive only)
- ⚠️ Still need to verify video_ids are in correct format before proceeding

---

### ⏳ Remaining Migrations Summary (7-14)

**All remaining migrations are ADDITIVE** - they create new tables or add new columns with defaults:

**New Feature Tables**:

- Migration #7: `followed_channels`, `youtube_videos`, `user_settings` tables
- Migration #8: `celery_task_status` table + columns to followed_channels
- Migration #9: `notifications` table

**New Columns with Defaults**:

- Migration #10: `executed_by` to notifications (default='user')
- Migration #11: `preferred_check_hour/minute` to user_settings + TWICE_WEEKLY→DAILY enum migration
- Migration #12: Auto-creates user_settings for orphaned users
- Migration #13: `timezone` to user_settings (default='Europe/Madrid')
- Migration #14: `youtube_channel_description` to followed_channels (nullable)

**Risk Level**: LOW - No data transformations, only schema additions

---

## Detailed Step-by-Step Plan

### Phase 1: Preparation (Local Environment)

**Step 1.1: Verify Current Production State**

```bash
# Copy production database to local machine (if not already done)
# Ensure you have: backend/data/labcastarr.db (the production backup)

# Create timestamped backup for safety
cp backend/data/labcastarr.db backend/data/labcastarr-prod-$(date +%Y%m%d-%H%M%S).db

# Check Alembic migration status
cd backend
DATABASE_URL="sqlite:///./data/labcastarr.db" uv run alembic current
```

**Expected Output**: Should show `210e7d798b58` (migration #6) based on production file listing

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
sqlite3 data/labcastarr-dev.db ".tables"

# Check episode count and verify video_ids are already prefixed
sqlite3 data/labcastarr-dev.db "SELECT COUNT(*) as total_episodes FROM episodes;"
sqlite3 data/labcastarr-dev.db "SELECT video_id, source_type FROM episodes LIMIT 10;"

# Should see yt_ and up_ prefixes already (since 210e7d798b58 was applied)

# Check current migration version
sqlite3 data/labcastarr-dev.db "SELECT * FROM alembic_version;"
# Expected: 210e7d798b58

# Check for uploaded episodes
sqlite3 data/labcastarr-dev.db "SELECT COUNT(*) FROM episodes WHERE source_type='upload';"
```

**Step 2.2: Run Remaining Alembic Migrations**

```bash
cd backend

# Check what migrations will be applied (should be 8 new ones)
DATABASE_URL="sqlite:///./data/labcastarr-dev.db" uv run alembic history
DATABASE_URL="sqlite:///./data/labcastarr-dev.db" uv run alembic current -v

# Apply pending migrations (7-14)
DATABASE_URL="sqlite:///./data/labcastarr-dev.db" uv run alembic upgrade head
```

**Expected Migrations to Apply**:

- f1a2b3c4d5e6 → Add follow channel feature
- g7h8i9j0k1l2 → Add Celery task status
- h9i0j1k2l3m4 → Add notifications table
- 37bd0516b334 → Add executed_by to notifications
- 9fb1bc92c905 → Add check time to user settings
- 7d0e08ad4b92 → Ensure user settings defaults
- 7f7abf5fdf3f → Add timezone to user settings
- 36ae9abb89c6 → Add YouTube channel description

**Watch for**:

- Should be fast (only schema additions, no data transformations)
- Migration 7d0e08ad4b92 will auto-create user_settings for users
- Migration execution time (note for production estimate)

**Step 2.3: Verify Migration Success**

```bash
cd backend

# Verify all migrations applied
DATABASE_URL="sqlite:///./data/labcastarr-dev.db" uv run alembic current
# Should show: 36ae9abb89c6 (current HEAD)

# Verify video_ids are still in correct format (should already have prefixes)
sqlite3 data/labcastarr-dev.db "SELECT video_id FROM episodes LIMIT 5;"
# Should show: yt_* or up_* format

# Verify new tables exist
sqlite3 data/labcastarr-dev.db ".schema followed_channels"
sqlite3 data/labcastarr-dev.db ".schema youtube_videos"
sqlite3 data/labcastarr-dev.db ".schema notifications"
sqlite3 data/labcastarr-dev.db ".schema celery_task_status"
sqlite3 data/labcastarr-dev.db ".schema user_settings"

# Verify user_settings were auto-created (migration #12)
sqlite3 data/labcastarr-dev.db "SELECT COUNT(*) FROM user_settings;"
sqlite3 data/labcastarr-dev.db "SELECT user_id, subscription_check_frequency, timezone FROM user_settings;"

# Check data integrity (counts should match pre-migration)
sqlite3 data/labcastarr-dev.db "SELECT COUNT(*) FROM episodes;"
sqlite3 data/labcastarr-dev.db "SELECT COUNT(*) FROM channels;"
sqlite3 data/labcastarr-dev.db "SELECT COUNT(*) FROM tags;"
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
docker compose --env-file .env.production -f docker-compose.prod.yml run --rm backend uv run alembic current

# Expected output: 210e7d798b58 (migration #6)
# This confirms production needs migrations #7-14
```

**Step 5.3: Run Production Migrations**

```bash
# Apply remaining 8 migrations (f1a2b3c4d5e6 through 36ae9abb89c6)
docker compose --env-file .env.production -f docker-compose.prod.yml run --rm backend uv run alembic upgrade head

# Monitor output - should see 8 migrations applied:
# - f1a2b3c4d5e6 -> Add follow channel feature
# - g7h8i9j0k1l2 -> Add Celery task status
# - h9i0j1k2l3m4 -> Add notifications table
# - 37bd0516b334 -> Add executed_by to notifications
# - 9fb1bc92c905 -> Add check time to user settings
# - 7d0e08ad4b92 -> Ensure user settings defaults
# - 7f7abf5fdf3f -> Add timezone to user settings
# - 36ae9abb89c6 -> Add YouTube channel description
```

**Step 5.4: Verify Migration Success**

```bash
# Check final migration state
docker compose --env-file .env.production -f docker-compose.prod.yml run --rm backend uv run alembic current
# Should show: 36ae9abb89c6 (current HEAD)

# Verify new tables exist
docker compose --env-file .env.production -f docker-compose.prod.yml run --rm backend sqlite3 data/labcastarr.db ".tables"
# Should include: followed_channels, youtube_videos, notifications, celery_task_status, user_settings

# Verify data integrity (episode count unchanged)
docker compose --env-file .env.production -f docker-compose.prod.yml run --rm backend sqlite3 data/labcastarr.db "SELECT COUNT(*) FROM episodes;"

# Verify user_settings created
docker compose --env-file .env.production -f docker-compose.prod.yml run --rm backend sqlite3 data/labcastarr.db "SELECT COUNT(*) FROM user_settings;"
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

**GOOD NEWS: The irreversible migration (210e7d798b58) has already been applied successfully in production!**

**If failure occurs in migrations #7-14** (all additive):

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

**If failure occurs in migration #11 (9fb1bc92c905)**:

- This migration changes TWICE_WEEKLY → DAILY (irreversible)
- If users had TWICE_WEEKLY setting, it will be lost on downgrade
- Other than this, all migrations #7-14 can be safely downgraded

**Downgrade Command** (if needed):

```bash
# Downgrade to specific migration
docker compose --env-file .env.production -f docker-compose.prod.yml run --rm backend uv run alembic downgrade <revision_id>

# Or restore from backup
docker compose -f docker-compose.prod.yml down
rm backend/data/labcastarr.db
cp backend/data/labcastarr-backup-*.db backend/data/labcastarr.db
```

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

| Risk                                 | Mitigation                                           | Status              |
| ------------------------------------ | ---------------------------------------------------- | ------------------- |
| Irreversible video_id transformation | Video ID transformation already done                 | ✅ Already Complete |
| Data loss during migration           | Test on local copy first; verified backup            | ⚠️ Required         |
| Migration fails mid-execution        | Backup before each attempt; monitor logs             | ⚠️ Required         |
| Extended downtime                    | Pre-calculate migration time from local test         | ⏳ In Progress      |
| Application incompatibility          | Test full application with migrated database locally | ⏳ In Progress      |
| Backup corruption                    | Verify backup integrity with PRAGMA checks           | ⚠️ Required         |
| New feature tables conflict          | All new migrations are additive (low risk)           | ✅ Low Risk         |

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

| Phase                              | Duration      | Dependencies          | Notes                             |
| ---------------------------------- | ------------- | --------------------- | --------------------------------- |
| Phase 1: Preparation               | 10 min        | Database backup copy  | Quick (already have prod DB)      |
| Phase 2: Local Migration Test      | 15 min        | Phase 1 complete      | Fast (8 additive migrations only) |
| Phase 3: Application Testing       | 30 min        | Phase 2 complete      | Test new features work            |
| Phase 4: Documentation             | 10 min        | Phase 3 complete      | Record findings                   |
| **Total Local Testing**            | **~1 hour**   |                       | Faster due to fewer migrations    |
| Phase 5: Production Migration      | 15-20 min     | Local test successful | Much faster (additive only)       |
| Phase 6: Post-Migration Monitoring | 1-2 hours     | Production live       | Verify stability                  |
| **Total**                          | **2-3 hours** |                       | Less than original estimate       |

**Production Downtime**: 15-20 minutes (Phase 5 only)

**Why Faster**:

- Most dangerous migration already applied ✅
- Only 8 additive migrations (vs 14 total)
- No data transformations required

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

## Questions Answered ✅

- ✅ Is current production database backup verified and accessible? **YES - SQL backup exists**
- ✅ What is current Alembic migration version in production? **210e7d798b58 (migration #6)**
- ✅ Are there any uploaded episodes in production? **YES - confirmed by user**
- ⏳ Is there a maintenance window scheduled for production migration? **User wants to test locally first**
- ⏳ Who will monitor the migration and respond to issues? **User will monitor**
- ⏳ Is there a communication plan for users about downtime? **TBD**

---

## Conclusion

**RECOMMENDED APPROACH**: Test on local copy first (Option A)

**Rationale**:

- ✅ Most dangerous migration (video_id transformation) already applied successfully
- ✅ Only 8 additive migrations remain (low risk but still worth testing)
- ✅ 1 hour of local testing provides confidence and timing estimates
- ✅ Minimal production downtime (15-20 minutes expected)

**Risk Level**: **MUCH LOWER** than initially assessed

- Critical transformation already complete
- Remaining migrations are schema additions only
- Can be safely downgraded if needed (except migration #11 enum change)

**Key Success Factors**:

1. Verify backup integrity before starting
2. Test migrations locally to catch any edge cases
3. Verify new features work with migrated database
4. Monitor application logs after production deployment

**Next Immediate Steps**:

1. Copy production database to local `backend/data/labcastarr-dev.db`
2. Run `DATABASE_URL="sqlite:///./data/labcastarr-dev.db" uv run alembic upgrade head`
3. Test backend/frontend with migrated database
4. If successful, schedule production migration window

---

## Summary for Quick Reference

**Current State**:

- Production: At migration #6 (210e7d798b58)
- Current codebase: At migration #14 (36ae9abb89c6)
- Gap: 8 migrations to apply (#7-14)

**Migration Types**:

- ✅ Data transformation (210e7d798b58): Already done
- ⏳ Schema additions (7-14): Need to apply

**Risk Assessment**:

- Original risk: HIGH (irreversible transformation)
- Current risk: LOW (additive only, can downgrade if needed)

**Timeline**:

- Local testing: ~1 hour
- Production downtime: 15-20 minutes
- Total: 2-3 hours including monitoring

---

Summary for Quick Reference

Current State:

- Production: At migration #6 (210e7d798b58)
- Current codebase: At migration #14 (36ae9abb89c6)
- Gap: 8 migrations to apply (#7-14)

Migration Types:

- ✅ Data transformation (210e7d798b58): Already done
- ⏳ Schema additions (7-14): Need to apply

Risk Assessment:

- Original risk: HIGH (irreversible transformation)
- Current risk: LOW (additive only, can downgrade if needed)

Timeline:

- Local testing: ~1 hour
- Production downtime: 15-20 minutes
- Total: 2-3 hours including monitoring
