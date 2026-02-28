# RSS Feed-Based Video Discovery Implementation Plan

## Project Overview

Implement a new YouTube video discovery method using RSS feeds as an alternative to the current yt-dlp channel listing approach. This will provide a faster way to check for new videos while maintaining the existing workflow as a separate option.

## Goals

1. Create two independent video discovery workflows (no fallback between them)
2. RSS-based workflow: Use YouTube RSS feed to identify new video IDs, then yt-dlp for metadata
3. Maintain existing yt-dlp workflow as "Search for Recent Videos (Slow API)"
4. Implement Strategy pattern for extensibility
5. Ensure backward compatibility with zero breaking changes

## Architecture Decisions

### Strategy Pattern Implementation

- Create abstract `VideoDiscoveryStrategy` interface in domain layer
- Two concrete implementations:
  - `YtdlpDiscoveryStrategy` (refactored existing logic)
  - `RSSDiscoveryStrategy` (new RSS-based logic)
- Both strategies share common metadata fetching via `YouTubeMetadataService`

### RSS Feed Approach

- YouTube RSS URL: `https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}`
- Returns last 10-15 videos in Atom XML format
- Check ALL RSS entries against database (not just until first match)
- Sequential yt-dlp calls for metadata (one per new video ID)

### Technical Stack

- **RSS Parsing**: lxml (already installed) with ElementTree API
- **HTTP Client**: aiohttp (already available)
- **Async/Await**: Maintain async patterns throughout
- **Celery**: New independent task `check_followed_channel_for_new_videos_rss`

---

## PHASE 1: Backend Architecture Refactoring

**Goal**: Introduce Strategy pattern without changing existing behavior

### Task 1.1: Create Strategy Interface

**File**: `backend/app/domain/services/video_discovery_strategy.py` (NEW)

Create abstract base class for discovery strategies:

```python
from abc import ABC, abstractmethod
from typing import List
from app.domain.entities.followed_channel import FollowedChannel
from app.domain.entities.youtube_video import YouTubeVideo

class VideoDiscoveryStrategy(ABC):
    """Abstract interface for video discovery strategies"""

    @abstractmethod
    async def discover_new_videos(
        self,
        followed_channel: FollowedChannel,
        max_videos: int = 50
    ) -> List[YouTubeVideo]:
        """
        Discover new videos from a followed channel.

        Args:
            followed_channel: The channel to check for new videos
            max_videos: Maximum number of videos to retrieve

        Returns:
            List of new YouTubeVideo entities (not yet persisted)
        """
        pass
```

**Dependencies**: None
**Risk**: Low - new interface file

### Task 1.2: Refactor Existing Discovery Service

**File**: `backend/app/infrastructure/services/ytdlp_discovery_strategy.py` (NEW)

Move logic from `ChannelDiscoveryServiceImpl` to new strategy:

```python
from typing import List
from app.domain.services.video_discovery_strategy import VideoDiscoveryStrategy
from app.domain.entities.followed_channel import FollowedChannel
from app.domain.entities.youtube_video import YouTubeVideo
from app.domain.services.youtube_metadata_service import YouTubeMetadataService
from app.domain.repositories.youtube_video_repository import YouTubeVideoRepository

class YtdlpDiscoveryStrategy(VideoDiscoveryStrategy):
    """Discovery strategy using yt-dlp for both listing and metadata"""

    def __init__(
        self,
        metadata_service: YouTubeMetadataService,
        youtube_video_repository: YouTubeVideoRepository
    ):
        self.metadata_service = metadata_service
        self.youtube_video_repository = youtube_video_repository

    async def discover_new_videos(
        self,
        followed_channel: FollowedChannel,
        max_videos: int = 50
    ) -> List[YouTubeVideo]:
        # Copy existing logic from ChannelDiscoveryServiceImpl.discover_new_videos()
        # No behavior changes - just restructured
        video_metadata_list = await self.metadata_service.list_channel_videos(
            channel_url=followed_channel.youtube_channel_url,
            max_videos=max_videos,
            year=None
        )

        new_videos = []
        for video_meta in video_metadata_list:
            video_id = video_meta.get("video_id")
            if not video_id:
                continue

            # Check if video already exists
            existing_video = await self.youtube_video_repository.get_by_video_id(video_id)
            if existing_video:
                continue

            # Extract full metadata
            full_metadata = await self.metadata_service.extract_video_metadata(
                video_meta.get("url")
            )

            # Create YouTubeVideo entity
            youtube_video = YouTubeVideo(
                # ... same as current implementation
            )

            new_videos.append(youtube_video)

        return new_videos
```

