# Production Deployment SOP - Database Migrations

## Standard Operating Procedure for Production Deployment with Database Changes

**Version:** 1.0
**Last Updated:** 2025-11-28
**Owner:** LabCastARR Team
**Review Cycle:** Quarterly

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Pre-Deployment Checklist](#pre-deployment-checklist)
4. [Deployment Procedure](#deployment-procedure)
5. [Post-Deployment Verification](#post-deployment-verification)
6. [Rollback Procedure](#rollback-procedure)
7. [Troubleshooting](#troubleshooting)
8. [Emergency Contacts](#emergency-contacts)

---

## Overview

### Purpose

This SOP defines the step-by-step process for deploying new versions of LabCastARR to production servers when the deployment includes database schema changes via Alembic migrations.

### Scope

- Applies to all production deployments involving database migrations
- Covers backup, deployment, verification, and rollback procedures
- Ensures zero data loss during migrations

### Key Principles

1. **Always backup before migrations**
2. **Test migrations in staging/pre-production first**
3. **Verify data integrity after deployment**
4. **Have a rollback plan ready**
5. **Document everything**

---

## Prerequisites

### Required Access

- [ ] SSH access to production server
- [ ] Docker access on production server
- [ ] Git repository access
- [ ] Access to `.env.production` configuration
- [ ] Backup storage access

### Required Tools

- [ ] SSH client
- [ ] Git client
- [ ] Docker and Docker Compose (on production server)
- [ ] SQLite tools (for backup verification)

### Knowledge Requirements

- Understanding of Docker Compose
- Basic SQLite knowledge
- Familiarity with Alembic migrations
- Access to this SOP document

---

## Pre-Deployment Checklist

### 1. Development Completion

- [ ] All code changes committed and pushed to repository
- [ ] Code reviewed and approved
- [ ] All tests passing locally
- [ ] Frontend builds successfully (`cd frontend && npm run build`)
- [ ] Backend tests pass (`cd backend && uv run pytest` if tests exist)

### 2. Migration Verification

#### Check Migration Status

```bash
# On your local development machine
cd backend

# View all migrations
uv run alembic history

# View pending migrations (should show new migrations)
uv run alembic current

# Verify migration file exists
ls -la alembic/versions/<new_migration_file>.py
```

#### Review Migration Content

- [ ] Open the migration file in `backend/alembic/versions/`
- [ ] Verify `upgrade()` function logic
- [ ] Verify `downgrade()` function logic (rollback capability)
- [ ] Check for data transformation logic (if any)
- [ ] Confirm no destructive operations without backups

**Example migration review:**

```python
# File: backend/alembic/versions/abc123def456_add_new_feature.py

def upgrade() -> None:
    # ✅ Adding columns - safe
    op.add_column('episodes', sa.Column('new_field', sa.String(), nullable=True))

    # ✅ Creating indexes - safe
    op.create_index('ix_episodes_new_field', 'episodes', ['new_field'])

    # ⚠️ Data transformation - verify logic carefully
    # Ensure this doesn't cause data loss

def downgrade() -> None:
    # ✅ Verify rollback works
    op.drop_index('ix_episodes_new_field')
    op.drop_column('episodes', 'new_field')
```

### 3. Pre-Production Testing

- [ ] Deploy to pre-production environment (`.env.pre`)
- [ ] Run migration in pre-production: `docker exec <backend-container> uv run alembic upgrade head`
- [ ] Verify application functionality in pre-production
- [ ] Test rollback in pre-production: `docker exec <backend-container> uv run alembic downgrade -1`
- [ ] Verify data integrity after rollback
- [ ] Re-apply migration to pre-production

**Pre-Production Deployment:**

```bash
# Deploy to pre-production with migrations
docker compose --env-file .env.pre -f docker-compose.pre.yml down
docker compose --env-file .env.pre -f docker-compose.pre.yml up --build -d

# Monitor logs
docker compose -f docker-compose.pre.yml logs backend-pre -f

# Verify health
curl https://labcastarr-api-pre.yourdomain.com/health/
```

### 4. Maintenance Window Planning

- [ ] Schedule deployment during low-traffic period
- [ ] Notify users of planned maintenance (if applicable)
- [ ] Prepare maintenance page (if needed)
- [ ] Estimate downtime (typically 5-15 minutes for migrations)
- [ ] Have rollback time buffer (additional 10-15 minutes)

### 5. Team Coordination

- [ ] Notify team of deployment schedule
- [ ] Assign roles (deployer, verifier, communicator)
- [ ] Ensure backup person is available
- [ ] Have communication channel open (Slack, Discord, etc.)

---

## Deployment Procedure

### Phase 1: Pre-Deployment Backup (CRITICAL)

#### Step 1.1: Connect to Production Server

```bash
# SSH into production server
ssh user@production-server.com

# Navigate to project directory
cd /path/to/labcastarr
```

#### Step 1.2: Stop Application Services

```bash
# Stop all services gracefully
docker compose -f docker-compose.prod.yml down

# Verify all containers stopped
docker compose -f docker-compose.prod.yml ps
```

**Expected Output:**
```
NAME   IMAGE   COMMAND   SERVICE   CREATED   STATUS   PORTS
(empty - all containers stopped)
```

#### Step 1.3: Create Database Backup

```bash
# Create backup directory with timestamp
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# Backup production database
cp backend/data/labcastarr.db $BACKUP_DIR/labcastarr.db
cp backend/data/labcastarr.db-wal $BACKUP_DIR/labcastarr.db-wal 2>/dev/null || true
cp backend/data/labcastarr.db-shm $BACKUP_DIR/labcastarr.db-shm 2>/dev/null || true

# Verify backup was created
ls -lh $BACKUP_DIR/

# Create backup manifest
echo "Backup created: $(date)" > $BACKUP_DIR/MANIFEST.txt
echo "Database size: $(du -h $BACKUP_DIR/labcastarr.db | cut -f1)" >> $BACKUP_DIR/MANIFEST.txt
echo "Git commit: $(git rev-parse HEAD)" >> $BACKUP_DIR/MANIFEST.txt

# Display backup info
cat $BACKUP_DIR/MANIFEST.txt
```

**Verification:**
- [ ] Database file backed up (typically 1MB - 500MB depending on data)
- [ ] WAL and SHM files backed up (if they exist)
- [ ] Manifest file created with timestamp and git commit

#### Step 1.4: Test Database Backup Integrity

```bash
# Verify SQLite database is not corrupted
sqlite3 $BACKUP_DIR/labcastarr.db "PRAGMA integrity_check;"
```

**Expected Output:**
```
ok
```

**If integrity check fails, DO NOT PROCEED. Investigate database corruption first.**

#### Step 1.5: Create Additional Backups (Optional but Recommended)

```bash
# Backup media files (episodes)
tar -czf $BACKUP_DIR/media_backup.tar.gz backend/media/

# Backup RSS feeds
tar -czf $BACKUP_DIR/feeds_backup.tar.gz backend/feeds/

# Backup logs (for troubleshooting)
tar -czf $BACKUP_DIR/logs_backup.tar.gz backend/logs/

# Display backup sizes
du -sh $BACKUP_DIR/*
```

#### Step 1.6: Store Backup Offsite (Recommended)

```bash
# Copy backup to offsite location (S3, NAS, etc.)
# Example with rsync to backup server:
rsync -avz $BACKUP_DIR/ backup-server:/backups/labcastarr/$BACKUP_DIR/

# Or compress and upload
tar -czf labcastarr_backup_$(date +%Y%m%d_%H%M%S).tar.gz $BACKUP_DIR/
# Upload to your backup solution
```

---

### Phase 2: Code Deployment

#### Step 2.1: Record Current State

```bash
# Record current git commit (for rollback reference)
git rev-parse HEAD > /tmp/previous_commit.txt
cat /tmp/previous_commit.txt

# Record current Docker images (for rollback reference)
docker compose -f docker-compose.prod.yml images > /tmp/previous_images.txt
cat /tmp/previous_images.txt
```

#### Step 2.2: Pull Latest Code

```bash
# Fetch latest code from repository
git fetch origin

# Checkout production branch (adjust branch name as needed)
git checkout main

# Pull latest changes
git pull origin main

# Verify you're on the correct commit
git log -1 --oneline
```

#### Step 2.3: Verify Environment Configuration

```bash
# Ensure production environment file exists
ls -la .env.production

# Verify critical environment variables are set
grep -E "ENVIRONMENT|DATABASE_URL|API_KEY_SECRET|JWT_SECRET_KEY" .env.production

# Check Docker Compose file
ls -la docker-compose.prod.yml
```

**Critical Environment Variables:**
- `ENVIRONMENT=production`
- `DATABASE_URL=sqlite:///./data/labcastarr.db`
- `API_KEY_SECRET=<your-secret>`
- `JWT_SECRET_KEY=<your-secret>`
- `BASE_URL=https://api.yourdomain.com`
- `FRONTEND_URL=https://yourdomain.com`

---

### Phase 3: Database Migration

#### Step 3.1: Start Backend Container Only (For Migration)

```bash
# Start only backend service for migration
docker compose --env-file .env.production -f docker-compose.prod.yml up -d backend-prod redis-prod

# Wait for backend to be ready (migrations run automatically via startup.sh)
sleep 30

# Monitor backend logs for migration progress
docker compose -f docker-compose.prod.yml logs backend-prod --tail=100 -f
```

**What to Look For in Logs:**

```
Running database migrations...
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade abc123 -> def456, add_new_feature
Starting application...
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**If you see errors, STOP and proceed to Rollback Procedure.**

#### Step 3.2: Verify Migration Success

```bash
# Connect to backend container
docker exec -it labcastarr-backend-prod-1 /bin/bash

# Inside container, check migration status
uv run alembic current

# Should show the latest migration revision
# Example output: abc123def456 (head)

# Exit container
exit
```

#### Step 3.3: Manual Migration (If Automatic Failed)

**Only if startup.sh failed to run migrations:**

```bash
# Stop backend container
docker compose -f docker-compose.prod.yml stop backend-prod

# Start container without running startup.sh
docker compose --env-file .env.production -f docker-compose.prod.yml run --rm backend-prod /bin/bash

# Inside container, run migration manually
uv run alembic upgrade head

# Check for errors
# If successful, exit and restart normally
exit

# Restart backend with normal startup script
docker compose -f docker-compose.prod.yml up -d backend-prod
```

#### Step 3.4: Verify Database Integrity Post-Migration

```bash
# Check database integrity
docker exec labcastarr-backend-prod-1 sqlite3 /app/data/labcastarr.db "PRAGMA integrity_check;"
```

**Expected Output:**
```
ok
```

---

### Phase 4: Full Application Startup

#### Step 4.1: Start All Services

```bash
# Start all production services
docker compose --env-file .env.production -f docker-compose.prod.yml up -d

# Verify all containers are running
docker compose -f docker-compose.prod.yml ps
```

**Expected Output:**
```
NAME                          STATUS          PORTS
labcastarr-backend-prod-1     Up (healthy)    0.0.0.0:8000->8000/tcp
labcastarr-frontend-prod-1    Up              0.0.0.0:3000->3000/tcp
labcastarr-redis-prod-1       Up (healthy)    6379/tcp
labcastarr-celery-worker-1    Up
labcastarr-celery-beat-1      Up
```

#### Step 4.2: Monitor Startup Logs

```bash
# Monitor all service logs
docker compose -f docker-compose.prod.yml logs -f

# Or monitor specific services:
docker compose -f docker-compose.prod.yml logs backend-prod -f
docker compose -f docker-compose.prod.yml logs frontend-prod -f
docker compose -f docker-compose.prod.yml logs celery-worker-prod -f
```

**Watch for:**
- No error messages
- Services showing "healthy" status
- Celery workers connecting to Redis
- Frontend connecting to backend API

#### Step 4.3: Wait for Health Checks

```bash
# Wait for backend health check to pass (may take 30-60 seconds)
echo "Waiting for backend to become healthy..."
timeout 120 bash -c 'until docker inspect --format="{{.State.Health.Status}}" labcastarr-backend-prod-1 | grep -q "healthy"; do sleep 2; done'

echo "Backend is healthy!"

# Verify Celery workers started
docker compose -f docker-compose.prod.yml logs celery-worker-prod --tail=20
```

---

## Post-Deployment Verification

### Phase 5: Functional Testing

#### Step 5.1: Backend API Health Check

```bash
# Test backend health endpoint
curl -i https://api.yourdomain.com/health/

# Expected: HTTP/1.1 200 OK
# Response should include: {"status": "healthy", ...}
```

#### Step 5.2: API Documentation Access

```bash
# Verify API docs are accessible
curl -I https://api.yourdomain.com/docs

# Expected: HTTP/1.1 200 OK
```

#### Step 5.3: Frontend Access

```bash
# Test frontend is accessible
curl -I https://yourdomain.com

# Expected: HTTP/1.1 200 OK
```

#### Step 5.4: Authentication Test

```bash
# Test login endpoint
curl -X POST https://api.yourdomain.com/v1/auth/login \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"email": "user@labcastarr.local", "password": "labcastarr123"}'

# Expected: JWT tokens returned
# {"access_token": "...", "refresh_token": "...", "token_type": "bearer"}
```

#### Step 5.5: Database Query Test

```bash
# Test that new schema changes are reflected
docker exec labcastarr-backend-prod-1 sqlite3 /app/data/labcastarr.db ".schema <new_table_name>"

# Or check if new column exists
docker exec labcastarr-backend-prod-1 sqlite3 /app/data/labcastarr.db "PRAGMA table_info(<table_name>);"
```

#### Step 5.6: Data Integrity Verification

```bash
# Check record counts (should match pre-deployment counts)
docker exec labcastarr-backend-prod-1 sqlite3 /app/data/labcastarr.db "SELECT COUNT(*) FROM users;"
docker exec labcastarr-backend-prod-1 sqlite3 /app/data/labcastarr.db "SELECT COUNT(*) FROM channels;"
docker exec labcastarr-backend-prod-1 sqlite3 /app/data/labcastarr.db "SELECT COUNT(*) FROM episodes;"

# Compare with pre-deployment counts recorded in backup manifest
```

#### Step 5.7: Application Feature Testing

**Manual UI Testing Checklist:**

- [ ] Open frontend: https://yourdomain.com
- [ ] Login with credentials
- [ ] Navigate to Episodes page
- [ ] Test YouTube episode creation (if applicable to changes)
- [ ] Test file upload (if applicable to changes)
- [ ] Test RSS feed access: `https://api.yourdomain.com/v1/feeds/1/feed.xml`
- [ ] Test audio playback
- [ ] Test new features introduced in this deployment
- [ ] Verify existing features still work

#### Step 5.8: Celery Background Tasks

```bash
# Check Celery worker is processing tasks
docker compose -f docker-compose.prod.yml logs celery-worker-prod --tail=50

# Should see:
# - Worker started
# - Connected to Redis
# - Ready to process tasks

# Test a background task (if applicable)
# Example: Follow a YouTube channel and verify Celery processes it
```

#### Step 5.9: Log Review

```bash
# Check for any errors in application logs
docker compose -f docker-compose.prod.yml logs --tail=200 | grep -i "error\|exception\|failed"

# Check backend logs specifically
docker compose -f docker-compose.prod.yml logs backend-prod --tail=100 | grep -i "error\|exception"

# Check Celery logs for task failures
docker compose -f docker-compose.prod.yml logs celery-worker-prod --tail=100 | grep -i "error\|exception\|failed"
```

**No errors should be present. If errors exist, investigate immediately.**

---

### Phase 6: Documentation and Cleanup

#### Step 6.1: Record Deployment Details

```bash
# Create deployment record
cat > deployment_log_$(date +%Y%m%d_%H%M%S).txt <<EOF
Deployment Date: $(date)
Deployed By: $(whoami)
Git Commit: $(git rev-parse HEAD)
Git Branch: $(git branch --show-current)
Migration Applied: $(docker exec labcastarr-backend-prod-1 uv run alembic current)
Backup Location: $BACKUP_DIR
Deployment Status: SUCCESS
Issues Encountered: None
Rollback Required: No
EOF

cat deployment_log_$(date +%Y%m%d_%H%M%S).txt
```

#### Step 6.2: Update Documentation

- [ ] Update `CHANGELOG.md` with deployment details
- [ ] Document any configuration changes
- [ ] Update API documentation if endpoints changed
- [ ] Note any breaking changes

#### Step 6.3: Notify Stakeholders

- [ ] Notify team deployment is complete
- [ ] Send deployment summary email/message
- [ ] Update status page (if applicable)
- [ ] Close maintenance window

#### Step 6.4: Backup Retention

```bash
# Keep last 10 backups, remove older ones
cd backups/
ls -t | tail -n +11 | xargs rm -rf

# Verify backup retention
ls -lh
```

---

## Rollback Procedure

### When to Rollback

Initiate rollback if:
- Migration fails with errors
- Database corruption detected
- Critical functionality broken
- Data loss detected
- Performance severely degraded
- Celery tasks failing consistently

### Rollback Steps

#### Step 1: Stop All Services Immediately

```bash
docker compose -f docker-compose.prod.yml down
```

#### Step 2: Restore Database from Backup

```bash
# Navigate to backup directory
cd /path/to/labcastarr

# Identify correct backup (from Phase 1)
BACKUP_DIR="backups/YYYYMMDD_HHMMSS"  # Use actual backup directory

# Stop any running containers
docker compose -f docker-compose.prod.yml down

# Remove current database
rm -f backend/data/labcastarr.db
rm -f backend/data/labcastarr.db-wal
rm -f backend/data/labcastarr.db-shm

# Restore database from backup
cp $BACKUP_DIR/labcastarr.db backend/data/labcastarr.db
cp $BACKUP_DIR/labcastarr.db-wal backend/data/labcastarr.db-wal 2>/dev/null || true
cp $BACKUP_DIR/labcastarr.db-shm backend/data/labcastarr.db-shm 2>/dev/null || true

# Verify restore
ls -lh backend/data/

# Verify database integrity
sqlite3 backend/data/labcastarr.db "PRAGMA integrity_check;"
```

**Expected Output:**
```
ok
```

#### Step 3: Rollback Code Changes

```bash
# Read previous commit from saved file
PREVIOUS_COMMIT=$(cat /tmp/previous_commit.txt)

# Checkout previous commit
git checkout $PREVIOUS_COMMIT

# Verify you're on correct commit
git log -1 --oneline
```

#### Step 4: Rollback Database Migration (If Partially Applied)

```bash
# Start backend container for migration rollback
docker compose --env-file .env.production -f docker-compose.prod.yml up -d backend-prod redis-prod

# Wait for container to start
sleep 10

# Connect to container and rollback migration
docker exec -it labcastarr-backend-prod-1 /bin/bash

# Inside container:
uv run alembic current  # Check current state
uv run alembic downgrade -1  # Rollback one migration
# Or: uv run alembic downgrade <previous_revision_id>

# Exit container
exit
```

#### Step 5: Restart All Services with Previous Version

```bash
# Rebuild containers with previous code
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d

# Monitor logs for errors
docker compose -f docker-compose.prod.yml logs -f
```

#### Step 6: Verify Rollback Success

```bash
# Check health endpoint
curl https://api.yourdomain.com/health/

# Check frontend
curl https://yourdomain.com

# Verify database record counts
docker exec labcastarr-backend-prod-1 sqlite3 /app/data/labcastarr.db "SELECT COUNT(*) FROM users;"
docker exec labcastarr-backend-prod-1 sqlite3 /app/data/labcastarr.db "SELECT COUNT(*) FROM episodes;"

# Test login functionality
curl -X POST https://api.yourdomain.com/v1/auth/login \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"email": "user@labcastarr.local", "password": "labcastarr123"}'
```

#### Step 7: Document Rollback

```bash
# Create rollback report
cat > rollback_report_$(date +%Y%m%d_%H%M%S).txt <<EOF
Rollback Date: $(date)
Rolled Back By: $(whoami)
Previous Commit: $PREVIOUS_COMMIT
Current Commit: $(git rev-parse HEAD)
Reason for Rollback: [DESCRIBE ISSUE]
Database Restored From: $BACKUP_DIR
Rollback Status: SUCCESS
Data Loss: None
Next Steps: [DESCRIBE INVESTIGATION NEEDED]
EOF

cat rollback_report_$(date +%Y%m%d_%H%M%S).txt
```

#### Step 8: Notify Team

- [ ] Alert team of rollback
- [ ] Share rollback report
- [ ] Schedule post-mortem meeting
- [ ] Document lessons learned

---

## Troubleshooting

### Issue: Migration Fails During Upgrade

**Symptoms:**
```
ERROR [alembic.util.messaging] Target database is not up to date.
```

**Solution:**
```bash
# Check current migration status
docker exec labcastarr-backend-prod-1 uv run alembic current

# Check migration history
docker exec labcastarr-backend-prod-1 uv run alembic history

# Manually apply specific migration
docker exec labcastarr-backend-prod-1 uv run alembic upgrade <revision_id>
```

---

### Issue: Database Locked Error

**Symptoms:**
```
sqlite3.OperationalError: database is locked
```

**Solution:**
```bash
# Stop all services accessing database
docker compose -f docker-compose.prod.yml down

# Wait for WAL checkpoint
sleep 5

# Check for stale WAL files
ls -lh backend/data/

# Checkpoint WAL manually
sqlite3 backend/data/labcastarr.db "PRAGMA wal_checkpoint(TRUNCATE);"

# Restart services
docker compose --env-file .env.production -f docker-compose.prod.yml up -d
```

---

### Issue: Health Check Failing

**Symptoms:**
```
unhealthy: Health check failed
```

**Solution:**
```bash
# Check health endpoint manually
docker exec labcastarr-backend-prod-1 curl http://localhost:8000/health/

# Check backend logs
docker compose -f docker-compose.prod.yml logs backend-prod --tail=50

# Common causes:
# 1. Migration still running (wait longer)
# 2. Database connection issues
# 3. Missing environment variables
# 4. Port conflict

# Verify environment variables
docker exec labcastarr-backend-prod-1 env | grep -E "DATABASE_URL|ENVIRONMENT"
```

---

### Issue: Celery Workers Not Starting

**Symptoms:**
```
Waiting for backend to become available...
```

**Solution:**
```bash
# Check if backend is healthy first
docker inspect labcastarr-backend-prod-1 | grep -A 5 Health

# Check Redis connection
docker exec labcastarr-redis-prod-1 redis-cli ping
# Should return: PONG

# Check Celery worker logs
docker compose -f docker-compose.prod.yml logs celery-worker-prod --tail=100

# Restart Celery workers
docker compose -f docker-compose.prod.yml restart celery-worker-prod celery-beat-prod
```

---

### Issue: Frontend Can't Connect to Backend

**Symptoms:**
```
Network error: Failed to fetch
```

**Solution:**
```bash
# Check if NEXT_PUBLIC_API_URL is correct
docker exec labcastarr-frontend-prod-1 env | grep NEXT_PUBLIC_API_URL

# Verify backend is accessible from frontend container
docker exec labcastarr-frontend-prod-1 curl http://backend-prod:8000/health/

# Check CORS settings in backend
docker exec labcastarr-backend-prod-1 env | grep CORS_ORIGINS

# Should include frontend URL
```

---

### Issue: Data Migration Caused Data Loss

**Symptoms:**
- Missing records after migration
- Null values where data should exist

**Solution:**
```bash
# IMMEDIATE: Stop services
docker compose -f docker-compose.prod.yml down

# Restore database from backup (see Rollback Procedure)
cp $BACKUP_DIR/labcastarr.db backend/data/labcastarr.db

# Investigate migration logic
cat backend/alembic/versions/<migration_file>.py

# Fix migration logic
# Test in pre-production
# Re-deploy with fixed migration
```

---

## Emergency Contacts

### Team Contacts

| Role | Name | Contact | Availability |
|------|------|---------|--------------|
| Primary Deployer | [Name] | [Email/Phone] | 24/7 |
| Backup Deployer | [Name] | [Email/Phone] | Business Hours |
| Database Admin | [Name] | [Email/Phone] | On-Call |
| DevOps Lead | [Name] | [Email/Phone] | 24/7 |

### Escalation Path

1. **Level 1:** Deployer attempts troubleshooting (15 minutes)
2. **Level 2:** Contact Backup Deployer (if Level 1 fails)
3. **Level 3:** Initiate rollback procedure (if Level 2 fails)
4. **Level 4:** Contact DevOps Lead for emergency support

---

## Appendix

### A. Pre-Deployment Record Template

```bash
# Run before deployment to record current state
cat > pre_deployment_$(date +%Y%m%d_%H%M%S).txt <<EOF
=== Pre-Deployment State ===
Date: $(date)
Git Commit: $(git rev-parse HEAD)
Git Branch: $(git branch --show-current)

=== Database State ===
Database Size: $(du -h backend/data/labcastarr.db | cut -f1)
Users Count: $(docker exec labcastarr-backend-prod-1 sqlite3 /app/data/labcastarr.db "SELECT COUNT(*) FROM users;" 2>/dev/null)
Channels Count: $(docker exec labcastarr-backend-prod-1 sqlite3 /app/data/labcastarr.db "SELECT COUNT(*) FROM channels;" 2>/dev/null)
Episodes Count: $(docker exec labcastarr-backend-prod-1 sqlite3 /app/data/labcastarr.db "SELECT COUNT(*) FROM episodes;" 2>/dev/null)

=== Migration State ===
Current Migration: $(docker exec labcastarr-backend-prod-1 uv run alembic current 2>/dev/null)

=== Container State ===
$(docker compose -f docker-compose.prod.yml ps)
EOF

cat pre_deployment_$(date +%Y%m%d_%H%M%S).txt
```

---

### B. Quick Reference Commands

```bash
# Backup database
cp backend/data/labcastarr.db backups/labcastarr_$(date +%Y%m%d_%H%M%S).db

# Check migration status
docker exec labcastarr-backend-prod-1 uv run alembic current

# Apply migrations manually
docker exec labcastarr-backend-prod-1 uv run alembic upgrade head

# Rollback one migration
docker exec labcastarr-backend-prod-1 uv run alembic downgrade -1

# Check database integrity
docker exec labcastarr-backend-prod-1 sqlite3 /app/data/labcastarr.db "PRAGMA integrity_check;"

# Health check
curl https://api.yourdomain.com/health/

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Restart services
docker compose -f docker-compose.prod.yml restart
```

---

### C. Post-Deployment Verification Checklist

Print this checklist and check off items during deployment:

```
□ Database backup created and verified
□ Backup stored offsite
□ Code pulled and verified
□ Migration applied successfully
□ Database integrity check passed
□ All containers running and healthy
□ Backend health endpoint responding
□ Frontend accessible
□ Login functionality working
□ Episode creation working
□ RSS feeds accessible
□ Audio playback working
□ No errors in logs
□ Celery workers processing tasks
□ Record counts match pre-deployment
□ New features working as expected
□ Deployment documented
□ Team notified
```

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-28 | LabCastARR Team | Initial SOP creation |

---

## Related Documents

- `CLAUDE.md` - Project overview and development guidelines
- `DEPLOYMENT.md` - General deployment documentation
- `backend/README.md` - Backend-specific documentation
- `backend/alembic/README` - Alembic migration documentation

---

**End of SOP**
