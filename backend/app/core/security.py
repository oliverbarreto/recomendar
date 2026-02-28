"""
Security middleware and utilities
"""
import time
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.requests: Dict[str, list] = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ["/health/", "/health/db", "/health/detailed"]:
            return await call_next(request)
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        
        # Clean old requests
        self._clean_old_requests(client_ip, current_time)
        
        # Check rate limit
        if self._is_rate_limited(client_ip, current_time):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {settings.rate_limit_requests} requests per {settings.rate_limit_period} seconds.",
                headers={"Retry-After": str(settings.rate_limit_period)}
            )
        
        # Add current request
        self.requests[client_ip].append(current_time)
        
        # Process request
        response = await call_next(request)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def _clean_old_requests(self, client_ip: str, current_time: float) -> None:
        """Remove requests older than the rate limit period"""
        cutoff_time = current_time - settings.rate_limit_period
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > cutoff_time
        ]
    
    def _is_rate_limited(self, client_ip: str, current_time: float) -> bool:
        """Check if client has exceeded rate limit"""
        return len(self.requests[client_ip]) >= settings.rate_limit_requests


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Security headers middleware
    """
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        
        if settings.security_headers_enabled:
            # Security headers
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
            
            # Content Security Policy - relaxed for Swagger UI to work
            is_docs_request = request.url.path in ["/docs", "/redoc"] or request.url.path.startswith("/docs/")
            
            if is_docs_request:
                # More permissive CSP for documentation pages
                csp = (
                    "default-src 'self'; "
                    "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
                    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                    "img-src 'self' data: https: https://cdn.jsdelivr.net https://fastapi.tiangolo.com; "
                    "font-src 'self' https://cdn.jsdelivr.net; "
                    "connect-src 'self'"
                )
            else:
                # Strict CSP for other pages
                csp = (
                    "default-src 'self'; "
                    "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                    "style-src 'self' 'unsafe-inline'; "
                    "img-src 'self' data: https:; "
                    "font-src 'self'; "
                    "connect-src 'self'"
                )
            response.headers["Content-Security-Policy"] = csp
            
            # HSTS (only in production)
            if not settings.debug:
                response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


def validate_host(request: Request) -> bool:
    """
    Validate request host against allowed hosts
    """
    host = request.headers.get("host", "").split(":")[0]
    return host in settings.allowed_hosts or host == ""


async def security_check_middleware(request: Request, call_next):
    """
    General security check middleware
    """
    # Host validation
    if not validate_host(request):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid host"
        )
    
    response = await call_next(request)
    return response