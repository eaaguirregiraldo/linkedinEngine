"""Tests del seed demo (D.4): idempotencia, regeneración tras borrar el
fichero, forma del brief contra el contrato canónico (C.1) y voz v0
provisional. Cubre CAP-01/CAP-03 y PST-01 (escenario "seed reproducible").
"""
from __future__ import annotations

from pathlib import Path

import pytest
from sqlmodel import Session

from api.schemas import BriefIn, DemoIdeaOut
from db import repos, seed
from db.engine import create_all_tables, create_db_engine


@pytest.fixture()
def engine(tmp_path: Path):
    return create_db_engine(tmp_path / "seed.db")


@pytest.fixture()
def session(engine):
    create_all_tables(engine)
    with Session(engine) as s:
        yield s


def test_seed_inserts_three_ideas(session) -> None:
    inserted = seed.seed_demo_data(session)
    assert inserted == 3
    ideas = seed.list_demo_ideas(session)
    assert len(ideas) == 3
    for idea in ideas:
        assert idea.status == "IDEA"
        assert idea.raw_idea.strip()


def test_seed_is_idempotent(session) -> None:
    """Doble seed no duplica (ADR-008 / PST-01)."""
    assert seed.seed_demo_data(session) == 3
    assert seed.seed_demo_data(session) == 0
    assert len(seed.list_demo_ideas(session)) == 3


def test_seed_regenerates_after_deleting_file(tmp_path: Path) -> None:
    """Borrar el fichero → un nuevo arranque regenera el estado demo."""
    db_path = tmp_path / "engine.db"

    engine = create_db_engine(db_path)
    create_all_tables(engine)
    with Session(engine) as s:
        assert seed.seed_demo_data(s) == 3
    engine.dispose()

    db_path.unlink()  # borrar data/engine.db
    assert not db_path.exists()

    engine2 = create_db_engine(db_path)
    create_all_tables(engine2)
    with Session(engine2) as s:
        assert seed.seed_demo_data(s) == 3
        assert len(seed.list_demo_ideas(s)) == 3
    engine2.dispose()


def test_demo_ideas_brief_conforms_to_canonical_contract(session) -> None:
    """Cada brief del seed valida contra ``BriefIn`` (contrato C.1) y cada idea
    mapea a ``DemoIdeaOut`` (design §9.3)."""
    seed.seed_demo_data(session)
    ideas = seed.list_demo_ideas(session)
    assert len(ideas) >= 3  # GET /api/ideas/demo devuelve ≥3

    for idea in ideas:
        brief = BriefIn.model_validate(idea.brief)
        assert brief.thesis.strip()
        assert brief.audience  # default de la idea demo (CAP-03)
        assert brief.objective
        assert len(brief.evidence) >= 1  # CAP-02: ≥1 evidencia
        demo = DemoIdeaOut(
            id=str(idea.id),
            raw_idea=idea.raw_idea,
            default_audience=brief.audience,
            default_objective=brief.objective,
        )
        assert demo.raw_idea.strip()


def test_seeded_projects_have_voice_v0_provisional(session) -> None:
    """Voz v0 provisional etiquetada (SOLUTION.md §4.2, VOI-01)."""
    seed.seed_demo_data(session)
    for idea in seed.list_demo_ideas(session):
        assert idea.voice_profile["version"] == "v0"
        assert "provisional" in idea.voice_profile["label"]
        assert idea.voice_profile["rules"]


def test_seed_evidence_shapes_are_typed(session) -> None:
    """La clasificación de evidencia usa los 3 tipos de CAP-05."""
    seed.seed_demo_data(session)
    valid_types = {"known_facts", "author_opinions", "open_questions"}
    for idea in seed.list_demo_ideas(session):
        for item in idea.brief["evidence"]:
            assert item["type"] in valid_types
            assert item["text"].strip()


def test_demo_ideas_exportable_via_repos(session) -> None:
    """El endpoint de ideas demo lee proyectos persistidos (P1-ready)."""
    seed.seed_demo_data(session)
    assert len(repos.list_projects(session)) == 3
