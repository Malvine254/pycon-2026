"""Small local-only persistence for the Mela demo app."""
from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from .config import PROJECT_ROOT

RUNTIME_DIR = PROJECT_ROOT / ".mela"
UPLOADS_DIR = RUNTIME_DIR / "uploads"
HISTORY_FILE = RUNTIME_DIR / "history.json"
INSTRUCTIONS_FILE = RUNTIME_DIR / "instructions.txt"
_lock = threading.Lock()


def _ensure_runtime() -> None:
    RUNTIME_DIR.mkdir(exist_ok=True)
    UPLOADS_DIR.mkdir(exist_ok=True)


def load_history() -> dict[str, dict[str, Any]]:
    _ensure_runtime()
    if not HISTORY_FILE.exists():
        return {}
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_history(history: dict[str, dict[str, Any]]) -> None:
    _ensure_runtime()
    with _lock:
        HISTORY_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")


def load_instructions() -> str:
    _ensure_runtime()
    try:
        return INSTRUCTIONS_FILE.read_text(encoding="utf-8") if INSTRUCTIONS_FILE.exists() else ""
    except OSError:
        return ""


def save_instructions(value: str) -> None:
    _ensure_runtime()
    with _lock:
        INSTRUCTIONS_FILE.write_text(value.strip(), encoding="utf-8")


def save_upload(name: str, data: bytes) -> Path:
    _ensure_runtime()
    path = UPLOADS_DIR / name
    path.write_bytes(data)
    return path


def delete_upload(name: str) -> None:
    try:
        (UPLOADS_DIR / name).unlink()
    except FileNotFoundError:
        pass


def list_uploads() -> list[Path]:
    _ensure_runtime()
    return [path for path in UPLOADS_DIR.iterdir() if path.is_file()]