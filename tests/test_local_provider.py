from dataclasses import replace

from pycord.config import Settings
from pycord.providers import local as local_module
from pycord.providers.local import FoundryLocalProvider


def make(endpoint=""):
    return FoundryLocalProvider(replace(Settings.from_env(), local_endpoint=endpoint))


def test_local_endpoint_override_wins(monkeypatch):
    monkeypatch.setattr(local_module.subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(AssertionError("not called")))
    assert make("http://127.0.0.1:5273/v1/").endpoint() == "http://127.0.0.1:5273"


def test_endpoint_detected_from_server_status(monkeypatch):
    status = "Status    Ready\nWeb URLs  http://127.0.0.1:61234/\n"
    monkeypatch.setattr(local_module.shutil, "which", lambda name: "foundry")
    monkeypatch.setattr(local_module.subprocess, "run", lambda *a, **k: type("R", (), {"stdout": status})())
    assert make().endpoint() == "http://127.0.0.1:61234"


def test_no_foundry_means_no_endpoint(monkeypatch):
    monkeypatch.setattr(local_module.shutil, "which", lambda name: None)
    provider = make()
    assert provider.endpoint() is None
    assert provider.is_available() is False
