from __future__ import annotations

from typing import Any


def validate_extracted_fields(payload: dict[str, Any]) -> dict[str, Any]:
    warnings: list[str] = []
    values = payload.copy()

    for field in ["broker_name", "depository", "dp_id", "client_id"]:
        value = str(values.get(field) or "").strip()
        values[field] = value
        if not value:
            warnings.append(f"{field} is empty. Please verify from the broker or depository statement.")

    if values.get("dp_id") and len(values["dp_id"]) < 4:
        warnings.append("DP ID appears too short or incomplete. Please verify it from the official statement.")

    if values.get("client_id") and len(values["client_id"]) < 3:
        warnings.append("Client ID appears incomplete. Please verify it before using it in the grievance.")

    return {"values": values, "warnings": warnings}
