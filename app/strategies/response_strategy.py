import time
from typing import Any, Dict
from app.dto.context_dto import GatewayContext
from app.dto.response_dto import GatewayMetadataDTO, GatewayResponse, StreamingResponseDTO
from app.interfaces.strategy_interface import ResponseStrategyInterface


class StandardResponseStrategy(ResponseStrategyInterface):
    def format_response(
        self, raw_data: Any, context: GatewayContext
    ) -> GatewayResponse:
        now_mono = time.monotonic()
        processing_time_ms = (
            (now_mono - context.start_time_monotonic) * 1000.0
            if context.start_time_monotonic > 0
            else 0.0
        )

        policy_summary = {
            p.policy_name: ("PASSED" if p.passed else "FAILED")
            for p in context.policy.policy_results
        }

        metadata = GatewayMetadataDTO(
            request_id=context.correlation.request_id,
            trace_id=context.correlation.trace_id,
            correlation_id=context.correlation.correlation_id,
            gateway_version=context.gateway_version,
            environment=context.environment,
            processing_time_ms=round(processing_time_ms, 2),
            target_service=context.routing.target_service,
            target_endpoint=context.routing.target_endpoint,
            provider=context.routing.provider,
            model=context.routing.model,
            tokens_used=context.estimated_tokens,
            cost_usd=context.estimated_cost_usd,
            policy_results_summary=policy_summary,
        )

        if isinstance(raw_data, dict):
            return GatewayResponse(
                success=raw_data.get("success", True),
                status_code=raw_data.get("status_code", 200),
                message=raw_data.get("message", "Request completed successfully"),
                data=raw_data.get("data", raw_data),
                metadata=metadata,
            )

        return GatewayResponse(
            success=True,
            status_code=200,
            message="Request completed successfully",
            data={"result": raw_data},
            metadata=metadata,
        )


class StreamingResponseStrategy(ResponseStrategyInterface):
    def format_response(
        self, raw_data: Any, context: GatewayContext
    ) -> StreamingResponseDTO:
        chunk_str = str(raw_data) if raw_data else ""
        return StreamingResponseDTO(
            chunk=chunk_str,
            is_final=False,
            metadata=None,
        )
