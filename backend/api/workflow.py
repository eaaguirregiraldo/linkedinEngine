"""Capa de aplicación (G.3, design §14): orquesta FSM + repos + harness.

Cada operación:
1. Verifica la transición FSM sobre el estado del proyecto (contexto con el
   dato requerido). Si la FSM rechaza, lanza ``StateTransitionRejected`` (409)
   SIN persistir nada (FSM-01: sin corrupción).
2. Persiste vía repos (``db.repos``), manteniendo el ``status`` del proyecto
   sincronizado con la FSM tras cada operación.
3. Registra la traza append-only del run (TRC-03) con ``build_trace_event``;
   la traza se sirve SIEMPRE redactada (TRC-02, RNF-04).

Contrato con los tests (G.3): las funciones reciben el provider y la función
del harness (``run_generation``/``run_evaluation``) por inyección — el módulo
no construye proveedores ni importa el harness en el import-time.
"""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Sequence

from sqlmodel import Session

from api import errors, schemas
from db import repos
from db.models import ContentProject, GenerationRun
from domain import fsm
from visual.contract import build_visual_contract

from core.trace import build_trace_event, redact_secrets


def _load_project_or_404(session: Session, project_id: int) -> ContentProject:
    project = repos.get_project(session, project_id)
    if project is None:
        raise errors.NotFoundError(f"proyecto {project_id} no existe")
    return project


def _load_run_or_404(session: Session, run_id: int) -> GenerationRun:
    run = repos.get_run(session, run_id)
    if run is None:
        raise errors.NotFoundError(f"run {run_id} no existe")
    return run


def _project_for_candidate(session: Session, candidate_id: int) -> ContentProject:
    run = _load_run_or_404(session, repos.get_candidate(session, candidate_id).run_id)
    return _load_project_or_404(session, run.project_id)


def _apply_transition(
    session: Session,
    project_id: int,
    event: str,
    ctx: fsm.FsmContext | None = None,
) -> str:
    """Aplica la transición FSM y persiste el nuevo estado del proyecto.

    Devuelve el estado destino. La FSM ya ejecutó los guards: si el evento no
    está permitido desde el estado actual o el guard falla, lanza
    ``StateTransitionRejected`` antes de tocar la DB (FSM-01).
    """
    project = _load_project_or_404(session, project_id)
    result = fsm.apply(project.status, event, ctx)
    if not result.ok:
        raise errors.StateTransitionRejected(
            result.reason or f"transicion {event} rechazada desde {project.status}"
        )
    updated = repos.set_project_status(session, project_id, result.state)
    return updated.status


def _candidate_out(candidate: Any) -> schemas.CandidateOut:
    evaluation = candidate.evaluation
    evaluation_summary: schemas.EvaluationSummary | None = None
    if evaluation:
        evaluation_summary = schemas.EvaluationSummary(
            score_final=evaluation.get("score_final", 0),
            decision=evaluation.get("decision"),
        )
    # Decisión vigente: la ÚLTIMA entrada del historial append-only pesa más
    # (p. ej. REVISION_REQUIRED por pedido humano, APPROVED); si aún no hay
    # historial, se cae a la decisión de la última evaluación.
    history = list(candidate.decision_history or [])
    decision: str | None = None
    if history:
        decision = history[-1].get("decision")
    elif evaluation:
        decision = evaluation.get("decision")
    return schemas.CandidateOut(
        id=candidate.id,
        angle=candidate.angle,
        hook=candidate.hook,
        body=candidate.body,
        cta=candidate.cta,
        claims=list(candidate.claims or []),
        content_version=candidate.content_version,
        evaluation=evaluation_summary,
        decision=decision,
    )


def _run_out(run: GenerationRun, candidates: Sequence[Any]) -> schemas.RunOut:
    rows = candidates
    return schemas.RunOut(
        id=run.id,
        project_id=run.project_id,
        status=run.status,
        provider=run.provider,
        model=run.model,
        prompt_version=run.prompt_version,
        schema_version=run.schema_version,
        prompt_hash=run.prompt_hash,
        candidates=[_candidate_out(row) for row in rows],
        error_code=run.error_code,
        started_at=run.started_at.isoformat(),
        completed_at=run.completed_at.isoformat() if run.completed_at else None,
    )


# ── Proyectos ───────────────────────────────────────────────────────────────


