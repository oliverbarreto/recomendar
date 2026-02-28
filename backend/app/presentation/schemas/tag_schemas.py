"""
Pydantic schemas for tag API endpoints
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


class TagCreateRequest(BaseModel):
    """Request schema for creating a new tag"""
    name: str = Field(..., min_length=1, max_length=50, description="Tag name")
    color: str = Field(default="#3B82F6", pattern=r'^#[0-9A-Fa-f]{6}$', description="Hex color code")
    channel_id: int = Field(..., gt=0, description="Channel ID")
    
    @validator('name')
    def validate_name(cls, name):
        """Validate and normalize tag name"""
        if not name or not name.strip():
            raise ValueError("Tag name cannot be empty")
        return name.strip()


class TagUpdateRequest(BaseModel):
    """Request schema for updating a tag"""
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="New tag name")
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$', description="New hex color code")
    
    @validator('name')
    def validate_name(cls, name):
        """Validate and normalize tag name"""
        if name is not None:
            if not name.strip():
                raise ValueError("Tag name cannot be empty")
            return name.strip()
        return name


class TagResponse(BaseModel):
    """Response schema for tag data"""
    id: int
    channel_id: int
    name: str
    color: str
    usage_count: int = Field(default=0, description="Number of episodes using this tag")
    is_system_tag: bool = Field(default=False, description="Whether this is a system tag")
    created_at: datetime
    updated_at: datetime


class TagListResponse(BaseModel):
    """Response schema for list of tags"""
    tags: List[TagResponse]
    total_count: int = Field(description="Total number of tags returned")
    channel_id: int


class TagSuggestion(BaseModel):
    """Individual tag suggestion for autocomplete"""
    id: int
    name: str
    color: str
    usage_count: int = Field(ge=0, description="Number of episodes using this tag")
    match_score: float = Field(ge=0.0, le=1.0, description="Relevance score (0-1)")


class TagSuggestionsResponse(BaseModel):
    """Response schema for tag suggestions"""
    suggestions: List[TagSuggestion]
    query: str = Field(description="Original search query")
    total_count: int = Field(description="Number of suggestions returned")


class TagStatisticsResponse(BaseModel):
    """Response schema for tag statistics"""
    channel_id: int
    total_tags: int = Field(ge=0, description="Total number of tags")
    used_tags: int = Field(ge=0, description="Number of tags with usage > 0")
    unused_tags: int = Field(ge=0, description="Number of tags with usage = 0")
    most_used_tags: List[Dict[str, Any]] = Field(default=[], description="Most frequently used tags")
    recently_used_tags: List[Dict[str, Any]] = Field(default=[], description="Recently used tags")


# Bulk Operations Schemas

class BulkAssignRequest(BaseModel):
    """Request schema for bulk tag assignment"""
    episode_ids: List[int] = Field(..., min_items=1, max_items=100, description="Episode IDs to assign tags to")
    tag_ids: List[int] = Field(..., min_items=1, max_items=20, description="Tag IDs to assign")
    channel_id: Optional[int] = Field(None, description="Optional channel ID for validation")
    
    @validator('episode_ids')
    def validate_episode_ids(cls, episode_ids):
        """Ensure episode IDs are unique"""
        if len(episode_ids) != len(set(episode_ids)):
            raise ValueError("Episode IDs must be unique")
        return episode_ids
    
    @validator('tag_ids')
    def validate_tag_ids(cls, tag_ids):
        """Ensure tag IDs are unique"""
        if len(tag_ids) != len(set(tag_ids)):
            raise ValueError("Tag IDs must be unique")
        return tag_ids


class BulkRemoveRequest(BaseModel):
    """Request schema for bulk tag removal"""
    episode_ids: List[int] = Field(..., min_items=1, max_items=100, description="Episode IDs to remove tags from")
    tag_ids: List[int] = Field(..., min_items=1, max_items=20, description="Tag IDs to remove")
    channel_id: Optional[int] = Field(None, description="Optional channel ID for validation")
    
    @validator('episode_ids')
    def validate_episode_ids(cls, episode_ids):
        """Ensure episode IDs are unique"""
        if len(episode_ids) != len(set(episode_ids)):
            raise ValueError("Episode IDs must be unique")
        return episode_ids
    
    @validator('tag_ids')
    def validate_tag_ids(cls, tag_ids):
        """Ensure tag IDs are unique"""
        if len(tag_ids) != len(set(tag_ids)):
            raise ValueError("Tag IDs must be unique")
        return tag_ids


class TagMergeRequest(BaseModel):
    """Request schema for merging tags"""
    source_tag_ids: List[int] = Field(..., min_items=1, max_items=10, description="Tag IDs to merge (will be deleted)")
    target_tag_id: int = Field(..., description="Target tag ID to merge into (will be kept)")
    channel_id: Optional[int] = Field(None, description="Optional channel ID for validation")
    
    @validator('source_tag_ids')
    def validate_source_tag_ids(cls, source_tag_ids):
        """Ensure source tag IDs are unique"""
        if len(source_tag_ids) != len(set(source_tag_ids)):
            raise ValueError("Source tag IDs must be unique")
        return source_tag_ids
    
    @validator('target_tag_id')
    def validate_target_not_in_source(cls, target_tag_id, values):
        """Ensure target tag is not in source list"""
        source_tag_ids = values.get('source_tag_ids', [])
        if target_tag_id in source_tag_ids:
            raise ValueError("Target tag cannot be in the list of source tags")
        return target_tag_id


class BulkOperationResponse(BaseModel):
    """Response schema for bulk operations"""
    success: bool
    processed_count: int = Field(ge=0, description="Number of successfully processed items")
    failed_count: int = Field(ge=0, description="Number of failed items")
    errors: List[str] = Field(default=[], description="List of error messages")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional operation details")


class TagColorValidationRequest(BaseModel):
    """Request schema for color validation"""
    color: str = Field(..., description="Hex color code to validate")
    check_similarity: bool = Field(default=False, description="Check for similar colors")
    channel_id: Optional[int] = Field(None, description="Channel ID to check against")


class TagColorValidationResponse(BaseModel):
    """Response schema for color validation"""
    is_valid: bool
    normalized_color: Optional[str] = Field(None, description="Normalized hex color if valid")
    similar_colors: List[Dict[str, Any]] = Field(default=[], description="Similar existing colors")
    contrast_text_color: Optional[str] = Field(None, description="Recommended text color for contrast")


class TagImportRequest(BaseModel):
    """Request schema for importing tags from CSV/JSON"""
    tags: List[Dict[str, Any]] = Field(..., min_items=1, max_items=100, description="Tags to import")
    channel_id: int = Field(..., gt=0, description="Channel ID")
    overwrite_existing: bool = Field(default=False, description="Overwrite existing tags with same name")
    
    @validator('tags')
    def validate_tags_format(cls, tags):
        """Validate tags format"""
        required_fields = ['name']
        for tag in tags:
            if not isinstance(tag, dict):
                raise ValueError("Each tag must be a dictionary")
            
            for field in required_fields:
                if field not in tag:
                    raise ValueError(f"Tag missing required field: {field}")
            
            if 'color' in tag and tag['color']:
                import re
                if not re.match(r'^#[0-9A-Fa-f]{6}$', tag['color']):
                    raise ValueError(f"Invalid color format: {tag['color']}")
        
        return tags


class TagImportResponse(BaseModel):
    """Response schema for tag import"""
    success: bool
    imported_count: int = Field(ge=0, description="Number of successfully imported tags")
    updated_count: int = Field(ge=0, description="Number of updated existing tags")
    failed_count: int = Field(ge=0, description="Number of failed imports")
    errors: List[str] = Field(default=[], description="Import error messages")
    imported_tags: List[TagResponse] = Field(default=[], description="Successfully imported tags")


class TagExportRequest(BaseModel):
    """Request schema for exporting tags"""
    channel_id: int = Field(..., gt=0, description="Channel ID")
    format: str = Field(default="json", pattern=r'^(json|csv)$', description="Export format")
    include_usage: bool = Field(default=True, description="Include usage statistics")
    include_associations: bool = Field(default=False, description="Include episode associations")


class TagExportResponse(BaseModel):
    """Response schema for tag export"""
    format: str
    data: str = Field(description="Exported data as string")
    filename: str = Field(description="Suggested filename")
    count: int = Field(ge=0, description="Number of exported tags")