"""
Application configuration settings
"""
from pydantic_settings import BaseSettings
from typing import Optional, List
import os
from pathlib import Path


def _detect_environment() -> str:
    """
    Detect the current environment based on various indicators
    """
    # Check explicit environment variable first (highest priority)
    env = os.environ.get('ENVIRONMENT', '').lower()
    if env in ['production', 'prod']:
        return 'production'
    elif env in ['development', 'dev']:
        return 'development'

    # Check if running in Docker (fallback)
    if os.path.exists('/.dockerenv') or os.environ.get('RUNNING_IN_DOCKER'):
        return 'production'  # Default Docker deployments to production

    # Default to development for local runs
    return 'development'


def _get_env_file_path() -> str:
    """
    Get the appropriate .env file path based on environment
    """
    current_env = _detect_environment()
    root_path = Path(__file__).parent.parent.parent

    if current_env == 'development':
        # Check for local .env file first, then fall back to root
        local_env = root_path / '.env.local'
        if local_env.exists():
            return str(local_env)
    elif current_env == 'production':
        # Use production environment file for production deployments
        prod_env = root_path / '.env.production'
        if prod_env.exists():
            return str(prod_env)

    # Use root-level .env file as fallback for all environments
    return str(root_path / '.env')


class Settings(BaseSettings):
    # Application settings
    app_name: str = "LabCastARR API"
    app_version: str = "0.1.0"
    debug: bool = False

    # Environment detection
    environment: str = _detect_environment()

    # Database settings
    database_url: str = "sqlite:///./data/labcastarr.db"

    # API settings
    api_key_secret: Optional[str] = None
    api_key_header: str = "X-API-Key"

    # iOS Shortcut API settings
    shortcut_api_key: Optional[str] = None
    shortcut_api_key_header: str = "X-Shortcut-Key"

    # Security settings
    enable_api_key_auth: bool = True
    rate_limit_requests: int = 1000  # Increased for development
    rate_limit_period: int = 60  # seconds
    allowed_hosts: list[str] = ["localhost", "127.0.0.1", "0.0.0.0"]  # Can be overridden by ALLOWED_HOSTS env var
    security_headers_enabled: bool = True

    # JWT Authentication settings
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60  # Extended from 15 to 60 minutes for better UX
    jwt_refresh_token_expire_days: int = 30  # Standard refresh token expiration (30 days)
    jwt_refresh_token_extended_expire_days: int = 90  # Extended expiration for "remember me" (90 days)

    # Media settings
    media_path: str = "./media"
    feeds_path: str = "./feeds"
    temp_path: str = "./media/temp"
    max_storage_gb: int = 100
    cleanup_orphaned_files: bool = True

    # YouTube Integration settings
    ytdlp_path: str = "yt-dlp"
    max_concurrent_downloads: int = 3
    download_timeout_minutes: int = 30
    default_audio_quality: str = "bestaudio"
    audio_format: str = "mp3"

    # File Upload settings
    max_upload_file_size_mb: int = 500
    allowed_upload_formats: List[str] = ["mp3", "m4a", "wav", "ogg", "flac"]
    target_audio_format: str = "mp3"
    target_audio_quality: str = "192"  # kbps for MP3
    convert_uploads_to_target: bool = True
    preserve_m4a: bool = True  # Don't convert M4A files

    # Background Task settings
    task_retry_attempts: int = 3
    task_retry_backoff_base: int = 2
    task_queue_size: int = 50
    task_cleanup_interval: str = "1h"

    # Celery and Redis settings
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: Optional[str] = None  # Defaults to redis_url if not set
    celery_result_backend: Optional[str] = None  # Defaults to redis_url if not set
    celery_task_serializer: str = "json"
    celery_result_serializer: str = "json"
    celery_accept_content: List[str] = ["json"]
    celery_timezone: str = "UTC"
    celery_enable_utc: bool = True

    # External API settings - will be overridden by env file
    cors_origins: List[str] = ["http://localhost:3000"]  # Default for development, overridden by CORS_ORIGINS env var

    # Domain and URL settings - will be overridden by env file based on environment
    domain: str = "localhost"
    base_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"

    # Default Channel settings (used when creating the default channel on first startup)
    default_channel_name: str = "My Podcast Channel"
    default_channel_description: str = "Convert YouTube videos to podcast episodes with LabCastARR"
    default_channel_website_url: Optional[str] = None
    default_channel_image_url: Optional[str] = None
    default_channel_category: str = "Technology"
    default_channel_language: str = "en"
    default_channel_explicit_content: bool = False
    default_channel_author_name: str = "LabCastARR User"
    default_channel_author_email: Optional[str] = None
    default_channel_owner_name: Optional[str] = None
    default_channel_owner_email: Optional[str] = None
    default_channel_feed_url: Optional[str] = None

    # Default User settings (used when creating the default user)
    default_user_name: str = "LabCastARR User"
    default_user_email: str = "user@labcastarr.local"
    default_user_password: str = "labcastarr123"  # This will be hashed

    # Logging settings
    log_level: str = "INFO"
    log_file_path: str = "./logs/labcastarr.log"
    log_max_file_size: int = 10  # MB
    log_backup_count: int = 5
    enable_file_logging: bool = False  # Enable for development, always True for production
    enable_request_logging: bool = True
    enable_performance_logging: bool = True
    log_sql_queries: bool = False  # Enable for debugging database issues
    
    class Config:
        env_file = _get_env_file_path()  # Dynamic env file based on environment
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra environment variables


# Global settings instance
settings = Settings()