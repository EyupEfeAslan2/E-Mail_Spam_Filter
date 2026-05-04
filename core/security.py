"""
Security and privacy helpers.
"""

import hashlib
import re
import secrets
from typing import Optional

from core.config import settings


EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)")


def privacy_hash(value: str, salt: Optional[str] = None) -> str:
    """Data structure: salted SHA-256 hash for privacy-preserving identity keys."""
    chosen_salt = salt if salt is not None else settings.privacy_salt
    return hashlib.sha256(f"{chosen_salt}:{value}".encode("utf-8")).hexdigest()


def redact_email_text(text: str) -> str:
    """Redact common personal identifiers before feedback is persisted."""
    text = EMAIL_RE.sub("[EMAIL]", text)
    text = PHONE_RE.sub("[PHONE]", text)
    return text


def verify_admin_token(token: Optional[str]) -> bool:
    """Data structure: constant-time token comparison protects admin endpoints."""
    if not token:
        return False
    return secrets.compare_digest(token, settings.admin_token)
