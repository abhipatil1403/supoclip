from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
example_path = ROOT / ".env.example"
env_path = ROOT / ".env"

content = example_path.read_text(encoding="utf-8")

# Insert Router settings
router_keys = """# Custom OpenAI-compatible router / gateway (FastRouter, AnyRouter, LiteLLM, Groq, DeepSeek)
OPENAI_BASE_URL=
FASTROUTER_API_KEY=
FASTROUTER_BASE_URL=https://api.fastrouter.ai/api/v1
ANYROUTER_API_KEY=
ANYROUTER_BASE_URL=https://anyrouter.cfd/v1
"""

if "FASTROUTER_API_KEY" not in content:
    content = content.replace("OPENAI_API_KEY=\n", "OPENAI_API_KEY=\n" + router_keys)

# Replace secrets
content = content.replace(
    "BETTER_AUTH_SECRET=supoclip_dev_secret_change_in_production",
    "BETTER_AUTH_SECRET=7eca18916c4dc7d9f44c7238bb436a55141391ae96ce12f88acaef85a78e6412"
)
content = content.replace(
    "BACKEND_AUTH_SECRET=change_me_backend_auth_secret",
    "BACKEND_AUTH_SECRET=806ddf2c4478d193fee0b894988792437fd2835fe2320b632caca4f356ae4839"
)
content = content.replace(
    "APP_SETTINGS_ENCRYPTION_KEY=change_me_settings_encryption_secret",
    "APP_SETTINGS_ENCRYPTION_KEY=9ef08f2ca8d49679832639bf1a44e68306d31f341ed431b45cd45b1630b71824"
)

# Also update .env.example with the router keys
example_path.write_text(content, encoding="utf-8")

# Write .env
env_path.write_text(content, encoding="utf-8")
print("Successfully generated .env and updated .env.example")

