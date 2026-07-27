import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional
from app.config.settings import Settings
from app.dto.context_dto import (
    CorrelationContext,
    GatewayContext,
    RequestContext,
    RoutingContext,
)
from app.dto.request_dto import GatewayRequest


class CorrelationManager:
    def __init__(self, settings: Settings):
        self._settings = settings

    def create_context(
        self,
        request: GatewayRequest,
        headers: Optional[Dict[str, str]] = None,
    ) -> GatewayContext:
        headers = headers or {}
        
        request_id = (
            headers.get("x-request-id")
            or headers.get("X-Request-ID")
            or f"req_{uuid.uuid4().hex[:12]}"
        )
        trace_id = (
            headers.get("x-trace-id")
            or headers.get("X-Trace-ID")
            or f"trc_{uuid.uuid4().hex[:16]}"
        )
        correlation_id = (
            headers.get("x-correlation-id")
            or headers.get("X-Correlation-ID")
            or f"cor_{uuid.uuid4().hex[:16]}"
        )

        correlation = CorrelationContext(
            request_id=request_id,
            trace_id=trace_id,
            correlation_id=correlation_id,
            timestamp=datetime.now(timezone.utc),
        )

        request_info = RequestContext(
            user_id=request.user_id or "anonymous",
            tenant_id=request.tenant_id or "default",
            app_id=request.app_id or "default_app",
            session_id=request.session_id,
            conversation_id=request.conversation_id,
        )

        routing_info = RoutingContext(
            provider=request.provider or "OpenAI",
            model=request.model or "gpt-4o",
            target_service=request.target_service,
        )

        return GatewayContext(
            correlation=correlation,
            request_info=request_info,
            routing=routing_info,
            start_time_monotonic=time.monotonic(),
            gateway_version=self._settings.gateway_config.gateway_version,
            environment=self._settings.app_env,
        )
