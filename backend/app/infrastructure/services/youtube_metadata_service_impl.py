"""
YouTube Metadata Service Implementation

Infrastructure layer implementation for YouTube metadata extraction using yt-dlp.
"""
import asyncio
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import yt_dlp

from app.domain.services.youtube_metadata_service import YouTubeMetadataServiceInterface

logger = logging.getLogger(__name__)


class MetadataExtractionError(Exception):
    """Exception raised when metadata extraction fails"""
    pass


class InvalidChannelURLError(Exception):
    """Exception raised when channel URL is invalid"""
    pass


class InvalidVideoURLError(Exception):
    """Exception raised when video URL is invalid"""
    pass


class YouTubeMetadataServiceImpl(YouTubeMetadataServiceInterface):
    """
    Implementation of YouTube metadata extraction service using yt-dlp
    
    Provides methods to extract channel and video metadata from YouTube.
    Uses full metadata extraction for accurate dates and comprehensive information.
    """
    
    def __init__(self):
        """Initialize the YouTube metadata service"""
        # Base yt-dlp options for metadata extraction
        self.ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,  # Full extraction for accurate metadata
            "skip_unavailable_videos": True,  # Skip members-only, private, deleted videos
            "ignoreerrors": True,  # Continue on errors
            "no_color": True,
            "progress_hooks": [],  # Disable progress hooks
        }
    
    async def extract_channel_info(self, channel_url: str) -> Dict[str, Any]:
        """
        Extract channel metadata from YouTube
        
        Args:
            channel_url: YouTube channel URL (supports various formats)
        
        Returns:
            Dictionary with channel metadata
        
        Raises:
            MetadataExtractionError: If extraction fails
            InvalidChannelURLError: If URL is invalid
        """
        try:
            # 🤖 Run yt-dlp extraction in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(
                None,
                self._extract_channel_info_sync,
                channel_url
            )

            if not info:
                raise MetadataExtractionError(f"Failed to extract channel info from {channel_url}")

            # 🤖 Extract channel_id - possible from different keys
            channel_id = info.get("channel_id") or info.get("id")

            # 🤖 Retrieve the most correct thumbnail URL
            thumbnail_url = None
            if "thumbnail" in info:
                thumbnail_url = info["thumbnail"]
            elif "thumbnails" in info and info["thumbnails"]:
                # Use the last thumbnail in the yt-dlp list (often highest res)
                thumbnail_candidates = info.get("thumbnails", [])
                # Ensure it's a list and has a 'url'
                if isinstance(thumbnail_candidates, list) and thumbnail_candidates and "url" in thumbnail_candidates[-1]:
                    thumbnail_url = thumbnail_candidates[-1]["url"]

            # Try to get channel creation date if available (not available with extract_flat)
            created_date = None

            return {
                "channel_id": channel_id,
                "name": info.get("channel") or info.get("title") or "Unknown Channel",
                "description": info.get("description") or "",
                "url": info.get("channel_url") or info.get("webpage_url") or info.get("url") or channel_url,
                "thumbnail_url": thumbnail_url,
                "created_date": created_date,  # Not available with extract_flat
            }
        except Exception as e:
            if isinstance(e, (MetadataExtractionError, InvalidChannelURLError)):
                raise
            logger.error(f"Error extracting channel info from {channel_url}: {e}")
            raise MetadataExtractionError(f"Failed to extract channel info: {str(e)}")
    
    def _extract_channel_info_sync(self, channel_url: str) -> Optional[Dict[str, Any]]:
        """
        Synchronous channel info extraction - optimized for speed
        
        Uses extract_flat=True with playlistend=0 to only get channel metadata
        without extracting video information, making it much faster.
        """
        try:
            # Use optimized options for channel metadata only (no video list)
            # This matches the user's suggested approach for fast channel info extraction
            channel_opts = {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": True,    # Flat extraction - only metadata, no video entries
                "skip_download": True,  # Don't download anything
                "playlistend": 0,       # Only metadata, no entries
                "ignoreerrors": True,
                "no_color": True,
            }
            with yt_dlp.YoutubeDL(channel_opts) as ydl:
                info = ydl.extract_info(channel_url, download=False)
                return info
        except Exception as e:
            logger.error(f"Error in sync channel extraction: {e}")
            return None
    
    async def extract_video_metadata(self, video_url: str) -> Dict[str, Any]:
        """
        Extract video metadata from YouTube
        
        Args:
            video_url: YouTube video URL
        
        Returns:
            Dictionary with video metadata
        
        Raises:
            MetadataExtractionError: If extraction fails
            InvalidVideoURLError: If URL is invalid
        """
        try:
            # Run yt-dlp extraction in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(
                None,
                self._extract_video_metadata_sync,
                video_url
            )
            
            if not info:
                raise MetadataExtractionError(f"Failed to extract video metadata from {video_url}")
            
            # Parse publish date
            publish_date = None
            if "upload_date" in info:
                try:
                    # yt-dlp provides upload_date as YYYYMMDD string
                    upload_date_str = str(info["upload_date"])
                    if len(upload_date_str) == 8:
                        publish_date = datetime.strptime(upload_date_str, "%Y%m%d")
                except (ValueError, KeyError) as e:
                    logger.warning(f"Could not parse upload_date: {e}")
            
            # If no upload_date, try timestamp
            if not publish_date and "timestamp" in info:
                try:
                    publish_date = datetime.fromtimestamp(info["timestamp"])
                except (ValueError, OSError) as e:
                    logger.warning(f"Could not parse timestamp: {e}")
            
            # Default to now if no date found
            if not publish_date:
                publish_date = datetime.utcnow()
            
            # Extract channel info
            channel_id = info.get("channel_id") or info.get("uploader_id")
            channel_name = info.get("channel") or info.get("uploader")
            channel_url = info.get("channel_url") or info.get("uploader_url")
            
            return {
                "video_id": info.get("id"),
                "title": info.get("title"),
                "description": info.get("description") or "",
                "url": info.get("webpage_url") or info.get("url") or video_url,
                "thumbnail_url": info.get("thumbnail"),
                "publish_date": publish_date,
                "duration": info.get("duration"),
                "view_count": info.get("view_count"),
                "like_count": info.get("like_count"),
                "comment_count": info.get("comment_count"),
                "channel_id": channel_id,
                "channel_name": channel_name,
                "channel_url": channel_url,
                "metadata_json": json.dumps(info),  # Store raw metadata as JSON string
            }
        except Exception as e:
            if isinstance(e, (MetadataExtractionError, InvalidVideoURLError)):
                raise
            logger.error(f"Error extracting video metadata from {video_url}: {e}")
            raise MetadataExtractionError(f"Failed to extract video metadata: {str(e)}")
    
    def _extract_video_metadata_sync(self, video_url: str) -> Optional[Dict[str, Any]]:
        """Synchronous video metadata extraction"""
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                return info
        except Exception as e:
            logger.error(f"Error in sync video extraction: {e}")
            return None
    
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
            max_videos: Maximum number of videos to fetch
            year: Optional year to filter videos
        
        Returns:
            List of video dictionaries
        """
        try:
            # Run yt-dlp extraction in thread pool
            loop = asyncio.get_event_loop()
            videos = await loop.run_in_executor(
                None,
                self._list_channel_videos_sync,
                channel_url,
                max_videos,
                year
            )
            
            return videos or []
        except Exception as e:
            logger.error(f"Error listing channel videos from {channel_url}: {e}")
            raise MetadataExtractionError(f"Failed to list channel videos: {str(e)}")
    
    def _list_channel_videos_sync(
        self,
        channel_url: str,
        max_videos: int = 50,
        year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Synchronous channel video listing"""
        try:
            # First, get channel ID for proper URL construction
            channel_id = None
            ydl_opts_flat = self.ydl_opts.copy()
            ydl_opts_flat["extract_flat"] = True  # Fast extraction for channel ID
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts_flat) as ydl:
                    info = ydl.extract_info(channel_url, download=False)
                    # Extract channel ID
                    if "entries" in info and info["entries"]:
                        first_entry = info["entries"][0]
                        channel_id = first_entry.get("channel_id") or first_entry.get("id")
                    elif "channel_id" in info:
                        channel_id = info["channel_id"]
                    elif "id" in info:
                        channel_id = info["id"]
            except Exception as e:
                logger.warning(f"Could not extract channel ID, using direct URL: {e}")
            
            # Construct videos URL
            if channel_id and channel_id.startswith("UC"):
                videos_url = f"https://www.youtube.com/channel/{channel_id}/videos"
            elif channel_id:
                videos_url = f"https://www.youtube.com/@{channel_id}/videos" if not channel_id.startswith("@") else f"https://www.youtube.com/{channel_id}/videos"
            else:
                videos_url = channel_url
            
            # Full extraction options
            ydl_opts = self.ydl_opts.copy()
            ydl_opts["playlistend"] = max_videos
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(videos_url, download=False)
            
            videos = []
            entries = info.get("entries", [])
            if not entries and "id" in info and "title" in info:
                # Single video entry
                entries = [info]
            
            # Flatten nested entries
            flattened_entries = []
            for entry in entries:
                if entry is None:
                    continue
                if "entries" in entry and isinstance(entry["entries"], list):
                    flattened_entries.extend(entry["entries"])
                else:
                    flattened_entries.append(entry)
            
            current_year = datetime.now().year
            target_year = year or current_year
            
            for entry in flattened_entries:
                if entry is None:
                    continue
                
                video_id = entry.get("id")
                if not video_id:
                    continue
                
                # Parse publish date
                publish_date = None
                if "upload_date" in entry:
                    try:
                        upload_date_str = str(entry["upload_date"])
                        if len(upload_date_str) == 8:
                            publish_date = datetime.strptime(upload_date_str, "%Y%m%d")
                    except (ValueError, KeyError):
                        pass
                
                # Filter by year if specified
                if year and publish_date and publish_date.year != year:
                    continue
                
                # Default publish_date if not available
                if not publish_date:
                    publish_date = datetime.utcnow()
                
                video_url = entry.get("webpage_url") or entry.get("url") or f"https://www.youtube.com/watch?v={video_id}"
                
                videos.append({
                    "video_id": video_id,
                    "title": entry.get("title", "Unknown"),
                    "url": video_url,
                    "publish_date": publish_date,
                    "thumbnail_url": entry.get("thumbnail"),
                    "duration": entry.get("duration"),
                })
            
            return videos
            
        except Exception as e:
            logger.error(f"Error in sync channel video listing: {e}")
            return []
    
    async def get_channel_creation_date(self, channel_url: str) -> Optional[datetime]:
        """
        Attempt to extract channel creation date from YouTube
        
        Note: This may not always be available depending on YouTube data
        
        Args:
            channel_url: YouTube channel URL
        
        Returns:
            Channel creation date if available, None otherwise
        """
        try:
            # Run yt-dlp extraction in thread pool
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(
                None,
                self._extract_channel_info_sync,
                channel_url
            )
            
            if not info:
                return None
            
            # Try to extract creation date from metadata
            # Note: YouTube doesn't always provide this information
            # We check various possible fields
            if "channel_follower_count" in info:
                # Some metadata might have creation info, but it's rare
                pass
            
            # If no creation date found, return None
            return None
            
        except Exception as e:
            logger.warning(f"Could not extract channel creation date from {channel_url}: {e}")
            return None


