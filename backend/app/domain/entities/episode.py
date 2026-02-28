"""
Episode domain entity
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from enum import Enum
from app.domain.value_objects.video_id import VideoId
from app.domain.value_objects.duration import Duration

if TYPE_CHECKING:
    from app.domain.entities.tag import Tag


class EpisodeStatus(Enum):
    """Episode processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Episode:
    """
    Episode domain entity representing a podcast episode
    """
    id: Optional[int]
    channel_id: int
    video_id: VideoId  # Required for all episodes (yt_* for YouTube, up_* for uploads)
    title: str
    description: str
    publication_date: datetime
    audio_file_path: Optional[str] = None
    video_url: str = ""
    thumbnail_url: str = ""
    duration: Optional[Duration] = None
    keywords: List[str] = field(default_factory=list)
    tags: List['Tag'] = field(default_factory=list)
    status: EpisodeStatus = EpisodeStatus.PENDING
    retry_count: int = 0
    download_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # YouTube channel information
    youtube_channel: Optional[str] = None  # Full channel name
    youtube_channel_id: Optional[str] = None  # YouTube channel ID
    youtube_channel_url: Optional[str] = None  # Channel URL

    # User preferences
    is_favorited: bool = False

    # Media file information
    media_file_size: Optional[int] = 0

    # Upload source tracking
    source_type: str = "youtube"  # "youtube" or "upload"
    original_filename: Optional[str] = None  # Original filename for uploaded files

    # Audio language and quality preferences
    audio_language: Optional[str] = None  # Actual downloaded language (ISO 639-1)
    audio_quality: Optional[str] = None  # Actual downloaded quality tier
    requested_language: Optional[str] = None  # What user originally requested
    requested_quality: Optional[str] = None  # What user originally requested
    
    def __post_init__(self):
        # Validate required fields
        if self.channel_id <= 0:
            raise ValueError("Valid channel_id is required")

        if not self.title or len(self.title.strip()) < 1:
            raise ValueError("Episode title is required")
        self.title = self.title.strip()

        if not self.description:
            self.description = ""

        # Generate video URL if not provided (only for YouTube episodes)
        if not self.video_url and self.video_id.is_youtube_episode():
            self.video_url = self.video_id.youtube_url

        # Ensure keywords is a list
        if self.keywords is None:
            self.keywords = []

        # Set timestamps
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def update_status(self, new_status: EpisodeStatus, message: Optional[str] = None) -> None:
        """
        Update episode status with validation
        """
        # Validate status transitions
        if not self._is_valid_status_transition(self.status, new_status):
            raise ValueError(f"Invalid status transition from {self.status.value} to {new_status.value}")
        
        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.utcnow()
        
        # Set download date when completed
        if new_status == EpisodeStatus.COMPLETED and old_status != EpisodeStatus.COMPLETED:
            self.download_date = datetime.utcnow()
        
        # Reset retry count on success
        if new_status == EpisodeStatus.COMPLETED:
            self.retry_count = 0
    
    def _is_valid_status_transition(self, from_status: EpisodeStatus, to_status: EpisodeStatus) -> bool:
        """
        Validate if status transition is allowed
        """
        valid_transitions = {
            EpisodeStatus.PENDING: [EpisodeStatus.PROCESSING, EpisodeStatus.FAILED],
            EpisodeStatus.PROCESSING: [EpisodeStatus.COMPLETED, EpisodeStatus.FAILED, EpisodeStatus.PENDING],
            EpisodeStatus.COMPLETED: [EpisodeStatus.PROCESSING],  # Allow reprocessing
            EpisodeStatus.FAILED: [EpisodeStatus.PENDING, EpisodeStatus.PROCESSING]
        }
        
        return to_status in valid_transitions.get(from_status, [])
    
    def increment_retry_count(self) -> None:
        """
        Increment retry count for failed episodes
        """
        if self.status not in [EpisodeStatus.FAILED, EpisodeStatus.PENDING]:
            raise ValueError("Can only increment retry count for failed or pending episodes")
        
        self.retry_count += 1
        self.updated_at = datetime.utcnow()
    
    def reset_for_retry(self) -> None:
        """
        Reset episode for retry attempt
        """
        if self.status != EpisodeStatus.FAILED:
            raise ValueError("Can only reset failed episodes for retry")
        
        self.status = EpisodeStatus.PENDING
        self.audio_file_path = None
        self.download_date = None
        self.updated_at = datetime.utcnow()
    
    def mark_as_completed(self, audio_file_path: str, duration_seconds: Optional[int] = None) -> None:
        """
        Mark episode as completed with audio file information
        """
        if not audio_file_path:
            raise ValueError("Audio file path is required to mark episode as completed")

        self.audio_file_path = audio_file_path
        self.status = EpisodeStatus.COMPLETED
        self.download_date = datetime.utcnow()
        self.retry_count = 0
        self.updated_at = datetime.utcnow()

        # Calculate and store media file size
        from app.infrastructure.services.media_file_service import MediaFileService
        media_service = MediaFileService()
        self.media_file_size = media_service.calculate_file_size(audio_file_path)

        if duration_seconds is not None and duration_seconds > 0:
            self.duration = Duration(duration_seconds)
    
    def update_metadata(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        publication_date: Optional[datetime] = None
    ) -> None:
        """
        Update episode metadata
        """
        if title is not None:
            if not title or len(title.strip()) < 1:
                raise ValueError("Episode title is required")
            self.title = title.strip()
        
        if description is not None:
            self.description = description
        
        if thumbnail_url is not None:
            self.thumbnail_url = thumbnail_url
        
        if keywords is not None:
            self.keywords = keywords
        
        if publication_date is not None:
            self.publication_date = publication_date
        
        self.updated_at = datetime.utcnow()

    def update_youtube_channel_info(
        self,
        channel: Optional[str] = None,
        channel_id: Optional[str] = None,
        channel_url: Optional[str] = None
    ) -> None:
        """
        Update YouTube channel information
        """
        if channel is not None:
            self.youtube_channel = channel.strip() if channel else None

        if channel_id is not None:
            self.youtube_channel_id = channel_id.strip() if channel_id else None

        if channel_url is not None:
            self.youtube_channel_url = channel_url.strip() if channel_url else None

        self.updated_at = datetime.utcnow()

    def toggle_favorite(self) -> bool:
        """
        Toggle favorite status

        Returns:
            New favorite status
        """
        self.is_favorited = not self.is_favorited
        self.updated_at = datetime.utcnow()
        return self.is_favorited

    def set_favorite(self, is_favorited: bool) -> None:
        """
        Set favorite status

        Args:
            is_favorited: New favorite status
        """
        self.is_favorited = is_favorited
        self.updated_at = datetime.utcnow()

    def can_retry(self, max_retries: int = 3) -> bool:
        """
        Check if episode can be retried
        """
        return self.status == EpisodeStatus.FAILED and self.retry_count < max_retries
    
    def is_processing_stuck(self, max_processing_hours: int = 2) -> bool:
        """
        Check if episode has been processing for too long
        """
        if self.status != EpisodeStatus.PROCESSING:
            return False
        
        hours_since_update = (datetime.utcnow() - self.updated_at).total_seconds() / 3600
        return hours_since_update > max_processing_hours

    def get_episode_number(self, episodes_list: List['Episode']) -> int:
        """Calculate episode number based on position in created_at order"""
        sorted_episodes = sorted(episodes_list, key=lambda x: x.created_at or datetime.min)
        try:
            return sorted_episodes.index(self) + 1
        except ValueError:
            # If episode not found in list, return a default
            return len(episodes_list) + 1

    def generate_subtitle(self) -> str:
        """Generate episode subtitle from YouTube channel info"""
        return f"by {self.youtube_channel}" if self.youtube_channel else ""

    def format_description_for_rss(self) -> str:
        """Format description preserving line breaks and basic formatting"""
        if not self.description:
            return ""

        # Preserve line breaks by converting to HTML breaks
        formatted = self.description.replace('\n\n', '<br/><br/>')
        formatted = formatted.replace('\n', '<br/>')

        # Keep basic markdown-like formatting
        return formatted
    
    @classmethod
    def create_episode(
        cls,
        channel_id: int,
        video_url: str,
        title: str,
        description: str = "",
        publication_date: Optional[datetime] = None,
        keywords: Optional[List[str]] = None,
        youtube_channel: Optional[str] = None,
        youtube_channel_id: Optional[str] = None,
        youtube_channel_url: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        requested_language: Optional[str] = None,
        requested_quality: Optional[str] = None
    ) -> 'Episode':
        """
        Factory method to create a new episode from YouTube URL
        """
        video_id = VideoId.from_url(video_url)

        return cls(
            id=None,
            channel_id=channel_id,
            video_id=video_id,
            title=title,
            description=description,
            publication_date=publication_date or datetime.utcnow(),
            video_url=video_url,
            thumbnail_url=thumbnail_url or "",
            keywords=keywords or [],
            youtube_channel=youtube_channel,
            youtube_channel_id=youtube_channel_id,
            youtube_channel_url=youtube_channel_url,
            requested_language=requested_language,
            requested_quality=requested_quality
        )

    def set_audio_preferences(
        self,
        requested_language: Optional[str] = None,
        requested_quality: Optional[str] = None,
        actual_language: Optional[str] = None,
        actual_quality: Optional[str] = None
    ) -> None:
        """Set audio language and quality preferences"""
        self.requested_language = requested_language
        self.requested_quality = requested_quality
        self.audio_language = actual_language
        self.audio_quality = actual_quality
        self.updated_at = datetime.utcnow()

    def reset_for_redownload(self) -> None:
        """
        Reset episode for re-download with improved MP3 conversion

        This method:
        - Sets status back to pending
        - Clears audio file path
        - Resets retry count
        - Updates timestamps
        """
        self.status = EpisodeStatus.PENDING
        self.audio_file_path = None
        self.retry_count = 0
        self.download_date = None
        self.media_file_size = 0
        self.updated_at = datetime.utcnow()