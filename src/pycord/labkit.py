"""Helpers that keep the lab scripts running when a model is not installed yet."""
from __future__ import annotations

from .config import Settings
from .providers import Provider, get_cloud_provider, get_local_provider

LOCAL_SETUP_HINT = """\
[!!] Local model not available - the local parts of this lab will be skipped or use the cloud.
     To install one (see labs/00-setup.md):
       Foundry Local:  winget install Microsoft.FoundryLocal   (macOS: brew install foundrylocal)
                       foundry model run phi-3.5-mini
       Ollama:         ollama pull qwen2.5:1.5b   and set LOCAL_RUNTIME=ollama in .env"""


def local_or_cloud(settings: Settings | None = None) -> Provider:
    """Prefer the local model; fall back to the cloud model so the lab can continue."""
    settings = settings or Settings.from_env()
    local = get_local_provider(settings)
    if local.is_available():
        return local
    print(LOCAL_SETUP_HINT)
    cloud = get_cloud_provider(settings)
    if cloud.is_available():
        print("     Continuing with the cloud model so you can follow along.\n")
        return cloud
    raise RuntimeError("No model available: install a local model or set FOUNDRY_ENDPOINT in .env (see labs/00-setup.md).")
