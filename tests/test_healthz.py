from fastapi.testclient import TestClient

from tts_atom.server import create_app


def test_healthz():
    client = TestClient(create_app())
    r = client.get("/healthz")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["service"] == "tts-atom"


def test_synthesize_http():
    client = TestClient(create_app())
    r = client.post(
        "/api/tts/synthesize",
        json={"text": "HTTP 测试", "provider": "mock"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["audio_url"]


def test_split_synthesize():
    client = TestClient(create_app())
    text = "好的，我们先看第一题。5加3等于几呢？你可以先数5个，再数3个。"
    r = client.post(
        "/api/tts/split-synthesize",
        json={"text": text, "provider": "mock", "return_segments": True},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert len(data["segments"]) >= 2
