from __future__ import annotations

from tts_atom.config import get_settings
from tts_atom.providers.base import TTSProvider
from tts_atom.providers.melotts_provider import MeloTTSProvider
from tts_atom.providers.mock_provider import MockProvider
from tts_atom.providers.stub_provider import StubProvider
from tts_atom.providers.windows_sapi_provider import WindowsSapiProvider
from tts_atom.roles.role_profiles import get_role
from tts_atom.schemas import TTSRequest


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, TTSProvider] = {
            "mock": MockProvider(),
            "melotts": MeloTTSProvider(),
            "windows_sapi": WindowsSapiProvider(),
            "kokoro": StubProvider("kokoro"),
            "edge": StubProvider("edge"),
            "doubao": StubProvider("doubao"),
        }

    def get(self, name: str) -> TTSProvider | None:
        return self._providers.get(name)

    def all(self) -> dict[str, TTSProvider]:
        return self._providers

    def availability(self) -> dict[str, bool]:
        settings = get_settings()
        out = {name: p.is_available() for name, p in self._providers.items()}
        if settings.force_mock:
            out["mock"] = True
        return out


def resolve_provider_chain(request: TTSRequest, registry: ProviderRegistry) -> list[str]:
    settings = get_settings()
    if settings.force_mock:
        return ["mock"]

    if request.provider != "auto":
        return [request.provider]

    chain: list[str] = []
    role = get_role(request.role_id)
    if role:
        chain.append(role.primary_provider)
        if role.fallback_provider:
            chain.append(role.fallback_provider)
    if settings.default_provider not in chain:
        chain.append(settings.default_provider)
    if "windows_sapi" not in chain:
        chain.append("windows_sapi")

    seen: set[str] = set()
    ordered: list[str] = []
    for name in chain:
        if name not in seen:
            seen.add(name)
            ordered.append(name)
    return ordered
