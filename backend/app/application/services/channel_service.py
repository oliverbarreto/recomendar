"""
Channel Application Service
Handles channel management and RSS feed settings
"""
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.domain.entities.channel import Channel
from app.domain.entities.episode import Episode
from app.domain.repositories.channel_repository import ChannelRepositoryInterface
from app.domain.repositories.episode_repository import EpisodeRepositoryInterface
from app.domain.services.feed_generation_service import FeedGenerationServiceInterface
from app.infrastructure.services.itunes_validator import iTunesValidator
from app.core.logging import get_structured_logger

logger = get_structured_logger("channel_service")


class ChannelService:
    """
    Application service for channel management and RSS feed operations
    """
    
    def __init__(
        self,
        channel_repository: ChannelRepositoryInterface,
        episode_repository: EpisodeRepositoryInterface,
        feed_generation_service: FeedGenerationServiceInterface
    ):
        self.channel_repository = channel_repository
        self.episode_repository = episode_repository
        self.feed_generation_service = feed_generation_service
        self.validator = iTunesValidator()
    
    async def create_channel(
        self,
        user_id: int,
        name: str,
        description: str,
        author_name: str = "",
        author_email: Optional[str] = None
    ) -> Channel:
        """
        Create a new podcast channel
        """
        channel = Channel.create_channel(
            user_id=user_id,
            name=name,
            description=description,
            author_name=author_name,
            author_email=author_email
        )
        
        created_channel = await self.channel_repository.create(channel)
        return created_channel
    
    async def get_channel(self, channel_id: int) -> Optional[Channel]:
        """
        Get channel by ID
        """
        return await self.channel_repository.get_by_id(channel_id)
    
    async def get_channels_by_user(self, user_id: int) -> List[Channel]:
        """
        Get all channels for a user
        """
        return await self.channel_repository.get_by_user_id(user_id)
    
    async def update_channel_settings(
        self,
        channel_id: int,
        settings: Dict[str, Any]
    ) -> Optional[Channel]:
        """
        Update channel settings and RSS feed configuration
        """
        channel = await self.channel_repository.get_by_id(channel_id)
        if not channel:
            return None
        
        # Update channel settings using the domain entity method
        channel.update_settings(
            name=settings.get('name'),
            description=settings.get('description'),
            website_url=settings.get('website_url'),
            image_url=settings.get('image_url'),
            category=settings.get('category'),
            language=settings.get('language'),
            explicit_content=settings.get('explicit_content'),
            author_name=settings.get('author_name'),
            author_email=settings.get('author_email'),
            owner_name=settings.get('owner_name'),
            owner_email=settings.get('owner_email')
        )
        
        # Update additional RSS feed settings
        if 'copyright' in settings:
            channel.copyright = settings['copyright']
        
        if 'podcast_type' in settings and settings['podcast_type'] in ['episodic', 'serial']:
            channel.podcast_type = settings['podcast_type']
        
        if 'subcategory' in settings:
            channel.subcategory = settings['subcategory']
        
        # Save updated channel
        updated_channel = await self.channel_repository.update(channel)
        
        # Regenerate and validate feed if channel has episodes
        if updated_channel:
            await self._update_feed_validation(updated_channel)
        
        return updated_channel
    
    async def update_feed_url(self, channel_id: int, domain: str) -> Optional[Channel]:
        """
        Update the RSS feed URL for a channel
        """
        channel = await self.channel_repository.get_by_id(channel_id)
        if not channel:
            return None
        
        channel.update_feed_url(domain)
        return await self.channel_repository.update(channel)
    
    async def generate_feed(self, channel_id: int, base_url: str) -> Optional[str]:
        """
        Generate RSS feed for a channel
        """
        channel = await self.channel_repository.get_by_id(channel_id)
        if not channel:
            return None
        
        # Get published episodes for the channel
        episodes = await self.episode_repository.get_published_by_channel_id(channel_id)
        
        # Generate RSS feed
        feed_xml = self.feed_generation_service.generate_rss_feed(
            channel, episodes, base_url
        )
        
        # Update feed last updated timestamp
        channel.feed_last_updated = datetime.utcnow()
        await self.channel_repository.update(channel)
        
        return feed_xml
    
    async def validate_feed(self, channel_id: int, base_url: str) -> Optional[Dict[str, Any]]:
        """
        Validate channel RSS feed against iTunes specifications
        """
        channel = await self.channel_repository.get_by_id(channel_id)
        if not channel:
            return None
        
        # Get published episodes
        episodes = await self.episode_repository.get_published_by_channel_id(channel_id)
        
        # Generate feed XML
        feed_xml = self.feed_generation_service.generate_rss_feed(
            channel, episodes, base_url
        )
        
        # Validate feed
        validation_result = self.validator.validate_full_feed(feed_xml)
        
        # Update validation score
        channel.feed_validation_score = validation_result['score']
        await self.channel_repository.update(channel)
        
        return validation_result
    
    async def get_feed_score(self, channel_id: int) -> Optional[float]:
        """
        Calculate and return feed quality score
        """
        channel = await self.channel_repository.get_by_id(channel_id)
        if not channel:
            return None
        
        episodes = await self.episode_repository.get_published_by_channel_id(channel_id)
        
        score = self.feed_generation_service.calculate_feed_score(channel, episodes)
        
        # Update score in database
        channel.feed_validation_score = score
        await self.channel_repository.update(channel)
        
        return score
    
    async def get_channel_statistics(self, channel_id: int) -> Optional[Dict[str, Any]]:
        """
        Get channel statistics and RSS feed information
        """
        channel = await self.channel_repository.get_by_id(channel_id)
        if not channel:
            return None
        
        # Get all episodes for the channel
        all_episodes = await self.episode_repository.get_by_channel_id(channel_id)
        published_episodes = [ep for ep in all_episodes if ep.status == "published"]
        
        # Calculate statistics
        total_duration = sum(ep.duration or 0 for ep in published_episodes)
        total_size = sum(ep.file_size or 0 for ep in published_episodes)
        
        # Get latest episode
        latest_episode = None
        if published_episodes:
            latest_episode = max(published_episodes, key=lambda ep: ep.publication_date or ep.created_at)
        
        return {
            'channel_id': channel_id,
            'channel_name': channel.name,
            'total_episodes': len(all_episodes),
            'published_episodes': len(published_episodes),
            'draft_episodes': len([ep for ep in all_episodes if ep.status == "draft"]),
            'processing_episodes': len([ep for ep in all_episodes if ep.status == "processing"]),
            'total_duration_seconds': total_duration,
            'total_size_bytes': total_size,
            'feed_validation_score': channel.feed_validation_score,
            'feed_last_updated': channel.feed_last_updated,
            'latest_episode': {
                'title': latest_episode.title,
                'publication_date': latest_episode.publication_date,
                'duration': latest_episode.duration
            } if latest_episode else None,
            'created_at': channel.created_at,
            'updated_at': channel.updated_at
        }
    
    async def delete_channel(self, channel_id: int) -> bool:
        """
        Delete a channel and all its episodes
        """
        channel = await self.channel_repository.get_by_id(channel_id)
        if not channel:
            return False
        
        # Delete all episodes first
        episodes = await self.episode_repository.get_by_channel_id(channel_id)
        for episode in episodes:
            await self.episode_repository.delete(episode.id)
        
        # Delete the channel
        return await self.channel_repository.delete(channel_id)
    
    async def _update_feed_validation(self, channel: Channel) -> None:
        """
        Update feed validation score after channel changes
        """
        try:
            episodes = await self.episode_repository.get_published_by_channel_id(channel.id)
            score = self.feed_generation_service.calculate_feed_score(channel, episodes)
            channel.feed_validation_score = score
            await self.channel_repository.update(channel)
        except Exception as e:
            # Log error but don't fail the main operation
            logger.warning(
                "Error updating feed validation score",
                channel_id=channel.id,
                error_type=type(e).__name__,
                error_message=str(e),
                exc_info=True
            )
    
    async def get_all_channels(self) -> List[Channel]:
        """
        Get all channels (admin function)
        """
        return await self.channel_repository.get_all()
    
    async def search_channels(self, query: str, limit: int = 10) -> List[Channel]:
        """
        Search channels by name or description
        """
        # This would be implemented in the repository layer
        # For now, get all and filter (not efficient for large datasets)
        all_channels = await self.channel_repository.get_all()
        query_lower = query.lower()
        
        matching_channels = []
        for channel in all_channels:
            if (query_lower in channel.name.lower() or 
                query_lower in (channel.description or "").lower()):
                matching_channels.append(channel)
                if len(matching_channels) >= limit:
                    break
        
        return matching_channels