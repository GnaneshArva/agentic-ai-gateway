import time
from collections import defaultdict
from typing import Dict, List
from app.config.settings import PolicyConfig
from app.dto.context_dto import GatewayContext
from app.dto.policy_dto import PolicyResult
from app.dto.request_dto import GatewayRequest
from app.interfaces.policy_interface import GatewayPolicyInterface


class RateLimitPolicy(GatewayPolicyInterface):
    def __init__(self, config: PolicyConfig):
        self._config = config
        # Key -> list of request timestamps
        self._requests: Dict[str, List[float]] = defaultdict(list)

    @property
    def name(self) -> str:
        return "RateLimitPolicy"

    async def evaluate(
        self, context: GatewayContext, request: GatewayRequest
    ) -> PolicyResult:
        key = (
            request.api_key
            or request.user_id
            or request.tenant_id
            or request.app_id
            or "anonymous"
        )
        now = time.time()
        window = 60.0
        limit = self._config.rate_limit_requests_per_minute

        # Remove timestamps outside of window
        timestamps = [t for t in self._requests[key] if now - t < window]
        self._requests[key] = timestamps

        if len(timestamps) >= limit:
            return PolicyResult(
                policy_name=self.name,
                passed=False,
                reason=f"Rate limit exceeded: {len(timestamps)} requests in last 60s (limit: {limit})",
                status_code=429,
                retryable=True,
                details={
                    "key": key,
                    "current": len(timestamps),
                    "limit": limit,
                    "window_seconds": window,
                },
            )

        # Record this request
        self._requests[key].append(now)

        return PolicyResult(
            policy_name=self.name,
            passed=True,
            reason="Rate limit within acceptable bounds",
            status_code=200,
            retryable=False,
            details={
                "key": key,
                "current": len(timestamps) + 1,
                "limit": limit,
                "remaining": limit - (len(timestamps) + 1),
            },
        )
