from __future__ import annotations

import json
import sys
from typing import Optional

import typer
import uvicorn

from tts_atom.config import get_settings
from tts_atom.core import cache as cache_mod
from tts_atom.core.engine import get_engine
from tts_atom.schemas import PrewarmRequest, SplitSynthesizeRequest, TTSRequest

app = typer.Typer(no_args_is_help=True, help="tts-atom — local TTS atomic service")


def _print_json(data: object) -> None:
    typer.echo(json.dumps(data, ensure_ascii=False, indent=2, default=str))


@app.command()
def synth(
    text: str = typer.Option(..., "--text", "-t", help="Text to synthesize"),
    voice: Optional[str] = typer.Option(None, "--voice"),
    role_id: Optional[str] = typer.Option(None, "--role-id"),
    provider: str = typer.Option("auto", "--provider"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    engine = get_engine()
    req = TTSRequest(text=text, voice=voice, role_id=role_id, provider=provider)  # type: ignore[arg-type]
    resp = engine.synthesize(req)
    if as_json:
        _print_json(resp.model_dump())
    elif not resp.ok:
        typer.secho(resp.error.message if resp.error else "failed", fg=typer.colors.RED)
        raise typer.Exit(1)
    else:
        typer.echo(f"audio: {resp.audio_path}")
    if not resp.ok:
        raise typer.Exit(1)


@app.command()
def speak(text: str = typer.Argument(..., help="Text to speak")) -> None:
    engine = get_engine()
    resp = engine.synthesize(TTSRequest(text=text))
    if not resp.ok or not resp.audio_path:
        typer.secho("synthesis failed", fg=typer.colors.RED)
        raise typer.Exit(1)
    path = resp.audio_path
    try:
        import winsound

        winsound.PlaySound(path, winsound.SND_FILENAME)
    except Exception:
        typer.echo(f"Audio saved to {path} (playback not available)")


@app.command()
def serve(
    host: Optional[str] = typer.Option(None, "--host"),
    port: Optional[int] = typer.Option(None, "--port"),
) -> None:
    settings = get_settings()
    uvicorn.run(
        "tts_atom.server:app",
        host=host or settings.host,
        port=port or settings.port,
        log_level=settings.log_level.lower(),
    )


@app.command()
def voices(
    provider: Optional[str] = typer.Option(None, "--provider"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    engine = get_engine()
    items = engine.list_voices(provider=provider)
    if as_json:
        _print_json([v.model_dump() for v in items])
    else:
        for v in items:
            typer.echo(f"{v.provider}\t{v.voice}\t{v.language}")


@app.command()
def doctor(as_json: bool = typer.Option(False, "--json")) -> None:
    settings = get_settings()
    engine = get_engine()
    report = {
        "ok": True,
        "audio_root": str(settings.audio_root.resolve()),
        "cache_root": str(settings.cache_root.resolve()),
        "models_root": str(settings.models_root.resolve()),
        "providers": engine.registry.availability(),
        "force_mock": settings.force_mock,
    }
    if as_json:
        _print_json(report)
    else:
        for k, v in report["providers"].items():
            typer.echo(f"{k}: {'ok' if v else 'unavailable'}")


@app.command("cache")
def cache_cmd(
    action: str = typer.Argument("clear", help="clear"),
    provider: Optional[str] = typer.Option(None, "--provider"),
) -> None:
    if action == "clear":
        cache_mod.clear_cache(provider)
        typer.echo("cache cleared")
    else:
        typer.echo(f"unknown action: {action}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
