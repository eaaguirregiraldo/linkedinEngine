"""Tests del servicio de aplicación ``api.workflow`` (G.3, design §14).

Criterio G.3: happy path completo (IDEA → … → SIMULATED_PUBLISHED) con
SQLite temporal; la edición invalida la evaluación previa (APPR-02/03);
un blocker activo bloquea el approve (APPR-01); ``GENERATION_FAILED``
conserva el brief (RNF-03, invariante 4); la traza es append-only y la
evaluación original sigue presente tras reevaluar (TRC-03); el detalle de
traza se sirve redactado (TRC-02).

Nada toca la DB real: cada test usa su propio fichero SQLite temporal
(fixture ``db_file`` del conftest raíz).
"""
from __future__ import annotations

from pathlib import Path

import pytest
from sqlmodel import Session

from ai.demo_provider import DemoProvider
from ai.harness import run_evaluation, run_generation
from api import errors, workflow
from api.schemas import BriefIn, CandidateContent
from db import repos
from db.engine import create_all_tables, create_db_engine
from db.models import ContentProject


@pytest.fixture()
def engine(db_file: Path):
    created = create_db_engine(db_file)
    create_all_tables(created)
    return created


@pytest.fixture()
def session(engine):
    with Session(engine) as s:
        yield s


def _demo_brief() -> BriefIn:
    return BriefIn(
        thesis=(
            "Migrar COBOL no es traducir sintaxis; es recuperar conocimiento "
            "operativo antes de tocar código."
        ),
        audience="líderes de modernización",
        objective="plantear la migración como recuperación de conocimiento",
        evidence=[
            {
                "id": "e1",
                "text": (
                    "El conocimiento operativo vive en reglas de negocio y "
                    "excepciones que rara vez están documentadas."
                ),
                "type": "known_facts",
            },
            {
                "id": "e2",
                "text": "La sintaxis es la parte más simple del sistema.",
                "type": "known_facts",
            },
        ],
        constraints=["No inventar cifras de empresas."],
    )


def _project_with_brief(session: Session) -> ContentProject:
    project = workflow.create_project(session, "Idea demo de prueba", "Demo")
    workflow.submit_brief(session, project.id, _demo_brief())
    return project


def _generated_run(session: Session) -> tuple[ContentProject, object]:
    project = _project_with_brief(session)
    run = workflow.generate(session, project.id, DemoProvider(), run_generation)
    return project, run


# ── Happy path (G.3 criterio 1) ─────────────────────────────────────────────


def test_happy_path_completo_hasta_simulated_published(session: Session):
    project = _project_with_brief(session)
    assert project.status == "BRIEF_READY"

    run = workflow.generate(session, project.id, DemoProvider(), run_generation)
    assert run.status == "GENERATED"
    assert len(run.candidates) == 3
    assert project.status == "GENERATED"
    # cada candidato arranca con versión 1 y sin evaluación
    for candidate in run.candidates:
        assert candidate.content_version == 1
        assert candidate.evaluation is None

    evaluation = workflow.evaluate_run(session, run.id, DemoProvider(), run_evaluation)
    assert evaluation.decision.outcome in ("RECOMMENDED", "REVISION_REQUIRED")
    assert evaluation.decision.best_candidate_id is not None
    assert project.status == evaluation.decision.outcome
    best = evaluation.decision.best_candidate_id

    approved = workflow.approve_candidate(session, best, "El ángulo elegido conecta con la audiencia.")
    assert approved.decision == "APPROVED"
    assert project.status == "APPROVED"

    visual = workflow.generate_visual(session, best)
    assert visual.status == "VISUAL_DRAFT"
    assert visual.elements and visual.alt_text
    assert project.status == "VISUAL_DRAFT"

    ready = workflow.approve_visual(session, visual.id, "El visual sostiene la tesis.")
    assert ready.status == "VISUAL_READY"
    assert project.status == "VISUAL_READY"

    publication = workflow.simulate_publish(session, best)
    assert publication.status == "SIMULATED_PUBLISHED"
    assert publication.receipt.remote_id is None
    assert publication.receipt.notice == "no se envió contenido a LinkedIn"
    assert publication.receipt.visual_id == visual.id
    assert project.status == "SIMULATED_PUBLISHED"

    # traza completa (TRC-01): brief, voz, proveedor, prompt hash y eventos
    detail = workflow.get_run_trace(session, run.id)
    assert detail.brief is not None and detail.brief.thesis == _demo_brief().thesis
    assert detail.voice_profile.label == "perfil de voz provisional v0"
    assert detail.run.provider == "DEMO_PROVIDER"
    assert detail.run.prompt_hash.startswith("sha256:")
    event_types = {event.type for event in detail.trace_events}
    assert {
        "prompt_resolved",
        "provider_invoked",
        "output_validated",
        "evaluation_scored",
        "evaluation_decision",
        "candidate_approved",
        "visual_contract_created",
        "visual_approved",
        "publication_simulated",
    } <= event_types


