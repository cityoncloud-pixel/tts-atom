from __future__ import annotations

import logging

from tts_atom.providers import melotts_runtime
from tts_atom.providers.base import TTSProvider, TTSProviderResult
from tts_atom.schemas import TTSRequest, VoiceInfo

logger = logging.getLogger(__name__)


class MeloTTSProvider(TTSProvider):
    name = "melotts"

    def is_available(self) -> bool:
        return melotts_runtime.is_melotts_usable()

    def list_voices(self, language: str | None = None) -> list[VoiceInfo]:
        if not self.is_available():
            return []
        voices: list[VoiceInfo] = []
        for voice_id, melo_lang, desc in melotts_runtime.list_melo_voices(language):
            voices.append(
                VoiceInfo(
                    voice=voice_id,
                    provider=self.name,
                    language=language or ("zh" if melo_lang == "ZH" else "en"),
                    description=desc,
                    recommended_roles=["rabbit_officer", "assistant", "narrator"],
                )
            )
        return voices

    def synthesize(self, request: TTSRequest) -> TTSProviderResult:
        if not self.is_available():
            raise RuntimeError(
                "MeloTTS is not installed. Run: pip install -e '.[melotts]' "
                "or scripts/install_melotts.ps1"
            )
        voice = request.voice or "zh_female_01"
        speed = max(0.5, min(float(request.speed), 2.0))
        try:
            audio_bytes, duration_ms = melotts_runtime.synthesize_melotts(
                request.text,
                voice=voice,
                language=request.language,
                speed=speed,
                sample_rate=request.sample_rate,
            )
        except Exception as exc:
            logger.exception("MeloTTS synthesis failed")
            raise RuntimeError(f"MeloTTS synthesis failed: {exc}") from exc

        return TTSProviderResult(
            audio_bytes=audio_bytes,
            duration_ms=duration_ms,
            provider=self.name,
            voice=voice,
        )
