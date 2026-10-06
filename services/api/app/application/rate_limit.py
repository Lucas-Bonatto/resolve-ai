from __future__ import annotations

import asyncio
from collections import OrderedDict, deque
from math import ceil
from time import monotonic


class SlidingWindowRateLimiter:
    """Bounded in-process safeguard for the single-process public showcase."""

    def __init__(self, request_limit: int, window_seconds: int, max_clients: int = 2048) -> None:
        self.request_limit = request_limit
        self.window_seconds = window_seconds
        self.max_clients = max_clients
        self._requests: OrderedDict[str, deque[float]] = OrderedDict()
        self._lock = asyncio.Lock()

    @property
    def tracked_clients(self) -> int:
        return len(self._requests)

    async def retry_after(self, client_id: str, now: float | None = None) -> int | None:
        observed_at = monotonic() if now is None else now
        cutoff = observed_at - self.window_seconds
        async with self._lock:
            history = self._requests.setdefault(client_id, deque())
            while history and history[0] <= cutoff:
                history.popleft()
            self._requests.move_to_end(client_id)
            if len(history) >= self.request_limit:
                return max(1, ceil(self.window_seconds - (observed_at - history[0])))
            history.append(observed_at)
            while len(self._requests) > self.max_clients:
                self._requests.popitem(last=False)
        return None

    async def reset(self) -> None:
        async with self._lock:
            self._requests.clear()
