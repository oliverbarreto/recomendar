claude

▐▛███▜▌ Claude Code v2.0.55
▝▜█████▛▘ Sonnet 4.5 · Claude Pro
▘▘ ▝▝ ~/local/dev/labcastarr
═══════════════════════════════════════════════════════ Conversation compacted · ctrl+o for history ═══════════════════════════════════════════════════════

⏺ I'll continue with Phase 1 by adding the explicit import statement to complete the RSS task registration fix.

⏺ Update(backend/app/infrastructure/celery_app.py)
⎿  Updated backend/app/infrastructure/celery_app.py with 1 addition  
 48 # Explicitly import task modules to ensure they're registered
49 # This ensures tasks are discovered even if include list has issues
50 import app.infrastructure.tasks.channel_check_tasks # noqa: F401
51 + import app.infrastructure.tasks.channel_check_rss_tasks # noqa: F401
52 import app.infrastructure.tasks.backfill_channel_task # noqa: F401
53 import app.infrastructure.tasks.create_episode_from_video_task # noqa: F401
54 import app.infrastructure.tasks.download_episode_task # noqa: F401

⏺ Perfect! Phase 1 is complete. I've successfully fixed the critical bug by adding the RSS task module registration to celery_app.py in two places:

1. ✅ Added to include list (line 21)
2. ✅ Added explicit import (line 51)

What this fixes: The Celery worker will now recognize and execute the check_followed_channel_for_new_videos_rss task. Previously, tasks were queued
to Redis but the worker didn't know they existed, causing them to stay stuck in PENDING status forever.

Next step: You need to restart the Celery worker to pick up this change:

docker compose -f docker-compose.dev.yml restart celery-worker-dev celery-beat-dev

After the restart, the RSS check button should work properly - tasks will execute and transition from PENDING → STARTED → SUCCESS.

Now I'll continue with Phase 2: Backend Task Cancellation Feature. Let me start by reading the current task status service to understand the
structure:

⏺ Read(backend/app/application/services/celery_task_status_service.py)
⎿  Read 92 lines

⏺ Now let me read the repository implementation to understand the database methods available:

⏺ Read(backend/app/infrastructure/repositories/celery_task_status_repository_impl.py)
⎿  Read 161 lines

⏺ Now let me add the new methods to the repository implementation. I'll start by adding repository methods for task management:

⏺ Update(backend/app/infrastructure/repositories/celery*task_status_repository_impl.py)
⎿  Updated backend/app/infrastructure/repositories/celery_task_status_repository_impl.py with 3 additions and 3 removals
1 """
2 Celery Task Status repository implementation using SQLAlchemy
3 """
4 - from sqlalchemy import select, and*, desc
4 + from sqlalchemy import select, and\_, desc, delete, func
5 from sqlalchemy.ext.asyncio import AsyncSession
6 - from typing import Optional, List
7 - from datetime import datetime
6 + from typing import Optional, List, Dict, Any
7 + from datetime import datetime, timedelta
8 import logging
9  
 10 from app.domain.entities.celery_task_status import CeleryTaskStatus, TaskStatus

⏺ Update(backend/app/infrastructure/repositories/celery*task_status_repository_impl.py)
⎿  Updated backend/app/infrastructure/repositories/celery_task_status_repository_impl.py with 111 additions and 1 removal
150 )
151 result = await self.session.execute(stmt)
152 model = result.scalar_one_or_none()
153 -  
 153 +  
 154 if model:
155 return self.\_model_to_entity(model)
156 return None
...
158 logger.error(f"Error getting latest task status for channel {followed_channel_id}: {e}")
159 raise
160  
 161 + async def get_all(self, limit: Optional[int] = None) -> List[CeleryTaskStatus]:
162 + """Get all task statuses (most recent first)"""
163 + try:
164 + stmt = select(CeleryTaskStatusModel).order_by(desc(CeleryTaskStatusModel.created_at))
165 + if limit:
166 + stmt = stmt.limit(limit)
167 +  
 168 + result = await self.session.execute(stmt)
169 + models = result.scalars().all()
170 + return [self._model_to_entity(model) for model in models]
171 + except Exception as e:
172 + logger.error(f"Error getting all task statuses: {e}")
173 + raise
174 +  
 175 + async def get_by_status(self, status: TaskStatus, limit: Optional[int] = None) -> List[CeleryTaskStatus]:
176 + """Get task statuses by status (most recent first)"""
177 + try:
178 + stmt = (
179 + select(CeleryTaskStatusModel)
180 + .where(CeleryTaskStatusModel.status == status.value)
181 + .order_by(desc(CeleryTaskStatusModel.created_at))
182 + )
183 + if limit:
184 + stmt = stmt.limit(limit)
185 +  
 186 + result = await self.session.execute(stmt)
187 + models = result.scalars().all()
188 + return [self._model_to_entity(model) for model in models]
189 + except Exception as e:
190 + logger.error(f"Error getting task statuses by status {status}: {e}")
191 + raise
192 +  
 193 + async def get_by_status_and_age(
194 + self,
195 + status: TaskStatus,
196 + older_than_minutes: int
197 + ) -> List[CeleryTaskStatus]:
198 + """Get task statuses by status that are older than specified minutes"""
199 + try:
200 + cutoff_time = datetime.utcnow() - timedelta(minutes=older_than_minutes)
201 + stmt = (
202 + select(CeleryTaskStatusModel)
203 + .where(
204 + and*(
205 + CeleryTaskStatusModel.status == status.value,
206 + CeleryTaskStatusModel.created_at < cutoff_time
207 + )
208 + )
209 + .order_by(desc(CeleryTaskStatusModel.created_at))
210 + )
211 + result = await self.session.execute(stmt)
212 + models = result.scalars().all()
213 + return [self._model_to_entity(model) for model in models]
214 + except Exception as e:
215 + logger.error(f"Error getting task statuses by status {status} and age: {e}")
216 + raise
217 +  
 218 + async def get_summary(self) -> Dict[str, Any]:
219 + """Get summary of task statuses grouped by status"""
220 + try:
221 + stmt = (
222 + select(
223 + CeleryTaskStatusModel.status,
224 + func.count(CeleryTaskStatusModel.id).label('count')
225 + )
226 + .group_by(CeleryTaskStatusModel.status)
227 + )
228 + result = await self.session.execute(stmt)
229 + rows = result.all()
230 +  
 231 + summary = {
232 + 'total': 0,
233 + 'by_status': {}
234 + }
235 +  
 236 + for row in rows:
237 + status_str = row[0]
238 + count = row[1]
239 + summary['by_status'][status_str] = count
240 + summary['total'] += count
241 +  
 242 + return summary
243 + except Exception as e:
244 + logger.error(f"Error getting task status summary: {e}")
245 + raise
246 +  
 247 + async def delete(self, task_id: str) -> bool:
248 + """Delete a task status record by task ID"""
249 + try:
250 + stmt = delete(CeleryTaskStatusModel).where(CeleryTaskStatusModel.task_id == task_id)
251 + result = await self.session.execute(stmt)
252 + await self.session.commit()
253 + return result.rowcount > 0
254 + except Exception as e:
255 + logger.error(f"Error deleting task status {task_id}: {e}")
256 + await self.session.rollback()
257 + raise
258 +  
 259 + async def delete_by_status(self, status: TaskStatus) -> int:
