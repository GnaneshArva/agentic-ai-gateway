from typing import List
from app.config.settings import Settings
from app.interfaces.policy_interface import GatewayPolicyInterface
from app.policies import (
    AllowedModelPolicy,
    AllowedProviderPolicy,
    BudgetPolicy,
    RateLimitPolicy,
    RequestSizePolicy,
    StreamingPolicy,
    TokenQuotaPolicy,
)


class PolicyFactory:
    @staticmethod
    def create_policies(settings: Settings) -> List[GatewayPolicyInterface]:
        if not settings.feature_flags.enable_policy_engine:
            return []

        policies: List[GatewayPolicyInterface] = [
            RequestSizePolicy(settings.policy_config),
            RateLimitPolicy(settings.policy_config),
            TokenQuotaPolicy(settings.policy_config),
            BudgetPolicy(settings.policy_config),
            AllowedModelPolicy(settings.policy_config),
            AllowedProviderPolicy(settings.policy_config),
            StreamingPolicy(settings.feature_flags),
        ]
        return policies
