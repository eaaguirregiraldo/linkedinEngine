"""Interfaz `GenAIProvider` y errores tipados (design §6.2, HARN-02).

Los providers NUNCA implementan retry/repair: eso vive en el harness (ADR-005,
HARN-05). Devuelven la salida cruda del modelo (JSON como texto) y el harness la
valida contra el schema canónico pydantic (HARN-04) y la repara si hace falta.
Los errores de SDK/red se normalizan a `ProviderError` con un `code` cerrado,
sin exponer detalles internos.
"""
from __future__ import annotations

from typing import Any, Protocol, Sequence, runtime_checkable

from api.schemas import BriefIn

# Códigos de error normalizados (design §6.2).
TRANSIENT = "TRANSIENT"
INVALID_OUTPUT = "INVALID_OUTPUT"
UNAVAILABLE = "UNAVAILABLE"


class ProviderError(Exception):
    """Error de provider normalizado (código + mensaje accionable).

    ``code`` ∈ {TRANSIENT, INVALID_OUTPUT, UNAVAILABLE}; ``details`` es un mapa
    opcional con contexto no sensible (nunca credenciales ni cabeceras).
    """

    def __init__(
        self,
        code: str,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


@runtime_checkable
class GenAIProvider(Protocol):
    """Contrato de provider GenAI (design §6.2, HARN-02).

    - ``name``: etiqueta para UI y traza ("DEMO_PROVIDER", "openai-compatible").
    - ``model``: modelo usado (None en demo determinística).
    - ``params``: parámetros relevantes para la traza (p. ej. temperature).
    - ``generate_candidates``: salida cruda JSON de generación (contrato HARN-04).
    - ``evaluate_candidates``: salida cruda JSON de evaluación (mismo contrato API).
    """

    name: str
    model: str | None
    params: dict[str, Any]

    def generate_candidates(self, brief: BriefIn) -> str:
        """Devuelve el JSON crudo de generación (``GenerationOutput``)."""

    def evaluate_candidates(
        self,
        candidates: Sequence[Any],
        brief: BriefIn,
        catalog_version: str,
    ) -> str:
        """Devuelve el JSON crudo de evaluación (``EvaluationOutput``).

        ``catalog_version`` es la versión del catálogo de clichés usado por el
        harness (VOI-06); el provider la contrasta con la suya si aplica.
        """


__all__ = [
    "INVALID_OUTPUT",
    "TRANSIENT",
    "UNAVAILABLE",
    "GenAIProvider",
    "ProviderError",
]
