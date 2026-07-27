from typing import List, Optional
from app.dto.request_dto import GatewayRequest, MessageDTO


class TokenEstimator:
    # Cost per 1K tokens in USD for input / output
    PRICING_TABLE = {
        "gpt-4o": {"input": 0.0025, "output": 0.0100},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-4": {"input": 0.0300, "output": 0.0600},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "claude-3-5-sonnet": {"input": 0.0030, "output": 0.0150},
        "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
        "gemini-1.5-pro": {"input": 0.00125, "output": 0.0050},
        "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
    }

    @classmethod
    def estimate_text_tokens(cls, text: Optional[str]) -> int:
        if not text:
            return 0
        # Heuristic: approx 1 token per 4 characters or 0.75 words
        words = text.split()
        return max(1, int(len(words) * 1.3))

    @classmethod
    def estimate_messages_tokens(cls, messages: List[MessageDTO]) -> int:
        total = 0
        for msg in messages:
            total += 4  # message overhead
            total += cls.estimate_text_tokens(msg.content)
            if msg.role:
                total += cls.estimate_text_tokens(msg.role)
        return total

    @classmethod
    def estimate_request_tokens(cls, request: GatewayRequest) -> int:
        prompt_tokens = cls.estimate_text_tokens(request.prompt)
        messages_tokens = cls.estimate_messages_tokens(request.messages or [])
        input_tokens = prompt_tokens + messages_tokens
        
        # Max expected completion tokens
        max_completion = request.max_tokens or 1000
        
        return input_tokens + max_completion

    @classmethod
    def estimate_request_cost(cls, request: GatewayRequest, estimated_tokens: int) -> float:
        model = (request.model or "gpt-4o").lower()
        pricing = cls.PRICING_TABLE.get(model, {"input": 0.0025, "output": 0.0100})
        
        # Split tokens roughly 40% input, 60% output
        input_tokens = int(estimated_tokens * 0.4)
        output_tokens = estimated_tokens - input_tokens
        
        cost = (input_tokens / 1000.0 * pricing["input"]) + (output_tokens / 1000.0 * pricing["output"])
        return round(cost, 6)
