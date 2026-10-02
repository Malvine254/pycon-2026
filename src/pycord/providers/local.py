"""Local provider: Phi running on Foundry Local (OpenAI-compatible API on localhost)."""
from __future__ import annotations

import json
import shutil
import re
import subprocess
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
        self.configured_endpoint = settings.local_endpoint.rstrip("/").removesuffix("/v1")

    def endpoint(self) -> str | None:
        """Base URL of Foundry Local, e.g. http://127.0.0.1:5273 (LOCAL_ENDPOINT wins over auto-detect)."""
        if self.configured_endpoint:
            return self.configured_endpoint
        if shutil.which("foundry") is None:
            return None
        try:
            status = subprocess.run(
                ["foundry", "server", "status"],
                capture_output=True,
                check=True,
                text=True,
                timeout=10,
            ).stdout
        except (OSError, subprocess.SubprocessError):
            return None
        match = re.search(r"Web URLs\s+(https?://\S+)", status)
        return match.group(1).rstrip("/") if match else None

    def _build_client(self) -> OpenAI:
        base_url = self.endpoint()
        if base_url is None:
            raise RuntimeError(
                f"Foundry Local is not running. Run `foundry server start`, then `foundry model load {self.alias}` "
                "(see labs/00-setup.md, Step 2)."
            )

        client = OpenAI(base_url=f"{base_url}/v1", api_key="foundry-local")
        models = list(client.models.list().data)
        model = next((item for item in models if self.alias.lower() in item.id.lower()), None)
        if model is None:
            raise RuntimeError(f"Foundry Local model '{self.alias}' is not loaded. Run `foundry model load {self.alias}`.")
        self.model = model.id
        return client

    def is_available(self) -> bool:
        base_url = self.endpoint()
        if base_url is None:
            return False
        try:
            with urllib.request.urlopen(f"{base_url}/v1/models", timeout=2) as response:
                models = json.loads(response.read()).get("data", [])
            return any(self.alias.lower() in str(model.get("id", "")).lower() for model in models)
        except (OSError, ValueError, json.JSONDecodeError):
            return False