def create_project(
    session: Session, raw_idea: str, title: str | None = None
) -> ContentProject:
    """Crea un proyecto en estado ``IDEA`` (CAP-01).

    Devuelve la instancia SQLModel VIVA del agregado (no un snapshot pydantic):
    el identity map de la sesión mantiene la misma instancia, de modo que las
    referencias previas ven los cambios de estado posteriores (los tests de G.3
    verifican ``project.status`` sobre la instancia que ellos crearon).
    """
    return repos.create_project(session, raw_idea, title)


def submit_brief(
    session: Session, project_id: int, brief: schemas.BriefIn
) -> ContentProject:
    """Persiste el brief (transición IDEA → BRIEF_READY; guard CAP-02/03).

    Devuelve la instancia viva del proyecto (mismo criterio que
    ``create_project``).
    """
    _apply_transition(session, project_id, "SUBMIT_BRIEF", fsm.FsmContext(brief=brief))
    return repos.set_project_brief(session, project_id, brief.model_dump())


def list_projects(session: Session) -> list[schemas.ProjectOut]:
    """Historial de proyectos (P1-ready, design §5.4)."""
    return [
        schemas.ProjectOut(
            id=project.id,
            raw_idea=project.raw_idea,
            title=project.title,
            status=project.status,
            created_at=project.created_at.isoformat(),
            updated_at=project.updated_at.isoformat(),
        )
        for project in repos.list_projects(session)
    ]


def get_project_detail(session: Session, project_id: int) -> schemas.ProjectDetailOut:
    return _project_detail_out(_load_project_or_404(session, project_id))


def _project_detail_out(project: ContentProject) -> schemas.ProjectDetailOut:
    return schemas.ProjectDetailOut(
        id=project.id,
        raw_idea=project.raw_idea,
        title=project.title,
        status=project.status,
        created_at=project.created_at.isoformat(),
        updated_at=project.updated_at.isoformat(),
        brief=schemas.BriefIn.model_validate(project.brief) if project.brief else None,
        voice_profile=schemas.VoiceProfileOut.model_validate(project.voice_profile)
        if project.voice_profile
        else None,
    )


# ── Generación ──────────────────────────────────────────────────────────────


def generate(
    session: Session,
    project_id: int,
    provider: Any,
    run_generation: Any,
) -> schemas.RunOut:
    """BRIEF_READY → GENERATING → GENERATED | GENERATION_FAILED (RF-02, HARN-05)."""
    project = _load_project_or_404(session, project_id)
    if project.status != "GENERATING":
        # retry_generate ya transicionó a GENERATING; cualquier otro estado pasa
        # por la FSM: BRIEF_READY → GENERATING, o rechazo 409 sin persistir nada.
        _apply_transition(session, project_id, "START_GENERATION")

    brief = schemas.BriefIn.model_validate(project.brief)
    result = run_generation(brief, provider)
    run = repos.create_run(
        session,
        project_id,
        provider=result.provider,
        model=result.model,
        prompt_version=result.prompt_version,
        schema_version=result.schema_version,
        prompt_hash=result.prompt_hash,
    )
    for event in redact_secrets(result.trace_events):
        repos.append_trace_event(session, run.id, event)

    if result.ok:
        _apply_transition(
            session, project_id, "GENERATION_SUCCEEDED", fsm.FsmContext(
                brief=brief, candidates=result.candidates
            )
        )
        rows = repos.add_candidates(
            session, run.id, [candidate.model_dump() for candidate in result.candidates]
        )
        repos.complete_run(session, run.id, "GENERATED")
        run = repos.get_run(session, run.id)
        return _run_out(run, rows)

    _apply_transition(session, project_id, "GENERATION_FAILED")
    repos.complete_run(
        session,
        run.id,
        "GENERATION_FAILED",
        error_code=result.error_code,
        raw_output=result.raw_output,
    )
    run = repos.get_run(session, run.id)
    return _run_out(run, [])


def retry_generate(
    session: Session,
    project_id: int,
    provider: Any,
    run_generation: Any,
) -> schemas.RunOut:
    """GENERATION_FAILED → GENERATING → GENERATED (RNF-03: abre un run NUEVO)."""
    project = _load_project_or_404(session, project_id)
    brief = schemas.BriefIn.model_validate(project.brief)
    _apply_transition(session, project_id, "RETRY_GENERATION", fsm.FsmContext(brief=brief))
    return generate(session, project_id, provider, run_generation)