**Dependencies**: Task 1.1
**Risk**: Medium - requires careful testing

### Task 1.3: Update Dependency Injection

**File**: `backend/app/core/dependencies.py`

Add factory functions for strategies:

```python
def get_ytdlp_discovery_strategy(
    metadata_service: YouTubeMetadataServiceImpl = Depends(get_youtube_metadata_service),
    youtube_video_repository: YouTubeVideoRepositoryImpl = Depends(get_youtube_video_repository)
) -> YtdlpDiscoveryStrategy:
    return YtdlpDiscoveryStrategy(
        metadata_service=metadata_service,
        youtube_video_repository=youtube_video_repository
    )

def get_rss_discovery_strategy(
    rss_service: YouTubeRSSService = Depends(get_youtube_rss_service),
    metadata_service: YouTubeMetadataServiceImpl = Depends(get_youtube_metadata_service),
    youtube_video_repository: YouTubeVideoRepositoryImpl = Depends(get_youtube_video_repository)
) -> RSSDiscoveryStrategy:
    return RSSDiscoveryStrategy(
        rss_service=rss_service,
        metadata_service=metadata_service,
        youtube_video_repository=youtube_video_repository
    )
```

**Dependencies**: Task 1.2, Phase 2
**Risk**: Low

### Task 1.4: Update Existing Celery Task

**File**: `backend/app/infrastructure/tasks/channel_check_tasks.py`

Update task to use `YtdlpDiscoveryStrategy`:

```python
# Replace direct ChannelDiscoveryServiceImpl usage with strategy
discovery_strategy = YtdlpDiscoveryStrategy(
    metadata_service=metadata_service,
    youtube_video_repository=youtube_video_repository
)

new_videos = await discovery_strategy.discover_new_videos(
    followed_channel=followed_channel,
    max_videos=50
)

# Rest of logic remains the same
```

**Dependencies**: Task 1.2
**Risk**: Medium - ensure no regression in existing functionality

---

## PHASE 2: RSS Feed Implementation

**Goal**: Create new RSS-based discovery workflow

### Task 2.1: Create RSS Service

**File**: `backend/app/infrastructure/services/youtube_rss_service.py` (NEW)

```python
import aiohttp
from lxml import etree
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class YouTubeRSSService:
    """Service for fetching and parsing YouTube channel RSS feeds"""

    RSS_FEED_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def fetch_channel_rss(self, channel_id: str) -> List[Dict]:
        """
        Fetch RSS feed for a YouTube channel.

        Args:
            channel_id: YouTube channel ID (UCxxx format)

        Returns:
            List of video dictionaries with: video_id, title, published, url

        Raises:
            Exception: If RSS fetch or parse fails
        """
        url = self.RSS_FEED_URL.format(channel_id=channel_id)

        try:
            session = await self._get_session()
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                response.raise_for_status()
                xml_content = await response.text()

            return self._parse_rss_feed(xml_content)

        except aiohttp.ClientError as e:
            logger.error(f"Failed to fetch RSS feed for channel {channel_id}: {e}")
            raise Exception(f"RSS feed fetch failed: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing RSS feed for channel {channel_id}: {e}")
            raise

    def _parse_rss_feed(self, xml_content: str) -> List[Dict]:
        """Parse YouTube Atom XML feed"""
        try:
            root = etree.fromstring(xml_content.encode('utf-8'))

            # Define namespaces
            namespaces = {
                'atom': 'http://www.w3.org/2005/Atom',
                'yt': 'http://www.youtube.com/xml/schemas/2015',
                'media': 'http://search.yahoo.com/mrss/'
            }

            videos = []
            for entry in root.findall('atom:entry', namespaces):
                video_id_elem = entry.find('yt:videoId', namespaces)
                title_elem = entry.find('atom:title', namespaces)
                published_elem = entry.find('atom:published', namespaces)
                link_elem = entry.find('atom:link[@rel="alternate"]', namespaces)

                if video_id_elem is not None and video_id_elem.text:
                    video = {
                        'video_id': video_id_elem.text,
                        'title': title_elem.text if title_elem is not None else 'Unknown',
                        'published': published_elem.text if published_elem is not None else None,
                        'url': link_elem.get('href') if link_elem is not None else f"https://www.youtube.com/watch?v={video_id_elem.text}"
                    }
                    videos.append(video)

            logger.info(f"Parsed {len(videos)} videos from RSS feed")
            return videos

        except etree.XMLSyntaxError as e:
            logger.error(f"XML parsing error: {e}")
            raise Exception(f"Invalid RSS feed XML: {str(e)}")

    async def close(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
```

