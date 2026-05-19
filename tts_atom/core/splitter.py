from __future__ import annotations

import re

PRIMARY_SPLITTERS = re.compile(r"([。！？；.!?;\n]+)")
MIN_LEN = 4
MAX_LEN = 80


def split_sentences(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    parts = PRIMARY_SPLITTERS.split(text)
    chunks: list[str] = []
    buf = ""
    for part in parts:
        if not part:
            continue
        if PRIMARY_SPLITTERS.fullmatch(part):
            buf += part
            if buf.strip():
                chunks.append(buf.strip())
            buf = ""
        else:
            buf += part
    if buf.strip():
        chunks.append(buf.strip())
    merged = _merge_short(chunks)
    result: list[str] = []
    for c in merged:
        result.extend(_split_long(c))
    return result


def _merge_short(chunks: list[str]) -> list[str]:
    if not chunks:
        return []
    out: list[str] = []
    acc = ""
    for ch in chunks:
        if len(ch) < MIN_LEN:
            acc = (acc + ch).strip()
            continue
        if acc:
            out.append(acc)
            acc = ""
        out.append(ch)
    if acc:
        if out:
            out[-1] = (out[-1] + " " + acc).strip()
        else:
            out.append(acc)
    return [o for o in out if o]


def _split_long(chunk: str) -> list[str]:
    if len(chunk) <= MAX_LEN:
        return [chunk]
    sub: list[str] = []
    rest = chunk
    while len(rest) > MAX_LEN:
        cut = rest.rfind("，", 0, MAX_LEN)
        if cut < MIN_LEN:
            cut = rest.rfind(" ", 0, MAX_LEN)
        if cut < MIN_LEN:
            cut = MAX_LEN
        sub.append(rest[:cut].strip())
        rest = rest[cut:].strip()
    if rest:
        sub.append(rest)
    return sub
