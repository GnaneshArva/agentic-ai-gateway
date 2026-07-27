from typing import Any, Dict, Optional


class GatewayException(Exception):
    def __init__(
        self,
        message: str,
        error_code: str = "GATEWAY_ERROR",
        status_code: int = 500,
        retryable: bool = False,
        component: str = "agentic-ai-gateway",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.retryable = retryable
        self.component = component
        self.details = details or {}


class ValidationException(GatewayException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            retryable=False,
            component="RequestValidator",
            details=details,
        )


class PolicyException(GatewayException):
    def __init__(
        self,
        message: str,
        error_code: str = "POLICY_VIOLATION",
        status_code: int = 429,
        retryable: bool = False,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            retryable=retryable,
            component="PolicyEngine",
            details=details,
        )


class RateLimitExceededException(PolicyException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            retryable=True,
            details=details,
        )


class TokenQuotaExceededException(PolicyException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="TOKEN_QUOTA_EXCEEDED",
            status_code=429,
            retryable=False,
            details=details,
        )


class BudgetExceededException(PolicyException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="BUDGET_EXCEEDED",
            status_code=429,
            retryable=False,
            details=details,
        )


class RoutingException(GatewayException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="ROUTING_ERROR",
            status_code=502,
            retryable=True,
            component="Router",
            details=details,
        )


class ForwardingException(GatewayException):
    def __init__(
        self,
        message: str,
        status_code: int = 502,
        retryable: bool = True,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="DOWNSTREAM_FAILURE",
            status_code=status_code,
            retryable=retryable,
            component="DownstreamForwarder",
            details=details,
        )


class TimeoutException(GatewayException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="GATEWAY_TIMEOUT",
            status_code=504,
            retryable=True,
            component="GatewayPipeline",
            details=details,
        )


class CircuitBreakerException(GatewayException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="CIRCUIT_OPEN",
            status_code=503,
            retryable=True,
            component="CircuitBreaker",
            details=details,
        )