**Dependencies**: None
**Risk**: Medium - new external service integration

### Task 2.2: Create RSS Discovery Strategy

**File**: `backend/app/infrastructure/services/rss_discovery_strategy.py` (NEW)

```python
from typing import List
import logging
from app.domain.services.video_discovery_strategy import VideoDiscoveryStrategy
from app.domain.entities.followed_channel import FollowedChannel
from app.domain.entities.youtube_video import YouTubeVideo, YouTubeVideoState
from app.domain.services.youtube_metadata_service import YouTubeMetadataService
from app.domain.repositories.youtube_video_repository import YouTubeVideoRepository
from app.infrastructure.services.youtube_rss_service import YouTubeRSSService

logger = logging.getLogger(__name__)

class RSSDiscoveryStrategy(VideoDiscoveryStrategy):
    """Discovery strategy using RSS feed for video IDs, yt-dlp for metadata"""

    def __init__(
        self,
        rss_service: YouTubeRSSService,
        metadata_service: YouTubeMetadataService,
        youtube_video_repository: YouTubeVideoRepository
    ):
        self.rss_service = rss_service
        self.metadata_service = metadata_service
        self.youtube_video_repository = youtube_video_repository

    async def discover_new_videos(
        self,
        followed_channel: FollowedChannel,
        max_videos: int = 50  # Ignored for RSS (always returns ~10-15)
    ) -> List[YouTubeVideo]:
        """
        Discover new videos using RSS feed.

        Process:
        1. Fetch RSS feed (returns last ~10-15 videos)
        2. Check ALL video IDs against database
        3. For new videos, fetch full metadata via yt-dlp (sequential)
        4. Return list of new YouTubeVideo entities
        """
        # Extract channel ID from followed_channel
        channel_id = followed_channel.youtube_channel_id

        if not channel_id:
            # Attempt extraction from URL
            channel_id = self._extract_channel_id(followed_channel.youtube_channel_url)

        # Fetch RSS feed
        rss_videos = await self.rss_service.fetch_channel_rss(channel_id)
        logger.info(f"RSS feed returned {len(rss_videos)} videos for channel {channel_id}")

        # Check ALL RSS video IDs against database
        new_videos = []
        for rss_video in rss_videos:
            video_id = rss_video.get('video_id')
            if not video_id:
                continue

            # Check if video already exists
            existing_video = await self.youtube_video_repository.get_by_video_id(video_id)
            if existing_video:
                logger.debug(f"Video {video_id} already exists, skipping")
                continue

            # Fetch full metadata using yt-dlp (sequential call)
            try:
                full_metadata = await self.metadata_service.extract_video_metadata(
                    rss_video.get('url')
                )

                # Create YouTubeVideo entity
                youtube_video = YouTubeVideo(
                    id=None,
                    video_id=video_id,
                    followed_channel_id=followed_channel.id,
                    title=full_metadata.get('title') or rss_video.get('title'),
                    description=full_metadata.get('description', ''),
                    url=rss_video.get('url'),
                    thumbnail_url=full_metadata.get('thumbnail_url'),
                    publish_date=full_metadata.get('publish_date'),
                    duration=full_metadata.get('duration'),
                    view_count=full_metadata.get('view_count'),
                    like_count=full_metadata.get('like_count'),
                    comment_count=full_metadata.get('comment_count'),
                    metadata_json=full_metadata.get('metadata_json'),
                    state=YouTubeVideoState.PENDING_REVIEW,
                    episode_id=None,
                    reviewed_at=None,
                )

                new_videos.append(youtube_video)
                logger.info(f"Discovered new video: {video_id} - {youtube_video.title}")

            except Exception as e:
                # Log error but continue with other videos
                logger.error(f"Failed to extract metadata for video {video_id}: {e}")
                continue

        logger.info(f"Discovered {len(new_videos)} new videos via RSS for channel {channel_id}")
        return new_videos

    def _extract_channel_id(self, channel_url: str) -> str:
        """Extract channel ID from various YouTube URL formats"""
        # Handle UC format: https://www.youtube.com/channel/UCxxx
        if '/channel/' in channel_url:
            return channel_url.split('/channel/')[-1].split('/')[0].split('?')[0]

        # Handle @handle format - need to extract from existing metadata
        # This should already be stored in followed_channel.youtube_channel_id
        raise ValueError(f"Cannot extract channel ID from URL: {channel_url}")
```

