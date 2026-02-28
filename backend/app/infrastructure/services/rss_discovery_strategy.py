"""
RSS Discovery Strategy Implementation

This module implements the video discovery strategy using YouTube RSS feeds
for video IDs and yt-dlp for metadata extraction.
"""

import logging
from typing import List
from datetime import datetime

from app.domain.services.video_discovery_strategy import VideoDiscoveryStrategy
from app.domain.entities.followed_channel import FollowedChannel
from app.domain.entities.youtube_video import YouTubeVideo, YouTubeVideoState
from app.domain.services.youtube_metadata_service import YouTubeMetadataServiceInterface
from app.domain.repositories.youtube_video_repository import YouTubeVideoRepository
from app.infrastructure.services.youtube_rss_service import YouTubeRSSService

logger = logging.getLogger(__name__)


class RSSDiscoveryStrategy(VideoDiscoveryStrategy):
    """
    Discovery strategy using RSS feed for video IDs, yt-dlp for metadata.

    This implementation:
    1. Fetches YouTube RSS feed (returns last ~10-15 videos)
    2. Checks ALL video IDs against the database
    3. For new videos, extracts full metadata using yt-dlp (sequential calls)
    4. Saves new videos to the database
    5. Returns list of saved video entities

    Note: RSS feeds only return the most recent 10-15 videos, so this is best
    for frequent checks on active channels.
    """

    def __init__(
        self,
        rss_service: YouTubeRSSService,
        metadata_service: YouTubeMetadataServiceInterface,
        youtube_video_repository: YouTubeVideoRepository
    ):
        """
        Initialize the RSS discovery strategy.

        Args:
            rss_service: Service for fetching YouTube RSS feeds
            metadata_service: Service for extracting YouTube metadata using yt-dlp
            youtube_video_repository: Repository for YouTube videos
        """
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
        4. Save new videos to database
        5. Return list of saved video entities

        Args:
            followed_channel: The channel to check for new videos
            max_videos: Ignored by RSS strategy (always returns ~10-15 from feed)

        Returns:
            List of new YouTubeVideo entities (already persisted)

        Raises:
            Exception: If RSS fetch or discovery fails
        """
        logger.info(
            f"[RSSDiscoveryStrategy] Discovering new videos for channel {followed_channel.id} "
            f"({followed_channel.youtube_channel_name}) using RSS feed"
        )

        # Extract channel ID from followed_channel
        channel_id = followed_channel.youtube_channel_id

        if not channel_id:
            # Attempt extraction from URL
            logger.warning(
                f"[RSSDiscoveryStrategy] No youtube_channel_id found, attempting extraction from URL"
            )
            channel_id = self._extract_channel_id(followed_channel.youtube_channel_url)

        # Fetch RSS feed
        rss_videos = await self.rss_service.fetch_channel_rss(channel_id)
        logger.info(
            f"[RSSDiscoveryStrategy] RSS feed returned {len(rss_videos)} videos for channel {channel_id}"
        )

        if not rss_videos:
            logger.info(f"[RSSDiscoveryStrategy] No videos in RSS feed for channel {channel_id}")
            return []

        # Check ALL RSS video IDs against database
        new_videos = []

        for rss_video in rss_videos:
            video_id = rss_video.get('video_id')
            if not video_id:
                logger.warning(f"[RSSDiscoveryStrategy] Skipping RSS entry with no video_id")
                continue

            # Check if video already exists in database
            existing_video = await self.youtube_video_repository.get_by_video_id(video_id)

            if existing_video:
                logger.debug(f"[RSSDiscoveryStrategy] Video {video_id} already exists, skipping")
                continue

            # This is a new video - fetch full metadata using yt-dlp (sequential call)
            try:
                logger.info(f"[RSSDiscoveryStrategy] Fetching metadata for new video: {video_id}")

                full_metadata = await self.metadata_service.extract_video_metadata(
                    rss_video.get('url')
                )

                # Create YouTubeVideo entity
                youtube_video = YouTubeVideo(
                    id=None,
                    video_id=video_id,
                    followed_channel_id=followed_channel.id,
                    title=full_metadata.get('title') or rss_video.get('title') or 'Unknown',
                    description=full_metadata.get('description') or '',
                    url=rss_video.get('url'),
                    thumbnail_url=full_metadata.get('thumbnail_url'),
                    publish_date=full_metadata.get('publish_date') or datetime.utcnow(),
                    duration=full_metadata.get('duration'),
                    view_count=full_metadata.get('view_count'),
                    like_count=full_metadata.get('like_count'),
                    comment_count=full_metadata.get('comment_count'),
                    metadata_json=full_metadata.get('metadata_json'),
                    state=YouTubeVideoState.PENDING_REVIEW,
                    episode_id=None,
                    reviewed_at=None,
                )

                # Save to database
                saved_video = await self.youtube_video_repository.create(youtube_video)
                new_videos.append(saved_video)

                logger.info(
                    f"[RSSDiscoveryStrategy] Discovered new video: {saved_video.title} ({saved_video.video_id})"
                )

            except Exception as e:
                # Log error but continue with other videos
                logger.error(
                    f"[RSSDiscoveryStrategy] Failed to extract metadata for video {video_id}: {e}",
                    exc_info=True
                )
                # Continue with next video even if this one fails
                continue

        logger.info(
            f"[RSSDiscoveryStrategy] Discovered {len(new_videos)} new videos via RSS "
            f"for channel {channel_id}"
        )
        return new_videos

    def _extract_channel_id(self, channel_url: str) -> str:
        """
        Extract channel ID from various YouTube URL formats.

        Args:
            channel_url: YouTube channel URL

        Returns:
            Channel ID (UCxxx format)

        Raises:
            ValueError: If channel ID cannot be extracted
        """
        # Handle UC format: https://www.youtube.com/channel/UCxxx
        if '/channel/' in channel_url:
            channel_id = channel_url.split('/channel/')[-1].split('/')[0].split('?')[0]
            logger.debug(f"[RSSDiscoveryStrategy] Extracted channel ID from URL: {channel_id}")
            return channel_id

        # Handle @handle format - this should already be stored in youtube_channel_id
        # If we reach here, the channel ID is not extractable from URL
        raise ValueError(
            f"Cannot extract channel ID from URL: {channel_url}. "
            "The channel ID should be stored in youtube_channel_id field."
        )
