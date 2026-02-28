# FastAPI Clean Architecture Example

Here is a comprehensive FastAPI application structure that follows Clean Architecture principles and SOLID design patterns. This approach provides maintainable, testable, and scalable code that follows enterprise-grade architecture patterns while remaining practical for real-world development.

Here's what this structure provides:

## Architecture Layers:

### 1. Domain Layer (domain/)

- Entities: Pure business objects (User) with business rules
- Repositories: Abstract interfaces defining data access contracts
- Exceptions: Domain-specific exceptions

### 2. Application Layer (application/)

- Use Cases: Orchestrate business logic and enforce business rules
- Services: Coordinate between repositories and handle business operations
- Contains application-specific business logic

### 3. Infrastructure Layer (infrastructure/)

- Database: SQLAlchemy models and connection management
- Repositories: Concrete implementations of repository interfaces
- External concerns like databases, file systems, etc.

### 4. Presentation Layer (presentation/)

- API Routes: FastAPI endpoints and HTTP concerns
- Schemas: Request/response models for API
- Dependencies: Dependency injection setup

## SOLID Principles Applied:

- Single Responsibility: Each class has one reason to change
- Open/Closed: Easy to extend (new repositories, use cases) without modifying existing code
- Liskov Substitution: Repository implementations can be swapped
- Interface Segregation: Small, focused interfaces
- Dependency Inversion: High-level modules don't depend on low-level modules

## Key Features:

- Async Support: Full async/await pattern throughout
- Dependency Injection: FastAPI's DI system manages all dependencies
- Clean Separation: Business logic isolated from framework concerns
- Testability: Easy to mock and test each layer independently
- Extensibility: Easy to add new features without breaking existing code

## Usage Example:

The structure allows you to easily:

- Swap database implementations (PostgreSQL, MongoDB, etc.)
- Add new use cases without touching existing code
- Test business logic independently of the API layer
- Scale the application by adding new domains

## **Directory Structure:**

```plaintext
project/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── dependencies.py
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── entities/
│   │   │   ├── __init__.py
│   │   │   └── user.py
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   └── user_repository.py
│   │   └── exceptions/
│   │       ├── __init__.py
│   │       └── base.py
│   ├── application/
│   │   ├── __init__.py
│   │   ├── use_cases/
│   │   │   ├── __init__.py
│   │   │   └── user_use_cases.py
│   │   └── services/
│   │       ├── __init__.py
│   │       └── user_service.py
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── database/
│   │   │   ├── __init__.py
│   │   │   ├── connection.py
│   │   │   └── models.py
│   │   └── repositories/
│   │       ├── __init__.py
│   │       └── sqlalchemy_user_repository.py
│   └── presentation/
│       ├── __init__.py
│       ├── api/
│       │   ├── __init__.py
│       │   ├── v1/
│       │   │   ├── __init__.py
│       │   │   └── users.py
│       │   └── deps.py
│       └── schemas/
│           ├── __init__.py
│           └── user_schemas.py
└── requirements.txt
```

## Example Code

### CORE

#### CONFIG
```python
# =============================================================================
# app/core/config.py
# =============================================================================
from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    app_name: str = "FastAPI Clean Architecture"
    debug: bool = False
    database_url: str = "sqlite:///./test.db"
    secret_key: str = "your-secret-key-here"
    
    class Config:
        env_file = ".env"

settings = Settings()
``` 

### DOMAIN

#### ENTITIES
```python
# =============================================================================
# app/domain/entities/user.py
# =============================================================================
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class User:
    """Domain entity representing a User"""
    id: Optional[int] = None
    email: str = ""
    username: str = ""
    full_name: str = ""
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.email:
            raise ValueError("Email is required")
        if not self.username:
            raise ValueError("Username is required")

```

#### REPOSITORY INTERFACE
```python
# =============================================================================
# app/domain/repositories/user_repository.py
# =============================================================================
from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.user import User

class UserRepository(ABC):
    """Abstract repository interface for User operations"""
    
    @abstractmethod
    async def create(self, user: User) -> User:
        """Create a new user"""
        pass
    
    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        pass
    
    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        pass
    
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination"""
        pass
    
    @abstractmethod
    async def update(self, user: User) -> User:
        """Update user"""
        pass
    
    @abstractmethod
    async def delete(self, user_id: int) -> bool:
        """Delete user by ID"""
        pass

```

