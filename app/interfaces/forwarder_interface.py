from abc import ABC, abstractmethod
from typing import AsyncGenerator, Any, Dict
from app.dto.context_dto import GatewayContext
from app.dto.request_dto import GatewayRequest
from app.dto.response_dto import GatewayResponse, StreamingResponseDTO
from app.dto.routing_dto import RoutingDecision


class RequestForwarderInterface(ABC):
    @abstractmethod
    async def forward(
        self,
        context: GatewayContext,
        request: GatewayRequest,
        decision: RoutingDecision,
    ) -> GatewayResponse:
        """Forwards standard HTTP request to downstream AI service."""
        pass

    @abstractmethod
    async def forward_stream(
        self,
        context: GatewayContext,
        request: GatewayRequest,
        decision: RoutingDecision,
    ) -> AsyncGenerator[StreamingResponseDTO, None]:
        """Forwards streaming HTTP request to downstream AI service."""
        pass
