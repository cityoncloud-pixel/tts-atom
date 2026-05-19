from __future__ import annotations

from tts_atom.providers.base import TTSProvider, TTSProviderResult
from tts_atom.schemas import TTSRequest, VoiceInfo


class StubProvider(TTSProvider):
    """Placeholder for providers not yet implemented."""

    def __init__(self, name: str) -> None:
        self.name = name

    def is_available(self) -> bool:
        return False

    def list_voices(self, language: str | None = None) -> list[VoiceInfo]:
        return []

    def synthesize(self, request: TTSRequest) -> TTSProviderResult:
        raise RuntimeError(f"Provider {self.name} is not implemented")
