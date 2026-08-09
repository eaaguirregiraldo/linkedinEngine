"""Contrato visual determinístico derivado de la tesis (F.1, VIS-01/03).

Sin LLM y sin red (design §7.1): un mapa versionado keyword→concepto traduce
frases literales de la tesis en un concepto visual NO decorativo y en
elementos ``{element_id, kind, description, rationale}`` donde cada
``rationale`` cita una frase/concepto literal de la tesis (VIS-03).

La salida es un dict con la forma del contrato canónico ``VisualContract``
(api.schemas): ``thesis, concept, elements, alt_text, status`` — este módulo
no importa el contrato pydantic para mantener el alcance de dependencias de
F (B + A1, tasks.md §2).
"""
from __future__ import annotations

import re
from typing import Any

__all__ = [
    "CONTRACT_VERSION",
    "CONCEPT_RULES_V1",
    "FALLBACK_CONCEPT",
    "ANGLE_META_V1",
    "get_field",
    "build_visual_contract",
]

# Versión del mapa keyword→concepto (design §7.1: "cambio exige versión nueva").
CONTRACT_VERSION = "1.0.0"

# ── Mapa keyword→concepto versionado ────────────────────────────────────────
# Cada regla: keywords (frases literales buscadas en la tesis, en minúsculas),
# concepto, metáfora y capas estructurales. Las reglas se evalúan en orden y
# gana la primera con un keyword presente en la tesis.
CONCEPT_RULES_V1: tuple[dict[str, Any], ...] = (
    {
        "keywords": ("conocimiento operativo", "conocimiento tácito"),
        "concept": (
            "diagrama de dos capas: código visible vs conocimiento operativo oculto"
        ),
        "metaphor": (
            "dos capas superpuestas: una franja superior delgada representa el "
            "código y una franja inferior mucho mayor representa las reglas, "
            "excepciones y el conocimiento tácito"
        ),
        "layers": (
            "capa visible: código y sintaxis",
            "capa oculta: reglas de negocio, excepciones y conocimiento tácito",
        ),
    },
    {
        "keywords": ("reglas de negocio", "mainframe", "décadas"),
        "concept": (
            "mainframe como caja de reglas de negocio acumuladas por décadas"
        ),
        "metaphor": (
            "una caja sólida central que acumula capas internas de reglas de "
            "negocio difíciles de tocar"
        ),
        "layers": (
            "capa exterior: el sistema que sigue en producción",
            "capas internas: reglas de negocio que nadie se atreve a tocar",
        ),
    },
    {
        "keywords": ("modelo de riesgo", "modernizar", "cambiar de lenguaje"),
        "concept": "contraste entre cambiar el lenguaje y cambiar el modelo de riesgo",
        "metaphor": (
            "dos bloques enfrentados: uno representa el lenguaje y el otro el "
            "modelo de riesgo de la operación"
        ),
        "layers": (
            "bloque de lenguaje: sintaxis y tecnología",
            "bloque de riesgo: decisiones operativas y de negocio",
        ),
    },
)

# Concepto de respaldo: estructural, derivado de la tesis (nunca decorativo).
FALLBACK_CONCEPT = (
    "estructura argumental de la tesis: una idea central sostenida por evidencia"
)
FALLBACK_METAPHOR = (
    "una única figura central que sostiene una capa de evidencia y una capa de conclusión"
)
FALLBACK_LAYERS = (
    "capa de evidencia que sostiene la tesis",
    "capa de conclusión derivada de la tesis",
)

# Metadatos por ángulo del candidato (determinista; el elemento de dominio
# refleja el ángulo elegido).
ANGLE_META_V1: dict[str, dict[str, str]] = {
    "problem-story": {
        "label": "Historia de problema",
        "domain_description": "el riesgo operativo que plantea el problema",
    },
    "practical-framework": {
        "label": "Marco práctico",
        "domain_description": "el marco práctico aplicable a la decisión",
    },
    "argued-position": {
        "label": "Posición argumentada",
        "domain_description": "la posición defendida con evidencia",
    },
}

_WHITESPACE_RE = re.compile(r"\s+")


