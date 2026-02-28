"""
Duration value object for episode duration handling
"""
from dataclasses import dataclass


@dataclass
class Duration:
    """
    Duration value object that handles time duration in seconds
    """
    seconds: int
    
    def __post_init__(self):
        if self.seconds < 0:
            raise ValueError("Duration cannot be negative")
    
    @property
    def minutes(self) -> int:
        """
        Get duration in minutes
        """
        return self.seconds // 60
    
    @property
    def hours(self) -> int:
        """
        Get duration in hours
        """
        return self.seconds // 3600
    
    @property
    def formatted(self) -> str:
        """
        Format duration as HH:MM:SS or MM:SS
        """
        hours, remainder = divmod(self.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"
    
    @property
    def human_readable(self) -> str:
        """
        Format duration in human-readable format
        """
        if self.seconds < 60:
            return f"{self.seconds} second{'s' if self.seconds != 1 else ''}"
        elif self.seconds < 3600:
            minutes = self.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        else:
            hours = self.seconds // 3600
            remaining_minutes = (self.seconds % 3600) // 60
            if remaining_minutes == 0:
                return f"{hours} hour{'s' if hours != 1 else ''}"
            return f"{hours} hour{'s' if hours != 1 else ''} {remaining_minutes} minute{'s' if remaining_minutes != 1 else ''}"
    
    def __str__(self) -> str:
        return self.formatted
    
    def __eq__(self, other) -> bool:
        if isinstance(other, Duration):
            return self.seconds == other.seconds
        return False
    
    def __hash__(self) -> int:
        return hash(self.seconds)
    
    def __lt__(self, other) -> bool:
        if isinstance(other, Duration):
            return self.seconds < other.seconds
        return NotImplemented
    
    def __le__(self, other) -> bool:
        if isinstance(other, Duration):
            return self.seconds <= other.seconds
        return NotImplemented
    
    def __gt__(self, other) -> bool:
        if isinstance(other, Duration):
            return self.seconds > other.seconds
        return NotImplemented
    
    def __ge__(self, other) -> bool:
        if isinstance(other, Duration):
            return self.seconds >= other.seconds
        return NotImplemented
    
    @classmethod
    def from_minutes(cls, minutes: int) -> 'Duration':
        """
        Create Duration from minutes
        """
        return cls(minutes * 60)
    
    @classmethod
    def from_hours(cls, hours: int) -> 'Duration':
        """
        Create Duration from hours
        """
        return cls(hours * 3600)
    
    @classmethod
    def from_formatted(cls, formatted: str) -> 'Duration':
        """
        Create Duration from formatted string (HH:MM:SS or MM:SS)
        """
        parts = formatted.split(':')
        if len(parts) == 2:  # MM:SS
            minutes, seconds = map(int, parts)
            return cls(minutes * 60 + seconds)
        elif len(parts) == 3:  # HH:MM:SS
            hours, minutes, seconds = map(int, parts)
            return cls(hours * 3600 + minutes * 60 + seconds)
        else:
            raise ValueError(f"Invalid duration format: {formatted}. Expected MM:SS or HH:MM:SS")