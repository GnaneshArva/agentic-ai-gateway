import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class CorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:12]}"
        trace_id = request.headers.get("X-Trace-ID") or f"trc_{uuid.uuid4().hex[:16]}"
        correlation_id = (
            request.headers.get("X-Correlation-ID") or f"cor_{uuid.uuid4().hex[:16]}"
        )

        request.state.request_id = request_id
        request.state.trace_id = trace_id
        request.state.correlation_id = correlation_id

        response = await call_next(request)

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Trace-ID"] = trace_id
        response.headers["X-Correlation-ID"] = correlation_id

        return response
