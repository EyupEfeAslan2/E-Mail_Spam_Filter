"""
Small in-memory rate limiter for API abuse protection.
"""

from collections import defaultdict, deque
from time import monotonic


class SlidingWindowRateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # Veri yapısı: Queue/deque. Her istemci için zaman damgaları kaydırmalı pencerede tutulur.
        self._events = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = monotonic()
        window_start = now - self.window_seconds
        events = self._events[key]
        while events and events[0] < window_start:
            events.popleft()
        if len(events) >= self.max_requests:
            return False
        events.append(now)
        return True
