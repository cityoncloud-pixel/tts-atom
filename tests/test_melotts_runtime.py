from unittest.mock import MagicMock, patch

import pytest

from tts_atom.providers import melotts_runtime
from tts_atom.providers.audio_util import silent_wav_bytes, wav_duration_ms
from tts_atom.providers.melotts_provider import MeloTTSProvider
from tts_atom.schemas import TTSRequest


def test_detect_backend_none():
    with patch.object(melotts_runtime, "_can_import_melo", return_value=False):
        with patch.object(melotts_runtime, "_find_melo_cli", return_value=None):
            assert melotts_runtime.detect_backend() == "none"


def test_detect_backend_python():
    with patch.object(melotts_runtime, "_can_import_melo", return_value=True):
        assert melotts_runtime.detect_backend() == "python_api"


def test_provider_uses_runtime():
    wav = silent_wav_bytes(50, 24000)
    with patch.object(melotts_runtime, "is_melotts_usable", return_value=True):
        with patch.object(
            melotts_runtime,
            "synthesize_melotts",
            return_value=(wav, wav_duration_ms(wav)),
        ) as synth:
            p = MeloTTSProvider()
            assert p.is_available()
            r = p.synthesize(TTSRequest(text="测试", voice="zh_female_01", provider="melotts"))
            assert r.provider == "melotts"
            synth.assert_called_once()


def test_provider_unavailable_raises():
    with patch.object(melotts_runtime, "is_melotts_usable", return_value=False):
        p = MeloTTSProvider()
        assert not p.is_available()
        with pytest.raises(RuntimeError, match="MeloTTS"):
            p.synthesize(TTSRequest(text="x", provider="melotts"))