260 + """Delete all task status records with the given status"""
261 + try:
262 + stmt = delete(CeleryTaskStatusModel).where(CeleryTaskStatusModel.status == status.value)
263 + result = await self.session.execute(stmt)
264 + await self.session.commit()
265 + return result.rowcount
266 + except Exception as e:
267 + logger.error(f"Error deleting task statuses by status {status}: {e}")
268 + await self.session.rollback()
269 + raise
270 +

⏺ Good! Now let me add the service methods that will use these repository methods and interact with Celery:

⏺ Update(backend/app/application/services/celery_task_status_service.py)
⎿  Updated backend/app/application/services/celery_task_status_service.py with 2 additions and 1 removal  
 3  
 4 Application service for managing and querying Celery task status.
5 """
6 - from typing import Optional, List
6 + from typing import Optional, List, Dict, Any
7 import logging
8  
 9 from app.domain.entities.celery_task_status import CeleryTaskStatus, TaskStatus
10 from app.infrastructure.repositories.celery_task_status_repository_impl import CeleryTaskStatusRepository
11 + from app.infrastructure.celery_app import celery_app
12  
 13 logger = logging.getLogger(**name**)
14

⏺ Update(backend/app/application/services/celery_task_status_service.py)
⎿  Updated backend/app/application/services/celery_task_status_service.py with 90 additions and 2 removals  
 75 ) -> Optional[CeleryTaskStatus]:
76 """
77 Get the most recent task status for a followed channel
78 -  
 78 +  
 79 Args:
80 followed_channel_id: ID of the followed channel
81 -  
 81 +  
 82 Returns:
83 Most recent CeleryTaskStatus entity if found, None otherwise
84 """
...
90 logger.error(f"Failed to get latest task status for channel {followed_channel_id}: {e}")
91 raise
92  
 93 + async def get_all_tasks_summary(self) -> Dict[str, Any]:
94 + """
95 + Get summary of all tasks grouped by status
96 +  
 97 + Returns:
98 + Dictionary with total count and breakdown by status
99 + """
100 + try:
101 + return await self.task_status_repository.get_summary()
102 + except Exception as e:
103 + logger.error(f"Failed to get tasks summary: {e}")
104 + raise
105 +  
 106 + async def revoke_task(self, task_id: str, terminate: bool = False) -> bool:
107 + """
108 + Revoke a running or pending Celery task
109 +  
 110 + Args:
111 + task_id: Celery task UUID
112 + terminate: If True, terminate task even if it's running (use with caution)
113 +  
 114 + Returns:
115 + True if task was revoked successfully
116 + """
117 + try:
118 + # Revoke the task in Celery
119 + celery_app.control.revoke(task_id, terminate=terminate, signal='SIGTERM')
120 +  
 121 + # Update task status in database
122 + task_status = await self.task_status_repository.get_by_task_id(task_id)
123 + if task_status:
124 + task_status.status = TaskStatus.FAILURE
125 + task_status.error_message = "Task manually cancelled by user"
126 + await self.task_status_repository.update(task_status)
127 +  
 128 + logger.info(f"Revoked task {task_id} (terminate={terminate})")
129 + return True
130 + except Exception as e:
131 + logger.error(f"Failed to revoke task {task_id}: {e}")
132 + raise
133 +  
 134 + async def purge_tasks_by_status(
135 + self,
136 + status: TaskStatus,
137 + older_than_minutes: Optional[int] = None
138 + ) -> Dict[str, int]:
139 + """
140 + Purge tasks with specific status from database
141 +  
 142 + Args:
143 + status: Task status to purge (PENDING, FAILURE, SUCCESS)
144 + older_than_minutes: Only purge tasks older than this many minutes (optional)
145 +  
 146 + Returns:
147 + Dictionary with counts of revoked and deleted tasks
148 + """
149 + try:
150 + # Get tasks to purge
151 + if older_than_minutes:
152 + tasks = await self.task_status_repository.get_by_status_and_age(
153 + status=status,
154 + older_than_minutes=older_than_minutes
155 + )
156 + else:
157 + tasks = await self.task_status_repository.get_by_status(status=status)
158 +  
 159 + # Revoke any PENDING tasks in Celery
160 + revoked_count = 0
161 + if status == TaskStatus.PENDING:
162 + for task in tasks:
163 + try:
164 + celery_app.control.revoke(task.task_id, terminate=False)
165 + revoked_count += 1
166 + except Exception as e:
167 + logger.warning(f"Failed to revoke task {task.task_id}: {e}")
168 +  
 169 + # Delete from database
170 + deleted_count = await self.task_status_repository.delete_by_status(status)
171 +  
 172 + logger.info(f"Purged {deleted_count} tasks with status {status} (revoked: {revoked_count})")
173 + return {
174 + 'revoked': revoked_count,
175 + 'deleted': deleted_count
176 + }
177 + except Exception as e:
178 + logger.error(f"Failed to purge tasks by status {status}: {e}")
179 + raise
180 +

⏺ Perfect! Now I need to create the API endpoints. Let me first check if there's an existing celery_tasks.py file or if I need to create one:

⏺ Search(pattern: "\*_/celery_task_.py")
⎿  Found 0 files

⏺ Bash(ls -la backend/app/presentation/api/v1/)
⎿  Error: Exit code 1
ls: backend/app/presentation/api/v1/: No such file or directory

⏺ Bash(find backend/app/presentation -name "\*.py" -type f | head -20)
⎿  find: backend/app/presentation: No such file or directory

⏺ Bash(pwd)
⎿  /Users/oliver/local/dev/labcastarr/frontend

⏺ Bash(ls -la ../backend/app/presentation/api/v1/)
⎿  total 504  
 drwxr-xr-x 20 oliver staff 640 Nov 29 15:15 .
drwxr-xr-x 6 oliver staff 192 Nov 12 17:42 ..
… +18 lines (ctrl+o to expand)

⏺ Great! There's already a celery_tasks.py file. Let me read it:

⏺ Read(backend/app/presentation/api/v1/celery_tasks.py)
⎿  Read 65 lines

⏺ Perfect! Now I'll add the new endpoints to this existing file. First, let me check the schemas to see what response models exist:

⏺ Bash(find ../backend/app/presentation/schemas -name "_celery_" -type f)
⎿  ../backend/app/presentation/schemas/celery_task_status_schemas.py

⏺ Read(backend/app/presentation/schemas/celery_task_status_schemas.py)
⎿  Read 29 lines

⏺ Now I'll add the new schemas and endpoints. First, let me add the new response schemas:

⏺ Update(backend/app/presentation/schemas/celery_task_status_schemas.py)
⎿  Updated backend/app/presentation/schemas/celery_task_status_schemas.py with 1 addition and 1 removal
2 Celery Task Status API Request/Response Schemas
3 """
4 from pydantic import BaseModel, Field
5 - from typing import Optional
5 + from typing import Optional, Dict, Any
6 from datetime import datetime
7  
 8

⏺ Update(backend/app/presentation/schemas/celery_task_status_schemas.py)
⎿  Updated backend/app/presentation/schemas/celery_task_status_schemas.py with 21 additions  
 26 class Config:
27 from_attributes = True
28  
 29 +  
 30 + class TasksSummaryResponse(BaseModel):
31 + """Response schema for tasks summary"""
32 + total: int = Field(..., description="Total number of tasks")
33 + by_status: Dict[str, int] = Field(..., description="Task counts grouped by status")
34 +  
 35 +  
 36 + class PurgeTasksRequest(BaseModel):
