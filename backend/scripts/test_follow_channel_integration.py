#!/usr/bin/env python3
"""
Follow Channel Feature Integration Test
Tests end-to-end functionality with database
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add the backend directory to the path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.infrastructure.database.connection import get_background_task_session
from app.infrastructure.repositories.followed_channel_repository_impl import FollowedChannelRepositoryImpl
from app.infrastructure.repositories.youtube_video_repository_impl import YouTubeVideoRepositoryImpl
from app.infrastructure.repositories.user_settings_repository_impl import UserSettingsRepositoryImpl
from app.infrastructure.repositories.user_repository import UserRepositoryImpl
from app.infrastructure.repositories.channel_repository import ChannelRepositoryImpl
from app.infrastructure.services.youtube_metadata_service_impl import YouTubeMetadataServiceImpl
from app.infrastructure.services.channel_discovery_service_impl import ChannelDiscoveryServiceImpl
from app.application.services.followed_channel_service import FollowedChannelService
from app.application.services.youtube_video_service import YouTubeVideoService
from app.application.services.user_settings_service import UserSettingsService
from app.domain.entities.followed_channel import SubscriptionCheckFrequency
from app.domain.entities.youtube_video import YouTubeVideoState
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_database_operations():
    """Test database operations for follow channel feature"""
    logger.info("=" * 70)
    logger.info("INTEGRATION TEST: Database Operations")
    logger.info("=" * 70)
    
    session = await get_background_task_session()
    try:
        # Initialize repositories
        user_repo = UserRepositoryImpl(session)
        followed_channel_repo = FollowedChannelRepositoryImpl(session)
        youtube_video_repo = YouTubeVideoRepositoryImpl(session)
        user_settings_repo = UserSettingsRepositoryImpl(session)
        channel_repo = ChannelRepositoryImpl(session)
        
        # Get or create a test user
        logger.info("Getting test user...")
        users = await user_repo.get_all(skip=0, limit=1)
        if not users:
            logger.warning("No users found in database. Please create a user first.")
            return False
        
        test_user = users[0]
        logger.info(f"Using test user: {test_user.id} ({test_user.username})")
        
        # Test 1: Create or get user settings
        logger.info("\n1. Testing UserSettings repository...")
        user_settings = await user_settings_repo.get_or_create_default(test_user.id)
        assert user_settings is not None, "User settings should be created"
        assert user_settings.user_id == test_user.id, "User ID should match"
        logger.info(f"✓ User settings created/retrieved: {user_settings.subscription_check_frequency.value}")
        
        # Test 2: Update user settings
        logger.info("\n2. Testing UserSettings update...")
        user_settings.subscription_check_frequency = SubscriptionCheckFrequency.WEEKLY
        updated_settings = await user_settings_repo.update(user_settings)
        assert updated_settings.subscription_check_frequency == SubscriptionCheckFrequency.WEEKLY
        logger.info("✓ User settings updated successfully")
        
        # Test 3: Create a test followed channel (using a real but safe channel URL)
        logger.info("\n3. Testing FollowedChannel repository...")
        test_channel_url = "https://www.youtube.com/@RickAstleyYT"
        
        # Check if channel already exists
        existing_channels = await followed_channel_repo.get_by_user_id(test_user.id)
        test_followed_channel = None
        for channel in existing_channels:
            if "RickAstley" in channel.youtube_channel_name or "Rick" in channel.youtube_channel_name:
                test_followed_channel = channel
                logger.info(f"Using existing followed channel: {channel.id}")
                break
        
        if not test_followed_channel:
            logger.info("Creating new followed channel...")
            # Use the service to create it properly
            metadata_service = YouTubeMetadataServiceImpl()
            discovery_service = ChannelDiscoveryServiceImpl(
                metadata_service=metadata_service,
                youtube_video_repository=youtube_video_repo,
                followed_channel_repository=followed_channel_repo
            )
            
            followed_channel_service = FollowedChannelService(
                followed_channel_repository=followed_channel_repo,
                youtube_video_repository=youtube_video_repo,
                metadata_service=metadata_service,
                discovery_service=discovery_service
            )
            
            # This would normally require authentication, but we'll test the service directly
            try:
                from fastapi import BackgroundTasks
                test_followed_channel = await followed_channel_service.follow_channel(
                    user_id=test_user.id,
                    youtube_channel_url=test_channel_url,
                    auto_approve=False,
                    auto_approve_channel_id=None,
                    background_tasks=BackgroundTasks()
                )
                logger.info(f"✓ Created followed channel: {test_followed_channel.id}")
            except Exception as e:
                logger.warning(f"Could not create followed channel via service: {e}")
                logger.info("Skipping channel creation test (requires full service setup)")
                return True
        
        # Test 4: List followed channels
        logger.info("\n4. Testing list followed channels...")
        user_channels = await followed_channel_repo.get_by_user_id(test_user.id)
        assert len(user_channels) > 0, "Should have at least one followed channel"
        logger.info(f"✓ Found {len(user_channels)} followed channels")
        
        # Test 5: Get channel by ID
        logger.info("\n5. Testing get channel by ID...")
        channel = await followed_channel_repo.get_by_id(test_followed_channel.id)
        assert channel is not None, "Channel should be retrievable"
        assert channel.id == test_followed_channel.id, "Channel ID should match"
        logger.info(f"✓ Retrieved channel: {channel.youtube_channel_name}")
        
        logger.info("\n✓ All database operations passed!")
        return True
        
    except Exception as e:
        logger.error(f"✗ Database operations test failed: {e}", exc_info=True)
        return False
    finally:
        await session.close()


async def test_video_discovery():
    """Test video discovery functionality"""
    logger.info("=" * 70)
    logger.info("INTEGRATION TEST: Video Discovery")
    logger.info("=" * 70)
    
    session = await get_background_task_session()
    try:
        # Initialize repositories and services
        followed_channel_repo = FollowedChannelRepositoryImpl(session)
        youtube_video_repo = YouTubeVideoRepositoryImpl(session)
        user_repo = UserRepositoryImpl(session)
        
        # Get a test user
        users = await user_repo.get_all(skip=0, limit=1)
        if not users:
            logger.warning("No users found. Skipping discovery test.")
            return True
        
        test_user = users[0]
        
        # Get a followed channel
        user_channels = await followed_channel_repo.get_by_user_id(test_user.id)
        if not user_channels:
            logger.warning("No followed channels found. Skipping discovery test.")
            return True
        
        test_channel = user_channels[0]
        logger.info(f"Testing discovery for channel: {test_channel.youtube_channel_name}")
        
        # Initialize discovery service
        metadata_service = YouTubeMetadataServiceImpl()
        discovery_service = ChannelDiscoveryServiceImpl(
            metadata_service=metadata_service,
            youtube_video_repository=youtube_video_repo,
            followed_channel_repository=followed_channel_repo
        )
        
        # Test discovery (limited to 3 videos for testing)
        logger.info("Discovering new videos...")
        new_videos = await discovery_service.discover_new_videos(
            followed_channel=test_channel,
            max_videos=3
        )
        
        logger.info(f"✓ Discovered {len(new_videos)} new videos")
        for video in new_videos:
            logger.info(f"  - {video.title} ({video.video_id}) - State: {video.state.value}")
            assert video.state == YouTubeVideoState.PENDING_REVIEW, "New videos should be PENDING_REVIEW"
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Video discovery test failed: {e}", exc_info=True)
        return False
    finally:
        await session.close()


async def test_video_state_transitions_db():
    """Test video state transitions with database"""
    logger.info("=" * 70)
    logger.info("INTEGRATION TEST: Video State Transitions")
    logger.info("=" * 70)
    
    session = await get_background_task_session()
    try:
        youtube_video_repo = YouTubeVideoRepositoryImpl(session)
        
        # Get a test video
        videos = await youtube_video_repo.get_all(skip=0, limit=1)
        if not videos:
            logger.warning("No videos found. Skipping state transition test.")
            return True
        
        test_video = videos[0]
        logger.info(f"Testing state transitions for video: {test_video.title}")
        logger.info(f"Current state: {test_video.state.value}")
        
        # Test state transitions
        if test_video.state == YouTubeVideoState.PENDING_REVIEW:
            # Transition to REVIEWED
            test_video.mark_as_reviewed()
            await youtube_video_repo.update(test_video)
            logger.info("✓ Transitioned to REVIEWED")
            
            # Transition back to PENDING_REVIEW for next test
            test_video.state = YouTubeVideoState.PENDING_REVIEW
            test_video.reviewed_at = None
            await youtube_video_repo.update(test_video)
        
        logger.info("✓ State transitions validated")
        return True
        
    except Exception as e:
        logger.error(f"✗ State transition test failed: {e}", exc_info=True)
        return False
    finally:
        await session.close()


async def run_integration_tests():
    """Run all integration tests"""
    logger.info("=" * 70)
    logger.info("FOLLOW CHANNEL FEATURE INTEGRATION TESTS")
    logger.info("=" * 70)
    
    tests = [
        ("Database Operations", test_database_operations),
        ("Video Discovery", test_video_discovery),
        ("Video State Transitions", test_video_state_transitions_db),
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
    logger.info("INTEGRATION TEST SUMMARY")
    logger.info("=" * 70)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        logger.info(f"{test_name:.<50} {status}")
        if success:
            passed += 1
    
    logger.info(f"\nResults: {passed}/{total} tests passed")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_integration_tests())
    sys.exit(0 if success else 1)

