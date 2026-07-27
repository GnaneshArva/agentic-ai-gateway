from app.config.settings import PolicyConfig
from app.dto.context_dto import GatewayContext
from app.dto.policy_dto import PolicyResult
from app.dto.request_dto import GatewayRequest
from app.interfaces.policy_interface import GatewayPolicyInterface


class AllowedProviderPolicy(GatewayPolicyInterface):
    def __init__(self, config: PolicyConfig):
        self._config = config

    @property
    def name(self) -> str:
        return "AllowedProviderPolicy"

    async def evaluate(
        self, context: GatewayContext, request: GatewayRequest
    ) -> PolicyResult:
        requested_provider = request.provider or "OpenAI"
        allowed = [p.lower() for p in self._config.allowed_providers]

        if requested_provider.lower() not in allowed:
            return PolicyResult(
                policy_name=self.name,
                passed=False,
                reason=f"Provider '{requested_provider}' is not in allowed providers list.",
                status_code=400,
                retryable=False,
                details={
                    "requested_provider": requested_provider,
                    "allowed_providers": self._config.allowed_providers,
                },
            )

        return PolicyResult(
            policy_name=self.name,
            passed=True,
            reason=f"Provider '{requested_provider}' is permitted",
            status_code=200,
            retryable=False,
            details={"requested_provider": requested_provider},
        )
