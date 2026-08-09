"""Tests de dependencias FastAPI (G.2, design §3, HARN-09).

Criterio de G.2: sin key → ``DemoProvider``; con flag → provider correcto;
nunca degradación silenciosa (si se pidió openai y no se puede, error tipado,
jamás un switch automático a demo).
"""
from __future__ import annotations

import sys
import types

import pytest
from sqlmodel import Session, select

from api import dependencies
from api.schemas import BriefIn
from ai.demo_provider import DemoProvider
from core.config import Settings
from db.engine import create_all_tables, create_db_engine
from db.models import ContentProject


# ── get_provider ─────────────────────────────────────────────────────────────


def test_default_settings_returns_demo_provider() -> None:
    """Default (``GENAI_PROVIDER=demo``, sin key) → ``DemoProvider``."""
    provider = dependencies.get_provider(Settings())
    assert isinstance(provider, DemoProvider)
    assert provider.name == "DEMO_PROVIDER"


def test_demo_provider_respects_force_invalid_flag() -> None:
    """``DEMO_FORCE_INVALID=true`` se propaga al constructor del demo."""
    provider = dependencies.get_provider(Settings(demo_force_invalid=True))
    assert isinstance(provider, DemoProvider)
    assert provider._force_invalid is True  # noqa: SLF001 — atributo de test


def test_openai_flag_with_key_selects_openai_provider(monkeypatch) -> None:
    """Con ``GENAI_PROVIDER=openai`` + key → el proveedor correcto (no demo).

    El adaptador ``ai.openai_compat`` es P1 (K.1): se inyecta un módulo fake en
    ``sys.modules`` para verificar la selección sin implementar el adaptador.
    """
    fake_module = types.ModuleType("ai.openai_compat")

    class FakeOpenAICompatProvider:
        name = "openai-compatible"
        model: str | None = "gpt-4o-mini"
        params: dict = {}

        def __init__(self, settings=None) -> None:
            self.settings = settings

        def generate_candidates(self, brief: BriefIn) -> str:
            raise NotImplementedError

        def evaluate_candidates(self, candidates, brief, catalog_version: str) -> str:
            raise NotImplementedError

    fake_module.OpenAICompatProvider = FakeOpenAICompatProvider
    monkeypatch.setitem(sys.modules, "ai.openai_compat", fake_module)

    settings = Settings(genai_provider="openai", openai_api_key="sk-test")
    provider = dependencies.get_provider(settings)
    assert isinstance(provider, FakeOpenAICompatProvider)
    assert provider.name == "openai-compatible"


def test_openai_flag_without_key_raises_never_demo() -> None:
    """``GENAI_PROVIDER=openai`` sin key → error tipado, NUNCA demo (HARN-09)."""
    from ai.providers import ProviderError

    settings = Settings(genai_provider="openai", openai_api_key="")
    with pytest.raises(ProviderError) as excinfo:
        dependencies.get_provider(settings)
    assert excinfo.value.code == "UNAVAILABLE"


def test_openai_flag_with_key_but_adapter_missing_raises(monkeypatch) -> None:
    """Flag + key pero adaptador P1 ausente → error tipado, sin degradación
    silenciosa a demo (el adaptador no existe hasta K.1)."""
    from ai.providers import ProviderError

    monkeypatch.delitem(sys.modules, "ai.openai_compat", raising=False)
    settings = Settings(genai_provider="openai", openai_api_key="sk-test")
    with pytest.raises(ProviderError) as excinfo:
        dependencies.get_provider(settings)
    assert excinfo.value.code == "UNAVAILABLE"


# ── get_session ──────────────────────────────────────────────────────────────


def test_get_session_yields_working_session(monkeypatch, tmp_path) -> None:
    """La dependencia cede una sesión SQLModel funcional sobre SQLite temp."""
    engine = create_db_engine(tmp_path / "g2.db")
    create_all_tables(engine)
    monkeypatch.setattr(dependencies, "_engine", engine)

    session = next(dependencies.get_session())
    try:
        assert isinstance(session, Session)
        assert list(session.exec(select(ContentProject))) == []
    finally:
        session.close()


def test_get_session_closes_on_generator_exit(monkeypatch, tmp_path) -> None:
    """La sesión se cierra al terminar el ciclo de vida del generador."""
    engine = create_db_engine(tmp_path / "g2b.db")
    create_all_tables(engine)
    monkeypatch.setattr(dependencies, "_engine", engine)

    closed: list[Session] = []
    original_close = Session.close

    def _recording_close(self) -> None:
        closed.append(self)
        original_close(self)

    monkeypatch.setattr(Session, "close", _recording_close)

    gen = dependencies.get_session()
    session = next(gen)
    with pytest.raises(StopIteration):
        next(gen)
    assert session in closed


# ── get_harness / get_settings ───────────────────────────────────────────────


def test_get_harness_exposes_run_functions() -> None:
    """``get_harness`` expone ``run_generation``/``run_evaluation``."""
    harness = dependencies.get_harness()
    assert callable(harness.run_generation)
    assert callable(harness.run_evaluation)


def test_get_settings_returns_cached_singleton() -> None:
    """``get_settings`` es el singleton cacheado de ``core.config``."""
    assert dependencies.get_settings is not None
    assert dependencies.get_settings() is dependencies.get_settings()
