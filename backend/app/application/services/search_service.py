"""
Search Service for orchestrating search operations
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.domain.repositories.search_repository import (
    SearchRepository, SearchFilters, SearchResponse, FilterOptions
)
from app.infrastructure.repositories.search_repository import SearchRepositoryImpl

logger = logging.getLogger(__name__)


class SearchService:
    """Service layer for search operations"""
    
    def __init__(self, search_repository: SearchRepository):
        self.search_repository = search_repository
    
    async def search_episodes(
        self,
        channel_id: int,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        duration_min: Optional[int] = None,
        duration_max: Optional[int] = None,
        sort_by: str = "relevance",
        sort_order: str = "desc",
        page: int = 1,
        limit: int = 20
    ) -> SearchResponse:
        """
        Search episodes with comprehensive filtering and ranking
        
        Args:
            channel_id: ID of the channel to search within
            query: Optional search query for full-text search
            tags: Optional list of tag names to filter by
            status: Optional episode status filter
            date_from: Optional start date for publication date range
            date_to: Optional end date for publication date range
            duration_min: Optional minimum duration in seconds
            duration_max: Optional maximum duration in seconds
            sort_by: Field to sort by (relevance, date, title, duration)
            sort_order: Sort direction (asc, desc)
            page: Page number for pagination
            limit: Number of results per page (max 50)
            
        Returns:
            SearchResponse with results and metadata
        """
        
        # Validate and sanitize inputs
        limit = min(max(1, limit), 50)  # Enforce limits
        page = max(1, page)
        sort_by = self._validate_sort_field(sort_by)
        sort_order = sort_order.lower() if sort_order.lower() in ['asc', 'desc'] else 'desc'
        
        # Validate date range
        if date_from and date_to and date_from > date_to:
            date_from, date_to = date_to, date_from  # Swap if reversed
        
        # Validate duration range
        if duration_min and duration_max and duration_min > duration_max:
            duration_min, duration_max = duration_max, duration_min  # Swap if reversed
        
        # Create search filters
        filters = SearchFilters(
            query=query.strip() if query else None,
            tags=tags or [],
            status=status,
            date_from=date_from,
            date_to=date_to,
            duration_min=duration_min,
            duration_max=duration_max,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        try:
            # Log search operation
            logger.info(f"Searching episodes for channel {channel_id} with query: '{query}', filters: {filters.__dict__}")
            
            # Perform search
            response = await self.search_repository.search_episodes(
                channel_id=channel_id,
                filters=filters,
                page=page,
                limit=limit
            )
            
            # Log search results
            logger.info(f"Search completed in {response.execution_time:.3f}s, found {response.total_count} results")
            
            return response
            
        except Exception as e:
            logger.error(f"Search failed for channel {channel_id}: {e}")
            raise
    
    async def get_filter_options(self, channel_id: int) -> FilterOptions:
        """
        Get available filter options for search interface
        
        Args:
            channel_id: ID of the channel
            
        Returns:
            FilterOptions with available filter values
        """
        
        try:
            return await self.search_repository.get_filter_options(channel_id)
        except Exception as e:
            logger.error(f"Failed to get filter options for channel {channel_id}: {e}")
            raise
    
    async def rebuild_search_index(self, channel_id: Optional[int] = None) -> bool:
        """
        Rebuild the search index for better performance
        
        Args:
            channel_id: Optional channel ID to rebuild index for specific channel
            
        Returns:
            True if rebuild was successful
        """
        
        try:
            logger.info(f"Rebuilding search index for channel: {channel_id or 'all'}")
            success = await self.search_repository.rebuild_search_index(channel_id)
            
            if success:
                logger.info("Search index rebuilt successfully")
            else:
                logger.warning("Search index rebuild failed")
                
            return success
            
        except Exception as e:
            logger.error(f"Failed to rebuild search index: {e}")
            return False
    
    async def get_search_suggestions(
        self,
        channel_id: int,
        partial_query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get search suggestions based on partial query
        
        Args:
            channel_id: ID of the channel
            partial_query: Partial search query
            limit: Maximum number of suggestions
            
        Returns:
            List of search suggestions
        """
        
        if not partial_query or len(partial_query.strip()) < 2:
            return []
        
        try:
            # For now, return simple suggestions based on episode titles
            # This could be enhanced with more sophisticated suggestion logic
            filters = SearchFilters(
                query=partial_query.strip(),
                sort_by="relevance",
                sort_order="desc"
            )
            
            response = await self.search_repository.search_episodes(
                channel_id=channel_id,
                filters=filters,
                page=1,
                limit=limit
            )
            
            suggestions = []
            for result in response.results:
                suggestions.append({
                    "id": f"episode_{result.episode.id}",
                    "text": result.episode.title,
                    "type": "episode_title",
                    "metadata": {
                        "episode_id": result.episode.id,
                        "relevance_score": result.relevance_score
                    }
                })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Failed to get search suggestions: {e}")
            return []
    
    async def get_trending_searches(
        self,
        channel_id: int,
        days: int = 7,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get trending search terms (placeholder for future implementation)
        
        Args:
            channel_id: ID of the channel
            days: Number of days to look back
            limit: Maximum number of trending searches
            
        Returns:
            List of trending search terms
        """
        
        # This is a placeholder implementation
        # In a real system, you would track search queries and their frequency
        logger.info(f"Getting trending searches for channel {channel_id} (placeholder)")
        
        return []
    
    def _validate_sort_field(self, sort_by: str) -> str:
        """Validate and normalize sort field"""
        
        valid_fields = ['relevance', 'date', 'title', 'duration']
        
        if sort_by.lower() in valid_fields:
            return sort_by.lower()
        
        # Default to relevance for invalid fields
        return 'relevance'
    
    def _calculate_relevance_boost(
        self,
        episode_title: str,
        episode_description: str,
        search_query: str
    ) -> float:
        """
        Calculate relevance boost based on search term matches
        
        Args:
            episode_title: Episode title
            episode_description: Episode description
            search_query: Search query
            
        Returns:
            Relevance boost factor (1.0 = no boost, >1.0 = boosted)
        """
        
        if not search_query:
            return 1.0
        
        boost = 1.0
        query_lower = search_query.lower()
        
        # Boost for exact title matches
        if episode_title and query_lower in episode_title.lower():
            boost += 0.5
        
        # Boost for title word matches
        if episode_title:
            title_words = episode_title.lower().split()
            query_words = query_lower.split()
            
            for query_word in query_words:
                if query_word in title_words:
                    boost += 0.1
        
        # Smaller boost for description matches
        if episode_description and query_lower in episode_description.lower():
            boost += 0.2
        
        return boost