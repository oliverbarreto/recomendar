"""
Base repository implementation using SQLAlchemy
"""
from abc import abstractmethod
from typing import TypeVar, Generic, List, Optional, Type
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.domain.repositories.base import BaseRepository

logger = logging.getLogger(__name__)

T = TypeVar('T')  # Domain entity type
M = TypeVar('M')  # SQLAlchemy model type


class BaseRepositoryImpl(Generic[T, M], BaseRepository[T]):
    """
    Base SQLAlchemy implementation of BaseRepository
    """

    def __init__(self, session: AsyncSession, model_class: Type[M]):
        self.session = session
        self.model_class = model_class

    @abstractmethod
    def _entity_to_model(self, entity: T) -> M:
        """Convert domain entity to SQLAlchemy model"""
        pass

    @abstractmethod
    def _model_to_entity(self, model: M) -> T:
        """Convert SQLAlchemy model to domain entity"""
        pass

    async def create(self, entity: T) -> T:
        """Create a new entity in the repository"""
        try:
            model = self._entity_to_model(entity)
            self.session.add(model)
            await self.session.commit()
            await self.session.refresh(model)
            return self._model_to_entity(model)

        except Exception as e:
            logger.error(f"Error creating entity: {e}")
            await self.session.rollback()
            raise

    async def get_by_id(self, entity_id: int) -> Optional[T]:
        """Retrieve an entity by its ID"""
        try:
            stmt = select(self.model_class).where(self.model_class.id == entity_id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()

            if model:
                return self._model_to_entity(model)
            return None

        except Exception as e:
            logger.error(f"Error getting entity by id {entity_id}: {e}")
            raise

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Retrieve all entities with pagination support"""
        try:
            stmt = select(self.model_class).offset(skip).limit(limit)
            result = await self.session.execute(stmt)
            models = result.scalars().all()

            return [self._model_to_entity(model) for model in models]

        except Exception as e:
            logger.error(f"Error getting all entities: {e}")
            raise

    async def update(self, entity: T) -> T:
        """Update an existing entity in the repository"""
        try:
            # Get existing model
            stmt = select(self.model_class).where(self.model_class.id == entity.id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()

            if not model:
                raise ValueError(f"Entity with id {entity.id} not found")

            # Update model with entity data
            updated_model = self._entity_to_model(entity)
            for key, value in updated_model.__dict__.items():
                if not key.startswith('_') and hasattr(model, key):
                    setattr(model, key, value)

            await self.session.commit()
            await self.session.refresh(model)
            return self._model_to_entity(model)

        except Exception as e:
            logger.error(f"Error updating entity: {e}")
            await self.session.rollback()
            raise

    async def delete(self, entity_id: int) -> bool:
        """Delete an entity by its ID"""
        try:
            stmt = delete(self.model_class).where(self.model_class.id == entity_id)
            result = await self.session.execute(stmt)
            await self.session.commit()

            return result.rowcount > 0

        except Exception as e:
            logger.error(f"Error deleting entity {entity_id}: {e}")
            await self.session.rollback()
            raise

    async def exists(self, entity_id: int) -> bool:
        """Check if an entity exists by its ID"""
        try:
            entity = await self.get_by_id(entity_id)
            return entity is not None

        except Exception as e:
            logger.error(f"Error checking if entity exists {entity_id}: {e}")
            raise