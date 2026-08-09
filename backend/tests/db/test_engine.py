"""Tests del engine SQLite (D.1): fichero, idempotencia de create_all, FK.

Cubre el criterio de D.1: SQLite temporal crea el fichero y
``create_all_tables()`` es idempotente. Usa las fixtures ``db_file`` de
``backend/tests/conftest.py`` (A1).
"""
from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import inspect
from sqlmodel import Session

from db.engine import create_all_tables, create_db_engine, default_db_path, session_factory


@pytest.fixture()
def engine(db_file: Path):
    created = create_db_engine(db_file)
    create_all_tables(created)
    return created


def test_create_db_engine_creates_parent_dir_and_file(tmp_path: Path) -> None:
    db_path = tmp_path / "nested" / "engine.db"
    engine = create_db_engine(db_path)
    create_all_tables(engine)
    assert db_path.exists(), "el fichero SQLite debe crearse en la ruta indicada"
    engine.dispose()


def test_create_all_tables_is_idempotent(engine) -> None:
    # Segunda llamada no debe fallar ni duplicar tablas (ADR-008).
    create_all_tables(engine)
    create_all_tables(engine)
    tables = inspect(engine).get_table_names()
    assert "contentproject" in tables
    assert "generationrun" in tables
    assert "candidate" in tables
    assert "visualasset" in tables
    assert "publicationattempt" in tables


def test_foreign_keys_pragma_enabled(db_file: Path) -> None:
    engine = create_db_engine(db_file)
    create_all_tables(engine)
    with engine.connect() as connection:
        row = connection.exec_driver_sql("PRAGMA foreign_keys").fetchone()
    assert row[0] == 1, "PRAGMA foreign_keys debe estar ON (claves foráneas)"
    engine.dispose()


def test_default_db_path_reads_settings() -> None:
    # A1.4 define DATABASE_PATH default "data/engine.db" (design §11.3).
    path = default_db_path()
    assert isinstance(path, str) and path.endswith("engine.db")


def test_session_factory_uses_given_engine(engine) -> None:
    with session_factory(engine) as session:
        assert isinstance(session, Session)
