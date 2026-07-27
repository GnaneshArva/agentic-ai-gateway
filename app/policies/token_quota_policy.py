from collections import defaultdict
from typing import Dict
from app.config.settings import PolicyConfig
from app.dto.context_dto import GatewayContext
from app.dto.policy_dto import PolicyResult
from app.dto.request_dto import GatewayRequest
from app.interfaces.policy_interface import GatewayPolicyInterface
from app.utils.token_estimator import TokenEstimator


class TokenQuotaPolicy(GatewayPolicyInterface):
    def __init__(self, config: PolicyConfig):
        self._config = config
        self._daily_usage: Dict[str, int] = defaultdict(int)
        self._monthly_usage: Dict[str, int] = defaultdict(int)

    @property
    def name(self) -> str:
        return "TokenQuotaPolicy"

    async def evaluate(
        self, context: GatewayContext, request: GatewayRequest
    ) -> PolicyResult:
        estimated_tokens = TokenEstimator.estimate_request_tokens(request)
        context.estimated_tokens = estimated_tokens

        if estimated_tokens > self._config.request_token_limit:
            return PolicyResult(
                policy_name=self.name,
                passed=False,
                reason=f"Request estimated tokens ({estimated_tokens}) exceeds maximum limit ({self._config.request_token_limit})",
                status_code=400,
                retryable=False,
                details={
                    "estimated_tokens": estimated_tokens,
                    "request_token_limit": self._config.request_token_limit,
                },
            )

        key = request.user_id or request.tenant_id or "default"
        current_daily = self._daily_usage[key]
        current_monthly = self._monthly_usage[key]

        if current_daily + estimated_tokens > self._config.daily_token_quota:
            return PolicyResult(
                policy_name=self.name,
                passed=False,
                reason=f"Daily token quota exceeded for {key}: used {current_daily}, requested {estimated_tokens}, quota {self._config.daily_token_quota}",
                status_code=429,
                retryable=False,
                details={
                    "daily_used": current_daily,
                    "daily_quota": self._config.daily_token_quota,
                },
            )

        if current_monthly + estimated_tokens > self._config.monthly_token_quota:
            return PolicyResult(
                policy_name=self.name,
                passed=False,
                reason=f"Monthly token quota exceeded for {key}: used {current_monthly}, requested {estimated_tokens}, quota {self._config.monthly_token_quota}",
                status_code=429,
                retryable=False,
                details={
                    "monthly_used": current_monthly,
                    "monthly_quota": self._config.monthly_token_quota,
                },
            )

        # Update in-memory counters
        self._daily_usage[key] += estimated_tokens
        self._monthly_usage[key] += estimated_tokens

        return PolicyResult(
            policy_name=self.name,
            passed=True,
            reason="Token quota check passed",
            status_code=200,
            retryable=False,
            details={
                "estimated_tokens": estimated_tokens,
                "daily_used": self._daily_usage[key],
                "daily_quota": self._config.daily_token_quota,
                "monthly_used": self._monthly_usage[key],
                "monthly_quota": self._config.monthly_token_quota,
            },
        )
