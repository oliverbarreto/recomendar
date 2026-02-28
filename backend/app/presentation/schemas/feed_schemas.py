"""
Feed API Response Schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class FeedValidationResponse(BaseModel):
    """Response schema for feed validation"""
    channel_id: int = Field(description="Channel ID")
    is_valid: bool = Field(description="Whether the feed is valid according to iTunes specifications")
    score: float = Field(description="Validation score from 0.0 to 100.0", ge=0.0, le=100.0)
    errors: List[str] = Field(description="List of validation errors that prevent iTunes acceptance")
    warnings: List[str] = Field(description="List of warnings that may affect feed quality")
    recommendations: List[str] = Field(description="List of recommendations to improve feed quality")
    validation_details: Dict[str, Any] = Field(description="Detailed validation information")
    validated_at: Optional[datetime] = Field(description="When the validation was performed")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "channel_id": 1,
                "is_valid": True,
                "score": 87.5,
                "errors": [],
                "warnings": [
                    "Episode 1: Description should be at least 100 characters for better SEO"
                ],
                "recommendations": [
                    "Consider adding iTunes keywords for better discoverability"
                ],
                "validation_details": {
                    "total_episodes": 5,
                    "channel_complete": True,
                    "itunes_complete": True,
                    "episodes_valid": True
                },
                "validated_at": "2024-01-15T10:30:00Z"
            }
        }


class FeedInfoResponse(BaseModel):
    """Response schema for feed information"""
    channel_id: int = Field(description="Channel ID")
    channel_name: str = Field(description="Channel name")
    feed_url: str = Field(description="RSS feed URL")
    episode_count: int = Field(description="Number of published episodes", ge=0)
    last_updated: Optional[datetime] = Field(description="When the feed was last updated")
    validation_score: Optional[float] = Field(description="iTunes validation score", ge=0.0, le=100.0)
    latest_episode_title: Optional[str] = Field(description="Title of the most recent episode")
    latest_episode_date: Optional[datetime] = Field(description="Publication date of the most recent episode")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "channel_id": 1,
                "channel_name": "My Tech Podcast",
                "feed_url": "http://localhost:8000/v1/feeds/1/feed.xml",
                "episode_count": 15,
                "last_updated": "2024-01-15T10:30:00Z",
                "validation_score": 92.5,
                "latest_episode_title": "Latest Episode About AI",
                "latest_episode_date": "2024-01-15T09:00:00Z"
            }
        }