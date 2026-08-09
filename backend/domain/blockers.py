"""Blocker activation and reproducible recommendation decisions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Literal, Mapping, Sequence

from .validation import (
    contains_personal_experience,
    contains_unsourced_assertion,
    find_prohibited_content,
    unsupported_assertion_markers,
)

THRESHOLD_RECOMMEND = 72
MIN_TOP_GAP = 4
THRESHOLD_REVISION_LOW = 60


@dataclass(frozen=True)
class Blocker:
    code: str
    message: str
    detail: str | None = None


@dataclass(frozen=True)
class Decision:
    outcome: Literal["RECOMMENDED", "REVISION_REQUIRED"]
    best_candidate_id: int | None
    reason: str
    brief_needs_revision: bool = False


def _value(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, Mapping):
        return obj.get(name, default)
    return getattr(obj, name, default)


def activate_blockers(candidate: Any, evidence: Iterable[Any]) -> tuple[Blocker, ...]:
    evidence = tuple(evidence)
    evidence_ids = {
        str(identifier) for item in evidence if (identifier := _value(item, "id"))
    }
    body = " ".join(
        str(_value(candidate, field, "")) for field in ("hook", "body", "cta")
    )
    blockers: list[Blocker] = []
    for claim in _value(candidate, "claims", ()) or ():
        text = str(_value(claim, "text", ""))
        support = str(_value(claim, "support", ""))
        supported = support in evidence_ids or support == "author_opinion"
        if not supported:
            blockers.append(Blocker("UNSUPPORTED_CLAIM", "Claim sin evidencia aprobada", text))
        if support == "needs_review":
            blockers.append(Blocker("NEEDS_REVIEW", "Claim needs_review sin resolver", text))
        if contains_personal_experience(text) and not supported:
            blockers.append(
                Blocker("INVENTED_EXPERIENCE", "Experiencia personal sin evidencia", text)
            )
        elif contains_unsourced_assertion(text) and not supported:
            blockers.append(Blocker("UNSUPPORTED_ASSERTION", "Cifra o afirmacion sin fuente", text))

    if contains_personal_experience(body):
        evidence_text = " ".join(str(_value(item, "text", "")) for item in evidence)
        if not contains_personal_experience(evidence_text):
            blockers.append(
                Blocker("INVENTED_EXPERIENCE", "Experiencia personal sin evidencia", body)
            )
    for marker in unsupported_assertion_markers(body, evidence):
        blockers.append(
            Blocker("UNSUPPORTED_ASSERTION", "Cifra o afirmacion sin fuente", marker)
        )
    for issue in find_prohibited_content(body):
        blockers.append(Blocker("PROHIBITED_CONTENT", issue.message, issue.code))

    unique: dict[tuple[str, str | None], Blocker] = {}
    for blocker in blockers:
        unique[(blocker.code, blocker.detail)] = blocker
    return tuple(unique.values())


def _score_tuple(score: Any, fallback_id: int) -> tuple[int, float]:
    candidate_id = int(_value(score, "candidate_id", fallback_id))
    value = float(_value(score, "score_final", _value(score, "score", score)))
    return candidate_id, value


def _blockers_for(candidate_id: int, blockers: Any) -> tuple[Any, ...]:
    if isinstance(blockers, Mapping):
        return tuple(blockers.get(candidate_id, blockers.get(str(candidate_id), ())) or ())
    return tuple(blockers or ())


def decide(scores: Sequence[Any], blockers: Any, top2_gap: float | None = None) -> Decision:
    if not scores:
        return Decision(
            "REVISION_REQUIRED",
            None,
            "No hay scores validos; revisar el brief y la evaluacion.",
            brief_needs_revision=True,
        )
    ranked = sorted(
        (_score_tuple(score, index) for index, score in enumerate(scores, 1)),
        key=lambda item: (-item[1], item[0]),
    )
    best_id, best_score = ranked[0]
    computed_gap = best_score - ranked[1][1] if len(ranked) > 1 else best_score
    gap = computed_gap if top2_gap is None else float(top2_gap)
    active_blockers = _blockers_for(best_id, blockers)

    if active_blockers:
        return Decision(
            "REVISION_REQUIRED",
            best_id,
            "El mejor candidato tiene blockers activos que deben resolverse.",
        )
    if best_score >= THRESHOLD_RECOMMEND and gap >= MIN_TOP_GAP:
        return Decision(
            "RECOMMENDED",
            best_id,
            f"Score {best_score:g} y brecha {gap:g}: supera los umbrales iniciales.",
        )
    if best_score < THRESHOLD_REVISION_LOW:
        return Decision(
            "REVISION_REQUIRED",
            best_id,
            "Todos los candidatos estan bajo 60; reformular el brief antes de regenerar.",
            brief_needs_revision=True,
        )
    return Decision(
        "REVISION_REQUIRED",
        best_id,
        "Se requieren las dos mejoras de mayor impacto antes de recomendar.",
    )


__all__ = [
    "MIN_TOP_GAP",
    "THRESHOLD_RECOMMEND",
    "THRESHOLD_REVISION_LOW",
    "Blocker",
    "Decision",
    "activate_blockers",
    "decide",
]
