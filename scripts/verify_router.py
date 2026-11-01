import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(ROOT))

from src.config import Config
from src.ai import (
    _split_llm_name,
    _get_missing_llm_key_error,
    _uses_native_output,
    _build_transcript_model,
)
from pydantic_ai.models.openai import OpenAIModel

def verify():
    # 1. Test splitting names
    p, m = _split_llm_name("fastrouter:anthropic/claude-sonnet-4.6")
    assert p == "fastrouter" and m == "anthropic/claude-sonnet-4.6", f"Failed: {p}, {m}"

    p, m = _split_llm_name("anyrouter:gpt-4o")
    assert p == "anyrouter" and m == "gpt-4o", f"Failed: {p}, {m}"

    p, m = _split_llm_name("openai:custom-model")
    assert p == "openai" and m == "custom-model", f"Failed: {p}, {m}"
    print("✓ _split_llm_name works for fastrouter, anyrouter, and openai")

    # 2. Test missing key errors
    os.environ.pop("FASTROUTER_API_KEY", None)
    os.environ.pop("ANYROUTER_API_KEY", None)
    os.environ.pop("OPENAI_API_KEY", None)
    cfg = Config()
    err = _get_missing_llm_key_error("fastrouter:auto", cfg)
    assert "FASTROUTER_API_KEY" in err, f"Unexpected error: {err}"

    err = _get_missing_llm_key_error("anyrouter:gpt-4o", cfg)
    assert "ANYROUTER_API_KEY" in err, f"Unexpected error: {err}"

    os.environ["FASTROUTER_API_KEY"] = "test-fr-key"
    cfg = Config()
    assert _get_missing_llm_key_error("fastrouter:auto", cfg) is None

    os.environ["ANYROUTER_API_KEY"] = "test-ar-key"
    cfg = Config()
    assert _get_missing_llm_key_error("anyrouter:gpt-4o", cfg) is None
    print("✓ _get_missing_llm_key_error works for fastrouter & anyrouter")

    # 3. Test _uses_native_output
    assert _uses_native_output("fastrouter:anthropic/claude-sonnet-4.6") is True
    assert _uses_native_output("anyrouter:gpt-4o") is True
    assert _uses_native_output("openai:gpt-4o") is False
    print("✓ _uses_native_output flags routers for native JSON output")

    # 4. Test _build_transcript_model for FastRouter
    os.environ["LLM"] = "fastrouter:anthropic/claude-sonnet-4.6"
    cfg = Config()
    model = _build_transcript_model(cfg)
    assert isinstance(model, OpenAIModel), f"Expected OpenAIModel, got {type(model)}"
    assert model.model_name == "anthropic/claude-sonnet-4.6"
    assert str(model.provider.base_url) == "https://api.fastrouter.ai/api/v1/"
    print("✓ _build_transcript_model instantiates OpenAIModel with FastRouter base URL")

    # 5. Test _build_transcript_model for custom OpenAI base URL
    os.environ["LLM"] = "openai:custom-model"
    os.environ["OPENAI_API_KEY"] = "sk-custom"
    os.environ["OPENAI_BASE_URL"] = "https://custom-gateway.xyz/v1"
    cfg = Config()
    model = _build_transcript_model(cfg)
    assert isinstance(model, OpenAIModel), f"Expected OpenAIModel, got {type(model)}"
    assert model.model_name == "custom-model"
    assert str(model.provider.base_url) == "https://custom-gateway.xyz/v1/"
    print("✓ _build_transcript_model instantiates OpenAIModel with custom OPENAI_BASE_URL")

    print("\nALL VERIFICATIONS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    verify()

