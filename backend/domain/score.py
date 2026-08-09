"""Transparent editorial scoring formula and deterministic penalties."""

from __future__ import annotations

import math
from typing import Any, Iterable, Mapping, Sequence

from .validation import (
    contains_personal_experience,
    contains_unsourced_assertion,
    normalize_text,
    substantially_similar,
)

DIMENSION_WEIGHTS = {
    "hook": 0.20,
    "niche_relevance": 0.20,
    "specificity_evidence": 0.20,
    "clarity": 0.15,
    "conversation_potential": 0.15,
    "voice_fit": 0.10,
}

PENALTY_RISK_INVENTED_EXPERIENCE = 25
PENALTY_RISK_PER_UNSUPPORTED_CLAIM = 10
PENALTY_RISK_MAX = 25
PENALTY_GENERICITY_PER_CLICHE = 5
PENALTY_GENERICITY_MAX = 15


def _value(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, Mapping):
        return obj.get(name, default)
    return getattr(obj, name, default)


def dimension_100(rating: int) -> float:
    if isinstance(rating, bool) or not isinstance(rating, int) or not 0 <= rating <= 5:
        raise ValueError("rating must be an integer between 0 and 5")
    return float(rating * 20)


def base_score(dimensions: Mapping[str, Any]) -> float:
    missing = set(DIMENSION_WEIGHTS) - set(dimensions)
    if missing:
        raise ValueError(f"missing dimensions: {', '.join(sorted(missing))}")
    return sum(
        DIMENSION_WEIGHTS[name]
        * dimension_100(int(_value(dimensions[name], "rating", dimensions[name])))
        for name in DIMENSION_WEIGHTS
    )


def clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    if lo > hi:
        raise ValueError("lower bound cannot exceed upper bound")
    return min(hi, max(lo, float(value)))


def _evidence_ids(evidence: Iterable[Any]) -> set[str]:
    return {str(identifier) for item in evidence if (identifier := _value(item, "id"))}


def penalizacion_riesgo(claims: Iterable[Any], evidence: Iterable[Any]) -> float:
    evidence_ids = _evidence_ids(evidence)
    unsupported = 0
    invented_experience = False
    for claim in claims:
        text = str(_value(claim, "text", ""))
        support = str(_value(claim, "support", ""))
        supported = support in evidence_ids or support == "author_opinion"
        if contains_personal_experience(text) and not supported:
            invented_experience = True
        elif not supported and (contains_unsourced_assertion(text) or support == "needs_review"):
            unsupported += 1
    if invented_experience:
        return float(PENALTY_RISK_INVENTED_EXPERIENCE)
    return float(min(PENALTY_RISK_MAX, unsupported * PENALTY_RISK_PER_UNSUPPORTED_CLAIM))


def penalizacion_genericidad(
    text: str,
    cliche_catalog: Iterable[str],
    other_candidates: Sequence[Any],
) -> float:
    normalized = normalize_text(text)
    phrases = getattr(cliche_catalog, "phrases", cliche_catalog)
    triggers = sum(1 for phrase in phrases if normalize_text(phrase) in normalized)
    if any(
        substantially_similar(text, str(_value(candidate, "body", candidate)))
        for candidate in other_candidates
    ):
        triggers += 1
    return float(min(PENALTY_GENERICITY_MAX, triggers * PENALTY_GENERICITY_PER_CLICHE))


def score_final(base: float, risk: float, generic: float) -> int:
    for value in (base, risk, generic):
        if not math.isfinite(float(value)):
            raise ValueError("score values must be finite")
    return round(clamp(float(base) - float(risk) - float(generic)))


def validate_dimension_scores(dimensions: Mapping[str, Any]) -> bool:
    if set(dimensions) != set(DIMENSION_WEIGHTS):
        return False
    for score in dimensions.values():
        rating = _value(score, "rating")
        quote = str(_value(score, "quote", "")).strip()
        rubric_rule = str(_value(score, "rubric_rule", "")).strip()
        if isinstance(rating, bool) or not isinstance(rating, int) or not 0 <= rating <= 5:
            return False
        if not quote or not rubric_rule:
            return False
    return True


__all__ = [
    "DIMENSION_WEIGHTS",
    "PENALTY_GENERICITY_MAX",
    "PENALTY_GENERICITY_PER_CLICHE",
    "PENALTY_RISK_INVENTED_EXPERIENCE",
    "PENALTY_RISK_MAX",
    "PENALTY_RISK_PER_UNSUPPORTED_CLAIM",
    "base_score",
    "clamp",
    "dimension_100",
    "penalizacion_genericidad",
    "penalizacion_riesgo",
    "score_final",
    "validate_dimension_scores",
]
