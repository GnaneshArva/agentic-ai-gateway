from app.interfaces.validator_interface import RequestValidatorInterface
from app.validators import RequestValidator


class ValidatorFactory:
    @staticmethod
    def create_validator() -> RequestValidatorInterface:
        return RequestValidator()
