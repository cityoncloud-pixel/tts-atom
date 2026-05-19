from tts_atom.core.cache import cache_key, cache_store, cache_lookup
from tts_atom.schemas import TTSRequest


def test_cache_key_stable():
    r1 = TTSRequest(text="你好", provider="mock", voice="zh_female_01")
    r2 = TTSRequest(text="你好", provider="mock", voice="zh_female_01")
    assert cache_key(r1, "mock", "zh_female_01") == cache_key(r2, "mock", "zh_female_01")


def test_cache_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("TTS_ATOM_CACHE_ROOT", str(tmp_path))
    from tts_atom.config import get_settings

    get_settings.cache_clear()
    import tts_atom.core.engine as eng

    eng._engine = None
    req = TTSRequest(text="cache test", provider="mock", voice="zh_female_01", cache=True)
    assert cache_lookup(req, "mock", "zh_female_01") is None
    cache_store(req, "mock", "zh_female_01", b"RIFF")
    assert cache_lookup(req, "mock", "zh_female_01") is not None
