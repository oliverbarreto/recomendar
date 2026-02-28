#!/usr/bin/env python3
"""
Follow Channel Feature Test Script
Comprehensive testing of the follow channel and video discovery feature
"""
import asyncio
import sys
import os
from datetime import datetime
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.domain.entities.followed_channel import FollowedChannel, SubscriptionCheckFrequency
from app.domain.entities.youtube_video import YouTubeVideo, YouTubeVideoState
from app.domain.entities.user_settings import UserSettings
from app.infrastructure.services.youtube_metadata_service_impl import YouTubeMetadataServiceImpl
from app.infrastructure.services.channel_discovery_service_impl import ChannelDiscoveryServiceImpl
from app.infrastructure.repositories.followed_channel_repository_impl import FollowedChannelRepositoryImpl
from app.infrastructure.repositories.youtube_video_repository_impl import YouTubeVideoRepositoryImpl
from app.infrastructure.repositories.user_settings_repository_impl import UserSettingsRepositoryImpl
from app.infrastructure.database.connection import get_background_task_session
from app.application.services.followed_channel_service import FollowedChannelService
from app.application.services.youtube_video_service import YouTubeVideoService
from app.application.services.user_settings_service import UserSettingsService
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_youtube_metadata_extraction():
    """Test YouTube metadata extraction using yt-dlp"""
    logger.info("=" * 60)
    logger.info("Test 1: YouTube Metadata Extraction")
    logger.info("=" * 60)
    
    try:
        metadata_service = YouTubeMetadataServiceImpl()
        
        # Test with a real YouTube video URL
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll (safe test video)
        logger.info(f"Extracting metadata from: {test_url}")
        
        metadata = await metadata_service.extract_video_metadata(test_url)
        
        # Validate metadata
        assert metadata is not None, "Metadata should not be None"
        assert "title" in metadata, "Metadata should contain title"
        assert "video_id" in metadata, "Metadata should contain video_id"
        assert metadata["video_id"] == "dQw4w9WgXcQ", "Video ID should match"
        
        logger.info(f"✓ Title: {metadata.get('title')}")
        logger.info(f"✓ Video ID: {metadata.get('video_id')}")
        logger.info(f"✓ Duration: {metadata.get('duration')} seconds")
        logger.info(f"✓ Views: {metadata.get('view_count')}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ YouTube metadata extraction test failed: {e}", exc_info=True)
        return False


async def test_channel_listing():
    """Test listing videos from a YouTube channel"""
    logger.info("=" * 60)
    logger.info("Test 2: Channel Video Listing")
    logger.info("=" * 60)
    
    try:
        metadata_service = YouTubeMetadataServiceImpl()
        
        # Test with a real YouTube channel URL
        # Using a small channel for faster testing
        test_channel_url = "https://www.youtube.com/@RickAstleyYT"  # Rick Astley's channel
        logger.info(f"Listing videos from channel: {test_channel_url}")
        
        videos = await metadata_service.list_channel_videos(
            channel_url=test_channel_url,
            max_videos=5,
            year=None
        )
        
        assert videos is not None, "Videos list should not be None"
        assert len(videos) > 0, "Should find at least one video"
        assert "video_id" in videos[0], "Video should have video_id"
        assert "title" in videos[0], "Video should have title"
        
        logger.info(f"✓ Found {len(videos)} videos")
        for i, video in enumerate(videos[:3], 1):
            logger.info(f"  {i}. {video.get('title', 'Unknown')} ({video.get('video_id', 'N/A')})")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Channel listing test failed: {e}", exc_info=True)
        return False


