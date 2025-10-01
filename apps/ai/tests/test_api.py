import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import sys
import types
import importlib.util
import importlib.machinery


def load_main_module():
    """Load apps/ai/main.py by absolute path to avoid package path issues."""
    main_path = Path(__file__).resolve().parents[1] / "main.py"
    # Ensure apps/ai root is on sys.path so `import src...` inside main.py works
    ai_root = str(Path(__file__).resolve().parents[1])
    if ai_root not in sys.path:
        sys.path.insert(0, ai_root)
    # Provide lightweight stubs to avoid importing heavy deps during tests
    # Stub package 'src' and subpackages so `from src.agent.agent import generate` succeeds
    if 'src' not in sys.modules:
        sys.modules['src'] = types.ModuleType('src')
    if 'src.agent' not in sys.modules:
        pkg = types.ModuleType('src.agent')
        sys.modules['src.agent'] = pkg
        setattr(sys.modules['src'], 'agent', pkg)
    if 'src.agent.agent' not in sys.modules:
        mod = types.ModuleType('src.agent.agent')
        def _stub_generate(message: str):
            return ("stub thinking", "stub message")
        setattr(mod, 'generate', _stub_generate)
        sys.modules['src.agent.agent'] = mod
        setattr(sys.modules['src.agent'], 'agent', mod)
    spec = importlib.util.spec_from_file_location("ai_main", str(main_path))
    assert spec and spec.loader, "Cannot load main.py spec"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[arg-type]
    return module


def get_app():
    module = load_main_module()
    return module.app


def test_health_endpoint():
    app = get_app()
    client = TestClient(app)
    r = client.get("/ai/health/")
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == 201


def test_generate_simple(monkeypatch):
    # Patch the generate symbol inside main module (already imported there)
    ai_main = load_main_module()

    def fake_generate(message: str):
        return ("thinking about: " + message, "echo: " + message)

    monkeypatch.setattr(ai_main, "generate", fake_generate)

    app = ai_main.app
    client = TestClient(app)
    r = client.post("/ai/generate/", json={"message": "hello"})
    assert r.status_code == 200 or r.status_code == 201
    data = r.json()
    assert "message" in data and "thinking" in data
    assert data["message"].startswith("echo: ")
    assert data["thinking"].startswith("thinking about:")


def test_generate_tool_like_trace(monkeypatch):
    # Simulate a generate that indicates RAG was used first and then web
    ai_main = load_main_module()

    def fake_generate(_msg: str):
        think = "Used search_rag -> results insufficient -> used web_search"
        msg = "1. Some row (fonte: payroll.csv)\nFinal: resposta baseada nas fontes"
        return (think, msg)

    monkeypatch.setattr(ai_main, "generate", fake_generate)

    app = ai_main.app
    client = TestClient(app)
    r = client.post("/ai/generate/", json={"message": "Qual o bônus?"})
    assert r.status_code == 200 or r.status_code == 201
    data = r.json()
    assert "message" in data and "thinking" in data
    assert "search_rag" in data["thinking"]
    assert "web_search" in data["thinking"]
    assert "payroll.csv" in data["message"]

def test_invalid_body_returns_422():
    app = get_app()
    client = TestClient(app)
    r = client.post("/ai/generate/", json={})
    # FastAPI with Pydantic should return 422 for missing required field
    assert r.status_code == 422


def test_generate_receives_message(monkeypatch):
    ai_main = load_main_module()
    received = {}

    def fake_generate(msg: str):
        received['msg'] = msg
        return ("t", "m")

    monkeypatch.setattr(ai_main, "generate", fake_generate)
    app = ai_main.app
    client = TestClient(app)
    r = client.post("/ai/generate/", json={"message": "ping"})
    assert r.status_code in (200, 201)
    assert received.get('msg') == 'ping'


def test_generate_exception_produces_500(monkeypatch):
    ai_main = load_main_module()

    def fake_generate(_msg: str):
        raise RuntimeError("boom")

    monkeypatch.setattr(ai_main, "generate", fake_generate)
    app = ai_main.app
    client = TestClient(app)
    r = client.post("/ai/generate/", json={"message": "x"})
    assert r.status_code == 500


