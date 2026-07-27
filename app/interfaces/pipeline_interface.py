from abc import ABC, abstractmethod
from typing import AsyncGenerator, Union
from app.dto.context_dto import GatewayContext
from app.dto.request_dto import GatewayRequest
from app.dto.response_dto import GatewayResponse, StreamingResponseDTO


class GatewayPipelineInterface(ABC):
    @abstractmethod
    async def execute(
        self, context: GatewayContext, request: GatewayRequest
    ) -> GatewayResponse:
        """Executes the request through the complete gateway pipeline."""
        pass

    @abstractmethod
    async def execute_stream(
        self, context: GatewayContext, request: GatewayRequest
    ) -> AsyncGenerator[StreamingResponseDTO, None]:
        """Executes the request through the gateway pipeline yielding streaming tokens."""
        pass
