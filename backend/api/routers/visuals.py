"""Routers de visuales (G.4, design §5.4/§13.5).

Aprobación/rechazo humano del contrato visual (VIS-06) y serving del SVG.

``GET /api/visuals/{id}/svg`` resuelve el asset desde la DB (id), NUNCA desde
input del usuario (sin path traversal, design §13.5): si el visual ya tiene un
``svg_path`` persistido se sirve ese fichero (FileResponse sobre un path
proveniente de la DB); si aún no se materializó, se renderiza el SVG desde el
contrato persistido (función pura ``render_svg_string``, VIS-02). En ambos
casos la respuesta es ``image/svg+xml``.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse, Response
from sqlmodel import Session

from api import errors, schemas, workflow
from api.routers import ERROR_RESPONSES
from api.dependencies import get_session
from db import repos
from visual.svg import render_svg_string

router = APIRouter(prefix="/api", tags=["visuals"], responses=ERROR_RESPONSES)


@router.post("/visuals/{visual_id}/approve", response_model=schemas.VisualOut)
def approve_visual(
    visual_id: int,
    payload: schemas.ReasonIn,
    session: Session = Depends(get_session),
) -> schemas.VisualOut:
    """VISUAL_DRAFT → VISUAL_READY con aprobación humana razonada (VIS-06)."""
    return workflow.approve_visual(session, visual_id, payload.reason)


@router.post("/visuals/{visual_id}/reject", response_model=schemas.VisualOut)
def reject_visual(
    visual_id: int,
    payload: schemas.ReasonIn,
    session: Session = Depends(get_session),
) -> schemas.VisualOut:
    """VISUAL_DRAFT → VISUAL_REVISION_REQUIRED con razón (VIS-06)."""
    return workflow.reject_visual(session, visual_id, payload.reason)


@router.post("/visuals/{visual_id}/regenerate", response_model=schemas.VisualOut)
def regenerate_visual(
    visual_id: int,
    session: Session = Depends(get_session),
) -> schemas.VisualOut:
    """VISUAL_REVISION_REQUIRED → VISUAL_DRAFT (VIS-06)."""
    return workflow.regenerate_visual(session, visual_id)


@router.get("/visuals/{visual_id}/svg")
def visual_svg(
    visual_id: int,
    session: Session = Depends(get_session),
) -> Response:
    """SVG del visual — path desde la DB, nunca del usuario (§13.5)."""
    visual = repos.get_visual(session, visual_id)
    if visual is None:
        raise errors.NotFoundError(f"visual {visual_id} no existe")
    if visual.svg_path:
        return FileResponse(visual.svg_path, media_type="image/svg+xml")
    svg = render_svg_string(visual)
    return Response(content=svg, media_type="image/svg+xml")
