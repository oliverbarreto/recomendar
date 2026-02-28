"""
Yt-dlp Discovery Strategy Implementation

This module implements the video discovery strategy using yt-dlp for both
listing videos and extracting metadata. This is the original/existing implementation
refactored to use the Strategy pattern.
"""

import logging
from typing import List
from datetime import datetime

from app.domain.services.video_discovery_strategy import VideoDiscoveryStrategy
from app.domain.entities.followed_channel import FollowedChannel
from app.domain.entities.youtube_video import YouTubeVideo, YouTubeVideoState
from app.domain.services.youtube_metadata_service import YouTubeMetadataServiceInterface
from app.domain.repositories.youtube_video_repository import YouTubeVideoRepository

logger = logging.getLogger(__name__)


class YtdlpDiscoveryStrategy(VideoDiscoveryStrategy):
    """
    Discovery strategy using yt-dlp for both listing and metadata extraction.

    This implementation:
    1. Uses yt-dlp to list channel videos (up to max_videos)
    2. Checks each video ID against the database
    3. For new videos, extracts full metadata using yt-dlp
    4. Saves new videos to the database
    5. Returns list of saved video entities
    """

    def __init__(
        self,
        metadata_service: YouTubeMetadataServiceInterface,
        youtube_video_repository: YouTubeVideoRepository
    ):
        """
        Initialize the yt-dlp discovery strategy.

        Args:
            metadata_service: Service for extracting YouTube metadata using yt-dlp
            youtube_video_repository: Repository for YouTube videos
        """
        self.metadata_service = metadata_service
        self.youtube_video_repository = youtube_video_repository

    async def discover_new_videos(
        self,
        followed_channel: FollowedChannel,
        max_videos: int = 50
    ) -> List[YouTubeVideo]:
        """
        Discover new videos from a followed channel using yt-dlp.

        This method:
        1. Fetches latest videos from YouTube channel using yt-dlp
        2. Compares with existing videos in database
        3. Extracts full metadata for new videos
        4. Saves new videos to database
        5. Returns list of newly created video entities

        Args:
            followed_channel: The followed channel to check
            max_videos: Maximum number of recent videos to check (default: 50)

        Returns:
            List of new YouTubeVideo entities (already persisted)

        Raises:
            Exception: If discovery fails
        """
        logger.info(
            f"[YtdlpDiscoveryStrategy] Discovering new videos for channel {followed_channel.id} "
            f"({followed_channel.youtube_channel_name}) using yt-dlp (max: {max_videos})"
        )

        # Fetch latest videos from YouTube using yt-dlp
        video_metadata_list = await self.metadata_service.list_channel_videos(
            channel_url=followed_channel.youtube_channel_url,
            max_videos=max_videos,
            year=None  # Get all recent videos regardless of year
        )

        if not video_metadata_list:
            logger.info(f"[YtdlpDiscoveryStrategy] No videos found for channel {followed_channel.id}")
            return []

        logger.info(
            f"[YtdlpDiscoveryStrategy] Found {len(video_metadata_list)} videos from yt-dlp "
            f"for channel {followed_channel.id}"
        )

        new_videos = []

        # Check each video to see if it's new
        for video_meta in video_metadata_list:
            video_id = video_meta.get("video_id")
            if not video_id:
                logger.warning(f"[YtdlpDiscoveryStrategy] Skipping video with no video_id")
                continue

            # Check if video already exists in database
            existing_video = await self.youtube_video_repository.get_by_video_id(video_id)

            if existing_video:
                # Video already exists, skip
                logger.debug(f"[YtdlpDiscoveryStrategy] Video {video_id} already exists, skipping")
                continue

            # This is a new video - extract full metadata and create entity
            try:
                # Extract full metadata for the video using yt-dlp
                full_metadata = await self.metadata_service.extract_video_metadata(
                    video_meta.get("url") or f"https://www.youtube.com/watch?v={video_id}"
                )

                # Create YouTubeVideo entity
                youtube_video = YouTubeVideo(
                    id=None,
                    video_id=video_id,
                    followed_channel_id=followed_channel.id,
                    title=full_metadata.get("title") or video_meta.get("title") or "Unknown",
                    description=full_metadata.get("description") or "",
                    url=full_metadata.get("url") or video_meta.get("url"),
                    thumbnail_url=full_metadata.get("thumbnail_url") or video_meta.get("thumbnail_url"),
                    publish_date=full_metadata.get("publish_date") or video_meta.get("publish_date") or datetime.utcnow(),
                    duration=full_metadata.get("duration") or video_meta.get("duration"),
                    view_count=full_metadata.get("view_count"),
                    like_count=full_metadata.get("like_count"),
                    comment_count=full_metadata.get("comment_count"),
                    metadata_json=full_metadata.get("metadata_json"),
                    state=YouTubeVideoState.PENDING_REVIEW,
                )

                # Save to database
                saved_video = await self.youtube_video_repository.create(youtube_video)
                new_videos.append(saved_video)

                logger.info(
                    f"[YtdlpDiscoveryStrategy] Discovered new video: {saved_video.title} ({saved_video.video_id})"
                )

            except Exception as e:
                logger.error(
                    f"[YtdlpDiscoveryStrategy] Error creating video entity for {video_id}: {e}",
                    exc_info=True
                )
                # Continue with next video even if this one fails
                continue

        logger.info(
            f"[YtdlpDiscoveryStrategy] Discovered {len(new_videos)} new videos "
            f"for channel {followed_channel.id}"
        )
        return new_videos
