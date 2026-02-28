"""
Tag domain entity
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
import re


@dataclass
class Tag:
    """
    Tag domain entity for categorizing episodes
    """
    id: Optional[int]
    channel_id: int
    name: str
    color: str = "#3B82F6"  # Default blue color
    usage_count: int = 0
    is_system_tag: bool = False
    last_used_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        # Validate channel_id
        if self.channel_id <= 0:
            raise ValueError("Valid channel_id is required")
        
        # Validate and normalize name
        if not self.name or len(self.name.strip()) < 1:
            raise ValueError("Tag name is required")
        
        self.name = self.name.strip()
        
        if len(self.name) > 50:
            raise ValueError("Tag name cannot exceed 50 characters")
        
        # Validate and normalize color
        if not self._is_valid_hex_color(self.color):
            self.color = "#3B82F6"  # Default to blue if invalid
        else:
            self.color = self.color.upper()  # Normalize to uppercase
        
        # Set timestamps
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def _is_valid_hex_color(self, color: str) -> bool:
        """
        Validate hex color format (#RRGGBB)
        """
        if not color:
            return False
        
        # Remove whitespace and ensure it starts with #
        color = color.strip()
        if not color.startswith('#'):
            color = f'#{color}'
        
        # Check if it matches hex color pattern
        pattern = r'^#[0-9A-Fa-f]{6}$'
        return bool(re.match(pattern, color))
    
    def update_name(self, new_name: str) -> None:
        """
        Update tag name with validation
        """
        if not new_name or len(new_name.strip()) < 1:
            raise ValueError("Tag name is required")
        
        new_name = new_name.strip()
        if len(new_name) > 50:
            raise ValueError("Tag name cannot exceed 50 characters")
        
        self.name = new_name
        self.updated_at = datetime.utcnow()
    
    def update_color(self, new_color: str) -> None:
        """
        Update tag color with validation
        """
        if not self._is_valid_hex_color(new_color):
            raise ValueError(f"Invalid hex color format: {new_color}")
        
        # Normalize color format
        new_color = new_color.strip()
        if not new_color.startswith('#'):
            new_color = f'#{new_color}'
        
        self.color = new_color.upper()
        self.updated_at = datetime.utcnow()
    
    def get_rgb_values(self) -> tuple[int, int, int]:
        """
        Get RGB values from hex color
        """
        hex_color = self.color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def get_contrasting_text_color(self) -> str:
        """
        Get contrasting text color (black or white) based on background color
        """
        r, g, b = self.get_rgb_values()
        
        # Calculate luminance using relative luminance formula
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        
        # Return white text for dark backgrounds, black for light backgrounds
        return "#FFFFFF" if luminance < 0.5 else "#000000"
    
    def is_similar_color(self, other_color: str, threshold: int = 50) -> bool:
        """
        Check if this tag's color is similar to another color
        """
        if not self._is_valid_hex_color(other_color):
            return False
        
        # Normalize other color
        other_color = other_color.strip().upper()
        if not other_color.startswith('#'):
            other_color = f'#{other_color}'
        
        # Get RGB values for both colors
        r1, g1, b1 = self.get_rgb_values()
        
        other_hex = other_color.lstrip('#')
        r2, g2, b2 = tuple(int(other_hex[i:i+2], 16) for i in (0, 2, 4))
        
        # Calculate Euclidean distance in RGB space
        distance = ((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2) ** 0.5
        
        return distance < threshold
    
    @classmethod
    def create_tag(cls, channel_id: int, name: str, color: Optional[str] = None) -> 'Tag':
        """
        Factory method to create a new tag
        """
        return cls(
            id=None,
            channel_id=channel_id,
            name=name,
            color=color or "#3B82F6"
        )
    
    @classmethod
    def get_default_colors(cls) -> List[str]:
        """
        Get list of predefined tag colors
        """
        return [
            "#3B82F6",  # Blue
            "#EF4444",  # Red
            "#10B981",  # Green
            "#F59E0B",  # Yellow
            "#8B5CF6",  # Purple
            "#06B6D4",  # Cyan
            "#F97316",  # Orange
            "#EC4899",  # Pink
            "#6B7280",  # Gray
            "#84CC16",  # Lime
        ]