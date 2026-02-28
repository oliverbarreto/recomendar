"""
User repository implementation using SQLAlchemy
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import logging

from app.domain.repositories.user import UserRepository
from app.domain.entities.user import User
from app.infrastructure.database.models.user import UserModel
from app.infrastructure.repositories.base_repository_impl import BaseRepositoryImpl

logger = logging.getLogger(__name__)


class UserRepositoryImpl(BaseRepositoryImpl[User, UserModel], UserRepository):
    """
    SQLAlchemy implementation of UserRepository
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session, UserModel)

    def _entity_to_model(self, entity: User) -> UserModel:
        """Convert User entity to UserModel"""
        return UserModel(
            id=entity.id,
            name=entity.name,
            email=entity.email,
            password_hash=entity.password_hash,
            is_admin=entity.is_admin,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )

    def _model_to_entity(self, model: UserModel) -> User:
        """Convert UserModel to User entity"""
        return User(
            id=model.id,
            name=model.name,
            email=model.email,
            password_hash=model.password_hash,
            is_admin=model.is_admin,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    async def find_by_email(self, email: str) -> Optional[User]:
        """Find a user by their email address"""
        try:
            stmt = select(UserModel).where(UserModel.email == email.lower())
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()

            if model:
                return self._model_to_entity(model)
            return None

        except Exception as e:
            logger.error(f"Error finding user by email {email}: {e}")
            raise

    async def email_exists(self, email: str) -> bool:
        """Check if an email address is already registered"""
        try:
            user = await self.find_by_email(email)
            return user is not None
        except Exception as e:
            logger.error(f"Error checking if email exists {email}: {e}")
            raise

    async def get_admin_users(self) -> List[User]:
        """Get all users with admin privileges"""
        try:
            stmt = select(UserModel).where(UserModel.is_admin == True)
            result = await self.session.execute(stmt)
            models = result.scalars().all()

            return [self._model_to_entity(model) for model in models]

        except Exception as e:
            logger.error(f"Error getting admin users: {e}")
            raise

    async def update_password(self, user_id: int, password_hash: str) -> bool:
        """Update a user's password hash"""
        try:
            stmt = select(UserModel).where(UserModel.id == user_id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()

            if model:
                model.password_hash = password_hash
                await self.session.commit()
                return True
            return False

        except Exception as e:
            logger.error(f"Error updating password for user {user_id}: {e}")
            await self.session.rollback()
            raise

    async def promote_to_admin(self, user_id: int) -> bool:
        """Promote a user to admin privileges"""
        try:
            stmt = select(UserModel).where(UserModel.id == user_id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()

            if model:
                model.is_admin = True
                await self.session.commit()
                return True
            return False

        except Exception as e:
            logger.error(f"Error promoting user {user_id} to admin: {e}")
            await self.session.rollback()
            raise

    async def revoke_admin(self, user_id: int) -> bool:
        """Revoke admin privileges from a user"""
        try:
            stmt = select(UserModel).where(UserModel.id == user_id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()

            if model:
                model.is_admin = False
                await self.session.commit()
                return True
            return False

        except Exception as e:
            logger.error(f"Error revoking admin privileges from user {user_id}: {e}")
            await self.session.rollback()
            raise