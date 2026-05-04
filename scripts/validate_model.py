"""
Validate trained model artifacts and minimum quality gates.
"""

import json
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from core.config import settings


REQUIRED_FILES = ("config.json", "metrics.json")


def read_metrics() -> dict:
    metrics_path = os.path.join(settings.model_path, "metrics.json")
    with open(metrics_path, "r", encoding="utf-8") as f:
        return json.load(f)


def metric_value(metrics: dict, name: str) -> float:
    return float(metrics.get(f"eval_{name}", metrics.get(name, 0.0)))


def main() -> int:
    missing = [
        name for name in REQUIRED_FILES
        if not os.path.exists(os.path.join(settings.model_path, name))
    ]
    if missing:
        print(f"Missing model artifacts in {settings.model_path}: {', '.join(missing)}")
        return 1

    metrics = read_metrics()
    failures = []
    gates = {
        "precision": settings.min_precision,
        "recall": settings.min_recall,
        "f1": settings.min_f1,
    }
    for name, minimum in gates.items():
        value = metric_value(metrics, name)
        if value < minimum:
            failures.append(f"{name}={value:.4f} < {minimum:.4f}")

    if failures:
        print("Model quality gate failed:")
        for failure in failures:
            print(f"- {failure}")
        return 2

    print("Model quality gate passed.")
    print(json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
