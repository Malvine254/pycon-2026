"""Common interface shared by cloud and local model providers."""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from openai import OpenAI


@dataclass
class ChatResult:
    text: str
    provider: str
    model: str
    latency_s: float
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_kes: float = 0.0
    route_reason: str = ""

    def summary(self) -> str:
        return (
            f"[{self.provider} | {self.model} | {self.latency_s:.2f}s | "
            f"{self.prompt_tokens}+{self.completion_tokens} tokens | KES {self.cost_kes:.4f}]"
        )


class Provider(ABC):
    """Any OpenAI-compatible chat endpoint: Microsoft Foundry or Foundry Local."""

    name: str = "provider"
    is_local: bool = False

    def __init__(self, model: str) -> None:
        self.model = model
        self._client: OpenAI | None = None

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            self._client = self._build_client()
        return self._client

    @abstractmethod
    def _build_client(self) -> OpenAI: ...

    @abstractmethod
    def is_available(self) -> bool: ...

    def cost_kes(self, prompt_tokens: int, completion_tokens: int) -> float:
        return 0.0

    def complete(self, messages: list[dict[str, Any]], **kwargs: Any):
        client = self.client  # building the client can resolve the real model id
        return client.chat.completions.create(model=self.model, messages=messages, **kwargs)

    def chat(self, messages: list[dict[str, Any]], **kwargs: Any) -> ChatResult:
        start = time.perf_counter()
        response = self.complete(messages, **kwargs)
        latency = time.perf_counter() - start
        usage = response.usage
        prompt_tokens = usage.prompt_tokens if usage else 0
        completion_tokens = usage.completion_tokens if usage else 0
        return ChatResult(
            text=response.choices[0].message.content or "",
            provider=self.name,
            model=self.model,
            latency_s=latency,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_kes=self.cost_kes(prompt_tokens, completion_tokens),
        )

    def ask(self, prompt: str, system: str | None = None, **kwargs: Any) -> ChatResult:
        messages: list[dict[str, Any]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return self.chat(messages, **kwargs)
