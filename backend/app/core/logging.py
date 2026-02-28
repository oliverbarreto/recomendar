"""
Central logging configuration for LabCastARR
"""
import logging
import logging.config
import logging.handlers
import sys
from pathlib import Path
from typing import Dict, Any
import structlog
from structlog.types import FilteringBoundLogger

from app.core.config import settings


class SanitizeFilter(logging.Filter):
    """Filter to sanitize sensitive information from logs"""

    SENSITIVE_FIELDS = [
        'password', 'token', 'api_key', 'secret', 'auth', 'authorization',
        'x-api-key', 'jwt', 'access_token', 'refresh_token'
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Sanitize sensitive information from log records
        """
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            msg_lower = record.msg.lower()
            for sensitive_field in self.SENSITIVE_FIELDS:
                if sensitive_field in msg_lower:
                    # Replace sensitive values with [REDACTED]
                    record.msg = self._sanitize_message(record.msg)
        return True

    def _sanitize_message(self, message: str) -> str:
        """Replace sensitive information with [REDACTED]"""
        import re

        # Pattern to match key-value pairs with sensitive information
        patterns = [
            (r'("(?:' + '|'.join(self.SENSITIVE_FIELDS) + r')"\s*:\s*")[^"]*(")', r'\1[REDACTED]\2'),
            (r'((?:' + '|'.join(self.SENSITIVE_FIELDS) + r')=)[^\s&]*', r'\1[REDACTED]'),
            (r'(Bearer\s+)[A-Za-z0-9\-\._~\+\/]+=*', r'\1[REDACTED]'),
        ]

        sanitized = message
        for pattern, replacement in patterns:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)

        return sanitized


def setup_structlog() -> None:
    """Configure structlog for structured logging"""

    # Determine if we're in production
    is_production = settings.environment == "production"

    # Configure processors based on environment
    if is_production:
        # Production: JSON output
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ]
        wrapper_class = structlog.stdlib.BoundLogger
        logger_factory = structlog.stdlib.LoggerFactory()
        cache_logger_on_first_use = True
    else:
        # Development: Human-readable output
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.dev.ConsoleRenderer(colors=True)
        ]
        wrapper_class = structlog.stdlib.BoundLogger
        logger_factory = structlog.stdlib.LoggerFactory()
        cache_logger_on_first_use = True

    structlog.configure(
        processors=processors,
        wrapper_class=wrapper_class,
        logger_factory=logger_factory,
        cache_logger_on_first_use=cache_logger_on_first_use,
    )


def get_logging_config() -> Dict[str, Any]:
    """
    Get logging configuration based on environment settings
    """
    # Create logs directory
    log_dir = Path(settings.log_file_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # Determine log level
    log_level = getattr(settings, 'log_level', 'INFO').upper()

    # Base configuration
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "sanitize": {
                "()": SanitizeFilter,
            }
        },
        "formatters": {
            "standard": {
                "format": "[%(asctime)s] [%(levelname)s] [%(name)s:%(funcName)s:%(lineno)d] %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "detailed": {
                "format": "[%(asctime)s] [%(levelname)s] [%(name)s:%(funcName)s:%(lineno)d] [%(process)d:%(thread)d] %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "json": {
                "format": '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "function": "%(funcName)s", "line": %(lineno)d, "message": "%(message)s"}',
                "datefmt": "%Y-%m-%dT%H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "standard" if settings.environment == "development" else "json",
                "stream": "ext://sys.stdout",
                "filters": ["sanitize"]
            }
        },
        "loggers": {
            # Application loggers
            "labcastarr": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False
            },
            "labcastarr.api": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False
            },
            "labcastarr.downloader": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False
            },
            "labcastarr.processor": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False
            },
            "labcastarr.rss": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False
            },
            "labcastarr.database": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False
            },
            "labcastarr.auth": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False
            },
            "labcastarr.system": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False
            },
            # Framework loggers
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "fastapi": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "sqlalchemy.engine": {
                "level": "WARNING",  # Reduce SQLAlchemy verbosity
                "handlers": ["console"],
                "propagate": False
            }
        },
        "root": {
            "level": log_level,
            "handlers": ["console"]
        }
    }

    # Add file logging for production or if explicitly enabled
    if settings.environment == "production" or getattr(settings, 'enable_file_logging', False):
        # Add rotating file handler
        config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": log_level,
            "formatter": "json" if settings.environment == "production" else "detailed",
            "filename": settings.log_file_path,
            "maxBytes": getattr(settings, 'log_max_file_size', 10) * 1024 * 1024,  # Default 10MB
            "backupCount": getattr(settings, 'log_backup_count', 5),
            "encoding": "utf8",
            "filters": ["sanitize"]
        }

        # Add file handler to all loggers
        for logger_name in config["loggers"]:
            if "handlers" in config["loggers"][logger_name]:
                config["loggers"][logger_name]["handlers"].append("file")

        # Add to root logger
        config["root"]["handlers"].append("file")

    return config


def setup_logging() -> None:
    """
    Initialize logging configuration for the application
    """
    # Setup structlog first
    setup_structlog()

    # Get and apply logging configuration
    logging_config = get_logging_config()
    logging.config.dictConfig(logging_config)

    # Create initial application logger
    logger = logging.getLogger("labcastarr.system")

    # Log initialization
    logger.info(
        "Logging system initialized",
        extra={
            "environment": settings.environment,
            "log_level": getattr(settings, 'log_level', 'INFO'),
            "file_logging": settings.environment == "production" or getattr(settings, 'enable_file_logging', False),
            "log_file_path": getattr(settings, 'log_file_path', 'Not configured')
        }
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with proper configuration

    Args:
        name: Logger name (should follow the pattern 'labcastarr.module')

    Returns:
        Configured logger instance
    """
    # Ensure the name follows our naming convention
    if not name.startswith("labcastarr."):
        name = f"labcastarr.{name}"

    return logging.getLogger(name)


def get_structured_logger(name: str) -> FilteringBoundLogger:
    """
    Get a structured logger instance using structlog

    Args:
        name: Logger name (should follow the pattern 'labcastarr.module')

    Returns:
        Structured logger instance
    """
    # Ensure the name follows our naming convention
    if not name.startswith("labcastarr."):
        name = f"labcastarr.{name}"

    return structlog.get_logger(name)


# Convenience functions for common logger categories
def get_api_logger() -> logging.Logger:
    """Get logger for API operations"""
    return get_logger("labcastarr.api")


def get_downloader_logger() -> logging.Logger:
    """Get logger for download operations"""
    return get_logger("labcastarr.downloader")


def get_processor_logger() -> logging.Logger:
    """Get logger for media processing operations"""
    return get_logger("labcastarr.processor")


def get_rss_logger() -> logging.Logger:
    """Get logger for RSS operations"""
    return get_logger("labcastarr.rss")


def get_database_logger() -> logging.Logger:
    """Get logger for database operations"""
    return get_logger("labcastarr.database")


def get_auth_logger() -> logging.Logger:
    """Get logger for authentication operations"""
    return get_logger("labcastarr.auth")


def get_system_logger() -> logging.Logger:
    """Get logger for system operations"""
    return get_logger("labcastarr.system")