# Fix Docker Production Deployment Errors

## Issues Identified

From the Docker build error and log analysis, I've identified the following issues:

1. **Frontend Build Failures** (Critical - blocking deployment):

- Missing shadcn/ui component: `scroll-area`
- Missing hook: `use-toast`

2. **Database Migration** (Needs verification):

- Notification table migration `h9i0j1k2l3m4_add_notifications_table.py` exists but may not have been applied

3. **Backend Logs Analysis** (From previous run):

- Redis connection working correctly in logs
- No import errors detected
- Application starts successfully

## Fix Strategy

### Phase 1: Fix Frontend Missing Dependencies

**Issue**: The notification bell component imports `@/components/ui/scroll-area` and `@/hooks/use-toast` which don't exist.

**Files to create**:

- `frontend/src/components/ui/scroll-area.tsx` - Add shadcn scroll-area component
- `frontend/src/hooks/use-toast.ts` - Add shadcn toast hook
- `frontend/src/components/ui/toast.tsx` - Add shadcn toast component (required by use-toast)
- `frontend/src/components/ui/toaster.tsx` - Add shadcn toaster component

**Implementation**:

1. Create `scroll-area.tsx` component using shadcn/ui standard implementation
2. Create `toast.tsx` component using shadcn/ui standard implementation
3. Create `toaster.tsx` component using shadcn/ui standard implementation
4. Create `use-toast.ts` hook using shadcn/ui standard implementation
5. Update `frontend/src/app/layout.tsx` to include `<Toaster />` component

### Phase 2: Verify Database Migration

**Issue**: Need to ensure the notification table migration has been applied to the production database.

**Actions**:

1. Check if migration `h9i0j1k2l3m4` has been applied
2. If not applied, the migration will run automatically on container startup via Alembic

**Note**: The backend Dockerfile should include migration commands. If missing, we'll add them.

### Phase 3: Verify Backend Dockerfile

**Issue**: Ensure the backend Dockerfile runs database migrations on startup.

**Files to check**:

- `backend/Dockerfile` - Verify it runs Alembic migrations

**Actions**:

1. Check if Dockerfile includes `alembic upgrade head` command
2. If missing, add migration command to startup script

### Phase 4: Test Docker Build

**Actions**:

1. Build and start all containers with: `docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d`
2. Verify all services start successfully
3. Check logs for any errors
4. Verify frontend is accessible
5. Verify backend API is accessible
6. Verify database migrations applied
7. Verify Celery workers are running

## Files to Create/Modify

**Create**:

- `frontend/src/components/ui/scroll-area.tsx`
- `frontend/src/components/ui/toast.tsx`
- `frontend/src/components/ui/toaster.tsx`
- `frontend/src/hooks/use-toast.ts`

**Modify**:

- `frontend/src/app/layout.tsx` (add Toaster component)
- `backend/Dockerfile` (verify/add migration command if needed)

## Success Criteria

- [ ] Frontend builds successfully without errors
- [ ] All Docker containers start and remain running
- [ ] Database migrations applied successfully
- [ ] Frontend accessible at configured port
- [ ] Backend API accessible and responding
- [ ] Celery workers connected to Redis
- [ ] No errors in container logs
