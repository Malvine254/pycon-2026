"""Local providers: Foundry Local and Ollama (both expose an OpenAI-compatible API)."""
from __future__ import annotations

import shutil
import re
import subprocess
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
        try:
            status = subprocess.run(
                ["foundry", "server", "status"],
                capture_output=True,
                check=True,
                text=True,
                timeout=10,
            ).stdout
        except (OSError, subprocess.SubprocessError) as exc:
            raise RuntimeError("Foundry Local server is not running. Start it with `foundry server start`.") from exc

        match = re.search(r"Web URLs\s+(https?://\S+)", status)
        if not match:
            raise RuntimeError("Foundry Local server endpoint was not found in `foundry server status`.")

        client = OpenAI(base_url=f"{match.group(1)}/v1", api_key="foundry-local")
        models = list(client.models.list().data)
        model = next((item for item in models if self.alias.lower() in item.id.lower()), None)
        if model is None:
            raise RuntimeError(f"Foundry Local model '{self.alias}' is not loaded.")
        self.model = model.id
        return client

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