**Dependencies**: Task 2.1
**Risk**: Medium - new core discovery logic

### Task 2.3: Create New Celery Task

**File**: `backend/app/infrastructure/tasks/channel_check_rss_tasks.py` (NEW)

```python
from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from typing import Dict, Any

from app.infrastructure.database.session import get_background_task_session
from app.infrastructure.repositories.followed_channel_repository_impl import FollowedChannelRepositoryImpl
from app.infrastructure.repositories.youtube_video_repository_impl import YouTubeVideoRepositoryImpl
from app.infrastructure.repositories.celery_task_status_repository_impl import CeleryTaskStatusRepositoryImpl
from app.infrastructure.repositories.notification_repository_impl import NotificationRepositoryImpl
from app.infrastructure.services.youtube_metadata_service_impl import YouTubeMetadataServiceImpl
from app.infrastructure.services.youtube_rss_service import YouTubeRSSService
from app.infrastructure.services.rss_discovery_strategy import RSSDiscoveryStrategy
from app.application.services.notification_service import NotificationService
from app.domain.entities.youtube_video import YouTubeVideoState

logger = logging.getLogger(__name__)

@shared_task(
    bind=True,
    name="app.infrastructure.tasks.channel_check_rss_tasks.check_followed_channel_for_new_videos_rss",
    autoretry_for=(ConnectionError, TimeoutError),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def check_followed_channel_for_new_videos_rss(
    self,
    followed_channel_id: int
) -> Dict[str, Any]:
    """
    Check for new videos using RSS feed strategy.

    This is a separate task from the yt-dlp version.
    """
    async def _check_channel_rss():
        session: AsyncSession = await get_background_task_session()

        try:
            # Initialize repositories
            followed_channel_repo = FollowedChannelRepositoryImpl(session)
            youtube_video_repo = YouTubeVideoRepositoryImpl(session)
            task_status_repo = CeleryTaskStatusRepositoryImpl(session)
            notification_repo = NotificationRepositoryImpl(session)

            # Get task status and mark as started
            task_status = await task_status_repo.get_by_task_id(self.request.id)
            if task_status:
                task_status.mark_started()
                await task_status_repo.update(task_status)

            # Get followed channel
            followed_channel = await followed_channel_repo.get_by_id(followed_channel_id)
            if not followed_channel:
                raise ValueError(f"Followed channel {followed_channel_id} not found")

            # Create notification service
            notif_service = NotificationService(notification_repo)

            # Send "search started" notification
            await notif_service.create_channel_search_started_notification(
                user_id=followed_channel.user_id,
                followed_channel_id=followed_channel.id,
                channel_name=followed_channel.youtube_channel_name
            )

            # Initialize RSS discovery strategy
            rss_service = YouTubeRSSService()
            metadata_service = YouTubeMetadataServiceImpl()
            discovery_strategy = RSSDiscoveryStrategy(
                rss_service=rss_service,
                metadata_service=metadata_service,
                youtube_video_repository=youtube_video_repo
            )

            # Discover new videos using RSS
            new_videos = await discovery_strategy.discover_new_videos(
                followed_channel=followed_channel,
                max_videos=50  # Ignored by RSS strategy
            )

            # Save new videos to database
            for video in new_videos:
                await youtube_video_repo.create(video)

            # Handle auto-approve if enabled
            if followed_channel.auto_approve and followed_channel.auto_approve_channel_id:
                from app.infrastructure.tasks.create_episode_from_video_task import create_episode_from_youtube_video

                for video in new_videos:
                    # Transition to QUEUED state
                    video.queue_for_episode_creation()
                    await youtube_video_repo.update(video)

                    # Queue episode creation task
                    create_episode_from_youtube_video.apply_async(
                        args=(video.id, followed_channel.auto_approve_channel_id, followed_channel.user_id)
                    )

            # Update last_checked timestamp
            await followed_channel_repo.update_last_checked(followed_channel.id)

            # Get total pending count
            total_pending_count = await youtube_video_repo.get_count_by_state(
                followed_channel_id=followed_channel.id,
                state=YouTubeVideoState.PENDING_REVIEW
            )

            # Send "search completed" notification
            await notif_service.create_channel_search_completed_notification(
                user_id=followed_channel.user_id,
                followed_channel_id=followed_channel.id,
                channel_name=followed_channel.youtube_channel_name,
                new_videos_count=len(new_videos),
                total_videos_count=total_pending_count
            )

            # Mark task as success
            if task_status:
                result = {
                    "new_videos_count": len(new_videos),
                    "total_pending_count": total_pending_count
                }
                task_status.mark_success(result_json=str(result))
                await task_status_repo.update(task_status)

            # Cleanup
            await rss_service.close()

            return {
                "status": "success",
                "new_videos_count": len(new_videos),
                "total_pending_count": total_pending_count
            }

        except Exception as e:
            logger.error(f"Error checking channel {followed_channel_id} via RSS: {e}", exc_info=True)

            # Mark task as failure
            if task_status:
                task_status.mark_failure(error_message=str(e))
                await task_status_repo.update(task_status)

            # Try to send error notification
            try:
                await notif_service.create_channel_search_error_notification(
                    user_id=followed_channel.user_id,
                    followed_channel_id=followed_channel.id,
                    channel_name=followed_channel.youtube_channel_name,
                    error_message=str(e)
                )
            except:
                pass

            return {
                "status": "error",
                "error": str(e)
            }
        finally:
            await session.close()

    from app.infrastructure.tasks.utils import _run_async
    return _run_async(_check_channel_rss())
```

