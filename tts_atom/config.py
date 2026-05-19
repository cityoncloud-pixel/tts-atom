from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TTS_ATOM_", env_file=".env", extra="ignore")

    host: str = "127.0.0.1"
    port: int = 9020
    default_provider: str = "melotts"
    default_language: str = "zh"
    audio_root: Path = Path("./runs")
    cache_root: Path = Path("./cache")
    models_root: Path = Path("./models")
    enable_cache: bool = True
    max_text_length: int = 1000
    default_format: str = "wav"
    default_sample_rate: int = 24000
    log_level: str = "INFO"
    force_mock: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
