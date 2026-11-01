import os
import shutil
from pathlib import Path

yt_path = Path("backend/src/youtube_utils.py")
content = yt_path.read_text(encoding="utf-8")

# 1. Add import os and import shutil if missing
imports_to_add = []
if "import os" not in content:
    imports_to_add.append("import os")
if "import shutil" not in content:
    imports_to_add.append("import shutil")

if imports_to_add:
    content = "\n".join(imports_to_add) + "\n" + content

# 2. Patch _build_info_options
target_block = """def _build_info_options(task_id: Optional[str] = None) -> Dict[str, Any]:
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extractaudio": False,
        "skip_download": True,
        # A watch?v=X&list=Y link otherwise resolves to the whole playlist,
        # which has no duration and can take minutes to walk.
        "noplaylist": True,
        "socket_timeout": 30,"""

replacement_block = """def _build_info_options(task_id: Optional[str] = None) -> Dict[str, Any]:
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extractaudio": False,
        "skip_download": True,
        # A watch?v=X&list=Y link otherwise resolves to the whole playlist,
        # which has no duration and can take minutes to walk.
        "noplaylist": True,
        "socket_timeout": 15,
        "youtube_include_dash_manifest": False,
        "youtube_include_hls_manifest": False,"""

if target_block in content:
    content = content.replace(target_block, replacement_block, 1)
    print("Replaced _build_info_options options.")
else:
    print("Target block for _build_info_options not found.")

# Add deno check in _build_info_options
proxy_target = """    if proxy_configured():"""
proxy_replacement = """    if shutil.which("deno"):
        ydl_opts.setdefault("js_runtimes", {})["deno"] = {}
    if proxy_configured():"""

if proxy_target in content:
    content = content.replace(proxy_target, proxy_replacement, 1)
    print("Added deno runtime check to _build_info_options.")
else:
    print("Proxy target not found.")

# 3. Patch provider fallback logic
providers_target = """    providers = [primary_provider, secondary_provider]"""
providers_replacement = """    # If YouTube Data API key / Google API key is configured, try it first for instant (<0.5s) metadata
    if (
        config.resolve_youtube_data_api_key()
        and os.getenv("YOUTUBE_METADATA_PROVIDER") != YOUTUBE_METADATA_PROVIDER_YTDLP
    ):
        providers = [YOUTUBE_METADATA_PROVIDER_DATA_API, YOUTUBE_METADATA_PROVIDER_YTDLP]
    else:
        providers = [primary_provider, secondary_provider]"""

if providers_target in content:
    content = content.replace(providers_target, providers_replacement, 1)
    print("Patched providers ordering in get_youtube_video_info.")
else:
    print("Providers target not found.")

yt_path.write_text(content, encoding="utf-8")
print("Finished patching backend/src/youtube_utils.py.")

