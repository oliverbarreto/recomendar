"""
Pydantic schemas for search API endpoints
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


class SearchHighlight(BaseModel):
    """Highlighted text snippet from search results"""
    title: Optional[List[str]] = Field(default=[], description="Highlighted title snippets")
    description: Optional[List[str]] = Field(default=[], description="Highlighted description snippets")


class SearchResultEpisode(BaseModel):
    """Episode data in search results"""
    id: int
    title: str
    description: Optional[str] = None
    duration: Optional[int] = None
    status: str
    publication_date: Optional[datetime] = None
    thumbnail_url: Optional[str] = None
    youtube_url: Optional[str] = None
    episode_number: Optional[int] = None
    season_number: Optional[int] = None
    tags: List[Dict[str, Any]] = Field(default=[], description="Associated tags")


class SearchResult(BaseModel):
    """Individual search result with relevance and highlighting"""
    episode: SearchResultEpisode
    relevance_score: float = Field(ge=0.0, le=1.0, description="Relevance score (0-1)")
    highlights: SearchHighlight = Field(default_factory=SearchHighlight)


class SearchMeta(BaseModel):
    """Search metadata and execution information"""
    query: Optional[str] = None
    execution_time: float = Field(ge=0.0, description="Query execution time in seconds")
    filters_applied: Dict[str, Any] = Field(default_factory=dict, description="Applied filters")


class SearchResponse(BaseModel):
    """Complete search response with results and pagination"""
    results: List[SearchResult] = Field(default=[], description="Search results")
    total_count: int = Field(ge=0, description="Total number of matching episodes")
    page: int = Field(ge=1, description="Current page number")
    per_page: int = Field(ge=1, le=50, description="Results per page")
    has_more: bool = Field(description="Whether more results are available")
    search_meta: SearchMeta


class TagOption(BaseModel):
    """Tag option for filtering"""
    id: int
    name: str
    color: str = Field(pattern=r'^#[0-9A-Fa-f]{6}$', description="Hex color code")
    episode_count: int = Field(ge=0, description="Number of episodes with this tag")


class DurationRange(BaseModel):
    """Duration range for filtering"""
    min: int = Field(ge=0, description="Minimum duration in seconds")
    max: int = Field(ge=0, description="Maximum duration in seconds")


class DateRange(BaseModel):
    """Date range for filtering"""
    earliest: Optional[datetime] = Field(description="Earliest episode publication date")
    latest: Optional[datetime] = Field(description="Latest episode publication date")


class FilterOptionsResponse(BaseModel):
    """Available filter options for search interface"""
    available_tags: List[TagOption] = Field(default=[], description="Available tags for filtering")
    status_options: List[str] = Field(default=[], description="Available episode statuses")
    duration_range: DurationRange
    date_range: DateRange


class SearchSuggestion(BaseModel):
    """Search suggestion item"""
    id: str
    text: str
    type: str = Field(description="Type of suggestion (query, tag, title)")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class SearchSuggestionsResponse(BaseModel):
    """Search suggestions response"""
    suggestions: List[SearchSuggestion] = Field(default=[], description="Search suggestions")


class TrendingSearch(BaseModel):
    """Trending search term"""
    query: str
    count: int = Field(ge=0, description="Number of times searched")
    trend: str = Field(description="Trend direction (up, down, stable)")


class TrendingSearchesResponse(BaseModel):
    """Trending searches response"""
    trending: List[TrendingSearch] = Field(default=[], description="Trending search terms")
    period_days: int = Field(ge=1, description="Period in days")


# Request validation schemas
class SearchRequest(BaseModel):
    """Search request parameters"""
    query: Optional[str] = Field(None, max_length=500, description="Search query")
    tags: Optional[List[str]] = Field(default=[], max_items=20, description="Tag names to filter by")
    status: Optional[str] = Field(None, pattern=r'^(draft|processing|published|failed)$', description="Episode status filter")
    date_from: Optional[datetime] = Field(None, description="Start date for publication date range")
    date_to: Optional[datetime] = Field(None, description="End date for publication date range")
    duration_min: Optional[int] = Field(None, ge=0, le=86400, description="Minimum duration in seconds")
    duration_max: Optional[int] = Field(None, ge=0, le=86400, description="Maximum duration in seconds")
    sort_by: str = Field(default="relevance", pattern=r'^(relevance|date|title|duration)$', description="Sort field")
    sort_order: str = Field(default="desc", pattern=r'^(asc|desc)$', description="Sort direction")
    page: int = Field(default=1, ge=1, le=1000, description="Page number")
    limit: int = Field(default=20, ge=1, le=50, description="Results per page")
    
    @validator('date_to')
    def validate_date_range(cls, date_to, values):
        """Ensure date_to is after date_from if both are provided"""
        date_from = values.get('date_from')
        if date_from and date_to and date_to < date_from:
            raise ValueError('date_to must be after date_from')
        return date_to
    
    @validator('duration_max')
    def validate_duration_range(cls, duration_max, values):
        """Ensure duration_max is greater than duration_min if both are provided"""
        duration_min = values.get('duration_min')
        if duration_min and duration_max and duration_max < duration_min:
            raise ValueError('duration_max must be greater than duration_min')
        return duration_max


class SearchSuggestionsRequest(BaseModel):
    """Search suggestions request parameters"""
    query: str = Field(min_length=1, max_length=100, description="Partial search query")
    limit: int = Field(default=5, ge=1, le=20, description="Maximum suggestions to return")


class RebuildIndexRequest(BaseModel):
    """Rebuild search index request"""
    channel_id: Optional[int] = Field(None, description="Optional channel ID to rebuild index for")


class RebuildIndexResponse(BaseModel):
    """Rebuild search index response"""
    success: bool
    message: str