"""
Channel domain entity
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from app.domain.value_objects.email import Email


@dataclass
class Channel:
    """
    Channel domain entity representing a podcast channel
    """
    id: Optional[int]
    user_id: int
    name: str
    description: str
    website_url: str
    image_url: Optional[str] = None
    category: str = "Technology"
    language: str = "en"
    explicit_content: bool = True
    author_name: str = ""
    author_email: Optional[Email] = None
    owner_name: str = ""
    owner_email: Optional[Email] = None
    feed_url: str = ""
    feed_last_updated: Optional[datetime] = None
    feed_validation_score: Optional[float] = None
    copyright: Optional[str] = None
    podcast_type: str = "episodic"
    subcategory: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        # Validate required fields
        if not self.name or len(self.name.strip()) < 1:
            raise ValueError("Channel name is required")
        self.name = self.name.strip()
        
        if not self.description:
            self.description = ""
        
        # Validate user_id
        if self.user_id <= 0:
            raise ValueError("Valid user_id is required")

        # Validate website_url is required
        if not self.website_url or len(self.website_url.strip()) < 1:
            raise ValueError("Website URL is required for iTunes compliance")
        
        # Validate and normalize optional URLs
        if self.website_url:
            self.website_url = self._normalize_url(self.website_url)
        
        if self.image_url:
            self.image_url = self._normalize_url(self.image_url)
        
        # Validate category
        if not self.category:
            self.category = "Technology"
        
        # Validate language code (basic validation)
        if not self.language or len(self.language) != 2:
            self.language = "en"
        
        # Set timestamps
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def _normalize_url(self, url: str) -> str:
        """
        Normalize URL by ensuring it has a protocol
        Only applies to absolute URLs, not relative paths
        """
        url = url.strip()
        # Skip normalization for relative URLs (starting with /)
        if url.startswith('/'):
            return url
        # Only add https:// for URLs that don't already have a protocol
        if url and not url.startswith(('http://', 'https://')):
            return f'https://{url}'
        return url
    
    def generate_feed_url(self, domain: str) -> str:
        """
        Generate RSS feed URL for this channel
        """
        if not domain:
            raise ValueError("Domain is required to generate feed URL")

        # Remove protocol from domain if present
        domain = domain.replace('https://', '').replace('http://', '')
        return f"https://{domain}/v1/feeds/{self.id}/feed.xml"
    
    def update_settings(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        website_url: Optional[str] = None,
        image_url: Optional[str] = None,
        category: Optional[str] = None,
        language: Optional[str] = None,
        explicit_content: Optional[bool] = None,
        author_name: Optional[str] = None,
        author_email: Optional[str] = None,
        owner_name: Optional[str] = None,
        owner_email: Optional[str] = None
    ) -> None:
        """
        Update channel settings with validation
        """
        if name is not None:
            if not name or len(name.strip()) < 1:
                raise ValueError("Channel name is required")
            self.name = name.strip()
        
        if description is not None:
            self.description = description
        
        if website_url is not None:
            self.website_url = self._normalize_url(website_url) if website_url else None
        
        if image_url is not None:
            self.image_url = self._normalize_url(image_url) if image_url else None
        
        if category is not None:
            self.category = category if category else "Technology"
        
        if language is not None:
            self.language = language if language and len(language) == 2 else "en"
        
        if explicit_content is not None:
            self.explicit_content = explicit_content
        
        if author_name is not None:
            self.author_name = author_name
        
        if author_email is not None:
            self.author_email = Email.create_optional(author_email)
        
        if owner_name is not None:
            self.owner_name = owner_name
        
        if owner_email is not None:
            self.owner_email = Email.create_optional(owner_email)
        
        self.updated_at = datetime.utcnow()
    
    def update_feed_url(self, domain: str) -> None:
        """
        Update the RSS feed URL based on domain
        """
        if self.id is None:
            raise ValueError("Cannot generate feed URL for channel without ID")
        
        self.feed_url = self.generate_feed_url(domain)
        self.updated_at = datetime.utcnow()
    
    @classmethod
    def create_channel(
        cls,
        user_id: int,
        name: str,
        description: str,
        author_name: str = "",
        author_email: Optional[str] = None
    ) -> 'Channel':
        """
        Factory method to create a new channel
        """
        return cls(
            id=None,
            user_id=user_id,
            name=name,
            description=description,
            author_name=author_name,
            author_email=Email.create_optional(author_email),
            owner_name=author_name,  # Default owner same as author
            owner_email=Email.create_optional(author_email)
        )