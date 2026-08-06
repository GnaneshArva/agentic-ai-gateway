from app.dto.policy_dto import ValidationResult
from app.dto.request_dto import GatewayRequest
from app.exceptions.gateway_exceptions import ValidationException
from app.interfaces.validator_interface import RequestValidatorInterface


class RequestValidator(RequestValidatorInterface):
    async def validate(self, request: GatewayRequest) -> ValidationResult:
        errors = []

        if not request.prompt and not request.messages:
            errors.append("Either 'prompt' or 'messages' must be provided in request payload.")

        if request.temperature < 0.0 or request.temperature > 2.0:
            errors.append(f"Temperature '{request.temperature}' must be between 0.0 and 2.0.")

        if request.top_p < 0.0 or request.top_p > 1.0:
            errors.append(f"top_p '{request.top_p}' must be between 0.0 and 1.0.")

        if request.top_k < 1 or request.top_k > 100:
            errors.append(f"top_k '{request.top_k}' must be between 1 and 100.")

        if request.max_tokens and request.max_tokens <= 0:
            errors.append(f"max_tokens '{request.max_tokens}' must be greater than 0.")

        if errors:
            raise ValidationException(
                message="Request validation failed.",
                details={"errors": errors},
            )

        return ValidationResult(valid=True, errors=[])
