"""
Channel Settings API Endpoints (Simplified)
"""
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from fastapi.responses import FileResponse, RedirectResponse
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import os
from pathlib import Path
import shutil
import uuid

from app.core.dependencies import get_database_session
from app.infrastructure.database.models import ChannelModel, EpisodeModel
from app.presentation.schemas.channel_schemas_simple import (
    ChannelCreateRequest, ChannelUpdateRequest, ChannelResponse,
    ChannelStatisticsResponse
)
from app.core.config import settings

router = APIRouter(prefix="/channels", tags=["channels"])


@router.post("/", response_model=ChannelResponse)
def create_channel(
    request: ChannelCreateRequest,
    db: Session = Depends(get_database_session)
):
    """
    Create a new podcast channel
    """
    try:
        # Create channel model with enhanced schema
        channel_model = ChannelModel(
            user_id=request.user_id,
            name=request.name,
            description=request.description,
            website_url=request.website_url,  # Now required
            image_url=None,
            category="Technology",
            language="en",
            explicit_content=True,  # Default to True as per plan
            author_name=request.author_name or "",
            author_email=request.author_email,
            owner_name=request.author_name or "",
            owner_email=request.author_email,
            feed_url="",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(channel_model)
        db.commit()
        db.refresh(channel_model)
        
        return ChannelResponse.model_validate(channel_model)
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating channel: {str(e)}")


@router.get("/", response_model=List[ChannelResponse])
def list_channels(
    user_id: Optional[int] = Query(default=None, description="Filter channels by user ID"),
    search: Optional[str] = Query(default=None, description="Search channels by name or description"),
    limit: int = Query(default=50, le=200, description="Maximum number of channels to return"),
    db: Session = Depends(get_database_session)
):
    """
    List channels with optional filtering
    """
    try:
        query = db.query(ChannelModel)
        
        if user_id:
            query = query.filter(ChannelModel.user_id == user_id)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (ChannelModel.name.ilike(search_term)) |
                (ChannelModel.description.ilike(search_term))
            )
        
        channels = query.limit(limit).all()
        
        return [ChannelResponse.model_validate(channel) for channel in channels]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing channels: {str(e)}")


