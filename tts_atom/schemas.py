from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

ProviderName = Literal[
    "auto", "melotts", "mock", "kokoro", "edge", "windows_sapi", "doubao"
]
AudioFormat = Literal["wav", "mp3", "ogg", "pcm"]


class TimingInfo(BaseModel):
    queue_ms: int = 0
    split_ms: int = 0
    cache_lookup_ms: int = 0
    synthesis_ms: int = 0
    file_write_ms: int = 0
    total_ms: int = 0


class ErrorDetail(BaseModel):
    code: str
    message: str
    source: str = "tts-atom"
    recoverable: bool = False
    details: dict[str, Any] = Field(default_factory=dict)


class VoiceInfo(BaseModel):
    voice: str
    provider: str
    language: str = "zh"
    gender: str | None = None
    description: str | None = None
    recommended_roles: list[str] = Field(default_factory=list)


class ProviderInfo(BaseModel):
    name: str
    available: bool
    local: bool = True
    default: bool = False
    supports: list[str] = Field(default_factory=lambda: ["zh"])
    features: list[str] = Field(default_factory=list)


class TTSRequest(BaseModel):
    text: str
    role_id: str | None = None
    voice: str | None = None
    provider: ProviderName = "auto"
    language: str = "zh"
    emotion: str = "neutral"
    speed: float = 1.0
    pitch: float = 1.0
    volume: float = 1.0
    format: AudioFormat = "wav"
    sample_rate: int = 24000
    cache: bool = True
    stream: bool = False
    sentence_split: bool = False
    return_segments: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class SegmentResult(BaseModel):
    index: int
    text: str
    audio_url: str
    audio_path: str
    duration_ms: int
    cached: bool = False


class SynthesizeResponse(BaseModel):
    ok: bool = True
    provider: str | None = None
    voice: str | None = None
    role_id: str | None = None
    audio_url: str | None = None
    audio_path: str | None = None
    format: str = "wav"
    sample_rate: int = 24000
    duration_ms: int = 0
    cached: bool = False
    segments: list[SegmentResult] = Field(default_factory=list)
    timing: TimingInfo = Field(default_factory=TimingInfo)
    error: ErrorDetail | None = None


class SplitSynthesizeRequest(TTSRequest):
    return_segments: bool = True
    sentence_split: bool = True


class SplitSynthesizeResponse(BaseModel):
    ok: bool = True
    provider: str | None = None
    voice: str | None = None
    role_id: str | None = None
    segments: list[SegmentResult] = Field(default_factory=list)
    timing: TimingInfo = Field(default_factory=TimingInfo)
    error: ErrorDetail | None = None


class PrewarmRequest(BaseModel):
    role_id: str | None = None
    provider: ProviderName = "auto"
    voice: str | None = None
    language: str = "zh"
    phrases: list[str] = Field(default_factory=list)


class PrewarmItem(BaseModel):
    text: str
    audio_url: str | None = None
    cached: bool = False
    ok: bool = True
    error: str | None = None


class PrewarmResponse(BaseModel):
    ok: bool = True
    created: int = 0
    cached: int = 0
    failed: int = 0
    items: list[PrewarmItem] = Field(default_factory=list)
    timing: TimingInfo = Field(default_factory=TimingInfo)
    error: ErrorDetail | None = None


class HealthResponse(BaseModel):
    ok: bool = True
    service: str = "tts-atom"
    version: str = "0.1.0"
    default_provider: str = "melotts"
    providers: dict[str, bool] = Field(default_factory=dict)


class ProvidersResponse(BaseModel):
    ok: bool = True
    providers: list[ProviderInfo] = Field(default_factory=list)


class VoicesResponse(BaseModel):
    ok: bool = True
    voices: list[VoiceInfo] = Field(default_factory=list)


EMOTION_PRESETS: dict[str, dict[str, float]] = {
    "cheerful": {"speed": 1.08, "pitch": 1.05, "volume": 1.0},
    "gentle": {"speed": 0.95, "pitch": 0.98, "volume": 0.95},
    "serious": {"speed": 0.92, "pitch": 0.95, "volume": 1.0},
    "thinking": {"speed": 0.9, "pitch": 0.97, "volume": 0.95},
    "praise": {"speed": 1.12, "pitch": 1.08, "volume": 1.0},
    "warning": {"speed": 0.95, "pitch": 0.96, "volume": 1.0},
    "neutral": {"speed": 1.0, "pitch": 1.0, "volume": 1.0},
}


def apply_emotion(request: TTSRequest) -> TTSRequest:
    preset = EMOTION_PRESETS.get(request.emotion, EMOTION_PRESETS["neutral"])
    data = request.model_dump()
    if request.speed == 1.0:
        data["speed"] = preset["speed"]
    if request.pitch == 1.0:
        data["pitch"] = preset["pitch"]
    if request.volume == 1.0:
        data["volume"] = preset["volume"]
    return TTSRequest(**data)
