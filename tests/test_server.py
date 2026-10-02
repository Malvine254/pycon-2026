import importlib.util
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from pycord.agent import AgentReply, ToolCall

SERVER_PATH = Path(__file__).resolve().parents[1] / "app" / "server.py"


class FakeAgent:
    def __init__(self, name):
        self.name = name
        self.calls = []
        self.languages = []

    def respond(self, question, history=None, language=None):
        self.calls.append((question, history))
        self.languages.append(language)
        return AgentReply(
            text=f"answer from {self.name}",
            provider=self.name,
            model=f"{self.name}-model",
            latency_s=0.1,
            tool_calls=[ToolCall("nairobi_time", "{}", '{"time": "10:00"}')],
        )


@pytest.fixture
def server(monkeypatch, tmp_path):
    from pycord import storage

    # Keep test uploads and chats out of the real .mela folder.
    monkeypatch.setattr(storage, "RUNTIME_DIR", tmp_path)
    monkeypatch.setattr(storage, "UPLOADS_DIR", tmp_path / "uploads")
    monkeypatch.setattr(storage, "HISTORY_FILE", tmp_path / "history.json")
    monkeypatch.setattr(storage, "INSTRUCTIONS_FILE", tmp_path / "instructions.txt")

    spec = importlib.util.spec_from_file_location("pycord_server", SERVER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.agents = {"local": FakeAgent("local"), "cloud": FakeAgent("cloud")}
    monkeypatch.setattr(module.local, "is_available", lambda: True)
    monkeypatch.setattr(module.cloud, "is_available", lambda: True)
    return module


def test_index_served(server):
    response = TestClient(server.app).get("/")
    assert response.status_code == 200
    assert "Mela" in response.text


def test_auto_uses_cloud_and_returns_tools(server):
    data = TestClient(server.app).post("/api/chat", json={"message": "What time is it?"}).json()
    assert data["provider"] == "cloud"
    assert data["tools"][0]["name"] == "nairobi_time"


def test_auto_keeps_pii_local(server):
    data = TestClient(server.app).post("/api/chat", json={"message": "Call 0712345678"}).json()
    assert data["provider"] == "local"
    assert server.agents["cloud"].calls == []


def test_pii_without_local_is_refused(server, monkeypatch):
    monkeypatch.setattr(server.local, "is_available", lambda: False)
    response = TestClient(server.app).post("/api/chat", json={"message": "Call 0712345678"})
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "pii_no_local"
    assert server.agents["cloud"].calls == []


def test_works_without_local_model(server, monkeypatch):
    monkeypatch.setattr(server.local, "is_available", lambda: False)
    client = TestClient(server.app)
    assert client.post("/api/chat", json={"message": "Habari"}).json()["provider"] == "cloud"
    response = client.post("/api/chat", json={"message": "Habari", "mode": "local"})
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "local_unavailable"
    assert server.agents["local"].calls == []


def test_no_model_available(server, monkeypatch):
    monkeypatch.setattr(server.local, "is_available", lambda: False)
    monkeypatch.setattr(server.cloud, "is_available", lambda: False)
    response = TestClient(server.app).post("/api/chat", json={"message": "Habari"})
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "no_model"


def test_language_and_route_code(server):
    client = TestClient(server.app)
    data = client.post("/api/chat", json={"message": "Habari", "language": "sw"}).json()
    assert data["route_code"] == "cloud_tools"
    assert server.agents["cloud"].languages == ["sw"]
    assert client.post("/api/chat", json={"message": "hi", "language": "fr"}).status_code == 422


def test_rejects_invalid_input(server):
    client = TestClient(server.app)
    assert client.post("/api/chat", json={"message": ""}).status_code == 422
    assert client.post("/api/chat", json={"message": "hi", "mode": "other"}).status_code == 422
    assert client.post("/api/chat", json={"message": "x" * 4001}).status_code == 422


def test_static_assets_served(server):
    client = TestClient(server.app)
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/static/i18n.js").status_code == 200
    assert client.get("/static/styles.css").status_code == 200


def test_upload_search_and_delete(server):
    client = TestClient(server.app)
    files = {"file": ("../notes.md", b"Pycord hackathon prize is a Raspberry Pi. Call 0712345678.", "text/markdown")}
    doc = client.post("/api/documents", files=files).json()
    assert doc["name"] == "notes.md"
    assert doc["pii"] is True
    assert any(d["name"] == "notes.md" for d in client.get("/api/documents").json())
    assert server.retriever.search("hackathon prize")[0][0].source == "upload/notes.md"

    assert client.delete(f"/api/documents/{doc['id']}").status_code == 200
    assert server.retriever.search("hackathon prize") == []
    assert client.delete(f"/api/documents/{doc['id']}").status_code == 404


def test_reupload_replaces_document(server):
    client = TestClient(server.app)
    client.post("/api/documents", files={"file": ("a.txt", b"first version", "text/plain")})
    client.post("/api/documents", files={"file": ("a.txt", b"second version", "text/plain")})
    uploads = [d for d in client.get("/api/documents").json() if not d["builtin"]]
    assert len(uploads) == 1
    texts = [c.text for c in server.retriever.chunks if c.source == "upload/a.txt"]
    assert texts == ["second version"]


def test_upload_rejects_bad_files(server):
    client = TestClient(server.app)
    assert client.post("/api/documents", files={"file": ("x.exe", b"MZ", "application/octet-stream")}).json()["detail"]["code"] == "unsupported_type"
    big = b"a" * (5 * 1024 * 1024 + 1)
    assert client.post("/api/documents", files={"file": ("big.txt", big, "text/plain")}).status_code == 400


def test_attached_file_content_is_sent_to_agent(server):
    client = TestClient(server.app)
    cv = b"Wanjiku Kamau. Python developer at Safaricom. Phone 0712345678."
    client.post("/api/documents", files={"file": ("Wanjiku_CV.txt", cv, "text/plain")})
    client.post("/api/chat", json={"message": "Summarise my CV", "attachments": ["Wanjiku_CV.txt"]})
    question, _ = server.agents["cloud"].calls[0]
    assert "Python developer at Safaricom" in question
    assert "0712345678" not in question  # redacted for the cloud model
    assert "[PHONE_KE]" in question


def test_attached_file_unredacted_for_local_model(server):
    client = TestClient(server.app)
    client.post("/api/documents", files={"file": ("cv.txt", b"Call me on 0712345678", "text/plain")})
    client.post("/api/chat", json={"message": "Summarise", "attachments": ["cv.txt"], "mode": "local"})
    question, _ = server.agents["local"].calls[0]
    assert "0712345678" in question


def test_unknown_attachment_is_ignored(server):
    TestClient(server.app).post("/api/chat", json={"message": "Summarise", "attachments": ["missing.md"]})
    question, _ = server.agents["cloud"].calls[0]
    assert question == "Summarise"


def test_search_matches_file_names(server):
    client = TestClient(server.app)
    client.post("/api/documents", files={"file": ("Malvine_Owuor_CV.txt", b"Experienced Azure engineer.", "text/plain")})
    assert server.retriever.search("cv")[0][0].source == "upload/Malvine_Owuor_CV.txt"
