"""
Channel Repository Interface
Domain layer interface for channel data access
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.channel import Channel


class ChannelRepositoryInterface(ABC):
    """
    Abstract repository interface for Channel entities
    """
    
    @abstractmethod
    async def create(self, channel: Channel) -> Channel:
        """
        Create a new channel
        
        Args:
            channel: Channel entity to create
            
        Returns:
            Created channel entity with assigned ID
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, channel_id: int) -> Optional[Channel]:
        """
        Get channel by ID
        
        Args:
            channel_id: Channel ID
            
        Returns:
            Channel entity or None if not found
        """
        pass
    
    @abstractmethod
    async def get_by_user_id(self, user_id: int) -> List[Channel]:
        """
        Get all channels for a user
        
        Args:
            user_id: User ID
            
        Returns:
            List of channel entities
        """
        pass
    
    @abstractmethod
    async def update(self, channel: Channel) -> Optional[Channel]:
        """
        Update an existing channel
        
        Args:
            channel: Channel entity with updated data
            
        Returns:
            Updated channel entity or None if not found
        """
        pass
    
    @abstractmethod
    async def delete(self, channel_id: int) -> bool:
        """
        Delete a channel
        
        Args:
            channel_id: Channel ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def get_all(self) -> List[Channel]:
        """
        Get all channels
        
        Returns:
            List of all channel entities
        """
        pass
    
    @abstractmethod
    async def search_by_name(self, name: str, limit: int = 10) -> List[Channel]:
        """
        Search channels by name
        
        Args:
            name: Search term
            limit: Maximum number of results
            
        Returns:
            List of matching channel entities
        """
        pass