#### EXCEPTIONS
```python
# =============================================================================
# app/domain/exceptions/base.py
# =============================================================================
class DomainException(Exception):
    """Base domain exception"""
    pass

class UserNotFoundException(DomainException):
    """Raised when user is not found"""
    pass

class UserAlreadyExistsException(DomainException):
    """Raised when user already exists"""
    pass

class InvalidUserDataException(DomainException):
    """Raised when user data is invalid"""
    pass
```

### APPLICATION 

#### USE CASES
```python
# =============================================================================
# app/application/use_cases/user_use_cases.py
# =============================================================================
from typing import List, Optional
from ..services.user_service import UserService
from ...domain.entities.user import User
from ...domain.exceptions.base import UserNotFoundException, UserAlreadyExistsException

class CreateUserUseCase:
    """Use case for creating a new user"""
    
    def __init__(self, user_service: UserService):
        self._user_service = user_service
    
    async def execute(self, email: str, username: str, full_name: str) -> User:
        """Execute the create user use case"""
        # Check if user already exists
        existing_user = await self._user_service.get_by_email(email)
        if existing_user:
            raise UserAlreadyExistsException(f"User with email {email} already exists")
        
        existing_user = await self._user_service.get_by_username(username)
        if existing_user:
            raise UserAlreadyExistsException(f"User with username {username} already exists")
        
        # Create new user
        user = User(email=email, username=username, full_name=full_name)
        return await self._user_service.create_user(user)

class GetUserUseCase:
    """Use case for retrieving a user"""
    
    def __init__(self, user_service: UserService):
        self._user_service = user_service
    
    async def execute(self, user_id: int) -> User:
        """Execute the get user use case"""
        user = await self._user_service.get_by_id(user_id)
        if not user:
            raise UserNotFoundException(f"User with ID {user_id} not found")
        return user

class GetUsersUseCase:
    """Use case for retrieving multiple users"""
    
    def __init__(self, user_service: UserService):
        self._user_service = user_service
    
    async def execute(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Execute the get users use case"""
        return await self._user_service.get_all(skip=skip, limit=limit)

class UpdateUserUseCase:
    """Use case for updating a user"""
    
    def __init__(self, user_service: UserService):
        self._user_service = user_service
    
    async def execute(self, user_id: int, **update_data) -> User:
        """Execute the update user use case"""
        existing_user = await self._user_service.get_by_id(user_id)
        if not existing_user:
            raise UserNotFoundException(f"User with ID {user_id} not found")
        
        # Update user fields
        for field, value in update_data.items():
            if hasattr(existing_user, field) and value is not None:
                setattr(existing_user, field, value)
        
        return await self._user_service.update_user(existing_user)

class DeleteUserUseCase:
    """Use case for deleting a user"""
    
    def __init__(self, user_service: UserService):
        self._user_service = user_service
    
    async def execute(self, user_id: int) -> bool:
        """Execute the delete user use case"""
        existing_user = await self._user_service.get_by_id(user_id)
        if not existing_user:
            raise UserNotFoundException(f"User with ID {user_id} not found")
        
        return await self._user_service.delete_user(user_id)
```

#### SERVICES

```python
# =============================================================================
# app/application/services/user_service.py
# =============================================================================
from typing import List, Optional
from ...domain.entities.user import User
from ...domain.repositories.user_repository import UserRepository

class UserService:
    """Service layer for user operations"""
    
    def __init__(self, user_repository: UserRepository):
        self._user_repository = user_repository
    
    async def create_user(self, user: User) -> User:
        """Create a new user"""
        return await self._user_repository.create(user)
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return await self._user_repository.get_by_id(user_id)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return await self._user_repository.get_by_email(email)
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return await self._user_repository.get_by_username(username)
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination"""
        return await self._user_repository.get_all(skip=skip, limit=limit)
    
    async def update_user(self, user: User) -> User:
        """Update user"""
        return await self._user_repository.update(user)
    
    async def delete_user(self, user_id: int) -> bool:
        """Delete user"""
        return await self._user_repository.delete(user_id)
```

### INFRASTRUCTURE

