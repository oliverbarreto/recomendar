"""
Media serving API endpoints for audio files and thumbnails
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse, Response
from pathlib import Path
import os
from typing import Optional, Generator
import aiofiles
import logging
import re

from app.application.services.episode_service import EpisodeService
from app.infrastructure.services.file_service import FileService
from app.core.dependencies import get_episode_service, get_file_service
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/media", tags=["media"])


async def _serve_audio_file(episode, request: Request) -> FileResponse | StreamingResponse:
    """
    Internal helper to serve audio file with range support

    Args:
        episode: Episode entity with audio_file_path
        request: HTTP request object for range header support

    Returns:
        FileResponse or StreamingResponse with audio file
    """
    # Get full file path
    media_path = Path(settings.media_path)
    file_path = media_path / episode.audio_file_path

    if not file_path.exists():
        logger.error(f"Audio file not found: {file_path}")
        raise HTTPException(status_code=404, detail="Audio file not found")

    # Security check - ensure file is within media directory
    try:
        file_path.resolve().relative_to(media_path.resolve())
    except ValueError:
        logger.warning(f"Attempted access to file outside media directory: {file_path}")
        raise HTTPException(status_code=403, detail="Access denied")

    # Get file stats and detect actual MIME type
    file_size = file_path.stat().st_size
    content_type = detect_audio_mime_type(file_path)

    # Log warning if file is actually WebM (indicates conversion issue)
    if content_type == "video/webm":
        logger.warning(f"WebM file served as audio for episode {episode.id}: {file_path}")

    # Handle range requests for streaming
    range_header = request.headers.get("Range") if request else None

    if range_header:
        # Parse range header
        range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)
        if not range_match:
            raise HTTPException(status_code=400, detail="Invalid range header")

        start = int(range_match.group(1))
        end = int(range_match.group(2)) if range_match.group(2) else file_size - 1

        # Validate range
        if start >= file_size or end >= file_size or start > end:
            raise HTTPException(
                status_code=416,
                detail="Range not satisfiable",
                headers={"Content-Range": f"bytes */{file_size}"}
            )

        # Create streaming response
        chunk_size = min(8192, end - start + 1)

        def file_streamer() -> Generator[bytes, None, None]:
            with open(file_path, 'rb') as f:
                f.seek(start)
                remaining = end - start + 1

                while remaining:
                    chunk = f.read(min(chunk_size, remaining))
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk

        content_length = end - start + 1
        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(content_length),
            "Content-Type": content_type,
            "Cache-Control": "public, max-age=3600"
        }

        return StreamingResponse(
            file_streamer(),
            status_code=206,
            headers=headers,
            media_type=content_type
        )

    else:
        # Serve entire file
        headers = {
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
            "Cache-Control": "public, max-age=3600"
        }

        return FileResponse(
            path=file_path,
            media_type=content_type,
            filename=f"{episode.title}.mp3",
            headers=headers
        )


def detect_audio_mime_type(file_path: Path) -> str:
    """
    Detect MIME type based on file headers/content, not just extension
    """
    try:
        with open(file_path, 'rb') as f:
            header = f.read(12)

        # MP3 signatures
        if header.startswith(b'ID3'):  # ID3 tag
            return "audio/mpeg"
        if len(header) >= 2 and header[0] == 0xFF and header[1] in [0xFB, 0xFA, 0xF3]:  # MP3 frame header
            return "audio/mpeg"

        # M4A/AAC signatures
        if b'ftyp' in header[:12]:  # MP4/M4A container
            return "audio/mp4"

        # OGG Vorbis
        if header.startswith(b'OggS'):
            return "audio/ogg"

        # WAV signature
        if header.startswith(b'RIFF') and b'WAVE' in header:
            return "audio/wav"

        # WebM signature (for detecting incorrectly formatted files)
        if header.startswith(b'\x1a\x45\xdf\xa3'):
            return "video/webm"

        # Fallback to extension-based detection
        extension = file_path.suffix.lower()
        extension_map = {
            '.mp3': 'audio/mpeg',
            '.m4a': 'audio/mp4',
            '.aac': 'audio/aac',
            '.ogg': 'audio/ogg',
            '.wav': 'audio/wav',
            '.flac': 'audio/flac'
        }

        return extension_map.get(extension, "audio/mpeg")  # Default to MP3

    except Exception as e:
        logger.warning(f"Failed to detect MIME type for {file_path}: {e}")
        return "audio/mpeg"  # Safe fallback


@router.get("/episodes/by-video-id/{video_id}/audio")
async def serve_episode_audio_by_video_id(
    video_id: str,
    channel_id: int = 1,
    request: Request = None,
    episode_service: EpisodeService = Depends(get_episode_service),
    file_service: FileService = Depends(get_file_service)
):
    """
    Serve episode audio file by YouTube video ID with range support for streaming

    This is the RECOMMENDED endpoint for serving media files, as it provides
    permanent, cache-friendly URLs that don't break when episodes are deleted.

    The audio format is indicated via HTTP Content-Type headers, not URL extension.
    This provides clean, RESTful URLs that are future-proof for multiple audio formats.

    Args:
        video_id: YouTube video ID (11 characters)
        channel_id: Channel ID (defaults to 1, for backward compatibility)
        request: HTTP request object for range header support

    Returns:
        FileResponse or StreamingResponse with audio file and proper Content-Type header
    """
    try:
        # Validate and create VideoId value object
        from app.domain.value_objects.video_id import VideoId

        try:
            # Support both new prefixed format (yt_*, up_*) and legacy 11-char format
            # Legacy format: Auto-prefix with yt_ for backward compatibility
            if len(video_id) == 11 and not video_id.startswith(('yt_', 'up_')):
                logger.info(f"Legacy video_id format detected: {video_id}, converting to yt_{video_id}")
                video_id = f"yt_{video_id}"

            vid = VideoId(video_id)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid episode ID format: {video_id}. Must be yt_<11chars> or up_<11chars>"
            )

        # Get episode by video_id and channel_id
        episode = await episode_service.episode_repository.find_by_video_id_and_channel(
            video_id=vid,
            channel_id=channel_id
        )

        if not episode:
            raise HTTPException(
                status_code=404,
                detail=f"Episode not found for video ID: {video_id} in channel {channel_id}"
            )

        if not episode.audio_file_path:
            raise HTTPException(status_code=404, detail="Audio file not available")

        # Continue with existing audio serving logic
        return await _serve_audio_file(episode, request)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving audio for video ID {video_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to serve audio file"
        )


@router.get("/episodes/{episode_id}/audio")
@router.get("/episodes/{episode_id}/audio.mp3")
async def serve_episode_audio(
    episode_id: int,
    request: Request,
    episode_service: EpisodeService = Depends(get_episode_service),
    file_service: FileService = Depends(get_file_service)
):
    """
    Serve episode audio file with range support for streaming
    
    This endpoint supports both YouTube-sourced and uploaded episodes.
    For YouTube episodes, the /episodes/by-video-id/{video_id}/audio endpoint is preferred.
    For uploaded episodes (without video_id), this is the correct endpoint to use.
    """
    try:
        # Get episode
        episode = await episode_service.get_episode(episode_id)
        if not episode:
            raise HTTPException(status_code=404, detail="Episode not found")

        if not episode.audio_file_path:
            raise HTTPException(status_code=404, detail="Audio file not available")

        # Use the shared helper function
        response = await _serve_audio_file(episode, request)

        # Only add deprecation warning for YouTube episodes (those with video_id)
        # Uploaded episodes don't have video_id, so this is the correct endpoint for them
        if episode.video_id:
            logger.warning(
                f"DEPRECATED: Integer ID endpoint accessed for YouTube episode {episode_id}. "
                f"Please use /episodes/by-video-id/{episode.video_id.value}/audio for permanent URLs."
            )
            response.headers["X-Deprecation-Warning"] = (
                "This endpoint is deprecated for YouTube episodes. Use /episodes/by-video-id/{video_id}/audio instead."
            )
            response.headers["X-Preferred-Endpoint"] = (
                f"/v1/media/episodes/by-video-id/{episode.video_id.value}/audio"
            )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving audio for episode {episode_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to serve audio file"
        )


@router.options("/episodes/{episode_id}/audio")
@router.options("/episodes/{episode_id}/audio.mp3")
async def audio_options():
    """Handle CORS preflight requests for audio endpoints"""
    return Response(
        headers={
            "Allow": "GET, HEAD, OPTIONS",
            "Accept-Ranges": "bytes",
            "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
            "Access-Control-Allow-Headers": "Range, Content-Type, Authorization"
        }
    )

@router.head("/episodes/{episode_id}/audio")
@router.head("/episodes/{episode_id}/audio.mp3")
async def get_episode_audio_info(
    episode_id: int,
    episode_service: EpisodeService = Depends(get_episode_service)
):
    """
    Get audio file info without content (for checking availability)
    """
    try:
        episode = await episode_service.get_episode(episode_id)
        if not episode or not episode.audio_file_path:
            raise HTTPException(status_code=404, detail="Audio file not available")
        
        # Get file stats and detect actual MIME type
        media_path = Path(settings.media_path)
        file_path = media_path / episode.audio_file_path

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Audio file not found")

        file_size = file_path.stat().st_size
        content_type = detect_audio_mime_type(file_path)

        # Log warning if file is actually WebM (indicates conversion issue)
        if content_type == "video/webm":
            logger.warning(f"WebM file served as audio for episode {episode_id}: {file_path}")

        headers = {
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
            "Content-Type": content_type,
            "Cache-Control": "public, max-age=3600"
        }
        
        from fastapi import Response
        return Response(
            status_code=200,
            headers=headers,
            media_type=content_type
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting audio info for episode {episode_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get audio file info"
        )


@router.get("/episodes/{episode_id}/thumbnail")
async def serve_episode_thumbnail(
    episode_id: int,
    episode_service: EpisodeService = Depends(get_episode_service)
):
    """
    Serve episode thumbnail image
    """
    try:
        episode = await episode_service.get_episode(episode_id)
        if not episode:
            raise HTTPException(status_code=404, detail="Episode not found")
        
        if not episode.thumbnail_url:
            raise HTTPException(status_code=404, detail="Thumbnail not available")
        
        # For now, redirect to the original thumbnail URL
        # In production, you might want to cache/proxy these
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=episode.thumbnail_url, status_code=302)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving thumbnail for episode {episode_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to serve thumbnail"
        )


@router.get("/storage/stats")
async def get_storage_stats(
    file_service: FileService = Depends(get_file_service)
):
    """
    Get storage usage statistics
    """
    try:
        stats = file_service.get_storage_stats()
        
        return {
            "total_files": stats["total_files"],
            "total_size_bytes": stats["total_size_bytes"],
            "total_size_mb": round(stats["total_size_mb"], 2),
            "total_size_gb": round(stats["total_size_gb"], 2),
            "disk_total_gb": round(stats["disk_total"] / (1024**3), 2),
            "disk_used_gb": round(stats["disk_used"] / (1024**3), 2),
            "disk_free_gb": round(stats["disk_free"] / (1024**3), 2),
            "disk_usage_percent": round(stats["disk_usage_percent"], 1)
        }
    
    except Exception as e:
        logger.error(f"Error getting storage stats: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get storage statistics"
        )


@router.post("/storage/cleanup")
async def cleanup_orphaned_files(
    file_service: FileService = Depends(get_file_service),
    episode_service: EpisodeService = Depends(get_episode_service)
):
    """
    Clean up orphaned files that don't have corresponding episodes
    """
    try:
        # This would need the episode repository, so let's get it differently
        from app.core.dependencies import get_episode_repository
        from app.infrastructure.database.connection import get_db
        
        # For now, return a placeholder response
        # In a real implementation, you'd need to properly inject the repository
        
        return {
            "message": "Cleanup functionality available - requires proper repository injection",
            "cleaned_files": 0,
            "size_freed_mb": 0
        }
    
    except Exception as e:
        logger.error(f"Error during file cleanup: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to cleanup files"
        )