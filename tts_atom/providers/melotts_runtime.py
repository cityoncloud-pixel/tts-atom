from __future__ import annotations

import io
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path
from threading import Lock
from typing import Literal

from tts_atom.config import get_settings
from tts_atom.providers.audio_util import wav_duration_ms

logger = logging.getLogger(__name__)

Backend = Literal["python_api", "cli", "none"]

_melo_import_patched = False


def _patch_melo_windows_imports() -> None:
    """MeloTTS 启动时会 import 全语言模块；Windows 上 MeCab DLL 常不可用。中文合成可跳过。"""
    global _melo_import_patched
    if _melo_import_patched:
        return
    import sys
    import types

    # 移除半加载的失败 MeCab
    for key in list(sys.modules):
        if key == "MeCab" or key.startswith("MeCab."):
            del sys.modules[key]

    fake = types.ModuleType("MeCab")

    class _FakeTagger:
        def __init__(self, *args, **kwargs):
            pass

        def parse(self, text: str) -> str:
            return ""

    fake.Tagger = _FakeTagger
    sys.modules["MeCab"] = fake
    _melo_import_patched = True


def _can_import_melo() -> bool:
    try:
        _patch_melo_windows_imports()
        from melo.api import TTS  # noqa: F401

        return True
    except ImportError:
        return False
    except Exception as exc:
        logger.debug("melo import failed: %s", exc)
        return False

# voice_id -> (MeloTTS language code, speaker key in spk2id)
VOICE_SPEAKER_MAP: dict[str, tuple[str, str]] = {
    "zh_female_01": ("ZH", "ZH"),
    "zh": ("ZH", "ZH"),
    "zh_mix": ("ZH", "ZH"),
    "en_default": ("EN", "EN-Default"),
    "en_us": ("EN", "EN-US"),
    "en_br": ("EN", "EN-BR"),
    "en_au": ("EN", "EN-AU"),
    "en_india": ("EN", "EN_INDIA"),
}

LANGUAGE_TO_MELO: dict[str, str] = {
    "zh": "ZH",
    "en": "EN",
    "mixed_zh_en": "ZH",
    "es": "ES",
    "fr": "FR",
    "jp": "JP",
    "kr": "KR",
}

_model_cache: dict[str, object] = {}
_cache_lock = Lock()


def detect_backend() -> Backend:
    if _can_import_melo():
        return "python_api"
    if _find_melo_cli():
        return "cli"
    return "none"


def _find_melo_cli() -> str | None:
    settings = get_settings()
    if settings.melotts_cli_path:
        p = Path(settings.melotts_cli_path)
        if p.is_file():
            return str(p)
    return shutil.which("melo") or shutil.which("melotts")


def is_melotts_usable() -> bool:
    return detect_backend() != "none"


def _configure_hf_cache() -> None:
    settings = get_settings()
    root = settings.models_root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HF_HOME", str(root))
    os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str(root / "hub"))


def _resolve_voice(voice: str | None, language: str) -> tuple[str, str]:
    if voice and voice in VOICE_SPEAKER_MAP:
        return VOICE_SPEAKER_MAP[voice]
    melo_lang = LANGUAGE_TO_MELO.get(language, "ZH")
    default_speaker = {
        "ZH": "ZH",
        "EN": "EN-Default",
        "ES": "ES",
        "FR": "FR",
        "JP": "JP",
        "KR": "KR",
    }.get(melo_lang, "ZH")
    return melo_lang, default_speaker


def _get_tts_model(melo_language: str):
    _patch_melo_windows_imports()
    from melo.api import TTS

    _configure_hf_cache()
    settings = get_settings()
    device = settings.melotts_device
    with _cache_lock:
        if melo_language not in _model_cache:
            logger.info("Loading MeloTTS model for language=%s device=%s", melo_language, device)
            _model_cache[melo_language] = TTS(
                language=melo_language,
                device=device,
                use_hf=settings.melotts_use_hf,
                ckpt_path=settings.melotts_ckpt_path,
            )
        return _model_cache[melo_language]


def _numpy_to_wav_bytes(audio, sample_rate: int) -> bytes:
    try:
        import numpy as np
        import soundfile as sf

        if not isinstance(audio, np.ndarray):
            audio = np.asarray(audio, dtype=np.float32)
        buf = io.BytesIO()
        sf.write(buf, audio, sample_rate, format="WAV")
        return buf.getvalue()
    except ImportError:
        pass

    # stdlib fallback: 16-bit PCM WAV
    import numpy as np

    audio = np.asarray(audio, dtype=np.float32)
    audio = np.clip(audio, -1.0, 1.0)
    pcm = (audio * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())
    return buf.getvalue()


