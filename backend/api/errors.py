"""Manejo global de errores (design §12, `api` API-04).

Modelo de error único para FE y BE:

.. code-block:: json

    { "error": { "code": "...", "message": "...", "details": {} } }

``ErrorBody``/``ErrorDetail`` viven en ``api.schemas`` (ADR-003: schema
canónico); este módulo define las excepciones de API y registra los handlers
globales de FastAPI que convierten excepciones del dominio/API en ese envelope.

Mapeo (design §12):

| HTTP | Código                          | Caso                                   |
|------|---------------------------------|----------------------------------------|
| 400  | ``VALIDATION_ERROR``            | validación de dominio no cubierta por pydantic |
| 404  | ``NOT_FOUND``                   | proyecto/run/candidato/visual inexistente |
| 409  | ``STATE_TRANSITION_REJECTED``   | transición FSM ilegal (mensaje con el requisito faltante) |
| 422  | ``CONTRACT_INVALID``            | salida GenAI inválida tras repair (interno → ``GENERATION_FAILED``) |
| 502  | ``PROVIDER_UNAVAILABLE``        | proveedor remoto caído/timeout (P1); la UI sugiere DemoProvider, nunca conmuta sola |
| 503  | ``SEMANTIC_EVALUATION_UNAVAILABLE`` | evaluador semántico caído → ``EVALUATION_PARTIAL`` |

La validación pydantic del request (FastAPI ``RequestValidationError``) se
expone como 422 ``VALIDATION_ERROR`` con el detalle del campo fallido
(API-01) y nunca persiste estado parcial.
"""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from ai.providers import ProviderError
from api.schemas import ErrorBody, ErrorDetail

# Códigos del modelo de error único (design §12).
VALIDATION_ERROR = "VALIDATION_ERROR"
NOT_FOUND = "NOT_FOUND"
STATE_TRANSITION_REJECTED = "STATE_TRANSITION_REJECTED"
CONTRACT_INVALID = "CONTRACT_INVALID"
PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
SEMANTIC_EVALUATION_UNAVAILABLE = "SEMANTIC_EVALUATION_UNAVAILABLE"

_HTTP_STATUS_BY_CODE = {
    VALIDATION_ERROR: 400,
    NOT_FOUND: 404,
    STATE_TRANSITION_REJECTED: 409,
    CONTRACT_INVALID: 422,
    PROVIDER_UNAVAILABLE: 502,
    SEMANTIC_EVALUATION_UNAVAILABLE: 503,
}


class ApiError(Exception):
    """Base de errores de API estructurados (design §12).

    ``status_code``/``code`` definen el contrato HTTP; ``details`` es un mapa
    opcional con contexto accionable (nunca detalles internos sensibles).
    """

    code: str = VALIDATION_ERROR
    status_code: int = 400

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(ApiError):
    """400 — validación de dominio no cubierta por el schema pydantic."""

    code = VALIDATION_ERROR
    status_code = 400


class NotFoundError(ApiError):
    """404 — recurso inexistente (proyecto/run/candidato/visual)."""

    code = NOT_FOUND
    status_code = 404


class StateTransitionRejected(ApiError):
    """409 — transición FSM ilegal; mensaje con el requisito faltante."""

    code = STATE_TRANSITION_REJECTED
    status_code = 409


class ContractInvalid(ApiError):
    """422 — salida GenAI inválida tras repair (interno → GENERATION_FAILED).

    El workflow convierte este error en el estado ``GENERATION_FAILED`` del run
    (RNF-03: el brief queda intacto); el handler existe para exponerlo si
    escapa, sin representarlo como éxito.
    """

    code = CONTRACT_INVALID
    status_code = 422


class ProviderUnavailable(ApiError):
    """502 — proveedor remoto caído/timeout (P1)."""

    code = PROVIDER_UNAVAILABLE
    status_code = 502


