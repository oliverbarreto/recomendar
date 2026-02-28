"""
Logging middleware for request/response tracking and user activity logging
"""
import time
import uuid
from typing import Callable, Optional, Dict, Any
import json

from fastapi import Request, Response
from fastapi.responses import StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import settings
from app.core.logging import get_api_logger, get_structured_logger
from app.domain.entities.event import Event, EventType, EventSeverity


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for comprehensive request/response logging and user activity tracking
    """

    def __init__(
        self,
        app: ASGIApp,
        skip_paths: Optional[list] = None,
        enable_request_body_logging: bool = False
    ):
        super().__init__(app)
        self.logger = get_api_logger()
        self.structured_logger = get_structured_logger("api")
        self.skip_paths = skip_paths or ["/health", "/docs", "/redoc", "/openapi.json"]
        self.enable_request_body_logging = enable_request_body_logging

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and response with comprehensive logging
        """
        # Skip logging for certain paths
        if any(request.url.path.startswith(path) for path in self.skip_paths):
            return await call_next(request)

        # Generate correlation ID for request tracing
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        # Start timing
        start_time = time.time()

        # Extract request information
        request_info = await self._extract_request_info(request)

        # Log request start
        if settings.enable_request_logging:
            self._log_request_start(request_info, correlation_id)

        # Process request and handle errors
        try:
            response = await call_next(request)

            # Calculate processing time
            processing_time = time.time() - start_time

            # Extract response information
            response_info = self._extract_response_info(response, processing_time)

            # Log request completion
            if settings.enable_request_logging:
                self._log_request_completion(request_info, response_info, correlation_id)

            # Log user activity if applicable
            if self._should_log_user_activity(request, response):
                await self._log_user_activity(request, response, request_info, response_info)

            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id

            return response

        except Exception as e:
            # Calculate processing time
            processing_time = time.time() - start_time

            # Log error
            self._log_request_error(request_info, str(e), processing_time, correlation_id)

            # Re-raise the exception
            raise e

    async def _extract_request_info(self, request: Request) -> Dict[str, Any]:
        """
        Extract comprehensive request information
        """
        # Get client IP (handle proxies)
        client_ip = self._get_client_ip(request)

        # Extract user information from JWT token if available
        user_id, user_email = await self._extract_user_from_jwt(request)

        # Store user info in request state for other middleware/endpoints
        if user_id:
            request.state.user_id = user_id
            request.state.user_email = user_email

        # Get API key information
        api_key_header = request.headers.get(settings.api_key_header, "Not provided")
        api_key_used = api_key_header != "Not provided"

        # Extract request body for certain endpoints (with size limit)
        request_body = None
        if (self.enable_request_body_logging and
            request.method in ["POST", "PUT", "PATCH"] and
            request.headers.get("content-type", "").startswith("application/json")):
            try:
                # Only log small payloads
                content_length = int(request.headers.get("content-length", 0))
                if content_length < 1024:  # Max 1KB
                    body = await request.body()
                    if body:
                        request_body = body.decode('utf-8')[:500]  # Truncate to 500 chars
            except Exception:
                request_body = "[Unable to read request body]"

        return {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": self._sanitize_headers(dict(request.headers)),
            "client_ip": client_ip,
            "user_agent": request.headers.get("user-agent", "Unknown"),
            "user_id": user_id,
            "user_email": user_email,
            "api_key_used": api_key_used,
            "request_body": request_body,
            "content_type": request.headers.get("content-type"),
            "content_length": request.headers.get("content-length"),
        }

    def _extract_response_info(self, response: Response, processing_time: float) -> Dict[str, Any]:
        """
        Extract response information
        """
        return {
            "status_code": response.status_code,
            "headers": self._sanitize_headers(dict(response.headers)),
            "processing_time_ms": round(processing_time * 1000, 2),
            "content_type": response.headers.get("content-type"),
            "content_length": response.headers.get("content-length"),
        }

    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP address, handling common proxy headers
        """
        # Check common proxy headers
        forwarded_headers = [
            "X-Forwarded-For",
            "X-Real-IP",
            "X-Forwarded",
            "Forwarded-For",
            "Forwarded"
        ]

        for header in forwarded_headers:
            if header in request.headers:
                # X-Forwarded-For can contain multiple IPs, take the first one
                ip = request.headers[header].split(',')[0].strip()
                if ip:
                    return ip

        # Fallback to client host
        if hasattr(request.client, 'host'):
            return request.client.host

        return "unknown"

    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """
        Sanitize sensitive headers before logging
        """
        sensitive_headers = {
            'authorization', 'x-api-key', 'cookie', 'set-cookie',
            'x-auth-token', 'x-session-token', 'x-csrf-token'
        }

        sanitized = {}
        for key, value in headers.items():
            if key.lower() in sensitive_headers:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = value

        return sanitized

    def _log_request_start(self, request_info: Dict[str, Any], correlation_id: str) -> None:
        """
        Log request start
        """
        self.structured_logger.info(
            "Request started",
            correlation_id=correlation_id,
            method=request_info["method"],
            path=request_info["path"],
            client_ip=request_info["client_ip"],
            user_agent=request_info["user_agent"],
            user_id=request_info["user_id"],
            api_key_used=request_info["api_key_used"]
        )

    def _log_request_completion(
        self,
        request_info: Dict[str, Any],
        response_info: Dict[str, Any],
        correlation_id: str
    ) -> None:
        """
        Log successful request completion
        """
        log_level = "info"

        # Determine log level based on status code
        if response_info["status_code"] >= 500:
            log_level = "error"
        elif response_info["status_code"] >= 400:
            log_level = "warning"

        log_method = getattr(self.structured_logger, log_level)

        log_method(
            "Request completed",
            correlation_id=correlation_id,
            method=request_info["method"],
            path=request_info["path"],
            status_code=response_info["status_code"],
            processing_time_ms=response_info["processing_time_ms"],
            client_ip=request_info["client_ip"],
            user_id=request_info["user_id"],
            content_length=response_info.get("content_length")
        )

        # Log performance warning for slow requests
        if (settings.enable_performance_logging and
            response_info["processing_time_ms"] > 1000):  # > 1 second
            self.structured_logger.warning(
                "Slow request detected",
                correlation_id=correlation_id,
                method=request_info["method"],
                path=request_info["path"],
                processing_time_ms=response_info["processing_time_ms"],
                user_id=request_info["user_id"]
            )

    def _log_request_error(
        self,
        request_info: Dict[str, Any],
        error_message: str,
        processing_time: float,
        correlation_id: str
    ) -> None:
        """
        Log request error
        """
        self.structured_logger.error(
            "Request failed",
            correlation_id=correlation_id,
            method=request_info["method"],
            path=request_info["path"],
            error_message=error_message,
            processing_time_ms=round(processing_time * 1000, 2),
            client_ip=request_info["client_ip"],
            user_id=request_info["user_id"]
        )

    def _should_log_user_activity(self, request: Request, response: Response) -> bool:
        """
        Determine if this request should generate a user activity event
        """
        # Only log successful user actions (2xx status codes)
        if not (200 <= response.status_code < 300):
            return False

        # Only log for authenticated users with user_id
        if not hasattr(request.state, 'user_id') or not request.state.user_id:
            return False

        # Only log state-changing operations
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            return True

        # Log certain GET operations that represent user actions
        user_action_paths = [
            "/v1/episodes/",  # Episode access
            "/v1/feeds/",     # Feed access
            "/v1/media/",     # Media access
        ]

        return any(request.url.path.startswith(path) for path in user_action_paths)

    async def _log_user_activity(
        self,
        request: Request,
        response: Response,
        request_info: Dict[str, Any],
        response_info: Dict[str, Any]
    ) -> None:
        """
        Log user activity as an event and save to database
        """
        try:
            # Determine action based on method and path
            action = self._determine_user_action(request.method, request.url.path)

            # Determine resource type and ID
            resource_type, resource_id = self._extract_resource_info(request.url.path)

            # Get channel ID (default to 1 if not found - for now)
            channel_id = getattr(request.state, 'channel_id', 1)

            # Get user ID from request state
            user_id = request.state.user_id
            if not user_id:
                return  # Skip if no authenticated user

            # Create user activity event and save to database
            from app.infrastructure.database.connection import get_async_db
            from app.application.services.event_service import EventService

            async for db in get_async_db():
                try:
                    event_service = EventService(db)

                    # Save user action event to database
                    event = await event_service.log_user_action(
                        channel_id=channel_id,
                        user_id=user_id,
                        action=action,
                        resource_type=resource_type,
                        resource_id=resource_id,
                        message=f"User {action} {resource_type}" + (f" {resource_id}" if resource_id else ""),
                        details={
                            "method": request.method,
                            "path": request.url.path,
                            "status_code": response.status_code,
                            "processing_time_ms": response_info["processing_time_ms"],
                            "correlation_id": getattr(request.state, 'correlation_id', None)
                        },
                        severity=EventSeverity.INFO,
                        ip_address=request_info["client_ip"],
                        user_agent=request_info["user_agent"]
                    )

                    # Log successful event creation
                    self.structured_logger.info(
                        "User activity event saved",
                        event_id=event.id,
                        event_type=event.event_type.value,
                        action=event.action,
                        resource_type=event.resource_type,
                        resource_id=event.resource_id,
                        user_id=event.user_id,
                        channel_id=event.channel_id,
                        correlation_id=getattr(request.state, 'correlation_id', None)
                    )
                    break

                except Exception as db_error:
                    self.logger.error(f"Failed to save user activity event to database: {db_error}")

                    # Fallback: at least log the activity without saving to DB
                    self.structured_logger.info(
                        "User activity logged (DB save failed)",
                        action=action,
                        resource_type=resource_type,
                        resource_id=resource_id,
                        user_id=user_id,
                        channel_id=channel_id,
                        correlation_id=getattr(request.state, 'correlation_id', None),
                        error=str(db_error)
                    )

        except Exception as e:
            # Don't fail the request if user activity logging fails
            self.logger.error(f"Failed to log user activity: {e}")

    def _determine_user_action(self, method: str, path: str) -> str:
        """
        Determine user action based on HTTP method and path
        """
        if method == "GET":
            if "/episodes/" in path:
                return "view_episode"
            elif "/feeds/" in path:
                return "access_feed"
            elif "/media/" in path:
                return "stream_media"
            elif "/channels/" in path:
                return "view_channel"
            else:
                return "view_resource"
        elif method == "POST":
            if "/episodes" in path:
                return "create_episode"
            elif "/channels" in path:
                return "create_channel"
            elif "/tags" in path:
                return "create_tag"
            else:
                return "create_resource"
        elif method == "PUT" or method == "PATCH":
            if "/episodes/" in path:
                return "update_episode"
            elif "/channels/" in path:
                return "update_channel"
            elif "/tags/" in path:
                return "update_tag"
            else:
                return "update_resource"
        elif method == "DELETE":
            if "/episodes/" in path:
                return "delete_episode"
            elif "/channels/" in path:
                return "delete_channel"
            elif "/tags/" in path:
                return "delete_tag"
            else:
                return "delete_resource"
        else:
            return f"{method.lower()}_resource"

    def _extract_resource_info(self, path: str) -> tuple[str, Optional[str]]:
        """
        Extract resource type and ID from the path
        """
        path_parts = path.strip('/').split('/')

        # Map path patterns to resource types
        if 'episodes' in path_parts:
            resource_type = "episode"
            # Try to find episode ID
            try:
                episode_index = path_parts.index('episodes')
                if episode_index + 1 < len(path_parts) and path_parts[episode_index + 1].isdigit():
                    return resource_type, path_parts[episode_index + 1]
            except (ValueError, IndexError):
                pass
            return resource_type, None
        elif 'channels' in path_parts:
            resource_type = "channel"
            try:
                channel_index = path_parts.index('channels')
                if channel_index + 1 < len(path_parts) and path_parts[channel_index + 1].isdigit():
                    return resource_type, path_parts[channel_index + 1]
            except (ValueError, IndexError):
                pass
            return resource_type, None
        elif 'feeds' in path_parts:
            resource_type = "feed"
            try:
                feed_index = path_parts.index('feeds')
                if feed_index + 1 < len(path_parts) and path_parts[feed_index + 1].isdigit():
                    return resource_type, path_parts[feed_index + 1]
            except (ValueError, IndexError):
                pass
            return resource_type, None
        elif 'tags' in path_parts:
            resource_type = "tag"
            try:
                tag_index = path_parts.index('tags')
                if tag_index + 1 < len(path_parts) and path_parts[tag_index + 1].isdigit():
                    return resource_type, path_parts[tag_index + 1]
            except (ValueError, IndexError):
                pass
            return resource_type, None
        elif 'media' in path_parts:
            resource_type = "media"
            return resource_type, None
        else:
            return "unknown", None

    async def _extract_user_from_jwt(self, request: Request) -> tuple[Optional[int], Optional[str]]:
        """
        Extract user information from JWT token in Authorization header
        """
        try:
            # Check for Authorization header
            auth_header = request.headers.get("authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return None, None

            # Extract token
            token = auth_header.replace("Bearer ", "")
            if not token:
                return None, None

            # Verify token and extract payload
            from app.core.jwt import get_jwt_service
            jwt_service = get_jwt_service()
            payload = jwt_service.verify_token(token)

            if not payload:
                return None, None

            # Extract user information from payload
            user_id = payload.get("user_id")
            user_email = payload.get("email")

            return user_id, user_email

        except Exception as e:
            # Don't fail the request if JWT extraction fails
            self.logger.debug(f"Failed to extract user from JWT: {e}")
            return None, None