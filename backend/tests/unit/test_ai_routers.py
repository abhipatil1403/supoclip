from src.config import Config
from src.ai import (
    _split_llm_name,
    _get_missing_llm_key_error,
    _uses_native_output,
    _build_transcript_model,
)
from pydantic_ai.models.openai import OpenAIModel


def test_split_llm_name_routers():
    provider, model = _split_llm_name("fastrouter:anthropic/claude-sonnet-4.6")
    assert provider == "fastrouter"
    assert model == "anthropic/claude-sonnet-4.6"

    provider, model = _split_llm_name("anyrouter:gpt-4o")
    assert provider == "anyrouter"
    assert model == "gpt-4o"

    provider, model = _split_llm_name("openai:custom-model")
    assert provider == "openai"
    assert model == "custom-model"


def test_missing_key_error_routers(monkeypatch):
    monkeypatch.delenv("FASTROUTER_API_KEY", raising=False)
    monkeypatch.delenv("ANYROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    cfg = Config()
    assert "FASTROUTER_API_KEY" in _get_missing_llm_key_error("fastrouter:auto", cfg)
    assert "ANYROUTER_API_KEY" in _get_missing_llm_key_error("anyrouter:gpt-4o", cfg)

    monkeypatch.setenv("FASTROUTER_API_KEY", "fr-test-key")
    cfg2 = Config()
    assert _get_missing_llm_key_error("fastrouter:auto", cfg2) is None

    monkeypatch.setenv("ANYROUTER_API_KEY", "ar-test-key")
    cfg3 = Config()
    assert _get_missing_llm_key_error("anyrouter:gpt-4o", cfg3) is None


def test_uses_native_output():
    assert _uses_native_output("fastrouter:anthropic/claude-sonnet-4.6") is True
    assert _uses_native_output("anyrouter:gpt-4o") is True
    assert _uses_native_output("openrouter:anthropic/claude-sonnet-5.5") is True
    assert _uses_native_output("openai:gpt-4o") is False


def test_build_transcript_model_fastrouter(monkeypatch):
    monkeypatch.setenv("FASTROUTER_API_KEY", "test-fr-key")
    monkeypatch.setenv("LLM", "fastrouter:anthropic/claude-sonnet-4.6")
    cfg = Config()

    model = _build_transcript_model(cfg)
    assert isinstance(model, OpenAIModel)
    assert model.model_name == "anthropic/claude-sonnet-4.6"
    assert str(model.provider.base_url) == "https://api.fastrouter.ai/api/v1/"


def test_build_transcript_model_openai_custom_base_url(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://custom-router.example.com/v1")
    monkeypatch.setenv("LLM", "openai:custom-gpt")
    cfg = Config()

    model = _build_transcript_model(cfg)
    assert isinstance(model, OpenAIModel)
    assert model.model_name == "custom-gpt"
    assert str(model.provider.base_url) == "https://custom-router.example.com/v1/"

