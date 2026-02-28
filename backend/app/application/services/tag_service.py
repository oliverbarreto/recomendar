"""
Tag Service for managing tags with CRUD operations and advanced features
"""
import logging
import re
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text, func, and_, or_
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.domain.entities.tag import Tag
from app.infrastructure.database.models.tag import TagModel, episode_tags
from app.infrastructure.database.models.episode import EpisodeModel

logger = logging.getLogger(__name__)


class TagCreate:
    """Data for creating a new tag"""
    def __init__(self, name: str, color: str = "#3B82F6", channel_id: int = None):
        self.name = name
        self.color = color
        self.channel_id = channel_id


class TagUpdate:
    """Data for updating an existing tag"""
    def __init__(self, name: Optional[str] = None, color: Optional[str] = None):
        self.name = name
        self.color = color


class TagStatistics:
    """Tag usage statistics"""
    def __init__(
        self,
        tag_id: int,
        usage_count: int,
        last_used_at: Optional[datetime] = None,
        episode_ids: Optional[List[int]] = None
    ):
        self.tag_id = tag_id
        self.usage_count = usage_count
        self.last_used_at = last_used_at
        self.episode_ids = episode_ids or []


class TagSuggestion:
    """Tag autocomplete suggestion"""
    def __init__(
        self,
        tag_id: int,
        name: str,
        color: str,
        usage_count: int = 0,
        match_score: float = 0.0
    ):
        self.tag_id = tag_id
        self.name = name
        self.color = color
        self.usage_count = usage_count
        self.match_score = match_score


class BulkOperationResult:
    """Result of bulk tag operation"""
    def __init__(
        self,
        success: bool,
        processed_count: int = 0,
        failed_count: int = 0,
        errors: List[str] = None
    ):
        self.success = success
        self.processed_count = processed_count
        self.failed_count = failed_count
        self.errors = errors or []