def _resample_wav(wav_bytes: bytes, target_sr: int) -> bytes:
    if target_sr <= 0:
        return wav_bytes
    with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
        src_sr = wf.getframerate()
        if src_sr == target_sr:
            return wav_bytes
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        frames = wf.readframes(wf.getnframes())
    if sampwidth != 2:
        return wav_bytes
    try:
        import numpy as np

        audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
        if n_channels > 1:
            audio = audio.reshape(-1, n_channels).mean(axis=1)
        duration = len(audio) / src_sr
        target_len = int(duration * target_sr)
        if target_len < 1:
            target_len = 1
        x_old = np.linspace(0, 1, num=len(audio), endpoint=False)
        x_new = np.linspace(0, 1, num=target_len, endpoint=False)
        resampled = np.interp(x_new, x_old, audio)
        pcm = (np.clip(resampled, -1, 1) * 32767).astype(np.int16)
        out = io.BytesIO()
        with wave.open(out, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(target_sr)
            wf.writeframes(pcm.tobytes())
        return out.getvalue()
    except ImportError:
        logger.warning("Cannot resample %s -> %s without numpy", src_sr, target_sr)
        return wav_bytes


def synthesize_melotts(
    text: str,
    *,
    voice: str | None,
    language: str,
    speed: float = 1.0,
    sample_rate: int = 24000,
) -> tuple[bytes, int]:
    """Return (wav_bytes, duration_ms). Raises RuntimeError if unavailable."""
    backend = detect_backend()
    melo_lang, speaker_key = _resolve_voice(voice, language)

    if backend == "python_api":
        wav_bytes, native_sr = _synthesize_api(text, melo_lang, speaker_key, speed)
    elif backend == "cli":
        wav_bytes, native_sr = _synthesize_cli(text, melo_lang, speaker_key, speed)
    else:
        raise RuntimeError(
            "MeloTTS is not installed. See README: pip install -e '.[melotts]' "
            "or https://github.com/myshell-ai/MeloTTS/blob/main/docs/install.md"
        )

    if sample_rate and sample_rate != native_sr:
        wav_bytes = _resample_wav(wav_bytes, sample_rate)
        native_sr = sample_rate

    return wav_bytes, wav_duration_ms(wav_bytes)


def _synthesize_api(
    text: str, melo_language: str, speaker_key: str, speed: float
) -> tuple[bytes, int]:
    model = _get_tts_model(melo_language)
    spk2id = model.hps.data.spk2id
    if speaker_key not in spk2id:
        speaker_key = next(iter(spk2id.keys()))
    speaker_id = spk2id[speaker_key]
    audio = model.tts_to_file(
        text,
        speaker_id,
        output_path=None,
        speed=max(0.5, min(speed, 2.0)),
        quiet=True,
    )
    native_sr = int(model.hps.data.sampling_rate)
    return _numpy_to_wav_bytes(audio, native_sr), native_sr


def _synthesize_cli(
    text: str, melo_language: str, speaker_key: str, speed: float
) -> tuple[bytes, int]:
    cli = _find_melo_cli()
    if not cli:
        raise RuntimeError("melo CLI not found")

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        out_path = Path(tmp.name)
    try:
        cmd = [cli, text, str(out_path), "-l", melo_language]
        if melo_language == "EN":
            cmd.extend(["--speaker", speaker_key])
        if speed != 1.0:
            cmd.extend(["--speed", str(speed)])
        logger.debug("MeloTTS CLI: %s", cmd)
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=get_settings().melotts_timeout_sec,
        )
        if proc.returncode != 0:
            # fallback: python -m melo.main
            cmd = [
                sys.executable,
                "-m",
                "melo.main",
                text,
                str(out_path),
                "-l",
                melo_language,
            ]
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=get_settings().melotts_timeout_sec,
            )
        if proc.returncode != 0:
            raise RuntimeError(
                f"melo CLI failed (code {proc.returncode}): {proc.stderr or proc.stdout}"
            )
        data = out_path.read_bytes()
        with wave.open(io.BytesIO(data), "rb") as wf:
            native_sr = wf.getframerate()
        return data, native_sr
    finally:
        out_path.unlink(missing_ok=True)


def list_melo_voices(language: str | None = None) -> list[tuple[str, str, str]]:
    """Return list of (voice_id, melo_lang, description)."""
    items = []
    for voice_id, (melo_lang, _) in VOICE_SPEAKER_MAP.items():
        if language:
            lang_key = LANGUAGE_TO_MELO.get(language, language.upper())
            if melo_lang != lang_key and not (language == "zh" and melo_lang == "ZH"):
                continue
        items.append((voice_id, melo_lang, f"MeloTTS speaker mapping ({melo_lang})"))
    if not items and (not language or language in ("zh", "mixed_zh_en")):
        items.append(("zh_female_01", "ZH", "MeloTTS 中文默认"))
    return items


def doctor_info() -> dict:
    backend = detect_backend()
    info = {
        "backend": backend,
        "import_ok": _can_import_melo(),
        "cli_path": _find_melo_cli(),
        "models_root": str(get_settings().models_root.resolve()),
        "device": get_settings().melotts_device,
    }
    if backend == "python_api":
        try:
            melo_lang, _ = _resolve_voice("zh_female_01", "zh")
            model = _get_tts_model(melo_lang)
            info["speakers"] = list(model.hps.data.spk2id.keys())
            info["sample_rate"] = int(model.hps.data.sampling_rate)
        except Exception as exc:  # noqa: BLE001
            info["load_error"] = str(exc)
    return info
