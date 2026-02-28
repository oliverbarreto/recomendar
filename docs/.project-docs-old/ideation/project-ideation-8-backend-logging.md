# Error Handling Strategy & Logging Plan for Python FastAPI

## Prompt used to generate this file
```markdown
```

---

## General Approach

- Use **exceptions as the primary mechanism** for error handling.
- Define a clear **custom error class hierarchy** using base domain exceptions.
	- Use a clearly defined custom exception hierarchy (e.g., BaseAppError, ValidationError, ExternalAPIError, DatabaseError, etc.).
	- Domain-level exceptions inherit from a shared BaseDomainError or similar to separate core logic from infrastructure.
- Consistency: All exceptions are caught at the framework level via FastAPI exception handlers.
- Avoid returning error codes/tuples — enforce clarity through `raise` + exception handling middleware.

## Logging

### Library / Method
- Use Python’s `logging` module with **`logging.config.dictConfig()`** for structured, JSON-based logging.

### Format
- **JSON** logs for better machine readability and indexing in tools like ELK, Grafana, or Datadog.
- Fields: timestamp, level, message, context (correlation ID, user, service, etc.)
- Example log entry:
```json
{
  "timestamp": "2025-05-25T16:21:00Z",
  "level": "error",
  "event": "External API call failed",
  "correlation_id": "abc123",
  "url": "https://api.example.com/data",
  "status_code": 500,
  "module": "weather_service"
}
```

### Levels
| Level     | Use Case                                                  |
|-----------|------------------------------------------------------------|
| DEBUG     | Developer-only, local debugging context                    |
| INFO      | Normal operations, request/response flow                   |
| WARNING   | Unexpected behavior, recoverable                           |
| ERROR     | Application-level errors, failed operations                |
| CRITICAL  | Service-breaking bugs, requires alerting                   |

### Context
- **Correlation ID**: Trace logs per request.
- **User ID** (if authenticated).
- **Service Name**, **Operation**, **Key Params** (sanitized).
- Exception traceback (only on ERROR+ levels).


## Specific Handling Patterns

### External API Calls
- Retry with **exponential backoff** using `tenacity`.  Retry Mechanism:
	- Exponential backoff
	- Max retries = 3–5
	- Logging on each retry
	- Timeout errors explicitly handled

- Timeouts:
	- Set connect_timeout=5, read_timeout=10 per request using httpx. Timeout: `httpx.get(..., timeout=5)`

#### Other advanced options (not used for this project):
- Catch and wrap external errors as custom `ExternalAPIError`.
- Circuit breaker (optional, if high volume): `aiobreaker` or custom pattern.

### Internal Errors / Business Logic
- Raise `BaseAppError` subclasses for domain logic.
- Example:
```python
class BaseAppError(Exception):
    message: str
    code: str

class UserNotFoundError(BaseAppError):
    message = "User not found"
    code = "USER_NOT_FOUND"
```

- Public API:
  - Catch and convert internal errors to HTTPException with:
  - status_code
  - detail with friendly message
  - error_code for frontend
  - error_id for internal tracking (logged)

- Example FastAPI handler:

```python
@app.exception_handler(BaseAppError)
async def app_exception_handler(request: Request, exc: BaseAppError):
    error_id = str(uuid.uuid4())
    log.error("App error occurred", error=exc, error_id=error_id)
    return JSONResponse(
        status_code=400,
        content={
            "message": exc.message,
            "error_code": exc.code,
            "error_id": error_id,
        }
    )
```


### Transaction Management
- Use SQLAlchemy’s context-managed transactions for DB transactions (`session.begin()`) to automatically rollback on failure.
- Example:
```python
with Session.begin():
    do_something()
    do_something_else()
```

#### Other advanced options (not used for this project):
- For non-default isolation levels (if needed):
```python
session.connection(execution_options={"isolation_level": "SERIALIZABLE"})
```
- For distributed transactions:
	- If needed, apply a **Saga pattern** with orchestrator (e.g., Kafka/NATS):
		- Choreography: via event queue (e.g., Kafka/NATS)
		- Orchestration: via a workflow engine (e.g., Temporal, AWS Step Functions)
		- Include compensating actions if one step fails

### Security Best Practices
- Never log:
	- Full tracebacks to clients
	- Secrets or tokens
	- Sensitive PII (e.g., password, SSN)
	- Mask or sanitize input logs if they might contain unsafe content.



# FastAPI Example with Structlog + Custom Error Handling

```python
# logging_config.py
import logging
import structlog

def configure_logging():
    logging.basicConfig(format="%(message)s", level=logging.INFO)
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
```

```python
# errors.py
class BaseAppError(Exception):
    def __init__(self, message: str, code: str):
        self.message = message
        self.code = code
        super().__init__(message)

class ExternalAPIError(BaseAppError):
    def __init__(self, message="External API failed"):
        super().__init__(message=message, code="EXTERNAL_API_ERROR")
```

```python
# services/external_service.py
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from errors import ExternalAPIError
import structlog

log = structlog.get_logger()

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def get_external_data(correlation_id: str):
    url = "https://httpbin.org/status/500"
    try:
        response = httpx.get(url, timeout=5)
        response.raise_for_status()
    except httpx.HTTPError as e:
        log.error("Failed API call", url=url, correlation_id=correlation_id, exc_info=e)
        raise ExternalAPIError()
    return response.json()
```

```python
# main.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from uuid import uuid4
import structlog

from errors import BaseAppError
from logging_config import configure_logging
from services.external_service import get_external_data

configure_logging()
log = structlog.get_logger()

app = FastAPI()

@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    correlation_id = str(uuid4())
    request.state.correlation_id = correlation_id
    structlog.contextvars.bind_contextvars(correlation_id=correlation_id)
    try:
        response = await call_next(request)
    finally:
        structlog.contextvars.clear_contextvars()
    return response

@app.exception_handler(BaseAppError)
async def base_app_error_handler(request: Request, exc: BaseAppError):
    error_id = str(uuid4())
    log.error("Handled application error", error_code=exc.code, error_id=error_id)
    return JSONResponse(
        status_code=400,
        content={
            "message": exc.message,
            "error_code": exc.code,
            "error_id": error_id,
        },
    )

@app.get("/external")
def call_external(request: Request):
    correlation_id = request.state.correlation_id
    data = get_external_data(correlation_id=correlation_id)
    return {"status": "ok", "data": data}
```

---

## To Run

```bash
pip install fastapi uvicorn structlog httpx tenacity
uvicorn main:app --reload
```

Then:

```bash
curl http://localhost:8000/external
```

You’ll see structured JSON logs like:

```json
{
  "timestamp": "2025-05-25T17:00:00Z",
  "level": "error",
  "event": "Failed API call",
  "url": "https://httpbin.org/status/500",
  "correlation_id": "9f31cb0b-77ff-4b90-a2df-5a8e5fcae7f7",
  "exception": "..."
}
```

---