---
title: "Asynchronous Database Sessions in FastAPI with SQLAlchemy"
source: "https://dev.to/akarshan/asynchronous-database-sessions-in-fastapi-with-sqlalchemy-1o7e"
author:
  - "[[DEV Community]]"
published: 2024-01-17
created: 2025-05-25
description: "FastAPI, a modern and fast web framework for building APIs with Python, provides strong support for... Tagged with async, fastapi, sqlalchmey, asyncscopedsession."
tags:
  - "clippings"
---

# Asynchronous Database Sessions in FastAPI with SQLAlchemy

FastAPI, a modern and fast web framework for building APIs with Python, provides strong support for asynchronous programming. Pairing it with SQLAlchemy's asynchronous capabilities allows you to build scalable, non-blocking applications with efficient database interactions.

In this post, we’ll walk through how to set up and use asynchronous SQLAlchemy sessions in a FastAPI application using a clean and production-friendly session manager pattern.

In this blog post, we'll explore how to use asynchronous database sessions in SQLAlchemy with FastAPI. We'll focus on creating an AsyncSession and managing its lifecycle using the asyncio module, along with demonstrating the use of dependency injection for cleaner and more maintainable code.

## Installation

Before we start, make sure to install the necessary dependencies:  

```
pip install fastapi sqlalchemy asyncpg uvicorn
```

`fastapi` – the web framework.  
`sqlalchemy` – ORM for database access.  
`asyncpg` – async driver for PostgreSQL.  
`uvicorn` – ASGI server to run FastAPI apps.

## ⚙️ Setting Up Async SQLAlchemy with FastAPI

### 🔧 Session Manager

Below is a modular implementation using create\_async\_engine and async\_sessionmaker:  

```
from __future__ import annotations

from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import AsyncAdaptedQueuePool
from sqlalchemy.sql import text

from core.settings import app_env_settings as settings

class SessionManager:
    """Manages asynchronous DB sessions with connection pooling."""

    def __init__(self) -> None:
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    def init_db(self) -> None:
        """Initialize the database engine and session factory."""
        database_url = (
            f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
            f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        )

        self.engine = create_async_engine(
            database_url,
            poolclass=AsyncAdaptedQueuePool,
            pool_size=settings.POOL_SIZE,
            max_overflow=settings.MAX_OVERFLOW,
            pool_pre_ping=True,
            pool_recycle=settings.POOL_RECYCLE,
            echo=settings.DEBUG,
        )

        self.session_factory = async_sessionmaker(
            self.engine,
            expire_on_commit=False,
            autoflush=False,
            class_=AsyncSession,
        )

    async def close(self) -> None:
        """Dispose of the database engine."""
        if self.engine:
            await self.engine.dispose()

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Yield a database session with the correct schema set."""
        if not self.session_factory:
            raise RuntimeError("Database session factory is not initialized.")

        async with self.session_factory() as session:
            try:
                if settings.POSTGRES_SCHEMA:
                    await session.execute(
                        text(f"SET search_path TO {settings.POSTGRES_SCHEMA}")
                    )
                yield session
            except Exception as e:
                await session.rollback()
                raise RuntimeError(f"Database session error: {e!r}") from e

# Global instances
sessionmanager = SessionManager()
Base = declarative_base()
```

### 🔍 Explanation of Key Parameters

#### create\_async\_engine

- `database_url`: Connection string.
- `poolclass`: Type of connection pool (AsyncAdaptedQueuePool supports async).
- `pool_size`: Max active connections in pool.
- `max_overflow`: Extra connections beyond pool\_size.
- `pool_pre_ping`: Check if connections are alive.
- `pool_recycle`: Recycle connections after X seconds.
- `echo`: SQL query logging (good for debugging).

#### async\_sessionmaker

- `bind`: Bind to the async engine.
- `expire_on_commit`: Keep ORM objects alive after commit.
- `autoflush`: Automatically sync pending changes.
- `class_`: Use AsyncSession class.

## 🧩 Integrating with FastAPI

### Using Dependency Injection

FastAPI supports dependency injection, making it easier to manage dependencies across different parts of your application. To use the database session as a dependency, you can utilize the Depends function. Here's an example of how you can inject the AsyncSession into your FastAPI route:  

```
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in sessionmanager.get_session():
        yield session
```
```
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.get("/users/")
async def list_users(session: AsyncSession = Depends(get_db)):
    result = await session.execute("SELECT * FROM users;")
    return result.fetchall()
```

### 🧪 Running Async Scripts

Now, let's see how you can use the asynchronous database session in practical scenarios, such as in scripts:  

```
import asyncio
from typing import List

async def clear_users(user_ids: List[int]):
    async for session in sessionmanager.get_session():
        await session.execute(
            text("DELETE FROM users WHERE id = ANY(:ids)"),
            {"ids": user_ids}
        )
        await session.commit()

if __name__ == "__main__":
    sessionmanager.init_db()
    asyncio.run(clear_users([1, 2, 3]))
```

Here is a sequence diagram for Async Session Management with Event Loop and Connection Pooling

[![Image description](https://media2.dev.to/dynamic/image/width=800%2Cheight=%2Cfit=scale-down%2Cgravity=auto%2Cformat=auto/https%3A%2F%2Fdev-to-uploads.s3.amazonaws.com%2Fuploads%2Farticles%2F2w6lt6f63rr2myzt6vdl.png)](https://media2.dev.to/dynamic/image/width=800%2Cheight=%2Cfit=scale-down%2Cgravity=auto%2Cformat=auto/https%3A%2F%2Fdev-to-uploads.s3.amazonaws.com%2Fuploads%2Farticles%2F2w6lt6f63rr2myzt6vdl.png)

✅ Final Thoughts  
Using SQLAlchemy’s AsyncSession with FastAPI through a well-structured session manager gives you:

- Efficient connection pooling
- Schema-specific control
- Clean separation of concerns
- Reusability across your app and scripts

This approach is robust, scalable, and production-ready for modern async backends.

 [![profile](https://media2.dev.to/dynamic/image/width=64,height=64,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.amazonaws.com%2Fuploads%2Forganization%2Fprofile_image%2F10846%2Fb8131f88-3d8a-476d-bcf0-2e0fb946e4d5.png) ACI.dev](https://dev.to/acidev)Promoted

[![ACI image](https://media2.dev.to/dynamic/image/width=775%2Cheight=%2Cfit=scale-down%2Cgravity=auto%2Cformat=auto/https%3A%2F%2Fi.imgur.com%2FJdwzkK1.jpeg)](https://bit.ly/4mdlYOl?bb=231139)

## ACI.dev: The Only MCP Server Your AI Agents Need

ACI.dev’s open-source tool-use platform and Unified MCP Server turns 600+ functions into two simple MCP tools on one server—search and execute. Comes with multi-tenant auth and natural-language permission scopes. 100% open-source under Apache 2.0.