**Dependencies**: Task 2.2
**Risk**: Medium - new async task with external service calls

### Task 2.4: Add RSS Service to DI

**File**: `backend/app/core/dependencies.py`

```python
@lru_cache()
def get_youtube_rss_service() -> YouTubeRSSService:
    """Get singleton YouTubeRSSService"""
    return YouTubeRSSService()
```

**Dependencies**: Task 2.1
**Risk**: Low

---

## PHASE 3: API Layer Updates

**Goal**: Expose RSS-based check via new API endpoint

### Task 3.1: Create New API Endpoint

**File**: `backend/app/presentation/api/v1/followed_channels.py`

Add new endpoint after existing `trigger_check()`:

```python
@router.post(
    "/{followed_channel_id}/check-rss",
    response_model=dict,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Check for new videos using RSS feed (fast)",
    description="Queue a background task to check for latest videos using YouTube RSS feed. Returns last ~10-15 videos.",
)
async def trigger_check_rss(
    followed_channel_id: int,
    current_user: UserDep,
    followed_channel_service: FollowedChannelServiceDep,
) -> dict:
    """
    Trigger RSS-based check for new videos.

    Fast method using YouTube RSS feed (returns last 10-15 videos).
    Uses yt-dlp only for metadata extraction of new videos.
    """
    try:
        from app.infrastructure.tasks.channel_check_rss_tasks import check_followed_channel_for_new_videos_rss

        # Verify channel exists and belongs to user
        channel = await followed_channel_service.get_followed_channel(
            followed_channel_id=followed_channel_id,
            user_id=current_user.id
        )

        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Followed channel {followed_channel_id} not found"
            )

        # Queue RSS check task
        task = check_followed_channel_for_new_videos_rss.apply_async(
            args=(followed_channel_id,),
            kwargs={}
        )

        return {
            "status": "queued",
            "message": "RSS check task queued successfully",
            "followed_channel_id": followed_channel_id,
            "task_id": task.id,
            "method": "rss_feed"
        }

    except ConnectionError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not connect to task queue. Please try again later."
        )
```

