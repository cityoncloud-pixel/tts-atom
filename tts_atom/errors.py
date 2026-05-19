from __future__ import annotations

from typing import Any

from tts_atom.schemas import ErrorDetail, TimingInfo

TTS_EMPTY_TEXT = "TTS_EMPTY_TEXT"
TTS_TEXT_TOO_LONG = "TTS_TEXT_TOO_LONG"
TTS_PROVIDER_NOT_FOUND = "TTS_PROVIDER_NOT_FOUND"
TTS_PROVIDER_UNAVAILABLE = "TTS_PROVIDER_UNAVAILABLE"
TTS_PROVIDER_FAILED = "TTS_PROVIDER_FAILED"
TTS_VOICE_NOT_FOUND = "TTS_VOICE_NOT_FOUND"
TTS_UNSUPPORTED_FORMAT = "TTS_UNSUPPORTED_FORMAT"
TTS_AUDIO_WRITE_FAILED = "TTS_AUDIO_WRITE_FAILED"
TTS_CACHE_ERROR = "TTS_CACHE_ERROR"
TTS_INTERNAL_ERROR = "TTS_INTERNAL_ERROR"

HTTP_STATUS: dict[str, int] = {
    TTS_EMPTY_TEXT: 400,
    TTS_TEXT_TOO_LONG: 400,
    TTS_PROVIDER_NOT_FOUND: 400,
    TTS_PROVIDER_UNAVAILABLE: 503,
    TTS_PROVIDER_FAILED: 502,
    TTS_VOICE_NOT_FOUND: 400,
    TTS_UNSUPPORTED_FORMAT: 400,
    TTS_AUDIO_WRITE_FAILED: 500,
    TTS_CACHE_ERROR: 500,
    TTS_INTERNAL_ERROR: 500,
}


class TTSAtomError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        source: str = "tts-atom",
        recoverable: bool = False,
        details: dict[str, Any] | None = None,
        http_status: int | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.source = source
        self.recoverable = recoverable
        self.details = details or {}
        self.http_status = http_status or HTTP_STATUS.get(code, 500)

    def to_error_detail(self) -> ErrorDetail:
        return ErrorDetail(
            code=self.code,
            message=self.message,
            source=self.source,
            recoverable=self.recoverable,
            details=self.details,
        )


def make_error(
    code: str,
    message: str,
    *,
    source: str = "tts-atom",
    recoverable: bool = False,
    details: dict[str, Any] | None = None,
) -> TTSAtomError:
    return TTSAtomError(code, message, source=source, recoverable=recoverable, details=details)


def error_response(exc: TTSAtomError, timing: TimingInfo | None = None) -> dict[str, Any]:
    return {
        "ok": False,
        "error": exc.to_error_detail().model_dump(),
        "timing": (timing or TimingInfo()).model_dump(),
    }
