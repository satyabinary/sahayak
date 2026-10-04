from utils.ai.schemas import VisionExtraction


def test_vision_schema_accepts_defaults():
    payload = {
        "broker_name": "Zerodha",
        "depository": "CDSL",
        "dp_id": "DP-123",
        "client_id": "CL-456",
        "confidence": {"broker_name": 0.9, "dp_id": 0.8, "client_id": 0.8},
        "evidence_text": "visible text",
        "warnings": []
    }
    model = VisionExtraction.model_validate(payload)
    assert model.broker_name == "Zerodha"
    assert model.dp_id == "DP-123"