class TagService:
    """Service for comprehensive tag management"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
    
    async def create_tag(self, tag_data: TagCreate) -> Tag:
        """
        Create a new tag with validation and duplicate prevention
        
        Args:
            tag_data: Tag creation data
            
        Returns:
            Created Tag entity
            
        Raises:
            ValueError: If tag name is invalid or already exists
        """
        
        # Validate tag name
        if not tag_data.name or not tag_data.name.strip():
            raise ValueError("Tag name cannot be empty")
        
        name = tag_data.name.strip()
        if len(name) > 50:
            raise ValueError("Tag name must be 50 characters or less")
        
        # Validate color format
        if not self._is_valid_hex_color(tag_data.color):
            raise ValueError("Invalid color format. Use hex format like #3B82F6")
        
        try:
            # Check for duplicate tag name in the same channel
            existing_tag = self.db_session.query(TagModel).filter(
                TagModel.channel_id == tag_data.channel_id,
                TagModel.name.ilike(name)  # Case-insensitive check
            ).first()
            
            if existing_tag:
                raise ValueError(f"Tag '{name}' already exists in this channel")
            
            # Create new tag
            tag_model = TagModel(
                name=name,
                color=tag_data.color,
                channel_id=tag_data.channel_id,
                usage_count=0,
                is_system_tag=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db_session.add(tag_model)
            self.db_session.commit()
            self.db_session.refresh(tag_model)
            
            logger.info(f"Created tag '{name}' with ID {tag_model.id} for channel {tag_data.channel_id}")
            
            return self._model_to_entity(tag_model)
            
        except IntegrityError as e:
            self.db_session.rollback()
            logger.error(f"Integrity error creating tag: {e}")
            raise ValueError("Tag creation failed due to database constraint")
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error(f"Database error creating tag: {e}")
            raise
    
    async def get_tags(
        self,
        channel_id: int,
        search_query: Optional[str] = None,
        sort_by: str = "name",
        sort_order: str = "asc",
        include_unused: bool = True,
        limit: Optional[int] = None
    ) -> List[Tag]:
        """
        Get tags for a channel with filtering and sorting

        Args:
            channel_id: Channel ID to get tags for
            search_query: Optional search query to filter tag names
            sort_by: Field to sort by (name, usage_count, created_at)
            sort_order: Sort direction (asc, desc)
            include_unused: Whether to include tags with zero usage
            limit: Optional limit on number of results

        Returns:
            List of Tag entities
        """

        try:
            # Get tags with calculated usage count from the association table
            query = self.db_session.query(
                TagModel,
                func.coalesce(func.count(episode_tags.c.episode_id), 0).label('actual_usage_count')
            ).outerjoin(
                episode_tags, TagModel.id == episode_tags.c.tag_id
            ).filter(
                TagModel.channel_id == channel_id
            ).group_by(TagModel.id)

            # Apply search filter
            if search_query and search_query.strip():
                search_term = f"%{search_query.strip()}%"
                query = query.filter(TagModel.name.ilike(search_term))

            # Filter out unused tags if requested
            if not include_unused:
                query = query.having(func.count(episode_tags.c.episode_id) > 0)

            # Apply sorting
            if sort_by == "usage_count":
                if sort_order.lower() == "desc":
                    query = query.order_by(func.count(episode_tags.c.episode_id).desc())
                else:
                    query = query.order_by(func.count(episode_tags.c.episode_id).asc())
            elif sort_by == "created_at":
                sort_column = TagModel.created_at
                if sort_order.lower() == "desc":
                    query = query.order_by(sort_column.desc())
                else:
                    query = query.order_by(sort_column.asc())
            else:  # default to name
                sort_column = TagModel.name
                if sort_order.lower() == "desc":
                    query = query.order_by(sort_column.desc())
                else:
                    query = query.order_by(sort_column.asc())

            # Apply limit
            if limit:
                query = query.limit(limit)

            results = query.all()

            # Convert to Tag entities with calculated usage count
            tags = []
            for tag_model, actual_usage_count in results:
                tag = self._model_to_entity(tag_model)
                # Override usage_count with the calculated value
                tag.usage_count = actual_usage_count
                tags.append(tag)

            return tags

        except SQLAlchemyError as e:
            logger.error(f"Database error getting tags: {e}")
            raise
    
    async def get_tag_by_id(self, tag_id: int) -> Optional[Tag]:
        """
        Get a tag by ID with calculated usage count

        Args:
            tag_id: Tag ID

        Returns:
            Tag entity or None if not found
        """

        try:
            # Get tag with calculated usage count
            result = self.db_session.query(
                TagModel,
                func.coalesce(func.count(episode_tags.c.episode_id), 0).label('actual_usage_count')
            ).outerjoin(
                episode_tags, TagModel.id == episode_tags.c.tag_id
            ).filter(
                TagModel.id == tag_id
            ).group_by(TagModel.id).first()

            if not result:
                return None

            tag_model, actual_usage_count = result
            tag = self._model_to_entity(tag_model)
            # Override usage_count with the calculated value
            tag.usage_count = actual_usage_count
            return tag

        except SQLAlchemyError as e:
            logger.error(f"Database error getting tag by ID: {e}")
            raise
    
    async def update_tag(self, tag_id: int, tag_data: TagUpdate) -> Optional[Tag]:
        """
        Update an existing tag
        
        Args:
            tag_id: ID of tag to update
            tag_data: Tag update data
            
        Returns:
            Updated Tag entity or None if not found
            
        Raises:
            ValueError: If update data is invalid
        """
        
        try:
            tag_model = self.db_session.get(TagModel, tag_id)
            if not tag_model:
                return None
            
            # Check if tag is system tag (protected from modification)
            if tag_model.is_system_tag and tag_data.name:
                raise ValueError("System tags cannot be renamed")
            
            # Validate and update name if provided
            if tag_data.name is not None:
                name = tag_data.name.strip()
                
                if not name:
                    raise ValueError("Tag name cannot be empty")
                
                if len(name) > 50:
                    raise ValueError("Tag name must be 50 characters or less")
                
                # Check for duplicate name in same channel
                existing_tag = self.db_session.query(TagModel).filter(
                    TagModel.channel_id == tag_model.channel_id,
                    TagModel.name.ilike(name),
                    TagModel.id != tag_id
                ).first()
                
                if existing_tag:
                    raise ValueError(f"Tag '{name}' already exists in this channel")
                
                tag_model.name = name
            
            # Validate and update color if provided
            if tag_data.color is not None:
                if not self._is_valid_hex_color(tag_data.color):
                    raise ValueError("Invalid color format. Use hex format like #3B82F6")
                tag_model.color = tag_data.color
            
            # Update timestamp
            tag_model.updated_at = datetime.utcnow()
            
            self.db_session.commit()
            self.db_session.refresh(tag_model)
            
            logger.info(f"Updated tag ID {tag_id}")
            
            return self._model_to_entity(tag_model)
            
        except IntegrityError as e:
            self.db_session.rollback()
            logger.error(f"Integrity error updating tag: {e}")
            raise ValueError("Tag update failed due to database constraint")
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error(f"Database error updating tag: {e}")
            raise
    
    async def delete_tag(
        self,
        tag_id: int,
        merge_to: Optional[int] = None,
        delete_associations: bool = True
    ) -> bool:
        """
        Delete a tag with optional merging to another tag
        
        Args:
            tag_id: ID of tag to delete
            merge_to: Optional ID of tag to merge associations to
            delete_associations: If True, delete episode associations; if False, preserve them
            
        Returns:
            True if deleted successfully
            
        Raises:
            ValueError: If merge target is invalid or tag is system tag
        """
        
        try:
            tag_model = self.db_session.get(TagModel, tag_id)
            if not tag_model:
                return False
            
            # Check if tag is system tag (protected from deletion)
            if tag_model.is_system_tag:
                raise ValueError("System tags cannot be deleted")
            
            # Handle merging if merge_to is specified
            if merge_to:
                merge_target = self.db_session.get(TagModel, merge_to)
                if not merge_target:
                    raise ValueError(f"Merge target tag with ID {merge_to} not found")
                
                if merge_target.channel_id != tag_model.channel_id:
                    raise ValueError("Cannot merge tags from different channels")
                
                # Transfer all episode associations to merge target
                self.db_session.execute(
                    text("""
                        UPDATE episode_tags 
                        SET tag_id = :merge_to 
                        WHERE tag_id = :tag_id
                        AND NOT EXISTS (
                            SELECT 1 FROM episode_tags et2 
                            WHERE et2.episode_id = episode_tags.episode_id 
                            AND et2.tag_id = :merge_to
                        )
                    """),
                    {"tag_id": tag_id, "merge_to": merge_to}
                )
                
                # Delete any remaining duplicate associations
                self.db_session.execute(
                    text("DELETE FROM episode_tags WHERE tag_id = :tag_id"),
                    {"tag_id": tag_id}
                )
                
                # Update merge target usage count
                new_usage_count = self.db_session.execute(
                    text("""
                        SELECT COUNT(*) FROM episode_tags WHERE tag_id = :merge_to
                    """),
                    {"merge_to": merge_to}
                ).scalar()
                
                merge_target.usage_count = new_usage_count
                merge_target.last_used_at = datetime.utcnow()
                
            elif delete_associations:
                # Delete all episode associations
                self.db_session.execute(
                    text("DELETE FROM episode_tags WHERE tag_id = :tag_id"),
                    {"tag_id": tag_id}
                )
            
            # Delete the tag
            self.db_session.delete(tag_model)
            self.db_session.commit()
            
            logger.info(f"Deleted tag ID {tag_id}")
            return True
            
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error(f"Database error deleting tag: {e}")
            raise
    
    async def get_tag_suggestions(
        self,
        query: str,
        channel_id: int,
        limit: int = 10,
        exclude_ids: Optional[List[int]] = None
    ) -> List[TagSuggestion]:
        """
        Get tag suggestions for autocomplete with fuzzy matching
        
        Args:
            query: Partial tag name query
            channel_id: Channel ID to search within
            limit: Maximum number of suggestions
            exclude_ids: Optional list of tag IDs to exclude
            
        Returns:
            List of TagSuggestion objects sorted by relevance
        """
        
        if not query or len(query.strip()) < 1:
            return []
        
        try:
            query_lower = query.strip().lower()
            
            # Build base query
            sql_query = """
            SELECT t.id, t.name, t.color, t.usage_count,
                   CASE 
                       WHEN LOWER(t.name) = :exact_query THEN 100
                       WHEN LOWER(t.name) LIKE :starts_with THEN 80
                       WHEN LOWER(t.name) LIKE :contains THEN 60
                       ELSE 40
                   END as match_score
            FROM tags t
            WHERE t.channel_id = :channel_id
            AND (
                LOWER(t.name) LIKE :contains
                OR LOWER(t.name) LIKE :starts_with
            )
            """
            
            params = {
                "channel_id": channel_id,
                "exact_query": query_lower,
                "starts_with": f"{query_lower}%",
                "contains": f"%{query_lower}%"
            }
            
            # Add exclusion filter if provided
            if exclude_ids:
                placeholders = ",".join([f":exclude_{i}" for i in range(len(exclude_ids))])
                sql_query += f" AND t.id NOT IN ({placeholders})"
                
                for i, exclude_id in enumerate(exclude_ids):
                    params[f"exclude_{i}"] = exclude_id
            
            # Add ordering and limit
            sql_query += """
            ORDER BY match_score DESC, t.usage_count DESC, t.name ASC
            LIMIT :limit
            """
            params["limit"] = limit
            
            # Execute query
            result = self.db_session.execute(text(sql_query), params).fetchall()
            
            suggestions = []
            for row in result:
                suggestions.append(TagSuggestion(
                    tag_id=row[0],
                    name=row[1],
                    color=row[2],
                    usage_count=row[3],
                    match_score=row[4] / 100.0  # Normalize to 0-1 range
                ))
            
            return suggestions
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting tag suggestions: {e}")
            return []
    
    async def get_tag_statistics(self, channel_id: int) -> Dict[str, Any]:
        """
        Get comprehensive tag statistics for a channel
        
        Args:
            channel_id: Channel ID
            
        Returns:
            Dictionary with tag statistics
        """
        
        try:
            # Get basic counts
            total_tags = self.db_session.query(TagModel).filter(
                TagModel.channel_id == channel_id
            ).count()
            
            used_tags = self.db_session.query(TagModel).filter(
                TagModel.channel_id == channel_id,
                TagModel.usage_count > 0
            ).count()
            
            # Get most used tags
            most_used = self.db_session.query(TagModel).filter(
                TagModel.channel_id == channel_id
            ).order_by(TagModel.usage_count.desc()).limit(5).all()
            
            # Get recently used tags
            recently_used = self.db_session.query(TagModel).filter(
                TagModel.channel_id == channel_id,
                TagModel.last_used_at.isnot(None)
            ).order_by(TagModel.last_used_at.desc()).limit(5).all()
            
            return {
                "total_tags": total_tags,
                "used_tags": used_tags,
                "unused_tags": total_tags - used_tags,
                "most_used": [
                    {
                        "id": tag.id,
                        "name": tag.name,
                        "color": tag.color,
                        "usage_count": tag.usage_count
                    }
                    for tag in most_used
                ],
                "recently_used": [
                    {
                        "id": tag.id,
                        "name": tag.name,
                        "color": tag.color,
                        "last_used_at": tag.last_used_at
                    }
                    for tag in recently_used
                ]
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting tag statistics: {e}")
            return {
                "total_tags": 0,
                "used_tags": 0,
                "unused_tags": 0,
                "most_used": [],
                "recently_used": []
            }
    
    def _model_to_entity(self, tag_model: TagModel) -> Tag:
        """Convert TagModel to Tag entity"""
        return Tag(
            id=tag_model.id,
            channel_id=tag_model.channel_id,
            name=tag_model.name,
            color=tag_model.color,
            usage_count=tag_model.usage_count,
            last_used_at=tag_model.last_used_at,
            is_system_tag=tag_model.is_system_tag,
            created_at=tag_model.created_at,
            updated_at=tag_model.updated_at
        )
    
    def _is_valid_hex_color(self, color: str) -> bool:
        """Validate hex color format"""
        if not color:
            return False
        
        # Check if it matches hex color pattern
        pattern = r'^#[0-9A-Fa-f]{6}$'
        return bool(re.match(pattern, color))