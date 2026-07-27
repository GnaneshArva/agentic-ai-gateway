from datetime import datetime, timezone
from app.config.settings import Settings
from app.dto.context_dto import GatewayContext
from app.dto.request_dto import GatewayRequest


class RequestEnricher:
    def __init__(self, settings: Settings):
        self._settings = settings

    def enrich(self, context: GatewayContext, request: GatewayRequest) -> GatewayContext:
        context.gateway_version = self._settings.gateway_config.gateway_version
        context.environment = self._settings.app_env
        context.custom_attributes.update(
            {
                "enriched_at": datetime.now(timezone.utc).isoformat(),
                "provider": request.provider or "OpenAI",
                "model": request.model or "gpt-4o",
                "client_app": request.app_id or "default_app",
            }
        )
        return context
