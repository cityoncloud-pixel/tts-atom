from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tts_atom.schemas import TTSRequest


@dataclass
class RoleProfile:
    role_id: str
    display_name: str
    primary_provider: str
    fallback_provider: str | None
    voice: str
    language: str
    speed: float
    pitch: float
    volume: float
    emotion_default: str


def _roles_path() -> Path:
    return Path(__file__).parent / "default_roles.json"


def load_roles() -> dict[str, RoleProfile]:
    data = json.loads(_roles_path().read_text(encoding="utf-8"))
    roles: dict[str, RoleProfile] = {}
    for item in data:
        p: dict[str, Any] = item["tts_profile"]
        roles[item["role_id"]] = RoleProfile(
            role_id=item["role_id"],
            display_name=item.get("display_name", item["role_id"]),
            primary_provider=p.get("primary_provider", "melotts"),
            fallback_provider=p.get("fallback_provider"),
            voice=p.get("voice", "zh_female_01"),
            language=p.get("language", "zh"),
            speed=float(p.get("speed", 1.0)),
            pitch=float(p.get("pitch", 1.0)),
            volume=float(p.get("volume", 1.0)),
            emotion_default=p.get("emotion_default", "neutral"),
        )
    return roles


def get_role(role_id: str | None) -> RoleProfile | None:
    if not role_id:
        return None
    return load_roles().get(role_id)


def apply_role(request: TTSRequest) -> TTSRequest:
    profile = get_role(request.role_id)
    if not profile:
        return request
    data = request.model_dump()
    if not request.voice:
        data["voice"] = profile.voice
    if request.language == "zh":
        data["language"] = profile.language
    if request.speed == 1.0:
        data["speed"] = profile.speed
    if request.pitch == 1.0:
        data["pitch"] = profile.pitch
    if request.volume == 1.0:
        data["volume"] = profile.volume
    if request.emotion == "neutral":
        data["emotion"] = profile.emotion_default
    return TTSRequest(**data)
