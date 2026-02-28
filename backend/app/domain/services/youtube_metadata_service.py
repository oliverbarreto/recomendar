"""
YouTube Metadata Service Domain Layer

Abstract interface for YouTube metadata extraction using yt-dlp.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime


class YouTubeMetadataServiceInterface(ABC):
    """
    Interface for YouTube metadata extraction service
    
    Provides methods to extract channel and video metadata from YouTube
    using yt-dlp library.
    """
    
    @abstractmethod
    async def extract_channel_info(self, channel_url: str) -> Dict[str, Any]:
        """
        Extract channel metadata from YouTube
        
        Args:
            channel_url: YouTube channel URL (supports various formats:
                - https://www.youtube.com/channel/UCxxxxx
                - https://www.youtube.com/@channelname
                - https://www.youtube.com/user/username
                - @channelname)
        
        Returns:
            Dictionary with channel metadata:
            - channel_id: YouTube channel ID (UCxxxxx or @handle)
            - name: Channel name
            - description: Channel description
            - url: Channel URL
            - thumbnail_url: Channel thumbnail URL
            - created_date: Optional channel creation date if available
        
        Raises:
            MetadataExtractionError: If extraction fails
            InvalidChannelURLError: If URL is invalid
        """
        pass
    
    @abstractmethod
    async def extract_video_metadata(self, video_url: str) -> Dict[str, Any]:
        """
        Extract video metadata from YouTube
        
        Args:
            video_url: YouTube video URL
        
        Returns:
            Dictionary with video metadata:
            - video_id: YouTube video ID
            - title: Video title
            - description: Video description
            - url: Video URL
            - thumbnail_url: Video thumbnail URL
            - publish_date: Video publish date (datetime)
            - duration: Video duration in seconds
            - view_count: View count
            - like_count: Like count
            - comment_count: Comment count
            - channel_id: YouTube channel ID
            - channel_name: Channel name
            - channel_url: Channel URL
            - metadata_json: Raw yt-dlp metadata as JSON string
        
        Raises:
            MetadataExtractionError: If extraction fails
            InvalidVideoURLError: If URL is invalid
        """
        pass
    
    @abstractmethod
    async def list_channel_videos(
        self,
        channel_url: str,
        max_videos: int = 50,
        year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        List videos from a YouTube channel
        
        Args:
            channel_url: YouTube channel URL
            max_videos: Maximum number of videos to fetch (default: 50)
            year: Optional year to filter videos (only videos from this year)
        
        Returns:
            List of video dictionaries, each containing:
            - video_id: YouTube video ID
            - title: Video title
            - url: Video URL
            - publish_date: Video publish date (datetime)
            - thumbnail_url: Optional thumbnail URL
        
        Raises:
            MetadataExtractionError: If extraction fails
            InvalidChannelURLError: If URL is invalid
        """
        pass
    
    @abstractmethod
    async def get_channel_creation_date(self, channel_url: str) -> Optional[datetime]:
        """
        Attempt to extract channel creation date from YouTube
        
        Note: This may not always be available depending on YouTube API/data
        
        Args:
            channel_url: YouTube channel URL
        
        Returns:
            Channel creation date if available, None otherwise
        
        Raises:
            MetadataExtractionError: If extraction fails
        """
        pass







