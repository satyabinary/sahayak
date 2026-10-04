from __future__ import annotations

from typing import Any


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def is_valid_dp_id(dp_id: str | None) -> bool:
    if not dp_id:
        return False
    cleaned = dp_id.strip()
    if len(cleaned) < 4 or len(cleaned) > 20:
        return False
    return all(ch.isalnum() or ch in {"-", "/", "_"} for ch in cleaned)


def is_valid_client_id(client_id: str | None) -> bool:
    if not client_id:
        return False
    cleaned = client_id.strip()
    return len(cleaned) >= 3 and len(cleaned) <= 25


def required_missing(case_data: dict[str, Any]) -> list[str]:
    required = ["investor_name", "broker_name", "issue_category", "description"]
    missing = []
    for field in required:
        if not normalize_text(case_data.get(field)):
            missing.append(field)
    return missing
