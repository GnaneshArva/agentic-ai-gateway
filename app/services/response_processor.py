from typing import Any, Dict
from app.dto.context_dto import GatewayContext
from app.dto.response_dto import GatewayResponse
from app.interfaces.response_processor_interface import ResponseProcessorInterface
from app.interfaces.strategy_interface import ResponseStrategyInterface


class ResponseProcessor(ResponseProcessorInterface):
    def __init__(self, response_strategy: ResponseStrategyInterface):
        self._strategy = response_strategy

    async def process(
        self, raw_response: Dict[str, Any], context: GatewayContext
    ) -> GatewayResponse:
        return self._strategy.format_response(raw_response, context)
