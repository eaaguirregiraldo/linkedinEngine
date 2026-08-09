"""Tests de los routers HTTP (G.4, design §5.4/§12/§13.5).

Criterio G.4 con TestClient + SQLite temporal:
- cada endpoint valida request/response contra los schemas (API-01);
- brief sin tesis → 422 ``VALIDATION_ERROR`` (API-01);
- aprobar sin evaluación → 409 accionable (API-04, FSM-02);
- doble generate → la segunda es rechazada SIN segunda ejecución (API-05, RNF-05);
- ``GET /api/visuals/{id}/svg`` responde ``image/svg+xml``;
- flujo completo vía HTTP termina ``SIMULATED_PUBLISHED`` con traza consultable
  (API-01, SIM-01).

El app de prueba monta los routers + handlers de error globales y reemplaza
``get_session`` por una sesión sobre SQLite temporal; el proveedor es
``DemoProvider`` (determinístico, sin red) y el harness real (G.4 no mockea
la generación/evaluación: el flujo completo vía HTTP es el criterio).
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import Session

from api import errors
from api.dependencies import get_session
from api.routers import candidates, meta, projects, runs, visuals
from db.engine import create_all_tables, create_db_engine


@pytest.fixture()
def client(db_file: Path):
    engine = create_db_engine(db_file)
    create_all_tables(engine)

    app = FastAPI()
    errors.register_exception_handlers(app)
    app.include_router(meta.router)
    app.include_router(projects.router)
    app.include_router(runs.router)
    app.include_router(candidates.router)
    app.include_router(visuals.router)

    def _override_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = _override_session
    with TestClient(app) as client:
        yield client


def _create_project(client: TestClient, raw_idea: str = "Idea demo de prueba") -> int:
    response = client.post("/api/projects", json={"raw_idea": raw_idea})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _brief_payload() -> dict:
    return {
        "thesis": (
            "Migrar COBOL no es traducir sintaxis; es recuperar conocimiento "
            "operativo antes de tocar código."
        ),
        "audience": "líderes de modernización",
        "objective": "plantear la migración como recuperación de conocimiento",
        "evidence": [
            {
                "id": "e1",
                "text": (
                    "El conocimiento operativo vive en reglas de negocio y "
                    "excepciones que rara vez están documentadas."
                ),
                "type": "known_facts",
            },
            {
                "id": "e2",
                "text": "La sintaxis es la parte más simple del sistema.",
                "type": "known_facts",
            },
        ],
        "constraints": ["No inventar cifras de empresas."],
    }


def _project_with_brief(client: TestClient) -> int:
    project_id = _create_project(client)
    response = client.post(f"/api/projects/{project_id}/brief", json=_brief_payload())
    assert response.status_code == 200, response.text
    return project_id


def _generated_run(client: TestClient) -> tuple[int, dict]:
    project_id = _project_with_brief(client)
    response = client.post(f"/api/projects/{project_id}/generate")
    assert response.status_code == 200, response.text
    run = response.json()
    assert len(run["candidates"]) == 3
    return project_id, run


# ── Meta y proyectos (API-01: contratos de request/response) ────────────────


def test_health_responde_contrato(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["provider"] == "demo"


def test_ideas_demo_devuelven_3_con_contrato(client: TestClient):
    response = client.get("/api/ideas/demo")
    assert response.status_code == 200
    ideas = response.json()
    assert len(ideas) == 3
    for idea in ideas:
        assert idea["id"]
        assert idea["raw_idea"]
        assert "default_audience" in idea
        assert "default_objective" in idea


def test_create_project_validates_schema(client: TestClient):
    response = client.post("/api/projects", json={"raw_idea": "   "})
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"


def test_brief_sin_tesis_es_422(client: TestClient):
    project_id = _create_project(client)
    payload = _brief_payload()
    payload["thesis"] = "   "
    response = client.post(f"/api/projects/{project_id}/brief", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_generate_sin_brief_es_409_accionable(client: TestClient):
    project_id = _create_project(client)
    response = client.post(f"/api/projects/{project_id}/generate")
    assert response.status_code == 409
    body = response.json()
    assert body["error"]["code"] == "STATE_TRANSITION_REJECTED"
    assert "brief" in body["error"]["message"].lower()


def test_listado_y_detalle_de_proyectos(client: TestClient):
    project_id = _project_with_brief(client)
    response = client.get("/api/projects")
    assert response.status_code == 200
    assert any(project["id"] == project_id for project in response.json())

    detail = client.get(f"/api/projects/{project_id}").json()
    assert detail["brief"]["thesis"]
    assert detail["voice_profile"]["provisional"] is True
    assert detail["status"] == "BRIEF_READY"


# ── Generación y API-05: doble envío rechazado sin segunda ejecución ────────


def test_doble_generate_es_rechazado_sin_segunda_ejecucion(client: TestClient):
    project_id, first_run = _generated_run(client)
    assert first_run["status"] == "GENERATED"

    second = client.post(f"/api/projects/{project_id}/generate")
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "STATE_TRANSITION_REJECTED"
    # la traza del proyecto sigue siendo la del primer run (API-05, RNF-05)
    trace = client.get(f"/api/runs/{first_run['id']}").json()
    assert trace["run"]["id"] == first_run["id"]


def test_aprobar_sin_evaluacion_es_409_accionable(client: TestClient):
    _, run = _generated_run(client)
    candidate_id = run["candidates"][0]["id"]
    response = client.post(
        f"/api/candidates/{candidate_id}/approve",
        json={"reason": "sin evaluación no se puede aprobar"},
    )
    assert response.status_code == 409
    body = response.json()
    assert body["error"]["code"] == "STATE_TRANSITION_REJECTED"
    assert body["error"]["message"]


# ── Flujo completo vía HTTP (API-01, SIM-01) ────────────────────────────────


def test_flujo_completo_via_http_termina_simulated_published(client: TestClient):
    project_id, run = _generated_run(client)
    run_id = run["id"]

    evaluation = client.post(f"/api/runs/{run_id}/evaluate")
    assert evaluation.status_code == 200, evaluation.text
    decision = evaluation.json()["decision"]
    assert decision["outcome"] in ("RECOMMENDED", "REVISION_REQUIRED")
    best = decision["best_candidate_id"]
    assert best is not None

    approved = client.post(
        f"/api/candidates/{best}/approve",
        json={"reason": "El ángulo elegido conecta con la audiencia."},
    )
    assert approved.status_code == 200
    assert approved.json()["decision"] == "APPROVED"

    visual = client.post(f"/api/candidates/{best}/visual")
    assert visual.status_code == 200
    visual_id = visual.json()["id"]
    assert visual.json()["status"] == "VISUAL_DRAFT"

    ready = client.post(
        f"/api/visuals/{visual_id}/approve",
        json={"reason": "El visual representa la tesis."},
    )
    assert ready.status_code == 200
    assert ready.json()["status"] == "VISUAL_READY"

    svg = client.get(f"/api/visuals/{visual_id}/svg")
    assert svg.status_code == 200
    assert svg.headers["content-type"].startswith("image/svg+xml")
    assert svg.text.lstrip().startswith("<svg")

    publication = client.post(f"/api/candidates/{best}/publish-simulated")
    assert publication.status_code == 200
    receipt = publication.json()["receipt"]
    assert receipt["status"] == "SIMULATED_PUBLISHED"
    assert receipt["mode"] == "simulated"
    assert receipt["remote_id"] is None
    assert receipt["notice"] == "no se envió contenido a LinkedIn"

    # traza consultable con la historia editorial completa (SIM-01, TRC-01);
    # RunOut.status es el ciclo de vida del RUN (GENERATED); el estado del
    # proyecto (FSM) llega a SIMULATED_PUBLISHED y se consulta por proyecto.
    trace = client.get(f"/api/runs/{run_id}")
    assert trace.status_code == 200
    detail = trace.json()
    assert detail["run"]["status"] == "GENERATED"
    project_state = client.get(f"/api/projects/{project_id}").json()
    assert project_state["status"] == "SIMULATED_PUBLISHED"
    event_types = {event["type"] for event in detail["trace_events"]}
    assert "publication_simulated" in event_types
    assert "evaluation_decision" in event_types
    assert any(
        candidate["decision"] == "APPROVED" for candidate in detail["run"]["candidates"]
    )
    assert detail["brief"]["thesis"]


def test_trace_de_run_inexistente_es_404(client: TestClient):
    response = client.get("/api/runs/9999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_visual_rechazado_se_regenera_y_exige_razon_para_aprobar(client: TestClient):
    _, run = _generated_run(client)
    evaluation = client.post(f"/api/runs/{run['id']}/evaluate").json()
    candidate_id = evaluation["decision"]["best_candidate_id"]
    client.post(
        f"/api/candidates/{candidate_id}/approve",
        json={"reason": "Selección editorial humana."},
    )
    visual = client.post(f"/api/candidates/{candidate_id}/visual").json()

    blank = client.post(f"/api/visuals/{visual['id']}/approve", json={"reason": "   "})
    assert blank.status_code == 422

    rejected = client.post(
        f"/api/visuals/{visual['id']}/reject",
        json={"reason": "La metáfora necesita revisión."},
    )
    assert rejected.json()["status"] == "VISUAL_REVISION_REQUIRED"

    regenerated = client.post(f"/api/visuals/{visual['id']}/regenerate")
    assert regenerated.status_code == 200
    assert regenerated.json()["id"] != visual["id"]
    assert regenerated.json()["status"] == "VISUAL_DRAFT"
