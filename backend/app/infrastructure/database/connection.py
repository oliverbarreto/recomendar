"""
Database connection and session management with monitoring and lifecycle logging
"""
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator, AsyncGenerator, Dict, Any
from app.core.config import settings
import sqlite3
import aiosqlite
import logging
import time
import threading
from datetime import datetime

# Set up logging for database connections
logger = logging.getLogger(__name__)

# Global connection tracking
_connection_stats = {
    'total_sessions_created': 0,
    'total_background_sessions_created': 0,
    'active_sessions': 0,
    'total_commits': 0,
    'total_rollbacks': 0,
    'total_session_closes': 0,
    'database_locks_detected': 0,
    'last_activity': None
}
_stats_lock = threading.Lock()

# Create sync database engine (for health checks and migrations)
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

# Create async database engine with enhanced SQLite-specific settings for concurrency
async_engine = create_async_engine(
    settings.database_url.replace("sqlite://", "sqlite+aiosqlite://"),
    echo=False,
    pool_timeout=60,  # Increased from 30 to 60 seconds
    pool_recycle=3600,
    pool_pre_ping=True,  # Enable connection health checks
    pool_reset_on_return='commit',  # Reset connections properly
    connect_args={
        "check_same_thread": False,
        "timeout": 60,  # Increased timeout to 60 seconds
        "isolation_level": None,  # Enable autocommit mode for better concurrency
    }
)

# Configure SQLite for better concurrency with async connections
@event.listens_for(async_engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite pragmas for better concurrency and performance with monitoring"""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        try:
            # Enable WAL mode for better concurrency (allows multiple readers + 1 writer)
            cursor.execute("PRAGMA journal_mode=WAL")
            
            # Set synchronous mode to NORMAL for better performance while maintaining safety
            cursor.execute("PRAGMA synchronous=NORMAL")
            
            # Set busy timeout to 60 seconds (increased from 30s)
            cursor.execute("PRAGMA busy_timeout=60000")
            
            # Store temporary tables in memory for better performance
            cursor.execute("PRAGMA temp_store=memory")
            
            # Increase cache size for better performance (10MB)
            cursor.execute("PRAGMA cache_size=10000")
            
            # Configure WAL mode settings for better concurrency
            cursor.execute("PRAGMA wal_autocheckpoint=1000")  # Auto-checkpoint every 1000 pages
            cursor.execute("PRAGMA wal_checkpoint_fullfsync=OFF")  # Faster WAL checkpoints
            
            # Enable query optimization
            cursor.execute("PRAGMA optimize")
            
            # Set read uncommitted isolation level for better read concurrency
            cursor.execute("PRAGMA read_uncommitted=1")
            
            # Configure locking mode for better concurrency
            cursor.execute("PRAGMA locking_mode=NORMAL")  # Allow multiple connections
            
            # Enable foreign key constraints (good practice)
            cursor.execute("PRAGMA foreign_keys=ON")
            
            # Set page size for optimal performance (4KB)
            cursor.execute("PRAGMA page_size=4096")
            
            # Configure mmap size for better I/O performance (64MB)
            cursor.execute("PRAGMA mmap_size=67108864")
            
            logger.debug("SQLite connection configured with enhanced concurrency and performance settings")
        except Exception as e:
            logger.error(f"Error setting SQLite pragmas: {e}")
        finally:
            cursor.close()

# Create sync session factory (for health checks)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False
)

# Create declarative base for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get synchronous database session (for health checks)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get async database session with lifecycle monitoring
    """
    session_id = id(object())  # Unique session identifier
    start_time = time.time()
    
    with _stats_lock:
        _connection_stats['total_sessions_created'] += 1
        _connection_stats['active_sessions'] += 1
        _connection_stats['last_activity'] = datetime.utcnow().isoformat()
    
    logger.debug(f"Created async session {session_id} (active: {_connection_stats['active_sessions']})")
    
    async with AsyncSessionLocal() as session:
        try:
            # Add session monitoring
            session._session_id = session_id
            session._created_at = start_time
            yield session
        finally:
            duration = time.time() - start_time
            with _stats_lock:
                _connection_stats['active_sessions'] -= 1
                _connection_stats['total_session_closes'] += 1
            
            logger.debug(
                f"Closed async session {session_id} after {duration:.2f}s "
                f"(active: {_connection_stats['active_sessions']})"
            )
            await session.close()


async def get_background_task_session() -> AsyncSession:
    """
    Get a fresh async database session specifically for background tasks with monitoring
    
    This creates a completely independent session that is not tied to any
    HTTP request context, solving session conflicts between request handlers
    and background tasks.
    """
    session_id = id(object())  # Unique session identifier
    start_time = time.time()
    
    with _stats_lock:
        _connection_stats['total_background_sessions_created'] += 1
        _connection_stats['active_sessions'] += 1
        _connection_stats['last_activity'] = datetime.utcnow().isoformat()
    
    logger.debug(
        f"Created background task session {session_id} "
        f"(active: {_connection_stats['active_sessions']}, "
        f"bg total: {_connection_stats['total_background_sessions_created']})"
    )
    
    session = AsyncSessionLocal()
    # Add session monitoring metadata
    session._session_id = session_id
    session._created_at = start_time
    session._is_background_task = True
    
    return session


def get_connection_stats() -> Dict[str, Any]:
    """
    Get current database connection statistics for monitoring
    
    Returns:
        Dictionary with connection stats including active sessions,
        total operations, and timing information
    """
    with _stats_lock:
        return _connection_stats.copy()


def log_database_operation(operation: str, session_id: int, details: str = None):
    """
    Log database operations for monitoring and debugging
    
    Args:
        operation: Type of operation (commit, rollback, close, etc.)
        session_id: Session identifier
        details: Additional operation details
    """
    with _stats_lock:
        _connection_stats['last_activity'] = datetime.utcnow().isoformat()
        
        if operation == 'commit':
            _connection_stats['total_commits'] += 1
        elif operation == 'rollback':
            _connection_stats['total_rollbacks'] += 1
        elif operation == 'close':
            _connection_stats['total_session_closes'] += 1
        elif operation == 'database_lock':
            _connection_stats['database_locks_detected'] += 1
    
    log_msg = f"DB Operation: {operation} on session {session_id}"
    if details:
        log_msg += f" - {details}"
    
    if operation == 'database_lock':
        logger.warning(log_msg)
    else:
        logger.debug(log_msg)


async def init_db():
    """
    Initialize database - create tables if they don't exist
    """
    # Import all models here to ensure they are registered with SQLAlchemy
    # before creating tables
    from app.infrastructure.database import models
    
    Base.metadata.create_all(bind=engine)