#### DATABASE MODELS
```python
# =============================================================================
# app/infrastructure/database/models.py
# =============================================================================
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class UserModel(Base):
    """SQLAlchemy model for User"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

#### DATABASE CONNECTION
```python
# =============================================================================
# app/infrastructure/database/connection.py
# =============================================================================
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from ...core.config import settings

# For async operations
async_engine = create_async_engine(
    settings.database_url.replace("sqlite://", "sqlite+aiosqlite://"),
    echo=settings.debug
)

AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db_session() -> AsyncSession:
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

#### REPOSITORY IMPLEMENTATION

```python
# =============================================================================
# app/infrastructure/repositories/sqlalchemy_user_repository.py
# =============================================================================
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...domain.entities.user import User
from ...domain.repositories.user_repository import UserRepository
from ..database.models import UserModel

class SQLAlchemyUserRepository(UserRepository):
    """SQLAlchemy implementation of UserRepository"""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    def _model_to_entity(self, model: UserModel) -> User:
        """Convert SQLAlchemy model to domain entity"""
        return User(
            id=model.id,
            email=model.email,
            username=model.username,
            full_name=model.full_name,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def _entity_to_model(self, entity: User) -> UserModel:
        """Convert domain entity to SQLAlchemy model"""
        return UserModel(
            id=entity.id,
            email=entity.email,
            username=entity.username,
            full_name=entity.full_name,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )
    
    async def create(self, user: User) -> User:
        """Create a new user"""
        db_user = UserModel(
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active
        )
        self._session.add(db_user)
        await self._session.commit()
        await self._session.refresh(db_user)
        return self._model_to_entity(db_user)
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self._session.execute(stmt)
        db_user = result.scalar_one_or_none()
        return self._model_to_entity(db_user) if db_user else None
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self._session.execute(stmt)
        db_user = result.scalar_one_or_none()
        return self._model_to_entity(db_user) if db_user else None
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        stmt = select(UserModel).where(UserModel.username == username)
        result = await self._session.execute(stmt)
        db_user = result.scalar_one_or_none()
        return self._model_to_entity(db_user) if db_user else None
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination"""
        stmt = select(UserModel).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        db_users = result.scalars().all()
        return [self._model_to_entity(db_user) for db_user in db_users]
    
    async def update(self, user: User) -> User:
        """Update user"""
        stmt = select(UserModel).where(UserModel.id == user.id)
        result = await self._session.execute(stmt)
        db_user = result.scalar_one()
        
        db_user.email = user.email
        db_user.username = user.username
        db_user.full_name = user.full_name
        db_user.is_active = user.is_active
        
        await self._session.commit()
        await self._session.refresh(db_user)
        return self._model_to_entity(db_user)
    
    async def delete(self, user_id: int) -> bool:
        """Delete user by ID"""
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self._session.execute(stmt)
        db_user = result.scalar_one_or_none()
        
        if db_user:
            await self._session.delete(db_user)
            await self._session.commit()
            return True
        return False
```

### PRESENTATION

#### SCHEMAS

```python
# =============================================================================
# app/presentation/schemas/user_schemas.py
# =============================================================================
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserCreateSchema(BaseModel):
    """Schema for creating a user"""
    email: EmailStr
    username: str
    full_name: str

class UserUpdateSchema(BaseModel):
    """Schema for updating a user"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponseSchema(BaseModel):
    """Schema for user response"""
    id: int
    email: str
    username: str
    full_name: str
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

```

#### DEPENDENCIES
```python
# =============================================================================
# app/presentation/api/deps.py
# =============================================================================
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ...infrastructure.database.connection import get_db_session
from ...infrastructure.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
from ...application.services.user_service import UserService
from ...application.use_cases.user_use_cases import (
    CreateUserUseCase,
    GetUserUseCase,
    GetUsersUseCase,
    UpdateUserUseCase,
    DeleteUserUseCase
)

# Repository Dependencies
async def get_user_repository(
    session: AsyncSession = Depends(get_db_session)
) -> SQLAlchemyUserRepository:
    """Get user repository dependency"""
    return SQLAlchemyUserRepository(session)

# Service Dependencies
async def get_user_service(
    user_repository: SQLAlchemyUserRepository = Depends(get_user_repository)
) -> UserService:
    """Get user service dependency"""
    return UserService(user_repository)

# Use Case Dependencies
async def get_create_user_use_case(
    user_service: UserService = Depends(get_user_service)
) -> CreateUserUseCase:
    """Get create user use case dependency"""
    return CreateUserUseCase(user_service)

async def get_get_user_use_case(
    user_service: UserService = Depends(get_user_service)
) -> GetUserUseCase:
    """Get user use case dependency"""
    return GetUserUseCase(user_service)

async def get_get_users_use_case(
    user_service: UserService = Depends(get_user_service)
) -> GetUsersUseCase:
    """Get users use case dependency"""
    return GetUsersUseCase(user_service)

async def get_update_user_use_case(
    user_service: UserService = Depends(get_user_service)
) -> UpdateUserUseCase:
    """Get update user use case dependency"""
    return UpdateUserUseCase(user_service)

async def get_delete_user_use_case(
    user_service: UserService = Depends(get_user_service)
) -> DeleteUserUseCase:
    """Get delete user use case dependency"""
    return DeleteUserUseCase(user_service)

```

