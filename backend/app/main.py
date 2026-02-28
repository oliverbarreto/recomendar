from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.security import RateLimitMiddleware, SecurityHeadersMiddleware, security_check_middleware
from app.core.logging import setup_logging, get_system_logger
from app.core.middleware.logging_middleware import LoggingMiddleware
from app.infrastructure.services.logging_service import logging_service

from app.presentation.api.health import router as health_router
from app.presentation.api.v1.router import v1_router

from app.infrastructure.database.connection import init_db

# Initialize logging system BEFORE creating FastAPI app
setup_logging()
logger = get_system_logger()

app = FastAPI(
    title=settings.app_name,
    description="A podcast channel for your Homelab - Backend API",
    version=settings.app_version,
    redirect_slashes=False  # Prevent redirects that break POST requests
)

# Configure middleware (order matters!)
# 1. Security headers (outermost)
app.add_middleware(SecurityHeadersMiddleware)

# 2. Logging middleware (early to capture all requests)
if settings.enable_request_logging:
    app.add_middleware(
        LoggingMiddleware,
        skip_paths=["/health", "/docs", "/redoc", "/openapi.json", "/favicon.ico"],
        enable_request_body_logging=settings.environment == "development"
    )

# 3. Rate limiting
app.add_middleware(RateLimitMiddleware)

# 4. CORS (should be after rate limiting but before auth)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "HEAD", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 5. Add security check middleware
app.middleware("http")(security_check_middleware)

# Include routers
app.include_router(health_router)
app.include_router(v1_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Custom handler for Pydantic validation errors (422)
    
    Logs detailed validation errors for debugging
    """
    errors = exc.errors()
    error_details = []
    error_messages = []
    
    for error in errors:
        field = ".".join(str(loc) for loc in error.get("loc", []))
        message = error.get("msg", "Validation error")
        error_type = error.get("type")
        
        error_details.append({
            "field": field,
            "message": message,
            "type": error_type,
            "input": error.get("input")
        })
        
        # Create a human-readable error message
        if field:
            error_messages.append(f"{field}: {message}")
        else:
            error_messages.append(message)
    
    # Try to get request body for logging (may already be consumed)
    body_str = None
    try:
        if request.method in ["POST", "PUT", "PATCH"]:
            body_bytes = await request.body()
            body_str = body_bytes.decode('utf-8') if body_bytes else None
    except Exception:
        # Body may already be consumed, that's ok
        pass
    
    # Log the validation error with full details
    logger.warning(
        f"Request validation failed for {request.method} {request.url.path}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "validation_errors": error_details,
            "request_body": body_str,
            "error_message": "; ".join(error_messages)
        }
    )
    
    # Also log the raw errors for debugging
    logger.error(
        f"Validation error details: {error_details}",
        exc_info=False
    )
    
    # Return both detailed errors (for debugging) and a formatted message (for UI)
    formatted_message = "; ".join(error_messages) if error_messages else "Validation error"
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": error_details,  # Keep detailed errors for debugging
            "message": formatted_message,  # Add a formatted message for UI
            "body": body_str
        }
    )


@app.on_event("startup")
async def startup_event():
    """
    Application startup event
    """
    # Log application startup
    await logging_service.log_application_start()
    logger.info("LabCastARR application startup initiated")

    try:
        # Initialize database
        logger.info("Initializing database connection")
        await init_db()
        logger.info("Database initialization completed")

        # Initialize default data (user and channel)
        from app.application.services.initialization_service import InitializationService

        initialization_service = InitializationService()

        logger.info("Starting default data initialization")
        result = await initialization_service.ensure_default_data()

        if result["user_created"] or result["user_migrated"] or result["channel_created"]:
            logger.info("Default data initialized successfully")
            if result["user_created"]:
                logger.info(f"Created default user (ID: {result['user_id']})")
            if result["user_migrated"]:
                logger.info(f"Migrated existing user (ID: {result['user_id']})")
                for change in result["migration_changes"]:
                    logger.info(f"Migration change: {change}")
            if result["channel_created"]:
                logger.info(f"Created default channel (ID: {result['channel_id']})")
        else:
            logger.info(f"Default data already exists (User ID: {result['user_id']}, Channel ID: {result['channel_id']})")

        if result["errors"]:
            logger.warning(f"Initialization warnings: {result['errors']}")

        # Initialize and validate JWT service configuration
        from app.core.jwt import get_jwt_service

        try:
            jwt_service = get_jwt_service()
            logger.info("JWT service initialized successfully")
            logger.info(f"Environment: {settings.environment}")
            logger.info(f"JWT Algorithm: {settings.jwt_algorithm}")
            logger.info(f"Access token expiry: {settings.jwt_access_token_expire_minutes} minutes")
            logger.info(f"Refresh token expiry: {settings.jwt_refresh_token_expire_days} days")

            if settings.jwt_secret_key == "your-secret-key-change-in-production":
                logger.warning("JWT secret key is using default value - change in production!")
            else:
                logger.info(f"JWT secret key configured (length: {len(settings.jwt_secret_key)} chars)")

        except Exception as jwt_error:
            logger.error(f"Failed to initialize JWT service: {jwt_error}")
            await logging_service.log_error_with_context(
                jwt_error,
                {"component": "jwt_service", "operation": "initialization"}
            )

        logger.info("LabCastARR application startup completed successfully")

    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        await logging_service.log_error_with_context(
            e,
            {"component": "application", "operation": "startup"}
        )
        # Don't prevent app startup if initialization fails


@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown event
    """
    logger.info("LabCastARR application shutdown initiated")
    await logging_service.log_application_shutdown()
    logger.info("LabCastARR application shutdown completed")


@app.get("/")
async def root():
    return {
        "message": "Welcome to LabCastARR API",
        "service": settings.app_name,
        "version": settings.app_version,
        "docs_url": "/docs"
    }
