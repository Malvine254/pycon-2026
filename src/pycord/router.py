"""Hybrid router: decide per request whether to run locally or in the cloud."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .privacy import contains_pii
from .providers.base import ChatResult, Provider

COMPLEX_HINTS = (
    "step by step",
    "analyse",
    "analyze",
    "compare",
    "write code",
    "python code",
    "explain in detail",
    "summarise",
    "summarize",
    "translate",
    "plan",
)


def is_complex(prompt: str, max_simple_chars: int = 400) -> bool:
    text = prompt.lower()
    return len(prompt) > max_simple_chars or any(hint in text for hint in COMPLEX_HINTS)


@dataclass(frozen=True)
class RouteDecision:
    target: str  # "local" or "cloud"
    reason: str
    allow_fallback: bool = True


class HybridRouter:
    def __init__(self, local: Provider, cloud: Provider, max_simple_chars: int = 400) -> None:
        self.local = local
        self.cloud = cloud
        self.max_simple_chars = max_simple_chars

    def decide(self, text: str) -> RouteDecision:
        local_ok = self.local.is_available()
        if contains_pii(text):
            if not local_ok:
                raise RuntimeError("Personal data detected but no local model is available; refusing to send it to the cloud.")
            return RouteDecision("local", "personal data detected - keeping it on this device", allow_fallback=False)

        cloud_ok = self.cloud.is_available()
        if not cloud_ok and not local_ok:
            raise RuntimeError("No model available: the cloud is unreachable and no local runtime was found.")
        if not cloud_ok:
            return RouteDecision("local", "cloud unreachable - working offline")
        if not local_ok:
            return RouteDecision("cloud", "no local runtime found")
        if is_complex(text, self.max_simple_chars):
            return RouteDecision("cloud", "complex task - using the bigger cloud model")
        return RouteDecision("local", "simple task - local is free and private")

    def chat(self, messages: list[dict[str, Any]], **kwargs: Any) -> ChatResult:
        # Check the whole conversation, not just the last turn, for personal data.
        user_text = "\n".join(str(m.get("content") or "") for m in messages if m.get("role") == "user")
        decision = self.decide(user_text)
        primary, backup = (self.local, self.cloud) if decision.target == "local" else (self.cloud, self.local)
        try:
            result = primary.chat(messages, **kwargs)
            result.route_reason = decision.reason
        except Exception as exc:
            if not decision.allow_fallback:
                raise
            result = backup.chat(messages, **kwargs)
            result.route_reason = f"{decision.reason}; {primary.name} failed ({type(exc).__name__}), fell back to {backup.name}"
        return result

    def ask(self, prompt: str, system: str | None = None, **kwargs: Any) -> ChatResult:
        messages: list[dict[str, Any]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return self.chat(messages, **kwargs)
