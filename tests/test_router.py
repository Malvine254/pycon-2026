import pytest

from pycord.providers.base import ChatResult, Provider
from pycord.router import HybridRouter


class FakeProvider(Provider):
    def __init__(self, name, is_local, available=True, fail=False):
        super().__init__(model=f"{name}-model")
        self.name = name
        self.is_local = is_local
        self.available = available
        self.fail = fail
        self.calls = 0

    def _build_client(self):
        raise AssertionError("not used in tests")

    def is_available(self):
        return self.available

    def chat(self, messages, **kwargs):
        self.calls += 1
        if self.fail:
            raise RuntimeError("boom")
        return ChatResult(text="ok", provider=self.name, model=self.model, latency_s=0.0)


def make(local_kw=None, cloud_kw=None):
    local = FakeProvider("local", True, **(local_kw or {}))
    cloud = FakeProvider("cloud", False, **(cloud_kw or {}))
    return HybridRouter(local, cloud), local, cloud


def test_simple_goes_local():
    router, _, _ = make()
    assert router.ask("Habari?").provider == "local"


def test_complex_goes_cloud():
    router, _, _ = make()
    assert router.ask("Compare Django and FastAPI step by step").provider == "cloud"


def test_pii_stays_local_even_if_complex():
    router, _, cloud = make()
    result = router.ask("Compare plans for 0712345678 step by step")
    assert result.provider == "local"
    assert cloud.calls == 0


def test_pii_in_history_stays_local():
    router, _, _ = make()
    messages = [
        {"role": "user", "content": "My number is 0712345678"},
        {"role": "assistant", "content": "Noted."},
        {"role": "user", "content": "Compare two phone plans step by step"},
    ]
    assert router.chat(messages).provider == "local"


def test_offline_uses_local():
    router, _, _ = make(cloud_kw={"available": False})
    assert router.ask("Compare A and B step by step").provider == "local"


def test_no_local_uses_cloud():
    router, _, _ = make(local_kw={"available": False})
    assert router.ask("Habari?").provider == "cloud"


def test_falls_back_when_local_fails():
    router, _, _ = make(local_kw={"fail": True})
    result = router.ask("Habari?")
    assert result.provider == "cloud"
    assert "fell back" in result.route_reason


def test_pii_never_falls_back_to_cloud():
    router, _, cloud = make(local_kw={"fail": True})
    with pytest.raises(RuntimeError):
        router.ask("My number is 0712345678")
    assert cloud.calls == 0


def test_pii_without_local_runtime_is_refused():
    router, _, cloud = make(local_kw={"available": False})
    with pytest.raises(RuntimeError, match="refusing"):
        router.ask("My number is 0712345678")
    assert cloud.calls == 0


def test_nothing_available_raises():
    router, _, _ = make(local_kw={"available": False}, cloud_kw={"available": False})
    with pytest.raises(RuntimeError, match="No model available"):
        router.ask("Habari?")
