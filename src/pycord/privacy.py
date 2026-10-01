"""Detect Kenyan personal data so it never leaves the device."""
from __future__ import annotations

import re
from dataclasses import dataclass

PATTERNS: dict[str, re.Pattern[str]] = {
    "phone_ke": re.compile(r"(?<!\d)(?:\+?254[\s-]?|0)[17]\d{2}[\s-]?\d{3}[\s-]?\d{3}(?!\d)"),
    "kra_pin": re.compile(r"\b[AP]\d{9}[A-Z]\b"),
    # 10 uppercase letters/digits containing at least one of each, e.g. QFT3XYZ12A
    "mpesa_code": re.compile(r"\b(?=[A-Z0-9]*\d)(?=[A-Z0-9]*[A-Z])[A-Z0-9]{10}\b"),
    "national_id": re.compile(r"\b(?:national\s+)?id(?:\s*(?:no\.?|number))?\s*[:#]?\s*\d{7,8}\b", re.IGNORECASE),
    "email": re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b"),
}


@dataclass(frozen=True)
class PIIMatch:
    kind: str
    value: str
    start: int
    end: int


def detect_pii(text: str) -> list[PIIMatch]:
    matches = [
        PIIMatch(kind, m.group(), m.start(), m.end())
        for kind, pattern in PATTERNS.items()
        for m in pattern.finditer(text)
    ]
    return sorted(matches, key=lambda m: m.start)


def contains_pii(text: str) -> bool:
    return any(pattern.search(text) for pattern in PATTERNS.values())


def redact(text: str) -> str:
    for kind, pattern in PATTERNS.items():
        text = pattern.sub(f"[{kind.upper()}]", text)
    return text
