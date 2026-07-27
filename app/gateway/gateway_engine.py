from typing import AsyncGenerator
from app.config.settings import Settings, get_settings
from app.dto.context_dto import GatewayContext
from app.dto.request_dto import GatewayRequest
from app.dto.response_dto import GatewayResponse, StreamingResponseDTO
from app.factories import PolicyFactory, RouterFactory, StrategyFactory, ValidatorFactory
from app.gateway.request_enricher import RequestEnricher
from app.integrations import DownstreamForwarder, GuardrailsClient, ObservabilityClient
from app.pipeline.gateway_pipeline import DefaultGatewayPipeline
from app.services import CorrelationManager, ResponseProcessor


class GatewayEngine:
    def __init__(self, settings: Settings = None):
        self._settings = settings or get_settings()

        # Factories & Components setup
        self._validator = ValidatorFactory.create_validator()
        self._enricher = RequestEnricher(self._settings)
        self._policies = PolicyFactory.create_policies(self._settings)
        self._router = RouterFactory.create_router(self._settings)

        # Strategies
        self._retry_strategy = StrategyFactory.create_retry_strategy(self._settings)
        self._circuit_breaker = StrategyFactory.create_circuit_breaker(self._settings)
        self._response_strategy = StrategyFactory.create_response_strategy()

        # Services & Integrations
        self._correlation_manager = CorrelationManager(self._settings)
        self._response_processor = ResponseProcessor(self._response_strategy)
        self._observability = ObservabilityClient(self._settings)
        self._guardrails = GuardrailsClient(self._settings)

        self._forwarder = DownstreamForwarder(
            settings=self._settings,
            retry_strategy=self._retry_strategy,
            circuit_breaker=self._circuit_breaker,
            response_processor=self._response_processor,
        )

        # Pipeline
        self._pipeline = DefaultGatewayPipeline(
            settings=self._settings,
            validator=self._validator,
            enricher=self._enricher,
            policies=self._policies,
            router=self._router,
            forwarder=self._forwarder,
            observability=self._observability,
            guardrails=self._guardrails,
        )

    def create_context(self, request: GatewayRequest, headers: dict = None) -> GatewayContext:
        return self._correlation_manager.create_context(request, headers)

    async def process_request(
        self, request: GatewayRequest, headers: dict = None
    ) -> GatewayResponse:
        context = self.create_context(request, headers)
        return await self._pipeline.execute(context, request)

    async def process_stream(
        self, request: GatewayRequest, headers: dict = None
    ) -> AsyncGenerator[StreamingResponseDTO, None]:
        context = self.create_context(request, headers)
        async for chunk in self._pipeline.execute_stream(context, request):
            yield chunk
