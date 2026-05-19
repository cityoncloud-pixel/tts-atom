from __future__ import annotations

from pathlib import Path

from tts_atom.config import get_settings
from tts_atom.providers.audio_util import silent_wav_bytes, wav_duration_ms
from tts_atom.providers.base import TTSProvider, TTSProviderResult
from tts_atom.schemas import TTSRequest, VoiceInfo

DEFAULT_VOICES = [
    VoiceInfo(
        voice="zh_female_01",
        provider="melotts",
        language="zh",
        gender="female",
        description="中文女声（MeloTTS 默认映射）",
        recommended_roles=["rabbit_officer", "assistant", "narrator"],
    ),
]


class MeloTTSProvider(TTSProvider):
    name = "melotts"

    def _models_path(self) -> Path:
        return get_settings().models_root

    def is_available(self) -> bool:
        root = self._models_path()
        if not root.exists():
            return False
        # Consider available if models dir has any content or marker file
        marker = root / ".melotts_ready"
        if marker.exists():
            return True
        return any(root.iterdir()) if root.is_dir() else False

    def list_voices(self, language: str | None = None) -> list[VoiceInfo]:
        if not self.is_available():
            return []
        if language and language not in ("zh", "mixed_zh_en"):
            return [v for v in DEFAULT_VOICES if v.language == language]
        return DEFAULT_VOICES

    def synthesize(self, request: TTSRequest) -> TTSProviderResult:
        voice = request.voice or "zh_female_01"
        # Real MeloTTS integration: install melotts and load model from models_root.
        # MVP: if models present, still use placeholder wav until melotts package wired.
        try:
            import melotts  # noqa: F401 — optional dependency
            # Future: call melotts synthesis here
        except ImportError:
            pass

        if not self.is_available():
            raise RuntimeError("MeloTTS models not configured under TTS_ATOM_MODELS_ROOT")

        data = silent_wav_bytes(max(100, int(80 * len(request.text))), request.sample_rate)
        return TTSProviderResult(
            audio_bytes=data,
            duration_ms=wav_duration_ms(data),
            provider=self.name,
            voice=voice,
        )
