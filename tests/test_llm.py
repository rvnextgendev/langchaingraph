from unittest.mock import Mock, patch

import pytest

from order_assistant.llm import Settings, build_reply_writer


def test_model_failure_uses_factual_template():
    model = Mock()
    model.invoke.side_effect = TimeoutError("provider details")
    assert build_reply_writer(model)("1001", "Shipped") == "Order 1001: Shipped"


def test_empty_model_reply_uses_template():
    model = Mock()
    model.invoke.return_value.text = " "
    assert build_reply_writer(model)("1002", "Processing") == "Order 1002: Processing"


def test_settings_repr_hides_key():
    assert "secret-key" not in repr(Settings(model="demo", api_key="secret-key"))


def test_settings_reads_groq_environment(monkeypatch):
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "test-secret")
    monkeypatch.setenv("GROQ_MODEL", "test-model")
    with patch("dotenv.load_dotenv"):
        settings = Settings.from_env()
    assert settings.model == "test-model"
    assert settings.api_key == "test-secret"


def test_missing_groq_settings_has_actionable_error(monkeypatch):
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_MODEL", raising=False)
    with patch("dotenv.load_dotenv"), pytest.raises(ValueError, match="GROQ_API_KEY"):
        Settings.from_env()


def test_generic_model_setting_takes_precedence(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("LLM_MODEL", "chosen-model")
    monkeypatch.setenv("GROQ_MODEL", "legacy-model")
    monkeypatch.setenv("GROQ_API_KEY", "test-secret")
    with patch("dotenv.load_dotenv"):
        assert Settings.from_env().model == "chosen-model"


def test_unsupported_provider_is_rejected(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "unsupported")
    with patch("dotenv.load_dotenv"), pytest.raises(ValueError, match="LLM_PROVIDER"):
        Settings.from_env()
