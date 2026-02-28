"""
Core application dependencies
"""
from functools import lru_cache
from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.infrastructure.database.connection import get_db, get_async_db
from app.core.config import settings
from app.infrastructure.repositories.episode_repository import EpisodeRepositoryImpl
from app.infrastructure.repositories.followed_channel_repository_impl import FollowedChannelRepositoryImpl
from app.infrastructure.repositories.youtube_video_repository_impl import YouTubeVideoRepositoryImpl
from app.infrastructure.repositories.user_settings_repository_impl import UserSettingsRepositoryImpl
from app.infrastructure.repositories.channel_repository import ChannelRepositoryImpl
from app.infrastructure.repositories.notification_repository_impl import NotificationRepositoryImpl
from app.infrastructure.repositories.celery_task_status_repository_impl import CeleryTaskStatusRepository
from app.application.services.episode_service import EpisodeService
from app.application.services.url_validation_service import URLValidationService
from app.application.services.metadata_processing_service import MetadataProcessingService
from app.application.services.followed_channel_service import FollowedChannelService
from app.application.services.youtube_video_service import YouTubeVideoService
from app.application.services.user_settings_service import UserSettingsService
from app.application.services.notification_service import NotificationService
from app.infrastructure.services.youtube_service import YouTubeService
from app.infrastructure.services.youtube_metadata_service_impl import YouTubeMetadataServiceImpl
from app.infrastructure.services.channel_discovery_service_impl import ChannelDiscoveryServiceImpl
from app.infrastructure.services.file_service import FileService
from app.infrastructure.services.download_service import DownloadService
from app.infrastructure.services.media_file_service import MediaFileService
from app.application.services.upload_processing_service import UploadProcessingService

logger = logging.getLogger(__name__)

# Global service instances
_youtube_service = None
_file_service = None
_url_validation_service = None
_metadata_processing_service = None
_download_service = None
_media_file_service = None
_upload_processing_service = None


def get_settings():
    """
    Dependency to get application settings
    """
    return settings


def get_database_session(db: Session = Depends(get_db)) -> Session:
    """
    Dependency to get database session
    """
    return db


@lru_cache()
def get_youtube_service() -> YouTubeService:
    """Get YouTube service instance"""
    global _youtube_service
    if _youtube_service is None:
        _youtube_service = YouTubeService()
        logger.info("Initialized YouTube service")
    return _youtube_service


@lru_cache()
def get_file_service() -> FileService:
    """Get file service instance"""
    global _file_service
    if _file_service is None:
        _file_service = FileService()
        logger.info("Initialized file service")
    return _file_service


@lru_cache()
def get_url_validation_service() -> URLValidationService:
    """Get URL validation service instance"""
    global _url_validation_service
    if _url_validation_service is None:
        _url_validation_service = URLValidationService()
        logger.info("Initialized URL validation service")
    return _url_validation_service


@lru_cache()
def get_metadata_processing_service() -> MetadataProcessingService:
    """Get metadata processing service instance"""
    global _metadata_processing_service
    if _metadata_processing_service is None:
        _metadata_processing_service = MetadataProcessingService()
        logger.info("Initialized metadata processing service")
    return _metadata_processing_service


def get_episode_repository(db_session: AsyncSession = Depends(get_async_db)) -> EpisodeRepositoryImpl:
    """Get episode repository instance"""
    return EpisodeRepositoryImpl(db_session)


def get_episode_service(
    episode_repository: EpisodeRepositoryImpl = Depends(get_episode_repository),
    metadata_service: MetadataProcessingService = Depends(get_metadata_processing_service),
    youtube_service: YouTubeService = Depends(get_youtube_service)
) -> EpisodeService:
    """Get episode service instance"""
    return EpisodeService(episode_repository, metadata_service, youtube_service)


@lru_cache()
def get_media_file_service() -> MediaFileService:
    """Get media file service instance"""
    global _media_file_service
    if _media_file_service is None:
        _media_file_service = MediaFileService()
        logger.info("Initialized media file service")
    return _media_file_service


@lru_cache()
def get_upload_processing_service(
    media_file_service: MediaFileService = Depends(get_media_file_service)
) -> UploadProcessingService:
    """Get upload processing service instance"""
    global _upload_processing_service
    if _upload_processing_service is None:
        _upload_processing_service = UploadProcessingService(media_file_service)
        logger.info("Initialized upload processing service")
    return _upload_processing_service


def get_download_service(
    youtube_service: YouTubeService = Depends(get_youtube_service),
    file_service: FileService = Depends(get_file_service),
    episode_repository: EpisodeRepositoryImpl = Depends(get_episode_repository)
) -> DownloadService:
    """Get download service instance"""
    global _download_service
    if _download_service is None:
        _download_service = DownloadService(youtube_service, file_service, episode_repository)
        logger.info("Initialized download service")
    return _download_service


