from abc import ABC, abstractmethod
from app.dto.policy_dto import ValidationResult
from app.dto.request_dto import GatewayRequest


class RequestValidatorInterface(ABC):
    @abstractmethod
    async def validate(self, request: GatewayRequest) -> ValidationResult:
        """Validates incoming request payload schema and constraints."""
        pass
