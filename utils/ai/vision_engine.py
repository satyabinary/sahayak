from __future__ import annotations

import json

from utils.ai.gemini_client import GeminiClient
from utils.ai.schemas import VisionExtraction


class VisionEngine:
    def __init__(self, client: GeminiClient | None = None) -> None:
        self.client = client or GeminiClient()

    def extract_dp_details(self, image_path: str) -> VisionExtraction:
        prompt = """
        Inspect the uploaded broker or depository screenshot.
        Extract these values if visible: broker_name, depository, dp_id, client_id.
        Return valid JSON only with keys: broker_name, depository, dp_id, client_id, confidence, evidence_text, warnings.
        confidence should be a dictionary with numeric values between 0 and 1.
        Make no unsupported assumptions.
        If uncertain, leave the value blank and note it in warnings.
        """.strip()
        raw = self.client.analyze_image(image_path, prompt)
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {
                "broker_name": None,
                "depository": None,
                "dp_id": None,
                "client_id": None,
                "confidence": {"broker_name": 0.0, "dp_id": 0.0, "client_id": 0.0},
                "evidence_text": raw,
                "warnings": ["The AI service returned data in an unexpected format. Please verify the details manually."],
            }
        return VisionExtraction.model_validate(payload)
