"""
Logging service for application-level logging operations
"""
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from app.core.logging import get_structured_logger, get_system_logger
from app.domain.entities.event import Event, EventType, EventSeverity
from app.core.config import settings


class LoggingService:
    """
    Service for managing application logging operations
    """

    def __init__(self):
        self.logger = get_system_logger()
        self.structured_logger = get_structured_logger("system")

    async def log_application_start(self) -> None:
        """
        Log application startup
        """
        self.structured_logger.info(
            "LabCastARR application starting",
            environment=settings.environment,
            version=settings.app_version,
            database_url=settings.database_url.replace(settings.database_url.split('@')[-1] if '@' in settings.database_url else '', '[REDACTED]') if '@' in settings.database_url else settings.database_url,
            api_key_configured=bool(settings.api_key_secret),
            cors_origins=settings.cors_origins,
            debug_mode=settings.debug
        )

    async def log_application_shutdown(self) -> None:
        """
        Log application shutdown
        """
        self.structured_logger.info(
            "LabCastARR application shutting down",
            environment=settings.environment,
            version=settings.app_version
        )

    async def log_database_operation(
        self,
        operation: str,
        table: str,
        details: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> None:
        """
        Log database operations
        """
        log_data = {
            "operation": operation,
            "table": table,
            "success": success,
            "details": details or {}
        }

        if duration_ms is not None:
            log_data["duration_ms"] = duration_ms

        if success:
            self.structured_logger.info(
                f"Database {operation} completed",
                **log_data
            )
        else:
            log_data["error_message"] = error_message
            self.structured_logger.error(
                f"Database {operation} failed",
                **log_data
            )

    async def log_external_api_call(
        self,
        service: str,
        endpoint: str,
        method: str = "GET",
        status_code: Optional[int] = None,
        duration_ms: Optional[float] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        request_details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log external API calls
        """
        log_data = {
            "service": service,
            "endpoint": endpoint,
            "method": method,
            "success": success,
            "request_details": request_details or {}
        }

        if status_code is not None:
            log_data["status_code"] = status_code

        if duration_ms is not None:
            log_data["duration_ms"] = duration_ms

        if success:
            self.structured_logger.info(
                f"External API call to {service} completed",
                **log_data
            )
        else:
            log_data["error_message"] = error_message
            self.structured_logger.error(
                f"External API call to {service} failed",
                **log_data
            )

    async def log_file_operation(
        self,
        operation: str,
        file_path: str,
        file_size: Optional[int] = None,
        duration_ms: Optional[float] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> None:
        """
        Log file system operations
        """
        log_data = {
            "operation": operation,
            "file_path": file_path,
            "success": success
        }

        if file_size is not None:
            log_data["file_size_bytes"] = file_size

        if duration_ms is not None:
            log_data["duration_ms"] = duration_ms

        if success:
            self.structured_logger.info(
                f"File {operation} completed",
                **log_data
            )
        else:
            log_data["error_message"] = error_message
            self.structured_logger.error(
                f"File {operation} failed",
                **log_data
            )

    async def log_background_task(
        self,
        task_name: str,
        task_id: Optional[str] = None,
        status: str = "started",
        duration_ms: Optional[float] = None,
        result: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> None:
        """
        Log background task execution
        """
        log_data = {
            "task_name": task_name,
            "status": status,
            "result": result or {}
        }

        if task_id:
            log_data["task_id"] = task_id

        if duration_ms is not None:
            log_data["duration_ms"] = duration_ms

        if status == "completed":
            self.structured_logger.info(
                f"Background task {task_name} completed",
                **log_data
            )
        elif status == "failed":
            log_data["error_message"] = error_message
            self.structured_logger.error(
                f"Background task {task_name} failed",
                **log_data
            )
        else:
            self.structured_logger.info(
                f"Background task {task_name} {status}",
                **log_data
            )

    async def log_security_event(
        self,
        event_type: str,
        details: Dict[str, Any],
        severity: EventSeverity = EventSeverity.WARNING,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None
    ) -> None:
        """
        Log security-related events
        """
        log_data = {
            "event_type": event_type,
            "details": details,
            "severity": severity.value,
            "user_id": user_id,
            "ip_address": ip_address
        }

        if severity in [EventSeverity.ERROR, EventSeverity.CRITICAL]:
            self.structured_logger.error(
                f"Security event: {event_type}",
                **log_data
            )
        elif severity == EventSeverity.WARNING:
            self.structured_logger.warning(
                f"Security event: {event_type}",
                **log_data
            )
        else:
            self.structured_logger.info(
                f"Security event: {event_type}",
                **log_data
            )

    async def log_performance_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = "ms",
        context: Optional[Dict[str, Any]] = None,
        threshold_exceeded: bool = False
    ) -> None:
        """
        Log performance metrics
        """
        if not settings.enable_performance_logging:
            return

        log_data = {
            "metric_name": metric_name,
            "value": value,
            "unit": unit,
            "context": context or {},
            "threshold_exceeded": threshold_exceeded
        }

        if threshold_exceeded:
            self.structured_logger.warning(
                f"Performance threshold exceeded: {metric_name}",
                **log_data
            )
        else:
            self.structured_logger.info(
                f"Performance metric: {metric_name}",
                **log_data
            )

    async def log_error_with_context(
        self,
        error: Exception,
        context: Dict[str, Any],
        operation: Optional[str] = None,
        user_id: Optional[int] = None,
        correlation_id: Optional[str] = None
    ) -> None:
        """
        Log errors with full context
        """
        log_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "operation": operation,
            "user_id": user_id,
            "correlation_id": correlation_id
        }

        self.structured_logger.error(
            f"Error in {operation or 'unknown operation'}",
            **log_data,
            exc_info=True
        )

    async def log_system_health(
        self,
        component: str,
        status: str,
        details: Optional[Dict[str, Any]] = None,
        response_time_ms: Optional[float] = None
    ) -> None:
        """
        Log system health check results
        """
        log_data = {
            "component": component,
            "status": status,
            "details": details or {}
        }

        if response_time_ms is not None:
            log_data["response_time_ms"] = response_time_ms

        if status == "healthy":
            self.structured_logger.info(
                f"Health check passed: {component}",
                **log_data
            )
        else:
            self.structured_logger.error(
                f"Health check failed: {component}",
                **log_data
            )

    async def log_configuration_change(
        self,
        setting_name: str,
        old_value: Any,
        new_value: Any,
        changed_by: Optional[str] = None
    ) -> None:
        """
        Log configuration changes
        """
        # Sanitize sensitive values
        old_display = "[REDACTED]" if self._is_sensitive_setting(setting_name) else str(old_value)
        new_display = "[REDACTED]" if self._is_sensitive_setting(setting_name) else str(new_value)

        self.structured_logger.info(
            f"Configuration changed: {setting_name}",
            setting_name=setting_name,
            old_value=old_display,
            new_value=new_display,
            changed_by=changed_by
        )

    def _is_sensitive_setting(self, setting_name: str) -> bool:
        """
        Check if a setting contains sensitive information
        """
        sensitive_keywords = [
            'password', 'secret', 'key', 'token', 'credential',
            'auth', 'private', 'secure'
        ]
        return any(keyword in setting_name.lower() for keyword in sensitive_keywords)

    async def get_recent_logs(
        self,
        hours: int = 24,
        level: Optional[str] = None,
        component: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent log entries (placeholder for future implementation)
        This would typically read from log files or a log database
        """
        # This is a placeholder - in a real implementation, you would:
        # 1. Read from log files
        # 2. Query a log database
        # 3. Interface with a logging service

        self.logger.info(
            f"Log query requested",
            hours=hours,
            level=level,
            component=component
        )

        return []

    async def cleanup_old_logs(self, days_to_keep: int = 30) -> int:
        """
        Clean up old log files (placeholder for future implementation)
        """
        self.logger.info(f"Log cleanup requested for logs older than {days_to_keep} days")

        # This would typically:
        # 1. Find log files older than the threshold
        # 2. Archive or delete them
        # 3. Return the number of files processed

        return 0


# Global logging service instance
logging_service = LoggingService()