# ── Evaluación ──────────────────────────────────────────────────────────────


def evaluate_run(
    session: Session,
    run_id: int,
    provider: Any,
    run_evaluation: Any,
) -> schemas.EvaluationOut:
    """GENERATED → EVALUATING → RECOMMENDED | REVISION_REQUIRED (RF-03, EVAL-06).

    Degrada a ``EVALUATION_PARTIAL`` si el evaluador semántico no está
    disponible (HARN-08 → 503): sin fabricar un score completo.
    """
    run = _load_run_or_404(session, run_id)
    project = _load_project_or_404(session, run.project_id)
    candidates = repos.list_candidates_for_run(session, run_id)

    # Idempotencia honesta (TRC-03, APPR-03): si la evaluación sigue vigente
    # (ningún candidato cambió desde la última), se devuelve la decisión
    # almacenada SIN re-correr el harness ni appendear eventos. La edición
    # (CANDIDATE_EDITED) es lo único que invalida la evaluación.
    stored = _stored_evaluation(session, candidates)
    if stored is not None:
        return stored

    brief = schemas.BriefIn.model_validate(project.brief)

    _apply_transition(session, project.id, "START_EVALUATION")
    result = run_evaluation(candidates, brief, provider)
    for event in redact_secrets(result.trace_events):
        repos.append_trace_event(session, run_id, event)

    if not result.ok:
        _apply_transition(session, project.id, "EVALUATION_PARTIAL")
        return schemas.EvaluationOut(
            candidate_scores=[],
            decision=schemas.DecisionOut(
                outcome="REVISION_REQUIRED",
                best_candidate_id=None,
                reason="evaluacion semantica no disponible; el run quedo EVALUATION_PARTIAL.",
                brief_needs_revision=True,
            ),
        )

    # El harness evalúa por POSICIÓN en la lista (EVAL-07: anonimiza y baraja;
    # `_remap_scores` devuelve candidate_id = índice ORIGINAL en `candidates`).
    # El orden de salida no es posicional: se mapea índice → ID real de la DB
    # antes de decidir y persistir (G.3).
    by_position = {position: row for position, row in enumerate(candidates)}
    scores = [
        score.model_copy(update={"candidate_id": by_position[score.candidate_id].id})
        for score in result.candidate_scores
    ]
    row_by_id = {row.id: row for row in candidates}
    decision = _decision_from(scores)
    for score in scores:
        repos.update_candidate_evaluation(
            session,
            score.candidate_id,
            {
                "score_final": score.score_final,
                "decision": decision.outcome,
                "blockers": [blocker.model_dump() for blocker in score.blockers],
                "content_version": row_by_id[score.candidate_id].content_version,
            },
        )
    repos.append_decision(
        session,
        decision.best_candidate_id,
        {
            **decision.model_dump(),
            "decision": decision.outcome,
            "by": "system",
            "at": build_trace_event("evaluation_decision")["ts"],
        },
    )
    repos.append_trace_event(
        session,
        run_id,
        build_trace_event("evaluation_decision", decision=decision.model_dump()),
    )
    _apply_transition(
        session, project.id, "EVALUATION_SUCCEEDED", fsm.FsmContext(evaluation=decision)
    )
    return schemas.EvaluationOut(
        candidate_scores=[score for score in scores],
        decision=decision,
    )


def _decision_from(scores: Sequence[Any]) -> schemas.DecisionOut:
    from domain import blockers

    blockers_by_candidate: dict[int, list[Any]] = {}
    for score in scores:
        blockers_by_candidate[score.candidate_id] = list(score.blockers)
    decision = blockers.decide(
        scores,
        {candidate_id: blockers for candidate_id, blockers in blockers_by_candidate.items()},
    )
    return schemas.DecisionOut(
        outcome=decision.outcome,
        best_candidate_id=decision.best_candidate_id,
        reason=decision.reason,
        brief_needs_revision=decision.brief_needs_revision,
    )


