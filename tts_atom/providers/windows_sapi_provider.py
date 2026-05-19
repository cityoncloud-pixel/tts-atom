from __future__ import annotations

import platform
import tempfile
from pathlib import Path

from tts_atom.providers.audio_util import wav_duration_ms
from tts_atom.providers.base import TTSProvider, TTSProviderResult
from tts_atom.schemas import TTSRequest, VoiceInfo

DEFAULT_VOICES = [
    VoiceInfo(
        voice="zh-CN-XiaoxiaoNeural",
        provider="windows_sapi",
        language="zh",
        description="Windows SAPI 默认中文映射",
        recommended_roles=["rabbit_officer"],
    ),
]


class WindowsSapiProvider(TTSProvider):
    name = "windows_sapi"

    def is_available(self) -> bool:
        if platform.system() != "Windows":
            return False
        try:
            import win32com.client  # noqa: F401
            return True
        except ImportError:
            try:
                import pyttsx3  # noqa: F401
                return True
            except ImportError:
                return False

    def list_voices(self, language: str | None = None) -> list[VoiceInfo]:
        if not self.is_available():
            return []
        return DEFAULT_VOICES

    def synthesize(self, request: TTSRequest) -> TTSProviderResult:
        voice = request.voice or "default"
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            out_path = Path(tmp.name)
        try:
            self._synthesize_to_file(request.text, out_path)
            data = out_path.read_bytes()
        finally:
            if out_path.exists():
                out_path.unlink(missing_ok=True)
        return TTSProviderResult(
            audio_bytes=data,
            duration_ms=wav_duration_ms(data),
            provider=self.name,
            voice=voice,
        )

    def _synthesize_to_file(self, text: str, path: Path) -> None:
        try:
            import pyttsx3

            engine = pyttsx3.init()
            engine.save_to_file(text, str(path))
            engine.runAndWait()
            return
        except ImportError:
            pass
        raise RuntimeError("Windows SAPI backend not available (install pyttsx3)")
