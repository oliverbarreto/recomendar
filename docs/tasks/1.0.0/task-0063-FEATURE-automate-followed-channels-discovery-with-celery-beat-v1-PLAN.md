# Implementation Plan for Task 0063: FEATURE - PLAN: Automated Scheduled Video Discovery for Followed Channels

⏺ User approved Claude's plan
⎿  Plan saved to: ~/.claude/plans/greedy-hatching-fountain.md · /plan to edit
Implementation Plan: Automated Scheduled Video Discovery for Followed Channels

Overview

Implement automated scheduled checks for ALL followed YouTube channels to discover new videos using the RSS method. The system will run at a fixed UTC time daily or
weekly based on user preferences, and track whether checks were user-initiated or system-initiated.

Requirements Summary

1. Automated Scheduled Checks: Check ALL followed channels for new videos on schedule (daily or weekly)
2. Discovery Method: Always use RSS method (5-10s per channel, last 10-15 videos)
3. User Settings:

- Check frequency: Daily or Weekly (remove "Twice Weekly" option)
- Preferred check time: Hour and minute selection in UTC (default 02:00)

4. Execution Tracking: Add "executed_by" field to notifications to distinguish user vs system triggers
5. Activity Page: Display "Executed By" column showing "User" or "System"
6. Auto-Approve Integration: Existing auto-approve feature works for both manual and scheduled checks

Architecture Decisions

- Fixed UTC Time: All users checked at same configured time (initially 2 AM UTC)
- Database-Driven Scheduling: Celery Beat task queries database for users needing checks
- RSS Method Only: Fast and efficient for automated checks
- Backward Compatible: Existing manual check functionality unchanged
- Clean Architecture: Follow existing domain/application/infrastructure/presentation layers

---

Phase 1: Database Schema Changes

Task 1.1: Add executed_by to notifications table

Create Migration: backend/alembic/versions/xxx_add_executed_by_to_notifications.py

# Add column to notifications table

def upgrade():
op.add_column('notifications',
sa.Column('executed_by', sa.String(20), server_default='user', nullable=False)
) # Create index for filtering
op.create_index('ix_notifications_executed_by', 'notifications', ['executed_by'])

def downgrade():
op.drop_index('ix_notifications_executed_by', 'notifications')
op.drop_column('notifications', 'executed_by')

Values: 'user' (manual trigger) or 'system' (scheduled trigger)

Task 1.2: Update user_settings table for time preferences

Create Migration: backend/alembic/versions/xxx_add_check_time_to_user_settings.py

def upgrade(): # Remove TWICE_WEEKLY from enum (requires enum recreation in SQLite) # Add preferred check time fields
op.add_column('user_settings',
sa.Column('preferred_check_hour', sa.Integer, server_default='2', nullable=False)
)
op.add_column('user_settings',
sa.Column('preferred_check_minute', sa.Integer, server_default='0', nullable=False)
) # Update existing TWICE_WEEKLY to DAILY
op.execute("UPDATE user_settings SET subscription_check_frequency = 'DAILY' WHERE subscription_check_frequency = 'TWICE_WEEKLY'")

def downgrade():
op.drop_column('user_settings', 'preferred_check_minute')
op.drop_column('user_settings', 'preferred_check_hour')

Files to Modify:

- backend/alembic/versions/ - Create 2 new migration files
- Run migrations: cd backend && uv run alembic upgrade head

---

Phase 2: Domain Layer Updates

Task 2.1: Update Notification entity

File: backend/app/domain/entities/notification.py

Changes:

- Add executed_by: str field to Notification dataclass
- Update factory methods to accept executed_by parameter
- Add validation for executed_by values ('user' or 'system')

Task 2.2: Update UserSettings entity

File: backend/app/domain/entities/user_settings.py

Changes:

- Add preferred_check_hour: int field (0-23)
- Add preferred_check_minute: int field (0-59)
- Update SubscriptionCheckFrequency enum to remove TWICE_WEEKLY
- Add validation for hour/minute ranges

---

Phase 3: Application Layer Updates

Task 3.1: Update NotificationService

File: backend/app/application/services/notification_service.py

Changes:

- Update notification creation methods to accept executed_by parameter:
  - notify_channel_search_started(user_id, channel_name, followed_channel_id, executed_by='user')
  - notify_channel_search_completed(user_id, channel_name, followed_channel_id, new_videos_count, total_videos_count, executed_by='user')
  - notify_channel_search_error(user_id, channel_name, followed_channel_id, error_message, executed_by='user')
