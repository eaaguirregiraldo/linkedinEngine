"""Tests del manejo global de errores (G.1, design §12, `api` API-04).

Criterio de G.1: test de handlers — cada código mapea al body estructurado
``ErrorBody`` con mensaje accionable. Cubre los 6 códigos del modelo de error
único (400/404/409/422/502/503) y la validación pydantic (API-01: 422 con
detalle del campo fallido).
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ai.providers import ProviderError, UNAVAILABLE
from api import errors
from api.schemas import BriefIn, ErrorBody


def _probe_app() -> FastAPI:
    """App de prueba: registra los handlers globales y expone rutas que
    lanzan cada error del modelo (design §12)."""
    app = FastAPI()
    errors.register_exception_handlers(app)

    @app.get("/probe/validation")
    def _validation() -> None:
        raise errors.ValidationError(
            "la tesis es obligatoria", details={"field": "thesis"}
        )

    @app.get("/probe/not-found")
    def _not_found() -> None:
        raise errors.NotFoundError(
            "no existe el proyecto solicitado", details={"resource": "project"}
        )

    @app.get("/probe/transition")
    def _transition() -> None:
        raise errors.StateTransitionRejected(
            "APROBAR no está permitido desde GENERATED: "
            "primero se necesita una evaluación (START_EVALUATION)",
            details={"current_state": "GENERATED", "event": "APPROVE"},
        )

    @app.get("/probe/contract")
    def _contract() -> None:
        raise errors.ContractInvalid(
            "la salida del modelo no cumple el contrato tras la reparación",
            details={"state": "GENERATION_FAILED"},
        )

    @app.get("/probe/provider")
    def _provider() -> None:
        raise errors.ProviderUnavailable(
            "el proveedor de IA no está disponible: reintentá más tarde "
            "o activá el proveedor demo",
        )

    @app.get("/probe/semantic")
    def _semantic() -> None:
        raise errors.SemanticEvaluationUnavailable(
            "el evaluador semántico no está disponible: la evaluación "
            "queda en EVALUATION_PARTIAL con solo chequeos determinísticos",
        )

    @app.get("/probe/provider-error")
    def _provider_error() -> None:
        raise ProviderError(UNAVAILABLE, "provider caído")

    @app.post("/probe/brief")
    def _brief(body: BriefIn) -> dict:
        return {"received": body.model_dump()}

    return app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(_probe_app())


@pytest.mark.parametrize(
    ("path", "status", "code"),
    [
        ("/probe/validation", 400, "VALIDATION_ERROR"),
        ("/probe/not-found", 404, "NOT_FOUND"),
        ("/probe/transition", 409, "STATE_TRANSITION_REJECTED"),
        ("/probe/contract", 422, "CONTRACT_INVALID"),
        ("/probe/provider", 502, "PROVIDER_UNAVAILABLE"),
        ("/probe/semantic", 503, "SEMANTIC_EVALUATION_UNAVAILABLE"),
    ],
)
def test_each_code_maps_to_structured_body(
    client: TestClient, path: str, status: int, code: str
) -> None:
    """Cada código del modelo de error mapea al envelope ``ErrorBody``."""
    response = client.get(path)
    assert response.status_code == status

    body = response.json()
    assert body["error"]["code"] == code
    assert body["error"]["message"].strip()  # mensaje accionable
    assert isinstance(body["error"]["details"], dict)

    # El envelope valida contra el contrato canónico (ADR-003).
    parsed = ErrorBody.model_validate(body)
    assert parsed.error.code == code


def test_transition_rejected_message_cites_missing_requirement(
    client: TestClient,
) -> None:
    """409: el mensaje explica el requisito faltante (API-04, G.1)."""
    response = client.get("/probe/transition")
    body = response.json()
    assert body["error"]["code"] == "STATE_TRANSITION_REJECTED"
    assert "evaluación" in body["error"]["message"]


def test_not_found_message_does_not_expose_internals(client: TestClient) -> None:
    """404: mensaje estable sin detalles internos de implementación (API-04)."""
    response = client.get("/probe/not-found")
    body = response.json()
    assert body["error"]["code"] == "NOT_FOUND"
    assert "sql" not in body["error"]["message"].lower()
    assert "traceback" not in body["error"]["message"].lower()


def test_pydantic_validation_error_returns_422_with_field_detail(
    client: TestClient,
) -> None:
    """API-01: request que viola el contrato → 422 con detalle del campo
    fallido, sin estado parcial."""
    response = client.post("/probe/brief", json={})
    assert response.status_code == 422

    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["message"].strip()
    # detalle del campo fallido (loc del error pydantic)
    assert body["error"]["details"]["fields"]


def test_provider_error_normalized_to_502(client: TestClient) -> None:
    """ProviderError del ecosistema GenAI se normaliza a 502
    PROVIDER_UNAVAILABLE (nunca detalles internos del SDK)."""
    response = client.get("/probe/provider-error")
    assert response.status_code == 502
    body = response.json()
    assert body["error"]["code"] == "PROVIDER_UNAVAILABLE"
    assert body["error"]["message"].strip()
