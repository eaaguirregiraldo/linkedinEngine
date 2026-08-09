"""Configuración central del backend (design §11.3, ADR por env vars).

Carga variables de entorno vía pydantic-settings. El fichero `.env` se
busca desde el directorio de trabajo hacia arriba (la raíz del workspace),
de modo que `npm --prefix backend run dev` (CWD = backend/) también lo
encuentre. Todos los defaults permiten correr en modo demo sin credenciales
(RNF-01): `GENAI_PROVIDER == "demo"`, sin API keys.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


def _discover_env_file() -> str | None:
    """Busca el primer `.env` desde el CWD hacia arriba (raíz del workspace)."""
    current = Path.cwd()
    for directory in (current, *current.parents):
        candidate = directory / ".env"
        if candidate.is_file():
            return str(candidate)
    return None


class Settings(BaseSettings):
    """Todas las variables de entorno del sistema (design §11.3)."""

    app_env: str = "dev"
    api_port: int = 8000
    database_path: str = "data/engine.db"
    genai_provider: str = "demo"  # "demo" | "openai" (P1)
    openai_base_url: str = "https://api.openai.com/v1"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_timeout: int = 60
    demo_force_invalid: bool = False
    trace_store_raw_output: bool = False
    visual_provider: str = "svg"  # "svg" | "image" (P1)
    image_api_url: str = ""
    image_api_key: str = ""
    # CORS_ORIGINS se documenta separada por comas (design §11.3). Se modela
    # como `str` simple para evitar el decode JSON que pydantic-settings hace
    # sobre tipos complejos en versiones antiguas (2.6.x); el consumidor usa
    # `cors_origins_list`.
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=_discover_env_file(),
        env_file_encoding="utf-8",
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Allowlist CORS efectiva (CORS_ORIGINS separada por comas)."""
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    """Singleton cacheado; los módulos lo usan para leer la configuración."""
    return Settings()