def get_field(obj: Any, name: str, default: Any = None) -> Any:
    """Lee un campo de un dict o de un objeto con atributos (shape-agnostic)."""
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _normalize(text: str) -> str:
    """Minúsculas + colapso de espacios en blanco (sin tocar la fuente)."""
    return _WHITESPACE_RE.sub(" ", text).strip().lower()


def _match_concept_rule(thesis: str) -> tuple[dict[str, Any] | None, str]:
    """Primera regla cuyo keyword aparezca en la tesis; devuelve (regla, frase)."""
    normalized = _normalize(thesis)
    for rule in CONCEPT_RULES_V1:
        for keyword in rule["keywords"]:
            if keyword in normalized:
                return rule, keyword
    return None, ""


def _literal_quote(thesis: str, keyword: str, max_chars: int = 120) -> str:
    """Fragmento literal de la tesis citado en los rationales (VIS-03).

    Si hay keyword coincidente devuelve la aparición original en la tesis
    (case-insensitive); si no, un prefijo literal de la tesis (sin elipsis,
    para que la cita siga siendo substring exacto).
    """
    if keyword:
        low = thesis.lower()
        start = low.find(keyword)
        if start != -1:
            return thesis[start : start + len(keyword)].strip()
    prefix = _WHITESPACE_RE.sub(" ", thesis).strip()
    return prefix[:max_chars].rstrip() if len(prefix) > max_chars else prefix


def _first_clause(thesis: str, max_chars: int = 120) -> str:
    """Primera cláusula de la tesis (para rationales del fallback)."""
    clause = re.split(r"[;.\n]", thesis, maxsplit=1)[0].strip()
    if not clause:
        clause = thesis
    return _literal_quote(thesis, "", max_chars) if len(clause) > max_chars else clause


def _candidate_angle(candidate: Any) -> str:
    angle = get_field(candidate, "angle", "")
    if isinstance(angle, str) and angle in ANGLE_META_V1:
        return angle
    return "argued-position"


def build_visual_contract(thesis: str, candidate: Any) -> dict[str, Any]:
    """Deriva el contrato visual de la tesis (F.1, VIS-01/03).

    Determinístico: misma tesis + mismo candidato → mismo contrato. Cada
    elemento cita una frase literal de la tesis en su ``rationale``.
    """
    thesis = _WHITESPACE_RE.sub(" ", thesis or "").strip()
    rule, keyword = _match_concept_rule(thesis)
    if rule is not None:
        concept = rule["concept"]
        metaphor = rule["metaphor"]
        layers = rule["layers"]
        quote = _literal_quote(thesis, keyword)
    else:
        concept = FALLBACK_CONCEPT
        metaphor = FALLBACK_METAPHOR
        layers = FALLBACK_LAYERS
        quote = _first_clause(thesis)

    angle = _candidate_angle(candidate)
    angle_meta = ANGLE_META_V1[angle]

    elements: list[dict[str, str]] = [
        {
            "element_id": "el-01",
            "kind": "metaphor",
            "description": metaphor,
            "rationale": f'La metáfora visual se deriva de la frase literal de la tesis: "{quote}".',
        }
    ]
    for index, layer in enumerate(layers, start=2):
        elements.append(
            {
                "element_id": f"el-{index:02d}",
                "kind": "structure",
                "description": layer,
                "rationale": f'Estructura derivada de la frase de la tesis: "{quote}".',
            }
        )
    elements.append(
        {
            "element_id": f"el-{len(elements) + 1:02d}",
            "kind": "domain",
            "description": (
                f"El ángulo {angle_meta['label']} destaca "
                f"{angle_meta['domain_description']} de la tesis"
            ),
            "rationale": f'Elemento de dominio fundamentado en la tesis: "{quote}".',
        }
    )
    elements.append(
        {
            "element_id": f"el-{len(elements) + 1:02d}",
            "kind": "text",
            "description": "tesis corta legible en la tarjeta",
            "rationale": f'El texto de la tarjeta resume la afirmación central: "{quote}".',
        }
    )

    alt_text = f"Tarjeta editorial con {concept}. La imagen ilustra la tesis: {thesis}"
    return {
        "thesis": thesis,
        "concept": concept,
        "elements": elements,
        "alt_text": alt_text,
        "status": "VISUAL_DRAFT",
    }
