import time
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from app.utils.logger import get_logger

logger = get_logger("LoggingMiddleware")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start_time = time.monotonic()
        path = request.url.path
        method = request.method

        response = await call_next(request)

        duration_ms = (time.monotonic() - start_time) * 1000.0
        req_id = getattr(request.state, "request_id", "-")

        logger.info(
            f"HTTP {method} {path} -> {response.status_code} ({duration_ms:.2f}ms) [req_id={req_id}]"
        )
        return response
