"""Cloud provider: a model deployed in Microsoft Foundry."""
from __future__ import annotations

import socket
from urllib.parse import urlparse

from openai import AzureOpenAI

from ..config import Settings
from .base import Provider

COGNITIVE_SERVICES_SCOPE = "https://cognitiveservices.azure.com/.default"


def is_reachable(url: str, timeout: float = 2.0) -> bool:
    host = urlparse(url).hostname
    if not host:
        return False
    try:
        with socket.create_connection((host, 443), timeout=timeout):
            return True
    except OSError:
        return False


class FoundryProvider(Provider):
    name = "foundry"
    is_local = False

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings.foundry_deployment)
        self.settings = settings

    def _build_client(self) -> AzureOpenAI:
        s = self.settings
        if not s.foundry_endpoint:
            raise RuntimeError("FOUNDRY_ENDPOINT is not set. Copy .env.example to .env and fill it in.")
        if s.foundry_api_key:
            return AzureOpenAI(
                azure_endpoint=s.foundry_endpoint,
                api_key=s.foundry_api_key,
                api_version=s.foundry_api_version,
            )
        from azure.identity import DefaultAzureCredential, get_bearer_token_provider

        token_provider = get_bearer_token_provider(DefaultAzureCredential(), COGNITIVE_SERVICES_SCOPE)
        return AzureOpenAI(
            azure_endpoint=s.foundry_endpoint,
            azure_ad_token_provider=token_provider,
            api_version=s.foundry_api_version,
        )

    def is_available(self) -> bool:
        return bool(self.settings.foundry_endpoint) and is_reachable(self.settings.foundry_endpoint)

    def cost_kes(self, prompt_tokens: int, completion_tokens: int) -> float:
        s = self.settings
        usd = (prompt_tokens / 1000) * s.cloud_input_usd_per_1k + (completion_tokens / 1000) * s.cloud_output_usd_per_1k
        return usd * s.usd_to_kes