# ── Edición invalida evaluación (APPR-02/03, FSM-03) ────────────────────────


def test_edicion_invalida_evaluacion_y_bloquea_aprobacion(session: Session):
    project, run = _generated_run(session)
    evaluation = workflow.evaluate_run(session, run.id, DemoProvider(), run_evaluation)
    best = evaluation.decision.best_candidate_id
    assert repos.get_candidate(session, best).evaluation is not None

    edited = workflow.edit_candidate(
        session,
        best,
        CandidateContent(
            hook="Nuevo hook editado manualmente",
            body="Nuevo cuerpo editado por el autor tras ver el score.",
            cta="¿Qué te parece esta nueva versión?",
        ),
    )
    assert edited.content_version == 2
    assert edited.evaluation is None
    assert project.status == "GENERATED"
    # la evaluación previa quedó invalidada en el candidato
    assert repos.get_candidate(session, best).evaluation is None

    # aprobar sin reevaluar tras la edición → bloqueado (APPR-03)
    with pytest.raises(errors.StateTransitionRejected):
        workflow.approve_candidate(session, best, "Quiero aprobar igual.")

    # la reevaluación liviana vuelve a dejar el flujo aprobable (APPR-03)
    re_eval = workflow.evaluate_run(session, run.id, DemoProvider(), run_evaluation)
    re_approved = workflow.approve_candidate(session, best, "Tras reevaluar, apruebo.")
    assert re_eval.decision.best_candidate_id is not None
    assert re_approved.decision == "APPROVED"


def test_edicion_sin_cambios_reales_rechazada(session: Session):
    project, run = _generated_run(session)
    evaluation = workflow.evaluate_run(session, run.id, DemoProvider(), run_evaluation)
    best = evaluation.decision.best_candidate_id
    candidate = repos.get_candidate(session, best)

    with pytest.raises(errors.StateTransitionRejected):
        workflow.edit_candidate(
            session,
            best,
            CandidateContent(hook=candidate.hook, body=candidate.body, cta=candidate.cta),
        )


# ── Blocker bloquea approve (APPR-01, EVAL-05) ──────────────────────────────


def test_blocker_activo_bloquea_approve(session: Session):
    project, run = _generated_run(session)
    evaluation = workflow.evaluate_run(session, run.id, DemoProvider(), run_evaluation)
    best = evaluation.decision.best_candidate_id
    assert project.status in ("RECOMMENDED", "REVISION_REQUIRED")

    # el evaluador demo no produce blockers para este brief; se inyecta el
    # resultado de EVAL-05 (blocker activo) en la evaluación vigente y se
    # verifica que la FSM bloquea la transición a APPROVED (APPR-01).
    vigente = dict(repos.get_candidate(session, best).evaluation)
    vigente["blockers"] = [
        {
            "code": "UNSUPPORTED_ASSERTION",
            "message": "Cifra o afirmacion sin fuente",
            "detail": "5 mainframes",
        }
    ]
    repos.update_candidate_evaluation(session, best, vigente)

    with pytest.raises(errors.StateTransitionRejected) as exc_info:
        workflow.approve_candidate(session, best, "Aun así quiero aprobar.")
    assert "blockers" in exc_info.value.message.lower()
    # el estado permanece sin cambios (FSM-01: sin corrupción)
    assert project.status in ("RECOMMENDED", "REVISION_REQUIRED")


def test_evaluacion_superficie_blockers_por_candidato(session: Session):
    """EVAL-05 vía flujo real: edición con experiencia inventada → blocker."""
    project, run = _generated_run(session)
    evaluation = workflow.evaluate_run(session, run.id, DemoProvider(), run_evaluation)
    best = evaluation.decision.best_candidate_id

    workflow.edit_candidate(
        session,
        best,
        CandidateContent(
            hook="Yo lideré una migración a escala",
            body="Yo lideré la migración de 5 mainframes en 2023 sin documentación previa.",
            cta="¿Querés conocer el resultado?",
        ),
    )
    re_eval = workflow.evaluate_run(session, run.id, DemoProvider(), run_evaluation)
    assert re_eval.decision.best_candidate_id is not None
    blockers = repos.get_candidate(session, best).evaluation["blockers"]
    assert blockers, "la re-evaluación debe exponer el blocker en el candidato"


