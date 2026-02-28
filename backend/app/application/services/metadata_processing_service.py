"""
Metadata processing service for converting YouTube metadata to Episode entities
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
import re
import logging
from app.domain.entities.episode import Episode, EpisodeStatus
from app.domain.value_objects.video_id import VideoId
from app.domain.value_objects.duration import Duration

logger = logging.getLogger(__name__)


class MetadataProcessingError(Exception):
    """Exception raised when metadata processing fails"""
    pass


class MetadataProcessingService:
    """
    Service for processing YouTube metadata into Episode entities
    """
    
    # Keywords to filter out
    FILTERED_KEYWORDS = {
        'video', 'youtube', 'watch', 'channel', 'subscribe',
        'like', 'comment', 'share', 'playlist', 'music'
    }
    
    def process_youtube_metadata(
        self, 
        channel_id: int, 
        metadata: Dict[str, Any],
        tags: Optional[List[str]] = None
    ) -> Episode:
        """
        Process YouTube metadata into Episode entity
        
        Args:
            channel_id: Channel ID to associate episode with
            metadata: Raw metadata from YouTube
            tags: Optional additional tags
            
        Returns:
            Episode entity
            
        Raises:
            MetadataProcessingError: If processing fails
        """
        try:
            logger.info(f"Processing metadata for video: {metadata.get('video_id')}")
            
            # Validate required fields
            if not metadata.get('video_id'):
                raise MetadataProcessingError("Video ID is required")

            if not metadata.get('title'):
                raise MetadataProcessingError("Title is required")

            # Create VideoId value object with yt_ prefix
            # metadata['video_id'] contains raw YouTube ID (e.g., "fuhx7VsH1mU")
            video_id = VideoId.from_youtube_id(metadata['video_id'])
            
            # Process duration
            duration = self._parse_duration(metadata.get('duration_seconds'))
            
            # Process publication date
            pub_date = self._parse_publication_date(metadata.get('publication_date'))
            
            # Clean and process keywords
            keywords = self._process_keywords(metadata.get('keywords', []), tags)
            
            # Create Episode entity
            episode = Episode(
                id=None,
                channel_id=channel_id,
                video_id=video_id,
                title=self._sanitize_title(metadata['title']),
                description=self._sanitize_description(metadata.get('description', '')),
                publication_date=pub_date,
                audio_file_path=None,  # Will be set after download
                video_url=metadata.get('video_url', video_id.youtube_url),
                thumbnail_url=metadata.get('thumbnail_url', ''),
                duration=duration,
                keywords=keywords,
                status=EpisodeStatus.PENDING,
                retry_count=0,
                download_date=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                # YouTube channel information
                youtube_channel=metadata.get('channel'),
                youtube_channel_id=metadata.get('channel_id'),
                youtube_channel_url=metadata.get('channel_url'),
                # User preferences
                is_favorited=False  # Default to not favorited
            )
            
            logger.info(f"Successfully processed metadata for episode: {episode.title}")
            return episode
            
        except Exception as e:
            logger.error(f"Failed to process metadata: {e}")
            raise MetadataProcessingError(f"Metadata processing failed: {e}")
    
    def _parse_duration(self, duration_seconds: Any) -> Optional[Duration]:
        """
        Parse duration from various formats
        """
        try:
            if duration_seconds is None:
                return None
            
            if isinstance(duration_seconds, (int, float)):
                seconds = int(duration_seconds)
                if seconds > 0:
                    return Duration(seconds)
            
            if isinstance(duration_seconds, str):
                # Try to parse string duration (e.g., "PT4M13S")
                if duration_seconds.startswith('PT'):
                    return self._parse_iso_duration(duration_seconds)
                
                # Try to parse numeric string
                try:
                    seconds = int(float(duration_seconds))
                    if seconds > 0:
                        return Duration(seconds)
                except ValueError:
                    pass
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to parse duration '{duration_seconds}': {e}")
            return None
    
    def _parse_iso_duration(self, duration_str: str) -> Optional[Duration]:
        """
        Parse ISO 8601 duration format (PT4M13S)
        """
        try:
            # Extract hours, minutes, seconds
            pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
            match = re.match(pattern, duration_str)
            
            if not match:
                return None
            
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            seconds = int(match.group(3) or 0)
            
            total_seconds = hours * 3600 + minutes * 60 + seconds
            
            if total_seconds > 0:
                return Duration(total_seconds)
            
            return None
            
        except Exception:
            return None
    
    def _parse_publication_date(self, date_value: Any) -> datetime:
        """
        Parse publication date from various formats
        """
        try:
            if isinstance(date_value, datetime):
                return date_value
            
            if isinstance(date_value, str):
                # Try YouTube format: YYYYMMDD
                if len(date_value) == 8 and date_value.isdigit():
                    return datetime.strptime(date_value, '%Y%m%d')
                
                # Try ISO format
                try:
                    return datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                except ValueError:
                    pass
                
                # Try other common formats
                formats = [
                    '%Y-%m-%d',
                    '%Y-%m-%d %H:%M:%S',
                    '%Y/%m/%d',
                    '%d/%m/%Y',
                    '%m/%d/%Y'
                ]
                
                for fmt in formats:
                    try:
                        return datetime.strptime(date_value, fmt)
                    except ValueError:
                        continue
            
        except Exception as e:
            logger.warning(f"Failed to parse publication date '{date_value}': {e}")
        
        # Fallback to current time
        return datetime.utcnow()
    
    def _process_keywords(
        self, 
        raw_keywords: List[str], 
        additional_tags: Optional[List[str]] = None
    ) -> List[str]:
        """
        Clean and filter keywords
        """
        all_keywords = []
        
        # Process raw keywords from YouTube
        if raw_keywords:
            for keyword in raw_keywords:
                if isinstance(keyword, str):
                    clean_keyword = self._clean_keyword(keyword)
                    if clean_keyword and self._is_valid_keyword(clean_keyword):
                        all_keywords.append(clean_keyword)
        
        # Add additional tags
        if additional_tags:
            for tag in additional_tags:
                if isinstance(tag, str):
                    clean_tag = self._clean_keyword(tag)
                    if clean_tag and self._is_valid_keyword(clean_tag):
                        all_keywords.append(clean_tag)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for keyword in all_keywords:
            keyword_lower = keyword.lower()
            if keyword_lower not in seen:
                seen.add(keyword_lower)
                unique_keywords.append(keyword)
        
        # Limit to reasonable number
        return unique_keywords[:20]
    
    def _clean_keyword(self, keyword: str) -> str:
        """
        Clean individual keyword
        """
        if not keyword:
            return ""
        
        # Strip whitespace and convert to lowercase
        cleaned = keyword.strip().lower()
        
        # Remove special characters except hyphens and underscores
        cleaned = re.sub(r'[^\w\s-]', '', cleaned)
        
        # Replace multiple spaces with single space
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Limit length
        if len(cleaned) > 50:
            cleaned = cleaned[:50].strip()
        
        return cleaned
    
    def _is_valid_keyword(self, keyword: str) -> bool:
        """
        Validate if keyword should be included
        """
        if not keyword or len(keyword) < 2:
            return False
        
        # Filter out common/generic keywords
        if keyword.lower() in self.FILTERED_KEYWORDS:
            return False
        
        # Filter out pure numbers
        if keyword.isdigit():
            return False
        
        # Filter out very short words (unless they're meaningful)
        meaningful_short_words = {'ai', 'ml', 'ui', 'ux', 'js', 'py', 'go'}
        if len(keyword) <= 2 and keyword.lower() not in meaningful_short_words:
            return False
        
        return True
    
    def _sanitize_title(self, title: str) -> str:
        """
        Sanitize and validate title
        """
        if not title:
            return "Untitled Episode"
        
        # Strip whitespace
        sanitized = title.strip()
        
        # Remove or replace problematic characters for file systems
        sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', sanitized)
        
        # Remove excessive whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized)
        
        # Limit length
        if len(sanitized) > 500:
            sanitized = sanitized[:497] + '...'
        
        # Ensure we have something
        if not sanitized.strip():
            sanitized = "Untitled Episode"
        
        return sanitized
    
    def _sanitize_description(self, description: str) -> str:
        """
        Sanitize description
        """
        if not description:
            return ""
        
        # Strip whitespace
        sanitized = description.strip()
        
        # Remove HTML tags
        sanitized = re.sub(r'<[^>]+>', '', sanitized)
        
        # Remove excessive whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized)
        
        # Limit length
        if len(sanitized) > 5000:
            sanitized = sanitized[:4997] + '...'
        
        return sanitized
    
    def update_episode_metadata(
        self,
        episode: Episode,
        metadata: Dict[str, Any]
    ) -> Episode:
        """
        Update existing episode with new metadata
        """
        try:
            logger.info(f"Updating metadata for episode: {episode.id}")
            
            # Update fields that are safe to change
            if 'title' in metadata:
                episode.update_metadata(title=self._sanitize_title(metadata['title']))
            
            if 'description' in metadata:
                episode.update_metadata(description=self._sanitize_description(metadata['description']))
            
            if 'thumbnail_url' in metadata:
                episode.update_metadata(thumbnail_url=metadata['thumbnail_url'])
            
            if 'keywords' in metadata:
                keywords = self._process_keywords(metadata['keywords'])
                episode.update_metadata(keywords=keywords)
            
            if 'publication_date' in metadata:
                pub_date = self._parse_publication_date(metadata['publication_date'])
                episode.update_metadata(publication_date=pub_date)
            
            logger.info(f"Successfully updated metadata for episode: {episode.id}")
            return episode
            
        except Exception as e:
            logger.error(f"Failed to update episode metadata: {e}")
            raise MetadataProcessingError(f"Metadata update failed: {e}")
    
    def validate_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate metadata before processing
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Required fields
        required_fields = ['video_id', 'title']
        for field in required_fields:
            if field not in metadata or not metadata[field]:
                validation_result['errors'].append(f"Missing required field: {field}")
        
        # Validate video ID format (expects raw YouTube ID, will be prefixed)
        if metadata.get('video_id'):
            try:
                VideoId.from_youtube_id(metadata['video_id'])
            except ValueError as e:
                validation_result['errors'].append(f"Invalid video ID: {e}")
        
        # Validate duration if present
        if 'duration_seconds' in metadata:
            duration = self._parse_duration(metadata['duration_seconds'])
            if duration is None and metadata['duration_seconds'] is not None:
                validation_result['warnings'].append("Could not parse duration")
        
        # Check title length
        if metadata.get('title') and len(metadata['title']) > 500:
            validation_result['warnings'].append("Title will be truncated")
        
        # Check description length
        if metadata.get('description') and len(metadata['description']) > 5000:
            validation_result['warnings'].append("Description will be truncated")
        
        validation_result['valid'] = len(validation_result['errors']) == 0
        
        return validation_result