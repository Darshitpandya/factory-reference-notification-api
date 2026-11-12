"""
PII redaction utilities.

All log entries, error traces, retry payloads, and audit exports
must run through these functions before emission.
"""

import re
from typing import Any

# Patterns to redact
_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_PHONE_RE = re.compile(r"\b(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_CREDIT_CARD_RE = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")

REDACTED = "[REDACTED]"


def redact_string(value: str) -> str:
    """Redact PII patterns from a string."""
    value = _EMAIL_RE.sub(REDACTED, value)
    value = _PHONE_RE.sub(REDACTED, value)
    value = _SSN_RE.sub(REDACTED, value)
    value = _CREDIT_CARD_RE.sub(REDACTED, value)
    return value


def redact_dict(data: dict[str, Any], pii_fields: set[str] | None = None) -> dict[str, Any]:
    """
    Recursively redact known PII fields and apply pattern matching.
    pii_fields: field names that are always redacted regardless of content.
    """
    _pii_fields = pii_fields or {
        "email", "phone", "mobile", "address", "ssn",
        "creditCard", "credit_card", "password", "token",
        "secret", "apiKey", "api_key",
    }

    result: dict[str, Any] = {}
    for key, value in data.items():
        if key in _pii_fields:
            result[key] = REDACTED
        elif isinstance(value, str):
            result[key] = redact_string(value)
        elif isinstance(value, dict):
            result[key] = redact_dict(value, _pii_fields)
        elif isinstance(value, list):
            result[key] = [
                redact_dict(item, _pii_fields) if isinstance(item, dict)
                else redact_string(item) if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            result[key] = value
    return result
