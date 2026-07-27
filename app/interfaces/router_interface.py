from abc import ABC, abstractmethod
from app.dto.context_dto import GatewayContext
from app.dto.request_dto import GatewayRequest
from app.dto.routing_dto import RoutingDecision


class RouterInterface(ABC):
    @abstractmethod
    async def route(
        self, context: GatewayContext, request: GatewayRequest
    ) -> RoutingDecision:
        """Determines the downstream target route for the incoming request."""
        pass