**Dependencies**: Phase 2 complete
**Risk**: Low - follows existing endpoint pattern

### Task 3.2: Update Existing Endpoint Documentation

**File**: `backend/app/presentation/api/v1/followed_channels.py`

Update existing `trigger_check()` endpoint:

```python
@router.post(
    "/{followed_channel_id}/check",
    response_model=dict,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Check for recent videos using yt-dlp (comprehensive)",  # UPDATED
    description="Queue a background task to check for new videos using yt-dlp. Retrieves up to 50 recent videos with full metadata.",  # UPDATED
)
async def trigger_check(
    followed_channel_id: int,
    current_user: UserDep,
    followed_channel_service: FollowedChannelServiceDep,
) -> dict:
    # ... existing implementation, no code changes
    return {
        "status": "queued",
        "message": "Check task queued successfully",
        "followed_channel_id": followed_channel_id,
        "task_id": task.id,
        "method": "ytdlp_full"  # ADD this field
    }
```

**Dependencies**: None (documentation only)
**Risk**: None - backward compatible

---

## PHASE 4: Frontend Updates

**Goal**: Add RSS option to UI and wire up to new endpoint

### Task 4.1: Update Context Menu

**File**: `frontend/src/components/features/subscriptions/followed-channels-list.tsx`

Update the dropdown menu to include both options:

```typescript
<DropdownMenuContent align="end">
  {/* NEW: RSS-based check */}
  <DropdownMenuItem
    onClick={onTriggerCheckRss}
    disabled={isCheckRssPending || isSearchingRss}
  >
    <Zap
      className={cn(
        "h-4 w-4 mr-2",
        (isCheckRssPending || isSearchingRss) && "animate-spin"
      )}
    />
    Search for Latest Videos (RSS Feed)
  </DropdownMenuItem>

  {/* UPDATED: Original yt-dlp check */}
  <DropdownMenuItem
    onClick={onTriggerCheck}
    disabled={isCheckPending || isSearching}
  >
    <RefreshCw
      className={cn(
        "h-4 w-4 mr-2",
        (isCheckPending || isSearching) && "animate-spin"
      )}
    />
    Search for Recent Videos (Slow API)
  </DropdownMenuItem>

  {/* Existing items: Backfill, Settings, Unfollow */}
</DropdownMenuContent>
```

Add handlers for RSS check:

```typescript
const triggerCheckRssMutation = useTriggerCheckRss()

const handleTriggerCheckRss = async () => {
  try {
    await triggerCheckRssMutation.mutateAsync(channel.id)
  } catch (error) {
    console.error("Failed to trigger RSS check:", error)
  }
}

const isCheckRssPending = triggerCheckRssMutation.isPending
const isSearchingRss =
  channelTaskStatus?.status === "PROGRESS" &&
  channelTaskStatus?.task_name?.includes("rss")
```

**Dependencies**: Task 4.2
**Risk**: Low

