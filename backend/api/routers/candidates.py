"""Routers de candidatos (G.4, design §5.4).

Generación, edición humana, revisión, aprobación, visual y publicación
simulada. La FSM corre ANTES de persistir (design §1, FSM-01): las
transiciones ilegales devuelven 409 ``STATE_TRANSITION_REJECTED`` con el
requisito faltante, sin corromper estado (p. ej. doble generate).
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlmodel import Session

from api import schemas, workflow
from api.routers import ERROR_RESPONSES
from api.dependencies import get_harness, get_provider, get_session

router = APIRouter(prefix="/api", tags=["candidates"], responses=ERROR_RESPONSES)


@router.post("/projects/{project_id}/generate", response_model=schemas.RunOut)
def generate(
    project_id: int,
    session: Session = Depends(get_session),
    provider: Any = Depends(get_provider),
    harness: Any = Depends(get_harness),
) -> schemas.RunOut:
    """BRIEF_READY → GENERATING → GENERATED | GENERATION_FAILED (RF-02)."""
    return workflow.generate(session, project_id, provider, harness.run_generation)


@router.post("/projects/{project_id}/retry-generate", response_model=schemas.RunOut)
def retry_generate(
    project_id: int,
    session: Session = Depends(get_session),
    provider: Any = Depends(get_provider),
    harness: Any = Depends(get_harness),
) -> schemas.RunOut:
    """GENERATION_FAILED → GENERATING → GENERATED (RNF-03: run NUEVO)."""
    return workflow.retry_generate(session, project_id, provider, harness.run_generation)


@router.post("/candidates/{candidate_id}/edit", response_model=schemas.CandidateOut)
def edit_candidate(
    candidate_id: int,
    payload: schemas.CandidateEdit,
    session: Session = Depends(get_session),
) -> schemas.CandidateOut:
    """Edición humana: invalida evaluación/visual (APPR-02/03, FSM-03)."""
    return workflow.edit_candidate(session, candidate_id, payload.content)


@router.post(
    "/candidates/{candidate_id}/request-revision",
    response_model=schemas.CandidateOut,
)
def request_revision(
    candidate_id: int,
    payload: schemas.ReasonIn,
    session: Session = Depends(get_session),
) -> schemas.CandidateOut:
    """RECOMMENDED → REVISION_REQUIRED con razón editorial (APPR-01)."""
    return workflow.request_revision(session, candidate_id, payload.reason)


@router.post("/candidates/{candidate_id}/approve", response_model=schemas.CandidateOut)
def approve_candidate(
    candidate_id: int,
    payload: schemas.ReasonIn,
    session: Session = Depends(get_session),
) -> schemas.CandidateOut:
    """Aprobación humana con razón; sin blockers activos (APPR-01)."""
    return workflow.approve_candidate(session, candidate_id, payload.reason)


@router.post("/candidates/{candidate_id}/visual", response_model=schemas.VisualOut)
def generate_visual(
    candidate_id: int,
    session: Session = Depends(get_session),
) -> schemas.VisualOut:
    """APPROVED → VISUAL_DRAFT (contrato derivado de la tesis, VIS-01/03)."""
    return workflow.generate_visual(session, candidate_id)


@router.post(
    "/candidates/{candidate_id}/publish-simulated",
    response_model=schemas.PublicationOut,
)
def publish_simulated(
    candidate_id: int,
    session: Session = Depends(get_session),
) -> schemas.PublicationOut:
    """VISUAL_READY → SIMULATED_PUBLISHED (SIM-01/02/04; recibo local)."""
    return workflow.simulate_publish(session, candidate_id)