#### API ROUTES
```python
# =============================================================================
# app/presentation/api/v1/users.py
# =============================================================================
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from ...schemas.user_schemas import UserCreateSchema, UserUpdateSchema, UserResponseSchema
from ....application.use_cases.user_use_cases import (
    CreateUserUseCase,
    GetUserUseCase,
    GetUsersUseCase,
    UpdateUserUseCase,
    DeleteUserUseCase
)
from ....domain.exceptions.base import (
    UserNotFoundException,
    UserAlreadyExistsException,
    InvalidUserDataException
)
from ..deps import (
    get_create_user_use_case,
    get_get_user_use_case,
    get_get_users_use_case,
    get_update_user_use_case,
    get_delete_user_use_case
)

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreateSchema,
    use_case: CreateUserUseCase = Depends(get_create_user_use_case)
):
    """Create a new user"""
    try:
        user = await use_case.execute(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name
        )
        return UserResponseSchema.from_orm(user)
    except UserAlreadyExistsException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except InvalidUserDataException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{user_id}", response_model=UserResponseSchema)
async def get_user(
    user_id: int,
    use_case: GetUserUseCase = Depends(get_get_user_use_case)
):
    """Get user by ID"""
    try:
        user = await use_case.execute(user_id)
        return UserResponseSchema.from_orm(user)
    except UserNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.get("/", response_model=List[UserResponseSchema])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    use_case: GetUsersUseCase = Depends(get_get_users_use_case)
):
    """Get all users with pagination"""
    users = await use_case.execute(skip=skip, limit=limit)
    return [UserResponseSchema.from_orm(user) for user in users]

@router.put("/{user_id}", response_model=UserResponseSchema)
async def update_user(
    user_id: int,
    user_data: UserUpdateSchema,
    use_case: UpdateUserUseCase = Depends(get_update_user_use_case)
):
    """Update user"""
    try:
        update_data = user_data.dict(exclude_unset=True)
        user = await use_case.execute(user_id, **update_data)
        return UserResponseSchema.from_orm(user)
    except UserNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InvalidUserDataException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    use_case: DeleteUserUseCase = Depends(get_delete_user_use_case)
):
    """Delete user"""
    try:
        await use_case.execute(user_id)
    except UserNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
```

### CORE

#### CORE DEPENDENCIES

```python
# =============================================================================
# app/core/dependencies.py
# =============================================================================
from fastapi import FastAPI
from .config import settings

def create_app() -> FastAPI:
    """Create FastAPI application"""
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        version="1.0.0"
    )
    
    # Include routers
    from ..presentation.api.v1.users import router as users_router
    app.include_router(users_router, prefix="/api/v1")
    
    return app
```

#### MAIN APP
```python
# =============================================================================
# app/main.py
# =============================================================================
from fastapi import FastAPI
from .core.dependencies import create_app
from .infrastructure.database.connection import async_engine
from .infrastructure.database.models import Base

app = create_app()

@app.on_event("startup")
async def startup_event():
    """Create database tables on startup"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "FastAPI Clean Architecture Example"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

```

### REQUIREMENTS
```plaintext
# =============================================================================
# requirements.txt
# =============================================================================
# fastapi==0.104.1
# uvicorn[standard]==0.24.0
# pydantic[email]==2.5.0
# sqlalchemy==2.0.23
# aiosqlite==0.19.0
# python-multipart==0.0.6
```






