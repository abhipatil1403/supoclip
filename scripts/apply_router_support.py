import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 1. Patch config.py
config_path = ROOT / "backend" / "src" / "config.py"
content = config_path.read_text(encoding="utf-8")

if "self.openai_base_url" not in content:
    target_init = '        self.openai_api_key = self._get_runtime_setting("OPENAI_API_KEY")\n        self.openrouter_api_key = self._get_runtime_setting("OPENROUTER_API_KEY")'
    replacement_init = (
        '        self.openai_api_key = self._get_runtime_setting("OPENAI_API_KEY")\n'
        '        self.openai_base_url = self._get_runtime_setting("OPENAI_BASE_URL")\n'
        '        self.fastrouter_api_key = self._get_runtime_setting("FASTROUTER_API_KEY")\n'
        '        self.fastrouter_base_url = (\n'
        '            self._get_runtime_setting("FASTROUTER_BASE_URL")\n'
        '            or "https://api.fastrouter.ai/api/v1"\n'
        '        )\n'
        '        self.anyrouter_api_key = self._get_runtime_setting("ANYROUTER_API_KEY")\n'
        '        self.anyrouter_base_url = (\n'
        '            self._get_runtime_setting("ANYROUTER_BASE_URL")\n'
        '            or "https://anyrouter.cfd/v1"\n'
        '        )\n'
        '        self.openrouter_api_key = self._get_runtime_setting("OPENROUTER_API_KEY")'
    )
    content = content.replace(target_init, replacement_init)

    target_runtime = '            "OPENAI_API_KEY": self.openai_api_key,\n            "OPENROUTER_API_KEY": self.openrouter_api_key,'
    replacement_runtime = (
        '            "OPENAI_API_KEY": self.openai_api_key,\n'
        '            "OPENAI_BASE_URL": self.openai_base_url,\n'
        '            "FASTROUTER_API_KEY": self.fastrouter_api_key,\n'
        '            "FASTROUTER_BASE_URL": self.fastrouter_base_url,\n'
        '            "ANYROUTER_API_KEY": self.anyrouter_api_key,\n'
        '            "ANYROUTER_BASE_URL": self.anyrouter_base_url,\n'
        '            "OPENROUTER_API_KEY": self.openrouter_api_key,'
    )
    content = content.replace(target_runtime, replacement_runtime)

    target_infer = '        if self.google_api_key:\n            return "google-gla:gemini-3-flash-preview"'
    replacement_infer = (
        '        if self.google_api_key:\n'
        '            return "google-gla:gemini-3-flash-preview"\n'
        '        if self.fastrouter_api_key:\n'
        '            return "fastrouter:auto"\n'
        '        if self.anyrouter_api_key:\n'
        '            return "anyrouter:gpt-4o"'
    )
    content = content.replace(target_infer, replacement_infer)
    config_path.write_text(content, encoding="utf-8")
    print("Patched config.py")

# 2. Patch runtime_settings.py
runtime_path = ROOT / "backend" / "src" / "runtime_settings.py"
content = runtime_path.read_text(encoding="utf-8")

if "FASTROUTER_API_KEY" not in content:
    target_keys = '    "OPENAI_API_KEY",\n    "OPENROUTER_API_KEY",'
    replacement_keys = (
        '    "OPENAI_API_KEY",\n'
        '    "OPENAI_BASE_URL",\n'
        '    "FASTROUTER_API_KEY",\n'
        '    "FASTROUTER_BASE_URL",\n'
        '    "ANYROUTER_API_KEY",\n'
        '    "ANYROUTER_BASE_URL",\n'
        '    "OPENROUTER_API_KEY",'
    )
    content = content.replace(target_keys, replacement_keys)
    runtime_path.write_text(content, encoding="utf-8")
    print("Patched runtime_settings.py")

# 3. Patch ai.py
ai_path = ROOT / "backend" / "src" / "ai.py"
content = ai_path.read_text(encoding="utf-8")

