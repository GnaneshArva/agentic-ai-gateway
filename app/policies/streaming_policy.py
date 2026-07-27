from app.config.settings import FeatureFlags
from app.dto.context_dto import GatewayContext
from app.dto.policy_dto import PolicyResult
from app.dto.request_dto import GatewayRequest
from app.interfaces.policy_interface import GatewayPolicyInterface


class StreamingPolicy(GatewayPolicyInterface):
    def __init__(self, feature_flags: FeatureFlags):
        self._flags = feature_flags

    @property
    def name(self) -> str:
        return "StreamingPolicy"

    async def evaluate(
        self, context: GatewayContext, request: GatewayRequest
    ) -> PolicyResult:
        if request.stream and not self._flags.enable_streaming:
            return PolicyResult(
                policy_name=self.name,
                passed=False,
                reason="Streaming responses are currently disabled on the gateway.",
                status_code=400,
                retryable=False,
                details={"requested_stream": True, "streaming_enabled": False},
            )

        return PolicyResult(
            policy_name=self.name,
            passed=True,
            reason="Streaming policy check passed",
            status_code=200,
            retryable=False,
            details={
                "stream_requested": request.stream,
                "streaming_enabled": self._flags.enable_streaming,
            },
        )
