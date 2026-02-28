"""
Initialization service for setting up default data on first startup
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
import logging

from app.core.config import settings
from app.domain.entities.user import User
from app.domain.entities.channel import Channel
from app.domain.value_objects.email import Email
from app.infrastructure.repositories.user_repository import UserRepositoryImpl
from app.infrastructure.repositories.channel_repository import ChannelRepositoryImpl
from app.infrastructure.database.connection import get_background_task_session
from app.application.services.user_migration_service import UserMigrationService

logger = logging.getLogger(__name__)


class InitializationService:
    """
    Service responsible for initializing default data when application starts fresh
    """

    def __init__(self):
        pass

    async def ensure_default_data(self) -> Dict[str, Any]:
        """
        Ensure default user and channel exist, create them if they don't.
        Also migrates existing users to match environment configuration.
        Returns information about what was created or updated.
        """
        result = {
            "user_created": False,
            "user_migrated": False,
            "channel_created": False,
            "user_id": None,
            "channel_id": None,
            "migration_changes": [],
            "errors": []
        }

        session = None
        try:
            session = await get_background_task_session()
            user_repo = UserRepositoryImpl(session)
            channel_repo = ChannelRepositoryImpl(session)

            # Check if we have any users
            users = await user_repo.get_all(limit=1)

            if not users:
                logger.info("No users found, creating default user...")
                user = await self._create_default_user(user_repo)
                result["user_created"] = True
                result["user_id"] = user.id
                logger.info(f"Created default user with ID: {user.id}")
            else:
                # Migrate existing users to match environment configuration
                migration_service = UserMigrationService()
                migration_result = await migration_service.migrate_default_user()

                if migration_result["user_updated"]:
                    result["user_migrated"] = True
                    result["migration_changes"] = migration_result["changes_made"]
                    logger.info(f"Migrated existing user: {', '.join(migration_result['changes_made'])}")

                if migration_result["errors"]:
                    result["errors"].extend(migration_result["errors"])

                result["user_id"] = migration_result["user_id"] or users[0].id
                logger.info(f"Using existing user with ID: {result['user_id']}")

            # Check if we have any channels for this user
            existing_channel = await channel_repo.find_by_user_id(result["user_id"])

            if not existing_channel:
                logger.info("No channel found for user, creating default channel...")
                channel = await self._create_default_channel(channel_repo, result["user_id"])
                result["channel_created"] = True
                result["channel_id"] = channel.id
                logger.info(f"Created default channel with ID: {channel.id}")
            else:
                result["channel_id"] = existing_channel.id
                logger.info(f"Using existing channel with ID: {existing_channel.id}")

            await session.commit()
            logger.info("Default data initialization completed successfully")

        except Exception as e:
            error_msg = f"Error during default data initialization: {e}"
            logger.error(error_msg)
            result["errors"].append(error_msg)

            if session:
                await session.rollback()

        finally:
            if session:
                await session.close()

        return result

    async def _create_default_user(self, user_repo: UserRepositoryImpl) -> User:
        """Create default user from configuration"""
        try:
            # Check if email already exists (shouldn't happen on fresh install)
            if await user_repo.email_exists(settings.default_user_email):
                raise ValueError(f"User with email {settings.default_user_email} already exists")

            # Create default user
            user = User.create_user(
                name=settings.default_user_name,
                email=settings.default_user_email,
                password=settings.default_user_password,
                is_admin=True  # Default user is admin
            )

            return await user_repo.create(user)

        except Exception as e:
            logger.error(f"Failed to create default user: {e}")
            raise

    async def _create_default_channel(self, channel_repo: ChannelRepositoryImpl, user_id: int) -> Channel:
        """Create default channel from configuration"""
        try:
            # Create channel with settings from environment
            channel = Channel(
                id=None,
                user_id=user_id,
                name=settings.default_channel_name,
                description=settings.default_channel_description,
                website_url=settings.default_channel_website_url,
                image_url=settings.default_channel_image_url,
                category=settings.default_channel_category,
                language=settings.default_channel_language,
                explicit_content=settings.default_channel_explicit_content,
                author_name=settings.default_channel_author_name or settings.default_user_name,
                author_email=Email.create_optional(settings.default_channel_author_email or settings.default_user_email),
                owner_name=settings.default_channel_owner_name or settings.default_user_name,
                owner_email=Email.create_optional(settings.default_channel_owner_email or settings.default_user_email),
                feed_url=settings.default_channel_feed_url or ""
            )

            return await channel_repo.create(channel)

        except Exception as e:
            logger.error(f"Failed to create default channel: {e}")
            raise

    async def get_initialization_status(self) -> Dict[str, Any]:
        """
        Get current initialization status without making changes
        """
        status = {
            "has_users": False,
            "has_channels": False,
            "user_count": 0,
            "channel_count": 0,
            "needs_initialization": False
        }

        session = None
        try:
            session = await get_background_task_session()
            user_repo = UserRepositoryImpl(session)
            channel_repo = ChannelRepositoryImpl(session)

            users = await user_repo.get_all(limit=100)
            status["user_count"] = len(users)
            status["has_users"] = len(users) > 0

            if status["has_users"]:
                # Check channels for the first user (simplified)
                channels = await channel_repo.get_all(limit=100)
                status["channel_count"] = len(channels)
                status["has_channels"] = len(channels) > 0

            status["needs_initialization"] = not (status["has_users"] and status["has_channels"])

        except Exception as e:
            logger.error(f"Error checking initialization status: {e}")
            status["error"] = str(e)

        finally:
            if session:
                await session.close()

        return status