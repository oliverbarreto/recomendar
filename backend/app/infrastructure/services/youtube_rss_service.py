"""
YouTube RSS Feed Service

This module provides functionality for fetching and parsing YouTube channel RSS feeds.
YouTube provides Atom XML feeds for channels that contain the latest 10-15 videos.
"""

import aiohttp
from lxml import etree
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class YouTubeRSSService:
    """Service for fetching and parsing YouTube channel RSS feeds"""

    RSS_FEED_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

    def __init__(self):
        """Initialize the RSS service"""
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def fetch_channel_rss(self, channel_id: str) -> List[Dict]:
        """
        Fetch RSS feed for a YouTube channel.

        Args:
            channel_id: YouTube channel ID (UCxxx format)

        Returns:
            List of video dictionaries with: video_id, title, published, url

        Raises:
            Exception: If RSS fetch or parse fails
        """
        url = self.RSS_FEED_URL.format(channel_id=channel_id)

        logger.info(f"[YouTubeRSSService] Fetching RSS feed for channel {channel_id}")

        try:
            session = await self._get_session()
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                response.raise_for_status()
                xml_content = await response.text()

            logger.debug(f"[YouTubeRSSService] Successfully fetched RSS feed for channel {channel_id}")
            return self._parse_rss_feed(xml_content)

        except aiohttp.ClientError as e:
            logger.error(f"[YouTubeRSSService] Failed to fetch RSS feed for channel {channel_id}: {e}")
            raise Exception(f"RSS feed fetch failed: {str(e)}")
        except Exception as e:
            logger.error(f"[YouTubeRSSService] Error processing RSS feed for channel {channel_id}: {e}")
            raise

    def _parse_rss_feed(self, xml_content: str) -> List[Dict]:
        """
        Parse YouTube Atom XML feed.

        Args:
            xml_content: XML content as string

        Returns:
            List of video dictionaries

        Raises:
            Exception: If XML parsing fails
        """
        try:
            root = etree.fromstring(xml_content.encode('utf-8'))

            # Define XML namespaces used in YouTube RSS feeds
            namespaces = {
                'atom': 'http://www.w3.org/2005/Atom',
                'yt': 'http://www.youtube.com/xml/schemas/2015',
                'media': 'http://search.yahoo.com/mrss/'
            }

            videos = []

            # Find all entry elements (each entry is a video)
            for entry in root.findall('atom:entry', namespaces):
                video_id_elem = entry.find('yt:videoId', namespaces)
                title_elem = entry.find('atom:title', namespaces)
                published_elem = entry.find('atom:published', namespaces)
                link_elem = entry.find('atom:link[@rel="alternate"]', namespaces)

                if video_id_elem is not None and video_id_elem.text:
                    video = {
                        'video_id': video_id_elem.text,
                        'title': title_elem.text if title_elem is not None else 'Unknown',
                        'published': published_elem.text if published_elem is not None else None,
                        'url': link_elem.get('href') if link_elem is not None else f"https://www.youtube.com/watch?v={video_id_elem.text}"
                    }
                    videos.append(video)
                    logger.debug(f"[YouTubeRSSService] Parsed video: {video['video_id']} - {video['title']}")

            logger.info(f"[YouTubeRSSService] Parsed {len(videos)} videos from RSS feed")
            return videos

        except etree.XMLSyntaxError as e:
            logger.error(f"[YouTubeRSSService] XML parsing error: {e}")
            raise Exception(f"Invalid RSS feed XML: {str(e)}")
        except Exception as e:
            logger.error(f"[YouTubeRSSService] Error parsing RSS feed: {e}")
            raise

    async def close(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.debug("[YouTubeRSSService] Closed aiohttp session")