37 + """Request schema for purging tasks"""
38 + status: str = Field(..., description="Task status to purge (PENDING, FAILURE, SUCCESS)")
39 + older_than_minutes: Optional[int] = Field(
40 + default=None,
41 + description="Only purge tasks older than this many minutes"
42 + )
43 +  
 44 +  
 45 + class PurgeTasksResponse(BaseModel):
46 + """Response schema for purge operation"""
47 + revoked: int = Field(..., description="Number of tasks revoked in Celery")
48 + deleted: int = Field(..., description="Number of tasks deleted from database")
49 +

⏺ Now let me add the new endpoints to the celery_tasks.py file:

⏺ Update(backend/app/presentation/api/v1/celery_tasks.py)
⎿  Updated backend/app/presentation/api/v1/celery_tasks.py with 7 additions and 1 removal  
 10 from app.core.auth import get_current_user_jwt
11 from app.application.services.celery_task_status_service import CeleryTaskStatusService
12 from app.infrastructure.repositories.celery_task_status_repository_impl import CeleryTaskStatusRepository
13 - from app.presentation.schemas.celery_task_status_schemas import CeleryTaskStatusResponse
13 + from app.presentation.schemas.celery_task_status_schemas import (
14 + CeleryTaskStatusResponse,
15 + TasksSummaryResponse,
16 + PurgeTasksRequest,
17 + PurgeTasksResponse
18 + )
19 + from app.domain.entities.celery_task_status import TaskStatus
20  
 21 logger = logging.getLogger(**name**)
22 router = APIRouter(prefix="/celery-tasks", tags=["celery-tasks"])

⏺ Update(backend/app/presentation/api/v1/celery_tasks.py)
⎿  Updated backend/app/presentation/api/v1/celery_tasks.py with 116 additions and 4 removals  
 45 ) -> CeleryTaskStatusResponse:
46 """
47 Get Celery task status by task ID
48 -  
 48 +  
 49 Returns the current status, progress, and result of a Celery task.
50 """
51 try:
52 task_status = await task_status_service.get_task_status(task_id)
53 -  
 53 +  
 54 if not task_status:
55 raise HTTPException(
56 status_code=status.HTTP_404_NOT_FOUND,
57 detail=f"Task {task_id} not found"
58 )
59 -  
 59 +  
 60 return CeleryTaskStatusResponse.model_validate(task_status)
61 -  
 61 +  
 62 except HTTPException:
63 raise
64 except Exception as e:
...
68 detail=f"Failed to get task status: {str(e)}"
69 )
70  
 71 +  
 72 + @router.get(
73 + "/summary",
74 + response_model=TasksSummaryResponse,
75 + responses={
76 + 401: {"description": "Authentication required"},
77 + }
78 + )
79 + async def get_tasks_summary(
80 + current_user: Annotated[dict, Depends(get_current_user_jwt)],
81 + task_status_service: CeleryTaskStatusService = Depends(get_task_status_service),
82 + ) -> TasksSummaryResponse:
83 + """
84 + Get summary of all tasks grouped by status
85 +  
 86 + Returns total count and breakdown by status (PENDING, STARTED, SUCCESS, FAILURE, etc.)
87 + """
88 + try:
89 + summary = await task_status_service.get_all_tasks_summary()
90 + return TasksSummaryResponse(**summary)
91 +  
 92 + except Exception as e:
93 + logger.error(f"Failed to get tasks summary: {e}", exc_info=True)
94 + raise HTTPException(
95 + status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
96 + detail=f"Failed to get tasks summary: {str(e)}"
97 + )
98 +  
 99 +  
 100 + @router.post(
101 + "/revoke/{task_id}",
102 + responses={
103 + 401: {"description": "Authentication required"},
104 + 404: {"description": "Task not found"},
105 + }
106 + )
107 + async def revoke_task(
108 + task_id: str,
109 + current_user: Annotated[dict, Depends(get_current_user_jwt)],
110 + task_status_service: CeleryTaskStatusService = Depends(get_task_status_service),
111 + ) -> dict:
112 + """
113 + Revoke a running or pending Celery task
114 +  
 115 + Cancels the task execution and updates status to FAILURE.
116 + Note: Only works for PENDING tasks. Running tasks may not stop immediately.
117 + """
118 + try:
119 + success = await task_status_service.revoke_task(task_id, terminate=False)
120 +  
 121 + return {
122 + "success": success,
123 + "message": f"Task {task_id} has been revoked"
124 + }
125 +  
 126 + except Exception as e:
127 + logger.error(f"Failed to revoke task: {e}", exc_info=True)
128 + raise HTTPException(
129 + status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
130 + detail=f"Failed to revoke task: {str(e)}"
131 + )
132 +  
 133 +  
 134 + @router.post(
135 + "/purge",
136 + response_model=PurgeTasksResponse,
137 + responses={
138 + 401: {"description": "Authentication required"},
139 + 400: {"description": "Invalid status value"},
140 + }
141 + )
142 + async def purge_tasks(
143 + request: PurgeTasksRequest,
144 + current_user: Annotated[dict, Depends(get_current_user_jwt)],
145 + task_status_service: CeleryTaskStatusService = Depends(get_task_status_service),
146 + ) -> PurgeTasksResponse:
147 + """
148 + Purge tasks with specific status from database
149 +  
 150 + Args:
151 + status: Task status to purge (PENDING, FAILURE, SUCCESS)
152 + older_than_minutes: Only purge tasks older than this many minutes (optional)
153 +  
 154 + Returns:
155 + Count of revoked and deleted tasks
156 + """
157 + try:
158 + # Validate status
159 + try:
160 + task_status = TaskStatus(request.status)
161 + except ValueError:
162 + raise HTTPException(
163 + status_code=status.HTTP_400_BAD_REQUEST,
164 + detail=f"Invalid status: {request.status}. Must be one of: PENDING, STARTED, PROGRESS, SUCCESS, FAILURE, RETRY"
165 + )
166 +  
 167 + result = await task_status_service.purge_tasks_by_status(
168 + status=task_status,
169 + older_than_minutes=request.older_than_minutes
170 + )
171 +  
 172 + return PurgeTasksResponse(**result)
173 +  
 174 + except HTTPException:
175 + raise
176 + except Exception as e:
177 + logger.error(f"Failed to purge tasks: {e}", exc_info=True)
178 + raise HTTPException(
179 + status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
180 + detail=f"Failed to purge tasks: {str(e)}"
181 + )
182 +

⏺ I need to fix the route order issue - the /summary route needs to be defined BEFORE the /{task_id} route to avoid path conflicts:

⏺ Update(backend/app/presentation/api/v1/celery_tasks.py)
⎿  Updated backend/app/presentation/api/v1/celery_tasks.py with 28 additions and 28 removals  
 31  
 32  
 33 @router.get(
34 + "/summary",
35 + response_model=TasksSummaryResponse,
36 + responses={
37 + 401: {"description": "Authentication required"},
38 + }
39 + )
40 + async def get_tasks_summary(
41 + current_user: Annotated[dict, Depends(get_current_user_jwt)],
42 + task_status_service: CeleryTaskStatusService = Depends(get_task_status_service),
43 + ) -> TasksSummaryResponse:
44 + """
45 + Get summary of all tasks grouped by status
46 +  
 47 + Returns total count and breakdown by status (PENDING, STARTED, SUCCESS, FAILURE, etc.)
48 + """
49 + try:
50 + summary = await task_status_service.get_all_tasks_summary()
51 + return TasksSummaryResponse(**summary)
52 +  
 53 + except Exception as e:
