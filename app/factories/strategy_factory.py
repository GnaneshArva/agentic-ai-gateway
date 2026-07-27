from app.config.settings import Settings
from app.interfaces.strategy_interface import (
    CircuitBreakerStrategyInterface,
    LoadBalancingStrategyInterface,
    ResponseStrategyInterface,
    RetryStrategyInterface,
    RoutingStrategyInterface,
)
from app.strategies import (
    ExponentialBackoffRetry,
    FixedDelayRetry,
    LeastConnectionsStrategy,
    NoRetryStrategy,
    PriorityRoutingStrategy,
    RoundRobinStrategy,
    RuleBasedRoutingStrategy,
    SimpleCircuitBreaker,
    SlidingWindowCircuitBreaker,
    StandardResponseStrategy,
    StaticRoutingStrategy,
    WeightedRoutingStrategy,
    WeightedStrategy,
)


class StrategyFactory:
    @staticmethod
    def create_routing_strategy(strategy_type: str) -> RoutingStrategyInterface:
        strategy_type = strategy_type.lower()
        if strategy_type == "rule_based":
            return RuleBasedRoutingStrategy()
        elif strategy_type == "priority":
            return PriorityRoutingStrategy()
        elif strategy_type == "weighted":
            return WeightedRoutingStrategy()
        return StaticRoutingStrategy()

    @staticmethod
    def create_retry_strategy(settings: Settings) -> RetryStrategyInterface:
        if not settings.feature_flags.enable_retry:
            return NoRetryStrategy()
        strategy_type = settings.retry_config.backoff_strategy.lower()
        if strategy_type == "fixed":
            return FixedDelayRetry(settings.retry_config)
        elif strategy_type == "exponential":
            return ExponentialBackoffRetry(settings.retry_config)
        return NoRetryStrategy()

    @staticmethod
    def create_circuit_breaker(settings: Settings) -> CircuitBreakerStrategyInterface:
        return SimpleCircuitBreaker(settings.circuit_breaker_config)

    @staticmethod
    def create_load_balancer(strategy_type: str = "round_robin") -> LoadBalancingStrategyInterface:
        strategy_type = strategy_type.lower()
        if strategy_type == "least_connections":
            return LeastConnectionsStrategy()
        elif strategy_type == "weighted":
            return WeightedStrategy()
        return RoundRobinStrategy()

    @staticmethod
    def create_response_strategy() -> ResponseStrategyInterface:
        return StandardResponseStrategy()