def _stored_evaluation(
    session: Session, candidates: Sequence[Any]
) -> schemas.EvaluationOut | None:
    """Devuelve la evaluación VIGENTE sin re-correr el harness (TRC-03/APPR-03).

    Si todos los candidatos tienen una evaluación persistida que coincide con
    su ``content_version`` (ninguno cambió desde la última evaluación), la
    decisión almacenada sigue siendo válida: se reconstruye desde los scores
    persistidos con la MISMA regla del dominio (``decide``). Re-evaluar en
    caliente es un no-op honesto — no se appendan eventos ni se toca el estado.
    """
    from domain import blockers

    stored: list[Any] = []
    blockers_by_candidate: dict[int, list[Any]] = {}
    for candidate in candidates:
        evaluation = candidate.evaluation
        if not evaluation or evaluation.get("content_version") != candidate.content_version:
            return None
        stored.append(
            SimpleNamespace(
                candidate_id=candidate.id, score_final=evaluation["score_final"]
            )
        )
        blockers_by_candidate[candidate.id] = list(evaluation.get("blockers", ()))
    decision = blockers.decide(stored, blockers_by_candidate)
    return schemas.EvaluationOut(
        candidate_scores=[],
        decision=schemas.DecisionOut(
            outcome=decision.outcome,
            best_candidate_id=decision.best_candidate_id,
            reason=decision.reason,
            brief_needs_revision=decision.brief_needs_revision,
        ),
    )


# ── Edición, revisión y aprobación humana ───────────────────────────────────


def edit_candidate(
    session: Session,
    candidate_id: int,
    content: schemas.CandidateContent,
) -> schemas.CandidateOut:
    """Edición humana (APPR-02/03): invalida evaluación y vuelve a GENERATED."""
    candidate = repos.get_candidate(session, candidate_id)
    if candidate is None:
        raise errors.NotFoundError(f"candidato {candidate_id} no existe")
    project = _project_for_candidate(session, candidate_id)
    changed = (
        candidate.hook != content.hook
        or candidate.body != content.body
        or candidate.cta != content.cta
    )
    _apply_transition(
        session,
        project.id,
        "CANDIDATE_EDITED",
        fsm.FsmContext(candidate_changed=changed),
    )
    repos.update_candidate_content(
        session, candidate_id, hook=content.hook, body=content.body, cta=content.cta
    )
    repos.bump_candidate_version(session, candidate_id)
    repos.append_trace_event(
        session,
        candidate.run_id,
        build_trace_event(
            "candidate_edited",
            candidate_id=candidate_id,
            content_version=candidate.content_version + 1,
        ),
    )
    return _candidate_out(repos.get_candidate(session, candidate_id))


def request_revision(
    session: Session,
    candidate_id: int,
    reason: str,
) -> schemas.CandidateOut:
    """RECOMMENDED → REVISION_REQUIRED (APPR-01, FSM ``_reason``)."""
    candidate = repos.get_candidate(session, candidate_id)
    if candidate is None:
        raise errors.NotFoundError(f"candidato {candidate_id} no existe")
    project = _project_for_candidate(session, candidate_id)
    _apply_transition(session, project.id, "REQUEST_REVISION", fsm.FsmContext(reason=reason))
    repos.append_decision(
        session,
        candidate_id,
        {
            "decision": "REVISION_REQUIRED",
            "by": "human",
            "reason": reason,
            "at": build_trace_event("revision_requested")["ts"],
        },
    )
    repos.append_trace_event(
        session,
        candidate.run_id,
        build_trace_event("revision_requested", candidate_id=candidate_id, reason=reason),
    )
    return _candidate_out(repos.get_candidate(session, candidate_id))


def approve_candidate(session: Session, candidate_id: int, reason: str) -> schemas.CandidateOut:
    """RECOMMENDED | REVISION_REQUIRED → APPROVED (APPR-01/03).

    La FSM bloquea con blockers activos (APPR-01) y sin razón (``_reason``);
    el estado del proyecto permanece intacto si se rechaza.
    """
    candidate = repos.get_candidate(session, candidate_id)
    if candidate is None:
        raise errors.NotFoundError(f"candidato {candidate_id} no existe")
    project = _project_for_candidate(session, candidate_id)
    evaluation = candidate.evaluation or {}
    ctx = fsm.FsmContext(
        evaluation=evaluation,
        blockers=evaluation.get("blockers", ()),
        candidate_id=candidate_id,
        reason=reason,
    )
    _apply_transition(session, project.id, "APPROVE", ctx)

    selected = repos.get_candidate(session, candidate_id)
    selected.selected = True
    selected.selection_reason = reason
    session.add(selected)
    session.commit()
    session.refresh(selected)
    repos.append_decision(
        session,
        candidate_id,
        {
            "decision": "APPROVED",
            "by": "human",
            "reason": reason,
            "at": build_trace_event("candidate_approved")["ts"],
        },
    )
    repos.append_trace_event(
        session,
        candidate.run_id,
        build_trace_event("candidate_approved", candidate_id=candidate_id, reason=reason),
    )
    return _candidate_out(repos.get_candidate(session, candidate_id))


