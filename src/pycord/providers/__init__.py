from __future__ import annotations

from ..config import Settings
from .base import ChatResult, Provider
from .foundry import FoundryProvider
from .local import FoundryLocalProvider

__all__ = [
    "ChatResult",
    "Provider",
    "FoundryProvider",
    "FoundryLocalProvider",
    "get_cloud_provider",
    "get_local_provider",
]


def get_cloud_provider(settings: Settings | None = None) -> FoundryProvider:
    return FoundryProvider(settings or Settings.from_env())


def get_local_provider(settings: Settings | None = None) -> FoundryLocalProvider:
    return FoundryLocalProvider(settings or Settings.from_env())
