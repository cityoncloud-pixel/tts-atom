from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from tts_atom.config import get_settings
from tts_atom.schemas import TTSRequest


def normalize_text(text: str) -> str:
    return " ".join(text.strip().split())


def cache_key(request: TTSRequest, provider: str, voice: str) -> str:
    payload = "|".join(
        [
            normalize_text(request.text),
            provider,
            voice,
            request.language,
            request.emotion,
            str(request.speed),
            str(request.pitch),
            str(request.volume),
            request.format,
            str(request.sample_rate),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def cache_path(request: TTSRequest, provider: str, voice: str) -> Path:
    settings = get_settings()
    key = cache_key(request, provider, voice)
    return settings.cache_root / provider / voice / f"{key}.{request.format}"


def cache_lookup(request: TTSRequest, provider: str, voice: str) -> Path | None:
    if not get_settings().enable_cache or not request.cache:
        return None
    path = cache_path(request, provider, voice)
    return path if path.is_file() else None


def cache_store(request: TTSRequest, provider: str, voice: str, audio_bytes: bytes) -> Path:
    path = cache_path(request, provider, voice)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(audio_bytes)
    return path


def clear_cache(provider: str | None = None) -> int:
    root = get_settings().cache_root
    if not root.exists():
        return 0
    if provider:
        target = root / provider
        if target.exists():
            shutil.rmtree(target)
        return 1
    shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    return 1
