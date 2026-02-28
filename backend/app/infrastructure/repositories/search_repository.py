"""
SearchRepository implementation using SQLite FTS5
"""
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_
from sqlalchemy.exc import SQLAlchemyError

from app.domain.repositories.search_repository import (
    SearchRepository, SearchFilters, SearchResult, SearchResponse, FilterOptions
)
from app.domain.entities.episode import Episode
from app.infrastructure.database.models.episode import EpisodeModel
from app.infrastructure.database.models.tag import TagModel, episode_tags
from app.infrastructure.database.models.channel import ChannelModel

logger = logging.getLogger(__name__)


class SearchRepositoryImpl(SearchRepository):
    """SQLite FTS5 implementation of SearchRepository"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
    
    async def search_episodes(
        self,
        channel_id: int,
        filters: SearchFilters,
        page: int = 1,
        limit: int = 20
    ) -> SearchResponse:
        """Search episodes using FTS5 and advanced filtering"""
        start_time = time.time()
        
        try:
            # Build base query
            if filters.query:
                # Use FTS5 for full-text search
                results, total_count = await self._search_with_fts5(
                    channel_id, filters, page, limit
                )
            else:
                # Use regular filtering without full-text search
                results, total_count = await self._search_with_filters(
                    channel_id, filters, page, limit
                )
            
            # Convert to SearchResult objects with highlights
            search_results = []
            for episode_model, relevance_score in results:
                episode = self._model_to_entity(episode_model)
                highlights = self._generate_highlights(episode_model, filters.query) if filters.query else {}
                
                search_results.append(SearchResult(
                    episode=episode,
                    relevance_score=relevance_score,
                    highlights=highlights
                ))
            
            execution_time = time.time() - start_time
            
            return SearchResponse(
                results=search_results,
                total_count=total_count,
                page=page,
                per_page=limit,
                execution_time=execution_time,
                filters_applied={
                    'query': filters.query,
                    'tags': filters.tags,
                    'status': filters.status,
                    'date_range': {
                        'from': filters.date_from.isoformat() if filters.date_from else None,
                        'to': filters.date_to.isoformat() if filters.date_to else None
                    },
                    'duration_range': {
                        'min': filters.duration_min,
                        'max': filters.duration_max
                    },
                    'sort_by': filters.sort_by,
                    'sort_order': filters.sort_order
                }
            )
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in search_episodes: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in search_episodes: {e}")
            raise
    
    async def _search_with_fts5(
        self,
        channel_id: int,
        filters: SearchFilters,
        page: int,
        limit: int
    ) -> Tuple[List[Tuple[EpisodeModel, float]], int]:
        """Search using FTS5 full-text search"""
        
        # Sanitize search query for FTS5
        fts_query = self._sanitize_fts5_query(filters.query)
        
        # Build FTS5 query with JOIN to episodes table for filtering
        base_query = """
        SELECT e.*, 
               es.rank,
               snippet(episode_search, 1, '<mark>', '</mark>', '...', 32) as title_snippet,
               snippet(episode_search, 2, '<mark>', '</mark>', '...', 64) as description_snippet
        FROM episode_search es
        JOIN episodes e ON e.id = es.episode_id
        WHERE es.title MATCH ? AND e.channel_id = ?
        """
        
        # Add additional filters
        conditions = []
        params = [fts_query, channel_id]
        
        if filters.status:
            conditions.append("e.status = ?")
            params.append(filters.status)
        
        if filters.date_from:
            conditions.append("e.publication_date >= ?")
            params.append(filters.date_from)
            
        if filters.date_to:
            conditions.append("e.publication_date <= ?")
            params.append(filters.date_to)
            
        if filters.duration_min:
            conditions.append("e.duration >= ?")
            params.append(filters.duration_min)
            
        if filters.duration_max:
            conditions.append("e.duration <= ?")
            params.append(filters.duration_max)
        
        # Add tag filtering if specified
        if filters.tags:
            tag_placeholders = ",".join(["?"] * len(filters.tags))
            conditions.append(f"""
                e.id IN (
                    SELECT DISTINCT et.episode_id 
                    FROM episode_tags et 
                    JOIN tags t ON t.id = et.tag_id 
                    WHERE t.name IN ({tag_placeholders})
                )
            """)
            params.extend(filters.tags)
        
        # Add conditions to query
        if conditions:
            base_query += " AND " + " AND ".join(conditions)
        
        # Add sorting
        if filters.sort_by == "relevance":
            base_query += " ORDER BY es.rank"
        elif filters.sort_by == "date":
            base_query += " ORDER BY e.publication_date"
        elif filters.sort_by == "title":
            base_query += " ORDER BY e.title"
        elif filters.sort_by == "duration":
            base_query += " ORDER BY e.duration"
        
        # Add sort direction
        if filters.sort_order.lower() == "desc":
            base_query += " DESC"
        else:
            base_query += " ASC"
        
        # Get total count first
        count_query = f"""
        SELECT COUNT(*) 
        FROM ({base_query}) subquery
        """
        
        try:
            # Execute count query
            count_result = self.db_session.execute(text(count_query), params).scalar()
            total_count = count_result or 0
            
            # Add pagination
            offset = (page - 1) * limit
            base_query += f" LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            # Execute main query
            result = self.db_session.execute(text(base_query), params).fetchall()
            
            # Convert to episode models with relevance scores
            episodes = []
            for row in result:
                # Create EpisodeModel from row data
                episode_model = self.db_session.get(EpisodeModel, row[0])  # row[0] should be episode id
                relevance_score = float(row[1]) if row[1] else 0.0  # FTS5 rank
                episodes.append((episode_model, relevance_score))
            
            return episodes, total_count
            
        except Exception as e:
            logger.error(f"FTS5 search error: {e}")
            # Fallback to regular search if FTS5 fails
            return await self._search_with_filters(channel_id, filters, page, limit)
    
    async def _search_with_filters(
        self,
        channel_id: int,
        filters: SearchFilters,
        page: int,
        limit: int
    ) -> Tuple[List[Tuple[EpisodeModel, float]], int]:
        """Search using regular SQL filters without FTS5"""
        
        query = self.db_session.query(EpisodeModel).filter(
            EpisodeModel.channel_id == channel_id
        )
        
        # Apply text search if query provided (fallback using LIKE)
        if filters.query:
            search_term = f"%{filters.query}%"
            query = query.filter(
                or_(
                    EpisodeModel.title.ilike(search_term),
                    EpisodeModel.description.ilike(search_term)
                )
            )
        
        # Apply other filters
        if filters.status:
            query = query.filter(EpisodeModel.status == filters.status)
            
        if filters.date_from:
            query = query.filter(EpisodeModel.publication_date >= filters.date_from)
            
        if filters.date_to:
            query = query.filter(EpisodeModel.publication_date <= filters.date_to)
            
        if filters.duration_min:
            query = query.filter(EpisodeModel.duration >= filters.duration_min)
            
        if filters.duration_max:
            query = query.filter(EpisodeModel.duration <= filters.duration_max)
        
        # Add tag filtering
        if filters.tags:
            query = query.join(episode_tags).join(TagModel).filter(
                TagModel.name.in_(filters.tags)
            ).distinct()
        
        # Get total count
        total_count = query.count()
        
        # Apply sorting
        if filters.sort_by == "date":
            sort_column = EpisodeModel.publication_date
        elif filters.sort_by == "title":
            sort_column = EpisodeModel.title
        elif filters.sort_by == "duration":
            sort_column = EpisodeModel.duration
        else:  # default to date for non-FTS searches
            sort_column = EpisodeModel.publication_date
        
        if filters.sort_order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Apply pagination
        offset = (page - 1) * limit
        episodes = query.offset(offset).limit(limit).all()
        
        # Return with default relevance score of 0.5
        return [(episode, 0.5) for episode in episodes], total_count
    
    def _sanitize_fts5_query(self, query: str) -> str:
        """Sanitize query string for FTS5 to prevent syntax errors"""
        if not query:
            return ""
        
        # Remove FTS5 special characters that could cause syntax errors
        # Keep basic operators but escape problematic ones
        sanitized = query.replace('"', '""')  # Escape quotes
        
        # If query contains only special chars or is too short, wrap in quotes
        if len(sanitized.strip()) < 2 or not sanitized.strip().isalnum():
            return f'"{sanitized}"'
            
        return sanitized
    
    def _generate_highlights(self, episode_model: EpisodeModel, query: str) -> Dict[str, List[str]]:
        """Generate highlighted snippets for search results"""
        highlights = {}
        
        if not query:
            return highlights
        
        query_lower = query.lower()
        
        # Highlight title
        if episode_model.title and query_lower in episode_model.title.lower():
            highlighted_title = episode_model.title.replace(
                query, f"<mark>{query}</mark>"
            )
            highlights["title"] = [highlighted_title]
        
        # Highlight description snippets
        if episode_model.description and query_lower in episode_model.description.lower():
            # Find snippet around the match
            desc_lower = episode_model.description.lower()
            match_index = desc_lower.find(query_lower)
            
            if match_index >= 0:
                start = max(0, match_index - 50)
                end = min(len(episode_model.description), match_index + len(query) + 50)
                snippet = episode_model.description[start:end]
                
                # Highlight the match in the snippet
                highlighted_snippet = snippet.replace(
                    query, f"<mark>{query}</mark>"
                )
                
                if start > 0:
                    highlighted_snippet = "..." + highlighted_snippet
                if end < len(episode_model.description):
                    highlighted_snippet = highlighted_snippet + "..."
                
                highlights["description"] = [highlighted_snippet]
        
        return highlights
    
    async def get_filter_options(self, channel_id: int) -> FilterOptions:
        """Get available filter options for the search interface"""
        
        try:
            # Get available tags with episode counts
            tag_query = """
            SELECT t.id, t.name, t.color, COUNT(et.episode_id) as episode_count
            FROM tags t
            LEFT JOIN episode_tags et ON t.id = et.tag_id
            LEFT JOIN episodes e ON et.episode_id = e.id
            WHERE t.channel_id = ? AND (e.channel_id = ? OR e.channel_id IS NULL)
            GROUP BY t.id, t.name, t.color
            ORDER BY episode_count DESC, t.name
            """
            
            tag_result = self.db_session.execute(text(tag_query), [channel_id, channel_id]).fetchall()
            available_tags = [
                {
                    "id": row[0],
                    "name": row[1],
                    "color": row[2],
                    "episode_count": row[3]
                }
                for row in tag_result
            ]
            
            # Get status options from episodes
            status_query = """
            SELECT DISTINCT status 
            FROM episodes 
            WHERE channel_id = ? AND status IS NOT NULL
            ORDER BY status
            """
            status_result = self.db_session.execute(text(status_query), [channel_id]).fetchall()
            status_options = [row[0] for row in status_result]
            
            # Get duration range
            duration_query = """
            SELECT MIN(duration) as min_duration, MAX(duration) as max_duration
            FROM episodes 
            WHERE channel_id = ? AND duration IS NOT NULL
            """
            duration_result = self.db_session.execute(text(duration_query), [channel_id]).fetchone()
            duration_range = {
                "min": int(duration_result[0]) if duration_result[0] else 0,
                "max": int(duration_result[1]) if duration_result[1] else 0
            }
            
            # Get date range
            date_query = """
            SELECT MIN(publication_date) as earliest, MAX(publication_date) as latest
            FROM episodes 
            WHERE channel_id = ? AND publication_date IS NOT NULL
            """
            date_result = self.db_session.execute(text(date_query), [channel_id]).fetchone()
            date_range = {
                "earliest": date_result[0] if date_result[0] else None,
                "latest": date_result[1] if date_result[1] else None
            }
            
            return FilterOptions(
                available_tags=available_tags,
                status_options=status_options,
                duration_range=duration_range,
                date_range=date_range
            )
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_filter_options: {e}")
            raise
    
    async def rebuild_search_index(self, channel_id: Optional[int] = None) -> bool:
        """Rebuild the FTS5 search index"""
        
        try:
            if channel_id:
                # Rebuild index for specific channel
                rebuild_query = """
                INSERT INTO episode_search(episode_search) VALUES('rebuild');
                """
            else:
                # Full rebuild
                rebuild_query = """
                INSERT INTO episode_search(episode_search) VALUES('rebuild');
                """
            
            self.db_session.execute(text(rebuild_query))
            self.db_session.commit()
            
            logger.info(f"Successfully rebuilt search index for channel_id: {channel_id}")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to rebuild search index: {e}")
            self.db_session.rollback()
            return False
    
    def _model_to_entity(self, episode_model: EpisodeModel) -> Episode:
        """Convert EpisodeModel to Episode entity"""
        return Episode(
            id=episode_model.id,
            channel_id=episode_model.channel_id,
            title=episode_model.title,
            description=episode_model.description,
            youtube_video_id=episode_model.youtube_video_id,
            youtube_url=episode_model.youtube_url,
            media_file_path=episode_model.media_file_path,
            duration=episode_model.duration,
            file_size=episode_model.file_size,
            status=episode_model.status,
            episode_number=episode_model.episode_number,
            season_number=episode_model.season_number,
            publication_date=episode_model.publication_date,
            created_at=episode_model.created_at,
            updated_at=episode_model.updated_at
        )