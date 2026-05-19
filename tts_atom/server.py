from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from tts_atom import __version__
from tts_atom.config import get_settings
from tts_atom.core.engine import get_engine
from tts_atom.errors import TTSAtomError, error_response
from tts_atom.schemas import (
    HealthResponse,
    ProvidersResponse,
    PrewarmRequest,
    SplitSynthesizeRequest,
    TTSRequest,
    VoicesResponse,
)


def create_app() -> FastAPI:
    settings = get_settings()
    settings.audio_root.mkdir(parents=True, exist_ok=True)
    settings.cache_root.mkdir(parents=True, exist_ok=True)

    app = FastAPI(title="tts-atom", version=__version__)
    engine = get_engine()

    @app.get("/healthz", response_model=HealthResponse)
    def healthz() -> HealthResponse:
        data = engine.health()
        return HealthResponse(**data)

    @app.get("/api/tts/providers", response_model=ProvidersResponse)
    def list_providers() -> ProvidersResponse:
        return ProvidersResponse(ok=True, providers=engine.list_providers())

    @app.get("/api/tts/voices", response_model=VoicesResponse)
    def list_voices(
        provider: str | None = Query(None),
        language: str | None = Query(None),
        role_id: str | None = Query(None),
    ) -> VoicesResponse:
        return VoicesResponse(
            ok=True, voices=engine.list_voices(provider=provider, language=language, role_id=role_id)
        )

    @app.post("/api/tts/synthesize")
    def synthesize(body: TTSRequest):
        resp = engine.synthesize(body)
        if not resp.ok and resp.error:
            exc = TTSAtomError(
                resp.error.code,
                resp.error.message,
                source=resp.error.source,
                recoverable=resp.error.recoverable,
                details=resp.error.details,
            )
            return JSONResponse(status_code=exc.http_status, content=error_response(exc, resp.timing))
        return resp

    @app.post("/api/tts/split-synthesize")
    def split_synthesize(body: SplitSynthesizeRequest):
        resp = engine.split_synthesize(body)
        if not resp.ok and resp.error:
            exc = TTSAtomError(
                resp.error.code,
                resp.error.message,
                source=resp.error.source,
                recoverable=resp.error.recoverable,
                details=resp.error.details,
            )
            return JSONResponse(status_code=exc.http_status, content=error_response(exc, resp.timing))
        return resp

    @app.post("/api/tts/prewarm")
    def prewarm(body: PrewarmRequest):
        return engine.prewarm(body)

    @app.get("/audio/cache/{full_path:path}")
    def serve_cache_file(full_path: str):
        target = settings.cache_root / full_path
        if not target.is_file():
            raise HTTPException(status_code=404, detail="not found")
        return FileResponse(target)

    app.mount("/audio", StaticFiles(directory=str(settings.audio_root)), name="audio_runs")
    return app


app = create_app()
