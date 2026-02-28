"""
File service for managing episode audio files and metadata
"""
import os
import shutil
import re
import aiohttp
from pathlib import Path
from typing import Optional, Dict, Any
import logging
import hashlib
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB, TDRC, COMM, TCON
from mutagen import MutagenError

from app.core.config import settings
from app.domain.entities.episode import Episode

logger = logging.getLogger(__name__)


class FileServiceError(Exception):
    """Exception raised by file service operations"""
    pass


class FileService:
    """
    Service for managing episode files and metadata
    """
    
    def __init__(self):
        self.media_path = Path(settings.media_path)
        self.temp_path = Path(settings.temp_path)
        
        # Ensure directories exist
        self.media_path.mkdir(parents=True, exist_ok=True)
        self.temp_path.mkdir(parents=True, exist_ok=True)
        
        # Allowed file extensions
        self.allowed_extensions = {'.mp3', '.m4a', '.ogg', '.wav', '.flac'}
        
        # Audio file size limits (in bytes)
        self.max_file_size = 500 * 1024 * 1024  # 500MB
        self.min_file_size = 1024  # 1KB
    
    async def process_audio_file(
        self, 
        temp_file_path: str, 
        episode: Episode
    ) -> str:
        """
        Process downloaded audio file: move, rename, and add metadata
        
        Args:
            temp_file_path: Path to temporary downloaded file
            episode: Episode entity
            
        Returns:
            Relative path to processed file
            
        Raises:
            FileServiceError: If processing fails
        """
        try:
            temp_path = Path(temp_file_path)
            
            # Validate input file
            if not temp_path.exists():
                raise FileServiceError(f"Temporary file not found: {temp_file_path}")
            
            await self._validate_audio_file(temp_path)
            
            # Generate final file path
            final_path = self._generate_file_path(episode)
            
            logger.info(f"Processing audio file for episode {episode.id}: {episode.title}")
            
            # Ensure target directory exists
            final_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Move file to final location
            shutil.move(str(temp_path), str(final_path))
            logger.debug(f"Moved file from {temp_path} to {final_path}")
            
            # Add metadata to audio file
            await self._add_audio_metadata(final_path, episode)
            
            # Set proper file permissions
            os.chmod(final_path, 0o644)
            
            # Return relative path for database storage
            relative_path = final_path.relative_to(self.media_path)
            
            logger.info(f"Successfully processed audio file: {relative_path}")
            return str(relative_path)
            
        except Exception as e:
            logger.error(f"Failed to process audio file: {e}")
            
            # Clean up on failure
            try:
                if 'final_path' in locals() and final_path.exists():
                    final_path.unlink()
            except Exception:
                pass
            
            raise FileServiceError(f"Audio file processing failed: {e}")
    
    async def _validate_audio_file(self, file_path: Path):
        """Validate audio file before processing"""
        try:
            # Check file size
            file_size = file_path.stat().st_size
            
            if file_size < self.min_file_size:
                raise FileServiceError(f"File too small: {file_size} bytes")
            
            if file_size > self.max_file_size:
                raise FileServiceError(f"File too large: {file_size} bytes")
            
            # Check file extension
            if file_path.suffix.lower() not in self.allowed_extensions:
                logger.warning(f"Unexpected file extension: {file_path.suffix}")
            
            # Try to read audio metadata to validate it's a valid audio file
            try:
                audio = MP3(str(file_path))
                if audio.info.length < 1:  # At least 1 second
                    raise FileServiceError("Audio file appears to be empty or corrupted")
            except MutagenError:
                # File might not be MP3, that's okay
                pass
                
        except FileServiceError:
            raise
        except Exception as e:
            raise FileServiceError(f"File validation failed: {e}")
    
    def _generate_file_path(self, episode: Episode) -> Path:
        """
        Generate organized file path for episode
        """
        # Use channel ID for organization
        channel_dir = f"channel_{episode.channel_id}"

        # Generate filename with only video ID for uniqueness
        filename = f"{episode.video_id.value}.mp3"
        
        return self.media_path / channel_dir / filename
    
    
    async def _add_audio_metadata(self, file_path: Path, episode: Episode):
        """
        Add ID3 metadata to MP3 file
        """
        try:
            logger.debug(f"Adding metadata to audio file: {file_path}")
            
            # Load audio file
            try:
                audio = MP3(str(file_path), ID3=ID3)
            except MutagenError as e:
                logger.warning(f"Could not load audio file for metadata: {e}")
                return
            
            # Ensure ID3 tag exists
            if audio.tags is None:
                audio.add_tags()
            
            # Add basic metadata
            audio.tags.add(TIT2(encoding=3, text=episode.title))
            audio.tags.add(TPE1(encoding=3, text="LabCastARR"))
            audio.tags.add(TALB(encoding=3, text=f"Channel {episode.channel_id}"))
            audio.tags.add(TCON(encoding=3, text="Podcast"))
            
            # Add publication year
            if episode.publication_date:
                audio.tags.add(TDRC(encoding=3, text=str(episode.publication_date.year)))
            
            # Add description as comment
            if episode.description:
                # Limit comment length
                description = episode.description[:1000]
                audio.tags.add(COMM(
                    encoding=3,
                    lang='eng',
                    desc='Description',
                    text=description
                ))
            
            # Download and add thumbnail as cover art
            if episode.thumbnail_url:
                try:
                    cover_data = await self._download_thumbnail(episode.thumbnail_url)
                    if cover_data:
                        # Determine image format
                        if cover_data.startswith(b'\x89PNG'):
                            mime_type = 'image/png'
                        elif cover_data.startswith(b'\xff\xd8'):
                            mime_type = 'image/jpeg'
                        else:
                            mime_type = 'image/jpeg'  # Default
                        
                        audio.tags.add(APIC(
                            encoding=3,
                            mime=mime_type,
                            type=3,  # Cover (front)
                            desc='Cover',
                            data=cover_data
                        ))
                        logger.debug("Added cover art to audio file")
                except Exception as e:
                    logger.warning(f"Failed to add cover art: {e}")
            
            # Save metadata
            audio.save()
            logger.debug("Successfully added metadata to audio file")
            
        except Exception as e:
            logger.warning(f"Failed to add metadata to {file_path}: {e}")
            # Don't fail the entire process for metadata errors
    
    async def _download_thumbnail(self, thumbnail_url: str) -> Optional[bytes]:
        """
        Download thumbnail image for cover art
        """
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(thumbnail_url) as response:
                    if response.status == 200:
                        content_length = response.headers.get('content-length')
                        
                        # Check size limit (5MB max for thumbnails)
                        if content_length and int(content_length) > 5 * 1024 * 1024:
                            logger.warning("Thumbnail too large, skipping")
                            return None
                        
                        data = await response.read()
                        
                        # Validate it's actually an image
                        if data.startswith((b'\x89PNG', b'\xff\xd8', b'GIF')):
                            return data
                        else:
                            logger.warning("Downloaded thumbnail is not a valid image")
                            return None
                    else:
                        logger.warning(f"Failed to download thumbnail: HTTP {response.status}")
                        return None
                        
        except Exception as e:
            logger.warning(f"Failed to download thumbnail: {e}")
            return None
    
    async def delete_episode_file(self, file_path: str) -> bool:
        """
        Delete episode audio file
        
        Args:
            file_path: Relative path to file
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            full_path = self.media_path / file_path
            
            if full_path.exists():
                # Validate path is within media directory (security)
                resolved_path = full_path.resolve()
                resolved_media = self.media_path.resolve()
                
                if not str(resolved_path).startswith(str(resolved_media)):
                    raise FileServiceError("File path outside media directory")
                
                full_path.unlink()
                logger.info(f"Deleted episode file: {file_path}")
                
                # Clean up empty directories
                try:
                    parent = full_path.parent
                    if parent != self.media_path and not any(parent.iterdir()):
                        parent.rmdir()
                        logger.debug(f"Removed empty directory: {parent}")
                except OSError:
                    pass  # Directory not empty
                
                return True
            else:
                logger.warning(f"File not found for deletion: {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get audio file information
        
        Args:
            file_path: Relative path to file
            
        Returns:
            Dictionary with file information or None if not found
        """
        try:
            full_path = self.media_path / file_path
            
            if not full_path.exists():
                return None
            
            # Get file stats
            stat = full_path.stat()
            
            file_info = {
                "file_path": file_path,
                "file_size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "exists": True
            }
            
            # Try to get audio information
            try:
                audio = MP3(str(full_path))
                file_info.update({
                    "duration": audio.info.length,
                    "bitrate": audio.info.bitrate,
                    "sample_rate": audio.info.sample_rate,
                    "mode": getattr(audio.info, 'mode', 'unknown'),
                    "channels": getattr(audio.info, 'channels', None)
                })
            except MutagenError as e:
                logger.warning(f"Could not read audio info for {file_path}: {e}")
                file_info["audio_error"] = str(e)
            
            return file_info
            
        except Exception as e:
            logger.error(f"Failed to get file info for {file_path}: {e}")
            return None
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage usage statistics
        """
        try:
            total_size = 0
            file_count = 0
            
            # Walk through media directory
            for root, dirs, files in os.walk(self.media_path):
                for file in files:
                    file_path = Path(root) / file
                    try:
                        size = file_path.stat().st_size
                        total_size += size
                        file_count += 1
                    except OSError:
                        continue
            
            # Get disk usage
            disk_usage = shutil.disk_usage(self.media_path)
            
            return {
                "total_files": file_count,
                "total_size_bytes": total_size,
                "total_size_mb": total_size / (1024 * 1024),
                "total_size_gb": total_size / (1024 * 1024 * 1024),
                "disk_total": disk_usage.total,
                "disk_used": disk_usage.used,
                "disk_free": disk_usage.free,
                "disk_usage_percent": (disk_usage.used / disk_usage.total) * 100
            }
            
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {
                "error": str(e),
                "total_files": 0,
                "total_size_bytes": 0
            }
    
    async def cleanup_orphaned_files(self, episode_repository) -> Dict[str, Any]:
        """
        Clean up orphaned files that don't have corresponding episodes
        """
        try:
            logger.info("Starting orphaned file cleanup")
            
            cleaned_files = []
            total_size_freed = 0
            
            # Get all episode file paths from database
            episodes = await episode_repository.get_all()
            db_file_paths = {
                episode.audio_file_path 
                for episode in episodes 
                if episode.audio_file_path
            }
            
            # Walk through media directory
            for root, dirs, files in os.walk(self.media_path):
                for file in files:
                    file_path = Path(root) / file
                    relative_path = file_path.relative_to(self.media_path)
                    relative_str = str(relative_path)
                    
                    # Skip if file is referenced in database
                    if relative_str in db_file_paths:
                        continue
                    
                    # Skip non-audio files
                    if file_path.suffix.lower() not in self.allowed_extensions:
                        continue
                    
                    # File is orphaned, delete it
                    try:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        
                        cleaned_files.append(relative_str)
                        total_size_freed += file_size
                        
                        logger.debug(f"Deleted orphaned file: {relative_str}")
                        
                    except Exception as e:
                        logger.warning(f"Failed to delete orphaned file {relative_str}: {e}")
            
            # Clean up empty directories
            for root, dirs, files in os.walk(self.media_path, topdown=False):
                for dir_name in dirs:
                    dir_path = Path(root) / dir_name
                    try:
                        if not any(dir_path.iterdir()):
                            dir_path.rmdir()
                            logger.debug(f"Removed empty directory: {dir_path}")
                    except OSError:
                        pass  # Directory not empty or other error
            
            result = {
                "cleaned_files": len(cleaned_files),
                "size_freed_bytes": total_size_freed,
                "size_freed_mb": total_size_freed / (1024 * 1024),
                "files": cleaned_files[:100]  # Limit list size
            }
            
            logger.info(f"Cleanup complete: {len(cleaned_files)} files, {result['size_freed_mb']:.2f} MB freed")
            return result
            
        except Exception as e:
            logger.error(f"Failed to cleanup orphaned files: {e}")
            return {
                "error": str(e),
                "cleaned_files": 0,
                "size_freed_bytes": 0
            }