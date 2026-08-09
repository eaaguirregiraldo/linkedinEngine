"""Engine y session factory para SQLite en fichero (D.1, ADR-008, design §9.1).

Responsabilidades:
- Construir el engine contra ``DATABASE_PATH`` (settings de ``core.config``,
  A1.4), creando el directorio padre si falta (``data/``).
- ``create_all_tables`` idempotente: ``SQLModel.metadata.create_all`` (ADR-008).
- ``session_factory`` para obtener sesiones SQLModel sobre un engine dado.

Detalles de SQLite:
- ``check_same_thread=False``: los endpoints síncronos de FastAPI (ADR-009)
  pueden abrir la sesión desde hilos distintos del que creó el engine.
- ``PRAGMA foreign_keys=ON`` por conexión: SQLite no las activa por defecto y
  las claves foráneas de los 5 agregados deben respetarse.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine

from core.config import get_settings

__all__ = [
    "default_db_path",
    "create_db_engine",
    "create_all_tables",
    "session_factory",
]


def default_db_path() -> str:
    """Ruta por defecto de la DB (design §11.3 ``DATABASE_PATH``).

    Proviene de ``core.config.Settings`` (A1.4), que ya resuelve el ``.env``
    del workspace; default ``data/engine.db``.
    """
    return get_settings().database_path


def create_db_engine(db_path: str | os.PathLike[str] | None = None) -> Any:
    """Crea el engine SQLite para ``db_path`` (default: ``DATABASE_PATH``).

    Crea el directorio padre si no existe (``data/`` al primer arranque) y
    activa ``PRAGMA foreign_keys=ON`` por conexión.
    """
    path = Path(db_path if db_path is not None else default_db_path())
    if str(path) != ":memory:":
        path.parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(
        f"sqlite:///{path}",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:  # pragma: no cover
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


def create_all_tables(engine: Any) -> None:
    """Crea las tablas si no existen. Idempotente (ADR-008)."""
    SQLModel.metadata.create_all(engine)


def session_factory(engine: Any | None = None) -> Session:
    """Factory de sesiones SQLModel (bind = engine o el engine por defecto)."""
    return Session(bind=engine if engine is not None else create_db_engine())
