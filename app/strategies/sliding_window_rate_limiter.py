import time
from typing import Dict, List
from app.utils.logger import get_logger

logger = get_logger("sliding_window_rate_limiter")


class SlidingWindowRateLimiter:
    """Sliding Window Rate Limiting algorithm tracking timestamps within window duration."""

    def __init__(self, max_requests: int = 100, window_seconds: float = 60.0):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, List[float]] = {}

    def is_allowed(self, client_id: str) -> bool:
        now = time.time()
        cutoff = now - self.window_seconds

        timestamps = self._requests.get(client_id, [])
        # Evict timestamps older than sliding window cutoff
        timestamps = [ts for ts in timestamps if ts > cutoff]

        if len(timestamps) < self.max_requests:
            timestamps.append(now)
            self._requests[client_id] = timestamps
            return True

        logger.warning(
            f"Sliding window rate limit exceeded for client '{client_id}' ({len(timestamps)}/{self.max_requests} in {self.window_seconds}s)",
            client_id=client_id
        )
        self._requests[client_id] = timestamps
        return False
