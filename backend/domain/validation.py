"""Deterministic candidate and guardrail validation using only the stdlib."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

CLICHE_CATALOG_VERSION = "1"
DEFAULT_MAX_LENGTHS = {"hook": 300, "body": 3_000, "cta": 300}
PARAPHRASE_THRESHOLD = 0.82


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    field: str | None = None
    candidate_index: int | None = None


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    issues: tuple[ValidationIssue, ...] = ()


@dataclass(frozen=True)
class ClaimValidationResult:
    claims: tuple[dict[str, Any], ...]
    issues: tuple[ValidationIssue, ...]

    @property
    def ok(self) -> bool:
        return not self.issues


@dataclass(frozen=True)
class ClicheCatalog:
    version: str
    sha256: str
    phrases: tuple[str, ...]


def _value(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, Mapping):
        return obj.get(name, default)
    return getattr(obj, name, default)


def normalize_text(text: str) -> str:
    """Normalize case, accents, whitespace, and punctuation for comparisons."""
    decomposed = unicodedata.normalize("NFKD", str(text).casefold())
    without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(re.findall(r"\w+", without_accents, flags=re.UNICODE))


def substantially_similar(first: str, second: str, threshold: float = PARAPHRASE_THRESHOLD) -> bool:
    """Detect near-duplicates by sequence and token overlap."""
    left, right = normalize_text(first), normalize_text(second)
    if not left or not right:
        return left == right
    sequence_ratio = SequenceMatcher(None, left, right).ratio()
    left_tokens, right_tokens = set(left.split()), set(right.split())
    token_ratio = len(left_tokens & right_tokens) / max(1, len(left_tokens | right_tokens))
    return sequence_ratio >= threshold or token_ratio >= threshold


def load_cliche_catalog(path: str | Path | None = None) -> ClicheCatalog:
    catalog_path = Path(path) if path else Path(__file__).with_name("cliches_v1.txt")
    raw = catalog_path.read_bytes()
    phrases = tuple(
        line.strip()
        for line in raw.decode("utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )
    return ClicheCatalog(
        version=CLICHE_CATALOG_VERSION,
        sha256=f"sha256:{hashlib.sha256(raw).hexdigest()}",
        phrases=phrases,
    )


_PROHIBITED_PATTERNS = (
    ("PERSONAL_ATTACK", re.compile(r"\b(?:idiota|imbecil|inutil|estupido)\b", re.IGNORECASE)),
    ("SECRET", re.compile(r"\b(?:api[_ -]?key|password|contrasena|token|secreto)\b", re.IGNORECASE)),
    (
        "PERSONAL_DATA",
        re.compile(
            r"\b(?:datos personales|dni|documento de identidad|direccion particular|telefono personal)\b",
            re.IGNORECASE,
        ),
    ),
    ("GUARANTEE", re.compile(r"\b(?:te garantizo|garantia de|resultado garantizado)\b", re.IGNORECASE)),
    (
        "LIVING_PERSON_IMITATION",
        re.compile(r"\b(?:escribi|habla|imita)\s+(?:como|igual que)\s+[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ]+"),
    ),
    (
        "FALSE_MANUAL_AUTHORSHIP",
        re.compile(r"\b(?:escrito|redactado)\s+(?:manualmente\s+)?por\s+juan\b", re.IGNORECASE),
    ),
)


def find_prohibited_content(text: str) -> tuple[ValidationIssue, ...]:
    return tuple(
        ValidationIssue(code, f"Contenido prohibido detectado: {match.group(0)}")
        for code, pattern in _PROHIBITED_PATTERNS
        if (match := pattern.search(str(text)))
    )


def contains_personal_experience(text: str) -> bool:
    normalized = normalize_text(text)
    return bool(
        re.search(
            r"\b(?:yo\s+)?(?:vi|lidere|dirigi|implemente|aprendi|logre|redujimos|migramos)\b",
            normalized,
        )
    )


def contains_unsourced_assertion(text: str) -> bool:
    normalized = normalize_text(text)
    has_number_or_url = bool(re.search(r"(?:\d|https?://|www\.)", str(text), re.IGNORECASE))
    has_absolute = bool(
        re.search(r"\b(?:siempre|nunca|todos|ninguno|garantiza|demostrado que)\b", normalized)
    )
    return has_number_or_url or has_absolute


def unsupported_assertion_markers(text: str, evidence: Iterable[Any]) -> tuple[str, ...]:
    """Return numbers/URLs/absolute claims that are absent from approved evidence."""
    evidence_text = " ".join(str(_value(item, "text", "")) for item in evidence).casefold()
    markers = re.findall(r"https?://\S+|www\.\S+|\b\d+(?:[.,]\d+)?%?\b", str(text), re.IGNORECASE)
    unsupported = [marker for marker in markers if marker.casefold().rstrip(".,;)") not in evidence_text]
    normalized_evidence = normalize_text(evidence_text)
    for absolute in re.findall(
        r"\b(?:siempre|nunca|todos|ninguno|garantiza|demostrado que)\b",
        normalize_text(text),
    ):
        if absolute not in normalized_evidence:
            unsupported.append(absolute)
    return tuple(dict.fromkeys(unsupported))


def _evidence_ids(evidence: Iterable[Any]) -> set[str]:
    return {str(identifier) for item in evidence if (identifier := _value(item, "id"))}


def validate_claims(claims: Iterable[Any], evidence: Iterable[Any]) -> ClaimValidationResult:
    evidence_ids = _evidence_ids(evidence)
    normalized_claims: list[dict[str, Any]] = []
    issues: list[ValidationIssue] = []
    for index, claim in enumerate(claims):
        text = str(_value(claim, "text", "")).strip()
        support = str(_value(claim, "support", "")).strip()
        valid_support = support in evidence_ids or support == "author_opinion"
        if not text or not valid_support:
            support = "needs_review"
            issues.append(
                ValidationIssue(
                    "UNSUPPORTED_CLAIM",
                    f"Claim sin soporte existente: {text or '<vacio>'}",
                    field="claims",
                    candidate_index=index,
                )
            )
        normalized_claims.append({"text": text, "support": support})
    return ClaimValidationResult(tuple(normalized_claims), tuple(issues))


def parse_json_only(raw: str) -> Any:
    """Parse exactly one JSON value and reject surrounding prose."""
    if not isinstance(raw, str):
        raise ValueError("raw output must be text")
    stripped = raw.strip()
    try:
        value, end = json.JSONDecoder().raw_decode(stripped)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON: {exc.msg}") from exc
    if stripped[end:].strip():
        raise ValueError("text outside JSON is not allowed")
    return value


def validate_candidates(
    candidates: Sequence[Any],
    evidence: Iterable[Any],
    *,
    max_lengths: Mapping[str, int] | None = None,
    require_exactly_three: bool = True,
) -> ValidationResult:
    limits = dict(DEFAULT_MAX_LENGTHS if max_lengths is None else max_lengths)
    evidence = tuple(evidence)
    issues: list[ValidationIssue] = []
    if require_exactly_three and len(candidates) != 3:
        issues.append(ValidationIssue("INVALID_CARDINALITY", "Se requieren exactamente 3 candidatos"))

    angles: list[str] = []
    hooks: list[str] = []
    bodies: list[str] = []
    for index, candidate in enumerate(candidates):
        angles.append(str(_value(candidate, "angle", "")))
        hooks.append(str(_value(candidate, "hook", "")))
        bodies.append(str(_value(candidate, "body", "")))
        full_text = " ".join(
            str(_value(candidate, field, "")) for field in ("hook", "body", "cta")
        )
        unsupported = unsupported_assertion_markers(full_text, evidence)
        if unsupported:
            issues.append(
                ValidationIssue(
                    "UNSUPPORTED_ASSERTION",
                    f"Cifra, URL o afirmacion absoluta sin evidencia: {', '.join(unsupported)}",
                    candidate_index=index,
                )
            )
        for field, maximum in limits.items():
            text = str(_value(candidate, field, ""))
            if not text.strip():
                issues.append(ValidationIssue("EMPTY_FIELD", f"{field} no puede estar vacio", field, index))
            elif len(text) > maximum:
                issues.append(
                    ValidationIssue("LENGTH_EXCEEDED", f"{field} supera {maximum} caracteres", field, index)
                )
        claim_result = validate_claims(_value(candidate, "claims", ()) or (), evidence)
        issues.extend(
            ValidationIssue(issue.code, issue.message, issue.field, index) for issue in claim_result.issues
        )
        issues.extend(
            ValidationIssue(issue.code, issue.message, issue.field, index)
            for issue in find_prohibited_content(full_text)
        )

    if len(set(angles)) != len(angles):
        issues.append(ValidationIssue("DUPLICATE_ANGLE", "Los angulos deben ser unicos"))
    for first in range(len(candidates)):
        for second in range(first + 1, len(candidates)):
            if normalize_text(hooks[first]) == normalize_text(hooks[second]):
                issues.append(
                    ValidationIssue("DUPLICATE_HOOK", f"Hooks {first + 1} y {second + 1} son identicos")
                )
            if normalize_text(bodies[first]) == normalize_text(bodies[second]):
                issues.append(
                    ValidationIssue("DUPLICATE_BODY", f"Bodies {first + 1} y {second + 1} son identicos")
                )
            elif substantially_similar(bodies[first], bodies[second]):
                issues.append(
                    ValidationIssue(
                        "SUBSTANTIAL_PARAPHRASE",
                        f"Bodies {first + 1} y {second + 1} son parafrasis sustanciales",
                    )
                )
    return ValidationResult(not issues, tuple(issues))


__all__ = [
    "CLICHE_CATALOG_VERSION",
    "ClicheCatalog",
    "ClaimValidationResult",
    "ValidationIssue",
    "ValidationResult",
    "contains_personal_experience",
    "contains_unsourced_assertion",
    "find_prohibited_content",
    "load_cliche_catalog",
    "normalize_text",
    "parse_json_only",
    "substantially_similar",
    "unsupported_assertion_markers",
    "validate_candidates",
    "validate_claims",
]
