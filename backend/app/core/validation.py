"""
Input validation and sanitization utilities
"""
import re
import html
from typing import Any, Optional
from urllib.parse import urlparse
from pydantic import BaseModel, validator


class SecurityValidators:
    """
    Collection of security validation methods
    """
    
    # Common malicious patterns
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'onload\s*=',
        r'onerror\s*=',
        r'onclick\s*=',
        r'onmouseover\s*=',
    ]
    
    SQL_INJECTION_PATTERNS = [
        r'(\bUNION\b|\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b)',
        r'(\bOR\b|\bAND\b)\s+\d+\s*=\s*\d+',
        r"'[^']*'|\"[^\"]*\"",
        r';\s*(--|\#)',
    ]
    
    PATH_TRAVERSAL_PATTERNS = [
        r'\.\./|\.\.\\',
        r'/etc/passwd',
        r'/etc/shadow',
        r'\\windows\\system32',
    ]
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """
        Sanitize string input
        
        Args:
            value: Input string
            max_length: Maximum allowed length
            
        Returns:
            str: Sanitized string
        """
        if not isinstance(value, str):
            return str(value)
        
        # Limit length
        value = value[:max_length]
        
        # HTML escape
        value = html.escape(value)
        
        # Remove null bytes and control characters
        value = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', value)
        
        return value.strip()
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """
        Validate URL format and security
        
        Args:
            url: URL to validate
            
        Returns:
            bool: True if URL is valid and safe
        """
        try:
            parsed = urlparse(url)
            
            # Check scheme
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Check for local/private IPs in hostname
            if parsed.hostname:
                # Basic check for localhost/private IPs
                if parsed.hostname in ['localhost', '127.0.0.1', '0.0.0.0']:
                    return False
                
                # Check for private IP ranges (basic)
                if (parsed.hostname.startswith('192.168.') or 
                    parsed.hostname.startswith('10.') or 
                    parsed.hostname.startswith('172.')):
                    return False
            
            return True
            
        except Exception:
            return False
    
    @staticmethod
    def validate_youtube_url(url: str) -> bool:
        """
        Validate YouTube URL specifically
        
        Args:
            url: YouTube URL to validate
            
        Returns:
            bool: True if valid YouTube URL
        """
        if not SecurityValidators.validate_url(url):
            return False
        
        youtube_patterns = [
            r'youtube\.com/watch\?v=',
            r'youtu\.be/',
            r'youtube\.com/embed/',
            r'm\.youtube\.com/watch\?v=',
        ]
        
        return any(re.search(pattern, url) for pattern in youtube_patterns)
    
    @staticmethod
    def check_malicious_content(value: str) -> bool:
        """
        Check for malicious content patterns
        
        Args:
            value: String to check
            
        Returns:
            bool: True if malicious content detected
        """
        value_lower = value.lower()
        
        # Check XSS patterns
        for pattern in SecurityValidators.XSS_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        
        # Check SQL injection patterns  
        for pattern in SecurityValidators.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        
        # Check path traversal patterns
        for pattern in SecurityValidators.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        
        return False
    
    @staticmethod
    def validate_filename(filename: str) -> bool:
        """
        Validate filename for security
        
        Args:
            filename: Filename to validate
            
        Returns:
            bool: True if filename is safe
        """
        # Check for path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return False
        
        # Check for reserved names (Windows)
        reserved_names = [
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        ]
        
        if filename.upper() in reserved_names:
            return False
        
        # Check for malicious patterns
        if SecurityValidators.check_malicious_content(filename):
            return False
        
        return True


class SecureBaseModel(BaseModel):
    """
    Base model with built-in security validation
    """
    
    @validator('*', pre=True)
    def validate_strings(cls, v):
        """Validate all string fields for security"""
        if isinstance(v, str):
            # Check for malicious content
            if SecurityValidators.check_malicious_content(v):
                raise ValueError("Potentially malicious content detected")
            
            # Sanitize the string
            return SecurityValidators.sanitize_string(v)
        
        return v