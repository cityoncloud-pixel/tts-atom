from __future__ import annotations

from tts_atom.providers.audio_util import silent_wav_bytes, wav_duration_ms
from tts_atom.providers.base import TTSProvider, TTSProviderResult
from tts_atom.schemas import TTSRequest, VoiceInfo

DEFAULT_VOICES = [
    VoiceInfo(
        voice="zh_female_01",
        provider="mock",
        language="zh",
        gender="female",
        description="Mock 中文女声（测试用）",
        recommended_roles=["rabbit_officer", "assistant", "narrator"],
    ),
]


class MockProvider(TTSProvider):
    name = "mock"

    def is_available(self) -> bool:
        return True

    def list_voices(self, language: str | None = None) -> list[VoiceInfo]:
        if language and language != "zh":
            return []
        return DEFAULT_VOICES

    def synthesize(self, request: TTSRequest) -> TTSProviderResult:
        voice = request.voice or "zh_female_01"
        data = silent_wav_bytes(100, request.sample_rate)
        return TTSProviderResult(
            audio_bytes=data,
            duration_ms=wav_duration_ms(data),
            provider=self.name,
            voice=voice,
        )
