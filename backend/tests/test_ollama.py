"""Ollama adapter error handling tests (no real Ollama needed)."""

from app.services.ollama_adapter import OllamaAdapter, OllamaError


class _FakeResponse:
    def __init__(self, status_code, text, json_data=None):
        self.status_code = status_code
        self.text = text
        self._json = json_data or {}

    def json(self):
        import json

        return json.loads(self.text)


class _FakeClient:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def get(self, url, timeout=None):
        self.calls.append(("GET", url))
        return self.responses.get(url, _FakeResponse(200, "{}"))

    def post(self, url, json=None, timeout=None):
        self.calls.append(("POST", url))
        return self.responses.get(url, _FakeResponse(200, "{}"))

    def close(self):
        pass


def test_status_unreachable():
    adapter = OllamaAdapter()

    def boom(*a, **k):
        raise OSError("refused")

    adapter._client.get = boom
    st = adapter.status()
    adapter.close()
    assert st["reachable"] is False
    assert st["model_available"] is False
    assert st["mode"] == "unavailable"
    assert st["error"] is not None


def test_generate_empty_response_error():
    adapter = OllamaAdapter()
    adapter._client = _FakeClient({
        "http://127.0.0.1:11434/api/version": _FakeResponse(200, '{"version":"0.1"}'),
        "http://127.0.0.1:11434/api/tags": _FakeResponse(200, '{"models":[{"name":"codellama:7b-instruct"}]}'),
        "http://127.0.0.1:11434/api/chat": _FakeResponse(200, ""),
    })

    from pydantic import BaseModel

    class Out(BaseModel):
        summary: str

    try:
        adapter.generate_json("sys", "user", Out)
        raise AssertionError("should raise OllamaError")
    except OllamaError as exc:
        assert exc.code == "empty_response"
    adapter.close()


def test_generate_malformed_json_error():
    adapter = OllamaAdapter()
    adapter._client = _FakeClient({
        "http://127.0.0.1:11434/api/version": _FakeResponse(200, '{"version":"0.1"}'),
        "http://127.0.0.1:11434/api/tags": _FakeResponse(200, '{"models":[{"name":"codellama:7b-instruct"}]}'),
        "http://127.0.0.1:11434/api/chat": _FakeResponse(200, "{not json"),
    })

    from pydantic import BaseModel

    class Out(BaseModel):
        summary: str

    try:
        adapter.generate_json("sys", "user", Out)
        raise AssertionError("should raise")
    except OllamaError as exc:
        assert exc.code == "malformed_json"
    adapter.close()
