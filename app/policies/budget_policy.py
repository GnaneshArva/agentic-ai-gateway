from collections import defaultdict
from typing import Dict
from app.config.settings import PolicyConfig
from app.dto.context_dto import GatewayContext
from app.dto.policy_dto import PolicyResult
from app.dto.request_dto import GatewayRequest
from app.interfaces.policy_interface import GatewayPolicyInterface
from app.utils.token_estimator import TokenEstimator


class BudgetPolicy(GatewayPolicyInterface):
    def __init__(self, config: PolicyConfig):
        self._config = config
        self._daily_spent: Dict[str, float] = defaultdict(float)
        self._monthly_spent: Dict[str, float] = defaultdict(float)

    @property
    def name(self) -> str:
        return "BudgetPolicy"

    async def evaluate(
        self, context: GatewayContext, request: GatewayRequest
    ) -> PolicyResult:
        tokens = context.estimated_tokens or TokenEstimator.estimate_request_tokens(request)
        estimated_cost = TokenEstimator.estimate_request_cost(request, tokens)
        context.estimated_cost_usd = estimated_cost

        key = request.tenant_id or request.user_id or "default"
        current_daily = self._daily_spent[key]
        current_monthly = self._monthly_spent[key]

        if current_daily + estimated_cost > self._config.daily_budget_usd:
            return PolicyResult(
                policy_name=self.name,
                passed=False,
                reason=f"Daily budget exceeded for {key}: spent ${current_daily:.4f}, estimated ${estimated_cost:.4f}, limit ${self._config.daily_budget_usd:.2f}",
                status_code=429,
                retryable=False,
                details={
                    "daily_spent_usd": current_daily,
                    "daily_budget_usd": self._config.daily_budget_usd,
                    "estimated_cost_usd": estimated_cost,
                },
            )

        if current_monthly + estimated_cost > self._config.monthly_budget_usd:
            return PolicyResult(
                policy_name=self.name,
                passed=False,
                reason=f"Monthly budget exceeded for {key}: spent ${current_monthly:.4f}, estimated ${estimated_cost:.4f}, limit ${self._config.monthly_budget_usd:.2f}",
                status_code=429,
                retryable=False,
                details={
                    "monthly_spent_usd": current_monthly,
                    "monthly_budget_usd": self._config.monthly_budget_usd,
                    "estimated_cost_usd": estimated_cost,
                },
            )

        self._daily_spent[key] += estimated_cost
        self._monthly_spent[key] += estimated_cost

        return PolicyResult(
            policy_name=self.name,
            passed=True,
            reason="Budget check passed",
            status_code=200,
            retryable=False,
            details={
                "estimated_cost_usd": estimated_cost,
                "daily_spent_usd": round(self._daily_spent[key], 4),
                "daily_budget_usd": self._config.daily_budget_usd,
                "monthly_spent_usd": round(self._monthly_spent[key], 4),
                "monthly_budget_usd": self._config.monthly_budget_usd,
            },
        )
