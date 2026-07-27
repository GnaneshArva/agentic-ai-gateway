from abc import ABC, abstractmethod
from typing import Optional
from app.dto.context_dto import GatewayContext
from app.dto.request_dto import GatewayRequest


class PipelineHandler(ABC):
    def __init__(self, next_handler: Optional["PipelineHandler"] = None):
        self._next_handler = next_handler

    def set_next(self, handler: "PipelineHandler") -> "PipelineHandler":
        self._next_handler = handler
        return handler

    @abstractmethod
    async def handle(
        self, context: GatewayContext, request: GatewayRequest
    ) -> None:
        if self._next_handler:
            await self._next_handler.handle(context, request)