# ── GENERATION_FAILED conserva brief (RNF-03, invariante 4) ─────────────────


def test_generation_failed_conserva_brief_y_retry(session: Session):
    project = _project_with_brief(session)
    brief_antes = dict(project.brief)

    failed = workflow.generate(
        session, project.id, DemoProvider(force_invalid=True), run_generation
    )
    assert failed.status == "GENERATION_FAILED"
    assert failed.error_code == "INVALID_OUTPUT"
    assert failed.candidates == []
    # el proyecto conserva el brief (RNF-03) y su estado honesto
    assert project.status == "GENERATION_FAILED"
    assert project.brief == brief_antes
    # la ejecución fallida conserva error y traza (invariante 4)
    assert repos.get_run(session, failed.id).error_code == "INVALID_OUTPUT"
    detail = workflow.get_run_trace(session, failed.id)
    assert detail.brief is not None and detail.brief.thesis == _demo_brief().thesis

    # reintentar con provider sano: nuevo run GENERATED, el fallido intacto
    retried = workflow.retry_generate(session, project.id, DemoProvider(), run_generation)
    assert retried.status == "GENERATED"
    assert retried.id != failed.id
    assert project.status == "GENERATED"
    assert repos.get_run(session, failed.id).status == "GENERATION_FAILED"


# ── Traza append-only (TRC-03) y redacción (TRC-02) ─────────────────────────


def test_traza_append_only_tras_reevaluacion(session: Session):
    project, run = _generated_run(session)
    workflow.evaluate_run(session, run.id, DemoProvider(), run_evaluation)

    before = workflow.get_run_trace(session, run.id)
    first_round = [e for e in before.trace_events if e.type == "evaluation_scored"]
    assert len(first_round) == 3

    # edición + reevaluación liviana (APPR-03)
    evaluation = workflow.evaluate_run(session, run.id, DemoProvider(), run_evaluation)
    best = evaluation.decision.best_candidate_id
    workflow.edit_candidate(
        session,
        best,
        CandidateContent(
            hook="Hook modificado para la prueba de traza",
            body="Cuerpo modificado para la prueba de traza.",
            cta="¿CTA modificada?",
        ),
    )
    workflow.evaluate_run(session, run.id, DemoProvider(), run_evaluation)

    after = workflow.get_run_trace(session, run.id)
    scored = [e for e in after.trace_events if e.type == "evaluation_scored"]
    # 3 (primera ronda) + 3 (reevaluación) — nada se borró ni sobrescribió
    assert len(scored) == 6
    assert scored[:3] == list(first_round)


def test_traza_redacta_secretos_al_servirse(session: Session):
    project, run = _generated_run(session)
    repos.append_trace_event(
        session,
        run.id,
        {
            "ts": "2026-01-01T00:00:00+00:00",
            "type": "debug",
            "api_key": "sk-secreto-no-persistir",
            "params": {"authorization": "Bearer abc123"},
        },
    )

    detail = workflow.get_run_trace(session, run.id)
    dump = detail.model_dump()
    assert "sk-secreto-no-persistir" not in str(dump)
    assert "Bearer abc123" not in str(dump)
    debug = next(event for event in dump["trace_events"] if event["type"] == "debug")
    assert debug["api_key"] == "[REDACTED]"
    assert debug["params"]["authorization"] == "[REDACTED]"


# ── Transiciones ilegales (FSM-02) y recursos inexistentes ─────────────────


def test_transiciones_ilegales_son_409_accionable(session: Session):
    # generar sin brief (IDEA → START_GENERATION ilegal)
    project = workflow.create_project(session, "Idea sin brief")
    with pytest.raises(errors.StateTransitionRejected) as exc_info:
        workflow.generate(session, project.id, DemoProvider(), run_generation)
    assert project.status == "IDEA"  # estado sin corrupción
    assert "prerequisitos" in exc_info.value.message.lower() or "no esta permitido" in exc_info.value.message.lower()

    # aprobar sin evaluación (GENERATED → APPROVE ilegal)
    project2, run = _generated_run(session)
    best = repos.list_candidates_for_run(session, run.id)[0].id
    with pytest.raises(errors.StateTransitionRejected):
        workflow.approve_candidate(session, best, "Sin evaluación no.")
    assert project2.status == "GENERATED"

    # publicar sin candidato aprobado (GENERATED → SIMULATE_PUBLISH ilegal)
    with pytest.raises(errors.StateTransitionRejected):
        workflow.simulate_publish(session, best)


