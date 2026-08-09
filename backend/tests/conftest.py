"""conftest raíz de backend — propiedad del batch A1 (Wave 1).

Añade `backend/` al sys.path para que los tests de los lotes B/C/D/E/F/G
puedan importar `domain.*`, `ai.*`, `api.*`, `db.*`, `visual.*` y `core.*`
sin importar el directorio de trabajo desde el que se invoque pytest.

Expone helpers de SQLite temporal para los tests de persistencia (lote D).
"""
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import pytest  # noqa: E402


@pytest.fixture
def db_file(tmp_path: Path) -> Path:
    """Ruta a un fichero SQLite temporal (no crea el fichero)."""
    return tmp_path / "test.db"


@pytest.fixture
def sqlite_db_url(db_file: Path) -> str:
    """URL SQLAlchemy para un fichero SQLite temporal."""
    return f"sqlite:///{db_file}"
