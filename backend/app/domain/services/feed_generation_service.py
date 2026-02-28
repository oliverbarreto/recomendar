"""
RSS Feed Generation Service Domain Layer
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from app.domain.entities.channel import Channel
from app.domain.entities.episode import Episode


class FeedGenerationServiceInterface(ABC):
    """
    Interface for RSS feed generation service
    """
    
    @abstractmethod
    def generate_rss_feed(
        self, 
        channel: Channel, 
        episodes: List[Episode],
        base_url: str
    ) -> str:
        """
        Generate RSS feed XML for a channel and its episodes
        
        Args:
            channel: Channel entity with RSS feed settings
            episodes: List of episode entities to include in feed
            base_url: Base URL for media files and feed links
            
        Returns:
            RSS feed XML string
        """
        pass
    
    @abstractmethod
    def validate_feed(self, feed_xml: str) -> tuple[bool, List[str]]:
        """
        Validate RSS feed against iTunes specifications
        
        Args:
            feed_xml: RSS feed XML string
            
        Returns:
            Tuple of (is_valid, validation_errors)
        """
        pass
    
    @abstractmethod
    def calculate_feed_score(self, channel: Channel, episodes: List[Episode]) -> float:
        """
        Calculate feed quality score based on iTunes compliance
        
        Args:
            channel: Channel entity
            episodes: List of episode entities
            
        Returns:
            Feed quality score (0.0 to 100.0)
        """
        pass