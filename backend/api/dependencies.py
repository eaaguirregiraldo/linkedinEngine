"""Dependencias FastAPI (design §3, HARN-09).

- ``get_session``: cede una sesión SQLModel por request (ADR-009 síncrono)
  sobre un engine cacheado a nivel de módulo (SQLite ``DATABASE_PATH``).
- ``get_settings``: re-export del singleton cacheado de ``core.config``.
- ``get_provider``: selección de proveedor GenAI — ``DemoProvider`` por
  default; OpenAI-compatible SOLO si ``GENAI_PROVIDER=openai`` + key
  (adaptador P1, K.1). Nunca degradación silenciosa (HARN-09): si se pidió
  openai y no se puede construir, se lanza ``ProviderError(UNAVAILABLE)``
  tipado — la UI sugiere DemoProvider, el sistema no conmuta solo.
- ``get_harness``: expone el módulo ``ai.harness`` (retry/repair/traza).
"""
from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from fastapi import Depends
from sqlmodel import Session

from ai.demo_provider import DemoProvider
from ai.providers import UNAVAILABLE, GenAIProvider, ProviderError
from core.config import Settings, get_settings
from db.engine import create_db_engine

__all__ = [
    "get_harness",
    "get_provider",
    "get_session",
    "get_settings",
]

# Engine cacheado a nivel de módulo: las sesiones se abren sobre este engine.
# Los tests lo reemplazan con `monkeypatch.setattr(dependencies, "_engine", e)`.
_engine: Any | None = None


def get_session() -> Iterator[Session]:
    """Dependencia de sesión SQLModel (design §3, ADR-009).

    La sesión vive dentro del ciclo del request: se cierra al terminar.
    """
    global _engine
    if _engine is None:
        _engine = create_db_engine()
    with Session(_engine) as session:
        yield session


def get_provider(settings: Settings = Depends(get_settings)) -> GenAIProvider:
    """Selecciona el proveedor GenAI según ``GENAI_PROVIDER`` (HARN-09).

    - ``demo`` (default): ``DemoProvider`` determinístico, sin red ni keys.
    - ``openai``: SOLO si hay ``OPENAI_API_KEY``; el adaptador es P1 (K.1) y
      se importa de forma diferida. Sin key o sin adaptador → error tipado
      ``ProviderError(UNAVAILABLE)``: nunca conmutación automática a demo.
    """
    if settings.genai_provider == "openai":
        if not settings.openai_api_key:
            raise ProviderError(
                UNAVAILABLE,
                "GENAI_PROVIDER=openai requiere OPENAI_API_KEY: "
                "activá la key o usá demo explícitamente (HARN-09)",
            )
        try:
            from ai.openai_compat import OpenAICompatProvider  # P1, opcional
        except ImportError as exc:  # adaptador no implementado (hasta K.1)
            raise ProviderError(
                UNAVAILABLE,
                "el adaptador OpenAI-compatible no está disponible en esta "
                "build: usá GENAI_PROVIDER=demo (HARN-09, sin conmutación automática)",
            ) from exc
        return OpenAICompatProvider(settings=settings)
    return DemoProvider(force_invalid=settings.demo_force_invalid)


def get_harness() -> Any:
    """Expone el módulo ``ai.harness`` (run_generation/run_evaluation)."""
    from ai import harness

    return harness
