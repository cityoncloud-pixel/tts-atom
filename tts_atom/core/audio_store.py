from __future__ import annotations

import hashlib
from datetime import date
from pathlib import Path

from tts_atom.config import get_settings


def _date_dir() -> str:
    return date.today().isoformat()


def save_audio(audio_bytes: bytes, suffix: str = ".wav", segment_index: int | None = None) -> tuple[Path, str]:
    settings = get_settings()
    day = _date_dir()
    h = hashlib.sha256(audio_bytes).hexdigest()[:12]
    name = f"{h}{f'_seg{segment_index:03d}' if segment_index is not None else ''}{suffix}"
    out_dir = settings.audio_root / day
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / name
    path.write_bytes(audio_bytes)
    audio_url = f"/audio/{day}/{name}"
    return path, audio_url


def audio_url_for_cache(cache_path: Path) -> str:
    settings = get_settings()
    try:
        rel = cache_path.relative_to(settings.cache_root)
    except ValueError:
        rel = cache_path.name
    return f"/audio/cache/{rel.as_posix()}"
