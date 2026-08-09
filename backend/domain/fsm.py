"""Declarative, framework-free project state machine."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .validation import validate_candidates

STATES = frozenset(
    {
        "IDEA",
        "BRIEF_READY",
        "GENERATING",
        "GENERATED",
        "EVALUATING",
        "EVALUATION_PARTIAL",
        "RECOMMENDED",
        "REVISION_REQUIRED",
        "APPROVED",
        "VISUAL_DRAFT",
        "VISUAL_READY",
        "VISUAL_REVISION_REQUIRED",
        "SIMULATED_PUBLISHED",
        "GENERATION_FAILED",
        "PUBLISHING_REAL",
        "PUBLISHED_REAL",
        "REAL_PUBLISH_FAILED",
    }
)

EVENTS = frozenset(
    {
        "SUBMIT_BRIEF",
        "START_GENERATION",
        "GENERATION_SUCCEEDED",
        "GENERATION_FAILED",
        "RETRY_GENERATION",
        "START_EVALUATION",
        "EVALUATION_SUCCEEDED",
        "EVALUATION_PARTIAL",
        "CONTINUE_PARTIAL",
        "CANDIDATE_EDITED",
        "REQUEST_REVISION",
        "APPROVE",
        "GENERATE_VISUAL",
        "APPROVE_VISUAL",
        "REJECT_VISUAL",
        "REGENERATE_VISUAL",
        "SIMULATE_PUBLISH",
        "START_REAL_PUBLISH",
        "PUBLISH_SUCCEEDED",
        "PUBLISH_FAILED",
    }
)


@dataclass(frozen=True)
class GuardResult:
    ok: bool
    reason: str | None = None


Guard = Callable[["FsmContext"], GuardResult]


@dataclass(frozen=True)
class Transition:
    source: str
    event: str
    guard: Guard | None
    target: str


@dataclass(frozen=True)
class TransitionResult:
    ok: bool
    state: str | None
    reason: str | None = None


@dataclass(frozen=True)
class FsmContext:
    brief: Any = None
    candidates: Any = None
    evaluation: Any = None
    blockers: Any = ()
    visual: Any = None
    real_provider_enabled: bool = False
    approved_candidate_id: Any = None
    candidate_id: Any = None
    reason: str | None = None
    candidate_changed: bool = False
    remote_id: str | None = None


def _value(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, Mapping):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _accepted() -> GuardResult:
    return GuardResult(True)


def _brief_valid(ctx: FsmContext) -> GuardResult:
    thesis = str(_value(ctx.brief, "thesis", "")).strip()
    evidence = _value(ctx.brief, "evidence", ()) or ()
    if thesis and evidence:
        return _accepted()
    return GuardResult(False, "El brief requiere tesis unica y al menos una evidencia.")


def _generation_valid(ctx: FsmContext) -> GuardResult:
    result = validate_candidates(ctx.candidates or (), _value(ctx.brief, "evidence", ()) or ())
    if result.ok:
        return _accepted()
    codes = ", ".join(issue.code for issue in result.issues)
    return GuardResult(False, f"Contrato de candidatos invalido: {codes}")


def _evaluation_valid(ctx: FsmContext) -> GuardResult:
    outcome = str(_value(ctx.evaluation, "outcome", _value(ctx.evaluation, "decision", ""))).upper()
    if outcome not in {"RECOMMENDED", "REVISION_REQUIRED"}:
        return GuardResult(False, "La evaluacion requiere una decision reproducible.")
    if outcome == "RECOMMENDED" and ctx.blockers:
        return GuardResult(False, "Un candidato con blockers no puede quedar RECOMMENDED.")
    return _accepted()


def _changed(ctx: FsmContext) -> GuardResult:
    return _accepted() if ctx.candidate_changed else GuardResult(False, "La edicion debe incluir cambios reales.")


def _reason(ctx: FsmContext) -> GuardResult:
    return _accepted() if str(ctx.reason or "").strip() else GuardResult(False, "Se requiere una razon editorial.")


def _approve(ctx: FsmContext) -> GuardResult:
    if ctx.blockers:
        return GuardResult(False, "Deben resolverse los blockers antes de aprobar.")
    if ctx.candidate_id is None:
        return GuardResult(False, "Se requiere un candidato para aprobar.")
    return _reason(ctx)


def _approved_candidate(ctx: FsmContext) -> GuardResult:
    if ctx.approved_candidate_id is None:
        return GuardResult(False, "Se requiere un candidato APPROVED.")
    return _accepted()


def _visual_valid(ctx: FsmContext) -> GuardResult:
    alt_text = str(_value(ctx.visual, "alt_text", "")).strip()
    elements = _value(ctx.visual, "elements", ()) or ()
    if alt_text and elements and all(str(_value(item, "rationale", "")).strip() for item in elements):
        return _accepted()
    return GuardResult(False, "El visual requiere alt_text y rationale en todos sus elementos.")


def _simulation_ready(ctx: FsmContext) -> GuardResult:
    if ctx.approved_candidate_id is None:
        return GuardResult(False, "La simulacion requiere un candidato APPROVED.")
    if str(_value(ctx.visual, "status", "")).upper() != "VISUAL_READY":
        return GuardResult(False, "La simulacion requiere un visual VISUAL_READY.")
    return _accepted()


def real_publish_enabled(ctx: FsmContext | None = None) -> bool:
    """P0 invariant: real publication is disabled regardless of input."""
    return False


def _real_publish_disabled(ctx: FsmContext) -> GuardResult:
    del ctx
    return GuardResult(False, "La publicacion real esta reservada e inalcanzable en P0.")


TRANSITIONS = (
    Transition("IDEA", "SUBMIT_BRIEF", _brief_valid, "BRIEF_READY"),
    Transition("BRIEF_READY", "START_GENERATION", None, "GENERATING"),
    Transition("GENERATING", "GENERATION_SUCCEEDED", _generation_valid, "GENERATED"),
    Transition("GENERATING", "GENERATION_FAILED", None, "GENERATION_FAILED"),
    Transition("GENERATION_FAILED", "RETRY_GENERATION", _brief_valid, "GENERATING"),
    Transition("GENERATED", "START_EVALUATION", None, "EVALUATING"),
    Transition(
        "EVALUATING",
        "EVALUATION_SUCCEEDED",
        _evaluation_valid,
        "RECOMMENDED|REVISION_REQUIRED",
    ),
    Transition("EVALUATING", "EVALUATION_PARTIAL", None, "EVALUATION_PARTIAL"),
    Transition("EVALUATION_PARTIAL", "CONTINUE_PARTIAL", None, "REVISION_REQUIRED"),
    Transition("GENERATED", "CANDIDATE_EDITED", _changed, "GENERATED"),
    Transition("RECOMMENDED", "CANDIDATE_EDITED", _changed, "GENERATED"),
    Transition("REVISION_REQUIRED", "CANDIDATE_EDITED", _changed, "GENERATED"),
    Transition("VISUAL_DRAFT", "CANDIDATE_EDITED", _changed, "GENERATED"),
    Transition("VISUAL_READY", "CANDIDATE_EDITED", _changed, "GENERATED"),
    Transition("RECOMMENDED", "REQUEST_REVISION", _reason, "REVISION_REQUIRED"),
    Transition("RECOMMENDED", "APPROVE", _approve, "APPROVED"),
    Transition("REVISION_REQUIRED", "APPROVE", _approve, "APPROVED"),
    Transition("APPROVED", "GENERATE_VISUAL", _approved_candidate, "VISUAL_DRAFT"),
    Transition("VISUAL_DRAFT", "APPROVE_VISUAL", _visual_valid, "VISUAL_READY"),
    Transition("VISUAL_DRAFT", "REJECT_VISUAL", _reason, "VISUAL_REVISION_REQUIRED"),
    Transition("VISUAL_REVISION_REQUIRED", "REGENERATE_VISUAL", None, "VISUAL_DRAFT"),
    Transition("VISUAL_READY", "SIMULATE_PUBLISH", _simulation_ready, "SIMULATED_PUBLISHED"),
    Transition("VISUAL_READY", "START_REAL_PUBLISH", _real_publish_disabled, "PUBLISHING_REAL"),
    Transition("PUBLISHING_REAL", "PUBLISH_SUCCEEDED", _real_publish_disabled, "PUBLISHED_REAL"),
    Transition("PUBLISHING_REAL", "PUBLISH_FAILED", _real_publish_disabled, "REAL_PUBLISH_FAILED"),
)


def _normalize_symbol(value: str) -> str:
    symbol = re.sub(r"\(.*\)$", "", str(value).strip())
    symbol = symbol.replace("-", "_").replace(" ", "_").upper()
    return {"EDIT_CANDIDATE": "CANDIDATE_EDITED"}.get(symbol, symbol)


# Requisito faltante por evento para el mensaje de transición ilegal (design
# §12 / `api` API-04: "mensaje con el requisito faltante", p. ej. publicar sin
# aprobación). Solo se consulta cuando el evento NO es legal desde el estado
# actual; los guards ya cubren los casos con contexto.
_REQUIREMENT_BY_EVENT: dict[str, str] = {
    "SUBMIT_BRIEF": "el proyecto debe estar en IDEA",
    "START_GENERATION": "un brief aprobado (estado BRIEF_READY)",
    "RETRY_GENERATION": "el run anterior en GENERATION_FAILED",
    "START_EVALUATION": "una generacion completada (estado GENERATED)",
    "CANDIDATE_EDITED": "un proyecto con candidatos generados",
    "REQUEST_REVISION": "una evaluacion previa del candidato (RECOMMENDED)",
    "APPROVE": "una evaluacion previa del candidato (RECOMMENDED o REVISION_REQUIRED)",
    "GENERATE_VISUAL": "un candidato APPROVED",
    "APPROVE_VISUAL": "un visual en VISUAL_DRAFT",
    "REJECT_VISUAL": "un visual en VISUAL_DRAFT",
    "REGENERATE_VISUAL": "un visual en VISUAL_REVISION_REQUIRED",
    "SIMULATE_PUBLISH": "candidato APPROVED y visual VISUAL_READY",
}


def apply(state: str, event: str, ctx: FsmContext | None = None) -> TransitionResult:
    current = _normalize_symbol(state)
    attempted = _normalize_symbol(event)
    if current not in STATES:
        return TransitionResult(False, state, f"Estado desconocido: {state}")
    if attempted not in EVENTS:
        return TransitionResult(False, current, f"Evento desconocido: {event}")
    transition = next(
        (item for item in TRANSITIONS if item.source == current and item.event == attempted),
        None,
    )
    if transition is None:
        requirement = _REQUIREMENT_BY_EVENT.get(attempted)
        detail = f"se requiere: {requirement}" if requirement else "complete los prerequisitos"
        return TransitionResult(
            False,
            current,
            f"Transicion ilegal: {attempted} no esta permitido desde {current}; {detail}.",
        )
    context = ctx or FsmContext()
    if transition.guard is not None:
        guard_result = transition.guard(context)
        if not guard_result.ok:
            return TransitionResult(False, current, guard_result.reason)
    target = transition.target
    if target == "RECOMMENDED|REVISION_REQUIRED":
        target = str(
            _value(context.evaluation, "outcome", _value(context.evaluation, "decision", ""))
        ).upper()
    return TransitionResult(True, target)


__all__ = [
    "EVENTS",
    "STATES",
    "TRANSITIONS",
    "FsmContext",
    "GuardResult",
    "Transition",
    "TransitionResult",
    "apply",
    "real_publish_enabled",
]
