from types import SimpleNamespace

from fastapi.testclient import TestClient

from backend import api


client = TestClient(api.app)


def test_health_reports_api_and_gemini_configuration():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_chat_api_delegates_to_chat_engine(monkeypatch):
    recorded = {}

    class FakeChatEngine:
        def handle_message(self, message, **kwargs):
            recorded["message"] = message
            recorded.update(kwargs)
            return SimpleNamespace(
                answer="Namaste! How can I help?",
                mode="general",
                retrieved_count=0,
                gemini_called=True,
                sources=[],
                grievance_case=None,
                pending_case_field=None,
            )

    monkeypatch.setattr(api, "ChatEngine", FakeChatEngine)
    response = client.post(
        "/api/chat",
        json={
            "session_id": "test-session",
            "message": "hi",
            "language": "english",
            "history": [],
            "case": {},
            "pending_case_field": None,
        },
    )

    assert response.status_code == 200
    assert response.json()["answer"] == "Namaste! How can I help?"
    assert recorded["message"] == "hi"
    assert recorded["language"] == "english"
    assert "gemini_called" not in response.json()
    assert "retrieved_count" not in response.json()


def test_grievance_case_is_saved_and_returned():
    payload = {
        "session_id": "api-test-case",
        "case": {"broker_name": "User Broker", "amount_involved": "Rs 2500"},
    }

    saved = client.post("/api/grievance", json=payload)
    loaded = client.get("/api/grievance/api-test-case")

    assert saved.status_code == 200
    assert loaded.status_code == 200
    assert loaded.json()["case"]["broker_name"] == "User Broker"
    assert loaded.json()["case"]["amount_involved"] == "Rs 2500"


def test_vision_rejects_unrecognized_image_bytes():
    response = client.post(
        "/api/vision/extract",
        files={"image": ("not-image.png", b"not an image", "image/png")},
    )

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "request_error"


def test_validation_errors_use_safe_consistent_json():
    response = client.post("/api/chat", json={"message": "hi"})

    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "validation_error",
            "message": "Please check the submitted information.",
        }
    }


def test_knowledge_diagnostics_are_disabled_outside_development(monkeypatch):
    monkeypatch.setattr(api.settings, "app_env", "production")

    response = client.get("/api/knowledge-base/status")

    assert response.status_code == 404
    assert response.json()["error"]["message"] == "Not found."


def test_pdf_endpoint_returns_downloadable_pdf():
    response = client.post("/api/complaint/pdf", json={"content": "Complaint draft"})

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


def test_pdf_endpoint_supports_hindi_text():
    response = client.post("/api/complaint/pdf", json={"content": "शिकायत का मसौदा"})

    assert response.status_code == 200
    assert response.content.startswith(b"%PDF")