# Type aliases for dependency injection
EpisodeRepositoryDep = Annotated[EpisodeRepositoryImpl, Depends(get_episode_repository)]
EpisodeServiceDep = Annotated[EpisodeService, Depends(get_episode_service)]
YouTubeServiceDep = Annotated[YouTubeService, Depends(get_youtube_service)]
FileServiceDep = Annotated[FileService, Depends(get_file_service)]
URLValidationServiceDep = Annotated[URLValidationService, Depends(get_url_validation_service)]
MetadataProcessingServiceDep = Annotated[MetadataProcessingService, Depends(get_metadata_processing_service)]
DownloadServiceDep = Annotated[DownloadService, Depends(get_download_service)]


# Follow Channel Feature Dependencies

def get_followed_channel_repository(
    db_session: AsyncSession = Depends(get_async_db)
) -> FollowedChannelRepositoryImpl:
    """Get followed channel repository instance"""
    return FollowedChannelRepositoryImpl(db_session)


def get_youtube_video_repository(
    db_session: AsyncSession = Depends(get_async_db)
) -> YouTubeVideoRepositoryImpl:
    """Get YouTube video repository instance"""
    return YouTubeVideoRepositoryImpl(db_session)


def get_user_settings_repository(
    db_session: AsyncSession = Depends(get_async_db)
) -> UserSettingsRepositoryImpl:
    """Get user settings repository instance"""
    return UserSettingsRepositoryImpl(db_session)


def get_channel_repository(
    db_session: AsyncSession = Depends(get_async_db)
) -> ChannelRepositoryImpl:
    """Get channel repository instance"""
    return ChannelRepositoryImpl(db_session)


@lru_cache()
def get_youtube_metadata_service() -> YouTubeMetadataServiceImpl:
    """Get YouTube metadata service instance"""
    return YouTubeMetadataServiceImpl()


def get_channel_discovery_service(
    metadata_service: YouTubeMetadataServiceImpl = Depends(get_youtube_metadata_service),
    youtube_video_repository: YouTubeVideoRepositoryImpl = Depends(get_youtube_video_repository),
    followed_channel_repository: FollowedChannelRepositoryImpl = Depends(get_followed_channel_repository)
) -> ChannelDiscoveryServiceImpl:
    """Get channel discovery service instance"""
    return ChannelDiscoveryServiceImpl(
        metadata_service=metadata_service,
        youtube_video_repository=youtube_video_repository,
        followed_channel_repository=followed_channel_repository
    )


def get_task_status_repository(
    db_session: AsyncSession = Depends(get_async_db)
) -> CeleryTaskStatusRepository:
    """Get Celery task status repository instance"""
    return CeleryTaskStatusRepository(db_session)


def get_followed_channel_service(
    followed_channel_repository: FollowedChannelRepositoryImpl = Depends(get_followed_channel_repository),
    youtube_video_repository: YouTubeVideoRepositoryImpl = Depends(get_youtube_video_repository),
    metadata_service: YouTubeMetadataServiceImpl = Depends(get_youtube_metadata_service),
    discovery_service: ChannelDiscoveryServiceImpl = Depends(get_channel_discovery_service),
    task_status_repository: CeleryTaskStatusRepository = Depends(get_task_status_repository)
) -> FollowedChannelService:
    """Get followed channel service instance"""
    return FollowedChannelService(
        followed_channel_repository=followed_channel_repository,
        youtube_video_repository=youtube_video_repository,
        metadata_service=metadata_service,
        discovery_service=discovery_service,
        task_status_repository=task_status_repository
    )


def get_youtube_video_service(
    youtube_video_repository: YouTubeVideoRepositoryImpl = Depends(get_youtube_video_repository),
    followed_channel_repository: FollowedChannelRepositoryImpl = Depends(get_followed_channel_repository),
    channel_repository: ChannelRepositoryImpl = Depends(get_channel_repository)
) -> YouTubeVideoService:
    """Get YouTube video service instance"""
    return YouTubeVideoService(
        youtube_video_repository=youtube_video_repository,
        followed_channel_repository=followed_channel_repository,
        channel_repository=channel_repository
    )


def get_user_settings_service(
    user_settings_repository: UserSettingsRepositoryImpl = Depends(get_user_settings_repository)
) -> UserSettingsService:
    """Get user settings service instance"""
    return UserSettingsService(user_settings_repository)


def get_notification_repository(
    db_session: AsyncSession = Depends(get_async_db)
) -> NotificationRepositoryImpl:
    """Get notification repository instance"""
    return NotificationRepositoryImpl(db_session)


def get_notification_service(
    notification_repository: NotificationRepositoryImpl = Depends(get_notification_repository)
) -> NotificationService:
    """Get notification service instance"""
    return NotificationService(notification_repository)


# Type aliases for dependency injection
FollowedChannelServiceDep = Annotated[FollowedChannelService, Depends(get_followed_channel_service)]
YouTubeVideoServiceDep = Annotated[YouTubeVideoService, Depends(get_youtube_video_service)]
UserSettingsServiceDep = Annotated[UserSettingsService, Depends(get_user_settings_service)]
NotificationRepositoryDep = Annotated[NotificationRepositoryImpl, Depends(get_notification_repository)]
NotificationServiceDep = Annotated[NotificationService, Depends(get_notification_service)]