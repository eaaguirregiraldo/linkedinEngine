"""Repos finos por agregado sobre SQLModel (D.3, design §9.1/§9.2, ADR-002).

Reglas transversales:
- **Traza append-only (TRC-03):** los repos NO exponen mutación de
  ``trace_events``; solo ``append_trace_event``. Las correcciones se registran
  como eventos nuevos.
- **Edición con invalidación (invariante 1, §9.2):** ``bump_candidate_version``
  incrementa ``content_version`` y deja la evaluación actual en ``None``; la
  evaluación previa permanece consultable vía ``trace_events`` (TRC-03).
- **Publicación simulada (invariante 5):** ``save_publication_attempt`` fija
  ``mode="simulated"`` y ``remote_id=None`` siempre.
- **Sin secretos (PST-02):** los repos persisten datos ya redactados por el
  workflow/harness; no existe columna de credenciales.
- **Ejecución fallida (invariante 4):** el run conserva error + traza y no se
  crean candidatos incompletos como válidos (el workflow no los agrega).
"""
from __future__ import annotations

from typing import Any, Iterable, Optional

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from db.models import (
    Candidate,
    ContentProject,
    GenerationRun,
    PublicationAttempt,
    VisualAsset,
    utcnow,
)

__all__ = [
    "create_project",
    "get_project",
    "set_project_status",
    "set_project_brief",
    "list_projects",
    "create_run",
    "get_run",
    "append_trace_event",
    "complete_run",
    "add_candidates",
    "get_candidate",
    "list_candidates_for_run",
    "update_candidate_evaluation",
    "append_decision",
    "bump_candidate_version",
    "update_candidate_content",
    "save_visual",
    "get_visual",
    "get_latest_visual_for_candidate",
    "update_visual_status",
    "save_publication_attempt",
    "get_publication_for_candidate",
    "get_run_detail",
]


# ── ContentProject ─────────────────────────────────────────────────────────


def create_project(
    session: Session, raw_idea: str, title: Optional[str] = None
) -> ContentProject:
    """Crea un proyecto en estado ``IDEA`` (CAP-01)."""
    project = ContentProject(raw_idea=raw_idea, title=title, status="IDEA")
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


def get_project(session: Session, project_id: int) -> Optional[ContentProject]:
    return session.get(ContentProject, project_id)


def set_project_status(
    session: Session, project_id: int, status: str
) -> Optional[ContentProject]:
    """Actualiza el estado FSM del proyecto (la autorización la hace el workflow).

    Muta la MISMA instancia del identity map y la refresca: cualquier
    referencia previa al proyecto ve el nuevo estado (los tests del workflow
    verifican ``project.status`` sobre la instancia que ellos crearon).
    """
    project = get_project(session, project_id)
    if project is None:
        return None
    project.status = status
    project.updated_at = utcnow()
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


def set_project_brief(
    session: Session, project_id: int, brief: dict[str, Any]
) -> Optional[ContentProject]:
    """Persiste el brief del proyecto (la validez la gobierna el guard FSM).

    Muta la instancia del identity map y la refresca (mismo criterio que
    ``set_project_status``): las referencias previas ven el brief nuevo.
    """
    project = get_project(session, project_id)
    if project is None:
        return None
    project.brief = brief
    project.updated_at = utcnow()
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


def list_projects(session: Session) -> list[ContentProject]:
    """Lista proyectos (P1-ready: historial navegable; design §5.4)."""
    statement = select(ContentProject).order_by(ContentProject.updated_at.desc())
    return list(session.exec(statement))


# ── GenerationRun ──────────────────────────────────────────────────────────


