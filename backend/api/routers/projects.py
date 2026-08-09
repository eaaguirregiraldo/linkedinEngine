"""Routers de proyectos e ideas demo (G.4, design §5.4).

- ``GET /api/ideas/demo``: las 3 ideas demo del seed (design §9.3) como
  ``DemoIdeaOut`` — el FE las ofrece en el paso 1 del wizard (CAP-01).
- ``POST /api/projects``: crea un proyecto en estado ``IDEA`` (CAP-01).
- ``POST /api/projects/{id}/brief``: captura el brief → ``BRIEF_READY``
  (guard de la FSM exige tesis única + al menos una evidencia).
- ``GET /api/projects/{id}``: detalle con brief y perfil de voz v0.
- ``GET /api/projects``: historial (P1-ready).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session

from api import schemas, workflow
from api.routers import ERROR_RESPONSES
from api.dependencies import get_session
from db.seed import DEMO_IDEAS

router = APIRouter(prefix="/api", tags=["projects"], responses=ERROR_RESPONSES)


@router.get("/ideas/demo", response_model=list[schemas.DemoIdeaOut])
def list_demo_ideas() -> list[schemas.DemoIdeaOut]:
    """Ideas demo del seed (design §9.3) — sin tocar la DB."""
    return [
        schemas.DemoIdeaOut(
            id=idea["id"],
            raw_idea=idea["raw_idea"],
            default_audience=idea.get("audience", ""),
            default_objective=idea.get("objective", ""),
        )
        for idea in DEMO_IDEAS
    ]


@router.post("/projects", response_model=schemas.ProjectOut, status_code=201)
def create_project(
    payload: schemas.ProjectCreate,
    session: Session = Depends(get_session),
) -> schemas.ProjectOut:
    """Crea un proyecto en estado ``IDEA`` (CAP-01)."""
    project = workflow.create_project(session, payload.raw_idea, payload.title)
    return schemas.ProjectOut(
        id=project.id,
        raw_idea=project.raw_idea,
        title=project.title,
        status=project.status,
        created_at=project.created_at.isoformat(),
        updated_at=project.updated_at.isoformat(),
    )


@router.post("/projects/{project_id}/brief", response_model=schemas.ProjectOut)
def submit_brief(
    project_id: int,
    payload: schemas.BriefIn,
    session: Session = Depends(get_session),
) -> schemas.ProjectOut:
    """Captura el brief (transición IDEA → BRIEF_READY; guard CAP-02/03)."""
    project = workflow.submit_brief(session, project_id, payload)
    return schemas.ProjectOut(
        id=project.id,
        raw_idea=project.raw_idea,
        title=project.title,
        status=project.status,
        created_at=project.created_at.isoformat(),
        updated_at=project.updated_at.isoformat(),
    )


@router.get("/projects/{project_id}", response_model=schemas.ProjectDetailOut)
def project_detail(
    project_id: int,
    session: Session = Depends(get_session),
) -> schemas.ProjectDetailOut:
    """Detalle del proyecto: brief, estado y voz aplicada (§5.4)."""
    return workflow.get_project_detail(session, project_id)


@router.get("/projects", response_model=list[schemas.ProjectOut])
def list_projects(session: Session = Depends(get_session)) -> list[schemas.ProjectOut]:
    """Historial de proyectos (P1-ready, design §5.4)."""
    return workflow.list_projects(session)
