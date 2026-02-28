"""
Search Repository Interface for full-text search operations
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.domain.entities.episode import Episode


class SearchFilters:
    """Filters for search operations"""
    
    def __init__(
        self,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        duration_min: Optional[int] = None,
        duration_max: Optional[int] = None,
        sort_by: str = "relevance",
        sort_order: str = "desc"
    ):
        self.query = query
        self.tags = tags or []
        self.status = status
        self.date_from = date_from
        self.date_to = date_to
        self.duration_min = duration_min
        self.duration_max = duration_max
        self.sort_by = sort_by
        self.sort_order = sort_order


class SearchResult:
    """Result of a search operation with metadata"""
    
    def __init__(
        self,
        episode: Episode,
        relevance_score: float = 0.0,
        highlights: Optional[Dict[str, List[str]]] = None
    ):
        self.episode = episode
        self.relevance_score = relevance_score
        self.highlights = highlights or {}


class SearchResponse:
    """Complete search response with results and metadata"""
    
    def __init__(
        self,
        results: List[SearchResult],
        total_count: int,
        page: int,
        per_page: int,
        execution_time: float = 0.0,
        filters_applied: Optional[Dict[str, Any]] = None
    ):
        self.results = results
        self.total_count = total_count
        self.page = page
        self.per_page = per_page
        self.has_more = (page * per_page) < total_count
        self.execution_time = execution_time
        self.filters_applied = filters_applied or {}


class FilterOptions:
    """Available filter options for search interface"""
    
    def __init__(
        self,
        available_tags: List[Dict[str, Any]],
        status_options: List[str],
        duration_range: Dict[str, int],
        date_range: Dict[str, Optional[datetime]]
    ):
        self.available_tags = available_tags
        self.status_options = status_options
        self.duration_range = duration_range
        self.date_range = date_range


class SearchRepository(ABC):
    """Abstract repository for search operations"""
    
    @abstractmethod
    async def search_episodes(
        self,
        channel_id: int,
        filters: SearchFilters,
        page: int = 1,
        limit: int = 20
    ) -> SearchResponse:
        """
        Search episodes with full-text search and filtering
        
        Args:
            channel_id: ID of the channel to search within
            filters: Search filters and criteria
            page: Page number for pagination
            limit: Number of results per page
            
        Returns:
            SearchResponse with results and metadata
        """
        pass
    
    @abstractmethod
    async def get_filter_options(self, channel_id: int) -> FilterOptions:
        """
        Get available filter options for search interface
        
        Args:
            channel_id: ID of the channel
            
        Returns:
            FilterOptions with available filter values
        """
        pass
    
    @abstractmethod
    async def rebuild_search_index(self, channel_id: Optional[int] = None) -> bool:
        """
        Rebuild the full-text search index
        
        Args:
            channel_id: Optional channel ID to rebuild index for specific channel
            
        Returns:
            True if rebuild was successful
        """
        pass