def create_run(
    session: Session,
    project_id: int,
    provider: str,
    prompt_version: str,
    schema_version: str,
    prompt_hash: str,
    model: Optional[str] = None,
) -> GenerationRun:
    """Abre un run en estado ``GENERATING``."""
    run = GenerationRun(
        project_id=project_id,
        status="GENERATING",
        provider=provider,
        model=model,
        prompt_version=prompt_version,
        schema_version=schema_version,
        prompt_hash=prompt_hash,
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def get_run(session: Session, run_id: int) -> Optional[GenerationRun]:
    return session.get(GenerationRun, run_id)


def append_trace_event(
    session: Session, run_id: int, event: dict[str, Any]
) -> Optional[GenerationRun]:
    """Agrega un evento a ``trace_events``. Append-only (TRC-03): no existe
    API de repos para modificar o eliminar eventos ya persistidos."""
    run = get_run(session, run_id)
    if run is None:
        return None
    events = list(run.trace_events or [])
    events.append(event)
    run.trace_events = events
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def complete_run(
    session: Session,
    run_id: int,
    status: str,
    error_code: Optional[str] = None,
    raw_output: Optional[str] = None,
    *,
    prompt_version: Optional[str] = None,
    schema_version: Optional[str] = None,
    prompt_hash: Optional[str] = None,
) -> Optional[GenerationRun]:
    """Cierra el run (GENERATED | GENERATION_FAILED).

    Una ejecución fallida conserva error + traza (invariante 4): se setea
    ``error_code`` y se mantiene intacto ``trace_events``. ``raw_output`` solo
    se persiste si el harness lo decide (TRACE_STORE_RAW_OUTPUT=true).
    Los metadatos de prompt (versión/schema/hash) se fijan al cerrar el run:
    el harness los resuelve DURANTE la ejecución (el workflow los propaga).
    """
    run = get_run(session, run_id)
    if run is None:
        return None
    run.status = status
    run.error_code = error_code
    run.completed_at = utcnow()
    if raw_output is not None:
        run.raw_output = raw_output
    if prompt_version is not None:
        run.prompt_version = prompt_version
    if schema_version is not None:
        run.schema_version = schema_version
    if prompt_hash is not None:
        run.prompt_hash = prompt_hash
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


# ── Candidate ──────────────────────────────────────────────────────────────


def add_candidates(
    session: Session, run_id: int, candidates: Iterable[dict[str, Any]]
) -> list[Candidate]:
    """Persiste los candidatos de un run (content_version=1).

    Invariante 6 (§9.2): ``angle`` único por run. Si se intenta duplicar, la
    constraint ``uq_candidate_run_angle`` rechaza el commit y el repo eleva un
    ``ValueError`` sin dejar el run a medias.
    """
    rows: list[Candidate] = []
    for item in candidates:
        rows.append(
            Candidate(
                run_id=run_id,
                angle=item["angle"],
                hook=item["hook"],
                body=item["body"],
                cta=item["cta"],
                claims=list(item.get("claims", [])),
                content_version=1,
            )
        )
    for row in rows:
        session.add(row)
    try:
        session.commit()
    except IntegrityError as exc:  # angle duplicado en el mismo run
        session.rollback()
        raise ValueError(
            f"angle duplicado en run {run_id}: invariante §9.2 (único por run)"
        ) from exc
    for row in rows:
        session.refresh(row)
    return rows


def get_candidate(session: Session, candidate_id: int) -> Optional[Candidate]:
    return session.get(Candidate, candidate_id)


def list_candidates_for_run(session: Session, run_id: int) -> list[Candidate]:
    statement = select(Candidate).where(Candidate.run_id == run_id).order_by(Candidate.id)
    return list(session.exec(statement))


def update_candidate_evaluation(
    session: Session, candidate_id: int, evaluation: dict[str, Any]
) -> Optional[Candidate]:
    """Fija la evaluación ACTUAL del candidato (dimensiones + score)."""
    candidate = get_candidate(session, candidate_id)
    if candidate is None:
        return None
    candidate.evaluation = evaluation
    session.add(candidate)
    session.commit()
    session.refresh(candidate)
    return candidate


def append_decision(
    session: Session, candidate_id: int, decision: dict[str, Any]
) -> Optional[Candidate]:
    """Registra una decisión en ``decision_history`` (append-only)."""
    candidate = get_candidate(session, candidate_id)
    if candidate is None:
        return None
    history = list(candidate.decision_history or [])
    history.append(decision)
    candidate.decision_history = history
    session.add(candidate)
    session.commit()
    session.refresh(candidate)
    return candidate


def bump_candidate_version(
    session: Session, candidate_id: int
) -> Optional[Candidate]:
    """Edición humana (CANDIDATE_EDITED, invariante 1, §9.2).

    Incrementa ``content_version`` e invalida la evaluación actual (None);
    la selección deja de estar vigente. La evaluación previa queda conservada
    en ``trace_events`` (append-only, TRC-03).
    """
    candidate = get_candidate(session, candidate_id)
    if candidate is None:
        return None
    candidate.content_version += 1
    candidate.evaluation = None
    candidate.selected = False
    session.add(candidate)
    session.commit()
    session.refresh(candidate)
    return candidate


def update_candidate_content(
    session: Session,
    candidate_id: int,
    *,
    hook: str,
    body: str,
    cta: str,
) -> Optional[Candidate]:
    """Aplica el contenido editado por el humano (APPR-02, design §5.4).

    Solo el contenido (hook/body/cta); la invalidación de evaluación y el
    ``content_version`` los maneja ``bump_candidate_version`` (el workflow
    los coordina en el orden correcto dentro de la transición FSM).
    """
    candidate = get_candidate(session, candidate_id)
    if candidate is None:
        return None
    candidate.hook = hook
    candidate.body = body
    candidate.cta = cta
    session.add(candidate)
    session.commit()
    session.refresh(candidate)
    return candidate


# ── VisualAsset ────────────────────────────────────────────────────────────


def save_visual(
    session: Session,
    candidate_id: int,
    *,
    thesis: str,
    concept: str,
    elements: list[dict[str, Any]],
    alt_text: str,
    svg_path: Optional[str] = None,
) -> VisualAsset:
    """Crea el visual en estado ``VISUAL_DRAFT`` (VIS-06: aprobación humana)."""
    visual = VisualAsset(
        candidate_id=candidate_id,
        thesis=thesis,
        concept=concept,
        elements=list(elements),
        alt_text=alt_text,
        svg_path=svg_path,
        status="VISUAL_DRAFT",
    )
    session.add(visual)
    session.commit()
    session.refresh(visual)
    return visual


def get_visual(session: Session, visual_id: int) -> Optional[VisualAsset]:
    return session.get(VisualAsset, visual_id)


def get_latest_visual_for_candidate(
    session: Session, candidate_id: int
) -> Optional[VisualAsset]:
    """Último visual del candidato (SIM-04: la simulación lo exige VISUAL_READY)."""
    statement = (
        select(VisualAsset)
        .where(VisualAsset.candidate_id == candidate_id)
        .order_by(VisualAsset.id.desc())
    )
    return session.exec(statement).first()


def update_visual_status(
    session: Session, visual_id: int, status: str
) -> Optional[VisualAsset]:
    visual = get_visual(session, visual_id)
    if visual is None:
        return None
    visual.status = status
    session.add(visual)
    session.commit()
    session.refresh(visual)
    return visual


# ── PublicationAttempt ─────────────────────────────────────────────────────


def save_publication_attempt(
    session: Session,
    candidate_id: int,
    *,
    status: str = "SIMULATED_PUBLISHED",
    receipt: dict[str, Any],
) -> PublicationAttempt:
    """Persiste un intento de publicación SIMULADO.

    Invariante 5 (§9.2, ADR-007): ``mode="simulated"`` y ``remote_id=None``
    siempre — jamás un ID remoto inventado (SIM-02, RNF-02).
    """
    attempt = PublicationAttempt(
        candidate_id=candidate_id,
        mode="simulated",
        status=status,
        remote_id=None,
        receipt=receipt,
    )
    session.add(attempt)
    session.commit()
    session.refresh(attempt)
    return attempt


def get_publication_for_candidate(
    session: Session, candidate_id: int
) -> Optional[PublicationAttempt]:
    statement = (
        select(PublicationAttempt)
        .where(PublicationAttempt.candidate_id == candidate_id)
        .order_by(PublicationAttempt.id.desc())
    )
    return session.exec(statement).first()


# ── Run detail (traza ensamblable) ─────────────────────────────────────────


def get_run_detail(session: Session, run_id: int) -> Optional[dict[str, Any]]:
    """Run + candidatos + visuales + publicación por candidato.

    El workflow (G.3) ensambla la traza a partir de este detalle junto con
    ``evaluation``/``decision_history``/``receipt`` (design §14).
    """
    run = get_run(session, run_id)
    if run is None:
        return None
    candidates = list_candidates_for_run(session, run_id)
    visuals: dict[int, VisualAsset] = {}
    publications: dict[int, PublicationAttempt] = {}
    for candidate in candidates:
        visual = session.exec(
            select(VisualAsset)
            .where(VisualAsset.candidate_id == candidate.id)
            .order_by(VisualAsset.id.desc())
        ).first()
        if visual is not None:
            visuals[candidate.id] = visual
        publication = get_publication_for_candidate(session, candidate.id)
        if publication is not None:
            publications[candidate.id] = publication
    return {
        "run": run,
        "candidates": candidates,
        "visuals": visuals,
        "publications": publications,
    }
