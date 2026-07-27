from abc import ABC, abstractmethod
from typing import Any, Callable, List, Optional, TypeVar
from app.dto.context_dto import GatewayContext
from app.dto.request_dto import GatewayRequest
from app.dto.routing_dto import RouteDefinition, RoutingDecision

T = TypeVar("T")


class RoutingStrategyInterface(ABC):
    @abstractmethod
    async def select_route(
        self,
        routes: List[RouteDefinition],
        context: GatewayContext,
        request: GatewayRequest,
    ) -> RouteDefinition:
        """Selects a target route from available definitions based on strategy."""
        pass


class RetryStrategyInterface(ABC):
    @abstractmethod
    async def execute_with_retry(
        self,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Executes async callable with configurable retry logic."""
        pass


class CircuitBreakerStrategyInterface(ABC):
    @abstractmethod
    async def can_execute(self, service_name: str) -> bool:
        """Returns true if circuit breaker allows call."""
        pass

    @abstractmethod
    async def record_success(self, service_name: str) -> None:
        """Records success call."""
        pass

    @abstractmethod
    async def record_failure(self, service_name: str) -> None:
        """Records failure call."""
        pass

    @abstractmethod
    def get_state(self, service_name: str) -> str:
        """Returns state: CLOSED, OPEN, HALF_OPEN."""
        pass


class LoadBalancingStrategyInterface(ABC):
    @abstractmethod
    def select(self, instances: List[RouteDefinition]) -> RouteDefinition:
        """Selects an instance using load balancing strategy."""
        pass


class ResponseStrategyInterface(ABC):
    @abstractmethod
    def format_response(
        self, raw_data: Any, context: GatewayContext
    ) -> Any:
        """Formats normalized response."""
        pass
