"""
Channel repository interface
"""
from abc import abstractmethod
from typing import Optional, List
from app.domain.repositories.base import BaseRepository
from app.domain.entities.channel import Channel

class ChannelRepository(BaseRepository[Channel]):
    """
    Repository interface for Channel entities.
    Extends BaseRepository with channel-specific operations.
    """
    
    @abstractmethod
    async def find_by_user_id(self, user_id: int) -> Optional[Channel]:
        """
        Find a channel by user ID (one channel per user)
        
        Args:
            user_id: The user ID to search for
            
        Returns:
            The channel if found, None otherwise
            
        Raises:
            RepositoryError: If search fails
        """
        pass
    
    @abstractmethod
    async def update_feed_url(self, channel_id: int, feed_url: str) -> bool:
        """
        Update the RSS feed URL for a channel
        
        Args:
            channel_id: The channel ID
            feed_url: The new feed URL
            
        Returns:
            True if URL was updated, False if channel not found
            
        Raises:
            RepositoryError: If update fails
        """
        pass
    
    @abstractmethod
    async def find_by_name(self, name: str) -> List[Channel]:
        """
        Find channels by name (partial match, case-insensitive)
        
        Args:
            name: The name or partial name to search for
            
        Returns:
            List of matching channels (may be empty)
            
        Raises:
            RepositoryError: If search fails
        """
        pass
    
    @abstractmethod
    async def get_channels_by_category(self, category: str) -> List[Channel]:
        """
        Get all channels in a specific category
        
        Args:
            category: The category to filter by
            
        Returns:
            List of channels in the category (may be empty)
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def get_channels_by_language(self, language: str) -> List[Channel]:
        """
        Get all channels in a specific language
        
        Args:
            language: The language code to filter by (e.g., 'en', 'es')
            
        Returns:
            List of channels in the language (may be empty)
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def update_metadata(self, channel_id: int, **kwargs) -> bool:
        """
        Update channel metadata fields
        
        Args:
            channel_id: The channel ID
            **kwargs: Fields to update (description, website_url, image_url, etc.)
            
        Returns:
            True if metadata was updated, False if channel not found
            
        Raises:
            RepositoryError: If update fails
        """
        pass
    
    @abstractmethod
    async def channel_name_exists(self, name: str, exclude_channel_id: Optional[int] = None) -> bool:
        """
        Check if a channel name already exists
        
        Args:
            name: The channel name to check
            exclude_channel_id: Optional channel ID to exclude from check (for updates)
            
        Returns:
            True if name exists, False otherwise
            
        Raises:
            RepositoryError: If check fails
        """
        pass