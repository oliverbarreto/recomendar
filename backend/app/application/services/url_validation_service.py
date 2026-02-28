"""
URL validation service for YouTube URLs
"""
import re
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs, unquote
import logging

logger = logging.getLogger(__name__)


class URLValidationService:
    """
    Service for validating and normalizing YouTube URLs
    """
    
    YOUTUBE_DOMAINS = {
        'youtube.com', 'www.youtube.com', 
        'youtu.be', 'www.youtu.be', 
        'm.youtube.com', 'music.youtube.com'
    }
    
    YOUTUBE_PATTERNS = [
        # Standard watch URLs
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        # Shortened URLs
        r'(?:https?://)?youtu\.be/([a-zA-Z0-9_-]{11})',
        # Embed URLs
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        # Mobile URLs
        r'(?:https?://)?(?:m\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        # Playlist URLs (extract video ID)
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})&list=[\w-]+',
    ]
    
    def validate_youtube_url(self, url: str) -> Dict[str, Any]:
        """
        Comprehensive YouTube URL validation and normalization
        
        Args:
            url: URL to validate
            
        Returns:
            Dictionary with validation result and normalized URL
        """
        logger.debug(f"Validating YouTube URL: {url}")
        
        # Basic input validation
        if not url:
            return self._error_response('URL is required')
        
        if not isinstance(url, str):
            return self._error_response('URL must be a string')
        
        # Length validation
        if len(url) > 2048:
            return self._error_response('URL is too long (max 2048 characters)')
        
        # Normalize URL
        try:
            normalized_url = self._normalize_url(url)
        except Exception as e:
            return self._error_response(f'URL normalization failed: {str(e)}')
        
        # Parse URL
        try:
            parsed = urlparse(normalized_url)
        except Exception:
            return self._error_response('Invalid URL format')
        
        # Check domain
        if parsed.netloc.lower() not in self.YOUTUBE_DOMAINS:
            return self._error_response('URL must be from YouTube')
        
        # Extract video ID
        video_id = self._extract_video_id(normalized_url)
        if not video_id:
            return self._error_response('Invalid YouTube video ID')
        
        # Validate video ID format
        if not self._is_valid_video_id(video_id):
            return self._error_response('Invalid YouTube video ID format')
        
        # Check for suspicious patterns
        security_check = self._security_validation(normalized_url)
        if not security_check['safe']:
            return self._error_response(f'Security validation failed: {security_check["reason"]}')
        
        logger.info(f"Successfully validated YouTube URL: {video_id}")
        
        return {
            'valid': True,
            'video_id': video_id,
            'normalized_url': normalized_url,
            'original_url': url,
            'canonical_url': f'https://www.youtube.com/watch?v={video_id}',
            'domain': parsed.netloc.lower(),
            'url_type': self._get_url_type(normalized_url)
        }
    
    def _normalize_url(self, url: str) -> str:
        """
        Normalize YouTube URL to standard format
        """
        # Strip whitespace
        url = url.strip()
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # URL decode
        url = unquote(url)
        
        # Handle some common malformations
        url = url.replace('youtu.be/', 'youtube.com/watch?v=')
        url = url.replace('youtube.com/embed/', 'youtube.com/watch?v=')
        
        return url
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """
        Extract video ID from various YouTube URL formats
        """
        for pattern in self.YOUTUBE_PATTERNS:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Try parsing query parameters as fallback
        try:
            parsed = urlparse(url)
            if 'v' in parse_qs(parsed.query):
                video_id = parse_qs(parsed.query)['v'][0]
                if self._is_valid_video_id(video_id):
                    return video_id
        except Exception:
            pass
        
        return None
    
    def _is_valid_video_id(self, video_id: str) -> bool:
        """
        Validate YouTube video ID format
        """
        if not video_id or not isinstance(video_id, str):
            return False
        
        # YouTube video IDs are exactly 11 characters
        if len(video_id) != 11:
            return False
        
        # Valid characters: letters, numbers, hyphens, underscores
        pattern = r'^[a-zA-Z0-9_-]{11}$'
        return bool(re.match(pattern, video_id))
    
    def _security_validation(self, url: str) -> Dict[str, Any]:
        """
        Perform security validation on URL
        """
        # Check for obvious malicious patterns
        suspicious_patterns = [
            r'javascript:',
            r'data:',
            r'<script',
            r'</script',
            r'<%',
            r'%>',
        ]
        
        url_lower = url.lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, url_lower, re.IGNORECASE):
                return {
                    'safe': False,
                    'reason': f'Suspicious pattern detected: {pattern}'
                }
        
        # Check for excessive redirects or suspicious query parameters
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        
        suspicious_params = ['redirect', 'goto', 'url', 'link', 'forward']
        for param in suspicious_params:
            if param in query_params:
                return {
                    'safe': False,
                    'reason': f'Suspicious query parameter: {param}'
                }
        
        return {'safe': True, 'reason': None}
    
    def _get_url_type(self, url: str) -> str:
        """
        Determine the type of YouTube URL
        """
        if 'youtu.be/' in url:
            return 'shortened'
        elif '/embed/' in url:
            return 'embed'
        elif '/watch' in url:
            if 'list=' in url:
                return 'playlist'
            return 'standard'
        elif 'm.youtube.com' in url:
            return 'mobile'
        elif 'music.youtube.com' in url:
            return 'music'
        return 'unknown'
    
    def _error_response(self, message: str) -> Dict[str, Any]:
        """
        Generate error response
        """
        return {
            'valid': False,
            'error': message,
            'error_code': self._get_error_code(message)
        }
    
    def _get_error_code(self, message: str) -> str:
        """
        Generate error code based on message
        """
        if 'required' in message.lower():
            return 'URL_REQUIRED'
        elif 'domain' in message.lower() or 'youtube' in message.lower():
            return 'INVALID_DOMAIN'
        elif 'video id' in message.lower():
            return 'INVALID_VIDEO_ID'
        elif 'too long' in message.lower():
            return 'URL_TOO_LONG'
        elif 'format' in message.lower():
            return 'INVALID_FORMAT'
        elif 'security' in message.lower():
            return 'SECURITY_VIOLATION'
        else:
            return 'VALIDATION_ERROR'
    
    def extract_video_id_only(self, url: str) -> Optional[str]:
        """
        Quick method to extract just the video ID
        """
        validation = self.validate_youtube_url(url)
        if validation['valid']:
            return validation['video_id']
        return None
    
    def is_youtube_url(self, url: str) -> bool:
        """
        Quick check if URL is from YouTube
        """
        if not url:
            return False
        
        try:
            normalized = self._normalize_url(url)
            parsed = urlparse(normalized)
            return parsed.netloc.lower() in self.YOUTUBE_DOMAINS
        except Exception:
            return False
    
    def get_canonical_url(self, url: str) -> Optional[str]:
        """
        Get canonical YouTube URL
        """
        validation = self.validate_youtube_url(url)
        if validation['valid']:
            return validation['canonical_url']
        return None