"""Workshop settings loaded from environment variables and the project .env file."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = PROJECT_ROOT / "data" / "docs"

load_dotenv(PROJECT_ROOT / ".env")


def _float(name: str, default: float) -> float:
    value = os.getenv(name)
    return float(value) if value else default


@dataclass(frozen=True)
class Settings:
    foundry_endpoint: str
    foundry_api_key: str
    foundry_deployment: str
    foundry_api_version: str
    local_runtime: str
    local_model: str
    ollama_base_url: str
    ollama_model: str
    usd_to_kes: float
    cloud_input_usd_per_1k: float
    cloud_output_usd_per_1k: float

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            foundry_endpoint=os.getenv("FOUNDRY_ENDPOINT", "").rstrip("/"),
            foundry_api_key=os.getenv("FOUNDRY_API_KEY", ""),
            foundry_deployment=os.getenv("FOUNDRY_DEPLOYMENT", "gpt-5-mini"),
            foundry_api_version=os.getenv("FOUNDRY_API_VERSION", "2025-08-07"),
            local_runtime=os.getenv("LOCAL_RUNTIME", "foundry-local").lower(),
            local_model=os.getenv("LOCAL_MODEL", "phi-3.5-mini"),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
            ollama_model=os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b"),
            usd_to_kes=_float("USD_TO_KES", 129.0),
            cloud_input_usd_per_1k=_float("CLOUD_INPUT_USD_PER_1K", 0.00015),
            cloud_output_usd_per_1k=_float("CLOUD_OUTPUT_USD_PER_1K", 0.0006),
        )
