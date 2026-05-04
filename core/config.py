"""
Central runtime configuration.

All operational values are read from environment variables so secrets and
deployment-specific settings stay out of source code.
"""

from dataclasses import dataclass
import os


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    model_path: str = os.getenv("SPAM_MODEL_PATH", "data/model")
    model_name: str = os.getenv("SPAM_MODEL_NAME", "distilbert-base-uncased")
    model_max_length: int = _env_int("SPAM_MODEL_MAX_LENGTH", 256)
    threshold_path: str = os.getenv("SPAM_THRESHOLD_PATH", "data/runtime/threshold.json")
    bloom_path: str = os.getenv("SPAM_BLOOM_PATH", "data/runtime/spam_bloom.bin")
    ham_allowlist_path: str = os.getenv("SPAM_HAM_ALLOWLIST_PATH", "data/runtime/ham_allowlist.txt")
    reports_file: str = os.getenv("SPAM_REPORTS_FILE", "data/processed/user_reports.csv")
    retrain_state_path: str = os.getenv("SPAM_RETRAIN_STATE_PATH", "data/runtime/retrain_state.json")
    feedback_retrain_threshold: int = _env_int("SPAM_RETRAIN_THRESHOLD", 50)
    min_precision: float = _env_float("SPAM_MIN_PRECISION", 0.9)
    min_recall: float = _env_float("SPAM_MIN_RECALL", 0.9)
    min_f1: float = _env_float("SPAM_MIN_F1", 0.9)
    rate_limit_window_seconds: int = _env_int("SPAM_RATE_LIMIT_WINDOW_SECONDS", 60)
    rate_limit_feedback: int = _env_int("SPAM_RATE_LIMIT_FEEDBACK", 30)
    rate_limit_admin: int = _env_int("SPAM_RATE_LIMIT_ADMIN", 60)
    privacy_salt: str = os.getenv("SPAM_PRIVACY_SALT", "local-dev-salt-change-me")
    admin_token: str = os.getenv("SPAM_ADMIN_TOKEN", "change-me-admin-token")
    default_threshold: float = _env_float("SPAM_DEFAULT_THRESHOLD", 0.5)
    bloom_size: int = _env_int("SPAM_BLOOM_SIZE", 100000)
    bloom_hash_count: int = _env_int("SPAM_BLOOM_HASH_COUNT", 5)
    use_rule_fallback: bool = os.getenv("SPAM_USE_RULE_FALLBACK", "1") == "1"
    force_cpu: bool = os.getenv("SPAM_FORCE_CPU", "0") == "1"


settings = Settings()