### Task 4.2: Create RSS Mutation Hook

**File**: `frontend/src/hooks/use-followed-channels.ts`

Add new mutation hook:

```typescript
export function useTriggerCheckRss() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id: number) => {
      const response = await apiClient.triggerCheckRss(id)
      return { channelId: id, taskId: response.task_id }
    },
    onSuccess: (data) => {
      // Invalidate to refresh channel list
      queryClient.invalidateQueries({ queryKey: followedChannelKeys.all })

      // Start polling for this specific channel's task status
      queryClient.invalidateQueries({
        queryKey: ["task-status", "channel", data.channelId],
      })

      // Also invalidate notifications
      queryClient.invalidateQueries({ queryKey: ["notifications"] })

      toast.success("RSS check task queued successfully")
    },
    onError: (error: Error) => {
      toast.error(`Failed to trigger RSS check: ${error.message}`)
    },
  })
}
```

**Dependencies**: Task 4.3
**Risk**: Low

### Task 4.3: Add API Client Method

**File**: `frontend/src/lib/api-client.ts`

```typescript
async triggerCheckRss(id: number): Promise<{
    task_id: string
    status: string
    message: string
    followed_channel_id: number
    method: string
}> {
    return this.request<...>(
        `/followed-channels/${id}/check-rss`,
        { method: "POST" }
    )
}
```

**Dependencies**: Phase 3 complete
**Risk**: Low

### Task 4.4: Update TypeScript Types

**File**: `frontend/src/types/index.ts`

Add discriminator for task method (optional):

```typescript
export interface CheckTaskResponse {
  task_id: string
  status: string
  message: string
  followed_channel_id: number
  method: "ytdlp_full" | "rss_feed" // NEW
}
```

**Dependencies**: None
**Risk**: None

---

## PHASE 5: Testing & Documentation

**Goal**: Validate implementation and update documentation

### Task 5.1: Integration Testing

Test scenarios:

1. **RSS check on channel with new videos**

   - Follow a channel
   - Trigger RSS check
   - Verify new videos discovered
   - Check notifications

2. **RSS check on channel with no new videos**

   - Trigger RSS check twice
   - Verify no duplicates created
   - Check notification count

3. **RSS check with auto-approve enabled**

   - Enable auto-approve
   - Trigger RSS check
   - Verify episode creation tasks queued

4. **Yt-dlp check still works**

   - Trigger original check method
   - Verify behavior unchanged

5. **Both methods work independently**

   - Trigger RSS check
   - Immediately trigger yt-dlp check
   - Verify both tasks execute

6. **RSS feed error handling**
   - Test with invalid channel ID
   - Verify error notification
   - Task marked as FAILURE

**Risk**: Low - validation only

### Task 5.2: Performance Comparison

Create performance metrics:

```python
# Log timing data in both tasks
import time

start_time = time.time()
# ... discovery logic ...
elapsed_time = time.time() - start_time

logger.info(f"Discovery took {elapsed_time:.2f}s for {len(new_videos)} videos")
```

Expected results:

- RSS method: ~5-10 seconds for 10-15 videos
- Yt-dlp method: ~30-60 seconds for 50 videos

**Risk**: Low

### Task 5.3: Update Technical Documentation

**File**: `docs/documentation/TECHNICAL-ANALYSIS-FEATURE-follow-channels-architecture.md`

Add new section:

```markdown
### Discovery Method Comparison

| Method      | Speed          | Video Count       | Use Case                         |
| ----------- | -------------- | ----------------- | -------------------------------- |
| RSS Feed    | Fast (~5-10s)  | Last 10-15 videos | Frequent checks, active channels |
| Yt-dlp Full | Slow (~30-60s) | Up to 50 videos   | Deep scans, historical discovery |

### RSS Feed Discovery Workflow

1. Fetch YouTube RSS feed (Atom XML)
2. Parse video IDs from feed (~10-15 recent videos)
3. Check ALL video IDs against database
4. For new videos, fetch full metadata via yt-dlp (sequential)
5. Save to database, handle auto-approve, send notifications
```

