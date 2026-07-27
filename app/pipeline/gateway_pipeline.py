import asyncio
from typing import AsyncGenerator, List
from app.config.settings import Settings
from app.dto.context_dto import GatewayContext
from app.dto.policy_dto import PolicyResult
from app.dto.request_dto import GatewayRequest
from app.dto.response_dto import GatewayResponse, StreamingResponseDTO
from app.exceptions.gateway_exceptions import PolicyException, ValidationException
from app.gateway.request_enricher import RequestEnricher
from app.integrations.downstream_forwarder import DownstreamForwarder
from app.integrations.guardrails_client import GuardrailsClient
from app.integrations.observability_client import ObservabilityClient
from app.interfaces.pipeline_interface import GatewayPipelineInterface
from app.interfaces.policy_interface import GatewayPolicyInterface
from app.interfaces.router_interface import RouterInterface
from app.interfaces.validator_interface import RequestValidatorInterface
from app.utils.logger import get_logger

logger = get_logger("GatewayPipeline")


class DefaultGatewayPipeline(GatewayPipelineInterface):
    def __init__(
        self,
        settings: Settings,
        validator: RequestValidatorInterface,
        enricher: RequestEnricher,
        policies: List[GatewayPolicyInterface],
        router: RouterInterface,
        forwarder: DownstreamForwarder,
        observability: ObservabilityClient,
        guardrails: GuardrailsClient,
    ):
        self._settings = settings
        self._validator = validator
        self._enricher = enricher
        self._policies = policies
        self._router = router
        self._forwarder = forwarder
        self._observability = observability
        self._guardrails = guardrails

    async def execute(
        self, context: GatewayContext, request: GatewayRequest
    ) -> GatewayResponse:
        # Step 1: Telemetry - Request Received
        await self._observability.publish_event(
            "RequestReceived", context, {"prompt_length": len(request.prompt or "")}
        )

        # Step 2: Validation
        validation_result = await self._validator.validate(request)
        if not validation_result.valid:
            raise ValidationException(
                "Request validation failed",
                details={"errors": validation_result.errors},
            )
        await self._observability.publish_event("ValidationCompleted", context)

        # Step 3: Enrichment
        context = self._enricher.enrich(context, request)

        # Step 4: Guardrails validation (if enabled)
        await self._guardrails.validate_input(context, request)

        # Step 5: Parallel Policy Execution via asyncio.gather()
        if self._policies and self._settings.feature_flags.enable_policy_engine:
            policy_tasks = [policy.evaluate(context, request) for policy in self._policies]
            policy_results: List[PolicyResult] = await asyncio.gather(*policy_tasks)
            context.policy.policy_results = policy_results

            for result in policy_results:
                if not result.passed:
                    context.policy.all_passed = False
                    context.policy.failed_policy = result.policy_name
                    context.policy.failure_reason = result.reason

                    await self._observability.publish_event(
                        "PolicyViolation",
                        context,
                        {
                            "policy": result.policy_name,
                            "reason": result.reason,
                        },
                    )

                    raise PolicyException(
                        message=f"Policy violation in '{result.policy_name}': {result.reason}",
                        error_code=f"POLICY_VIOLATION_{result.policy_name.upper()}",
                        status_code=result.status_code,
                        retryable=result.retryable,
                        details=result.details,
                    )

        await self._observability.publish_event("PolicyExecuted", context)

        # Step 6: Routing Selection
        decision = await self._router.route(context, request)
        await self._observability.publish_event(
            "RoutingSelected",
            context,
            {
                "target_service": decision.target_service,
                "target_endpoint": decision.target_endpoint,
                "strategy": decision.strategy,
            },
        )

        # Step 7: Downstream Request Forwarding
        await self._observability.publish_event("DownstreamInvoked", context)
        response = await self._forwarder.forward(context, request, decision)

        # Step 8: Telemetry - Request Completed
        await self._observability.publish_event(
            "RequestCompleted",
            context,
            {"status_code": response.status_code, "success": response.success},
        )

        return response

    async def execute_stream(
        self, context: GatewayContext, request: GatewayRequest
    ) -> AsyncGenerator[StreamingResponseDTO, None]:
        await self._observability.publish_event("RequestReceived", context, {"stream": True})
        
        await self._validator.validate(request)
        context = self._enricher.enrich(context, request)

        if self._policies and self._settings.feature_flags.enable_policy_engine:
            policy_tasks = [policy.evaluate(context, request) for policy in self._policies]
            policy_results: List[PolicyResult] = await asyncio.gather(*policy_tasks)
            for result in policy_results:
                if not result.passed:
                    raise PolicyException(
                        message=f"Policy violation: {result.reason}",
                        status_code=result.status_code,
                    )

        decision = await self._router.route(context, request)
        await self._observability.publish_event("RoutingSelected", context)

        async for chunk in self._forwarder.forward_stream(context, request, decision):
            yield chunk

        await self._observability.publish_event("RequestCompleted", context)
