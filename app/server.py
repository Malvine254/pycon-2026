"""Msaidizi web app for the agent. Run with: python app/server.py"""
import threading
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Annotated, Literal
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from pycord.agent import Agent
from pycord.config import DOCS_DIR, Settings
from pycord.documents import MAX_UPLOAD_BYTES, DocumentError, extract_text, safe_name
from pycord.privacy import contains_pii
from pycord.providers import get_cloud_provider, get_local_provider
from pycord.rag import BM25Retriever, chunk_text, load_documents

STATIC_DIR = Path(__file__).parent / "static"
MAX_UPLOADS = 20

settings = Settings.from_env()
local = get_local_provider(settings)
cloud = get_cloud_provider(settings)
retriever = BM25Retriever(load_documents(DOCS_DIR))
builtin_docs = Counter(chunk.source for chunk in retriever.chunks)
builtin_pii = {chunk.source for chunk in retriever.chunks if contains_pii(chunk.text)}
uploads: dict[str, dict] = {}
uploads_lock = threading.Lock()
agents = {"local": Agent(local, retriever), "cloud": Agent(cloud, retriever)}

app = FastAPI(title="Msaidizi")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class Turn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=8000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    history: list[Turn] = Field(default_factory=list, max_length=20)
    mode: Literal["auto", "local", "cloud"] = "auto"
    attachments: list[Annotated[str, Field(max_length=120)]] = Field(default_factory=list, max_length=10)


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


@app.get("/api/documents")
def list_documents() -> list[dict]:
    builtin = [
        {"id": None, "name": name, "chunks": count, "pii": name in builtin_pii, "builtin": True}
        for name, count in sorted(builtin_docs.items())
    ]
    with uploads_lock:
        return builtin + list(uploads.values())


@app.post("/api/documents")
def upload_document(file: UploadFile) -> dict:
    name = safe_name(file.filename or "")
    data = file.file.read(MAX_UPLOAD_BYTES + 1)
    try:
        text = extract_text(name, data)
    except DocumentError as exc:
        raise HTTPException(400, str(exc)) from exc

    source = f"upload/{name}"
    chunks = chunk_text(source, text)
    with uploads_lock:
        replaced = [doc_id for doc_id, doc in uploads.items() if doc["name"] == name]
        if not replaced and len(uploads) >= MAX_UPLOADS:
            raise HTTPException(400, f"Limit of {MAX_UPLOADS} uploaded documents reached. Remove one first.")
        for doc_id in replaced:
            del uploads[doc_id]
        retriever.remove_source(source)
        retriever.add(chunks)
        doc = {
            "id": uuid4().hex,
            "name": name,
            "source": source,
            "chunks": len(chunks),
            "pii": contains_pii(text),
            "builtin": False,
        }
        uploads[doc["id"]] = doc
    return doc


@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: str) -> dict:
    with uploads_lock:
        doc = uploads.pop(doc_id, None)
        if doc is None:
            raise HTTPException(404, "Document not found.")
        retriever.remove_source(doc["source"])
    return {"deleted": doc_id}


@app.post("/api/chat")
def chat(req: ChatRequest) -> dict:
    history = [turn.model_dump() for turn in req.history]
    user_text = "\n".join([*(t["content"] for t in history if t["role"] == "user"), req.message])
    target, reason = choose_target(req.mode, user_text)
    message = req.message
    if req.attachments:
        message += f"\n\n(Attached files: {', '.join(req.attachments)} - use search_docs to read them.)"
    try:
        reply = agents[target].respond(message, history=history)
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
