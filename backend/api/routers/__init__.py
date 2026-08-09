"""Routers HTTP (G.4, design §5.4).

Cada router delega en ``api.workflow`` (capa de aplicación) y declara
``response_model``/request pydantic del contrato canónico (ADR-003) para que
``/openapi.json`` sea la fuente del contrato FE.

``ERROR_RESPONSES`` documenta el envelope de error único (design §12, API-04)
en todos los endpoints: fuerza a ``ErrorBody``/``ErrorDetail`` dentro del
``/openapi.json``, de modo que el FE los tipee desde ``schema.d.ts`` (ADR-003)
y nunca a mano (H1.1).
"""
from __future__ import annotations

from api import schemas

ERROR_RESPONSES = {
    400: {
        "model": schemas.ErrorBody,
        "description": "VALIDATION_ERROR: el request no cumple el contrato",
    },
    404: {
        "model": schemas.ErrorBody,
        "description": "NOT_FOUND: proyecto/run/candidato/visual inexistente",
    },
    409: {
        "model": schemas.ErrorBody,
        "description": (
            "STATE_TRANSITION_REJECTED: transición FSM ilegal, "
            "con el requisito faltante en el mensaje"
        ),
    },
}
