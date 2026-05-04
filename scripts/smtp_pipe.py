"""
Postfix/Exim pipe helper for SMTP integration.

Example Postfix transport can pipe raw RFC822 messages to this script. The script
extracts the plain-text body, calls the spam API, and exits with a non-zero code
only when the API is unreachable.
"""

import email
import os
import sys

import requests


API_URL = os.getenv("SPAM_API_URL", "http://127.0.0.1:8000/predict")
REQUEST_TIMEOUT = int(os.getenv("SPAM_API_TIMEOUT", "10"))


def get_email_body(msg):
    """Data structure: Tree traversal. MIME parts are walked as a message tree."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True) or b""
                return payload.decode(part.get_content_charset() or "utf-8", errors="replace")
    payload = msg.get_payload(decode=True) or b""
    return payload.decode(msg.get_content_charset() or "utf-8", errors="replace")


def main() -> int:
    raw_message = sys.stdin.buffer.read()
    if not raw_message:
        print("No message received.", file=sys.stderr)
        return 64

    msg = email.message_from_bytes(raw_message)
    body = get_email_body(msg)
    response = requests.post(API_URL, json={"text": body}, timeout=REQUEST_TIMEOUT)
    if response.status_code != 200:
        print(f"Spam API failed: {response.status_code}", file=sys.stderr)
        return 75

    result = response.json()
    print(f"{result['prediction']} confidence={result['confidence']:.3f} layer={result['layer']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
