"""
Base repository interface for all domain entities
"""
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional

T = TypeVar('T')

class BaseRepository(Generic[T], ABC):
    """
    Generic base repository interface providing common CRUD operations.
    All specific repository interfaces should extend this base class.
    """
    
    @abstractmethod
    async def create(self, entity: T) -> T:
        """
        Create a new entity in the repository
        
        Args:
            entity: The entity to create
            
        Returns:
            The created entity with populated ID and timestamps
            
        Raises:
            RepositoryError: If creation fails
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, entity_id: int) -> Optional[T]:
        """
        Retrieve an entity by its ID
        
        Args:
            entity_id: The unique identifier of the entity
            
        Returns:
            The entity if found, None otherwise
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """
        Retrieve all entities with pagination support
        
        Args:
            skip: Number of entities to skip (for pagination)
            limit: Maximum number of entities to return
            
        Returns:
            List of entities (may be empty)
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def update(self, entity: T) -> T:
        """
        Update an existing entity in the repository
        
        Args:
            entity: The entity to update (must have valid ID)
            
        Returns:
            The updated entity
            
        Raises:
            RepositoryError: If update fails or entity not found
        """
        pass
    
    @abstractmethod
    async def delete(self, entity_id: int) -> bool:
        """
        Delete an entity by its ID
        
        Args:
            entity_id: The unique identifier of the entity to delete
            
        Returns:
            True if entity was deleted, False if entity not found
            
        Raises:
            RepositoryError: If deletion fails
        """
        pass
    
    @abstractmethod
    async def exists(self, entity_id: int) -> bool:
        """
        Check if an entity exists by its ID
        
        Args:
            entity_id: The unique identifier to check
            
        Returns:
            True if entity exists, False otherwise
            
        Raises:
            RepositoryError: If check fails
        """
        pass