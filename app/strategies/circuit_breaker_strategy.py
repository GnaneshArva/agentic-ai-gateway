import time
from typing import Dict, List
from app.config.settings import CircuitBreakerConfig
from app.interfaces.strategy_interface import CircuitBreakerStrategyInterface
from app.utils.logger import get_logger

logger = get_logger("CircuitBreaker")


class SimpleCircuitBreaker(CircuitBreakerStrategyInterface):
    STATE_CLOSED = "CLOSED"
    STATE_OPEN = "OPEN"
    STATE_HALF_OPEN = "HALF_OPEN"

    def __init__(self, config: CircuitBreakerConfig):
        self._config = config
        self._state: Dict[str, str] = {}
        self._failures: Dict[str, int] = {}
        self._last_failure_time: Dict[str, float] = {}

    def get_state(self, service_name: str) -> str:
        state = self._state.get(service_name, self.STATE_CLOSED)
        if state == self.STATE_OPEN:
            last_fail = self._last_failure_time.get(service_name, 0.0)
            if time.time() - last_fail >= self._config.recovery_timeout_seconds:
                logger.info(f"CircuitBreaker for '{service_name}' transitioning OPEN -> HALF_OPEN")
                self._state[service_name] = self.STATE_HALF_OPEN
                return self.STATE_HALF_OPEN
        return state

    async def can_execute(self, service_name: str) -> bool:
        state = self.get_state(service_name)
        if state == self.STATE_OPEN:
            return False
        return True

    async def record_success(self, service_name: str) -> None:
        state = self.get_state(service_name)
        if state in (self.STATE_HALF_OPEN, self.STATE_OPEN):
            logger.info(f"CircuitBreaker for '{service_name}' transitioning {state} -> CLOSED")
        self._state[service_name] = self.STATE_CLOSED
        self._failures[service_name] = 0

    async def record_failure(self, service_name: str) -> None:
        self._failures[service_name] = self._failures.get(service_name, 0) + 1
        self._last_failure_time[service_name] = time.time()

        if self._failures[service_name] >= self._config.failure_threshold:
            logger.warning(
                f"CircuitBreaker for '{service_name}' threshold ({self._config.failure_threshold}) reached. Transitioning -> OPEN"
            )
            self._state[service_name] = self.STATE_OPEN


class SlidingWindowCircuitBreaker(CircuitBreakerStrategyInterface):
    def __init__(self, config: CircuitBreakerConfig, window_seconds: float = 60.0):
        self._config = config
        self._window_seconds = window_seconds
        self._state: Dict[str, str] = {}
        self._failure_timestamps: Dict[str, List[float]] = {}
        self._last_failure_time: Dict[str, float] = {}

    def get_state(self, service_name: str) -> str:
        state = self._state.get(service_name, SimpleCircuitBreaker.STATE_CLOSED)
        if state == SimpleCircuitBreaker.STATE_OPEN:
            last_fail = self._last_failure_time.get(service_name, 0.0)
            if time.time() - last_fail >= self._config.recovery_timeout_seconds:
                self._state[service_name] = SimpleCircuitBreaker.STATE_HALF_OPEN
                return SimpleCircuitBreaker.STATE_HALF_OPEN
        return state

    async def can_execute(self, service_name: str) -> bool:
        return self.get_state(service_name) != SimpleCircuitBreaker.STATE_OPEN

    async def record_success(self, service_name: str) -> None:
        self._state[service_name] = SimpleCircuitBreaker.STATE_CLOSED
        self._failure_timestamps[service_name] = []

    async def record_failure(self, service_name: str) -> None:
        now = time.time()
        self._last_failure_time[service_name] = now
        timestamps = self._failure_timestamps.get(service_name, [])
        timestamps = [t for t in timestamps if now - t <= self._window_seconds]
        timestamps.append(now)
        self._failure_timestamps[service_name] = timestamps

        if len(timestamps) >= self._config.failure_threshold:
            self._state[service_name] = SimpleCircuitBreaker.STATE_OPEN
