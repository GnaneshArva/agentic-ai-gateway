from abc import ABC, abstractmethod
from app.dto.context_dto import GatewayContext
from app.dto.policy_dto import PolicyResult
from app.dto.request_dto import GatewayRequest


class GatewayPolicyInterface(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Returns policy unique name."""
        pass

    @abstractmethod
    async def evaluate(
        self, context: GatewayContext, request: GatewayRequest
    ) -> PolicyResult:
        """Evaluates the policy against request and context."""
        pass
