from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Generator

from tts_atom.schemas import TimingInfo


class TimingCollector:
    def __init__(self) -> None:
        self._start = time.perf_counter()
        self.data = TimingInfo()

    def elapsed_ms(self) -> int:
        return int((time.perf_counter() - self._start) * 1000)

    def finalize(self) -> TimingInfo:
        self.data.total_ms = self.elapsed_ms()
        return self.data

    @contextmanager
    def track(self, field: str) -> Generator[None, None, None]:
        t0 = time.perf_counter()
        try:
            yield
        finally:
            ms = int((time.perf_counter() - t0) * 1000)
            setattr(self.data, field, getattr(self.data, field) + ms)
