"""
Small HTTP load test for the spam prediction API.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from statistics import mean
import os
import time

import requests


API_URL = os.getenv("SPAM_API_URL", "http://127.0.0.1:8000/predict")
REQUESTS = int(os.getenv("SPAM_LOAD_REQUESTS", "100"))
CONCURRENCY = int(os.getenv("SPAM_LOAD_CONCURRENCY", "10"))
TIMEOUT = int(os.getenv("SPAM_API_TIMEOUT", "10"))

SAMPLES = (
    "free prize click now limited offer winner",
    "quarterly invoice attached for your review",
    "urgent lottery bonus claim money today",
    "team sync notes and project timeline",
)


def send_one(index: int) -> tuple[int, float]:
    started = time.perf_counter()
    response = requests.post(
        API_URL,
        json={"text": SAMPLES[index % len(SAMPLES)]},
        timeout=TIMEOUT,
    )
    elapsed_ms = (time.perf_counter() - started) * 1000
    return response.status_code, elapsed_ms


def percentile(values: list[float], pct: float) -> float:
    values = sorted(values)
    index = min(len(values) - 1, int(round((pct / 100) * (len(values) - 1))))
    return values[index]


def main() -> int:
    latencies = []
    status_counts = {}
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        futures = [executor.submit(send_one, i) for i in range(REQUESTS)]
        for future in as_completed(futures):
            status, latency = future.result()
            latencies.append(latency)
            status_counts[status] = status_counts.get(status, 0) + 1

    print(f"requests={REQUESTS} concurrency={CONCURRENCY}")
    print(f"statuses={status_counts}")
    print(f"avg_ms={mean(latencies):.2f} p95_ms={percentile(latencies, 95):.2f} max_ms={max(latencies):.2f}")
    return 0 if status_counts.get(200, 0) == REQUESTS else 1


if __name__ == "__main__":
    raise SystemExit(main())
