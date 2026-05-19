import os

import pytest

os.environ["TTS_ATOM_FORCE_MOCK"] = "true"
os.environ["TTS_ATOM_ENABLE_CACHE"] = "true"


@pytest.fixture(autouse=True)
def _reset_engine(monkeypatch):
    import tts_atom.core.engine as eng

    eng._engine = None
    get_settings = __import__("tts_atom.config", fromlist=["get_settings"]).get_settings
    get_settings.cache_clear()
    yield
    eng._engine = None