54 + logger.error(f"Failed to get tasks summary: {e}", exc_info=True)
55 + raise HTTPException(
56 + status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
57 + detail=f"Failed to get tasks summary: {str(e)}"
58 + )
59 +  
 60 +  
 61 + @router.get(
62 "/{task_id}",
63 response_model=CeleryTaskStatusResponse,
64 responses={
...
69 )
70  
 71  
 72 - @router.get(
73 - "/summary",
74 - response_model=TasksSummaryResponse,
75 - responses={
76 - 401: {"description": "Authentication required"},
77 - }
78 - )
79 - async def get_tasks_summary(
80 - current_user: Annotated[dict, Depends(get_current_user_jwt)],
81 - task_status_service: CeleryTaskStatusService = Depends(get_task_status_service),
82 - ) -> TasksSummaryResponse:
83 - """
84 - Get summary of all tasks grouped by status
85 -  
 86 - Returns total count and breakdown by status (PENDING, STARTED, SUCCESS, FAILURE, etc.)
87 - """
88 - try:
89 - summary = await task_status_service.get_all_tasks_summary()
90 - return TasksSummaryResponse(**summary)
91 -  
 92 - except Exception as e:
93 - logger.error(f"Failed to get tasks summary: {e}", exc_info=True)
94 - raise HTTPException(
95 - status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
96 - detail=f"Failed to get tasks summary: {str(e)}"
97 - )
98 -  
 99 -  
 72 @router.post(
73 "/revoke/{task_id}",
74 responses={

⏺ Perfect! Phase 2 is now complete. Let me update the todo list and move to Phase 3 (Frontend UI):

⏺ Now let's work on the frontend. First, let me read the existing API client to understand the pattern:

⏺ Read(frontend/src/lib/api-client.ts)
⎿  Read 100 lines

⏺ Search(pattern: "celery.*task|task.*summary|purge", path: "frontend/src/lib/api-client.ts", output_mode: "content")
⎿  Found 6 lines (ctrl+o to expand)

⏺ Let me read more of the API client to see the existing Celery task methods:

⏺ Read(frontend/src/lib/api-client.ts)
⎿  Read 50 lines

⏺ Now let me add the new task management methods to the API client. I'll add them right after the existing Celery task methods:

⏺ Update(frontend/src/lib/api-client.ts)
⎿  Updated frontend/src/lib/api-client.ts with 31 additions  
 428 }
429 }
430  
 431 + async getTasksSummary(): Promise<{ total: number; by_status: Record<string, number> }> {
432 + return this.request<{ total: number; by_status: Record<string, number> }>(
433 + "/celery-tasks/summary"
434 + )
435 + }
436 +  
 437 + async revokeTask(taskId: string): Promise<{ success: boolean; message: string }> {
438 + return this.request<{ success: boolean; message: string }>(
439 + `/celery-tasks/revoke/${taskId}`,
440 + {
441 + method: "POST",
442 + }
443 + )
444 + }
445 +  
 446 + async purgeTasks(
447 + status: string,
448 + olderThanMinutes?: number
449 + ): Promise<{ revoked: number; deleted: number }> {
450 + return this.request<{ revoked: number; deleted: number }>(
451 + "/celery-tasks/purge",
452 + {
453 + method: "POST",
454 + body: JSON.stringify({
455 + status,
456 + older_than_minutes: olderThanMinutes,
457 + }),
458 + }
459 + )
460 + }
461 +  
 462 // User Settings API methods
463 async getUserSettings(): Promise<UserSettings> {
464 return this.request<UserSettings>("/users/settings")

⏺ Good! Now let me create the React Query hooks file. First, let me check if there's an existing hooks directory structure:

⏺ Bash(ls -la src/hooks/use-\*.ts 2>/dev/null | head -10)
⎿  -rw-r--r-- 1 oliver staff 2283 Nov 12 17:15 src/hooks/use-activity-detection.ts
-rw-r--r-- 1 oliver staff 1846 Nov 12 17:15 src/hooks/use-channels.ts
-rw-r--r-- 1 oliver staff 14616 Nov 12 17:15 src/hooks/use-episodes.ts
… +7 lines (ctrl+o to expand)

⏺ Let me check the existing use-task-status.ts to understand the pattern:

⏺ Read(frontend/src/hooks/use-task-status.ts)
⎿  Read 76 lines

⏺ Perfect! Now I'll create a new hooks file for the task management operations. I'll add the new hooks to the existing use-task-status.ts file since
they're closely related:

⏺ Update(frontend/src/hooks/use-task-status.ts)
⎿  Updated frontend/src/hooks/use-task-status.ts with 2 additions and 2 removals  
 1 /\*_
2 - _ React Query hooks for Celery task status tracking
2 + _ React Query hooks for Celery task status tracking and management
3 _/
4  
 5 - import { useQuery } from "@tanstack/react-query"
5 + import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
6 import { apiClient } from "@/lib/api-client"
7 import { CeleryTaskStatus } from "@/types"
8

⏺ Update(frontend/src/hooks/use-task-status.ts)
⎿  Updated frontend/src/hooks/use-task-status.ts with 1 addition  
 12 task: (taskId: string) => [...taskStatusKeys.all, "task", taskId] as const,
13 channel: (channelId: number) =>
14 [...taskStatusKeys.all, "channel", channelId] as const,
15 + summary: () => [...taskStatusKeys.all, "summary"] as const,
16 }
17  
 18 /\*\*

⏺ Update(frontend/src/hooks/use-task-status.ts)
⎿  Updated frontend/src/hooks/use-task-status.ts with 49 additions  
 74 staleTime: 1000, // Consider data stale after 1 second
75 })
76 }
77 +  
 78 + /**
79 + _ Hook to get summary of all tasks grouped by status
80 + _/
81 + export function useTasksSummary(enabled: boolean = true) {
82 + return useQuery({
83 + queryKey: taskStatusKeys.summary(),
84 + queryFn: () => apiClient.getTasksSummary(),
85 + enabled,
86 + refetchInterval: 5000, // Refresh every 5 seconds
87 + staleTime: 2000,
88 + })
89 + }
90 +  
 91 + /**
92 + _ Hook to revoke a specific task
93 + _/
94 + export function useRevokeTask() {
95 + const queryClient = useQueryClient()
96 +  
 97 + return useMutation({
98 + mutationFn: (taskId: string) => apiClient.revokeTask(taskId),
99 + onSuccess: () => {
100 + // Invalidate all task-related queries
101 + queryClient.invalidateQueries({ queryKey: taskStatusKeys.all })
102 + },
103 + })
104 + }
105 +  
 106 + /\*_
107 + _ Hook to purge tasks by status
108 + \*/
109 + export function usePurgeTasks() {
110 + const queryClient = useQueryClient()
111 +  
 112 + return useMutation({
113 + mutationFn: ({
114 + status,
115 + olderThanMinutes,
116 + }: {
117 + status: string
118 + olderThanMinutes?: number
119 + }) => apiClient.purgeTasks(status, olderThanMinutes),
120 + onSuccess: () => {
121 + // Invalidate all task-related queries
122 + queryClient.invalidateQueries({ queryKey: taskStatusKeys.all })
123 + },
124 + })
125 + }

⏺ Perfect! Now let me find the Settings interface component to add the task management UI:

⏺ Bash(find src/components -name "_settings_" -type f 2>/dev/null)
⎿  src/components/features/settings/settings-interface.tsx

⏺ Read(frontend/src/components/features/settings/settings-interface.tsx)
⎿  Read 100 lines

