from __future__ import annotations

import io
import struct
import wave


def silent_wav_bytes(duration_ms: int = 100, sample_rate: int = 24000) -> bytes:
    n_frames = max(1, int(sample_rate * duration_ms / 1000))
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"\x00\x00" * n_frames)
    return buf.getvalue()


def wav_duration_ms(data: bytes) -> int:
    with wave.open(io.BytesIO(data), "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        return int(frames / rate * 1000) if rate else 0