async def test_video_state_transitions():
    """Test YouTube video state transitions"""
    logger.info("=" * 60)
    logger.info("Test 3: Video State Transitions")
    logger.info("=" * 60)
    
    try:
        # Create a test video entity (without database)
        video = YouTubeVideo(
            id=None,
            video_id="test_video_123",
            followed_channel_id=1,
            title="Test Video",
            description="Test description",
            url="https://www.youtube.com/watch?v=test_video_123",
            state=YouTubeVideoState.PENDING_REVIEW
        )
        
        # Test state transitions
        assert video.state == YouTubeVideoState.PENDING_REVIEW, "Initial state should be PENDING_REVIEW"
        
        # Test: PENDING_REVIEW -> REVIEWED
        video.mark_as_reviewed()
        assert video.state == YouTubeVideoState.REVIEWED, "State should be REVIEWED"
        assert video.reviewed_at is not None, "reviewed_at should be set"
        
        # Reset for next test
        video.state = YouTubeVideoState.PENDING_REVIEW
        video.reviewed_at = None
        
        # Test: PENDING_REVIEW -> QUEUED
        video.queue_for_episode_creation()
        assert video.state == YouTubeVideoState.QUEUED, "State should be QUEUED"
        
        # Test: QUEUED -> DOWNLOADING
        video.mark_as_downloading()
        assert video.state == YouTubeVideoState.DOWNLOADING, "State should be DOWNLOADING"
        
        # Test: DOWNLOADING -> EPISODE_CREATED
        video.mark_as_episode_created(episode_id=123)
        assert video.state == YouTubeVideoState.EPISODE_CREATED, "State should be EPISODE_CREATED"
        assert video.episode_id == 123, "episode_id should be set"
        
        # Test: PENDING_REVIEW -> DISCARDED
        video2 = YouTubeVideo(
            id=None,
            video_id="test_video_456",
            followed_channel_id=1,
            title="Test Video 2",
            state=YouTubeVideoState.PENDING_REVIEW
        )
        video2.mark_as_discarded()
        assert video2.state == YouTubeVideoState.DISCARDED, "State should be DISCARDED"
        
        logger.info("✓ All state transitions validated")
        return True
        
    except Exception as e:
        logger.error(f"✗ State transitions test failed: {e}", exc_info=True)
        return False


async def test_followed_channel_entity():
    """Test FollowedChannel entity creation and validation"""
    logger.info("=" * 60)
    logger.info("Test 4: FollowedChannel Entity")
    logger.info("=" * 60)
    
    try:
        # Create a test followed channel
        channel = FollowedChannel(
            id=None,
            user_id=1,
            youtube_channel_id="UCuAXFkgsw1L7xaCfnd5JJOw",
            youtube_channel_name="Test Channel",
            youtube_channel_url="https://www.youtube.com/@testchannel",
            auto_approve=False,
            auto_approve_channel_id=None
        )
        
        assert channel.user_id == 1, "user_id should be set"
        assert channel.youtube_channel_id == "UCuAXFkgsw1L7xaCfnd5JJOw", "youtube_channel_id should be set"
        assert channel.auto_approve is False, "auto_approve should be False by default"
        assert channel.created_at is not None, "created_at should be set"
        assert channel.updated_at is not None, "updated_at should be set"
        
        # Test with auto-approve enabled
        channel2 = FollowedChannel(
            id=None,
            user_id=1,
            youtube_channel_id="UCuAXFkgsw1L7xaCfnd5JJOw",
            youtube_channel_name="Test Channel 2",
            youtube_channel_url="https://www.youtube.com/@testchannel2",
            auto_approve=True,
            auto_approve_channel_id=5
        )
        
        assert channel2.auto_approve is True, "auto_approve should be True"
        assert channel2.auto_approve_channel_id == 5, "auto_approve_channel_id should be set"
        
        logger.info("✓ FollowedChannel entity validation passed")
        return True
        
    except Exception as e:
        logger.error(f"✗ FollowedChannel entity test failed: {e}", exc_info=True)
        return False


async def test_user_settings_entity():
    """Test UserSettings entity"""
    logger.info("=" * 60)
    logger.info("Test 5: UserSettings Entity")
    logger.info("=" * 60)
    
    try:
        # Create test user settings
        settings = UserSettings(
            id=None,
            user_id=1,
            subscription_check_frequency=SubscriptionCheckFrequency.DAILY
        )
        
        assert settings.user_id == 1, "user_id should be set"
        assert settings.subscription_check_frequency == SubscriptionCheckFrequency.DAILY, "frequency should be DAILY"
        assert settings.created_at is not None, "created_at should be set"
        
        # Test different frequencies
        settings2 = UserSettings(
            id=None,
            user_id=2,
            subscription_check_frequency=SubscriptionCheckFrequency.WEEKLY
        )
        assert settings2.subscription_check_frequency == SubscriptionCheckFrequency.WEEKLY, "frequency should be WEEKLY"
        
        logger.info("✓ UserSettings entity validation passed")
        return True
        
    except Exception as e:
        logger.error(f"✗ UserSettings entity test failed: {e}", exc_info=True)
        return False


