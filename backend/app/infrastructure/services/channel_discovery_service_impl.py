"""
Channel Discovery Service Implementation

Infrastructure layer implementation for discovering new videos from followed channels.
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.domain.services.channel_discovery_service import ChannelDiscoveryServiceInterface
from app.domain.entities.followed_channel import FollowedChannel
from app.domain.entities.youtube_video import YouTubeVideo, YouTubeVideoState
from app.domain.services.youtube_metadata_service import YouTubeMetadataServiceInterface
from app.domain.repositories.youtube_video_repository import YouTubeVideoRepository
from app.domain.repositories.followed_channel_repository import FollowedChannelRepository

logger = logging.getLogger(__name__)


class DiscoveryError(Exception):
    """Exception raised when discovery fails"""
    pass


class ChannelDiscoveryServiceImpl(ChannelDiscoveryServiceInterface):
    """
    Implementation of channel discovery service
    
    Provides business logic for discovering new videos from followed channels
    and managing the discovery workflow.
    """
    
    def __init__(
        self,
        metadata_service: YouTubeMetadataServiceInterface,
        youtube_video_repository: YouTubeVideoRepository,
        followed_channel_repository: FollowedChannelRepository
    ):
        """
        Initialize the channel discovery service
        
        Args:
            metadata_service: Service for extracting YouTube metadata
            youtube_video_repository: Repository for YouTube videos
            followed_channel_repository: Repository for followed channels
        """
        self.metadata_service = metadata_service
        self.youtube_video_repository = youtube_video_repository
        self.followed_channel_repository = followed_channel_repository
    
    async def discover_new_videos(
        self,
        followed_channel: FollowedChannel,
        max_videos: int = 50
    ) -> List[YouTubeVideo]:
        """
        Discover new videos from a followed channel
        
        This method:
        1. Fetches latest videos from YouTube channel
        2. Compares with existing videos in database
        3. Returns list of new videos that need to be created
        
        Args:
            followed_channel: The followed channel to check
            max_videos: Maximum number of recent videos to check
        
        Returns:
            List of new YouTubeVideo entities (may be empty)
        
        Raises:
            DiscoveryError: If discovery fails
        """
        try:
            logger.info(f"Discovering new videos for channel {followed_channel.id} ({followed_channel.youtube_channel_name})")
            
            # Fetch latest videos from YouTube
            video_metadata_list = await self.metadata_service.list_channel_videos(
                channel_url=followed_channel.youtube_channel_url,
                max_videos=max_videos,
                year=None  # Get all recent videos regardless of year
            )
            
            if not video_metadata_list:
                logger.info(f"No videos found for channel {followed_channel.id}")
                return []
            
            new_videos = []
            
            # Check each video to see if it's new
            for video_meta in video_metadata_list:
                video_id = video_meta.get("video_id")
                if not video_id:
                    continue
                
                # Check if video already exists
                existing_video = await self.youtube_video_repository.get_by_video_id(video_id)
                
                if existing_video:
                    # Video already exists, skip
                    continue
                
                # This is a new video - create YouTubeVideo entity
                try:
                    # Extract full metadata for the video
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
                    
                    logger.info(f"Discovered new video: {saved_video.title} ({saved_video.video_id})")
                    
                except Exception as e:
                    logger.error(f"Error creating video entity for {video_id}: {e}")
                    continue
            
            # Update last_checked timestamp
            if new_videos:
                await self.followed_channel_repository.update_last_checked(followed_channel.id)
            
            logger.info(f"Discovered {len(new_videos)} new videos for channel {followed_channel.id}")
            return new_videos
            
        except Exception as e:
            logger.error(f"Error discovering videos for channel {followed_channel.id}: {e}")
            raise DiscoveryError(f"Failed to discover videos: {str(e)}")
    
    async def backfill_channel_videos(
        self,
        followed_channel: FollowedChannel,
        max_videos: int = 20,
        year: Optional[int] = None
    ) -> List[YouTubeVideo]:
        """
        Backfill historical videos from a followed channel
        
        This method fetches historical videos and creates YouTubeVideo
        entities for them. Used when first following a channel or
        when user requests backfill for specific years.
        
        Args:
            followed_channel: The followed channel to backfill
            max_videos: Maximum number of videos to fetch
            year: Optional year to filter videos (None for all years)
        
        Returns:
            List of YouTubeVideo entities created (may be empty)
        
        Raises:
            DiscoveryError: If backfill fails
        """
        try:
            logger.info(f"Backfilling videos for channel {followed_channel.id} (year: {year}, max: {max_videos})")
            
            # Fetch videos from YouTube
            video_metadata_list = await self.metadata_service.list_channel_videos(
                channel_url=followed_channel.youtube_channel_url,
                max_videos=max_videos,
                year=year
            )
            
            if not video_metadata_list:
                logger.info(f"No videos found for channel {followed_channel.id}")
                return []
            
            created_videos = []
            
            # Create YouTubeVideo entities for each video
            for video_meta in video_metadata_list:
                video_id = video_meta.get("video_id")
                if not video_id:
                    continue
                
                # Check if video already exists
                existing_video = await self.youtube_video_repository.get_by_video_id(video_id)
                
                if existing_video:
                    # Video already exists, skip
                    continue
                
                # Extract full metadata for the video
                try:
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
                    created_videos.append(saved_video)
                    
                    logger.debug(f"Backfilled video: {saved_video.title} ({saved_video.video_id})")
                    
                except Exception as e:
                    logger.error(f"Error backfilling video {video_id}: {e}")
                    continue
            
            logger.info(f"Backfilled {len(created_videos)} videos for channel {followed_channel.id}")
            return created_videos
            
        except Exception as e:
            logger.error(f"Error backfilling videos for channel {followed_channel.id}: {e}")
            raise DiscoveryError(f"Failed to backfill videos: {str(e)}")
    
    async def check_for_new_videos_since(
        self,
        followed_channel: FollowedChannel,
        since_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Check for new videos published since a specific date
        
        Args:
            followed_channel: The followed channel to check
            since_date: Date to check from (if None, uses last_checked)
        
        Returns:
            List of video metadata dictionaries for new videos
        
        Raises:
            DiscoveryError: If check fails
        """
        try:
            # Use last_checked if since_date not provided
            check_date = since_date or followed_channel.last_checked or datetime.utcnow()
            
            logger.info(f"Checking for new videos since {check_date} for channel {followed_channel.id}")
            
            # Fetch recent videos from YouTube
            video_metadata_list = await self.metadata_service.list_channel_videos(
                channel_url=followed_channel.youtube_channel_url,
                max_videos=50,  # Check last 50 videos
                year=None
            )
            
            if not video_metadata_list:
                return []
            
            new_videos = []
            
            # Filter videos published after check_date
            for video_meta in video_metadata_list:
                publish_date = video_meta.get("publish_date")
                
                if publish_date and publish_date > check_date:
                    # This is a new video published after last check
                    new_videos.append(video_meta)
            
            logger.info(f"Found {len(new_videos)} new videos since {check_date} for channel {followed_channel.id}")
            return new_videos
            
        except Exception as e:
            logger.error(f"Error checking for new videos for channel {followed_channel.id}: {e}")
            raise DiscoveryError(f"Failed to check for new videos: {str(e)}")