def test_recursos_inexistentes_lanzan_not_found(session: Session):
    with pytest.raises(errors.NotFoundError):
        workflow.generate(session, 9999, DemoProvider(), run_generation)
    with pytest.raises(errors.NotFoundError):
        workflow.evaluate_run(session, 9999, DemoProvider(), run_evaluation)
    with pytest.raises(errors.NotFoundError):
        workflow.get_run_trace(session, 9999)
    with pytest.raises(errors.NotFoundError):
        workflow.approve_candidate(session, 9999, "razón")
    with pytest.raises(errors.NotFoundError):
        workflow.edit_candidate(
            session, 9999, CandidateContent(hook="h", body="b", cta="c")
        )
    with pytest.raises(errors.NotFoundError):
        workflow.generate_visual(session, 9999)
    with pytest.raises(errors.NotFoundError):
        workflow.approve_visual(session, 9999, "razón")
    with pytest.raises(errors.NotFoundError):
        workflow.simulate_publish(session, 9999)


# ── Aprobación humana: razón obligatoria y override (APPR-01/04) ────────────


def test_aprobacion_sin_razon_rechazada(session: Session):
    project, run = _generated_run(session)
    evaluation = workflow.evaluate_run(session, run.id, DemoProvider(), run_evaluation)
    best = evaluation.decision.best_candidate_id
    with pytest.raises(errors.StateTransitionRejected):
        workflow.approve_candidate(session, best, "   ")
    assert project.status in ("RECOMMENDED", "REVISION_REQUIRED")


def test_override_desde_revision_requerida_con_razon(session: Session):
    """APPR-01 escenario override: REQUEST_REVISION → approve con razón."""
    project, run = _generated_run(session)
    evaluation = workflow.evaluate_run(session, run.id, DemoProvider(), run_evaluation)
    best = evaluation.decision.best_candidate_id

    revised = workflow.request_revision(session, best, "El gancho no conecta con la audiencia.")
    assert revised.decision == "REVISION_REQUIRED"
    assert project.status == "REVISION_REQUIRED"

    overridden = workflow.approve_candidate(session, best, "Override editorial justificado.")
    assert overridden.decision == "APPROVED"
    assert project.status == "APPROVED"


# ── Visual (VIS-06, APPR-05) ────────────────────────────────────────────────


def test_solo_candidato_aprobado_genera_visual(session: Session):
    # candidato no aprobado → GENERATE_VISUAL ilegal (APPR-05)
    project, run = _generated_run(session)
    best = repos.list_candidates_for_run(session, run.id)[0].id
    with pytest.raises(errors.StateTransitionRejected):
        workflow.generate_visual(session, best)
    assert project.status == "GENERATED"


def test_rechazo_de_visual_con_razon(session: Session):
    project, run = _generated_run(session)
    evaluation = workflow.evaluate_run(session, run.id, DemoProvider(), run_evaluation)
    best = evaluation.decision.best_candidate_id
    workflow.approve_candidate(session, best, "Apruebo el candidato.")
    visual = workflow.generate_visual(session, best)

    rejected = workflow.reject_visual(session, visual.id, "La metáfora no representa la tesis.")
    assert rejected.status == "VISUAL_REVISION_REQUIRED"
    assert project.status == "VISUAL_REVISION_REQUIRED"

    regenerated = workflow.regenerate_visual(session, visual.id)
    assert regenerated.id != visual.id
    assert regenerated.status == "VISUAL_DRAFT"
    assert project.status == "VISUAL_DRAFT"


# ── Simulación honesta (SIM-02, SIM-04) ─────────────────────────────────────


def test_simulacion_requiere_visual_listo(session: Session):
    project, run = _generated_run(session)
    evaluation = workflow.evaluate_run(session, run.id, DemoProvider(), run_evaluation)
    best = evaluation.decision.best_candidate_id
    workflow.approve_candidate(session, best, "Apruebo.")

    # candidato aprobado pero sin visual VISUAL_READY → bloqueado (SIM-04)
    with pytest.raises(errors.StateTransitionRejected):
        workflow.simulate_publish(session, best)
    assert project.status == "APPROVED"


def test_recibo_local_sin_ids_remotos(session: Session):
    project, run = _generated_run(session)
    evaluation = workflow.evaluate_run(session, run.id, DemoProvider(), run_evaluation)
    best = evaluation.decision.best_candidate_id
    workflow.approve_candidate(session, best, "Apruebo.")
    visual = workflow.generate_visual(session, best)
    workflow.approve_visual(session, visual.id, "El visual representa la tesis.")

    publication = workflow.simulate_publish(session, best)
    assert publication.receipt.remote_id is None
    assert publication.receipt.mode == "simulated"
    attempt = repos.get_publication_for_candidate(session, best)
    assert attempt.remote_id is None
    assert attempt.mode == "simulated"