# ── Visual ──────────────────────────────────────────────────────────────────


def generate_visual(session: Session, candidate_id: int) -> schemas.VisualOut:
    """APPROVED → VISUAL_DRAFT (APPR-05, VIS-01/03: contrato derivado de la tesis)."""
    candidate = repos.get_candidate(session, candidate_id)
    if candidate is None:
        raise errors.NotFoundError(f"candidato {candidate_id} no existe")
    project = _project_for_candidate(session, candidate_id)
    contract = build_visual_contract(project.brief["thesis"], candidate)
    ctx = fsm.FsmContext(approved_candidate_id=candidate_id, visual=contract)
    _apply_transition(session, project.id, "GENERATE_VISUAL", ctx)
    visual = repos.save_visual(
        session,
        candidate_id,
        thesis=contract["thesis"],
        concept=contract["concept"],
        elements=contract["elements"],
        alt_text=contract["alt_text"],
    )
    repos.append_trace_event(
        session,
        candidate.run_id,
        build_trace_event(
            "visual_contract_created",
            visual_id=visual.id,
            concept=contract["concept"],
        ),
    )
    return _visual_out(visual)


def approve_visual(session: Session, visual_id: int, reason: str) -> schemas.VisualOut:
    """VISUAL_DRAFT → VISUAL_READY (VIS-06, guard ``_visual_valid``)."""
    visual = repos.get_visual(session, visual_id)
    if visual is None:
        raise errors.NotFoundError(f"visual {visual_id} no existe")
    if not reason.strip():
        raise errors.StateTransitionRejected("la aprobación visual requiere una razón humana")
    project = _project_for_candidate(session, visual.candidate_id)
    ctx = fsm.FsmContext(visual=visual, reason=reason)
    _apply_transition(session, project.id, "APPROVE_VISUAL", ctx)
    visual = repos.update_visual_status(session, visual_id, "VISUAL_READY")
    candidate = repos.get_candidate(session, visual.candidate_id)
    repos.append_trace_event(
        session,
        candidate.run_id,
        build_trace_event(
            "visual_approved",
            visual_id=visual_id,
            actor="human",
            reason=reason,
        ),
    )
    return _visual_out(visual)


def reject_visual(session: Session, visual_id: int, reason: str) -> schemas.VisualOut:
    """VISUAL_DRAFT → VISUAL_REVISION_REQUIRED (VIS-06, FSM ``_reason``)."""
    visual = repos.get_visual(session, visual_id)
    if visual is None:
        raise errors.NotFoundError(f"visual {visual_id} no existe")
    project = _project_for_candidate(session, visual.candidate_id)
    _apply_transition(
        session,
        project.id,
        "REJECT_VISUAL",
        fsm.FsmContext(visual=visual, reason=reason),
    )
    visual = repos.update_visual_status(session, visual_id, "VISUAL_REVISION_REQUIRED")
    candidate = repos.get_candidate(session, visual.candidate_id)
    repos.append_trace_event(
        session,
        candidate.run_id,
        build_trace_event("visual_rejected", visual_id=visual_id, reason=reason),
    )
    return _visual_out(visual)


def regenerate_visual(session: Session, visual_id: int) -> schemas.VisualOut:
    """VISUAL_REVISION_REQUIRED → VISUAL_DRAFT sobre el candidato aprobado."""
    visual = repos.get_visual(session, visual_id)
    if visual is None:
        raise errors.NotFoundError(f"visual {visual_id} no existe")
    candidate = repos.get_candidate(session, visual.candidate_id)
    project = _project_for_candidate(session, visual.candidate_id)
    _apply_transition(session, project.id, "REGENERATE_VISUAL")
    contract = build_visual_contract(project.brief["thesis"], candidate)
    regenerated = repos.save_visual(
        session,
        candidate.id,
        thesis=contract["thesis"],
        concept=contract["concept"],
        elements=contract["elements"],
        alt_text=contract["alt_text"],
    )
    repos.append_trace_event(
        session,
        candidate.run_id,
        build_trace_event(
            "visual_regenerated",
            previous_visual_id=visual_id,
            visual_id=regenerated.id,
        ),
    )
    return _visual_out(regenerated)


