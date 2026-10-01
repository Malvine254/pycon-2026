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

    def respond(self, question, history=None):
        self.calls.append((question, history))
        return AgentReply(
            text=f"answer from {self.name}",
            provider=self.name,
            model=f"{self.name}-model",
            latency_s=0.1,
            tool_calls=[ToolCall("nairobi_time", "{}", '{"time": "10:00"}')],
        )


@pytest.fixture
def server(monkeypatch):
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
    assert "Msaidizi" in response.text


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
    assert server.agents["cloud"].calls == []


def test_rejects_invalid_input(server):
    client = TestClient(server.app)
    assert client.post("/api/chat", json={"message": ""}).status_code == 422
    assert client.post("/api/chat", json={"message": "hi", "mode": "other"}).status_code == 422
    assert client.post("/api/chat", json={"message": "x" * 4001}).status_code == 422
