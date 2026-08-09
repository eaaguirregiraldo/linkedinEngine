"""Tests de repos e invariantes (D.2/D.3): 5 agregados, PST-01, TRC-03,
invariantes §9.2 y PST-02 (sin credenciales).

Cubre el criterio de D.3: round-trip de los 5 agregados; una NUEVA sesión lee
lo persistido (PST-01); una ejecución fallida conserva error+traza y no expone
candidatos incompletos como válidos (invariante 4). Cada test usa SQLite en
fichero temporal (fixtures ``db_file``/``engine``) — nada toca la DB real.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import inspect
from sqlmodel import Session

from db import repos
from db.engine import create_all_tables, create_db_engine
from db.models import ContentProject


@pytest.fixture()
def engine(db_file: Path):
    created = create_db_engine(db_file)
    create_all_tables(created)
    return created


@pytest.fixture()
def session(engine):
    with Session(engine) as s:
        yield s


# ── Helpers de datos ────────────────────────────────────────────────────────


def _make_candidates() -> list[dict]:
    return [
        {
            "angle": "problem-story",
            "hook": "Hook problema",
            "body": "Cuerpo del candidato problem-story.",
            "cta": "¿Qué conocimiento operativo tenés sin documentar?",
            "claims": [{"text": "La sintaxis es la parte simple.", "support": "e2"}],
        },
        {
            "angle": "practical-framework",
            "hook": "Hook framework",
            "body": "Cuerpo del candidato practical-framework.",
            "cta": "Probá mapear reglas antes de tocar código.",
            "claims": [{"text": "Empezá por inventariar reglas.", "support": "e1"}],
        },
        {
            "angle": "argued-position",
            "hook": "Hook posición",
            "body": "Cuerpo del candidato argued-position.",
            "cta": "¿Coincidís en que el riesgo es el conocimiento?",
            "claims": [],
        },
    ]


def _create_project_with_run(session: Session) -> tuple[ContentProject, object]:
    project = repos.create_project(session, "Idea demo de prueba")
    repos.set_project_brief(
        session,
        project.id,
        {
            "thesis": "Migrar es recuperar conocimiento.",
            "audience": "líderes",
            "objective": "reencuadrar",
            "evidence": [],
            "constraints": [],
        },
    )
    repos.set_project_status(session, project.id, "BRIEF_READY")
    run = repos.create_run(
        session,
        project.id,
        provider="DEMO_PROVIDER",
        prompt_version="1.0.0",
        schema_version="1.0.0",
        prompt_hash="sha256:abc",
    )
    return project, run


# ── D.1/D.3: round-trip de los 5 agregados ─────────────────────────────────


def test_project_round_trip_new_session_reads(engine, session) -> None:
    """PST-01: una NUEVA sesión lee lo persistido (sobrevive la sesión)."""
    project = repos.create_project(session, "Idea persistida", title="Título")
    with Session(engine) as fresh:
        loaded = repos.get_project(fresh, project.id)
        assert loaded is not None
        assert loaded.raw_idea == "Idea persistida"
        assert loaded.title == "Título"
        assert loaded.status == "IDEA"


def test_five_aggregates_round_trip(session) -> None:
    """Recorre los 5 agregados y verifica ``get_run_detail`` los ensambla."""
    project, run = _create_project_with_run(session)
    candidates = repos.add_candidates(session, run.id, _make_candidates())
    assert len(candidates) == 3

    evaluation = {
        "dimensions": {"hook": 4, "niche_relevance": 4},
        "penalties": {"risk": 0, "generic": 0},
        "score_final": 80,
        "blockers": [],
    }
    updated = repos.update_candidate_evaluation(session, candidates[0].id, evaluation)
    assert updated.evaluation == evaluation

    visual = repos.save_visual(
        session,
        candidates[0].id,
        thesis="Migrar es recuperar conocimiento.",
        concept="capa visible vs capa oculta",
        elements=[{"element_id": "e1", "kind": "figure", "description": "x", "rationale": "de la tesis"}],
        alt_text="Diagrama de capas de conocimiento",
    )
    assert visual.status == "VISUAL_DRAFT"

    repos.update_visual_status(session, visual.id, "VISUAL_READY")
    receipt = {
        "id": 1,
        "created_at": "2026-08-09T00:00:00Z",
        "candidate_version": 1,
        "visual_id": visual.id,
        "notice": "no se envió contenido a LinkedIn",
    }
    attempt = repos.save_publication_attempt(
        session, candidates[0].id, receipt=receipt
    )

    detail = repos.get_run_detail(session, run.id)
    assert detail is not None
    assert detail["run"].status == "GENERATING"
    assert len(detail["candidates"]) == 3
    assert detail["visuals"][candidates[0].id].status == "VISUAL_READY"
    assert detail["publications"][candidates[0].id].id == attempt.id

    # list_projects (P1-ready) devuelve el proyecto.
    assert [p.id for p in repos.list_projects(session)] == [project.id]


# ── Invariantes §9.2 ───────────────────────────────────────────────────────


def test_angle_unique_per_run(session) -> None:
    """Invariante 6: ``angle`` único por run."""
    _, run = _create_project_with_run(session)
    candidates = _make_candidates()
    candidates.append(dict(candidates[0]))  # angle duplicado
    with pytest.raises(ValueError, match="angle duplicado"):
        repos.add_candidates(session, run.id, candidates)


def test_edit_invalidates_evaluation_and_bumps_version(session) -> None:
    """Invariante 1: edición → content_version++ y evaluación invalidada."""
    _, run = _create_project_with_run(session)
    candidate = repos.add_candidates(session, run.id, _make_candidates())[0]
    repos.update_candidate_evaluation(
        session, candidate.id, {"score_final": 80, "dimensions": {}}
    )
    bumped = repos.bump_candidate_version(session, candidate.id)
    assert bumped.content_version == 2
    assert bumped.evaluation is None
    assert bumped.selected is False


def test_decision_history_append_only(session) -> None:
    """``decision_history`` acumula decisiones sin borrar las anteriores."""
    _, run = _create_project_with_run(session)
    candidate = repos.add_candidates(session, run.id, _make_candidates())[0]
    repos.append_decision(
        session, candidate.id, {"decision": "RECOMMENDED", "by": "evaluator", "reason": "score alto", "at": "t1"}
    )
    repos.append_decision(
        session, candidate.id, {"decision": "REVISION_REQUIRED", "by": "editor", "reason": "revisión", "at": "t2"}
    )
    loaded = repos.get_candidate(session, candidate.id)
    assert [d["decision"] for d in loaded.decision_history] == [
        "RECOMMENDED",
        "REVISION_REQUIRED",
    ]


def test_trace_events_append_only(session) -> None:
    """TRC-03: los eventos se agregan en orden y no existe mutación."""
    _, run = _create_project_with_run(session)
    repos.append_trace_event(session, run.id, {"ts": "t1", "type": "prompt_resolved", "prompt_id": "p@1.0.0"})
    repos.append_trace_event(session, run.id, {"ts": "t2", "type": "provider_invoked", "provider": "DEMO_PROVIDER"})
    loaded = repos.get_run(session, run.id)
    assert [e["type"] for e in loaded.trace_events] == ["prompt_resolved", "provider_invoked"]
    # complete_run conserva la traza intacta (no la pisa ni la reemplaza).
    repos.complete_run(session, run.id, "GENERATED")
    again = repos.get_run(session, run.id)
    assert [e["type"] for e in again.trace_events] == ["prompt_resolved", "provider_invoked"]


def test_failed_run_preserves_error_trace_and_no_valid_candidates(session) -> None:
    """Invariante 4 (PST-01 escenario): fallo conserva error+traza y no crea
    candidatos incompletos como válidos."""
    _, run = _create_project_with_run(session)
    repos.append_trace_event(session, run.id, {"ts": "t1", "type": "output_validated", "checks": [{"name": "schema", "ok": False}]})
    failed = repos.complete_run(session, run.id, "GENERATION_FAILED", error_code="INVALID_OUTPUT")
    assert failed.status == "GENERATION_FAILED"
    assert failed.error_code == "INVALID_OUTPUT"
    assert failed.completed_at is not None
    assert len(failed.trace_events) == 1
    assert repos.list_candidates_for_run(session, run.id) == []


# ── Invariante 5 (publicación simulada) ────────────────────────────────────


def test_save_publication_attempt_remote_id_always_none(session) -> None:
    """Invariante 5: en modo simulado ``remote_id`` es SIEMPRE None (SIM-02).

    La garantía vive en el repo (SQLModel table=True no ejecuta validators de
    pydantic en ``__init__``): no hay camino para persistir un intento
    simulado con ``remote_id`` no nulo.
    """
    _, run = _create_project_with_run(session)
    candidate = repos.add_candidates(session, run.id, _make_candidates())[0]
    attempt = repos.save_publication_attempt(
        session, candidate.id, receipt={"notice": "no se envió contenido a LinkedIn"}
    )
    assert attempt.mode == "simulated"
    assert attempt.status == "SIMULATED_PUBLISHED"
    assert attempt.remote_id is None
    # El recibo local no contiene IDs/URLs remotos (RNF-02, SIM-02): sin claves
    # remote/url y sin valores que apunten a un recurso remoto. El texto del
    # notice ("no se envió contenido a LinkedIn") SÍ menciona LinkedIn — es el
    # aviso honesto obligatorio, no un enlace.
    assert not any("remote" in key or "url" in key for key in attempt.receipt)
    assert not any(
        isinstance(value, str) and value.startswith(("http", "urn:"))
        for value in attempt.receipt.values()
    )


# ── PST-02: sin secretos en persistencia ───────────────────────────────────


def test_no_credential_columns_in_any_table(engine) -> None:
    """PST-02: ninguna tabla de la demo tiene columnas de credenciales."""
    secret_hints = ("key", "token", "secret", "password", "credential", "authorization")
    inspector = inspect(engine)
    for table in inspector.get_table_names():
        for column in inspector.get_columns(table):
            name = column["name"].lower()
            assert not any(hint in name for hint in secret_hints), (
                f"columna de credenciales detectada: {table}.{column['name']}"
            )