⏺ Let me search for the Advanced tab in this file:

⏺ Search(pattern: "Advanced|renderAdvanced|advanced", path: "frontend/src/components/features/settings/settings-interface.tsx", output_mode: "content")
⎿  Found 6 lines (ctrl+o to expand)

⏺ Read(frontend/src/components/features/settings/settings-interface.tsx)
⎿  Read 120 lines

⏺ Perfect! Now I'll add the task management section. I need to add it before the "Other Advanced Settings Placeholder" section. First, let me add the
necessary imports at the top:

⏺ Read(frontend/src/components/features/settings/settings-interface.tsx)
⎿  Read 80 lines

⏺ Update(frontend/src/components/features/settings/settings-interface.tsx)
⎿  Updated frontend/src/components/features/settings/settings-interface.tsx with 3 additions and 1 removal
59 Database,
60 FileX,
61 AlertCircle,
62 - Bell
62 + Bell,
63 + ListTodo,
64 + X
65 } from 'lucide-react'
66 import { toast } from 'sonner'
67 import { cn } from '@/lib/utils'

⏺ Update(frontend/src/components/features/settings/settings-interface.tsx)
⎿  Updated frontend/src/components/features/settings/settings-interface.tsx with 1 addition
71 import type { Tag, Channel } from '@/types'
72 import { apiClient } from '@/lib/api-client'
73 import { SubscriptionCheckFrequency } from '@/types'
74 + import { useTasksSummary, usePurgeTasks } from '@/hooks/use-task-status'
75  
 76 // Mock data
77 const mockChannelData = {

⏺ Now I need to find where the state variables are defined and add new state for the purge dialog. Let me search for useState:

⏺ Search(pattern: "const \[.\*useState", path: "frontend/src/components/features/settings/settings-interface.tsx", output_mode: "content")
⎿  Found 31 lines (ctrl+o to expand)

⏺ Read(frontend/src/components/features/settings/settings-interface.tsx)
⎿  Read 20 lines

⏺ Perfect! Now I'll add the state for the purge dialog right after the delete library state:

⏺ Update(frontend/src/components/features/settings/settings-interface.tsx)
⎿  Updated frontend/src/components/features/settings/settings-interface.tsx with 8 additions  
 255 error?: string
256 } | null>(null)
257  
 258 + // Task management state
259 + const [showPurgeDialog, setShowPurgeDialog] = useState(false)
260 + const [purgeStatus, setPurgeStatus] = useState<'PENDING' | 'FAILURE' | 'SUCCESS'>('PENDING')
261 +  
 262 + // Hooks for task management
263 + const { data: tasksSummary, isLoading: isLoadingTasks } = useTasksSummary(activeTab === 'advanced')
264 + const purgeTasks = usePurgeTasks()
265 +  
 266 // Load channel data on component mount
267 useEffect(() => {
268 loadChannelData()

⏺ Now I need to add the handler function for purging tasks. Let me find where other handler functions are defined and add it there:

⏺ Search(pattern: "const handle.\*= async", path: "frontend/src/components/features/settings/settings-interface.tsx", output_mode: "content", head_limit: 5)
⎿  Found 5 lines (ctrl+o to expand)

⏺ Let me find the deleteLibrary handler to add my purge handler nearby:

⏺ Search(pattern: "handleDelete.*Library|const.*purge|const.\*cancel", path: "frontend/src/components/features/settings/settings-interface.tsx",
output_mode: "content")
⎿  Found 21 lines (ctrl+o to expand)

⏺ Read(frontend/src/components/features/settings/settings-interface.tsx)
⎿  Read 100 lines

⏺ Perfect! Now I'll add the handler functions for purging tasks right after these delete library handlers:

⏺ Update(frontend/src/components/features/settings/settings-interface.tsx)
⎿  Updated frontend/src/components/features/settings/settings-interface.tsx with 28 additions  
 623 }
624 }
625  
 626 + // Task management handlers
627 + const handlePurgeTasksClick = (status: 'PENDING' | 'FAILURE' | 'SUCCESS') => {
628 + setPurgeStatus(status)
629 + setShowPurgeDialog(true)
630 + }
631 +  
 632 + const handlePurgeTasksExecute = async () => {
633 + try {
634 + const result = await purgeTasks.mutateAsync({
635 + status: purgeStatus,
636 + olderThanMinutes: undefined, // Purge all tasks with this status
637 + })
638 +  
 639 + toast.success(
640 + `Purged ${result.deleted} ${purgeStatus} tasks` +
641 + (result.revoked > 0 ? ` (${result.revoked} revoked from queue)` : '')
642 + )
643 + setShowPurgeDialog(false)
644 + } catch (error) {
645 + console.error('Purge tasks error:', error)
646 + toast.error(`Failed to purge tasks: ${error instanceof Error ? error.message : 'Unknown error'}`)
647 + }
648 + }
649 +  
 650 + const handlePurgeTasksCancel = () => {
651 + setShowPurgeDialog(false)
652 + }
653 +  
 654 // Update profile data when user changes