if "OpenAIProvider" not in content:
    # Add imports
    content = content.replace(
        "from pydantic_ai.models.openrouter import OpenRouterModel",
        "from pydantic_ai.models.openai import OpenAIModel\nfrom pydantic_ai.models.openrouter import OpenRouterModel",
    )
    content = content.replace(
        "from pydantic_ai.providers.openrouter import OpenRouterProvider",
        "from pydantic_ai.providers.openai import OpenAIProvider\nfrom pydantic_ai.providers.openrouter import OpenRouterProvider",
    )

    # Add supported providers
    content = content.replace(
        'SUPPORTED_LLM_PROVIDERS = {"google", "google-gla", "openai", "openrouter", "anthropic", "ollama"}',
        'SUPPORTED_LLM_PROVIDERS = {"google", "google-gla", "openai", "openrouter", "anthropic", "ollama", "fastrouter", "anyrouter"}',
    )

    # Provider errors
    content = content.replace(
        '"Use google-gla:*, openai:*, openrouter:*, anthropic:*, or ollama:*."',
        '"Use google-gla:*, openai:*, openrouter:*, anthropic:*, ollama:*, fastrouter:*, or anyrouter:*."',
    )

    missing_key_target = '    if provider == "openrouter" and not runtime_config.openrouter_api_key:\n        return "Selected LLM provider is OpenRouter, but OPENROUTER_API_KEY is not set."'
    missing_key_replacement = (
        missing_key_target + '\n\n'
        '    if provider == "fastrouter" and not (runtime_config.fastrouter_api_key or runtime_config.openai_api_key):\n'
        '        return "Selected LLM provider is FastRouter, but FASTROUTER_API_KEY (or OPENAI_API_KEY) is not set."\n\n'
        '    if provider == "anyrouter" and not (runtime_config.anyrouter_api_key or runtime_config.openai_api_key):\n'
        '        return "Selected LLM provider is AnyRouter, but ANYROUTER_API_KEY (or OPENAI_API_KEY) is not set."'
    )
    content = content.replace(missing_key_target, missing_key_replacement)

    # _uses_native_output
    content = content.replace(
        'return provider == "openrouter" or (',
        'return provider in {"openrouter", "fastrouter", "anyrouter"} or (',
    )

    # _build_transcript_model
    build_target = '    if provider == "openrouter":'
    build_router = (
        '    if provider in {"fastrouter", "anyrouter"} or (provider == "openai" and runtime_config.openai_base_url):\n'
        '        if provider == "fastrouter":\n'
        '            base_url = runtime_config.fastrouter_base_url or "https://api.fastrouter.ai/api/v1"\n'
        '            api_key = runtime_config.fastrouter_api_key or runtime_config.openai_api_key\n'
        '        elif provider == "anyrouter":\n'
        '            base_url = runtime_config.anyrouter_base_url or "https://anyrouter.cfd/v1"\n'
        '            api_key = runtime_config.anyrouter_api_key or runtime_config.openai_api_key\n'
        '        else:\n'
        '            base_url = runtime_config.openai_base_url\n'
        '            api_key = runtime_config.openai_api_key\n\n'
        '        profile = OpenAIModelProfile(supports_json_schema_output=True)\n'
        '        return OpenAIModel(\n'
        '            provider_model_name,\n'
        '            provider=OpenAIProvider(\n'
        '                base_url=base_url,\n'
        '                api_key=api_key,\n'
        '            ),\n'
        '            profile=profile,\n'
        '            settings={"max_tokens": 8192},\n'
        '        )\n\n'
        '    if provider == "openrouter":'
    )
    content = content.replace(build_target, build_router)

    # Signatures
    for func_sig in [
        '        runtime_config.openai_api_key,\n        runtime_config.openrouter_api_key,',
        '        runtime_config.openai_api_key,\n        runtime_config.openrouter_api_key,',
        '        runtime_config.openai_api_key,\n        runtime_config.openrouter_api_key,',
    ]:
        content = content.replace(
            '        runtime_config.openai_api_key,\n        runtime_config.openrouter_api_key,',
            (
                '        runtime_config.openai_api_key,\n'
                '        runtime_config.openai_base_url,\n'
                '        runtime_config.fastrouter_api_key,\n'
                '        runtime_config.fastrouter_base_url,\n'
                '        runtime_config.anyrouter_api_key,\n'
                '        runtime_config.anyrouter_base_url,\n'
                '        runtime_config.openrouter_api_key,'
            ),
            1,
        )

    ai_path.write_text(content, encoding="utf-8")
    print("Patched ai.py")

# 4. Patch docker-compose.yml
compose_path = ROOT / "docker-compose.yml"
content = compose_path.read_text(encoding="utf-8")

if "OPENAI_BASE_URL" not in content:
    target_compose = "      - OPENAI_API_KEY=${OPENAI_API_KEY}"
    replacement_compose = (
        "      - OPENAI_API_KEY=${OPENAI_API_KEY}\n"
        "      - OPENAI_BASE_URL=${OPENAI_BASE_URL:-}\n"
        "      - FASTROUTER_API_KEY=${FASTROUTER_API_KEY:-}\n"
        "      - FASTROUTER_BASE_URL=${FASTROUTER_BASE_URL:-}\n"
        "      - ANYROUTER_API_KEY=${ANYROUTER_API_KEY:-}\n"
        "      - ANYROUTER_BASE_URL=${ANYROUTER_BASE_URL:-}"
    )
    content = content.replace(target_compose, replacement_compose)
    compose_path.write_text(content, encoding="utf-8")
    print("Patched docker-compose.yml")

print("Done router patch!")

# 5. Patch PROCESS_ENV_SETTING_KEYS in runtime_settings.py
content = runtime_path.read_text(encoding="utf-8")
if '"FASTROUTER_BASE_URL"' not in content.split("PROCESS_ENV_SETTING_KEYS")[1]:
    target = 'PROCESS_ENV_SETTING_KEYS = frozenset(\n    {\n        "OPENAI_API_KEY",'
    replacement = (
        'PROCESS_ENV_SETTING_KEYS = frozenset(\n    {\n'
        '        "OPENAI_API_KEY",\n'
        '        "OPENAI_BASE_URL",\n'
        '        "FASTROUTER_API_KEY",\n'
        '        "FASTROUTER_BASE_URL",\n'
        '        "ANYROUTER_API_KEY",\n'
        '        "ANYROUTER_BASE_URL",'
    )
    content = content.replace(target, replacement, 1)
    runtime_path.write_text(content, encoding="utf-8")
    print("Patched PROCESS_ENV_SETTING_KEYS")
