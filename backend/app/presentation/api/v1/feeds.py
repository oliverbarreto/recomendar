"""
RSS Feed API Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Response, Query
from fastapi.responses import PlainTextResponse
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.dependencies import get_database_session
from app.core.config import settings
from app.infrastructure.database.models import ChannelModel, EpisodeModel
from app.infrastructure.services.feed_generation_service_impl import FeedGenerationServiceImpl
from app.infrastructure.services.itunes_validator import iTunesValidator
from app.domain.entities.channel import Channel
from app.domain.entities.episode import Episode, EpisodeStatus
from app.domain.value_objects.video_id import VideoId
from app.domain.value_objects.duration import Duration
from app.presentation.schemas.feed_schemas import (
    FeedValidationResponse, FeedInfoResponse
)

router = APIRouter(prefix="/feeds", tags=["feeds"])


@router.get("/{channel_id}/feed.xml", response_class=PlainTextResponse)
def get_rss_feed(
    channel_id: int,
    db: Session = Depends(get_database_session),
    limit: Optional[int] = Query(default=50, le=200, description="Maximum number of episodes to include")
):
    """
    Generate and serve RSS feed for a channel
    
    Returns iTunes-compliant RSS feed XML
    """
    # Get channel from database
    channel_model = db.get(ChannelModel, channel_id)
    if not channel_model:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    # Convert to domain entity
    channel = Channel(
        id=channel_model.id,
        user_id=channel_model.user_id,
        name=channel_model.name,
        description=channel_model.description,
        website_url=channel_model.website_url,
        image_url=channel_model.image_url,
        category=channel_model.category,
        language=channel_model.language,
        explicit_content=channel_model.explicit_content,
        author_name=channel_model.author_name,
        author_email=channel_model.author_email,
        owner_name=channel_model.owner_name,
        owner_email=channel_model.owner_email,
        feed_url=channel_model.feed_url,
        feed_last_updated=None,  # Default for missing field
        feed_validation_score=None,  # Default for missing field
        copyright=None,  # Default for missing field
        podcast_type="episodic",  # Default for missing field
        subcategory=None,  # Default for missing field
        created_at=channel_model.created_at,
        updated_at=channel_model.updated_at
    )
    
    # Get completed episodes for this channel (completed = ready for feed)
    # Order by created_at (when user added to channel) not publication_date (YouTube date)
    episode_models = db.query(EpisodeModel)\
        .filter(EpisodeModel.channel_id == channel_id)\
        .filter(EpisodeModel.status == "completed")\
        .order_by(EpisodeModel.created_at.desc())\
        .limit(limit)\
        .all()
    
    # Convert to domain entities
    episodes = []
    for ep_model in episode_models:
        episode = Episode(
            id=ep_model.id,
            channel_id=ep_model.channel_id,
            video_id=VideoId(ep_model.video_id),
            title=ep_model.title,
            description=ep_model.description,
            video_url=ep_model.video_url or "",
            audio_file_path=ep_model.audio_file_path,
            duration=Duration(ep_model.duration_seconds) if ep_model.duration_seconds else None,
            status=EpisodeStatus(ep_model.status),
            publication_date=ep_model.publication_date,
            created_at=ep_model.created_at,
            updated_at=ep_model.updated_at,
            youtube_channel=ep_model.youtube_channel,
            youtube_channel_id=ep_model.youtube_channel_id,
            youtube_channel_url=ep_model.youtube_channel_url,
            is_favorited=ep_model.is_favorited or False
        )
        episodes.append(episode)
    
    # Generate RSS feed
    feed_service = FeedGenerationServiceImpl()
    base_url = settings.base_url
    
    try:
        feed_xml = feed_service.generate_rss_feed(channel, episodes, base_url)
        
        # Note: feed_last_updated field not available in current schema
        # Would update timestamp here when field is added
        
        return Response(
            content=feed_xml,
            media_type="application/rss+xml",
            headers={
                "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
                "Content-Disposition": f'inline; filename="channel_{channel_id}_feed.xml"'
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating RSS feed: {str(e)}")


@router.post("/{channel_id}/validate")
def validate_feed(
    channel_id: int,
    db: Session = Depends(get_database_session)
) -> FeedValidationResponse:
    """
    Validate RSS feed against iTunes specifications
    
    Returns detailed validation report with score, errors, warnings, and recommendations
    """
    # Get channel from database
    channel_model = db.get(ChannelModel, channel_id)
    if not channel_model:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    # Convert to domain entity
    channel = Channel(
        id=channel_model.id,
        user_id=channel_model.user_id,
        name=channel_model.name,
        description=channel_model.description,
        website_url=channel_model.website_url,
        image_url=channel_model.image_url,
        category=channel_model.category,
        language=channel_model.language,
        explicit_content=channel_model.explicit_content,
        author_name=channel_model.author_name,
        author_email=channel_model.author_email,
        owner_name=channel_model.owner_name,
        owner_email=channel_model.owner_email,
        feed_url=channel_model.feed_url,
        feed_last_updated=None,  # Default for missing field
        feed_validation_score=None,  # Default for missing field
        copyright=None,  # Default for missing field
        podcast_type="episodic",  # Default for missing field
        subcategory=None,  # Default for missing field
        created_at=channel_model.created_at,
        updated_at=channel_model.updated_at
    )
    
    # Get published episodes
    # Order by created_at (when user added to channel) not publication_date (YouTube date)
    episode_models = db.query(EpisodeModel)\
        .filter(EpisodeModel.channel_id == channel_id)\
        .filter(EpisodeModel.status == "completed")\
        .order_by(EpisodeModel.created_at.desc())\
        .all()
    
    # Convert to domain entities
    episodes = []
    for ep_model in episode_models:
        episode = Episode(
            id=ep_model.id,
            channel_id=ep_model.channel_id,
            video_id=VideoId(ep_model.video_id),
            title=ep_model.title,
            description=ep_model.description,
            video_url=ep_model.video_url or "",
            audio_file_path=ep_model.audio_file_path,
            duration=Duration(ep_model.duration_seconds) if ep_model.duration_seconds else None,
            status=EpisodeStatus(ep_model.status),
            publication_date=ep_model.publication_date,
            created_at=ep_model.created_at,
            updated_at=ep_model.updated_at,
            youtube_channel=ep_model.youtube_channel,
            youtube_channel_id=ep_model.youtube_channel_id,
            youtube_channel_url=ep_model.youtube_channel_url,
            is_favorited=ep_model.is_favorited or False
        )
        episodes.append(episode)
    
    # Generate and validate feed
    feed_service = FeedGenerationServiceImpl()
    validator = iTunesValidator()
    base_url = settings.base_url
    
    try:
        # Generate feed XML
        feed_xml = feed_service.generate_rss_feed(channel, episodes, base_url)
        
        # Validate feed
        validation_result = validator.validate_full_feed(feed_xml)
        
        # Note: feed_validation_score field not available in current schema
        # Would update score here when field is added
        
        return FeedValidationResponse(
            channel_id=channel_id,
            is_valid=validation_result['is_valid'],
            score=validation_result['score'],
            errors=validation_result['errors'],
            warnings=validation_result['warnings'],
            recommendations=validation_result['recommendations'],
            validation_details=validation_result['validation_details'],
            validated_at=channel_model.updated_at
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating feed: {str(e)}")


@router.get("/{channel_id}/info")
def get_feed_info(
    channel_id: int,
    db: Session = Depends(get_database_session),
    response: Response = None
) -> FeedInfoResponse:
    """
    Get feed information and metadata
    """
    # Get channel from database
    channel_model = db.get(ChannelModel, channel_id)
    if not channel_model:
        raise HTTPException(status_code=404, detail="Channel not found")

    # Count published episodes
    episode_count = db.query(EpisodeModel)\
        .filter(EpisodeModel.channel_id == channel_id)\
        .filter(EpisodeModel.status == "completed")\
        .count()

    # Get most recent episode (by when user added it, not YouTube publication date)
    latest_episode = db.query(EpisodeModel)\
        .filter(EpisodeModel.channel_id == channel_id)\
        .filter(EpisodeModel.status == "completed")\
        .order_by(EpisodeModel.created_at.desc())\
        .first()

    # Set cache control headers to prevent browser caching
    if response:
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

    return FeedInfoResponse(
        channel_id=channel_id,
        channel_name=channel_model.name,
        feed_url=f"{settings.base_url}/v1/feeds/{channel_id}/feed.xml",
        episode_count=episode_count,
        last_updated=None,  # Not available in current schema
        validation_score=None,  # Not available in current schema
        latest_episode_title=latest_episode.title if latest_episode else None,
        latest_episode_date=latest_episode.publication_date if latest_episode else None
    )


@router.get("/")
def list_feeds(
    db: Session = Depends(get_database_session)
) -> List[FeedInfoResponse]:
    """
    List all available RSS feeds
    """
    # Get all channels with published episodes
    channels = db.query(ChannelModel).all()
    
    feeds = []
    for channel_model in channels:
        # Count episodes for this channel
        episode_count = db.query(EpisodeModel)\
            .filter(EpisodeModel.channel_id == channel_model.id)\
            .filter(EpisodeModel.status == "completed")\
            .count()
        
        # Get latest episode for this channel (by when user added it, not YouTube publication date)
        latest_episode = db.query(EpisodeModel)\
            .filter(EpisodeModel.channel_id == channel_model.id)\
            .filter(EpisodeModel.status == "completed")\
            .order_by(EpisodeModel.created_at.desc())\
            .first()
        
        feed_info = FeedInfoResponse(
            channel_id=channel_model.id,
            channel_name=channel_model.name,
            feed_url=f"{settings.base_url}/v1/feeds/{channel_model.id}/feed.xml",
            episode_count=episode_count,
            last_updated=None,  # Not available in current schema
            validation_score=None,  # Not available in current schema
            latest_episode_title=latest_episode.title if latest_episode else None,
            latest_episode_date=latest_episode.publication_date if latest_episode else None
        )
        feeds.append(feed_info)
    
    return feeds