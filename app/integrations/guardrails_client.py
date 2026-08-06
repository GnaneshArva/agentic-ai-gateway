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
        self._endpoint = f"{settings.guardrails_service_url.rstrip('/')}/guardrails/input/validate"

    async def validate_input(
        self, context: GatewayContext, request: GatewayRequest
    ) -> None:
        if not self._enabled:
            return

        payload = {
            "text": request.prompt or "",
            "session_id": request.session_id or getattr(context.correlation, "session_id", "sess_default"),
        }

        headers = {
            "X-Request-ID": context.correlation.request_id,
            "X-Trace-ID": context.correlation.trace_id,
            "X-Correlation-ID": context.correlation.correlation_id,
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(self._endpoint, json=payload, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    if not data.get("is_allowed", True):
                        violations = data.get("metadata", {}).get("violations", [])
                        msg = violations[0]["message"] if violations else "Blocked by security policy"
                        raise PolicyException(
                            message=f"Guardrail Policy Violation: {msg}",
                            error_code="GUARDRAILS_INPUT_BLOCKED",
                            status_code=400,
                        )
                    # Update request prompt with sanitized/masked text if returned
                    if data.get("sanitized_text"):
                        request.prompt = data["sanitized_text"]
        except PolicyException:
            raise
        except Exception as e:
            logger.warning(f"Guardrails service call skipped or failed gracefully: {e}")
