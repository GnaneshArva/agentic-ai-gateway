from app.config.settings import PolicyConfig
from app.dto.context_dto import GatewayContext
from app.dto.policy_dto import PolicyResult
from app.dto.request_dto import GatewayRequest
from app.interfaces.policy_interface import GatewayPolicyInterface


class AllowedModelPolicy(GatewayPolicyInterface):
    def __init__(self, config: PolicyConfig):
        self._config = config

    @property
    def name(self) -> str:
        return "AllowedModelPolicy"

    async def evaluate(
        self, context: GatewayContext, request: GatewayRequest
    ) -> PolicyResult:
        requested_model = request.model or "gpt-4o"
        allowed = [m.lower() for m in self._config.allowed_models]

        if requested_model.lower() not in allowed:
            return PolicyResult(
                policy_name=self.name,
                passed=False,
                reason=f"Model '{requested_model}' is not in the allowed models list.",
                status_code=400,
                retryable=False,
                details={
                    "requested_model": requested_model,
                    "allowed_models": self._config.allowed_models,
                },
            )

        return PolicyResult(
            policy_name=self.name,
            passed=True,
            reason=f"Model '{requested_model}' is permitted",
            status_code=200,
            retryable=False,
            details={"requested_model": requested_model},
        )
