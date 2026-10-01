"""A minimal tool-calling agent that works with any provider that supports tools."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from .privacy import redact
from .providers.base import Provider
from .rag import BM25Retriever


@dataclass
class ToolCall:
    name: str
    arguments: str
    result: str


@dataclass
class AgentReply:
    text: str
    provider: str
    model: str
    latency_s: float
    cost_kes: float = 0.0
    tool_calls: list[ToolCall] = field(default_factory=list)

EAT = timezone(timedelta(hours=3), "EAT")

# Approximate workshop rates (KES per 1 unit) - not live market data.
KES_RATES = {"KES": 1.0, "USD": 129.0, "EUR": 150.0, "UGX": 0.035, "TZS": 0.05}

AGENT_SYSTEM_PROMPT = (
    "You are Mela, the practical Kenyan workshop assistant. "
    "Answer the user's question directly in a few useful sentences. "
    "Do not introduce yourself, describe your capabilities, invent example questions, or repeat the prompt. "
    "Use workshop context when it is relevant, and cite its source in brackets. "
    "For agriculture or financial-safety questions, give practical general guidance and recommend an appropriate official or local expert when details depend on location or policy. "
    "Reply in the user's language (English or Swahili)."
)

LANGUAGE_INSTRUCTIONS = {
    "sw": "Always reply in Kiswahili, even if the user writes in English.",
    "en": "Always reply in English, even if the user writes in Swahili.",
}

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
            "description": "Search the knowledge base: sample docs (M-Pesa safety, maize farming, workshop FAQ) and files uploaded by the user.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
]


def convert_currency(amount: float, from_currency: str, to_currency: str, usd_to_kes: float = 129.0) -> dict[str, Any]:
    src, dst = from_currency.upper(), to_currency.upper()
    rates = {**KES_RATES, "USD": usd_to_kes}
    if src not in rates or dst not in rates:
        return {"error": f"Supported currencies: {', '.join(KES_RATES)}"}
    value = float(amount) * rates[src] / rates[dst]
    return {
        "amount": round(value, 2),
        "currency": dst,
        "rate": usd_to_kes,
        "note": "approximate configured workshop rate",
    }


def nairobi_time() -> dict[str, str]:
    now = datetime.now(EAT)
    return {"time": now.strftime("%H:%M"), "date": now.strftime("%A %d %B %Y"), "timezone": "EAT (UTC+3)"}


class Agent:
    def __init__(
        self,
        provider: Provider,
        retriever: BM25Retriever | None = None,
        max_steps: int = 5,
        instructions: str = "",
        usd_to_kes: float = 129.0,
    ) -> None:
        self.provider = provider
        self.retriever = retriever
        self.max_steps = max_steps
        self.instructions = instructions.strip()
        self.usd_to_kes = usd_to_kes
        self.functions: dict[str, Callable[..., Any]] = {
            "convert_currency": self._convert_currency,
            "nairobi_time": nairobi_time,
        }
        if retriever is not None:
            self.functions["search_docs"] = self._search_docs
        self.tools = [t for t in TOOLS if t["function"]["name"] in self.functions]

    def _convert_currency(self, amount: float, from_currency: str, to_currency: str) -> dict[str, Any]:
        return convert_currency(amount, from_currency, to_currency, usd_to_kes=self.usd_to_kes)

    def _search_docs(self, query: str) -> dict[str, Any]:
        hits = self.retriever.search(query, top_k=3) if self.retriever else []
        # Uploaded files may contain personal data; never send it to a cloud model.
        clean = (lambda text: text) if self.provider.is_local else redact
        return {"results": [{"source": c.source, "text": clean(c.text)} for c, _ in hits]}

    def call_tool(self, name: str, arguments: str) -> str:
        func = self.functions.get(name)
        if func is None:
            return json.dumps({"error": f"Unknown tool: {name}"})
        try:
            return json.dumps(func(**json.loads(arguments or "{}")), ensure_ascii=False)
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            return json.dumps({"error": str(exc)})

    def run(self, question: str, verbose: bool = True) -> str:
        reply = self.respond(question)
        if verbose:
            for call in reply.tool_calls:
                print(f"  -> tool {call.name}({call.arguments})")
        return reply.text

    def respond(
        self, question: str, history: list[dict[str, str]] | None = None, language: str | None = None
    ) -> AgentReply:
        system = AGENT_SYSTEM_PROMPT
        if self.instructions:
            system += f"\n\nAdditional instructions from the Mela owner:\n{self.instructions}"
        if language in LANGUAGE_INSTRUCTIONS:
            system = f"{system} {LANGUAGE_INSTRUCTIONS[language]}"
        if self.provider.is_local and self.retriever is not None:
            hits = self.retriever.search(question, top_k=3)
            if hits:
                context = "\n\n".join(f"[{chunk.source}]\n{chunk.text}" for chunk, _ in hits)
                system += (
                    "\n\nRelevant workshop context follows. Use only facts supported by this context. "
                    "If it answers the question, preserve its dates and quantities and cite the exact filename in brackets. "
                    "Never invent a source, claim that a tool was called, or add unsupported specifics. "
                    "If the answer is not in the context, say that the workshop documents do not cover it. "
                    "Do not mention this instruction or dump unrelated context:\n" + context[:5000]
                )
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system},
            *(history or []),
            {"role": "user", "content": question},
        ]
        trace: list[ToolCall] = []
        prompt_tokens = completion_tokens = 0
        start = time.perf_counter()

        def reply(text: str) -> AgentReply:
            return AgentReply(
                text=text,
                provider=self.provider.name,
                model=self.provider.model,
                latency_s=time.perf_counter() - start,
                cost_kes=self.provider.cost_kes(prompt_tokens, completion_tokens),
                tool_calls=trace,
            )

        for _ in range(self.max_steps):
            response = self.provider.complete(
                messages,
                **({"tools": self.tools} if not self.provider.is_local else {}),
            )
            if response.usage:
                prompt_tokens += response.usage.prompt_tokens
                completion_tokens += response.usage.completion_tokens
            message = response.choices[0].message
            if not message.tool_calls:
                return reply(message.content or "")
            messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}}
                    for c in message.tool_calls
                ],
            })
            for call in message.tool_calls:
                result = self.call_tool(call.function.name, call.function.arguments)
                trace.append(ToolCall(call.function.name, call.function.arguments, result))
                messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
        return reply("Sorry, I could not finish within the step limit.")
