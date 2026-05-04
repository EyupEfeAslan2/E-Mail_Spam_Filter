"""
Retraining orchestration primitives.

This module intentionally stays lightweight: it uses a JSON file as a durable
single-node queue marker instead of adding Celery/Redis for a project-sized app.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from threading import Lock
from typing import Any

from core.config import settings


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class RetrainState:
    requested: bool
    running: bool
    reason: str
    requested_at: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    last_error: str | None = None


class RetrainQueue:
    def __init__(self, state_path: str | None = None):
        self.state_path = state_path or settings.retrain_state_path
        self._lock = Lock()

    def _default_state(self) -> dict[str, Any]:
        return {
            "requested": False,
            "running": False,
            "reason": "",
            "requested_at": None,
            "started_at": None,
            "finished_at": None,
            "last_error": None,
        }

    def read(self) -> dict[str, Any]:
        """Data structure: Queue marker. JSON persists one pending retrain request."""
        try:
            with open(self.state_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            data = self._default_state()
        return {**self._default_state(), **data}

    def write(self, state: dict[str, Any]) -> None:
        os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    def enqueue(self, reason: str) -> dict[str, Any]:
        with self._lock:
            state = self.read()
            if state["running"]:
                return state
            state.update(
                {
                    "requested": True,
                    "reason": reason,
                    "requested_at": _utc_now(),
                    "last_error": None,
                }
            )
            self.write(state)
            return state

    def run_if_requested(self) -> dict[str, Any]:
        """Run training synchronously when a retrain request is pending."""
        with self._lock:
            state = self.read()
            if state["running"] or not state["requested"]:
                return state
            state.update({"running": True, "started_at": _utc_now(), "last_error": None})
            self.write(state)

        try:
            from core.train import train_model

            train_model()
            state.update(
                {
                    "requested": False,
                    "running": False,
                    "finished_at": _utc_now(),
                    "last_error": None,
                }
            )
        except Exception as exc:
            state.update(
                {
                    "running": False,
                    "finished_at": _utc_now(),
                    "last_error": str(exc),
                }
            )

        self.write(state)
        return state


retrain_queue = RetrainQueue()