- Pass executed_by to repository when creating notifications
- Default to 'user' for backward compatibility

Task 3.2: Update UserSettingsService

File: backend/app/application/services/user_settings_service.py

Changes:

- Add methods to update check time preferences:
  - update_check_time(user_id, hour, minute)
- Update get_user_settings() to include new fields
- Add validation for hour (0-23) and minute (0-59)
- Handle default creation with preferred_check_hour=2, preferred_check_minute=0

---

Phase 4: Infrastructure Layer Updates

Task 4.1: Update Notification database model

File: backend/app/infrastructure/database/models/notification.py

Changes:
class NotificationModel(Base):
**tablename** = "notifications" # ... existing fields ...
executed_by = Column(String(20), nullable=False, server_default='user', index=True)

Task 4.2: Update UserSettings database model

File: backend/app/infrastructure/database/models/user_settings.py

Changes:
class UserSettingsModel(Base):
**tablename** = "user_settings" # Update enum
subscription_check_frequency = Column(Enum('DAILY', 'WEEKLY', name='subscription_check_frequency_enum'), ...) # Add new fields
preferred_check_hour = Column(Integer, nullable=False, server_default='2')
preferred_check_minute = Column(Integer, nullable=False, server_default='0')

Task 4.3: Update RSS check task to accept executed_by parameter

File: backend/app/infrastructure/tasks/channel_check_rss_tasks.py

Changes:
@shared_task(bind=True, autoretry_for=(ConnectionError, TimeoutError))
def check_followed_channel_for_new_videos_rss(
self,
followed_channel_id: int,
executed_by: str = 'user' # NEW PARAMETER
): # Pass executed_by to all notification service calls
await notification_service.notify_channel_search_started(
user_id=followed_channel.user_id,
channel_name=followed_channel.youtube_channel_name,
followed_channel_id=followed_channel.id,
executed_by=executed_by # PASS THROUGH
) # ... repeat for completed and error notifications

Task 4.4: Create new scheduled check task

File: backend/app/infrastructure/tasks/channel_check_tasks.py

New Function:
@shared_task(name="scheduled_check_all_channels_rss")
def scheduled_check_all_channels_rss():
"""
Scheduled task to check all followed channels for new videos using RSS method.
Runs at configured time and checks channels based on user frequency preferences.
""" # 1. Get all users # 2. For each user, get their check frequency preference # 3. Calculate threshold based on frequency (daily=24h, weekly=7d) # 4. Query followed channels not checked since threshold # 5. Queue check_followed_channel_for_new_videos_rss with executed_by='system' # 6. Log statistics

Implementation Details:

- Query all users from database
- For each user:
  - Get subscription_check_frequency from user_settings
  - Calculate last_check_before threshold:
    - DAILY: now - 24 hours
    - WEEKLY: now - 7 days
  - Query followed_channels where last_checked < threshold OR last_checked IS NULL
  - Queue check_followed_channel_for_new_videos_rss.apply_async(args=(channel.id,), kwargs={'executed_by': 'system'})
- Return summary with stats

Task 4.5: Update Celery Beat schedule

File: backend/app/infrastructure/celery_beat_schedule.py

Changes:
beat_schedule = {
'scheduled-check-all-channels-rss': {
'task': 'scheduled_check_all_channels_rss',
'schedule': crontab(hour=2, minute=0), # 2 AM UTC daily
'options': {'queue': 'channel_checks'},
},
}

Note: Remove or comment out old periodic_check_all_channels task that uses yt-dlp method

Task 4.6: Update NotificationRepository implementation

File: backend/app/infrastructure/repositories/notification_repository_impl.py

Changes:

- Update create() method to handle executed_by field
- Ensure executed_by is mapped when converting from model to entity

---

Phase 5: Presentation Layer Updates

Task 5.1: Update Notification schemas

File: backend/app/presentation/schemas/notification_schemas.py

Changes:
class NotificationResponse(BaseModel):
id: int
user_id: int
type: NotificationType
title: str
message: str
data_json: Dict[str, Any] = Field(default_factory=dict, alias="dataJson")
read: bool
executed_by: str # NEW FIELD
created_at: datetime = Field(alias="createdAt")
updated_at: Optional[datetime] = Field(None, alias="updatedAt")

Task 5.2: Update UserSettings schemas

File: backend/app/presentation/schemas/user_settings_schemas.py

Changes:
class SubscriptionCheckFrequencyEnum(str, Enum):
DAILY = "DAILY"
WEEKLY = "WEEKLY" # Remove TWICE_WEEKLY

