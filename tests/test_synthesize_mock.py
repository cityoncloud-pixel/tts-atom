from tts_atom.core.engine import get_engine
from tts_atom.schemas import TTSRequest


def test_synthesize_mock():
    engine = get_engine()
    resp = engine.synthesize(TTSRequest(text="你好，小警员", provider="mock"))
    assert resp.ok is True
    assert resp.provider == "mock"
    assert resp.audio_path
    assert resp.timing.total_ms >= 0


def test_synthesize_cache_hit():
    engine = get_engine()
    req = TTSRequest(text="缓存测试", provider="mock", voice="zh_female_01")
    r1 = engine.synthesize(req)
    r2 = engine.synthesize(req)
    assert r1.ok and r2.ok
    assert r2.cached is True
