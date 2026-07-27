from abc import ABC, abstractmethod
from typing import Any, Dict
from app.dto.context_dto import GatewayContext
from app.dto.response_dto import GatewayResponse


class ResponseProcessorInterface(ABC):
    @abstractmethod
    async def process(
        self, raw_response: Dict[str, Any], context: GatewayContext
    ) -> GatewayResponse:
        """Processes and normalizes raw downstream response."""
        pass
