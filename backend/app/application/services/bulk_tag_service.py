"""
Bulk Tag Service for batch operations on tags and episode-tag associations
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text, and_
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.infrastructure.database.models.tag import TagModel, episode_tags
from app.infrastructure.database.models.episode import EpisodeModel

logger = logging.getLogger(__name__)


class BulkOperationResult:
    """Result of bulk tag operation"""
    def __init__(
        self,
        success: bool,
        processed_count: int = 0,
        failed_count: int = 0,
        errors: List[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.success = success
        self.processed_count = processed_count
        self.failed_count = failed_count
        self.errors = errors or []
        self.details = details or {}


class BulkTagService:
    """Service for bulk tag operations"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
    
    async def assign_tags_to_episodes(
        self,
        episode_ids: List[int],
        tag_ids: List[int],
        channel_id: Optional[int] = None
    ) -> BulkOperationResult:
        """
        Assign multiple tags to multiple episodes in bulk
        
        Args:
            episode_ids: List of episode IDs
            tag_ids: List of tag IDs to assign
            channel_id: Optional channel ID for additional validation
            
        Returns:
            BulkOperationResult with operation details
        """
        
        if not episode_ids or not tag_ids:
            return BulkOperationResult(
                success=False,
                errors=["Episode IDs and Tag IDs cannot be empty"]
            )
        
        processed_count = 0
        failed_count = 0
        errors = []
        
        try:
            # Validate that all episodes exist and belong to the same channel if specified
            if channel_id:
                episode_query = self.db_session.query(EpisodeModel).filter(
                    EpisodeModel.id.in_(episode_ids),
                    EpisodeModel.channel_id == channel_id
                )
            else:
                episode_query = self.db_session.query(EpisodeModel).filter(
                    EpisodeModel.id.in_(episode_ids)
                )
            
            valid_episodes = episode_query.all()
            valid_episode_ids = [ep.id for ep in valid_episodes]
            
            if len(valid_episode_ids) != len(episode_ids):
                invalid_ids = set(episode_ids) - set(valid_episode_ids)
                errors.append(f"Invalid episode IDs: {list(invalid_ids)}")
            
            # Validate that all tags exist
            valid_tags = self.db_session.query(TagModel).filter(
                TagModel.id.in_(tag_ids)
            ).all()
            valid_tag_ids = [tag.id for tag in valid_tags]
            
            if len(valid_tag_ids) != len(tag_ids):
                invalid_ids = set(tag_ids) - set(valid_tag_ids)
                errors.append(f"Invalid tag IDs: {list(invalid_ids)}")
            
            if not valid_episode_ids or not valid_tag_ids:
                return BulkOperationResult(
                    success=False,
                    failed_count=len(episode_ids) * len(tag_ids),
                    errors=errors
                )
            
            # Create tag assignments in bulk, avoiding duplicates
            assignment_data = []
            for episode_id in valid_episode_ids:
                for tag_id in valid_tag_ids:
                    assignment_data.append({
                        'episode_id': episode_id,
                        'tag_id': tag_id,
                        'created_at': datetime.utcnow()
                    })
            
            if assignment_data:
                # Use INSERT OR IGNORE to handle duplicates gracefully
                insert_query = """
                INSERT OR IGNORE INTO episode_tags (episode_id, tag_id, created_at)
                VALUES (:episode_id, :tag_id, :created_at)
                """
                
                result = self.db_session.execute(text(insert_query), assignment_data)
                processed_count = result.rowcount
                
                # Update tag usage counts
                for tag_id in valid_tag_ids:
                    usage_count_query = """
                    UPDATE tags 
                    SET usage_count = (
                        SELECT COUNT(*) FROM episode_tags WHERE tag_id = :tag_id
                    ),
                    last_used_at = :now
                    WHERE id = :tag_id
                    """
                    self.db_session.execute(text(usage_count_query), {
                        'tag_id': tag_id,
                        'now': datetime.utcnow()
                    })
            
            self.db_session.commit()
            
            logger.info(f"Bulk assigned {processed_count} tag-episode associations")
            
            return BulkOperationResult(
                success=True,
                processed_count=processed_count,
                failed_count=len(assignment_data) - processed_count,
                errors=errors,
                details={
                    'valid_episodes': len(valid_episode_ids),
                    'valid_tags': len(valid_tag_ids),
                    'total_attempted': len(assignment_data)
                }
            )
            
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error(f"Database error in bulk assign tags: {e}")
            return BulkOperationResult(
                success=False,
                failed_count=len(episode_ids) * len(tag_ids),
                errors=[f"Database error: {str(e)}"]
            )
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Unexpected error in bulk assign tags: {e}")
            return BulkOperationResult(
                success=False,
                failed_count=len(episode_ids) * len(tag_ids),
                errors=[f"Unexpected error: {str(e)}"]
            )
    
    async def remove_tags_from_episodes(
        self,
        episode_ids: List[int],
        tag_ids: List[int],
        channel_id: Optional[int] = None
    ) -> BulkOperationResult:
        """
        Remove multiple tags from multiple episodes in bulk
        
        Args:
            episode_ids: List of episode IDs
            tag_ids: List of tag IDs to remove
            channel_id: Optional channel ID for additional validation
            
        Returns:
            BulkOperationResult with operation details
        """
        
        if not episode_ids or not tag_ids:
            return BulkOperationResult(
                success=False,
                errors=["Episode IDs and Tag IDs cannot be empty"]
            )
        
        try:
            # Validate episodes if channel_id is provided
            if channel_id:
                valid_episode_count = self.db_session.query(EpisodeModel).filter(
                    EpisodeModel.id.in_(episode_ids),
                    EpisodeModel.channel_id == channel_id
                ).count()
                
                if valid_episode_count != len(episode_ids):
                    return BulkOperationResult(
                        success=False,
                        errors=["Some episodes do not exist or don't belong to the specified channel"]
                    )
            
            # Remove tag associations
            delete_query = """
            DELETE FROM episode_tags 
            WHERE episode_id IN ({episode_placeholders}) 
            AND tag_id IN ({tag_placeholders})
            """.format(
                episode_placeholders=','.join([':ep_' + str(i) for i in range(len(episode_ids))]),
                tag_placeholders=','.join([':tag_' + str(i) for i in range(len(tag_ids))])
            )
            
            # Build parameters
            params = {}
            for i, episode_id in enumerate(episode_ids):
                params[f'ep_{i}'] = episode_id
            for i, tag_id in enumerate(tag_ids):
                params[f'tag_{i}'] = tag_id
            
            result = self.db_session.execute(text(delete_query), params)
            processed_count = result.rowcount
            
            # Update tag usage counts
            for tag_id in tag_ids:
                usage_count_query = """
                UPDATE tags 
                SET usage_count = (
                    SELECT COUNT(*) FROM episode_tags WHERE tag_id = :tag_id
                )
                WHERE id = :tag_id
                """
                self.db_session.execute(text(usage_count_query), {'tag_id': tag_id})
            
            self.db_session.commit()
            
            logger.info(f"Bulk removed {processed_count} tag-episode associations")
            
            return BulkOperationResult(
                success=True,
                processed_count=processed_count,
                details={
                    'episodes_count': len(episode_ids),
                    'tags_count': len(tag_ids)
                }
            )
            
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error(f"Database error in bulk remove tags: {e}")
            return BulkOperationResult(
                success=False,
                failed_count=len(episode_ids) * len(tag_ids),
                errors=[f"Database error: {str(e)}"]
            )
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Unexpected error in bulk remove tags: {e}")
            return BulkOperationResult(
                success=False,
                failed_count=len(episode_ids) * len(tag_ids),
                errors=[f"Unexpected error: {str(e)}"]
            )
    
    async def replace_tags_on_episodes(
        self,
        episode_ids: List[int],
        old_tag_ids: List[int],
        new_tag_ids: List[int],
        channel_id: Optional[int] = None
    ) -> BulkOperationResult:
        """
        Replace old tags with new tags on multiple episodes
        
        Args:
            episode_ids: List of episode IDs
            old_tag_ids: List of tag IDs to remove
            new_tag_ids: List of tag IDs to add
            channel_id: Optional channel ID for validation
            
        Returns:
            BulkOperationResult with operation details
        """
        
        try:
            # First remove old tags
            remove_result = await self.remove_tags_from_episodes(
                episode_ids, old_tag_ids, channel_id
            )
            
            if not remove_result.success:
                return remove_result
            
            # Then add new tags
            add_result = await self.assign_tags_to_episodes(
                episode_ids, new_tag_ids, channel_id
            )
            
            return BulkOperationResult(
                success=add_result.success,
                processed_count=remove_result.processed_count + add_result.processed_count,
                failed_count=add_result.failed_count,
                errors=add_result.errors,
                details={
                    'removed_associations': remove_result.processed_count,
                    'added_associations': add_result.processed_count,
                    'episodes_count': len(episode_ids)
                }
            )
            
        except Exception as e:
            logger.error(f"Error in replace tags operation: {e}")
            return BulkOperationResult(
                success=False,
                errors=[f"Replace operation failed: {str(e)}"]
            )
    
    async def copy_tags_between_episodes(
        self,
        source_episode_id: int,
        target_episode_ids: List[int],
        channel_id: Optional[int] = None
    ) -> BulkOperationResult:
        """
        Copy all tags from source episode to target episodes
        
        Args:
            source_episode_id: Episode ID to copy tags from
            target_episode_ids: List of episode IDs to copy tags to
            channel_id: Optional channel ID for validation
            
        Returns:
            BulkOperationResult with operation details
        """
        
        try:
            # Get tags from source episode
            source_tags_query = """
            SELECT DISTINCT tag_id FROM episode_tags 
            WHERE episode_id = :source_id
            """
            
            result = self.db_session.execute(
                text(source_tags_query), 
                {'source_id': source_episode_id}
            ).fetchall()
            
            tag_ids = [row[0] for row in result]
            
            if not tag_ids:
                return BulkOperationResult(
                    success=True,
                    processed_count=0,
                    details={'message': 'Source episode has no tags to copy'}
                )
            
            # Copy tags to target episodes
            return await self.assign_tags_to_episodes(
                target_episode_ids, tag_ids, channel_id
            )
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in copy tags: {e}")
            return BulkOperationResult(
                success=False,
                errors=[f"Database error: {str(e)}"]
            )
    
    async def merge_tags(
        self,
        source_tag_ids: List[int],
        target_tag_id: int,
        channel_id: Optional[int] = None
    ) -> BulkOperationResult:
        """
        Merge multiple tags into a single target tag
        
        Args:
            source_tag_ids: List of tag IDs to merge (will be deleted)
            target_tag_id: Tag ID to merge into (will be kept)
            channel_id: Optional channel ID for validation
            
        Returns:
            BulkOperationResult with operation details
        """
        
        if target_tag_id in source_tag_ids:
            return BulkOperationResult(
                success=False,
                errors=["Target tag cannot be in the list of source tags to merge"]
            )
        
        try:
            # Validate that target tag exists
            target_tag = self.db_session.get(TagModel, target_tag_id)
            if not target_tag:
                return BulkOperationResult(
                    success=False,
                    errors=[f"Target tag with ID {target_tag_id} not found"]
                )
            
            if channel_id and target_tag.channel_id != channel_id:
                return BulkOperationResult(
                    success=False,
                    errors=["Target tag does not belong to the specified channel"]
                )
            
            merged_count = 0
            errors = []
            
            for source_tag_id in source_tag_ids:
                try:
                    # Transfer all episode associations to target tag
                    transfer_query = """
                    UPDATE episode_tags 
                    SET tag_id = :target_id 
                    WHERE tag_id = :source_id
                    AND NOT EXISTS (
                        SELECT 1 FROM episode_tags et2 
                        WHERE et2.episode_id = episode_tags.episode_id 
                        AND et2.tag_id = :target_id
                    )
                    """
                    
                    self.db_session.execute(text(transfer_query), {
                        'source_id': source_tag_id,
                        'target_id': target_tag_id
                    })
                    
                    # Delete remaining duplicate associations
                    self.db_session.execute(
                        text("DELETE FROM episode_tags WHERE tag_id = :source_id"),
                        {'source_id': source_tag_id}
                    )
                    
                    # Delete the source tag
                    source_tag = self.db_session.get(TagModel, source_tag_id)
                    if source_tag:
                        if not source_tag.is_system_tag:
                            self.db_session.delete(source_tag)
                            merged_count += 1
                        else:
                            errors.append(f"Cannot delete system tag with ID {source_tag_id}")
                    
                except Exception as e:
                    errors.append(f"Failed to merge tag {source_tag_id}: {str(e)}")
            
            # Update target tag usage count
            usage_count_query = """
            UPDATE tags 
            SET usage_count = (
                SELECT COUNT(*) FROM episode_tags WHERE tag_id = :tag_id
            ),
            last_used_at = :now
            WHERE id = :tag_id
            """
            
            self.db_session.execute(text(usage_count_query), {
                'tag_id': target_tag_id,
                'now': datetime.utcnow()
            })
            
            self.db_session.commit()
            
            logger.info(f"Successfully merged {merged_count} tags into tag {target_tag_id}")
            
            return BulkOperationResult(
                success=len(errors) == 0,
                processed_count=merged_count,
                failed_count=len(source_tag_ids) - merged_count,
                errors=errors,
                details={
                    'target_tag_id': target_tag_id,
                    'total_source_tags': len(source_tag_ids)
                }
            )
            
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error(f"Database error in merge tags: {e}")
            return BulkOperationResult(
                success=False,
                errors=[f"Database error: {str(e)}"]
            )