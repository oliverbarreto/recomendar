"""
Media file service for handling media file operations
"""
import os
import re
from typing import Optional, Dict, Tuple
from pathlib import Path
import magic
from mutagen import File as MutagenFile
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.wave import WAVE
from mutagen.oggvorbis import OggVorbis
from mutagen.flac import FLAC

from app.infrastructure.services.upload_service import FileValidationError
from app.core.logging import get_logger

logger = get_logger("media_file_service")

# Allowed MIME types for audio uploads
ALLOWED_MIME_TYPES = {
    'audio/mpeg': ['.mp3'],
    'audio/mp4': ['.m4a', '.mp4'],
    'audio/x-m4a': ['.m4a'],
    'audio/wav': ['.wav'],
    'audio/x-wav': ['.wav'],
    'audio/wave': ['.wav'],
    'audio/ogg': ['.ogg'],
    'audio/flac': ['.flac'],
    'audio/x-flac': ['.flac']
}


class MediaFileService:
    """Service for media file operations"""

    def calculate_file_size(self, file_path: str) -> int:
        """Calculate media file size in bytes"""
        try:
            if os.path.exists(file_path):
                return os.path.getsize(file_path)
            return 0
        except (OSError, IOError):
            return 0

    def update_episode_file_size(self, episode_id: int, file_path: str) -> int:
        """Update episode with calculated file size"""
        file_size = self.calculate_file_size(file_path)
        # Update database record
        # Implementation depends on repository pattern
        return file_size

    def validate_media_file(self, file_path: str) -> bool:
        """Validate that the media file exists and is accessible"""
        try:
            return os.path.exists(file_path) and os.path.isfile(file_path)
        except (OSError, IOError):
            return False

    def get_media_type(self, file_path: str) -> str:
        """Get MIME type for media file"""
        if not file_path:
            return "audio/mpeg"

        # Get file extension
        extension = Path(file_path).suffix.lower()

        # Map extensions to MIME types
        mime_types = {
            '.mp3': 'audio/mpeg',
            '.m4a': 'audio/mp4',
            '.wav': 'audio/wav',
            '.ogg': 'audio/ogg',
            '.flac': 'audio/flac'
        }

        return mime_types.get(extension, 'audio/mpeg')

    def validate_audio_file(self, file_path: str, max_size_mb: int = 500) -> Dict[str, any]:
        """
        Validate uploaded audio file using python-magic for MIME type detection
        
        Args:
            file_path: Path to the audio file
            max_size_mb: Maximum allowed file size in MB
            
        Returns:
            Dict with validation results: {'valid': bool, 'mime_type': str, 'error': str}
            
        Raises:
            FileValidationError: If file validation fails
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                raise FileValidationError(
                    "File does not exist",
                    details={'file_path': file_path}
                )
            
            # Check file size
            file_size = os.path.getsize(file_path)
            max_size_bytes = max_size_mb * 1024 * 1024
            
            if file_size > max_size_bytes:
                raise FileValidationError(
                    f"File size ({file_size / (1024 * 1024):.2f} MB) exceeds maximum allowed size ({max_size_mb} MB)",
                    details={'file_size': file_size, 'max_size': max_size_bytes}
                )
            
            # Detect MIME type using python-magic
            mime_type = magic.from_file(file_path, mime=True)
            
            # Check if MIME type is allowed
            if mime_type not in ALLOWED_MIME_TYPES:
                allowed_types = ', '.join(ALLOWED_MIME_TYPES.keys())
                raise FileValidationError(
                    f"Invalid audio format. Detected: {mime_type}. Allowed: {allowed_types}",
                    mime_type=mime_type,
                    details={'detected_mime': mime_type, 'allowed_mimes': list(ALLOWED_MIME_TYPES.keys())}
                )
            
            logger.info(f"Audio file validated successfully: {file_path}, MIME: {mime_type}, Size: {file_size / (1024 * 1024):.2f} MB")
            
            return {
                'valid': True,
                'mime_type': mime_type,
                'file_size': file_size,
                'error': None
            }
            
        except FileValidationError:
            raise
        except Exception as e:
            logger.error(f"Error validating audio file {file_path}: {e}")
            raise FileValidationError(
                f"Failed to validate audio file: {str(e)}",
                details={'error': str(e), 'file_path': file_path}
            )

    def extract_audio_metadata(self, file_path: str) -> Dict[str, any]:
        """
        Extract audio metadata (duration, bitrate) using mutagen
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Dict with metadata: {'duration_seconds': int, 'bitrate': int, 'sample_rate': int}
        """
        try:
            audio = MutagenFile(file_path)
            
            if audio is None:
                logger.warning(f"Could not extract metadata from {file_path}")
                return {
                    'duration_seconds': 0,
                    'bitrate': 0,
                    'sample_rate': 0
                }
            
            duration_seconds = int(audio.info.length) if hasattr(audio.info, 'length') else 0
            bitrate = int(audio.info.bitrate) if hasattr(audio.info, 'bitrate') else 0
            sample_rate = int(audio.info.sample_rate) if hasattr(audio.info, 'sample_rate') else 0
            
            logger.info(f"Extracted metadata from {file_path}: duration={duration_seconds}s, bitrate={bitrate}, sample_rate={sample_rate}")
            
            return {
                'duration_seconds': duration_seconds,
                'bitrate': bitrate,
                'sample_rate': sample_rate
            }
            
        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {e}")
            return {
                'duration_seconds': 0,
                'bitrate': 0,
                'sample_rate': 0
            }

    def validate_file_size(self, file_path: str, max_size_mb: int = 500) -> Tuple[bool, int]:
        """
        Validate file size against maximum limit
        
        Args:
            file_path: Path to the file
            max_size_mb: Maximum allowed size in MB
            
        Returns:
            Tuple of (is_valid, file_size_bytes)
        """
        try:
            file_size = os.path.getsize(file_path)
            max_size_bytes = max_size_mb * 1024 * 1024
            is_valid = file_size <= max_size_bytes
            
            return is_valid, file_size
            
        except Exception as e:
            logger.error(f"Error validating file size for {file_path}: {e}")
            return False, 0

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to remove dangerous characters and prevent path traversal
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename safe for filesystem storage
        """
        # Remove path components (prevent path traversal)
        filename = os.path.basename(filename)
        
        # Remove or replace dangerous characters
        # Keep alphanumeric, dots, hyphens, underscores, and spaces
        filename = re.sub(r'[^\w\s\-\.]', '_', filename)
        
        # Replace multiple spaces/underscores with single underscore
        filename = re.sub(r'[\s_]+', '_', filename)
        
        # Remove leading/trailing dots and underscores
        filename = filename.strip('._')
        
        # Limit filename length (keep extension)
        name, ext = os.path.splitext(filename)
        if len(name) > 200:
            name = name[:200]
        
        sanitized = f"{name}{ext}"
        
        logger.debug(f"Sanitized filename: {filename} -> {sanitized}")
        
        return sanitized