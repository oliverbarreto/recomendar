---
title: "(22) Best Practices for Logging in FastAPI Applications | LinkedIn"
source: "https://www.linkedin.com/pulse/best-practices-logging-fastapi-applications-manikandan-parasuraman-96n2c/"
author:
published: 27 de diciembre de 2024
created: 2025-05-25
description:
tags:
  - "clippings"
---

# Best Practices for Logging in FastAPI Applications

Logging is a critical component of any application, and FastAPI is no exception. Proper logging helps monitor the application, debug issues, and gain insights into its behavior. Here's a comprehensive guide to implementing and managing logging in FastAPI applications.

---

### Why Logging Matters in FastAPI

1. **Debugging and Troubleshooting**: Quickly identify and resolve errors.
2. **Performance Monitoring**: Track performance bottlenecks and optimize the system.
3. **Audit and Compliance**: Maintain a record of significant events for auditing purposes.
4. **User Behavior Tracking**: Understand user interactions with the application.

---

### Best Practices for Logging in FastAPI

### 1. Set Up a Logging Configuration

Leverage Python’s logging module to define a robust logging configuration.

```python
import logging
from logging.config import dictConfig

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "json": {
            "format": '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}'
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default"
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": "app.log",
            "formatter": "json"
        },
    },
    "loggers": {
        "uvicorn": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False
        },
        "app": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False
        },
    },
}

dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("app")
```

### 2. Integrate Logging with Uvicorn

Since FastAPI often runs with Uvicorn, configure Uvicorn's logging to work seamlessly with your application’s logs.

```bash
uvicorn app:app --log-config logging.yaml
```

### 3. Use Logging Levels Effectively

Adopt appropriate logging levels to categorize log entries:

- DEBUG: Detailed diagnostic information.
- INFO: General operational events.
- WARNING: Unusual situations that aren’t errors.
- ERROR: Issues that disrupt normal operation.
- CRITICAL: Severe problems that require immediate attention.

### 4. Structure Logs for Readability

Use JSON or structured logging formats to ensure compatibility with log aggregation and monitoring tools like ELK Stack, Splunk, or Datadog.

### 5. Capture Exceptions and Tracebacks

Wrap critical sections of code in try-except blocks and log exceptions.

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def read_root():
    try:
        # Simulate some operation
        result = 10 / 0
    except Exception as e:
        logger.error("An error occurred", exc_info=True)
        return {"error": "Something went wrong"}
    return {"message": "Hello, World!"}
```

### 6. Avoid Logging Sensitive Information

Ensure that personally identifiable information (PII) and sensitive data are not logged. Mask or redact such information if necessary.

```python   
logger.info("User logged in with email: %s", mask_email(user.email))
```

### 7. Leverage Middleware for Request and Response Logging

Create custom middleware to log HTTP requests and responses.

```python
from fastapi.middleware import Middleware

class LoggingMiddleware:
    async def __call__(self, scope, receive, send):
        logger.info(f"Request: {scope['method']} {scope['path']}")
        await send(receive)
        logger.info("Response sent")

middleware = [Middleware(LoggingMiddleware)]
```

### 8. Use Contextual Logging

Add context to log entries using structured fields like request IDs or user IDs.

```python
import uuid
from fastapi import Request

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    logger = logging.getLogger("app")
    logger = logger.bind(request_id=request_id)
    response = await call_next(request)
    logger.info(f"Request completed with status {response.status_code}")
    return response
```

### 9. Rotate Log Files

Use tools like logging.handlers.RotatingFileHandler to rotate log files and prevent them from growing indefinitely.

```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler("app.log", maxBytes=2000000, backupCount=5)
```

### 10. Integrate with Monitoring Tools

Send logs to external monitoring systems for real-time analysis.

- **Elastic Stack**: Use Filebeat to ship logs to Elasticsearch.
- **Datadog**: Integrate FastAPI with Datadog's logging module.
- **Prometheus**: Use FastAPI's integration with Prometheus for performance monitoring.

---

### Example: Complete Logging Setup in FastAPI

```python
from fastapi import FastAPI, Request
import logging
from logging.config import dictConfig

LOGGING_CONFIG = { ... }  # Use the LOGGING_CONFIG example above

dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("app")

app = FastAPI()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

@app.get("/")
async def home():
    logger.info("Processing home endpoint")
    return {"message": "Welcome to FastAPI Logging Best Practices"}
```


### Conclusion

By following these best practices, you can ensure your FastAPI application logs are comprehensive, useful, and maintainable. Proper logging can save hours of debugging and provide invaluable insights into your application's behavior, making it an essential part of your development workflow.

