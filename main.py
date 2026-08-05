import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.gzip import GZipMiddleware
from app.config import get_settings
from app.controllers import gateway_router, health_router
from app.dto.response_dto import ErrorResponse
from app.exceptions.gateway_exceptions import GatewayException
from app.middleware import CorrelationMiddleware, LoggingMiddleware, TelemetryMiddleware
from app.utils.logger import setup_logger

settings = get_settings()
logger = setup_logger(name=settings.app_name, level=settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name} on port {settings.port} ({settings.app_env})...")
    yield
    logger.info(f"Shutting down {settings.app_name}...")


app = FastAPI(
    title="Agentic AI Gateway",
    description="Enterprise AI Gateway for AI Request Validation, Policy Governance, Routing, Resiliency, and Telemetry Integration",
    version="1.0.0",
    lifespan=lifespan,
)

# Add Middlewares
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(TelemetryMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(CorrelationMiddleware)

# Include Routers
app.include_router(health_router)
app.include_router(gateway_router)


# Global Exception Handler for Gateway Exceptions
@app.exception_handler(GatewayException)
async def gateway_exception_handler(request: Request, exc: GatewayException):
    req_id = getattr(request.state, "request_id", f"req_{uuid.uuid4().hex[:12]}")
    error_dto = ErrorResponse(
        error_code=exc.error_code,
        message=exc.message,
        status_code=exc.status_code,
        retryable=exc.retryable,
        component=exc.component,
        details=exc.details,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_dto.model_dump(),
        headers={"X-Request-ID": req_id},
    )


# Fallback Exception Handler for uncaught exceptions
@app.exception_handler(Exception)
async def uncaught_exception_handler(request: Request, exc: Exception):
    logger.error(f"Uncaught exception: {exc}", exc_info=True)
    req_id = getattr(request.state, "request_id", f"req_{uuid.uuid4().hex[:12]}")
    error_dto = ErrorResponse(
        error_code="INTERNAL_SERVER_ERROR",
        message=str(exc),
        status_code=500,
        retryable=False,
        component="agentic-ai-gateway",
    )
    return JSONResponse(
        status_code=500,
        content=error_dto.model_dump(),
        headers={"X-Request-ID": req_id},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=settings.port, reload=True)
