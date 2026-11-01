import re
from pathlib import Path

# 1. Patch backend/src/config.py
config_path = Path("backend/src/config.py")
content = config_path.read_text(encoding="utf-8")

old_preflight = """        self.youtube_preflight_timeout_seconds = self._get_positive_float_env(
            "YOUTUBE_PREFLIGHT_TIMEOUT_SECONDS",
            30.0,
            maximum=180.0,
        )"""

new_preflight = """        self.youtube_preflight_timeout_seconds = self._get_positive_float_env(
            "YOUTUBE_PREFLIGHT_TIMEOUT_SECONDS",
            90.0,
            maximum=300.0,
        )"""

if old_preflight in content:
    content = content.replace(old_preflight, new_preflight)
    config_path.write_text(content, encoding="utf-8")
    print("Patched backend/src/config.py successfully.")
else:
    print("Could not find exact preflight block in config.py, trying regex...")
    pattern = r'self\.youtube_preflight_timeout_seconds = self\._get_positive_float_env\(\s*"YOUTUBE_PREFLIGHT_TIMEOUT_SECONDS",\s*30\.0,\s*maximum=180\.0,\s*\)'
    if re.search(pattern, content):
        content = re.sub(pattern, 'self.youtube_preflight_timeout_seconds = self._get_positive_float_env(\n            "YOUTUBE_PREFLIGHT_TIMEOUT_SECONDS",\n            90.0,\n            maximum=300.0,\n        )', content)
        config_path.write_text(content, encoding="utf-8")
        print("Patched backend/src/config.py via regex.")
    else:
        print("Warning: preflight config already modified or pattern not found.")

# 2. Patch backend/src/youtube_utils.py
yt_path = Path("backend/src/youtube_utils.py")
yt_content = yt_path.read_text(encoding="utf-8")

# Ensure import shutil
if "import shutil" not in yt_content:
    yt_content = yt_content.replace("import time\n", "import shutil\nimport time\n")

# Patch _build_info_options
old_opts = """"socket_timeout": 30,"""
new_opts = """"socket_timeout": 15,
        "youtube_include_dash_manifest": False,
        "youtube_include_hls_manifest": False,"""
if old_opts in yt_content:
    yt_content = yt_content.replace(old_opts, new_opts, 1)

# Add deno check in _build_info_options
old_proxy_check = """    if proxy_configured():"""
new_proxy_check = """    if shutil.which("deno"):
        ydl_opts.setdefault("js_runtimes", {})["deno"] = {}
    if proxy_configured():"""
if old_proxy_check in yt_content and 'shutil.which("deno")' not in yt_content:
    yt_content = yt_content.replace(old_proxy_check, new_proxy_check, 1)

# Patch providers ordering to prefer Data API if key is present unless explicitly set to yt_dlp
old_providers = """    providers = [primary_provider, secondary_provider]"""
new_providers = """    if (
        config.resolve_youtube_data_api_key()
        and os.getenv("YOUTUBE_METADATA_PROVIDER") != YOUTUBE_METADATA_PROVIDER_YTDLP
    ):
        providers = [YOUTUBE_METADATA_PROVIDER_DATA_API, YOUTUBE_METADATA_PROVIDER_YTDLP]
    else:
        providers = [primary_provider, secondary_provider]"""
if old_providers in yt_content and "config.resolve_youtube_data_api_key()" not in yt_content:
    yt_content = yt_content.replace(old_providers, new_providers, 1)

yt_path.write_text(yt_content, encoding="utf-8")
print("Patched backend/src/youtube_utils.py successfully.")

# 3. Patch .env and .env.example
for env_file in [Path(".env"), Path(".env.example")]:
    if env_file.exists():
        e_content = env_file.read_text(encoding="utf-8")
        if "YOUTUBE_PREFLIGHT_TIMEOUT_SECONDS=30" in e_content:
            e_content = e_content.replace("YOUTUBE_PREFLIGHT_TIMEOUT_SECONDS=30", "YOUTUBE_PREFLIGHT_TIMEOUT_SECONDS=90")
            env_file.write_text(e_content, encoding="utf-8")
            print(f"Updated {env_file.name} YOUTUBE_PREFLIGHT_TIMEOUT_SECONDS to 90.")

