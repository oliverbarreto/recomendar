"""
User migration service for updating existing user with environment values
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
import logging

from app.core.config import settings
from app.domain.entities.user import User
from app.infrastructure.repositories.user_repository import UserRepositoryImpl
from app.infrastructure.database.connection import get_background_task_session

logger = logging.getLogger(__name__)


class UserMigrationService:
    """
    Service for migrating existing user data to match environment configuration
    """

    def __init__(self):
        pass

    async def migrate_default_user(self) -> Dict[str, Any]:
        """
        Update existing user (John Tech) with default user configuration from environment

        Returns:
            Migration result information
        """
        result = {
            "user_found": False,
            "user_updated": False,
            "user_id": None,
            "changes_made": [],
            "errors": []
        }

        session = None
        try:
            session = await get_background_task_session()
            user_repo = UserRepositoryImpl(session)

            # Find the first admin user (should be John Tech)
            admin_users = await user_repo.get_admin_users()

            if not admin_users:
                # Try to find any user if no admin users exist
                all_users = await user_repo.get_all(limit=10)
                if all_users:
                    admin_users = [all_users[0]]  # Use first user
                    logger.info(f"No admin users found, using first user: {all_users[0].email}")

            if not admin_users:
                result["errors"].append("No users found to migrate")
                return result

            # Use the first admin user (or first user)
            user = admin_users[0]
            result["user_found"] = True
            result["user_id"] = user.id

            logger.info(f"Found user to migrate: {user.email} (ID: {user.id})")

            # Check what needs to be updated
            changes_needed = []

            # Check name
            if user.name != settings.default_user_name:
                changes_needed.append(f"name: '{user.name}' -> '{settings.default_user_name}'")

            # Check email
            if user.email != settings.default_user_email:
                changes_needed.append(f"email: '{user.email}' -> '{settings.default_user_email}'")

            # Check if password needs to be updated (we'll always update it for consistency)
            changes_needed.append("password: updated to match environment configuration")

            # Ensure user is admin
            if not user.is_admin:
                changes_needed.append("is_admin: false -> true")

            if not changes_needed:
                result["changes_made"] = ["No changes needed - user already matches environment"]
                logger.info("User already matches environment configuration")
                return result

            # Apply updates
            try:
                # Update basic profile information
                user.update_profile(
                    name=settings.default_user_name,
                    email=settings.default_user_email
                )

                # Update password
                user.update_password(settings.default_user_password)

                # Ensure admin status
                user.is_admin = True

                # Save changes
                updated_user = await user_repo.update(user)
                await session.commit()

                result["user_updated"] = True
                result["changes_made"] = changes_needed

                logger.info(f"Successfully migrated user {updated_user.id}: {', '.join(changes_needed)}")

            except Exception as e:
                await session.rollback()
                error_msg = f"Failed to update user: {e}"
                result["errors"].append(error_msg)
                logger.error(error_msg)

        except Exception as e:
            error_msg = f"Error during user migration: {e}"
            logger.error(error_msg)
            result["errors"].append(error_msg)

            if session:
                await session.rollback()

        finally:
            if session:
                await session.close()

        return result

    async def get_current_user_status(self) -> Dict[str, Any]:
        """
        Get information about current users in the system

        Returns:
            Current user status information
        """
        status = {
            "total_users": 0,
            "admin_users": 0,
            "users": [],
            "default_user_exists": False,
            "migration_needed": False
        }

        session = None
        try:
            session = await get_background_task_session()
            user_repo = UserRepositoryImpl(session)

            # Get all users
            all_users = await user_repo.get_all(limit=100)
            status["total_users"] = len(all_users)

            # Get admin users
            admin_users = await user_repo.get_admin_users()
            status["admin_users"] = len(admin_users)

            # Check users
            for user in all_users:
                user_info = {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "is_admin": user.is_admin,
                    "created_at": user.created_at.isoformat() if user.created_at else None
                }
                status["users"].append(user_info)

                # Check if default user already exists
                if (user.email == settings.default_user_email and
                    user.name == settings.default_user_name and
                    user.is_admin):
                    status["default_user_exists"] = True

            # Determine if migration is needed
            if status["total_users"] > 0 and not status["default_user_exists"]:
                status["migration_needed"] = True

        except Exception as e:
            logger.error(f"Error checking user status: {e}")
            status["error"] = str(e)

        finally:
            if session:
                await session.close()

        return status