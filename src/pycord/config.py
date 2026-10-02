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


def _int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value else default


@dataclass(frozen=True)
class Settings:
    app_host: str
    app_port: int
    foundry_endpoint: str
    foundry_api_key: str
    foundry_deployment: str
    foundry_api_version: str
    local_model: str
    local_endpoint: str
    usd_to_kes: float
    cloud_input_usd_per_1k: float
    cloud_output_usd_per_1k: float

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            app_host=os.getenv("APP_HOST", "127.0.0.1"),
            app_port=_int("APP_PORT", 8000),
            foundry_endpoint=os.getenv("FOUNDRY_ENDPOINT", "").rstrip("/"),
            foundry_api_key=os.getenv("FOUNDRY_API_KEY", ""),
            foundry_deployment=os.getenv("FOUNDRY_DEPLOYMENT", "gpt-5-mini"),
            foundry_api_version=os.getenv("FOUNDRY_API_VERSION", "2025-08-07"),
            local_model=os.getenv("LOCAL_MODEL", "phi-3.5-mini"),
            local_endpoint=os.getenv("LOCAL_ENDPOINT", "").strip(),
            usd_to_kes=_float("USD_TO_KES", 129.0),
            cloud_input_usd_per_1k=_float("CLOUD_INPUT_USD_PER_1K", 0.00015),
            cloud_output_usd_per_1k=_float("CLOUD_OUTPUT_USD_PER_1K", 0.0006),
        )
