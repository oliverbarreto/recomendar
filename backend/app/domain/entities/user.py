"""
User domain entity
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import hashlib
import secrets


@dataclass
class User:
    """
    User domain entity representing a system user
    """
    id: Optional[int]
    name: str
    email: str
    password_hash: str
    is_admin: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        # Validate name
        if not self.name or len(self.name.strip()) < 2:
            raise ValueError("User name must be at least 2 characters long")
        self.name = self.name.strip()
        
        # Validate email format
        if not self._is_valid_email(self.email):
            raise ValueError(f"Invalid email format: {self.email}")
        self.email = self.email.lower().strip()
        
        # Set timestamps
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def _is_valid_email(self, email: str) -> bool:
        """
        Validate email format using simple regex
        """
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def verify_password(self, password: str) -> bool:
        """
        Verify password against stored hash
        """
        return self._hash_password(password) == self.password_hash
    
    def update_password(self, new_password: str) -> None:
        """
        Update user password with new hash
        """
        if len(new_password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        self.password_hash = self._hash_password(new_password)
        self.updated_at = datetime.utcnow()
    
    def update_profile(self, name: Optional[str] = None, email: Optional[str] = None) -> None:
        """
        Update user profile information
        """
        if name is not None:
            if not name or len(name.strip()) < 2:
                raise ValueError("User name must be at least 2 characters long")
            self.name = name.strip()
        
        if email is not None:
            if not self._is_valid_email(email):
                raise ValueError(f"Invalid email format: {email}")
            self.email = email.lower().strip()
        
        self.updated_at = datetime.utcnow()
    
    @staticmethod
    def _hash_password(password: str) -> str:
        """
        Hash password using SHA-256 with salt
        Note: In production, use bcrypt or argon2
        """
        # Simple implementation for demo - use proper password hashing in production
        salt = "labcastarr_salt"  # In production, use random salt per user
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    @classmethod
    def create_user(cls, name: str, email: str, password: str, is_admin: bool = False) -> 'User':
        """
        Factory method to create a new user with validation
        """
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        password_hash = cls._hash_password(password)
        
        return cls(
            id=None,
            name=name,
            email=email,
            password_hash=password_hash,
            is_admin=is_admin
        )