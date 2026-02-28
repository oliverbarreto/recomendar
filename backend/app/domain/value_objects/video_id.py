"""
VideoId value object for universal episode ID validation
Supports YouTube episodes (yt_ prefix) and uploaded episodes (up_ prefix)
"""
from dataclasses import dataclass
import re
import secrets
import string


@dataclass
class VideoId:
    """
    Universal Episode ID value object that validates ID format

    Supports two formats:
    - YouTube episodes: yt_dQw4w9WgXcQ (yt_ + 11-char YouTube ID)
    - Uploaded episodes: up_abc123xyz789 (up_ + 11-char generated ID)

    Total length: 14 characters (3-char prefix + 11-char ID)
    """
    value: str

    def __post_init__(self):
        if not self._is_valid_episode_id(self.value):
            raise ValueError(f"Invalid episode ID: {self.value}. Must be yt_<11chars> or up_<11chars>")

    def _is_valid_episode_id(self, episode_id: str) -> bool:
        """
        Validate episode ID format

        Accepts:
        - yt_[a-zA-Z0-9_-]{11} for YouTube episodes
        - up_[a-zA-Z0-9_-]{11} for uploaded episodes
        """
        if not isinstance(episode_id, str):
            return False

        # Check total length (3 prefix + 11 chars)
        if len(episode_id) != 14:
            return False

        # Check prefix and ID format
        youtube_pattern = r'^yt_[a-zA-Z0-9_-]{11}$'
        upload_pattern = r'^up_[a-zA-Z0-9]{11}$'

        return bool(re.match(youtube_pattern, episode_id) or re.match(upload_pattern, episode_id))
    
    def __str__(self) -> str:
        return self.value

    def __eq__(self, other) -> bool:
        if isinstance(other, VideoId):
            return self.value == other.value
        return False

    def __hash__(self) -> int:
        return hash(self.value)

    def is_youtube_episode(self) -> bool:
        """Check if this is a YouTube episode (yt_ prefix)"""
        return self.value.startswith('yt_')

    def is_uploaded_episode(self) -> bool:
        """Check if this is an uploaded episode (up_ prefix)"""
        return self.value.startswith('up_')

    def get_raw_id(self) -> str:
        """
        Get the raw ID without prefix

        Returns:
            11-character ID without yt_ or up_ prefix
        """
        if len(self.value) >= 3:
            return self.value[3:]  # Strip first 3 characters (prefix)
        return self.value

    def get_prefix(self) -> str:
        """
        Get the prefix (yt_ or up_)

        Returns:
            3-character prefix
        """
        if len(self.value) >= 3:
            return self.value[:3]
        return ""

    @property
    def youtube_url(self) -> str:
        """
        Generate YouTube URL from video ID (only for YouTube episodes)

        Raises:
            ValueError: If called on non-YouTube episode
        """
        if not self.is_youtube_episode():
            raise ValueError(f"Cannot generate YouTube URL for non-YouTube episode: {self.value}")
        return f"https://www.youtube.com/watch?v={self.get_raw_id()}"

    @classmethod
    def from_url(cls, url: str) -> 'VideoId':
        """
        Extract video ID from YouTube URL and return with yt_ prefix

        Args:
            url: YouTube video URL

        Returns:
            VideoId with yt_ prefix

        Raises:
            ValueError: If URL format is invalid
        """
        patterns = [
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
            r'(?:https?://)?youtu\.be/([a-zA-Z0-9_-]{11})',
            r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                youtube_id = match.group(1)
                return cls.from_youtube_id(youtube_id)

        raise ValueError(f"Could not extract video ID from URL: {url}")

    @classmethod
    def from_youtube_id(cls, youtube_id: str) -> 'VideoId':
        """
        Create VideoId from raw YouTube video ID (adds yt_ prefix)

        Args:
            youtube_id: 11-character YouTube video ID

        Returns:
            VideoId with yt_ prefix

        Raises:
            ValueError: If YouTube ID format is invalid
        """
        # Validate raw YouTube ID format
        if not re.match(r'^[a-zA-Z0-9_-]{11}$', youtube_id):
            raise ValueError(f"Invalid YouTube video ID format: {youtube_id}")

        return cls(f"yt_{youtube_id}")

    @classmethod
    def from_upload_hash(cls, hash_value: str) -> 'VideoId':
        """
        Create VideoId from upload hash (adds up_ prefix)

        Args:
            hash_value: 11-character alphanumeric hash

        Returns:
            VideoId with up_ prefix

        Raises:
            ValueError: If hash format is invalid
        """
        # Validate hash format (11 alphanumeric characters)
        if not re.match(r'^[a-zA-Z0-9]{11}$', hash_value):
            raise ValueError(f"Invalid upload hash format: {hash_value}. Must be 11 alphanumeric characters")

        return cls(f"up_{hash_value}")

    @classmethod
    def generate_upload_id(cls) -> 'VideoId':
        """
        Generate a new unique upload ID

        Uses cryptographically secure random generation to create an 11-character
        alphanumeric ID for uploaded episodes.

        Returns:
            VideoId with up_ prefix and randomly generated 11-char ID

        Example:
            VideoId.generate_upload_id() -> VideoId("up_7k2m9x4p8qz")
        """
        # Use uppercase and lowercase letters + digits (62 possible characters)
        alphabet = string.ascii_letters + string.digits

        # Generate 11 random characters
        random_id = ''.join(secrets.choice(alphabet) for _ in range(11))

        return cls(f"up_{random_id}")