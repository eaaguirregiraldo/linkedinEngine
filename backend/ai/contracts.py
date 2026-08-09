# backend/ai/contracts.py
"""Contratos de salida GenAI.

Reutiliza los modelos canónicos de ``api.schemas``: el mismo schema que valida
la salida del provider es el del contrato API (design §5.1, ADR-003, HARN-04).
No hay redefinición: estos nombres son la MISMA clase (test de identidad, C.2).
"""

from api.schemas import (
    Blocker,
    CandidateOutput,
    CandidateScore,
    DimensionRatings,
    DimensionScore,
    EvaluationOutput,
    GenerationOutput,
    Penalties,
)

__all__ = [
    "Blocker",
    "CandidateOutput",
    "CandidateScore",
    "DimensionRatings",
    "DimensionScore",
    "EvaluationOutput",
    "GenerationOutput",
    "Penalties",
]
