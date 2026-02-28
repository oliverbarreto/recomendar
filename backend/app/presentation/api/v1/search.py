"""
Search API Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from app.core.dependencies import get_database_session
from app.application.services.search_service import SearchService
from app.infrastructure.repositories.search_repository import SearchRepositoryImpl
from app.presentation.schemas.search_schemas import (
    SearchResponse, FilterOptionsResponse, SearchSuggestionsResponse,
    TrendingSearchesResponse, RebuildIndexResponse
)

router = APIRouter(prefix="/search", tags=["search"])


def get_search_service(db: Session = Depends(get_database_session)) -> SearchService:
    """Dependency to get SearchService instance"""
    search_repository = SearchRepositoryImpl(db)
    return SearchService(search_repository)


@router.get("/episodes", response_model=SearchResponse)
async def search_episodes(
    channel_id: int = Query(..., description="Channel ID to search within"),
    query: Optional[str] = Query(None, max_length=500, description="Search query"),
    tags: Optional[List[str]] = Query(default=[], description="Tag names to filter by"),
    status: Optional[str] = Query(None, pattern=r'^(draft|processing|published|failed)$', description="Episode status"),
    date_from: Optional[datetime] = Query(None, description="Start date for publication date range"),
    date_to: Optional[datetime] = Query(None, description="End date for publication date range"),
    duration_min: Optional[int] = Query(None, ge=0, le=86400, description="Minimum duration in seconds"),
    duration_max: Optional[int] = Query(None, ge=0, le=86400, description="Maximum duration in seconds"),
    sort_by: str = Query(default="relevance", pattern=r'^(relevance|date|title|duration)$', description="Sort field"),
    sort_order: str = Query(default="desc", pattern=r'^(asc|desc)$', description="Sort direction"),
    page: int = Query(default=1, ge=1, le=1000, description="Page number"),
    limit: int = Query(default=20, ge=1, le=50, description="Results per page"),
    search_service: SearchService = Depends(get_search_service)
):
    """
    Search episodes with full-text search and advanced filtering
    
    Supports:
    - Full-text search across episode titles and descriptions
    - Tag-based filtering
    - Date range filtering
    - Duration range filtering
    - Status filtering
    - Multiple sorting options
    - Pagination with metadata
    """
    
    try:
        # Validate date range
        if date_from and date_to and date_from > date_to:
            raise HTTPException(
                status_code=400,
                detail="date_from must be before date_to"
            )
        
        # Validate duration range
        if duration_min and duration_max and duration_min > duration_max:
            raise HTTPException(
                status_code=400,
                detail="duration_min must be less than duration_max"
            )
        
        # Perform search
        response = await search_service.search_episodes(
            channel_id=channel_id,
            query=query,
            tags=tags,
            status=status,
            date_from=date_from,
            date_to=date_to,
            duration_min=duration_min,
            duration_max=duration_max,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            limit=limit
        )
        
        # Convert to response schema
        return _convert_search_response(response)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/filters", response_model=FilterOptionsResponse)
async def get_filter_options(
    channel_id: int = Query(..., description="Channel ID"),
    search_service: SearchService = Depends(get_search_service)
):
    """
    Get available filter options for search interface
    
    Returns:
    - Available tags with usage counts
    - Available episode statuses
    - Duration range (min/max)
    - Date range (earliest/latest)
    """
    
    try:
        filter_options = await search_service.get_filter_options(channel_id)
        
        return FilterOptionsResponse(
            available_tags=[
                {
                    "id": tag["id"],
                    "name": tag["name"],
                    "color": tag["color"],
                    "episode_count": tag["episode_count"]
                }
                for tag in filter_options.available_tags
            ],
            status_options=filter_options.status_options,
            duration_range={
                "min": filter_options.duration_range["min"],
                "max": filter_options.duration_range["max"]
            },
            date_range={
                "earliest": filter_options.date_range["earliest"],
                "latest": filter_options.date_range["latest"]
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get filter options: {str(e)}")


@router.get("/suggestions", response_model=SearchSuggestionsResponse)
async def get_search_suggestions(
    channel_id: int = Query(..., description="Channel ID"),
    query: str = Query(..., min_length=1, max_length=100, description="Partial search query"),
    limit: int = Query(default=5, ge=1, le=20, description="Maximum suggestions to return"),
    search_service: SearchService = Depends(get_search_service)
):
    """
    Get search suggestions based on partial query
    
    Returns suggestions based on:
    - Episode titles that match the partial query
    - Popular search terms (future enhancement)
    - Tag names (future enhancement)
    """
    
    try:
        suggestions = await search_service.get_search_suggestions(
            channel_id=channel_id,
            partial_query=query,
            limit=limit
        )
        
        return SearchSuggestionsResponse(suggestions=suggestions)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")


@router.get("/trending", response_model=TrendingSearchesResponse)
async def get_trending_searches(
    channel_id: int = Query(..., description="Channel ID"),
    days: int = Query(default=7, ge=1, le=30, description="Number of days to analyze"),
    limit: int = Query(default=10, ge=1, le=20, description="Maximum trending terms to return"),
    search_service: SearchService = Depends(get_search_service)
):
    """
    Get trending search terms for the past N days
    
    Note: This is a placeholder endpoint for future implementation
    when search analytics are implemented.
    """
    
    try:
        trending = await search_service.get_trending_searches(
            channel_id=channel_id,
            days=days,
            limit=limit
        )
        
        return TrendingSearchesResponse(
            trending=trending,
            period_days=days
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trending searches: {str(e)}")


@router.post("/reindex", response_model=RebuildIndexResponse)
async def rebuild_search_index(
    channel_id: Optional[int] = Query(None, description="Optional channel ID to rebuild index for"),
    search_service: SearchService = Depends(get_search_service)
):
    """
    Rebuild the full-text search index
    
    This can be useful if the search index becomes corrupted or
    if you want to ensure optimal search performance.
    
    Args:
        channel_id: If provided, rebuilds index only for this channel.
                   If None, rebuilds the entire search index.
    """
    
    try:
        success = await search_service.rebuild_search_index(channel_id)
        
        if success:
            message = f"Search index rebuilt successfully"
            if channel_id:
                message += f" for channel {channel_id}"
        else:
            message = "Failed to rebuild search index"
            
        return RebuildIndexResponse(
            success=success,
            message=message
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rebuild index: {str(e)}")


def _convert_search_response(response) -> SearchResponse:
    """Convert internal SearchResponse to API response schema"""
    
    return SearchResponse(
        results=[
            {
                "episode": {
                    "id": result.episode.id,
                    "title": result.episode.title,
                    "description": result.episode.description,
                    "duration": result.episode.duration,
                    "status": result.episode.status,
                    "publication_date": result.episode.publication_date,
                    "thumbnail_url": None,  # Will be populated when thumbnails are implemented
                    "youtube_url": result.episode.youtube_url,
                    "episode_number": result.episode.episode_number,
                    "season_number": result.episode.season_number,
                    "tags": []  # Tags will be populated separately if needed
                },
                "relevance_score": result.relevance_score,
                "highlights": {
                    "title": result.highlights.get("title", []),
                    "description": result.highlights.get("description", [])
                }
            }
            for result in response.results
        ],
        total_count=response.total_count,
        page=response.page,
        per_page=response.per_page,
        has_more=response.has_more,
        search_meta={
            "query": response.filters_applied.get("query"),
            "execution_time": response.execution_time,
            "filters_applied": response.filters_applied
        }
    )