@router.get("/{channel_id}", response_model=ChannelResponse)
def get_channel(
    channel_id: int,
    db: Session = Depends(get_database_session)
):
    """
    Get channel by ID
    """
    channel = db.get(ChannelModel, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    return ChannelResponse.model_validate(channel)


@router.put("/{channel_id}", response_model=ChannelResponse)
def update_channel(
    channel_id: int,
    request: ChannelUpdateRequest,
    db: Session = Depends(get_database_session)
):
    """
    Update channel settings and RSS feed configuration
    """
    try:
        channel = db.get(ChannelModel, channel_id)
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        # Update fields
        update_data = request.model_dump(exclude_none=True)
        for field, value in update_data.items():
            if hasattr(channel, field):
                setattr(channel, field, value)
        
        channel.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(channel)
        
        return ChannelResponse.model_validate(channel)
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating channel: {str(e)}")


@router.delete("/{channel_id}")
def delete_channel(
    channel_id: int,
    db: Session = Depends(get_database_session)
):
    """
    Delete channel and all its episodes
    """
    try:
        channel = db.get(ChannelModel, channel_id)
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        # Delete associated episodes first
        db.query(EpisodeModel).filter(EpisodeModel.channel_id == channel_id).delete()
        
        # Delete the channel
        db.delete(channel)
        db.commit()
        
        return {"message": "Channel deleted successfully"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting channel: {str(e)}")


@router.get("/{channel_id}/statistics", response_model=ChannelStatisticsResponse)
def get_channel_statistics(
    channel_id: int,
    db: Session = Depends(get_database_session)
):
    """
    Get channel statistics and RSS feed information
    """
    channel = db.get(ChannelModel, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    # Count episodes by status
    total_episodes = db.query(EpisodeModel).filter(EpisodeModel.channel_id == channel_id).count()
    published_episodes = db.query(EpisodeModel).filter(
        EpisodeModel.channel_id == channel_id,
        EpisodeModel.status == "published"
    ).count()
    draft_episodes = db.query(EpisodeModel).filter(
        EpisodeModel.channel_id == channel_id,
        EpisodeModel.status == "draft"
    ).count()
    processing_episodes = db.query(EpisodeModel).filter(
        EpisodeModel.channel_id == channel_id,
        EpisodeModel.status == "processing"
    ).count()
    
    # Get latest episode
    latest_episode = db.query(EpisodeModel).filter(
        EpisodeModel.channel_id == channel_id,
        EpisodeModel.status == "published"
    ).order_by(EpisodeModel.publication_date.desc()).first()
    
    # Calculate total duration and size
    episodes = db.query(EpisodeModel).filter(
        EpisodeModel.channel_id == channel_id,
        EpisodeModel.status == "published"
    ).all()

    total_duration = sum(ep.duration or 0 for ep in episodes)
    total_size = sum(ep.file_size or 0 for ep in episodes)

    # Count unique YouTube channels
    unique_youtube_channels = db.query(EpisodeModel.youtube_channel_id)\
        .filter(EpisodeModel.channel_id == channel_id)\
        .filter(EpisodeModel.youtube_channel_id.isnot(None))\
        .filter(EpisodeModel.youtube_channel_id != "")\
        .distinct().count()
    
    return ChannelStatisticsResponse(
        channel_id=channel_id,
        channel_name=channel.name,
        total_episodes=total_episodes,
        published_episodes=published_episodes,
        draft_episodes=draft_episodes,
        processing_episodes=processing_episodes,
        total_duration_seconds=total_duration,
        total_size_bytes=total_size,
        unique_youtube_channels=unique_youtube_channels,
        feed_validation_score=None,  # Not available in current schema
        feed_last_updated=None,  # Not available in current schema
        latest_episode={
            'title': latest_episode.title,
            'publication_date': latest_episode.publication_date,
            'duration': latest_episode.duration
        } if latest_episode else None,
        created_at=channel.created_at,
        updated_at=channel.updated_at
    )


@router.post("/{channel_id}/upload-image")
async def upload_channel_image(
    channel_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_database_session)
):
    """
    Upload channel image
    """
    try:
        # Verify channel exists
        channel = db.get(ChannelModel, channel_id)
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")

        # Validate file type
        allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
            )

        # Validate file size (max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB
        file_size = 0
        content = await file.read()
        file_size = len(content)

        if file_size > max_size:
            raise HTTPException(
                status_code=400,
                detail="File too large. Maximum size is 5MB"
            )

        # Create channel images directory
        media_path = Path(settings.media_path)
        channel_images_dir = media_path / f"channel_{channel_id}" / "images"
        channel_images_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        file_extension = file.filename.split(".")[-1] if file.filename else "jpg"
        unique_filename = f"channel_image_{uuid.uuid4().hex}.{file_extension}"
        file_path = channel_images_dir / unique_filename

        # Save file
        await file.seek(0)  # Reset file pointer
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Update channel with iTunes-compliant image URL (with .png extension)
        relative_path = f"channel_{channel_id}/images/{unique_filename}"
        # Use .png extension for iTunes compliance regardless of actual file type
        image_url = f"/v1/channels/{channel_id}/image.png"

        channel.image_url = image_url
        channel.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(channel)

        return {
            "message": "Image uploaded successfully",
            "image_url": image_url,
            "filename": unique_filename,
            "file_size": file_size
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading image: {str(e)}"
        )


@router.get("/{channel_id}/image.png")
@router.get("/{channel_id}/image.jpg")
async def get_channel_image_with_extension(
    channel_id: int,
    db: Session = Depends(get_database_session)
):
    """
    Get channel image with iTunes-compliant file extension
    This endpoint serves the actual image file for iTunes compliance
    """
    return await _serve_channel_image(channel_id, db)


@router.get("/{channel_id}/image")
async def get_channel_image(
    channel_id: int,
    db: Session = Depends(get_database_session)
):
    """
    Get channel image (legacy endpoint - redirects to .png for iTunes compliance)
    """
    # Redirect to iTunes-compliant URL with .png extension
    return RedirectResponse(url=f"/v1/channels/{channel_id}/image.png", status_code=301)


async def _serve_channel_image(
    channel_id: int,
    db: Session
):
    """
    Internal helper to serve channel image file
    """
    try:
        channel = db.get(ChannelModel, channel_id)
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")

        # Find the image file
        media_path = Path(settings.media_path)
        channel_images_dir = media_path / f"channel_{channel_id}" / "images"

        if not channel_images_dir.exists():
            raise HTTPException(status_code=404, detail="Channel image not found")

        # Find the most recent image file
        image_files = list(channel_images_dir.glob("channel_image_*"))
        if not image_files:
            raise HTTPException(status_code=404, detail="Channel image not found")

        # Get the most recent image
        latest_image = max(image_files, key=lambda x: x.stat().st_mtime)

        # Determine content type
        extension = latest_image.suffix.lower()
        content_type_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp'
        }
        content_type = content_type_map.get(extension, 'image/jpeg')

        return FileResponse(
            path=latest_image,
            media_type=content_type,
            headers={"Cache-Control": "public, max-age=3600"}
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving image: {str(e)}"
        )