class UserSettingsResponse(BaseModel):
subscription_check_frequency: SubscriptionCheckFrequencyEnum
preferred_check_hour: int # NEW FIELD
preferred_check_minute: int # NEW FIELD

class UserSettingsUpdateRequest(BaseModel):
subscription_check_frequency: Optional[SubscriptionCheckFrequencyEnum]
preferred_check_hour: Optional[int] # NEW FIELD (0-23)
preferred_check_minute: Optional[int] # NEW FIELD (0-59)

Task 5.3: Update user settings API endpoint

File: backend/app/presentation/api/v1/users.py

Changes:

- Update PUT /users/settings endpoint to accept and validate new time fields
- Add validation: hour in [0, 23], minute in [0, 59]
- Pass new fields to UserSettingsService

---

Phase 6: Frontend Updates

Task 6.1: Update TypeScript types

File: frontend/src/types/index.ts

Changes:
export enum SubscriptionCheckFrequency {
DAILY = 'DAILY',
WEEKLY = 'WEEKLY',
// Remove TWICE_WEEKLY
}

export interface UserSettings {
subscriptionCheckFrequency: SubscriptionCheckFrequency;
preferredCheckHour: number; // NEW
preferredCheckMinute: number; // NEW
}

export interface Notification {
id: number;
userId: number;
type: NotificationType;
title: string;
message: string;
dataJson?: Record<string, any>;
read: boolean;
executedBy: string; // NEW: 'user' or 'system'
createdAt: string;
updatedAt?: string;
}

Task 6.2: Update Settings UI - Subscriptions tab

File: frontend/src/components/features/settings/settings-interface.tsx

Changes (lines 1275-1363):

1. Remove "Twice Weekly" option from frequency dropdown
2. Add time picker for preferred check time:

- Use shadcn Select components for hour and minute
- Hour: 00-23 (24-hour format)
- Minute: 00-59
- Display in format "HH:MM UTC"

3. Update state management:
   const [checkFrequency, setCheckFrequency] = useState<SubscriptionCheckFrequency>('DAILY');
   const [checkHour, setCheckHour] = useState<number>(2);
   const [checkMinute, setCheckMinute] = useState<number>(0);
4. Update save handler to include new fields
5. Update help text to clarify fixed UTC time for all users

UI Layout:
Subscription Settings
Configure how often the system checks for new videos from followed channels

Check Frequency
[Dropdown: Daily / Weekly]

Preferred Check Time (UTC)
[Hour Select: 00-23] : [Minute Select: 00-59]

Note: All checks run at the same time for all users. This time is in UTC.
Daily checks run every day, and weekly checks run once per week.

Task 6.3: Update Activity table component

File: frontend/src/components/features/activity/activity-table.tsx

Changes:

1. Add new "Executed By" column after "Channel" column
2. Render badge based on executedBy value:
   {notification.executedBy === 'system' ? (
   <Badge variant="secondary" className="bg-purple-100 text-purple-800">
   System
   </Badge>
   ) : (
   <Badge variant="secondary" className="bg-blue-100 text-blue-800">
   User
   </Badge>
   )}
3. Update table headers array
4. Adjust column widths for new column

New Column Structure:
| Type | Channel | Executed By | Date | Time | Description | Actions |

Task 6.4: Update API client

File: frontend/src/lib/api.ts or frontend/src/lib/api-client.ts

Changes:

- Update updateUserSettings method to accept new time fields:
  updateUserSettings(data: {
  subscription_check_frequency?: SubscriptionCheckFrequency;
  preferred_check_hour?: number;
  preferred_check_minute?: number;
  })

---

Phase 7: Testing and Validation

Task 7.1: Backend testing

- Test database migrations (up and down)
- Test new scheduled task runs successfully
- Test RSS check task accepts and passes through executed_by
- Test notifications have correct executed_by value
- Test user settings API with new time fields
- Validate hour/minute range validation works

Task 7.2: Frontend testing

- Test settings UI displays time picker correctly
- Test saving settings with new time fields
- Test activity table displays "Executed By" column
- Test badge colors (blue for user, purple for system)
- Test frequency dropdown only shows Daily/Weekly
- Test time format displays correctly (HH:MM UTC)

Task 7.3: Integration testing

- Trigger manual check → verify executed_by='user' in notification
- Wait for scheduled check → verify executed_by='system' in notification
- Verify both types appear correctly in activity table
- Test auto-approve works for both manual and scheduled checks
- Test all followed channels are checked (not just auto-approve)
- Verify daily vs weekly frequency works correctly