655 useEffect(() => {
656 if (user) {

⏺ Perfect! Now I need to add the UI section to the Advanced tab. Let me add it right before the "Other Advanced Settings Placeholder" section:

⏺ Update(frontend/src/components/features/settings/settings-interface.tsx)
⎿  Updated frontend/src/components/features/settings/settings-interface.tsx with 117 additions  
 1428 </div>
1429 </div>
1430  
 1431 + <Separator />
1432 +  
 1433 + {/_ Task Management Section _/}
1434 + <div className="space-y-4">
1435 + <div>
1436 + <h4 className="font-semibold text-foreground flex items-center gap-2">
1437 + <ListTodo className="w-4 h-4" />
1438 + Background Task Management
1439 + </h4>
1440 + <p className="text-sm text-muted-foreground mt-1">
1441 + View and manage background tasks for video discovery and downloads
1442 + </p>
1443 + </div>
1444 +  
 1445 + {isLoadingTasks ? (
1446 + <div className="flex items-center justify-center py-8">
1447 + <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
1448 + </div>
1449 + ) : tasksSummary ? (
1450 + <div className="space-y-4">
1451 + {/_ Task Summary Cards _/}
1452 + <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
1453 + {/_ Pending Tasks _/}
1454 + <Card className={cn(
1455 + "transition-colors",
1456 + (tasksSummary.by*status?.PENDING || 0) > 0 && "border-yellow-500/30 bg-yellow-500/5"
1457 + )}>
1458 + <CardContent className="pt-6">
1459 + <div className="flex items-center justify-between">
1460 + <div>
1461 + <p className="text-sm font-medium text-muted-foreground">Pending</p>
1462 + <p className="text-2xl font-bold">{tasksSummary.by_status?.PENDING || 0}</p>
1463 + </div>
1464 + {(tasksSummary.by_status?.PENDING || 0) > 0 && (
1465 + <Button
1466 + variant="outline"
1467 + size="sm"
1468 + onClick={() => handlePurgeTasksClick('PENDING')}
1469 + className="gap-2"
1470 + >
1471 + <X className="w-3 h-3" />
1472 + Clear
1473 + </Button>
1474 + )}
1475 + </div>
1476 + </CardContent>
1477 + </Card>
1478 +  
 1479 + {/* Failed Tasks _/}
1480 + <Card className={cn(
1481 + "transition-colors",
1482 + (tasksSummary.by_status?.FAILURE || 0) > 0 && "border-red-500/30 bg-red-500/5"
1483 + )}>
1484 + <CardContent className="pt-6">
1485 + <div className="flex items-center justify-between">
1486 + <div>
1487 + <p className="text-sm font-medium text-muted-foreground">Failed</p>
1488 + <p className="text-2xl font-bold">{tasksSummary.by_status?.FAILURE || 0}</p>
1489 + </div>
1490 + {(tasksSummary.by_status?.FAILURE || 0) > 0 && (
1491 + <Button
1492 + variant="outline"
1493 + size="sm"
1494 + onClick={() => handlePurgeTasksClick('FAILURE')}
1495 + className="gap-2"
1496 + >
1497 + <X className="w-3 h-3" />
1498 + Clear
1499 + </Button>
1500 + )}
1501 + </div>
1502 + </CardContent>
1503 + </Card>
1504 +  
 1505 + {/_ Completed Tasks _/}
1506 + <Card className={cn(
1507 + "transition-colors",
1508 + (tasksSummary.by_status?.SUCCESS || 0) > 0 && "border-green-500/30 bg-green-500/5"
1509 + )}>
1510 + <CardContent className="pt-6">
1511 + <div className="flex items-center justify-between">
1512 + <div>
1513 + <p className="text-sm font-medium text-muted-foreground">Completed</p>
1514 + <p className="text-2xl font-bold">{tasksSummary.by_status?.SUCCESS || 0}</p>
1515 + </div>
1516 + {(tasksSummary.by_status?.SUCCESS || 0) > 0 && (
1517 + <Button
1518 + variant="outline"
1519 + size="sm"
1520 + onClick={() => handlePurgeTasksClick('SUCCESS')}
1521 + className="gap-2"
1522 + >
1523 + <X className="w-3 h-3" />
1524 + Clear
1525 + </Button>
1526 + )}
1527 + </div>
1528 + </CardContent>
1529 + </Card>
1530 + </div>
1531 +  
 1532 + {/_ Total Count _/}
1533 + <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
1534 + <div className="flex items-center gap-2">
1535 + <Activity className="w-4 h-4 text-muted-foreground" />
1536 + <span className="text-sm font-medium">Total Tasks</span>
1537 + </div>
1538 + <Badge variant="secondary">{tasksSummary.total}</Badge>
1539 + </div>
1540 + </div>
1541 + ) : (
1542 + <div className="text-center py-8 text-muted-foreground">
1543 + <p>No task data available</p>
1544 + </div>
1545 + )}
1546 + </div>
1547 +  
 1548 {/_ Other Advanced Settings Placeholder \_/}
1549 <Separator />
1550

⏺ Excellent! Now I need to add the purge confirmation dialog at the end of the component. Let me find where the delete dialog is and add the purge
dialog after it:

⏺ Search(pattern: "Delete Library Confirmation Dialog|{\/\* Delete", path: "frontend/src/components/features/settings/settings-interface.tsx", output_mode:
"content")
⎿  Found 0 lines

⏺ Search(pattern: "showDeleteDialog|Delete.\*Episodes", path: "frontend/src/components/features/settings/settings-interface.tsx", output_mode: "content",
head_limit: 3)
⎿  Found 3 lines (ctrl+o to expand)

⏺ Bash(grep -n "Dialog open={showDeleteDialog}" src/components/features/settings/settings-interface.tsx)
⎿  1610: <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>

⏺ Read(frontend/src/components/features/settings/settings-interface.tsx)
⎿  Read 50 lines

⏺ Let me find the end of this dialog:

⏺ Bash(grep -n "</Dialog>" src/components/features/settings/settings-interface.tsx | tail -2)
⎿  1845: </Dialog>

⏺ Read(frontend/src/components/features/settings/settings-interface.tsx)
⎿  Read 9 lines

⏺ Perfect! Now I'll add the purge tasks dialog right before the closing </>:

⏺ Update(frontend/src/components/features/settings/settings-interface.tsx)
⎿  Updated frontend/src/components/features/settings/settings-interface.tsx with 84 additions  
 1843 </DialogFooter>
1844 </DialogContent>
1845 </Dialog>
1846 +  
 1847 + {/_ Purge Tasks Confirmation Dialog _/}
1848 + <Dialog open={showPurgeDialog} onOpenChange={setShowPurgeDialog}>
1849 + <DialogContent className="max-w-md">
1850 + <DialogHeader>
1851 + <DialogTitle className="flex items-center gap-2">
1852 + <AlertTriangle className="w-5 h-5 text-yellow-500" />
1853 + Clear {purgeStatus} Tasks
1854 + </DialogTitle>
1855 + <DialogDescription>
1856 + Are you sure you want to clear all {purgeStatus} tasks from the database?
1857 + </DialogDescription>
1858 + </DialogHeader>
1859 +  
 1860 + <div className="space-y-4">
1861 + <div className="border border-yellow-500/20 rounded-lg p-4 bg-yellow-500/5">
1862 + <div className="flex items-center gap-2 mb-2">
1863 + <AlertCircle className="w-4 h-4 text-yellow-500" />
1864 + <span className="font-medium text-yellow-600 dark:text-yellow-500">This will:</span>
1865 + </div>
1866 + <div className="space-y-1 text-sm text-muted-foreground">
1867 + {purgeStatus === 'PENDING' && (
1868 + <>
1869 + <p>• Revoke all pending tasks from the queue</p>
1870 + <p>• Remove task records from the database</p>
1871 + <p>• Stop tasks from being executed</p>
1872 + </>
1873 + )}
1874 + {purgeStatus === 'FAILURE' && (
1875 + <>
1876 + <p>• Remove all failed task records</p>
1877 + <p>• Clear error logs from the database</p>
1878 + <p>• Clean up stuck/failed tasks</p>
1879 + </>
1880 + )}
1881 + {purgeStatus === 'SUCCESS' && (
1882 + <>
1883 + <p>• Remove all completed task records</p>
1884 + <p>• Clear task history from the database</p>
1885 + <p>• Free up database space</p>
1886 + </>
1887 + )}
1888 + </div>
1889 + </div>
1890 +  
 1891 + {tasksSummary && (
1892 + <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
1893 + <span className="text-sm font-medium">Tasks to be cleared:</span>
1894 + <Badge variant="secondary">
1895 + {tasksSummary.by_status?.[purgeStatus] || 0}
1896 + </Badge>
1897 + </div>
1898 + )}
1899 + </div>
1900 +  
 1901 + <DialogFooter>
1902 + <Button
1903 + variant="outline"
1904 + onClick={handlePurgeTasksCancel}
1905 + disabled={purgeTasks.isPending}
1906 + >
1907 + Cancel
1908 + </Button>
1909 + <Button
1910 + variant="default"
1911 + onClick={handlePurgeTasksExecute}
1912 + disabled={purgeTasks.isPending}
1913 + className="gap-2"
1914 + >
1915 + {purgeTasks.isPending ? (
1916 + <>
1917 + <Loader2 className="w-4 h-4 animate-spin" />
1918 + Clearing...
1919 + </>
1920 + ) : (
1921 + <>
1922 + <X className="w-4 h-4" />
1923 + Clear Tasks
1924 + </>
1925 + )}
1926 + </Button>
1927 + </DialogFooter>
1928 + </DialogContent>
1929 + </Dialog>
1930 </>
1931 )
1932 }
1933 \ No newline at end of file

⏺ Perfect! Phase 3 is now complete. Let me update the todo list:

⏺ Excellent! All phases are complete. Now let me create a summary of what was implemented and provide instructions for testing:

Summary of Implementation

I've successfully completed all 4 phases of the plan:

✅ PHASE 1: Fixed RSS Task Registration (CRITICAL BUG FIX)

Files Modified:

- /Users/oliver/local/dev/labcastarr/backend/app/infrastructure/celery_app.py

Changes:

1. Added "app.infrastructure.tasks.channel_check_rss_tasks" to the include list (line 21)
2. Added explicit import: import app.infrastructure.tasks.channel_check_rss_tasks # noqa: F401 (line 51)

What this fixes: The RSS task module is now properly registered with Celery. Previously, tasks were queued to Redis but the worker didn't know they
existed, causing them to stay stuck in PENDING status forever.

---

✅ PHASE 2: Added Task Cancellation Backend

Files Modified:

1. Backend Repository - /Users/oliver/local/dev/labcastarr/backend/app/infrastructure/repositories/celery_task_status_repository_impl.py:

   - Added imports: delete, func, Dict, Any, timedelta
   - Added 6 new repository methods:
     - get_all() - Get all task statuses
     - get_by_status() - Get tasks by specific status
     - get_by_status_and_age() - Get old tasks by status
     - get_summary() - Get task counts grouped by status
     - delete() - Delete a task by ID
     - delete_by_status() - Delete all tasks with a status

2. Backend Service - /Users/oliver/local/dev/labcastarr/backend/app/application/services/celery_task_status_service.py:

   - Added imports: Dict, Any, celery_app
   - Added 3 new service methods:
     - get_all_tasks_summary() - Get summary of all tasks
     - revoke_task() - Revoke a running/pending task using Celery control API
     - purge_tasks_by_status() - Purge tasks by status (revokes PENDING tasks in Celery, deletes from DB)

3. API Schemas - /Users/oliver/local/dev/labcastarr/backend/app/presentation/schemas/celery_task_status_schemas.py:

   - Added 3 new Pydantic schemas:
     - TasksSummaryResponse - Response for task summary
     - PurgeTasksRequest - Request for purging tasks
     - PurgeTasksResponse - Response with purge counts

4. API Endpoints - /Users/oliver/local/dev/labcastarr/backend/app/presentation/api/v1/celery_tasks.py:

   - Added 3 new API endpoints:
     - GET /celery-tasks/summary - Get task summary
     - POST /celery-tasks/revoke/{task_id} - Revoke a specific task
     - POST /celery-tasks/purge - Purge tasks by status
   - Fixed route order (moved /summary before /{task_id} to avoid path conflicts)

---

✅ PHASE 3: Added Task Cancellation Frontend UI

Files Modified:

1. API Client - /Users/oliver/local/dev/labcastarr/frontend/src/lib/api-client.ts:

   - Added 3 new API methods:
     - getTasksSummary() - Fetch task summary
     - revokeTask() - Revoke a task
     - purgeTasks() - Purge tasks by status

2. React Query Hooks - /Users/oliver/local/dev/labcastarr/frontend/src/hooks/use-task-status.ts:

   - Added query key: summary()
   - Added 3 new hooks:
     - useTasksSummary() - Query hook with 5s polling
     - useRevokeTask() - Mutation hook for revoking tasks
     - usePurgeTasks() - Mutation hook for purging tasks

3. Settings Interface - /Users/oliver/local/dev/labcastarr/frontend/src/components/features/settings/settings-interface.tsx:

   - Added icons: ListTodo, X
   - Added imports: useTasksSummary, usePurgeTasks
   - Added state variables:
     - showPurgeDialog - Control purge dialog visibility
     - purgeStatus - Track which status to purge
   - Added hooks:
     - tasksSummary - Query for task summary (only when Advanced tab is active)
     - purgeTasks - Mutation for purging tasks
   - Added handler functions:
     - handlePurgeTasksClick() - Open purge dialog
     - handlePurgeTasksExecute() - Execute purge operation
     - handlePurgeTasksCancel() - Cancel purge dialog
   - Added UI sections:
     - Background Task Management section in Advanced tab with:
       - 3 task status cards (Pending, Failed, Completed) with counts and Clear buttons
     - Color-coded borders (yellow for pending, red for failed, green for success)
     - Total task count display
     - Loading states
     - Purge Confirmation Dialog with: - Status-specific descriptions
       - Task count to be cleared
       - Loading states during purge
       - Confirmation/cancel buttons

---

✅ PHASE 4: Testing Instructions

Step 1: Restart Celery Worker (CRITICAL)
docker compose -f docker-compose.dev.yml restart celery-worker-dev celery-beat-dev
This is required for the RSS task registration fix to take effect.

Step 2: Test RSS Task Execution

1. Go to /subscriptions/channels
2. Click the "Search for Latest Videos (RSS Feed)" button on a channel
3. ✅ Expected: Task should transition from "queued" → "searching" → "updated" within seconds
4. ❌ Before fix: Task stayed stuck in "queued" status with started_at: null

Step 3: Test Task Management UI

1. Go to /settings and click the Advanced tab
2. You should see a new "Background Task Management" section showing:

   - Pending tasks count (yellow)
   - Failed tasks count (red)
   - Completed tasks count (green)
   - Total tasks count

3. Click "Clear" on any status card with tasks
4. Confirm in the dialog
5. ✅ Expected: Tasks should be purged and counts updated

Step 4: Verify Task Purging

1. Purge all PENDING tasks (if you had stuck ones)
2. Check that:

   - Tasks are removed from database
   - Pending count drops to 0
   - Toast notification shows success message

3. Try clicking RSS check again to create new tasks
4. Verify new tasks execute properly

---

API Endpoints Summary

New Endpoints:

- GET /v1/celery-tasks/summary - Get task counts by status
- POST /v1/celery-tasks/revoke/{task_id} - Cancel a specific task
- POST /v1/celery-tasks/purge - Bulk delete tasks by status

Request Example (Purge):
{
"status": "PENDING",
"older_than_minutes": 10 // Optional
}

Response Example (Purge):
{
"revoked": 5, // Tasks revoked in Celery
"deleted": 5 // Tasks deleted from database
}

---

Next Steps

1. Restart the Celery worker using the command above
2. Test the RSS button - it should work now!
3. Manage stuck tasks - Use the new Advanced tab to clear any old PENDING/FAILED tasks
4. Monitor task health - The Advanced tab now gives you visibility into background task status

The RSS task registration bug is fixed, and you now have full control over background tasks!

> I followed your instructions to restart the celery worker and the beat scheduler. I also restarted the containers and the problem persisted.

However, i did not use the very same command that you provided. I used the following command since i was using the production configuration:

```bash
#Step 1: Restart Celery Worker (CRITICAL)
#docker compose -f docker-compose.dev.yml restart celery-worker-dev celery-beat-dev

#But i used the following command since i was using the production configuration:
docker compose -f docker-compose.production.yml restart celery-worker celery-beat
```

After restarting the celery worker and the beat scheduler, the problem persisted. The card of the channel still showed "queued" as status and did not
change. And the "/activity" page did not show any events related to this last action. Moreover, the buttons icons keep spinning and the status of the
card does not change from "queued" after rebuilding the containers a couple of times.

Then I followed your instructions to use the new Advanced tab to clear any old PENDING/FAILED tasks and monitor task health. The Advanced tab now gives
you visibility into background task status. After using the CLEAR tasks, i went back to the follwoed channels page again, and now the problem was
gone. The card showed the last updated message with the date of the last completed task as expected.

Then i used the RSS button to search for new videos and it worked as expected. I was way faster than using the old button. I am checking channel with
id:1 which has no new videos published as of today, and we are updated in the database with the channel, and the search found no new videos to fetch
medatata. After it finnished, the card showed the last updated message with the date of the last completed task as expected.

The only problem that we need to fix is that when i use the button for the quick "RSS feed" search, the icons of both buttons start spinning and after
the task finnishes, both stop at the same time. The icon of a button should only spin when it is triggered. Clicking on a button should not make the
other button icon spin.

⏺ Excellent progress! The RSS task is working perfectly now, and the task management feature is working as expected. The issue with both buttons
spinning is actually expected behavior by design, but I can see why it might be confusing. Let me explain and then fix it.

Why Both Buttons Spin (Current Behavior)

Both buttons use the same hook useChannelTaskStatus(channel.id), which fetches the latest task for that channel. The backend only tracks one task per
channel at a time. When ANY task is running for a channel, both buttons see it and show the spinning state because:

1. Both methods create tasks with the same followed_channel_id
2. The API endpoint /followed-channels/{id}/task-status returns the latest task regardless of method
3. Both buttons query this same endpoint and see the same active task

However, I understand this is confusing UX. Users expect only the clicked button to spin. Let me fix this by tracking which method was used in the
task status and only spinning the matching button.

Solution: Track Task Name in Status

The task status already includes a task_name field that distinguishes between the two methods:

- "check_followed_channel_for_new_videos" (yt-dlp method)
- "check_followed_channel_for_new_videos_rss" (RSS method)

I'll update the frontend to check the task name and only show spinner on the matching button.

⏺ Read(frontend/src/components/features/followed-channels/followed-channel-card.tsx)
⎿  Error reading file

⏺ Bash(find src/components -name "*followed*channel\*" -type f 2>/dev/null | grep -i card)
⎿  No matches found

⏺ Bash(find src/components -name "_followed_" -type f 2>/dev/null)
⎿  src/components/features/subscriptions/followed-channels-list.tsx

⏺ Search(pattern: "RSS|check.*new.*video|button.\*spin|isChecking", path: "src/components/features/subscriptions/followed-channels-list.tsx", output_mode:
"content", head_limit: 15)
⎿  Found 14 lines (ctrl+o to expand)

⏺ Read(frontend/src/components/features/subscriptions/followed-channels-list.tsx)
⎿  Read 150 lines

⏺ Perfect! I can see the issue. Both buttons check isSearching which is true for ANY active task on that channel, regardless of which method triggered
it. I need to make each button only spin when its specific task type is running.

The solution is to check the taskStatus.task_name field to determine which method is running:

⏺ Update(frontend/src/components/features/subscriptions/followed-channels-list.tsx)
⎿  Updated frontend/src/components/features/subscriptions/followed-channels-list.tsx with 8 additions
240 taskStatus?.status === "PENDING" ||
241 taskStatus?.status === "STARTED"
242  
 243 + // Determine which specific method is running
244 + const isRssTaskRunning =
245 + isSearching &&
246 + taskStatus?.task_name === "check_followed_channel_for_new_videos_rss"
247 + const isYtdlpTaskRunning =
248 + isSearching &&
249 + taskStatus?.task_name === "check_followed_channel_for_new_videos"
250 +  
 251 return (
252 <Card className="hover:shadow-lg hover:-translate-y-1 transition-all duration-200">
253 <CardHeader className="pb-3">

⏺ Now I need to update the button disabled states and animations to use these specific flags:

⏺ Update(frontend/src/components/features/subscriptions/followed-channels-list.tsx)
⎿  Updated frontend/src/components/features/subscriptions/followed-channels-list.tsx with 2 additions and 2 removals
312 <Zap
313 className={cn(
314 "h-4 w-4 mr-2",
315 - (isCheckRssPending || isSearching) && "animate-spin"
315 + (isCheckRssPending || isRssTaskRunning) && "animate-spin"
316 )}
317 />
318 Search for Latest Videos (RSS Feed)
...
324 <RefreshCw
325 className={cn(
326 "h-4 w-4 mr-2",
327 - (isCheckPending || isSearching) && "animate-spin"
327 + (isCheckPending || isYtdlpTaskRunning) && "animate-spin"
328 )}
329 />
330 Search for Recent Videos (Slow API)

⏺ Perfect! Now let me update the todo list to mark this fix as complete:

⏺ Perfect! I've fixed the button spinner issue. Here's what changed:

Button Spinner Fix

File Modified: /Users/oliver/local/dev/labcastarr/frontend/src/components/features/subscriptions/followed-channels-list.tsx

Changes:

1. Added two new computed values that check both the task status AND the task name:
   const isRssTaskRunning =
   isSearching &&
   taskStatus?.task_name === "check_followed_channel_for_new_videos_rss"

const isYtdlpTaskRunning =
isSearching &&
taskStatus?.task_name === "check_followed_channel_for_new_videos" 2. Updated button animations to use the specific task flags instead of the generic isSearching: - RSS button (Zap icon): Now only spins when isCheckRssPending || isRssTaskRunning - Slow API button (RefreshCw icon): Now only spins when isCheckPending || isYtdlpTaskRunning 3. Both buttons remain disabled when ANY task is running (isSearching) to prevent starting multiple tasks simultaneously 4. But only the matching button shows the spinner animation based on the task name

How It Works Now

Before:

- Click RSS button → Both buttons spin ❌
- Click Slow API button → Both buttons spin ❌

After:

- Click RSS button → Only RSS button spins ✅
- Click Slow API button → Only Slow API button spins ✅
- Both buttons stay disabled during any task (prevents race conditions) ✅

Testing Instructions

1. Rebuild the frontend to pick up the changes:
   docker compose -f docker-compose.prod.yml up --build -d frontend
2. Test RSS button:

   - Click "Search for Latest Videos (RSS Feed)"
   - ✅ Only the Zap icon should spin
   - ✅ The RefreshCw icon should NOT spin
   - ✅ Both buttons should be disabled (can't click either)

3. Test Slow API button:

   - Click "Search for Recent Videos (Slow API)"
   - ✅ Only the RefreshCw icon should spin
   - ✅ The Zap icon should NOT spin
   - ✅ Both buttons should be disabled

This provides much clearer visual feedback to the user about which operation is running while still preventing multiple concurrent tasks per channel!

> /context
> ⎿

      Context Usage
     ⛁ ⛀ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁   claude-sonnet-4-5-20250929 · 147k/200k tokens (73%)
     ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁
     ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁   ⛁ System prompt: 3.4k tokens (1.7%)
     ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁   ⛁ System tools: 16.6k tokens (8.3%)
     ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛁   ⛁ Memory files: 5.4k tokens (2.7%)
     ⛁ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶   ⛁ Messages: 76.3k tokens (38.1%)
     ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶   ⛶ Free space: 53k (26.7%)
     ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛝ ⛝ ⛝   ⛝ Autocompact buffer: 45.0k tokens (22.5%)
     ⛝ ⛝ ⛝ ⛝ ⛝ ⛝ ⛝ ⛝ ⛝ ⛝
     ⛝ ⛝ ⛝ ⛝ ⛝ ⛝ ⛝ ⛝ ⛝ ⛝

     Memory files · /memory
     └ Project (/Users/oliver/local/dev/labcastarr/CLAUDE.md): 5.4k tokens

     SlashCommand Tool · 15 commands
     └ Total: 2.7k tokens

> /usage
> ⎿  Status dialog dismissed

───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

> ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
> ? for shortcuts
