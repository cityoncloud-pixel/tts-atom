from __future__ import annotations

from tts_atom import __version__
from tts_atom.config import get_settings
from tts_atom.core import cache as cache_mod
from tts_atom.core.audio_store import audio_url_for_cache, save_audio
from tts_atom.core.router import ProviderRegistry, resolve_provider_chain
from tts_atom.core.splitter import split_sentences
from tts_atom.core.timing import TimingCollector
from tts_atom.errors import (
    TTS_EMPTY_TEXT,
    TTS_INTERNAL_ERROR,
    TTS_PROVIDER_FAILED,
    TTS_PROVIDER_NOT_FOUND,
    TTS_TEXT_TOO_LONG,
    TTS_UNSUPPORTED_FORMAT,
    TTSAtomError,
    make_error,
)
from tts_atom.providers.audio_util import wav_duration_ms
from tts_atom.roles.role_profiles import apply_role, get_role
from tts_atom.schemas import (
    ProviderInfo,
    PrewarmItem,
    PrewarmRequest,
    PrewarmResponse,
    SegmentResult,
    SplitSynthesizeRequest,
    SplitSynthesizeResponse,
    SynthesizeResponse,
    TTSRequest,
    VoiceInfo,
    apply_emotion,
)


class Engine:
    def __init__(self) -> None:
        self.registry = ProviderRegistry()
        self.settings = get_settings()

    def _validate_request(self, request: TTSRequest) -> None:
        if not request.text or not request.text.strip():
            raise make_error(TTS_EMPTY_TEXT, "Text must not be empty")
        if len(request.text) > self.settings.max_text_length:
            raise make_error(
                TTS_TEXT_TOO_LONG,
                f"Text exceeds max length {self.settings.max_text_length}",
            )
        if request.format not in ("wav", "mp3", "ogg", "pcm"):
            raise make_error(TTS_UNSUPPORTED_FORMAT, f"Unsupported format: {request.format}")

    def _prepare(self, request: TTSRequest) -> TTSRequest:
        req = apply_role(request)
        req = apply_emotion(req)
        if not req.voice:
            req = req.model_copy(update={"voice": "zh_female_01"})
        return req

    def _try_cache(self, req: TTSRequest, timing: TimingCollector) -> SynthesizeResponse | None:
        voice = req.voice or "zh_female_01"
        chain = resolve_provider_chain(req, self.registry)
        with timing.track("cache_lookup_ms"):
            for pname in chain:
                hit = cache_mod.cache_lookup(req, pname, voice)
                if hit:
                    data = hit.read_bytes()
                    return SynthesizeResponse(
                        ok=True,
                        provider=pname,
                        voice=voice,
                        role_id=req.role_id,
                        audio_url=audio_url_for_cache(hit),
                        audio_path=str(hit),
                        format=req.format,
                        sample_rate=req.sample_rate,
                        duration_ms=wav_duration_ms(data),
                        cached=True,
                    )
        return None

    def _synthesize_provider(
        self, req: TTSRequest, timing: TimingCollector, segment_index: int | None = None
    ) -> SynthesizeResponse:
        voice = req.voice or "zh_female_01"
        chain = resolve_provider_chain(req, self.registry)
        attempted: list[str] = []
        last_err: Exception | None = None

        with timing.track("synthesis_ms"):
            for pname in chain:
                provider = self.registry.get(pname)
                attempted.append(pname)
                if not provider or not provider.is_available():
                    continue
                try:
                    result = provider.synthesize(req)
                    with timing.track("file_write_ms"):
                        if req.cache and self.settings.enable_cache:
                            cache_mod.cache_store(req, result.provider, result.voice, result.audio_bytes)
                        path, url = save_audio(
                            result.audio_bytes,
                            suffix=f".{req.format}",
                            segment_index=segment_index,
                        )
                    return SynthesizeResponse(
                        ok=True,
                        provider=result.provider,
                        voice=result.voice,
                        role_id=req.role_id,
                        audio_url=url,
                        audio_path=str(path),
                        format=req.format,
                        sample_rate=req.sample_rate,
                        duration_ms=result.duration_ms,
                        cached=False,
                    )
                except Exception as exc:  # noqa: BLE001
                    last_err = exc
                    continue

        if not chain:
            raise make_error(TTS_PROVIDER_NOT_FOUND, "No provider in resolution chain")
        raise make_error(
            TTS_PROVIDER_FAILED,
            str(last_err) if last_err else "All providers failed",
            source=attempted[-1] if attempted else "tts-atom",
            recoverable=True,
            details={"attempted": attempted},
        )

    def synthesize(self, request: TTSRequest) -> SynthesizeResponse:
        timing = TimingCollector()
        try:
            self._validate_request(request)
            req = self._prepare(request)
            cached = self._try_cache(req, timing)
            if cached:
                cached.timing = timing.finalize()
                return cached
            resp = self._synthesize_provider(req, timing)
            resp.timing = timing.finalize()
            return resp
        except TTSAtomError as exc:
            return SynthesizeResponse(ok=False, timing=timing.finalize(), error=exc.to_error_detail())
        except Exception as exc:  # noqa: BLE001
            err = make_error(TTS_INTERNAL_ERROR, str(exc))
            return SynthesizeResponse(ok=False, timing=timing.finalize(), error=err.to_error_detail())

    def split_synthesize(self, request: SplitSynthesizeRequest) -> SplitSynthesizeResponse:
        timing = TimingCollector()
        try:
            self._validate_request(request)
            with timing.track("split_ms"):
                sentences = split_sentences(request.text) or [request.text]
            segments: list[SegmentResult] = []
            provider_name: str | None = None
            voice_name: str | None = None
            for idx, sent in enumerate(sentences):
                sub = request.model_copy(update={"text": sent})
                req = self._prepare(sub)
                cached = self._try_cache(req, timing)
                if cached and cached.audio_url and cached.audio_path:
                    resp = cached
                else:
                    resp = self._synthesize_provider(req, timing, segment_index=idx)
                provider_name = resp.provider
                voice_name = resp.voice
                segments.append(
                    SegmentResult(
                        index=idx,
                        text=sent,
                        audio_url=resp.audio_url or "",
                        audio_path=resp.audio_path or "",
                        duration_ms=resp.duration_ms,
                        cached=resp.cached,
                    )
                )
            return SplitSynthesizeResponse(
                ok=True,
                provider=provider_name,
                voice=voice_name,
                role_id=request.role_id,
                segments=segments,
                timing=timing.finalize(),
            )
        except TTSAtomError as exc:
            return SplitSynthesizeResponse(ok=False, timing=timing.finalize(), error=exc.to_error_detail())
        except Exception as exc:  # noqa: BLE001
            err = make_error(TTS_INTERNAL_ERROR, str(exc))
            return SplitSynthesizeResponse(ok=False, timing=timing.finalize(), error=err.to_error_detail())

    def prewarm(self, request: PrewarmRequest) -> PrewarmResponse:
        timing = TimingCollector()
        created = cached = failed = 0
        items: list[PrewarmItem] = []
        for phrase in request.phrases:
            sub = TTSRequest(
                text=phrase,
                role_id=request.role_id,
                voice=request.voice,
                provider=request.provider,
                language=request.language,
            )
            resp = self.synthesize(sub)
            if resp.ok:
                if resp.cached:
                    cached += 1
                else:
                    created += 1
                items.append(
                    PrewarmItem(text=phrase, audio_url=resp.audio_url, cached=resp.cached, ok=True)
                )
            else:
                failed += 1
                items.append(
                    PrewarmItem(
                        text=phrase,
                        ok=False,
                        error=resp.error.message if resp.error else "failed",
                    )
                )
        return PrewarmResponse(
            ok=failed == 0,
            created=created,
            cached=cached,
            failed=failed,
            items=items,
            timing=timing.finalize(),
        )

    def list_providers(self) -> list[ProviderInfo]:
        settings = get_settings()
        avail = self.registry.availability()
        infos: list[ProviderInfo] = []
        for name, provider in self.registry.all().items():
            infos.append(
                ProviderInfo(
                    name=name,
                    available=avail.get(name, False),
                    local=name not in ("edge", "doubao"),
                    default=name == settings.default_provider,
                    supports=["zh", "en"] if name in ("melotts", "mock") else ["zh"],
                    features=["speed", "cache", "speaker"] if avail.get(name) else [],
                )
            )
        return infos

    def list_voices(
        self, provider: str | None = None, language: str | None = None, role_id: str | None = None
    ) -> list[VoiceInfo]:
        voices: list[VoiceInfo] = []
        names = [provider] if provider else list(self.registry.all().keys())
        for pname in names:
            p = self.registry.get(pname or "")
            if not p or not p.is_available():
                continue
            voices.extend(p.list_voices(language))
        role = get_role(role_id)
        if role:
            matched = [v for v in voices if v.voice == role.voice]
            if matched:
                return matched
        return voices

    def health(self) -> dict:
        settings = get_settings()
        return {
            "ok": True,
            "service": "tts-atom",
            "version": __version__,
            "default_provider": settings.default_provider,
            "providers": self.registry.availability(),
        }


_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = Engine()
    return _engine
