"""
Tag Management API Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Path
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.core.dependencies import get_database_session
from app.application.services.tag_service import TagService, TagCreate, TagUpdate
from app.application.services.bulk_tag_service import BulkTagService
from app.presentation.schemas.tag_schemas import (
    TagResponse, TagCreateRequest, TagUpdateRequest, TagListResponse,
    TagSuggestionsResponse, TagStatisticsResponse, BulkAssignRequest,
    BulkRemoveRequest, BulkOperationResponse, TagMergeRequest
)

router = APIRouter(prefix="/tags", tags=["tags"])


def get_tag_service(db: Session = Depends(get_database_session)) -> TagService:
    """Dependency to get TagService instance"""
    return TagService(db)


def get_bulk_tag_service(db: Session = Depends(get_database_session)) -> BulkTagService:
    """Dependency to get BulkTagService instance"""
    return BulkTagService(db)


@router.post("/", response_model=TagResponse)
async def create_tag(
    request: TagCreateRequest,
    tag_service: TagService = Depends(get_tag_service)
):
    """
    Create a new tag
    
    Creates a new tag with the specified name and color for a channel.
    Tag names must be unique within a channel.
    """
    
    try:
        tag_data = TagCreate(
            name=request.name,
            color=request.color,
            channel_id=request.channel_id
        )
        
        tag = await tag_service.create_tag(tag_data)
        
        return TagResponse(
            id=tag.id,
            channel_id=tag.channel_id,
            name=tag.name,
            color=tag.color,
            usage_count=0,
            is_system_tag=False,
            created_at=tag.created_at,
            updated_at=tag.updated_at
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create tag: {str(e)}")


@router.get("/", response_model=TagListResponse)
async def list_tags(
    channel_id: int = Query(..., description="Channel ID to get tags for"),
    search: Optional[str] = Query(None, max_length=100, description="Search query to filter tag names"),
    sort_by: str = Query(default="name", pattern=r'^(name|usage_count|created_at)$', description="Field to sort by"),
    sort_order: str = Query(default="asc", pattern=r'^(asc|desc)$', description="Sort direction"),
    include_unused: bool = Query(default=True, description="Include tags with zero usage"),
    limit: Optional[int] = Query(default=None, ge=1, le=500, description="Limit number of results"),
    tag_service: TagService = Depends(get_tag_service)
):
    """
    List tags for a channel with filtering and sorting options
    
    Supports:
    - Search by tag name
    - Sorting by name, usage count, or creation date
    - Optional exclusion of unused tags
    - Results limiting
    """
    
    try:
        tags = await tag_service.get_tags(
            channel_id=channel_id,
            search_query=search,
            sort_by=sort_by,
            sort_order=sort_order,
            include_unused=include_unused,
            limit=limit
        )
        
        tag_responses = [
            TagResponse(
                id=tag.id,
                channel_id=tag.channel_id,
                name=tag.name,
                color=tag.color,
                usage_count=getattr(tag, 'usage_count', 0),
                is_system_tag=getattr(tag, 'is_system_tag', False),
                created_at=tag.created_at,
                updated_at=tag.updated_at
            )
            for tag in tags
        ]
        
        return TagListResponse(
            tags=tag_responses,
            total_count=len(tag_responses),
            channel_id=channel_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tags: {str(e)}")


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(
    tag_id: int = Path(..., description="Tag ID"),
    tag_service: TagService = Depends(get_tag_service)
):
    """Get a specific tag by ID"""
    
    try:
        tag = await tag_service.get_tag_by_id(tag_id)
        
        if not tag:
            raise HTTPException(status_code=404, detail="Tag not found")
        
        return TagResponse(
            id=tag.id,
            channel_id=tag.channel_id,
            name=tag.name,
            color=tag.color,
            usage_count=getattr(tag, 'usage_count', 0),
            is_system_tag=getattr(tag, 'is_system_tag', False),
            created_at=tag.created_at,
            updated_at=tag.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tag: {str(e)}")


@router.put("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: int = Path(..., description="Tag ID"),
    request: TagUpdateRequest = ...,
    tag_service: TagService = Depends(get_tag_service)
):
    """
    Update a tag's name and/or color
    
    System tags cannot be renamed but their color can be changed.
    """
    
    try:
        tag_data = TagUpdate(
            name=request.name,
            color=request.color
        )
        
        updated_tag = await tag_service.update_tag(tag_id, tag_data)
        
        if not updated_tag:
            raise HTTPException(status_code=404, detail="Tag not found")
        
        return TagResponse(
            id=updated_tag.id,
            channel_id=updated_tag.channel_id,
            name=updated_tag.name,
            color=updated_tag.color,
            usage_count=getattr(updated_tag, 'usage_count', 0),
            is_system_tag=getattr(updated_tag, 'is_system_tag', False),
            created_at=updated_tag.created_at,
            updated_at=updated_tag.updated_at
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update tag: {str(e)}")


@router.delete("/{tag_id}")
async def delete_tag(
    tag_id: int = Path(..., description="Tag ID"),
    merge_to: Optional[int] = Query(None, description="Optional tag ID to merge associations to"),
    delete_associations: bool = Query(default=True, description="Whether to delete episode associations"),
    tag_service: TagService = Depends(get_tag_service)
):
    """
    Delete a tag with optional merging
    
    Options:
    - Delete with all associations removed
    - Delete with associations merged to another tag
    - System tags cannot be deleted
    """
    
    try:
        success = await tag_service.delete_tag(
            tag_id=tag_id,
            merge_to=merge_to,
            delete_associations=delete_associations
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Tag not found")
        
        return {"message": "Tag deleted successfully", "tag_id": tag_id}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete tag: {str(e)}")


@router.get("/suggestions", response_model=TagSuggestionsResponse)
async def get_tag_suggestions(
    channel_id: int = Query(..., description="Channel ID"),
    query: str = Query(..., min_length=1, max_length=100, description="Partial tag name"),
    limit: int = Query(default=10, ge=1, le=20, description="Maximum suggestions to return"),
    exclude: Optional[List[int]] = Query(default=[], description="Tag IDs to exclude from suggestions"),
    tag_service: TagService = Depends(get_tag_service)
):
    """
    Get tag suggestions for autocomplete
    
    Returns tags that match the query string, ranked by:
    1. Exact matches
    2. Starts with query
    3. Contains query
    4. Usage frequency
    """
    
    try:
        suggestions = await tag_service.get_tag_suggestions(
            query=query,
            channel_id=channel_id,
            limit=limit,
            exclude_ids=exclude
        )
        
        return TagSuggestionsResponse(
            suggestions=[
                {
                    "id": suggestion.tag_id,
                    "name": suggestion.name,
                    "color": suggestion.color,
                    "usage_count": suggestion.usage_count,
                    "match_score": suggestion.match_score
                }
                for suggestion in suggestions
            ],
            query=query,
            total_count=len(suggestions)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tag suggestions: {str(e)}")


@router.get("/statistics/{channel_id}", response_model=TagStatisticsResponse)
async def get_tag_statistics(
    channel_id: int = Path(..., description="Channel ID"),
    tag_service: TagService = Depends(get_tag_service)
):
    """Get comprehensive tag statistics for a channel"""
    
    try:
        stats = await tag_service.get_tag_statistics(channel_id)
        
        return TagStatisticsResponse(
            channel_id=channel_id,
            total_tags=stats["total_tags"],
            used_tags=stats["used_tags"],
            unused_tags=stats["unused_tags"],
            most_used_tags=stats["most_used"],
            recently_used_tags=stats["recently_used"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tag statistics: {str(e)}")


# Bulk Operations Endpoints

@router.post("/bulk/assign", response_model=BulkOperationResponse)
async def bulk_assign_tags(
    request: BulkAssignRequest,
    bulk_service: BulkTagService = Depends(get_bulk_tag_service)
):
    """
    Assign multiple tags to multiple episodes in bulk
    
    Useful for:
    - Adding the same tags to multiple episodes
    - Batch categorization of content
    """
    
    try:
        result = await bulk_service.assign_tags_to_episodes(
            episode_ids=request.episode_ids,
            tag_ids=request.tag_ids,
            channel_id=request.channel_id
        )
        
        return BulkOperationResponse(
            success=result.success,
            processed_count=result.processed_count,
            failed_count=result.failed_count,
            errors=result.errors,
            details=result.details
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk assign failed: {str(e)}")


@router.post("/bulk/remove", response_model=BulkOperationResponse)
async def bulk_remove_tags(
    request: BulkRemoveRequest,
    bulk_service: BulkTagService = Depends(get_bulk_tag_service)
):
    """
    Remove multiple tags from multiple episodes in bulk
    
    Useful for:
    - Cleaning up incorrect categorizations
    - Batch removal of deprecated tags
    """
    
    try:
        result = await bulk_service.remove_tags_from_episodes(
            episode_ids=request.episode_ids,
            tag_ids=request.tag_ids,
            channel_id=request.channel_id
        )
        
        return BulkOperationResponse(
            success=result.success,
            processed_count=result.processed_count,
            failed_count=result.failed_count,
            errors=result.errors,
            details=result.details
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk remove failed: {str(e)}")


@router.post("/bulk/merge", response_model=BulkOperationResponse)
async def merge_tags(
    request: TagMergeRequest,
    bulk_service: BulkTagService = Depends(get_bulk_tag_service)
):
    """
    Merge multiple tags into a single target tag
    
    All episodes associated with source tags will be associated with the target tag.
    Source tags will be deleted after successful merge.
    """
    
    try:
        result = await bulk_service.merge_tags(
            source_tag_ids=request.source_tag_ids,
            target_tag_id=request.target_tag_id,
            channel_id=request.channel_id
        )
        
        return BulkOperationResponse(
            success=result.success,
            processed_count=result.processed_count,
            failed_count=result.failed_count,
            errors=result.errors,
            details=result.details
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tag merge failed: {str(e)}")


@router.post("/bulk/copy", response_model=BulkOperationResponse)
async def copy_tags_between_episodes(
    source_episode_id: int = Query(..., description="Episode ID to copy tags from"),
    target_episode_ids: List[int] = Query(..., description="Episode IDs to copy tags to"),
    channel_id: Optional[int] = Query(None, description="Optional channel ID for validation"),
    bulk_service: BulkTagService = Depends(get_bulk_tag_service)
):
    """
    Copy all tags from one episode to multiple other episodes
    
    Useful for:
    - Applying the same categorization to similar content
    - Batch tagging based on a template episode
    """
    
    try:
        result = await bulk_service.copy_tags_between_episodes(
            source_episode_id=source_episode_id,
            target_episode_ids=target_episode_ids,
            channel_id=channel_id
        )
        
        return BulkOperationResponse(
            success=result.success,
            processed_count=result.processed_count,
            failed_count=result.failed_count,
            errors=result.errors,
            details=result.details
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tag copy failed: {str(e)}")


@router.get("/colors/defaults")
async def get_default_colors():
    """Get list of predefined tag colors"""
    
    from app.domain.entities.tag import Tag
    
    return {
        "colors": Tag.get_default_colors(),
        "description": "Predefined color palette for tags"
    }