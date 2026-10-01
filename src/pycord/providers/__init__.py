from __future__ import annotations

from ..config import Settings
from .base import ChatResult, Provider
from .foundry import FoundryProvider
from .local import FoundryLocalProvider, OllamaProvider

__all__ = [
    "ChatResult",
    "Provider",
    "FoundryProvider",
    "FoundryLocalProvider",
    "OllamaProvider",
    "get_cloud_provider",
    "get_local_provider",
]


def get_cloud_provider(settings: Settings | None = None) -> FoundryProvider:
    return FoundryProvider(settings or Settings.from_env())


def get_local_provider(settings: Settings | None = None) -> Provider:
    settings = settings or Settings.from_env()
    if settings.local_runtime == "foundry-local":
        return FoundryLocalProvider(settings)
    if settings.local_runtime == "ollama":
        return OllamaProvider(settings)
    raise ValueError(f"Unknown LOCAL_RUNTIME '{settings.local_runtime}'. Use 'foundry-local' or 'ollama'.")