def _visual_out(visual: Any) -> schemas.VisualOut:
    return schemas.VisualOut(
        id=visual.id,
        candidate_id=visual.candidate_id,
        thesis=visual.thesis,
        concept=visual.concept,
        elements=list(visual.elements or []),
        alt_text=visual.alt_text,
        status=visual.status,
        svg_path=visual.svg_path,
    )


# ── Publicación simulada ────────────────────────────────────────────────────


def simulate_publish(session: Session, candidate_id: int) -> schemas.PublicationOut:
    """VISUAL_READY → SIMULATED_PUBLISHED (SIM-01/02/04; ADR-007).

    Recibo LOCAL: ``remote_id=None``, ``mode="simulated"`` y el notice literal
    del contrato. Jamás un ID remoto inventado.
    """
    candidate = repos.get_candidate(session, candidate_id)
    if candidate is None:
        raise errors.NotFoundError(f"candidato {candidate_id} no existe")
    project = _project_for_candidate(session, candidate_id)
    visual = repos.get_latest_visual_for_candidate(session, candidate_id)
    ctx = fsm.FsmContext(
        approved_candidate_id=candidate_id,
        visual=visual,
    )
    _apply_transition(session, project.id, "SIMULATE_PUBLISH", ctx)
    notice = "no se envió contenido a LinkedIn"
    attempt = repos.save_publication_attempt(
        session,
        candidate_id,
        receipt={
            "visual_id": visual.id,
            "mode": "simulated",
            "status": "SIMULATED_PUBLISHED",
            "notice": notice,
        },
    )
    repos.append_trace_event(
        session,
        candidate.run_id,
        build_trace_event(
            "publication_simulated",
            candidate_id=candidate_id,
            visual_id=visual.id,
            receipt_id=attempt.id,
            mode="simulated",
            status="SIMULATED_PUBLISHED",
            notice=notice,
        ),
    )
    return schemas.PublicationOut(
        receipt=schemas.ReceiptOut(
            id=attempt.id,
            mode=attempt.mode,
            status=attempt.status,
            candidate_id=candidate_id,
            visual_id=visual.id,
            created_at=attempt.created_at.isoformat(),
            notice=notice,
            remote_id=attempt.remote_id,
        ),
        candidate_id=candidate_id,
        visual_id=visual.id,
    )


# ── Traza (TRC-01/02/03) ────────────────────────────────────────────────────


def get_run_trace(session: Session, run_id: int) -> schemas.RunDetailOut:
    """Traza completa del run (design §14), SIEMPRE redactada (TRC-02).

    Ensambla: ``trace_events`` del run (append-only), brief, voz y el run en sí.
    ``redact_secrets`` se aplica sobre la respuesta ensamblada antes de
    devolverla (RNF-04).
    """
    run = _load_run_or_404(session, run_id)
    project = _load_project_or_404(session, run.project_id)
    trace_events = list(run.trace_events or [])
    candidates = repos.list_candidates_for_run(session, run_id)
    detail = schemas.RunDetailOut(
        run=_run_out(run, candidates),
        trace_events=[schemas.TraceEventOut(**event) for event in trace_events],
        brief=schemas.BriefIn.model_validate(project.brief) if project.brief else None,
        voice_profile=schemas.VoiceProfileOut.model_validate(project.voice_profile)
        if project.voice_profile
        else None,
    )
    return schemas.RunDetailOut.model_validate(redact_secrets(detail.model_dump()))


__all__ = [
    "approve_candidate",
    "approve_visual",
    "create_project",
    "edit_candidate",
    "evaluate_run",
    "generate",
    "generate_visual",
    "get_project_detail",
    "get_run_trace",
    "list_projects",
    "reject_visual",
    "regenerate_visual",
    "request_revision",
    "retry_generate",
    "simulate_publish",
    "submit_brief",
]
