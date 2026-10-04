from utils.config import Settings


def test_settings_default_values():
    settings = Settings(
        gemini_api_key="test-key",
        gemini_model="gemini-3.8-flash",
        gemini_embedding_model="gemini-embedding-001",
        chat_max_output_tokens=1200,
    )
    assert settings.gemini_model == "gemini-3.8-flash"
    assert settings.gemini_embedding_model == "gemini-embedding-001"
    assert settings.chat_max_output_tokens == 1200


def test_missing_api_key_raises_on_from_env(monkeypatch):
    import utils.config as config

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr(config, "load_dotenv", lambda: None)
    try:
        config.Settings.from_env()
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError when GEMINI_API_KEY missing")


def test_chat_token_budget_is_configurable(monkeypatch):
    import utils.config as config

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("CHAT_MAX_OUTPUT_TOKENS", "1600")
    monkeypatch.setattr(config, "load_dotenv", lambda: None)

    assert config.Settings.from_env().chat_max_output_tokens == 1600
