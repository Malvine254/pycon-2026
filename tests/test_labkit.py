import pytest

from pycord import labkit


class Fake:
    def __init__(self, name, available):
        self.name = name
        self.available = available

    def is_available(self):
        return self.available


def patch(monkeypatch, local_ok, cloud_ok):
    monkeypatch.setattr(labkit, "get_local_provider", lambda s: Fake("local", local_ok))
    monkeypatch.setattr(labkit, "get_cloud_provider", lambda s: Fake("cloud", cloud_ok))


def test_prefers_local(monkeypatch):
    patch(monkeypatch, True, True)
    assert labkit.local_or_cloud(object()).name == "local"


def test_falls_back_to_cloud_with_hint(monkeypatch, capsys):
    patch(monkeypatch, False, True)
    assert labkit.local_or_cloud(object()).name == "cloud"
    assert "foundry model load phi-3.5-mini" in capsys.readouterr().out


def test_no_model_gives_clear_error(monkeypatch):
    patch(monkeypatch, False, False)
    with pytest.raises(RuntimeError, match="labs/00-setup.md"):
        labkit.local_or_cloud(object())