**Risk**: None

### Task 5.4: Update CLAUDE.md

**File**: `CLAUDE.md`

Add to "Key Features and Workflows" section:

```markdown
- **Check for New Videos**: Two discovery methods available:
  - **RSS Feed (Fast)**: Uses YouTube channel RSS feed to identify last 10-15 videos, then yt-dlp for metadata
  - **Yt-dlp Full (Comprehensive)**: Uses yt-dlp to scan up to 50 recent videos with full metadata
```

**Risk**: None

---

## Implementation Order

### Recommended Sequence

1. **Phase 1** (Backend refactoring) - MUST complete first
2. **Phase 2** (RSS implementation) - After Phase 1
3. **Phase 3** (API endpoints) - After Phase 2
4. **Phase 4** (Frontend) - Can start after Phase 3 Task 3.1
5. **Phase 5** (Testing) - Continuous throughout, final validation at end

### Deployment Strategy

1. Deploy backend changes first (Phases 1-3)
2. Test backend endpoints manually
3. Deploy frontend changes (Phase 4)
4. Monitor for errors
5. Rollback plan: Disable RSS endpoint, keep yt-dlp method working

---

## Critical Files Summary

### New Files to Create (11 files)

**Backend (7 files)**:

1. `backend/app/domain/services/video_discovery_strategy.py` - Strategy interface
2. `backend/app/infrastructure/services/ytdlp_discovery_strategy.py` - Existing logic refactored
3. `backend/app/infrastructure/services/youtube_rss_service.py` - RSS fetching/parsing
4. `backend/app/infrastructure/services/rss_discovery_strategy.py` - RSS discovery logic
5. `backend/app/infrastructure/tasks/channel_check_rss_tasks.py` - New Celery task
6. (No new files, just updates) - API endpoint, DI

**Frontend (0 new files, just updates)**:

- All changes are modifications to existing files

### Files to Modify (6 files)

**Backend (4 files)**:

1. `backend/app/core/dependencies.py` - Add DI factories
2. `backend/app/presentation/api/v1/followed_channels.py` - Add RSS endpoint
3. `backend/app/infrastructure/tasks/channel_check_tasks.py` - Use strategy pattern

**Frontend (2 files)**:

1. `frontend/src/components/features/subscriptions/followed-channels-list.tsx` - Menu updates
2. `frontend/src/hooks/use-followed-channels.ts` - New mutation hook
3. `frontend/src/lib/api-client.ts` - New API method

**Documentation (2 files)**:

1. `docs/documentation/TECHNICAL-ANALYSIS-FEATURE-follow-channels-architecture.md`
2. `CLAUDE.md`

---

## Risk Assessment

### High Risk Areas

- **None** - All changes are additive and isolated

### Medium Risk Areas

1. **Phase 1 Refactoring** - Strategy pattern introduction
   - **Mitigation**: Thorough testing, no behavior changes
2. **RSS Parsing** - External XML format dependency
   - **Mitigation**: Error handling, fallback to yt-dlp method exists
3. **Sequential yt-dlp Calls** - Could be slow for 15 videos
   - **Mitigation**: Still faster than listing 50 videos

### Low Risk Areas

- Frontend changes (mirrors existing patterns)
- API endpoint additions (follows existing structure)
- Documentation updates

---

## Success Criteria

1. ✅ Two independent check methods available in UI
2. ✅ RSS method faster than yt-dlp method for recent videos
3. ✅ No breaking changes to existing functionality
4. ✅ Both methods share notification system
5. ✅ Auto-approve works with both methods
6. ✅ Task status polling works for both task types
7. ✅ Strategy pattern allows future extensions
8. ✅ All tests pass
9. ✅ Documentation complete

---

## Future Enhancements (Out of Scope)

- Scheduled automatic RSS checks (cron job)
- YouTube Data API v3 integration (another strategy)
- Webhook-based discovery
- Parallel yt-dlp metadata fetching
- RSS feed caching
- User preference for default method

---

**End of Plan**
