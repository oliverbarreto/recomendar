"""
Upload processing service for handling file uploads with streaming and conversion
"""
import os
import asyncio
import time
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime
import aiofiles
import subprocess

from fastapi import UploadFile

from app.infrastructure.services.upload_service import (
    FileConversionError,
    FileValidationError
)
from app.infrastructure.services.media_file_service import MediaFileService
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("upload_processing_service")

# Chunk size for streaming file writes (8KB)
CHUNK_SIZE = 8 * 1024


class UploadProcessingService:
    """Service for processing uploaded audio files with streaming and conversion"""
    
    def __init__(self, media_file_service: MediaFileService):
        self.media_file_service = media_file_service
        self.temp_path = Path(settings.temp_path)
        self.media_path = Path(settings.media_path)
        
        # Ensure directories exist
        self.temp_path.mkdir(parents=True, exist_ok=True)
        self.media_path.mkdir(parents=True, exist_ok=True)
    
    async def process_uploaded_episode(
        self,
        upload_file: UploadFile,
        channel_id: int,
        episode_title: str
    ) -> Dict[str, any]:
        """
        Process uploaded audio file with streaming, validation, and conversion
        
        Args:
            upload_file: FastAPI UploadFile object
            channel_id: Channel ID for storage organization
            episode_title: Episode title for filename generation
            
        Returns:
            Dict with processing results: {
                'file_path': str,  # Relative path to final audio file
                'file_size': int,  # File size in bytes
                'duration_seconds': int,  # Audio duration
                'mime_type': str,  # Final MIME type
                'original_filename': str  # Original uploaded filename
            }
            
        Raises:
            FileValidationError: If file validation fails
            FileConversionError: If audio conversion fails
        """
        start_time = time.time()
        temp_file_path = None
        final_file_path = None
        
        try:
            logger.info(f"Starting upload processing for channel {channel_id}: {upload_file.filename}")
            
            # Sanitize original filename
            original_filename = self.media_file_service.sanitize_filename(upload_file.filename)
            
            # Generate temporary filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            temp_filename = f"upload_{channel_id}_{timestamp}_{original_filename}"
            temp_file_path = self.temp_path / temp_filename
            
            # Stream file to disk
            logger.info(f"Streaming upload to temp file: {temp_file_path}")
            await self._stream_file_to_disk(upload_file, temp_file_path)
            
            # Validate audio file
            logger.info(f"Validating audio file: {temp_file_path}")
            validation_result = self.media_file_service.validate_audio_file(
                str(temp_file_path),
                max_size_mb=settings.max_upload_file_size_mb
            )
            
            mime_type = validation_result['mime_type']
            file_size = validation_result['file_size']
            
            # Extract metadata
            logger.info(f"Extracting audio metadata from: {temp_file_path}")
            metadata = self.media_file_service.extract_audio_metadata(str(temp_file_path))
            duration_seconds = metadata['duration_seconds']
            
            # Determine if conversion is needed
            needs_conversion = self._needs_conversion(mime_type)
            
            # Process file (convert or move)
            if needs_conversion:
                logger.info(f"Converting audio file from {mime_type} to MP3")
                final_file_path = await self._convert_and_store(
                    temp_file_path,
                    channel_id,
                    episode_title,
                    timestamp
                )
                final_mime_type = "audio/mpeg"
            else:
                logger.info(f"Moving audio file to final storage (no conversion needed)")
                final_file_path = await self._move_to_storage(
                    temp_file_path,
                    channel_id,
                    episode_title,
                    timestamp,
                    mime_type
                )
                final_mime_type = mime_type
            
            # Get final file size (may have changed after conversion)
            final_file_size = os.path.getsize(final_file_path)
            
            # Calculate relative path from media root
            relative_path = final_file_path.relative_to(self.media_path)
            
            # Clean up temp file if it still exists
            if temp_file_path and temp_file_path.exists():
                try:
                    os.remove(temp_file_path)
                    logger.debug(f"Cleaned up temp file: {temp_file_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temp file {temp_file_path}: {e}")
            
            processing_duration = time.time() - start_time
            logger.info(
                f"Upload processing completed in {processing_duration:.2f}s: "
                f"{relative_path}, size={final_file_size / (1024 * 1024):.2f}MB, "
                f"duration={duration_seconds}s"
            )
            
            return {
                'file_path': str(relative_path),
                'file_size': final_file_size,
                'duration_seconds': duration_seconds,
                'mime_type': final_mime_type,
                'original_filename': original_filename,
                'processing_duration_ms': int(processing_duration * 1000)
            }
            
        except (FileValidationError, FileConversionError):
            # Clean up temp file on error
            if temp_file_path and temp_file_path.exists():
                try:
                    os.remove(temp_file_path)
                    logger.debug(f"Cleaned up temp file after error: {temp_file_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temp file {temp_file_path}: {e}")
            raise
        except Exception as e:
            # Clean up temp file on unexpected error
            if temp_file_path and temp_file_path.exists():
                try:
                    os.remove(temp_file_path)
                except:
                    pass
            logger.error(f"Unexpected error processing upload: {e}")
            raise FileValidationError(
                f"Failed to process uploaded file: {str(e)}",
                details={'error': str(e)}
            )
    
    async def _stream_file_to_disk(self, upload_file: UploadFile, dest_path: Path) -> None:
        """
        Stream uploaded file to disk using 8KB chunks for memory efficiency
        
        Args:
            upload_file: FastAPI UploadFile object
            dest_path: Destination file path
        """
        try:
            async with aiofiles.open(dest_path, 'wb') as f:
                while True:
                    chunk = await upload_file.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    await f.write(chunk)
            
            logger.debug(f"Streamed file to disk: {dest_path}, size={os.path.getsize(dest_path)} bytes")
            
        except Exception as e:
            logger.error(f"Error streaming file to disk: {e}")
            raise FileValidationError(
                f"Failed to save uploaded file: {str(e)}",
                details={'error': str(e), 'dest_path': str(dest_path)}
            )
    
    def _needs_conversion(self, mime_type: str) -> bool:
        """
        Determine if audio file needs conversion based on MIME type
        
        Args:
            mime_type: MIME type of the audio file
            
        Returns:
            True if conversion needed, False otherwise
        """
        # MP3 files never need conversion
        if mime_type == 'audio/mpeg':
            return False
        
        # M4A files don't need conversion if preserve_m4a is True
        if mime_type in ['audio/mp4', 'audio/x-m4a'] and settings.preserve_m4a:
            return False
        
        # All other formats need conversion
        return settings.convert_uploads_to_target
    
    async def _convert_and_store(
        self,
        source_path: Path,
        channel_id: int,
        episode_title: str,
        timestamp: str
    ) -> Path:
        """
        Convert audio file to MP3 using FFmpeg and store in final location
        
        Args:
            source_path: Path to source audio file
            channel_id: Channel ID for storage organization
            episode_title: Episode title for filename
            timestamp: Timestamp for unique filename
            
        Returns:
            Path to final converted file
            
        Raises:
            FileConversionError: If FFmpeg conversion fails
        """
        try:
            # Generate output filename
            safe_title = self.media_file_service.sanitize_filename(episode_title)
            output_filename = f"{safe_title}_{timestamp}.mp3"
            
            # Create channel directory
            channel_dir = self.media_path / f"channel_{channel_id}"
            channel_dir.mkdir(parents=True, exist_ok=True)
            
            output_path = channel_dir / output_filename
            
            # FFmpeg command for MP3 conversion
            # Using VBR quality 2 (~190 kbps)
            ffmpeg_cmd = [
                'ffmpeg',
                '-i', str(source_path),
                '-vn',  # No video
                '-ar', '44100',  # Sample rate
                '-ac', '2',  # Stereo
                '-b:a', f'{settings.target_audio_quality}k',  # Bitrate
                '-y',  # Overwrite output file
                str(output_path)
            ]
            
            logger.info(f"Running FFmpeg conversion: {' '.join(ffmpeg_cmd)}")
            
            # Run FFmpeg conversion
            process = await asyncio.create_subprocess_exec(
                *ffmpeg_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_output = stderr.decode('utf-8') if stderr else 'Unknown error'
                logger.error(f"FFmpeg conversion failed: {error_output}")
                raise FileConversionError(
                    f"Audio conversion failed: {error_output}",
                    ffmpeg_output=error_output,
                    details={'return_code': process.returncode, 'source': str(source_path)}
                )
            
            logger.info(f"FFmpeg conversion successful: {output_path}")
            
            return output_path
            
        except FileConversionError:
            raise
        except Exception as e:
            logger.error(f"Error during audio conversion: {e}")
            raise FileConversionError(
                f"Failed to convert audio file: {str(e)}",
                details={'error': str(e), 'source': str(source_path)}
            )
    
    async def _move_to_storage(
        self,
        source_path: Path,
        channel_id: int,
        episode_title: str,
        timestamp: str,
        mime_type: str
    ) -> Path:
        """
        Move audio file to final storage location without conversion
        
        Args:
            source_path: Path to source audio file
            channel_id: Channel ID for storage organization
            episode_title: Episode title for filename
            timestamp: Timestamp for unique filename
            mime_type: MIME type to determine file extension
            
        Returns:
            Path to final file
        """
        try:
            # Determine file extension from MIME type
            extension_map = {
                'audio/mpeg': '.mp3',
                'audio/mp4': '.m4a',
                'audio/x-m4a': '.m4a',
                'audio/wav': '.wav',
                'audio/x-wav': '.wav',
                'audio/wave': '.wav',
                'audio/ogg': '.ogg',
                'audio/flac': '.flac',
                'audio/x-flac': '.flac'
            }
            
            extension = extension_map.get(mime_type, '.mp3')
            
            # Generate output filename
            safe_title = self.media_file_service.sanitize_filename(episode_title)
            output_filename = f"{safe_title}_{timestamp}{extension}"
            
            # Create channel directory
            channel_dir = self.media_path / f"channel_{channel_id}"
            channel_dir.mkdir(parents=True, exist_ok=True)
            
            output_path = channel_dir / output_filename
            
            # Move file to final location
            source_path.rename(output_path)
            
            logger.info(f"Moved file to storage: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error moving file to storage: {e}")
            raise FileValidationError(
                f"Failed to move file to storage: {str(e)}",
                details={'error': str(e), 'source': str(source_path)}
            )