Task 7.4: Performance testing

- Test with multiple users and multiple followed channels
- Measure RSS check performance (should be 5-10s per channel)
- Verify task queueing doesn't overwhelm system
- Check database query performance with indexes

---

Phase 8: Documentation and Deployment

Task 8.1: Update documentation

File: CLAUDE.md

- Document new scheduled check feature
- Update settings section with time preference
- Document executed_by field in notifications
- Update activity page documentation

File: docs/documentation/TECHNICAL-ANALYSIS-FEATURE-follow-channels-architecture.md

- Add section on scheduled checks
- Document new Celery task
- Update notification schema documentation

Task 8.2: Create migration guide

Create docs/tasks/task-0060-FEATURE-automated-scheduled-video-discovery.md:

- Feature overview
- Migration steps for database
- Configuration changes
- Testing checklist
- Rollback procedure

Task 8.3: Deployment checklist

1. Run database migrations (both migrations)
2. Restart backend services to load new Celery Beat schedule
3. Restart Celery workers
4. Restart Celery Beat scheduler
5. Verify scheduled task appears in Celery Beat logs
6. Test manual check still works
7. Monitor first scheduled check execution
8. Verify notifications have correct executed_by values
9. Check activity page displays correctly

---

Critical Files Summary

Backend Files to Modify:

1. backend/alembic/versions/ - 2 new migration files
2. backend/app/domain/entities/notification.py - Add executed_by
3. backend/app/domain/entities/user_settings.py - Add time fields, update enum
4. backend/app/application/services/notification_service.py - Add executed_by parameter
5. backend/app/application/services/user_settings_service.py - Add time field methods
6. backend/app/infrastructure/database/models/notification.py - Add executed_by column
7. backend/app/infrastructure/database/models/user_settings.py - Add time columns, update enum
8. backend/app/infrastructure/tasks/channel_check_rss_tasks.py - Add executed_by parameter
9. backend/app/infrastructure/tasks/channel_check_tasks.py - Create new scheduled task
10. backend/app/infrastructure/celery_beat_schedule.py - Update schedule
11. backend/app/infrastructure/repositories/notification_repository_impl.py - Handle executed_by
12. backend/app/presentation/schemas/notification_schemas.py - Add executed_by field
13. backend/app/presentation/schemas/user_settings_schemas.py - Add time fields, update enum
14. backend/app/presentation/api/v1/users.py - Update settings endpoint

Frontend Files to Modify:

1. frontend/src/types/index.ts - Update types
2. frontend/src/components/features/settings/settings-interface.tsx - Add time picker
3. frontend/src/components/features/activity/activity-table.tsx - Add "Executed By" column
4. frontend/src/lib/api.ts or frontend/src/lib/api-client.ts - Update API methods

Documentation Files:

1. CLAUDE.md - Update feature documentation
2. docs/documentation/TECHNICAL-ANALYSIS-FEATURE-follow-channels-architecture.md - Add scheduled checks
3. docs/tasks/task-0060-FEATURE-automated-scheduled-video-discovery.md - Implementation log

---

Implementation Order

Execute phases sequentially:

1. Phase 1 (Database) - Must be first
2. Phase 2 (Domain) - After database
3. Phase 3 (Application) - After domain
4. Phase 4 (Infrastructure) - After application
5. Phase 5 (Presentation/API) - After infrastructure
6. Phase 6 (Frontend) - After API
7. Phase 7 (Testing) - After all code changes
8. Phase 8 (Documentation) - Final phase

Key Dependencies:

- Migrations must run before any code uses new fields
- Backend changes must be complete before frontend changes
- Celery workers must restart after task changes
- Celery Beat must restart after schedule changes

---

Risk Mitigation

1. Backward Compatibility: Default executed_by='user' ensures existing code works
2. Data Migration: Convert TWICE_WEEKLY to DAILY automatically
3. Gradual Rollout: Manual checks work unchanged while scheduled checks are added
4. Monitoring: Log scheduled task execution for observability
5. Rollback: Both migrations have downgrade functions

Success Criteria

- Database migrations run successfully
- Settings page allows time selection (HH:MM UTC)
- Scheduled task runs at configured time
- All followed channels checked (RSS method)
- Notifications show correct executed_by value
- Activity page displays "Executed By" column with color-coded badges
- Manual checks show "User", scheduled checks show "System"
- Auto-approve creates episodes for both trigger types
- Performance remains acceptable (5-10s per channel)
- No breaking changes to existing functionality
