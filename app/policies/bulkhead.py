import asyncio
from typing import Dict
from contextlib import asynccontextmanager
from app.exceptions.custom_exceptions import GatewayException
from app.utils.logger import get_logger

logger = get_logger("bulkhead_policy")


class BulkheadPolicy:
    """Bulkhead Isolation Policy restricting concurrent requests per backend service."""

    def __init__(self, max_concurrent_calls: int = 50):
        self.max_concurrent_calls = max_concurrent_calls
        self._semaphores: Dict[str, asyncio.Semaphore] = {}

    def _get_semaphore(self, service_name: str) -> asyncio.Semaphore:
        if service_name not in self._semaphores:
            self._semaphores[service_name] = asyncio.Semaphore(self.max_concurrent_calls)
        return self._semaphores[service_name]

    @asynccontextmanager
    async def acquire(self, service_name: str):
        semaphore = self._get_semaphore(service_name)
        if semaphore.locked() and semaphore._value == 0:
            logger.warning(f"Bulkhead limit reached for service '{service_name}' ({self.max_concurrent_calls} active calls)", service=service_name)
            raise GatewayException(f"Bulkhead limit reached for service '{service_name}'. Request rejected to preserve platform stability.", status_code=503)

        async with semaphore:
            yield
