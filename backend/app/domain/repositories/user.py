"""
User repository interface
"""
from abc import abstractmethod
from typing import Optional
from app.domain.repositories.base import BaseRepository
from app.domain.entities.user import User

class UserRepository(BaseRepository[User]):
    """
    Repository interface for User entities.
    Extends BaseRepository with user-specific operations.
    """
    
    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[User]:
        """
        Find a user by their email address
        
        Args:
            email: The email address to search for
            
        Returns:
            The user if found, None otherwise
            
        Raises:
            RepositoryError: If search fails
        """
        pass
    
    @abstractmethod
    async def email_exists(self, email: str) -> bool:
        """
        Check if an email address is already registered
        
        Args:
            email: The email address to check
            
        Returns:
            True if email exists, False otherwise
            
        Raises:
            RepositoryError: If check fails
        """
        pass
    
    @abstractmethod
    async def get_admin_users(self) -> list[User]:
        """
        Get all users with admin privileges
        
        Returns:
            List of admin users (may be empty)
            
        Raises:
            RepositoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def update_password(self, user_id: int, password_hash: str) -> bool:
        """
        Update a user's password hash
        
        Args:
            user_id: The user ID
            password_hash: The new hashed password
            
        Returns:
            True if password was updated, False if user not found
            
        Raises:
            RepositoryError: If update fails
        """
        pass
    
    @abstractmethod
    async def promote_to_admin(self, user_id: int) -> bool:
        """
        Promote a user to admin privileges
        
        Args:
            user_id: The user ID to promote
            
        Returns:
            True if user was promoted, False if user not found
            
        Raises:
            RepositoryError: If promotion fails
        """
        pass
    
    @abstractmethod
    async def revoke_admin(self, user_id: int) -> bool:
        """
        Revoke admin privileges from a user
        
        Args:
            user_id: The user ID to demote
            
        Returns:
            True if admin privileges were revoked, False if user not found
            
        Raises:
            RepositoryError: If demotion fails
        """
        pass