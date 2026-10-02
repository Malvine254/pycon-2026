"""Pycord - a hybrid AI system with Microsoft Foundry and local models (PyCon Kenya 2026)."""
import sys

__version__ = "0.1.0"

# Windows consoles default to cp1252 and crash on characters like "‑" in model replies.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure") and (_stream.encoding or "").lower() not in ("utf-8", "utf8"):
        _stream.reconfigure(errors="replace")
