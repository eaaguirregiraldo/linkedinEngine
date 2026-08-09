"""Tests de ``api.main`` (G.5, design §11.2/§13, ADR-008).

Criterio G.5 con TestClient (corre el lifespan por contexto):
- la app arranca con los routers montados (smoke: ``uvicorn api.main:app``);
- ``GET /openapi.json`` 200;
- preflight CORS responde los headers correctos (allowlist, sin credenciales);
- el seed se aplica al primer arranque y NO duplica al reiniciar (ADR-008);
- ``/docs``/``/redoc`` solo en ``APP_ENV=dev`` (design §13).

Her meticidad: cada test apunta ``DATABASE_PATH`` a un SQLite temporal ANTES de
construir la app (``get_settings`` es singleton cacheado; se limpia el cache y
se resetea ``dependencies._engine`` para que la sesión de los requests apunte
al mismo fichero que seedea el lifespan).
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.config import get_settings
from db.engine import create_all_tables, create_db_engine


@pytest.fixture()
def app(monkeypatch, db_file: Path):
    from api import dependencies

    monkeypatch.setenv("DATABASE_PATH", str(db_file))
    get_settings.cache_clear()
    monkeypatch.setattr(dependencies, "_engine", None)

    from api.main import create_app

    created = create_app()
    yield created
    # Restaura el singleton de settings: tras el teardown del fixture, el env
    # vuelve al original (monkeypatch) y el próximo get_settings() re-lee los
    # valores reales — sin esto, el cache queda polucionado con la DB temp y
    # otros tests (p. ej. db/test_engine.py) ven la ruta equivocada.
    get_settings.cache_clear()


@pytest.fixture()
def client(app: FastAPI):
    with TestClient(app) as client:
        yield client


def test_app_arranca_con_routers_montados():
    from api.main import app as module_app

    assert isinstance(module_app, FastAPI)
    paths = {route.path for route in module_app.routes}
    assert "/api/health" in paths
    assert "/api/ideas/demo" in paths
    assert "/api/runs/{run_id}" in paths
    assert "/api/visuals/{visual_id}/svg" in paths


def test_openapi_json_200(client: TestClient):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    spec = response.json()
    assert spec["info"]["title"]
    assert "/api/projects" in spec["paths"]
    assert "CandidateOut" in spec["components"]["schemas"]
    assert "ErrorBody" in spec["components"]["schemas"]


def test_health_a_traves_de_la_app_real(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_preflight_cors_allowlist_sin_credenciales(client: TestClient):
    allowed = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert allowed.status_code == 200
    assert (
        allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
    )
    # allow_credentials=False (API-03): jamás reflejar credenciales
    assert allowed.headers.get("access-control-allow-credentials") in (None, "false")


def test_preflight_cors_origen_fuera_de_la_allowlist(client: TestClient):
    denied = client.options(
        "/api/health",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert "access-control-allow-origin" not in denied.headers


def test_seed_aplicado_al_primer_arranque_y_no_duplica_al_reiniciar(
    app: FastAPI, client: TestClient
):
    first = client.get("/api/projects").json()
    assert len(first) == 3  # seed del primer arranque (ADR-008)

    # "reinicio": un segundo TestClient sobre la MISMA DB vuelve a correr el
    # lifespan; el seed es idempotente (ContentProject ya no está vacío).
    with TestClient(app) as restarted:
        again = restarted.get("/api/projects").json()
        assert len(again) == 3
        assert [p["id"] for p in again] == [p["id"] for p in first]


def test_docs_solo_en_dev(client: TestClient):
    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 200


def test_docs_ocultos_en_prod(monkeypatch, db_file: Path):
    from api import dependencies

    monkeypatch.setenv("APP_ENV", "prod")
    monkeypatch.setenv("DATABASE_PATH", str(db_file))
    get_settings.cache_clear()
    monkeypatch.setattr(dependencies, "_engine", None)

    from api.main import create_app

    prod_app = create_app()
    with TestClient(prod_app) as prod_client:
        assert prod_client.get("/docs").status_code == 404
        assert prod_client.get("/redoc").status_code == 404
        # el contrato OpenAPI sigue disponible para el FE (ADR-003)
        assert prod_client.get("/openapi.json").status_code == 200
    get_settings.cache_clear()  # no polucionar el singleton para otros tests


def test_seed_es_idempotente_a_nivel_de_engine(db_file: Path):
    """Guard del ADR-008 sin HTTP: el seed no inserta si ya hay proyectos."""
    from db.seed import seed_demo_data
    from sqlmodel import Session

    engine = create_db_engine(db_file)
    create_all_tables(engine)
    with Session(engine) as session:
        assert seed_demo_data(session) == 3
        assert seed_demo_data(session) == 0  # segunda llamada: no duplica
