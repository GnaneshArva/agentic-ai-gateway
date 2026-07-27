from datetime import datetime, timezone
from typing import Any, Dict, Optional
import httpx
from app.config.settings import Settings
from app.dto.context_dto import GatewayContext
from app.utils.logger import get_logger

logger = get_logger("ObservabilityClient")


class ObservabilityClient:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._enabled = settings.feature_flags.enable_telemetry
        self._endpoint = f"{settings.observability_service_url.rstrip('/')}/api/v1/telemetry/events"

    async def publish_event(
        self,
        event_type: str,
        context: GatewayContext,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not self._enabled:
            return

        event_data = {
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": context.correlation.request_id,
            "trace_id": context.correlation.trace_id,
            "correlation_id": context.correlation.correlation_id,
            "gateway_version": context.gateway_version,
            "environment": context.environment,
            "user_id": context.request_info.user_id,
            "tenant_id": context.request_info.tenant_id,
            "target_service": context.routing.target_service,
            "payload": payload or {},
        }

        # Non-blocking async publish with failure isolation
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.post(self._endpoint, json=event_data)
                if response.status_code >= 400:
                    logger.warning(
                        f"Observability service returned status {response.status_code} for event '{event_type}'"
                    )
        except Exception as e:
            # FAILURE ISOLATION: Observability failures must never block request flow
            logger.warning(
                f"Failed to publish telemetry event '{event_type}' to observability service: {e}"
            )
