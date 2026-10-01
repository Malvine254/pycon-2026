"""Local providers: Foundry Local and Ollama (both expose an OpenAI-compatible API)."""
from __future__ import annotations

import shutil
import urllib.error
import urllib.request

from openai import OpenAI

from ..config import Settings
from .base import Provider


class FoundryLocalProvider(Provider):
    name = "foundry-local"
    is_local = True

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings.local_model)
        self.alias = settings.local_model

    def _build_client(self) -> OpenAI:
        from foundry_local import FoundryLocalManager

        # Starts the service, downloads the model on first use and loads it.
        manager = FoundryLocalManager(self.alias)
        self.model = manager.get_model_info(self.alias).id
        return OpenAI(base_url=manager.endpoint, api_key=manager.api_key)

    def is_available(self) -> bool:
        return shutil.which("foundry") is not None


class OllamaProvider(Provider):
    name = "ollama"
    is_local = True

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings.ollama_model)
        self.base_url = settings.ollama_base_url.rstrip("/")

    def _build_client(self) -> OpenAI:
        return OpenAI(base_url=self.base_url, api_key="ollama")

    def is_available(self) -> bool:
        root = self.base_url.removesuffix("/v1")
        try:
            with urllib.request.urlopen(f"{root}/api/tags", timeout=1.5) as response:
                return response.status == 200
        except (urllib.error.URLError, OSError):
            return False
