import asyncio
from app.config.settings import CircuitBreakerConfig, RetryConfig
from app.strategies import (
    ExponentialBackoffRetry,
    FixedDelayRetry,
    RoundRobinStrategy,
    SimpleCircuitBreaker,
)
from app.dto.routing_dto import RouteDefinition


def test_simple_circuit_breaker():
    async def _run():
        config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout_seconds=0.5)
        cb = SimpleCircuitBreaker(config)

        service = "test-service"
        assert await cb.can_execute(service) is True
        assert cb.get_state(service) == "CLOSED"

        await cb.record_failure(service)
        assert await cb.can_execute(service) is True

        await cb.record_failure(service)
        assert await cb.can_execute(service) is False
        assert cb.get_state(service) == "OPEN"

        await cb.record_success(service)
        assert await cb.can_execute(service) is True
        assert cb.get_state(service) == "CLOSED"

    asyncio.run(_run())


def test_retry_strategy_success():
    async def _run():
        config = RetryConfig(max_retries=3, retry_delay_seconds=0.01)
        retry = FixedDelayRetry(config)

        call_count = 0

        async def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return "success"

        res = await retry.execute_with_retry(flaky_func)
        assert res == "success"
        assert call_count == 2

    asyncio.run(_run())


def test_round_robin_load_balancing():
    r1 = RouteDefinition(service_name="s1", endpoint_url="http://s1")
    r2 = RouteDefinition(service_name="s2", endpoint_url="http://s2")

    lb = RoundRobinStrategy()
    first = lb.select([r1, r2])
    second = lb.select([r1, r2])

    assert first.service_name == "s1"
    assert second.service_name == "s2"