class SemanticEvaluationUnavailable(ApiError):
    """503 — evaluador semántico caído → EVALUATION_PARTIAL."""

    code = SEMANTIC_EVALUATION_UNAVAILABLE
    status_code = 503


def _error_response(exc: ApiError) -> JSONResponse:
    body = ErrorBody(
        error=ErrorDetail(code=exc.code, message=exc.message, details=exc.details)
    )
    return JSONResponse(status_code=exc.status_code, content=body.model_dump())


async def _api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    return _error_response(exc)


async def _request_validation_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """422 con el detalle del campo fallido (API-01)."""
    fields = [
        {
            "loc": ".".join(str(part) for part in error.get("loc", ())),
            "msg": error.get("msg", ""),
        }
        for error in exc.errors()
    ]
    body = ErrorBody(
        error=ErrorDetail(
            code=VALIDATION_ERROR,
            message="el request no cumple el contrato: revisá los campos indicados",
            details={"fields": fields},
        )
    )
    return JSONResponse(status_code=422, content=body.model_dump())


async def _provider_error_handler(
    request: Request, exc: ProviderError
) -> JSONResponse:
    """502 normalizado: nunca exponer detalles internos del SDK al cliente.

    El código normalizado del provider (TRANSIENT/INVALID_OUTPUT/UNAVAILABLE)
    viaja en ``details`` como contexto accionable no sensible (design §13.2).
    """
    body = ErrorBody(
        error=ErrorDetail(
            code=PROVIDER_UNAVAILABLE,
            message=exc.message or "el proveedor de IA no está disponible",
            details={
                "code": exc.code,
                "action": "revisá .env (GENAI_PROVIDER y OPENAI_API_KEY), reiniciá el backend "
                "o elegí DemoProvider explícitamente",
            },
        )
    )
    return JSONResponse(status_code=502, content=body.model_dump())


async def _http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Normaliza cualquier HTTPException de Starlette al envelope único.

    Mapea los códigos del modelo de error (design §12); para el resto usa un
    código genérico honesto según la clase del status, sin exponer detalles
    internos (design §13.2).
    """
    code = _CODE_BY_HTTP.get(exc.status_code, _GENERIC_CODE_BY_HTTP.get(exc.status_code, "INTERNAL_ERROR"))
    message = exc.detail if isinstance(exc.detail, str) else "solicitud rechazada"
    body = ErrorBody(error=ErrorDetail(code=code, message=message, details={}))
    return JSONResponse(status_code=exc.status_code, content=body.model_dump())


_CODE_BY_HTTP = {value: key for key, value in _HTTP_STATUS_BY_CODE.items()}

# Códigos genéricos honestos para HTTPException fuera del modelo §12 (p. ej.
# 405 de FastAPI para método no permitido). No reemplazan el modelo único:
# cubren casos de framework que el dominio nunca emite.
_GENERIC_CODE_BY_HTTP = {405: "METHOD_NOT_ALLOWED"}


def register_exception_handlers(app: FastAPI) -> None:
    """Registra los handlers globales de error en la app FastAPI (design §12).

    Llamar en ``main.py`` al construir la aplicación. Los handlers de clases
    base (``ApiError``) capturan también sus subclases vía MRO de Starlette.
    """
    app.add_exception_handler(ApiError, _api_error_handler)
    app.add_exception_handler(RequestValidationError, _request_validation_handler)
    app.add_exception_handler(ProviderError, _provider_error_handler)
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)


__all__ = [
    "ApiError",
    "CONTRACT_INVALID",
    "ContractInvalid",
    "NOT_FOUND",
    "NotFoundError",
    "PROVIDER_UNAVAILABLE",
    "ProviderUnavailable",
    "SEMANTIC_EVALUATION_UNAVAILABLE",
    "SemanticEvaluationUnavailable",
    "STATE_TRANSITION_REJECTED",
    "StateTransitionRejected",
    "VALIDATION_ERROR",
    "ValidationError",
    "register_exception_handlers",
]
