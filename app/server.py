"""Msaidizi web UI for the agent. Run with: python app/server.py"""
from dataclasses import asdict
from pathlib import Path
from typing import Literal

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from pycord.agent import Agent
from pycord.config import DOCS_DIR, Settings
from pycord.privacy import contains_pii
from pycord.providers import get_cloud_provider, get_local_provider
from pycord.rag import BM25Retriever, load_documents

STATIC_DIR = Path(__file__).parent / "static"

settings = Settings.from_env()
local = get_local_provider(settings)
cloud = get_cloud_provider(settings)
retriever = BM25Retriever(load_documents(DOCS_DIR))
agents = {"local": Agent(local, retriever), "cloud": Agent(cloud, retriever)}

app = FastAPI(title="Msaidizi")


class Turn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=8000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    history: list[Turn] = Field(default_factory=list, max_length=20)
    mode: Literal["auto", "local", "cloud"] = "auto"


def choose_target(mode: str, user_text: str) -> tuple[str, str]:
    if mode != "auto":
        return mode, f"{mode} model selected"
    if contains_pii(user_text):
        if not local.is_available():
            raise HTTPException(422, "Personal data detected and no local model is available - not sending it to the cloud.")
        return "local", "personal data detected - kept on this device"
    if not cloud.is_available():
        return "local", "cloud unreachable - working offline"
    return "cloud", "cloud model has the best tool support"


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/status")
def status() -> dict:
    return {
        "local": {"name": local.name, "model": local.model, "available": local.is_available()},
        "cloud": {"name": cloud.name, "model": cloud.model, "available": cloud.is_available()},
    }


@app.post("/api/chat")
def chat(req: ChatRequest) -> dict:
    history = [turn.model_dump() for turn in req.history]
    user_text = "\n".join([*(t["content"] for t in history if t["role"] == "user"), req.message])
    target, reason = choose_target(req.mode, user_text)
    try:
        reply = agents[target].respond(req.message, history=history)
    except Exception as exc:
        raise HTTPException(502, f"{type(exc).__name__}: {exc}") from exc
    return {
        "reply": reply.text,
        "tools": [asdict(call) for call in reply.tool_calls],
        "provider": reply.provider,
        "model": reply.model,
        "latency_s": round(reply.latency_s, 2),
        "cost_kes": round(reply.cost_kes, 4),
        "route_reason": reason,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
