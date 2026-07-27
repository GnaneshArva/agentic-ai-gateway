import asyncio
from typing import Any, Callable
from app.config.settings import RetryConfig
from app.interfaces.strategy_interface import RetryStrategyInterface
from app.utils.logger import get_logger

logger = get_logger("RetryStrategy")


class NoRetryStrategy(RetryStrategyInterface):
    async def execute_with_retry(
        self, func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> Any:
        return await func(*args, **kwargs)


class FixedDelayRetry(RetryStrategyInterface):
    def __init__(self, config: RetryConfig):
        self._config = config

    async def execute_with_retry(
        self, func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> Any:
        last_exception = None
        for attempt in range(1, self._config.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self._config.max_retries:
                    logger.warning(
                        f"FixedDelayRetry: Attempt {attempt}/{self._config.max_retries} failed: {e}. Retrying in {self._config.retry_delay_seconds}s..."
                    )
                    await asyncio.sleep(self._config.retry_delay_seconds)
        if last_exception:
            raise last_exception


class ExponentialBackoffRetry(RetryStrategyInterface):
    def __init__(self, config: RetryConfig):
        self._config = config

    async def execute_with_retry(
        self, func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> Any:
        last_exception = None
        delay = self._config.retry_delay_seconds
        for attempt in range(1, self._config.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self._config.max_retries:
                    logger.warning(
                        f"ExponentialBackoffRetry: Attempt {attempt}/{self._config.max_retries} failed: {e}. Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                    delay *= 2.0
        if last_exception:
            raise last_exception
