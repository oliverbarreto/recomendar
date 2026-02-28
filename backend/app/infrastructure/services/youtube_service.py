"""
YouTube service for downloading videos and extracting metadata using yt-dlp
"""
import yt_dlp
from typing import Dict, Any, Optional, Callable
import asyncio
import logging
import time
import copy
from pathlib import Path
from app.core.config import settings
from app.core.logging import get_downloader_logger, get_structured_logger
from app.infrastructure.services.logging_service import logging_service
from app.domain.value_objects.video_id import VideoId
from app.infrastructure.services.audio_format_selection_service import AudioFormatSelectionService

logger = get_downloader_logger()
structured_logger = get_structured_logger("downloader")


class YouTubeExtractionError(Exception):
    """Exception raised when YouTube metadata extraction fails"""
    pass


class YouTubeDownloadError(Exception):
    """Exception raised when YouTube download fails"""
    pass


class YouTubeService:
    """
    Service for interacting with YouTube via yt-dlp
    """
    
    def __init__(self):
        self.media_path = Path(settings.media_path)
        self.temp_path = Path(settings.temp_path)
        
        # Ensure directories exist
        self.media_path.mkdir(parents=True, exist_ok=True)
        self.temp_path.mkdir(parents=True, exist_ok=True)
        
        # Base yt-dlp options with proper audio extraction and anti-blocking measures
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            # Enable remote JS challenge solver for HLS multi-language formats
            'remote_components': ['ejs:github'],
            # Force audio-only download with MP3 conversion
            'format': 'bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio/best[height<=480]',
            'outtmpl': str(self.temp_path / 'downloads' / '%(id)s.%(ext)s'),
            # Post-processors for guaranteed MP3 conversion
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            # Ensure we get MP3 output
            'prefer_ffmpeg': True,
            'keepvideo': False,
            # Anti-blocking measures for YouTube
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            },
            # 🤖 Permissive extractor args: android_vr + web_safari expose HLS manifests
            # where YouTube serves dubbed multi-language audio tracks. skip=[] ensures
            # HLS/DASH are NOT skipped (skipping HLS was the root cause of missing languages).
            'extractor_args': {
                'youtube': {
                    'player_client': ['android_vr', 'web', 'web_safari'],
                    'skip': [],
                }
            },
            # Additional retry and timeout settings
            'retries': 3,
            'fragment_retries': 3,
            'socket_timeout': 30,
        }
    
    async def extract_metadata(self, url: str) -> Dict[str, Any]:
        """
        Extract video metadata without downloading

        Args:
            url: YouTube video URL

        Returns:
            Dictionary containing video metadata

        Raises:
            YouTubeExtractionError: If extraction fails
        """
        start_time = time.time()

        try:
            structured_logger.info(
                "Starting metadata extraction",
                url=url,
                operation="extract_metadata"
            )

            # Run yt-dlp extraction in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            metadata = await loop.run_in_executor(
                None,
                self._extract_metadata_sync,
                url
            )

            duration_ms = (time.time() - start_time) * 1000
            video_id = metadata.get('id')
            video_title = metadata.get('title', 'Unknown')

            structured_logger.info(
                "Metadata extraction completed successfully",
                url=url,
                video_id=video_id,
                video_title=video_title,
                duration_ms=round(duration_ms, 2),
                operation="extract_metadata"
            )

            # Log to external API service
            await logging_service.log_external_api_call(
                service="youtube",
                endpoint=url,
                method="GET",
                duration_ms=duration_ms,
                success=True,
                request_details={"operation": "metadata_extraction", "video_id": video_id}
            )

            return self._parse_metadata(metadata)

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            structured_logger.error(
                "Metadata extraction failed",
                url=url,
                error_message=str(e),
                duration_ms=round(duration_ms, 2),
                operation="extract_metadata"
            )

            # Log to external API service
            await logging_service.log_external_api_call(
                service="youtube",
                endpoint=url,
                method="GET",
                duration_ms=duration_ms,
                success=False,
                error_message=str(e),
                request_details={"operation": "metadata_extraction"}
            )

            raise YouTubeExtractionError(f"Failed to extract metadata: {e}")
    
    def _extract_metadata_sync(self, url: str) -> Dict[str, Any]:
        """
        Synchronous metadata extraction with permissive options to discover
        all available formats including HLS multi-language dubbed audio tracks.
        """
        opts = {
            'quiet': True,
            'no_warnings': True,
            'remote_components': ['ejs:github'],
            'extractor_args': {
                'youtube': {
                    'player_client': ['android_vr', 'web', 'web_safari'],
                    'skip': [],
                }
            },
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)
    
    async def download_audio(
        self,
        url: str,
        output_path: Optional[str] = None,
        progress_callback: Optional[Callable] = None,
        audio_language: Optional[str] = None,
        audio_quality: Optional[str] = None
    ) -> tuple:
        """
        Download audio file from YouTube

        Args:
            url: YouTube video URL
            output_path: Custom output path (optional)
            progress_callback: Callback for progress updates
            audio_language: Preferred audio language (ISO 639-1) or None
            audio_quality: Preferred audio quality tier ("low"/"medium"/"high") or None

        Returns:
            Tuple of (file_path, format_info) where format_info contains
            actual_language, actual_quality, fallback_occurred, fallback_reason

        Raises:
            YouTubeDownloadError: If download fails
        """
        try:
            need_custom_format = bool(audio_language or audio_quality)
            logger.info(
                f"Starting download for URL: {url} "
                f"(language={audio_language}, quality={audio_quality}, custom={need_custom_format})"
            )

            # Build format selector string using yt-dlp's native language filtering
            format_selection_service = AudioFormatSelectionService()
            format_selector, preferred_kbps = format_selection_service.build_format_selector(
                audio_language, audio_quality
            )

            if need_custom_format:
                # 🤖 Permissive opts matching the proven ytdlp-custom-audio-downloader:
                # - player_client includes android_vr + web_safari for HLS manifest access
                # - skip=[] ensures HLS dubbed audio tracks are visible
                # - remote_components solves YouTube JS challenges
                download_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'remote_components': ['ejs:github'],
                    'format': format_selector,
                    'outtmpl': str(self.temp_path / 'downloads' / '%(id)s.%(ext)s'),
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': preferred_kbps,
                    }],
                    'prefer_ffmpeg': True,
                    'keepvideo': False,
                    'http_headers': self.ydl_opts['http_headers'],
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['android_vr', 'web', 'web_safari'],
                            'skip': [],
                        }
                    },
                    'retries': 3,
                    'fragment_retries': 3,
                    'socket_timeout': 30,
                }
                logger.info(
                    f"[DOWNLOAD] Using permissive opts (android_vr+web+web_safari, skip=[]) "
                    f"with format selector: {format_selector}"
                )
            else:
                # Standard opts for default downloads (faster, restricted clients)
                download_opts = copy.deepcopy(self.ydl_opts)

            if output_path:
                download_opts['outtmpl'] = output_path
            if progress_callback:
                download_opts['progress_hooks'] = [progress_callback]

            # Download with fallback
            loop = asyncio.get_event_loop()
            try:
                file_path, info = await loop.run_in_executor(
                    None, self._download_audio_sync, url, download_opts
                )
            except YouTubeDownloadError as e:
                if need_custom_format:
                    # FALLBACK: custom format failed, retry with default opts
                    logger.warning(f"Custom format download failed, retrying with defaults: {e}")
                    fallback_opts = copy.deepcopy(self.ydl_opts)
                    if output_path:
                        fallback_opts['outtmpl'] = output_path
                    if progress_callback:
                        fallback_opts['progress_hooks'] = [progress_callback]
                    file_path, info = await loop.run_in_executor(
                        None, self._download_audio_sync, url, fallback_opts
                    )
                    return (file_path, {
                        'actual_language': None,
                        'actual_quality': None,
                        'fallback_occurred': True,
                        'fallback_reason': f"Custom format failed, used default: {e}",
                    })
                else:
                    raise

            # Determine actual language/quality from download result
            format_info = self._build_format_info(info, audio_language, audio_quality)

            logger.info(
                f"[DOWNLOAD] Complete for URL: {url}, "
                f"format_id={info.get('format_id')}, "
                f"format={info.get('format')}, "
                f"actual_language={format_info.get('actual_language')}, "
                f"fallback={format_info.get('fallback_occurred')}"
            )

            return (file_path, format_info)

        except Exception as e:
            logger.error(f"Failed to download audio from {url}: {e}")
            raise YouTubeDownloadError(f"Download failed: {e}")
    
    def _download_audio_sync(self, url: str, opts: Dict[str, Any]) -> tuple:
        """
        Synchronous audio download.

        Returns:
            Tuple of (file_path, info_dict) where info_dict contains metadata
            about the downloaded format including language field.
        """
        with yt_dlp.YoutubeDL(opts) as ydl:
            # Single call: extracts info AND downloads in one step.
            # This avoids mismatches between format analysis and download phases.
            info = ydl.extract_info(url, download=True)

        if not info:
            raise YouTubeDownloadError("Failed to extract video information")

        # Log the resolved format for debugging
        logger.info(
            f"[DOWNLOAD] yt-dlp resolved: format_id={info.get('format_id')}, "
            f"format={info.get('format')}, language={info.get('language')}, "
            f"ext={info.get('ext')}"
        )

        video_id = info.get('id')
        if not video_id:
            raise YouTubeDownloadError("Could not determine video ID")

        # Determine where the final MP3 file should be based on output template
        outtmpl = opts.get('outtmpl')
        default_template = str(self.temp_path / 'downloads' / '%(id)s.%(ext)s')

        # Handle yt-dlp's dictionary format for outtmpl
        if isinstance(outtmpl, dict):
            custom_template = outtmpl.get('default', default_template)
        elif isinstance(outtmpl, str):
            custom_template = outtmpl
        else:
            custom_template = default_template

        if custom_template != default_template:
            logger.debug(f"Using custom template: {custom_template}")
            final_file = Path(custom_template.replace('%(ext)s', 'mp3'))
        else:
            final_file = self.temp_path / 'downloads' / f"{video_id}.mp3"

        if not final_file.exists():
            logger.error(f"Expected MP3 file not found: {final_file}")
            raise YouTubeDownloadError("MP3 conversion failed - file not found")

        if not self._validate_audio_file(str(final_file)):
            logger.error(f"Downloaded file is not a valid MP3: {final_file}")
            raise YouTubeDownloadError("Downloaded file is not a valid MP3 audio file")

        return (str(final_file), info)
    
    def _validate_audio_file(self, file_path: str) -> bool:
        """
        Validate that the downloaded file is actually an MP3 audio file
        """
        try:
            # Check file exists
            if not Path(file_path).exists():
                return False

            # Read first few bytes to check file signature
            with open(file_path, 'rb') as f:
                header = f.read(12)

            # Check for MP3 file signatures
            # ID3 tag: starts with 'ID3'
            if header.startswith(b'ID3'):
                return True

            # MP3 frame header: starts with 0xFF followed by 0xFB, 0xFA, or 0xF3
            if len(header) >= 2 and header[0] == 0xFF and header[1] in [0xFB, 0xFA, 0xF3]:
                return True

            # Additional check for common MP3 patterns
            if b'mp3' in header.lower() or b'mpeg' in header.lower():
                return True

            logger.warning(f"File does not appear to be MP3. Header: {header.hex()}")
            return False

        except Exception as e:
            logger.error(f"Error validating audio file {file_path}: {e}")
            return False

    def _build_format_info(
        self,
        info: Dict[str, Any],
        requested_language: Optional[str],
        requested_quality: Optional[str]
    ) -> Dict[str, Any]:
        """
        Build format_info dict by inspecting what yt-dlp actually downloaded.

        Checks the info dict's language field to determine if the requested
        language was obtained or if fallback occurred.
        """
        # Determine actual language from the downloaded format
        actual_language = info.get('language')

        # For merged format downloads, check requested_formats for language
        requested_formats = info.get('requested_formats') or []
        for fmt in requested_formats:
            lang = fmt.get('language')
            if lang:
                actual_language = lang
                break

        # Quality is controlled by FFmpeg post-processor, so it matches request
        actual_quality = requested_quality

        fallback_occurred = False
        fallback_reason = None

        if requested_language:
            if actual_language and actual_language.startswith(requested_language):
                # Got the requested language
                logger.info(
                    f"[FORMAT_INFO] Language match: requested='{requested_language}', "
                    f"got='{actual_language}'"
                )
            elif actual_language:
                # Got a different language
                fallback_occurred = True
                fallback_reason = (
                    f"Requested language '{requested_language}' but "
                    f"downloaded '{actual_language}'"
                )
                logger.warning(f"[FORMAT_INFO] Language fallback: {fallback_reason}")
            else:
                # No language metadata on downloaded format
                fallback_reason = (
                    f"Requested language '{requested_language}' but "
                    f"no language metadata on downloaded format "
                    f"(format_id={info.get('format_id')})"
                )
                logger.info(f"[FORMAT_INFO] {fallback_reason}")

        return {
            'actual_language': actual_language,
            'actual_quality': actual_quality,
            'fallback_occurred': fallback_occurred,
            'fallback_reason': fallback_reason,
        }

    def _parse_metadata(self, info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse yt-dlp info into Episode-compatible format
        """
        return {
            'video_id': info.get('id'),
            'title': info.get('title', 'Untitled'),
            'description': info.get('description', ''),
            'duration_seconds': info.get('duration'),
            'publication_date': info.get('upload_date'),
            'video_url': info.get('webpage_url'),
            'thumbnail_url': info.get('thumbnail'),
            'uploader': info.get('uploader'),
            'uploader_id': info.get('uploader_id'),
            'view_count': info.get('view_count', 0),
            'like_count': info.get('like_count'),
            'keywords': info.get('tags', []),
            'categories': info.get('categories', []),
            'language': info.get('language'),
            'availability': info.get('availability'),
            # YouTube channel information (yt-dlp fields)
            'channel': info.get('channel'),  # Full name of the channel
            'channel_id': info.get('channel_id'),  # Id of the channel
            'channel_url': info.get('channel_url'),  # URL of the channel
        }
    
    async def check_video_availability(self, url: str) -> Dict[str, Any]:
        """
        Check if video is available for download
        
        Args:
            url: YouTube video URL
            
        Returns:
            Dictionary with availability info
        """
        try:
            metadata = await self.extract_metadata(url)
            
            availability = metadata.get('availability', 'unknown')
            is_available = availability in ['public', 'unlisted']
            
            return {
                'available': is_available,
                'availability': availability,
                'video_id': metadata.get('video_id'),
                'title': metadata.get('title'),
                'reason': None if is_available else f"Video is {availability}"
            }
            
        except YouTubeExtractionError as e:
            return {
                'available': False,
                'availability': 'error',
                'video_id': None,
                'title': None,
                'reason': str(e)
            }
    
    def validate_url(self, url: str) -> bool:
        """
        Quick validation of YouTube URL format
        """
        try:
            VideoId.from_url(url)
            return True
        except ValueError:
            return False
    
    def get_video_id(self, url: str) -> str:
        """
        Extract video ID from URL
        """
        try:
            video_id = VideoId.from_url(url)
            return video_id.value
        except ValueError as e:
            raise YouTubeExtractionError(f"Invalid YouTube URL: {e}")
    
    def get_audio_formats(self, url: str) -> Dict[str, Any]:
        """
        Get available audio formats for a video
        """
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'listformats': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                
                audio_formats = []
                for format_info in info.get('formats', []):
                    if format_info.get('acodec') != 'none':
                        audio_formats.append({
                            'format_id': format_info.get('format_id'),
                            'ext': format_info.get('ext'),
                            'acodec': format_info.get('acodec'),
                            'abr': format_info.get('abr'),
                            'filesize': format_info.get('filesize'),
                            'language': format_info.get('language'),
                        })
                
                return {
                    'video_id': info.get('id'),
                    'audio_formats': audio_formats
                }
                
        except Exception as e:
            raise YouTubeExtractionError(f"Failed to get formats: {e}")