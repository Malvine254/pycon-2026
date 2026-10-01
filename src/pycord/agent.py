"""A minimal tool-calling agent that works with any provider that supports tools."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from .providers.base import Provider
from .rag import BM25Retriever

EAT = timezone(timedelta(hours=3), "EAT")

# Approximate workshop rates (KES per 1 unit) - not live market data.
KES_RATES = {"KES": 1.0, "USD": 129.0, "EUR": 150.0, "UGX": 0.035, "TZS": 0.05}

AGENT_SYSTEM_PROMPT = (
    "You are Msaidizi, a helpful assistant for people in Kenya. "
    "Use the available tools when they help. Be concise. Reply in the user's language (English or Swahili)."
)

TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "convert_currency",
            "description": "Convert money between KES, USD, EUR, UGX and TZS.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number"},
                    "from_currency": {"type": "string", "description": "e.g. USD"},
                    "to_currency": {"type": "string", "description": "e.g. KES"},
                },
                "required": ["amount", "from_currency", "to_currency"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "nairobi_time",
            "description": "Get the current date and time in Nairobi (EAT).",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_docs",
            "description": "Search the local knowledge base (M-Pesa safety, maize farming, workshop FAQ).",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
]


def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict[str, Any]:
    src, dst = from_currency.upper(), to_currency.upper()
    if src not in KES_RATES or dst not in KES_RATES:
        return {"error": f"Supported currencies: {', '.join(KES_RATES)}"}
    value = float(amount) * KES_RATES[src] / KES_RATES[dst]
    return {"amount": round(value, 2), "currency": dst, "note": "approximate workshop rates"}


def nairobi_time() -> dict[str, str]:
    now = datetime.now(EAT)
    return {"time": now.strftime("%H:%M"), "date": now.strftime("%A %d %B %Y"), "timezone": "EAT (UTC+3)"}


class Agent:
    def __init__(self, provider: Provider, retriever: BM25Retriever | None = None, max_steps: int = 5) -> None:
        self.provider = provider
        self.retriever = retriever
        self.max_steps = max_steps
        self.functions: dict[str, Callable[..., Any]] = {
            "convert_currency": convert_currency,
            "nairobi_time": nairobi_time,
        }
        if retriever is not None:
            self.functions["search_docs"] = self._search_docs
        self.tools = [t for t in TOOLS if t["function"]["name"] in self.functions]

    def _search_docs(self, query: str) -> dict[str, Any]:
        hits = self.retriever.search(query, top_k=3) if self.retriever else []
        return {"results": [{"source": c.source, "text": c.text} for c, _ in hits]}

    def call_tool(self, name: str, arguments: str) -> str:
        func = self.functions.get(name)
        if func is None:
            return json.dumps({"error": f"Unknown tool: {name}"})
        try:
            return json.dumps(func(**json.loads(arguments or "{}")), ensure_ascii=False)
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            return json.dumps({"error": str(exc)})

    def run(self, question: str, verbose: bool = True) -> str:
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ]
        for _ in range(self.max_steps):
            message = self.provider.complete(messages, tools=self.tools).choices[0].message
            if not message.tool_calls:
                return message.content or ""
            messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}}
                    for c in message.tool_calls
                ],
            })
            for call in message.tool_calls:
                if verbose:
                    print(f"  -> tool {call.function.name}({call.function.arguments})")
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": self.call_tool(call.function.name, call.function.arguments),
                })
        return "Sorry, I could not finish within the step limit."
