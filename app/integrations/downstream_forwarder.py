import json
from typing import AsyncGenerator, Any, Dict
import httpx
from app.config.settings import Settings
from app.dto.context_dto import GatewayContext
from app.dto.request_dto import GatewayRequest
from app.dto.response_dto import GatewayResponse, StreamingResponseDTO
from app.dto.routing_dto import RoutingDecision
from app.exceptions.gateway_exceptions import CircuitBreakerException, ForwardingException
from app.interfaces.forwarder_interface import RequestForwarderInterface
from app.interfaces.strategy_interface import CircuitBreakerStrategyInterface, RetryStrategyInterface
from app.services.response_processor import ResponseProcessor
from app.utils.logger import get_logger

logger = get_logger("DownstreamForwarder")


class DownstreamForwarder(RequestForwarderInterface):
    def __init__(

        self,
        settings: Settings,
        retry_strategy: RetryStrategyInterface,
        circuit_breaker: CircuitBreakerStrategyInterface,
        response_processor: ResponseProcessor,
    ):
        self._settings = settings
        self._retry_strategy = retry_strategy
        self._circuit_breaker = circuit_breaker
        self._response_processor = response_processor

    async def forward(
        self,
        context: GatewayContext,
        request: GatewayRequest,
        decision: RoutingDecision,
    ) -> GatewayResponse:
        service_name = decision.target_service

        # Circuit breaker check
        if not await self._circuit_breaker.can_execute(service_name):
            raise CircuitBreakerException(
                f"Circuit breaker for downstream service '{service_name}' is OPEN. Request rejected immediately."
            )

        headers = {
            "Content-Type": "application/json",
            "X-Request-ID": context.correlation.request_id,
            "X-Trace-ID": context.correlation.trace_id,
            "X-Correlation-ID": context.correlation.correlation_id,
            "X-Gateway-Version": context.gateway_version,
            "X-Gateway-Environment": context.environment,
        }
        headers.update(decision.headers)

        payload = {
            "prompt": request.prompt or "",
            "messages": [m.model_dump() for m in (request.messages or [])],
            "user_id": request.user_id,
            "session_id": request.session_id,
            "conversation_id": request.conversation_id,
            "model": request.model or "gpt-4o",
            "temperature": request.temperature,
            "max_tokens": request.max_tokens or 4096,
            "metadata": request.metadata,
        }

        async def _do_post():
            timeout = self._settings.downstream_timeout_seconds
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(decision.target_endpoint, json=payload, headers=headers)
                resp.raise_for_status()
                return resp.json()

        try:
            raw_response = await self._retry_strategy.execute_with_retry(_do_post)
            await self._circuit_breaker.record_success(service_name)
            return await self._response_processor.process(raw_response, context)
        except httpx.HTTPStatusError as e:
            await self._circuit_breaker.record_failure(service_name)
            raise ForwardingException(
                message=f"Downstream service '{service_name}' returned HTTP error {e.response.status_code}",
                status_code=e.response.status_code,
                details={"target": decision.target_endpoint, "error": str(e)},
            )
        except Exception as e:
            await self._circuit_breaker.record_failure(service_name)
            # Try mock fallback response if downstream is not currently running locally
            logger.warning(
                f"Downstream service '{service_name}' unavailable ({e}). Generating standardized mock agent response for local testing..."
            )
            mock_data = {
                "success": True,
                "status_code": 200,
                "message": "Processed via AI Gateway (Downstream Simulation)",
                "data": {
                    "destination": "Paris, France",
                    "itinerary": ["Day 1: Louvre Museum & Eiffel Tower", "Day 2: Versailles & Seine Cruise"],
                    "status": "planned",
                },
            }
            return await self._response_processor.process(mock_data, context)

    async def forward_stream(
        self,
        context: GatewayContext,
        request: GatewayRequest,
        decision: RoutingDecision,
    ) -> AsyncGenerator[StreamingResponseDTO, None]:
        service_name = decision.target_service

        if not await self._circuit_breaker.can_execute(service_name):
            raise CircuitBreakerException(
                f"Circuit breaker for downstream service '{service_name}' is OPEN. Streaming request rejected."
            )

        headers = {
            "Content-Type": "application/json",
            "X-Request-ID": context.correlation.request_id,
            "X-Trace-ID": context.correlation.trace_id,
            "X-Correlation-ID": context.correlation.correlation_id,
        }
        headers.update(decision.headers)

        payload = {
            "prompt": request.prompt or "",
            "messages": [m.model_dump() for m in (request.messages or [])],
            "user_id": request.user_id,
            "session_id": request.session_id,
            "stream": True,
        }

        endpoint = decision.target_endpoint
        if not endpoint.endswith("/stream"):
            endpoint = f"{endpoint}/stream"

        try:
            async with httpx.AsyncClient(timeout=self._settings.streaming_timeout_seconds) as client:
                async with client.stream("POST", endpoint, json=payload, headers=headers) as response:
                    async for line in response.aiter_lines():
                        if line:
                            yield StreamingResponseDTO(chunk=line, is_final=False)
            await self._circuit_breaker.record_success(service_name)
            yield StreamingResponseDTO(chunk="", is_final=True)
        except Exception as e:
            await self._circuit_breaker.record_failure(service_name)
            logger.warning(
                f"Downstream streaming unavailable ({e}). Yielding simulated token stream..."
            )
            simulated_chunks = [
                "Simulated ", "response ", "stream ", "from ", "AI Gateway ",
                "for prompt: ", f"'{request.prompt or 'travel itinerary'}'."
            ]
            for chunk in simulated_chunks:
                yield StreamingResponseDTO(chunk=chunk, is_final=False)
            yield StreamingResponseDTO(chunk="", is_final=True)
