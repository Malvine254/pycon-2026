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
            raise RuntimeError(
                f"Foundry Local is not running. Run `foundry server start`, then `foundry model load {self.alias}` "
                "(see labs/00-setup.md, Step 2)."
            ) from exc

        match = re.search(r"Web URLs\s+(https?://\S+)", status)
        if not match:
            raise RuntimeError("Foundry Local server endpoint was not found in `foundry server status`.")

        client = OpenAI(base_url=f"{match.group(1)}/v1", api_key="foundry-local")
        models = list(client.models.list().data)
        model = next((item for item in models if self.alias.lower() in item.id.lower()), None)
        if model is None:
            raise RuntimeError(f"Foundry Local model '{self.alias}' is not loaded. Run `foundry model load {self.alias}`.")
        self.model = model.id
        return client

    def is_available(self) -> bool:
        if shutil.which("foundry") is None:
            return False
        try:
            status = subprocess.run(
                ["foundry", "server", "status"],
                capture_output=True,
                check=True,
                text=True,
                timeout=5,
            ).stdout
            match = re.search(r"Web URLs\s+(https?://\S+)", status)
            if "Ready" not in status or not match:
                return False
            with urllib.request.urlopen(f"{match.group(1)}/v1/models", timeout=2) as response:
                models = json.loads(response.read()).get("data", [])
            return any(self.alias.lower() in str(model.get("id", "")).lower() for model in models)
        except (OSError, ValueError, json.JSONDecodeError, subprocess.SubprocessError):
            return False
