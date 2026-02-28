"""
Tag repository interface
"""
from abc import abstractmethod
from typing import List, Optional
from app.domain.repositories.base import BaseRepository
from app.domain.entities.tag import Tag

class TagRepository(BaseRepository[Tag]):
    """
    Repository interface for Tag entities.
    Extends BaseRepository with tag-specific operations and episode associations.
    """
    
    @abstractmethod
    async def find_by_channel(self, channel_id: int) -> List[Tag]:
        """
        Find all tags for a specific channel
        
        Args:
            channel_id: The channel ID to search for
            
        Returns:
            List of tags for the channel (may be empty)
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def find_by_name(self, channel_id: int, name: str) -> Optional[Tag]:
        """
        Find a tag by name within a specific channel
        
        Args:
            channel_id: The channel ID to search within
            name: The tag name to search for
            
        Returns:
            The tag if found, None otherwise
            
        Raises:
            RepositoryError: If search fails
        """
        pass
    
    @abstractmethod
    async def get_episode_tags(self, episode_id: int) -> List[Tag]:
        """
        Get all tags associated with an episode
        
        Args:
            episode_id: The episode ID
            
        Returns:
            List of tags for the episode (may be empty)
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def add_episode_tag(self, episode_id: int, tag_id: int) -> bool:
        """
        Associate a tag with an episode
        
        Args:
            episode_id: The episode ID
            tag_id: The tag ID
            
        Returns:
            True if association was created, False if it already exists
            
        Raises:
            RepositoryError: If association fails
        """
        pass
    
    @abstractmethod
    async def remove_episode_tag(self, episode_id: int, tag_id: int) -> bool:
        """
        Remove tag association from an episode
        
        Args:
            episode_id: The episode ID
            tag_id: The tag ID
            
        Returns:
            True if association was removed, False if it didn't exist
            
        Raises:
            RepositoryError: If removal fails
        """
        pass
    
    @abstractmethod
    async def get_episodes_by_tag(self, tag_id: int, skip: int = 0, limit: int = 50) -> List[int]:
        """
        Get episode IDs that are associated with a specific tag
        
        Args:
            tag_id: The tag ID
            skip: Number of episodes to skip (for pagination)
            limit: Maximum number of episode IDs to return
            
        Returns:
            List of episode IDs (may be empty)
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def bulk_add_episode_tags(self, episode_id: int, tag_ids: List[int]) -> int:
        """
        Associate multiple tags with an episode
        
        Args:
            episode_id: The episode ID
            tag_ids: List of tag IDs to associate
            
        Returns:
            Number of new associations created
            
        Raises:
            RepositoryError: If bulk operation fails
        """
        pass
    
    @abstractmethod
    async def bulk_remove_episode_tags(self, episode_id: int, tag_ids: List[int]) -> int:
        """
        Remove multiple tag associations from an episode
        
        Args:
            episode_id: The episode ID
            tag_ids: List of tag IDs to remove
            
        Returns:
            Number of associations removed
            
        Raises:
            RepositoryError: If bulk operation fails
        """
        pass
    
    @abstractmethod
    async def tag_name_exists(self, channel_id: int, name: str, exclude_tag_id: Optional[int] = None) -> bool:
        """
        Check if a tag name already exists within a channel
        
        Args:
            channel_id: The channel ID to check within
            name: The tag name to check
            exclude_tag_id: Optional tag ID to exclude from check (for updates)
            
        Returns:
            True if name exists, False otherwise
            
        Raises:
            RepositoryError: If check fails
        """
        pass
    
    @abstractmethod
    async def get_popular_tags(self, channel_id: int, limit: int = 10) -> List[tuple[Tag, int]]:
        """
        Get most popular tags for a channel based on episode count
        
        Args:
            channel_id: The channel ID
            limit: Maximum number of tags to return
            
        Returns:
            List of (tag, episode_count) tuples sorted by usage
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass