from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from tts_atom.schemas import TTSRequest, VoiceInfo


@dataclass
class TTSProviderResult:
    audio_bytes: bytes
    duration_ms: int
    provider: str
    voice: str


class TTSProvider(ABC):
    name: str

    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    def list_voices(self, language: str | None = None) -> list[VoiceInfo]: ...

    @abstractmethod
    def synthesize(self, request: TTSRequest) -> TTSProviderResult: ...
