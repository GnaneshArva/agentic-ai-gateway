import json
from app.config.settings import PolicyConfig
from app.dto.context_dto import GatewayContext
from app.dto.policy_dto import PolicyResult
from app.dto.request_dto import GatewayRequest
from app.interfaces.policy_interface import GatewayPolicyInterface


class RequestSizePolicy(GatewayPolicyInterface):
    def __init__(self, config: PolicyConfig):
        self._config = config

    @property
    def name(self) -> str:
        return "RequestSizePolicy"

    async def evaluate(
        self, context: GatewayContext, request: GatewayRequest
    ) -> PolicyResult:
        # Check conversation history length
        msg_count = len(request.messages or [])
        if msg_count > self._config.max_conversation_history:
            return PolicyResult(
                policy_name=self.name,
                passed=False,
                reason=f"Conversation message count ({msg_count}) exceeds maximum allowed history ({self._config.max_conversation_history})",
                status_code=400,
                retryable=False,
                details={
                    "message_count": msg_count,
                    "max_allowed": self._config.max_conversation_history,
                },
            )

        # Estimate serialized payload size
        raw_bytes = len(json.dumps(request.model_dump()).encode("utf-8"))
        if raw_bytes > self._config.max_payload_bytes:
            return PolicyResult(
                policy_name=self.name,
                passed=False,
                reason=f"Payload size ({raw_bytes} bytes) exceeds maximum limit ({self._config.max_payload_bytes} bytes)",
                status_code=413,
                retryable=False,
                details={
                    "payload_size_bytes": raw_bytes,
                    "max_payload_bytes": self._config.max_payload_bytes,
                },
            )

        return PolicyResult(
            policy_name=self.name,
            passed=True,
            reason="Request size validation passed",
            status_code=200,
            retryable=False,
            details={"payload_size_bytes": raw_bytes, "message_count": msg_count},
        )