async def test_celery_task_imports():
    """Test that Celery tasks can be imported"""
    logger.info("=" * 60)
    logger.info("Test 6: Celery Task Imports")
    logger.info("=" * 60)
    
    try:
        from app.infrastructure.tasks.channel_check_tasks import (
            check_followed_channel_for_new_videos,
            periodic_check_all_channels,
            test_task
        )
        from app.infrastructure.tasks.backfill_channel_task import backfill_followed_channel
        from app.infrastructure.tasks.create_episode_from_video_task import create_episode_from_youtube_video
        
        assert check_followed_channel_for_new_videos is not None, "check_followed_channel_for_new_videos should be importable"
        assert periodic_check_all_channels is not None, "periodic_check_all_channels should be importable"
        assert backfill_followed_channel is not None, "backfill_followed_channel should be importable"
        assert create_episode_from_youtube_video is not None, "create_episode_from_youtube_video should be importable"
        assert test_task is not None, "test_task should be importable"
        
        logger.info("✓ All Celery tasks imported successfully")
        return True
        
    except Exception as e:
        logger.error(f"✗ Celery task import test failed: {e}", exc_info=True)
        return False


async def test_domain_services():
    """Test domain service interfaces"""
    logger.info("=" * 60)
    logger.info("Test 7: Domain Service Interfaces")
    logger.info("=" * 60)
    
    try:
        from app.domain.services.youtube_metadata_service import YouTubeMetadataServiceInterface
        from app.domain.services.channel_discovery_service import ChannelDiscoveryServiceInterface
        from app.domain.repositories.followed_channel_repository import FollowedChannelRepository
        from app.domain.repositories.youtube_video_repository import YouTubeVideoRepository
        from app.domain.repositories.user_settings_repository import UserSettingsRepository
        
        # Verify interfaces exist
        assert YouTubeMetadataServiceInterface is not None
        assert ChannelDiscoveryServiceInterface is not None
        assert FollowedChannelRepository is not None
        assert YouTubeVideoRepository is not None
        assert UserSettingsRepository is not None
        
        logger.info("✓ All domain interfaces imported successfully")
        return True
        
    except Exception as e:
        logger.error(f"✗ Domain service interface test failed: {e}", exc_info=True)
        return False


async def test_repository_interfaces():
    """Test repository interfaces"""
    logger.info("=" * 60)
    logger.info("Test 8: Repository Interfaces")
    logger.info("=" * 60)
    
    try:
        from app.domain.repositories.followed_channel_repository import FollowedChannelRepository
        from app.domain.repositories.youtube_video_repository import YouTubeVideoRepository
        from app.domain.repositories.user_settings_repository import UserSettingsRepository
        
        # Check that repository methods are defined
        assert hasattr(FollowedChannelRepository, 'get_by_id')
        assert hasattr(FollowedChannelRepository, 'get_by_user_id')
        assert hasattr(YouTubeVideoRepository, 'get_by_id')
        assert hasattr(YouTubeVideoRepository, 'get_by_video_id')
        assert hasattr(UserSettingsRepository, 'get_or_create_default')
        
        logger.info("✓ All repository interfaces validated")
        return True
        
    except Exception as e:
        logger.error(f"✗ Repository interface test failed: {e}", exc_info=True)
        return False


async def run_all_tests():
    """Run all follow channel feature tests"""
    logger.info("=" * 70)
    logger.info("FOLLOW CHANNEL FEATURE TEST SUITE")
    logger.info("=" * 70)
    
    tests = [
        ("YouTube Metadata Extraction", test_youtube_metadata_extraction),
        ("Channel Video Listing", test_channel_listing),
        ("Video State Transitions", test_video_state_transitions),
        ("FollowedChannel Entity", test_followed_channel_entity),
        ("UserSettings Entity", test_user_settings_entity),
        ("Celery Task Imports", test_celery_task_imports),
        ("Domain Service Interfaces", test_domain_services),
        ("Repository Interfaces", test_repository_interfaces),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*70}")
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            logger.error(f"✗ {test_name} failed with exception: {e}", exc_info=True)
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("TEST SUMMARY")
    logger.info("=" * 70)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        logger.info(f"{test_name:.<50} {status}")
        if success:
            passed += 1
    
    logger.info(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("\n🎉 ALL FOLLOW CHANNEL FEATURE TESTS PASSED!")
        logger.info("✓ YouTube metadata extraction")
        logger.info("✓ Channel video listing")
        logger.info("✓ Video state transitions")
        logger.info("✓ Domain entities")
        logger.info("✓ Celery task imports")
        logger.info("✓ Domain service interfaces")
        logger.info("✓ Repository interfaces")
        return True
    else:
        logger.warning(f"\n⚠️  {total - passed} tests failed. Please review the implementation.")
        return False


if __name__ == "__main__":
    # Run the validation
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

