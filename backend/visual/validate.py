"""Validación automática del contrato visual (F.2, VIS-03/04/05/07).

El sistema MUST validar automáticamente la completitud del contrato:
todo elemento con ``rationale`` no vacío (VIS-03), ``alt_text`` obligatorio
y específico (VIS-04), elementos prohibidos ausentes (marcas no autorizadas,
texto ilegible, estereotipos retro sin relación argumental — VIS-05/07).
La pertinencia semántica final la aprueba una persona (VIS-06) en el
workflow (G), no acá.

Acepta dict o pydantic ``VisualContract`` (shape-agnostic); la semántica de
blancos vive en esta capa (el contrato pydantic solo valida ``min_length``).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from visual.contract import get_field

__all__ = [
    "ValidationResult",
    "GENERIC_ALT_TEXTS",
    "FORBIDDEN_MARK_PATTERNS",
    "STEREOTYPE_KEYWORDS",
    "ILLEGIBLE_TEXT_MAX_CHARS",
    "validate_visual_contract",
    "is_valid",
]

# ── Catálogos de rechazo (deterministas, versionados en el código) ──────────

# Alt texts genéricos: no describen el contenido ni su relación con la tesis.
GENERIC_ALT_TEXTS = frozenset(
    {
        "imagen",
        "visual",
        "tarjeta",
        "gráfico",
        "grafico",
        "svg",
        "ilustración",
        "ilustracion",
        "foto",
        "imagen del contenido",
        "imagen decorativa",
        "una imagen",
    }
)

# Marcas no autorizadas (design §13.5 / VIS-07): logos, marcas registradas.
FORBIDDEN_MARK_PATTERNS = (
    "logo",
    "marca registrada",
    "®",
    "™",
    "watermark",
    "marca de agua",
)

# Esterotipos retro que solo decoran si el rationale no los defiende desde la
# tesis (VIS-07, SOLUTION.md §8).
STEREOTYPE_KEYWORDS = (
    "cinta magnética",
    "cinta magnetica",
    "tarjeta perforada",
    "punch card",
    "disquete",
    "diskette",
    "terminal verde",
    "código verde",
    "codigo verde",
    "computadora antigua",
    "mainframe antiguo",
)

# Texto de imagen más largo que esto se considera ilegible (VIS-05/07).
ILLEGIBLE_TEXT_MAX_CHARS = 140

_STOPWORDS = frozenset(
    {
        "para",
        "con",
        "por",
        "que",
        "esta",
        "este",
        "esta",
        "del",
        "las",
        "los",
        "una",
        "uno",
        "sus",
        "desde",
        "hacia",
        "como",
        "mas",
        "más",
        "sin",
        "sobre",
        "entre",
    }
)
_WORD_RE = re.compile(r"[a-záéíóúñü0-9]{5,}")


@dataclass
class ValidationResult:
    """Resultado de la validación automática del contrato visual."""

    valid: bool
    errors: list[str] = field(default_factory=list)


def _meaningful_words(text: str) -> set[str]:
    """Palabras significativas (≥5 chars, sin stopwords) de un texto."""
    return {
        match
        for match in _WORD_RE.findall(text.lower())
        if match not in _STOPWORDS
    }


def _contains_any(text: str, patterns: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(pattern.lower() in lowered for pattern in patterns)


def _is_generic_alt_text(alt_text: str) -> bool:
    return alt_text.strip().lower() in GENERIC_ALT_TEXTS


def _relates_to_thesis(text: str, thesis: str) -> bool:
    """¿El texto comparte palabras significativas con la tesis (específico)?"""
    thesis_words = _meaningful_words(thesis)
    if not thesis_words:
        return True  # sin anclas posibles no se puede juzgar → no rechazar
    return bool(_meaningful_words(text) & thesis_words)


def validate_visual_contract(contract: Any) -> ValidationResult:
    """Valida el contrato visual; devuelve errores accionables (VIS-03/04/05/07)."""
    errors: list[str] = []

    thesis = (get_field(contract, "thesis") or "").strip()
    if not thesis:
        errors.append("el contrato no define una tesis no vacía")

    elements = get_field(contract, "elements") or []
    if not elements:
        errors.append("el contrato no define elementos visuales")

    for element in elements:
        element_id = (get_field(element, "element_id") or "?").strip() or "?"
        description = (get_field(element, "description") or "").strip()
        rationale = (get_field(element, "rationale") or "").strip()
        kind = (get_field(element, "kind") or "").strip().lower()

        if not description:
            errors.append(f"elemento {element_id}: descripción vacía")
        if not rationale:
            errors.append(f"elemento {element_id}: rationale vacío (VIS-03)")

        if description and _contains_any(description, FORBIDDEN_MARK_PATTERNS):
            errors.append(f"elemento {element_id}: marca no autorizada (VIS-07)")
        if kind == "text" and len(description) > ILLEGIBLE_TEXT_MAX_CHARS:
            errors.append(f"elemento {element_id}: texto ilegible en la imagen (VIS-07)")
        if description and _contains_any(description, STEREOTYPE_KEYWORDS):
            if not (rationale and _relates_to_thesis(rationale, thesis)):
                errors.append(
                    f"elemento {element_id}: estereotipo retro sin relación argumental (VIS-07)"
                )

    alt_text = (get_field(contract, "alt_text") or "").strip()
    if not alt_text:
        errors.append("alt_text vacío (VIS-04)")
    elif _is_generic_alt_text(alt_text):
        errors.append("alt_text genérico: no describe el contenido (VIS-04)")
    elif thesis and not _relates_to_thesis(alt_text, thesis):
        errors.append("alt_text no específico: no referencia la tesis (VIS-04)")

    return ValidationResult(valid=not errors, errors=errors)


def is_valid(contract: Any) -> bool:
    """Conveniencia: ¿el contrato pasa la validación automática?"""
    return validate_visual_contract(contract).valid
