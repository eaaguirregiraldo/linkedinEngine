"""Routers de runs (G.4, design §5.4/§14).

- ``GET /api/runs/{run_id}``: traza completa SIEMPRE redactada (TRC-01/02) —
  events append-only del run + brief + voz.
- ``POST /api/runs/{run_id}/evaluate``: evalúa con el proveedor activo;
  idempotente si la evaluación sigue vigente (TRC-03/APPR-03); degrada a
  ``EVALUATION_PARTIAL`` (503) si el evaluador semántico no está disponible
  (HARN-08) sin fabricar un score completo.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlmodel import Session

from api import schemas, workflow
from api.routers import ERROR_RESPONSES
from api.dependencies import get_harness, get_provider, get_session

router = APIRouter(prefix="/api", tags=["runs"], responses=ERROR_RESPONSES)


@router.get("/runs/{run_id}", response_model=schemas.RunDetailOut)
def run_trace(run_id: int, session: Session = Depends(get_session)) -> schemas.RunDetailOut:
    """Traza del run, redactada antes de responder (TRC-02, RNF-04)."""
    return workflow.get_run_trace(session, run_id)


@router.post("/runs/{run_id}/evaluate", response_model=schemas.EvaluationOut)
def evaluate_run(
    run_id: int,
    session: Session = Depends(get_session),
    provider: Any = Depends(get_provider),
    harness: Any = Depends(get_harness),
) -> schemas.EvaluationOut:
    """GENERATED → RECOMMENDED | REVISION_REQUIRED | EVALUATION_PARTIAL."""
    return workflow.evaluate_run(session, run_id, provider, harness.run_evaluation)
