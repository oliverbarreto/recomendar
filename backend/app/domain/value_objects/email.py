"""
Email value object for domain validation
"""
from dataclasses import dataclass
import re
from typing import Optional


@dataclass
class Email:
    """
    Email value object that validates email format
    """
    value: str
    
    def __post_init__(self):
        if not self._is_valid_email(self.value):
            raise ValueError(f"Invalid email format: {self.value}")
    
    def _is_valid_email(self, email: str) -> bool:
        """
        Validate email format using regex
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def __str__(self) -> str:
        return self.value
    
    def __eq__(self, other) -> bool:
        if isinstance(other, Email):
            return self.value.lower() == other.value.lower()
        return False
    
    def __hash__(self) -> int:
        return hash(self.value.lower())
    
    @classmethod
    def create_optional(cls, email: Optional[str]) -> Optional['Email']:
        """
        Create optional Email from string, returns None if email is None or empty
        """
        if email is None or email.strip() == "":
            return None
        return cls(email.strip())