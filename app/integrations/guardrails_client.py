from typing import Any, Dict, Optional
import httpx
from app.config.settings import Settings
from app.dto.context_dto import GatewayContext
from app.dto.request_dto import GatewayRequest
from app.exceptions.gateway_exceptions import PolicyException
from app.utils.logger import get_logger

logger = get_logger("GuardrailsClient")


class GuardrailsClient:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._enabled = settings.feature_flags.enable_guardrails
        self._endpoint = f"{settings.guardrails_service_url.rstrip('/')}/api/v1/guardrails/validate/input"

    async def validate_input(
        self, context: GatewayContext, request: GatewayRequest
    ) -> None:
        if not self._enabled:
            return

        payload = {
            "prompt": request.prompt or "",
            "messages": [m.model_dump() for m in (request.messages or [])],
            "user_id": request.user_id,
            "session_id": request.session_id,
        }

        headers = {
            "X-Request-ID": context.correlation.request_id,
            "X-Trace-ID": context.correlation.trace_id,
            "X-Correlation-ID": context.correlation.correlation_id,
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(self._endpoint, json=payload, headers=headers)
                if response.status_code == 400 or response.status_code == 422:
                    data = response.json()
                    raise PolicyException(
                        message=f"Guardrails input validation rejected request: {data.get('detail', 'Policy violation')}",
                        error_code="GUARDRAILS_VIOLATION",
                        status_code=400,
                    )
        except PolicyException:
            raise
        except Exception as e:
            logger.warning(f"Guardrails service call skipped or failed gracefully: {e}")
