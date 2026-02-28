"""
RSS Feed Generation Service Implementation using PodGen
"""
from typing import List, Optional
from datetime import datetime, timedelta
import pytz
import re
from xml.etree import ElementTree as ET

from podgen import Podcast, Episode as PodgenEpisode, Media, Category, Person

from app.domain.entities.channel import Channel
from app.domain.entities.episode import Episode
from app.domain.entities.event import EventSeverity
from app.domain.services.feed_generation_service import FeedGenerationServiceInterface
from app.infrastructure.services.media_file_service import MediaFileService
from app.application.services.event_service import EventService
from app.core.logging import get_rss_logger, get_structured_logger

logger = get_rss_logger()
structured_logger = get_structured_logger("rss")


class PodcastWithNamespaces(Podcast):
    """
    Extended Podcast class that includes modern podcast namespaces
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add podcast namespace for modern podcast standards
        self._nsmap['podcast'] = 'https://podcastindex.org/namespace/1.0'



class FeedGenerationServiceImpl(FeedGenerationServiceInterface):
    """
    PodGen-based RSS feed generation service implementation with business event tracking
    """

    def __init__(self, event_service: Optional[EventService] = None, user_id: Optional[int] = None, channel_id: Optional[int] = None):
        self.event_service = event_service
        self.user_id = user_id
        self.channel_id = channel_id
    
    def generate_rss_feed(
        self,
        channel: Channel,
        episodes: List[Episode],
        base_url: str
    ) -> str:
        """
        Generate iTunes-compliant RSS feed with enhanced metadata and business event tracking
        """
        # Emit RSS generation started event
        self._emit_rss_generation_event("started", channel, episodes)

        try:
            # Store iTunes-compliant channel image URL for episode use
            self._channel_image_url = self._make_image_url_itunes_compliant(channel.image_url, base_url)

            # Generate feed URL for atom:link rel="self" element
            # Extract domain from base_url for consistency
            import re
            domain_match = re.match(r'https?://([^/]+)', base_url)
            domain = domain_match.group(1) if domain_match else base_url.replace('https://', '').replace('http://', '').split('/')[0]
            feed_url = f"{base_url}/v1/feeds/{channel.id}/feed.xml"

            # Create podcast object with enhanced settings and modern namespaces
            podcast = PodcastWithNamespaces(
                name=channel.name,
                description=channel.description,
                website=channel.website_url,  # Now required
                language=channel.language,
                explicit=bool(channel.explicit_content),  # Convert to boolean for iTunes compliance
                category=self._get_category(channel.category, channel.subcategory),
                authors=[Person(
                    name=channel.author_name or channel.owner_name,
                    email=str(channel.owner_email) if channel.owner_email else None
                )],
                owner=Person(
                    name=channel.owner_name or channel.author_name,
                    email=str(channel.owner_email) if channel.owner_email else None
                ),
                feed_url=feed_url  # This triggers atom:link rel="self" generation
            )

            # Set iTunes-specific fields with compliant image URL
            if channel.image_url:
                itunes_image_url = self._make_image_url_itunes_compliant(channel.image_url, base_url)
                podcast.image = itunes_image_url

            if channel.copyright:
                podcast.copyright = channel.copyright

            # Set iTunes summary and subtitle (same as description)
            podcast.summary = channel.description
            podcast.subtitle = channel.description

            # Set podcast type
            podcast.podcast_type = channel.podcast_type

            # Add episodes with enhanced metadata
            for ep in episodes:
                if ep.status.value == "completed" and ep.audio_file_path:
                    podcast_episode = self._create_episode(ep, base_url, episodes, channel)
                    if podcast_episode:
                        podcast.episodes.append(podcast_episode)

            # Generate RSS XML
            rss_xml = str(podcast)

            # Emit RSS generation completed event
            self._emit_rss_generation_event("completed", channel, episodes, {"feed_size_bytes": len(rss_xml.encode('utf-8'))})

            return rss_xml

        except Exception as e:
            # Emit RSS generation failed event
            self._emit_rss_generation_event("failed", channel, episodes, {"error_message": str(e)})
            structured_logger.error(
                "RSS generation failed",
                channel_id=channel.id,
                error_type=type(e).__name__,
                error_message=str(e),
                exc_info=True
            )
            raise
    
    def validate_feed(self, feed_xml: str) -> tuple[bool, List[str]]:
        """
        Validate RSS feed against iTunes specifications
        """
        errors = []
        
        try:
            # Parse XML
            root = ET.fromstring(feed_xml)
            
            # Check required elements
            channel_elem = root.find('.//channel')
            if channel_elem is None:
                errors.append("Missing required <channel> element")
                return False, errors
            
            # Required channel elements
            required_elements = [
                ('title', 'Missing required <title> element'),
                ('description', 'Missing required <description> element'),
                ('link', 'Missing required <link> element'),
                ('language', 'Missing required <language> element')
            ]
            
            for elem_name, error_msg in required_elements:
                if channel_elem.find(elem_name) is None:
                    errors.append(error_msg)
            
            # Check iTunes namespace
            itunes_ns = {'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd'}
            
            # iTunes required elements
            itunes_required = [
                ('.//itunes:author', 'Missing iTunes author'),
                ('.//itunes:category', 'Missing iTunes category'),
                ('.//itunes:image', 'Missing iTunes image'),
                ('.//itunes:explicit', 'Missing iTunes explicit tag'),
                ('.//itunes:owner', 'Missing iTunes owner')
            ]
            
            for xpath, error_msg in itunes_required:
                if root.find(xpath, itunes_ns) is None:
                    errors.append(error_msg)
            
            # Validate episodes
            episodes = root.findall('.//item')
            for i, episode in enumerate(episodes):
                episode_errors = self._validate_episode(episode, i + 1)
                errors.extend(episode_errors)
            
            # Check image dimensions and format
            image_elem = root.find('.//itunes:image', itunes_ns)
            if image_elem is not None:
                href = image_elem.get('href')
                if href and not self._is_valid_image_url(href):
                    errors.append("iTunes image should be 1400x1400 to 3000x3000 pixels, square aspect ratio")
            
        except ET.ParseError as e:
            errors.append(f"XML parsing error: {str(e)}")
        
        return len(errors) == 0, errors
    
    def calculate_feed_score(self, channel: Channel, episodes: List[Episode]) -> float:
        """
        Calculate feed quality score based on iTunes best practices
        """
        score = 0.0
        max_score = 100.0
        
        # Channel completeness (40 points)
        if channel.name and len(channel.name.strip()) > 0:
            score += 5
        if channel.description and len(channel.description) >= 50:
            score += 10
        if channel.image_url:
            score += 10
        if channel.author_name:
            score += 5
        if channel.owner_email:
            score += 5
        if channel.category:
            score += 5
        
        # Episode quality (40 points)
        if episodes:
            completed_episodes = [ep for ep in episodes if ep.status.value == "completed"]
            if completed_episodes:
                score += 10
                
                # Average episode completeness
                episode_scores = []
                for ep in completed_episodes[:10]:  # Check up to 10 recent episodes
                    ep_score = 0
                    if ep.title and len(ep.title.strip()) > 0:
                        ep_score += 25
                    if ep.description and len(ep.description) >= 100:
                        ep_score += 25
                    if ep.audio_file_path:
                        ep_score += 25
                    if ep.duration and ep.duration.seconds > 0:
                        ep_score += 25
                    episode_scores.append(ep_score)
                
                if episode_scores:
                    avg_episode_score = sum(episode_scores) / len(episode_scores)
                    score += (avg_episode_score / 100) * 30
        
        # Technical compliance (20 points)
        feed_xml = self.generate_rss_feed(channel, episodes, "https://example.com")
        is_valid, validation_errors = self.validate_feed(feed_xml)
        if is_valid:
            score += 20
        else:
            # Partial credit based on error count
            error_penalty = min(len(validation_errors) * 2, 20)
            score += max(0, 20 - error_penalty)
        
        return min(score, max_score)
    
    def _create_episode(self, episode: Episode, base_url: str, all_episodes: List[Episode], channel: Channel) -> Optional[PodgenEpisode]:
        """
        Create PodGen episode with enhanced iTunes fields
        """
        if not episode.audio_file_path:
            return None

        # Use video_id-based URL for permanent, cache-friendly media links
        # This ensures URLs remain valid even if episodes are deleted and re-created
        # Format is indicated via Content-Type header and RSS enclosure type attribute
        media_url = f"{base_url}/v1/media/episodes/by-video-id/{episode.video_id.value}/audio"

        # Calculate episode number based on position
        episode_number = episode.get_episode_number(all_episodes)

        # Generate subtitle from YouTube channel info
        subtitle = episode.generate_subtitle()

        # Format description with preserved line breaks
        formatted_description = episode.format_description_for_rss()

        # Get media file size
        media_file_service = MediaFileService()
        if episode.media_file_size and episode.media_file_size > 0:
            file_size = episode.media_file_size
        else:
            # Calculate file size using full path
            from app.core.config import settings
            from pathlib import Path
            full_file_path = Path(settings.media_path) / episode.audio_file_path
            file_size = media_file_service.calculate_file_size(str(full_file_path))

        # Determine media type
        media_type = media_file_service.get_media_type(episode.audio_file_path)

        try:
            # Create media object with proper size
            media = Media(
                url=media_url,
                size=file_size,
                type=media_type,
                duration=timedelta(seconds=episode.duration.seconds) if episode.duration else None
            )

            # Use episode creation date (when added to channel) instead of YouTube publication date
            # This ensures episodes appear in the order they were added to the podcast
            pub_date = episode.created_at or episode.publication_date
            if pub_date.tzinfo is None:
                pub_date = pytz.utc.localize(pub_date)

            # Create episode with enhanced fields
            podcast_episode = PodgenEpisode(
                title=episode.title,
                summary=formatted_description,
                media=media,
                publication_date=pub_date
            )

            # Set iTunes-specific enhanced fields
            if subtitle:
                podcast_episode.subtitle = subtitle

            # Set explicit content from channel setting
            podcast_episode.explicit = bool(channel.explicit_content)

            # Set episode position/order for iTunes
            podcast_episode.position = episode_number

            # Use channel image for episode (if available)
            if hasattr(self, '_channel_image_url') and self._channel_image_url:
                podcast_episode.image = self._channel_image_url

            return podcast_episode

        except Exception as e:
            structured_logger.error(
                "Error creating podcast episode",
                episode_id=episode.id,
                error_type=type(e).__name__,
                error_message=str(e),
                exc_info=True
            )
            # Also emit a business event for episode creation failure
            self._emit_episode_creation_failed_event(episode, str(e))
            return None
    
    def _get_category(self, primary: str, secondary: Optional[str] = None) -> Category:
        """
        Get iTunes category object
        """
        # Map common categories to iTunes categories
        category_mapping = {
            "Technology": "Technology",
            "Business": "Business",
            "Comedy": "Comedy",
            "Education": "Education",
            "News": "News",
            "Sports": "Sports",
            "Health": "Health & Fitness",
            "Music": "Music",
            "Science": "Science",
            "Society": "Society & Culture",
            "True Crime": "True Crime",
            "Arts": "Arts"
        }
        
        mapped_primary = category_mapping.get(primary, "Technology")
        
        try:
            if secondary:
                return Category(mapped_primary, secondary)
            else:
                return Category(mapped_primary)
        except:
            return Category("Technology")
    
    def _get_media_type(self, file_path: str) -> str:
        """
        Determine MIME type from file extension
        """
        file_path = file_path.lower()
        if file_path.endswith('.mp3'):
            return 'audio/mpeg'
        elif file_path.endswith('.m4a'):
            return 'audio/mp4'
        elif file_path.endswith('.wav'):
            return 'audio/wav'
        elif file_path.endswith('.ogg'):
            return 'audio/ogg'
        else:
            return 'audio/mpeg'  # Default to MP3
    
    def _validate_episode(self, episode_elem, episode_num: int) -> List[str]:
        """
        Validate individual episode element
        """
        errors = []
        
        # Required episode elements
        if episode_elem.find('title') is None:
            errors.append(f"Episode {episode_num}: Missing title")
        
        if episode_elem.find('description') is None:
            errors.append(f"Episode {episode_num}: Missing description")
        
        enclosure = episode_elem.find('enclosure')
        if enclosure is None:
            errors.append(f"Episode {episode_num}: Missing enclosure (media file)")
        else:
            # Validate enclosure attributes
            if not enclosure.get('url'):
                errors.append(f"Episode {episode_num}: Enclosure missing URL")
            if not enclosure.get('length'):
                errors.append(f"Episode {episode_num}: Enclosure missing length")
            if not enclosure.get('type'):
                errors.append(f"Episode {episode_num}: Enclosure missing type")
        
        return errors
    
    def _is_valid_image_url(self, url: str) -> bool:
        """
        Basic validation of image URL format
        """
        valid_extensions = ['.jpg', '.jpeg', '.png']
        return any(url.lower().endswith(ext) for ext in valid_extensions)

    def _make_image_url_itunes_compliant(self, image_url: str, base_url: str) -> str:
        """
        Convert image URL to iTunes-compliant format with proper file extension
        """

        if not image_url:
            return image_url

        # Ensure we have a valid base_url - use settings if missing or malformed
        from app.core.config import settings
        original_base_url = base_url
        if not base_url or not base_url.startswith('http'):
            base_url = settings.base_url
            structured_logger.warning(
                "Invalid base_url provided to _make_image_url_itunes_compliant, using settings.base_url",
                provided_base_url=original_base_url,
                fallback_base_url=base_url
            )

        # If it's a relative URL, make it absolute with base_url
        if image_url.startswith('/'):
            # Remove trailing slash from base_url if present
            base = base_url.rstrip('/')
            absolute_url = f"{base}{image_url}"
        else:
            absolute_url = image_url

        # Ensure the URL has a valid iTunes-compliant extension
        if not absolute_url.lower().endswith(('.png', '.jpg', '.jpeg')):
            # If URL ends with '/image', add .png extension
            if absolute_url.endswith('/image'):
                absolute_url = absolute_url + '.png'
            # If URL contains '/image' but doesn't end with an extension, add .png
            elif '/image' in absolute_url and not absolute_url.endswith(('.png', '.jpg', '.jpeg')):
                absolute_url = absolute_url + '.png'

        return absolute_url
    
    def _load_itunes_categories(self) -> dict:
        """
        Load iTunes podcast categories
        """
        # This could be expanded with the full iTunes category list
        return {
            "Technology": ["Podcasting", "Tech News"],
            "Business": ["Careers", "Investing", "Marketing"],
            "Education": ["Courses", "How To", "Language Learning"],
            "News": ["Daily News", "Politics", "Tech News"],
            "Sports": ["Baseball", "Basketball", "Football"],
            "Health & Fitness": ["Alternative Health", "Fitness", "Medicine"],
            "Comedy": ["Comedy Interviews", "Improv", "Stand-Up"],
            "Music": ["Music Commentary", "Music History", "Music Interviews"],
            "Science": ["Astronomy", "Chemistry", "Physics"],
            "Society & Culture": ["Documentary", "Personal Journals", "Philosophy"],
            "True Crime": [],
            "Arts": ["Books", "Design", "Performing Arts"]
        }

    def _emit_rss_generation_event(self, action: str, channel: Channel, episodes: List[Episode], details: Optional[dict] = None):
        """Emit business event for RSS generation lifecycle"""
        if not self.event_service or not self.user_id:
            return

        try:
            event_details = {
                "channel_id": channel.id,
                "channel_name": channel.name,
                "episode_count": len(episodes),
                "completed_episodes": len([ep for ep in episodes if ep.status.value == "completed"]),
            }
            if details:
                event_details.update(details)

            severity = EventSeverity.INFO
            if action == "failed":
                severity = EventSeverity.ERROR

            message_map = {
                "started": f"RSS feed generation started for channel '{channel.name}'",
                "completed": f"RSS feed generation completed for channel '{channel.name}'",
                "failed": f"RSS feed generation failed for channel '{channel.name}'"
            }

            # Use asyncio to run the async method
            import asyncio
            asyncio.create_task(self.event_service.log_user_action(
                channel_id=self.channel_id or channel.id,
                user_id=self.user_id,
                action=f"rss_generation_{action}",
                resource_type="channel",
                resource_id=str(channel.id),
                message=message_map.get(action, f"RSS generation {action}"),
                details=event_details,
                severity=severity
            ))

        except Exception as e:
            logger.error(f"Failed to emit RSS generation {action} event: {e}")

    def _emit_episode_creation_failed_event(self, episode: Episode, error: str):
        """Emit business event for episode creation failure during RSS generation"""
        if not self.event_service or not self.user_id:
            return

        try:
            import asyncio
            asyncio.create_task(self.event_service.log_user_action(
                channel_id=self.channel_id or episode.channel_id,
                user_id=self.user_id,
                action="rss_episode_creation_failed",
                resource_type="episode",
                resource_id=str(episode.id),
                message=f"Failed to create RSS episode for '{episode.title}'",
                details={
                    "episode_id": episode.id,
                    "episode_title": episode.title,
                    "error_message": error,
                    "has_audio_file": bool(episode.audio_file_path),
                    "episode_status": episode.status.value
                },
                severity=EventSeverity.WARNING
            ))

        except Exception as e:
            logger.error(f"Failed to emit episode creation failed event for episode {episode.id}: {e}")

