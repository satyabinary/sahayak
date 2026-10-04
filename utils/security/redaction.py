import re
from typing import Any


SENSITIVE_PATTERNS = (
    (re.compile(r"(?i)\b(?:pan|aadhaar|account|bank)\b.*?[A-Z0-9]{4,}\b"), "[REDACTED]"),
    (re.compile(r"\b\d{12}\b"), "[REDACTED_AADHAAR]"),
    (re.compile(r"\b\d{16}\b"), "[REDACTED_CARD]"),
    (re.compile(r"(?i)(?:api[_ -]?key|token)\s*[:=]\s*[^\s,;]+"), "api_key=[REDACTED]"),
)


def redact_sensitive_text(text: str | None) -> str:
    if not text:
        return ""
    redacted = text
    for pattern, replacement in SENSITIVE_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def safe_log_data(data: Any) -> str:
    try:
        return redact_sensitive_text(str(data))
    except Exception:
        return "[unavailable]"
