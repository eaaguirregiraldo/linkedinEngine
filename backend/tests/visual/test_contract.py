# backend/tests/visual/test_contract.py
"""Tests de `visual.contract` — Batch F, tarea F.1.

Cubre el criterio de F.1: el contrato para la tesis demo de design §9.3
produce un concepto NO decorativo (VIS-01), todo elemento tiene `rationale`
no vacío que cita una frase/concepto LITERAL de la tesis (VIS-03), el mapa
keyword→concepto es versionado, y el contrato es determinístico.
"""

import re

import pytest

from visual.contract import (
    ANGLE_META_V1,
    CONCEPT_RULES_V1,
    CONTRACT_VERSION,
    FALLBACK_CONCEPT,
    build_visual_contract,
)

# Tesis demo de design §9.3 (seed) — la primera es el ejemplo oficial de VIS-01.
THESIS_DEMO_1 = (
    "Migrar COBOL no es traducir sintaxis; es recuperar conocimiento "
    "operativo antes de tocar código"
)
THESIS_DEMO_2 = (
    "El mainframe sigue en producción por una razón: décadas de reglas de "
    "negocio que nadie se atreve a tocar"
)
THESIS_DEMO_3 = "Modernizar no es cambiar de lenguaje; es cambiar el modelo de riesgo"

# Patrones decorativos que el concepto MUST NO repetir (VIS-01 escenario 2):
# la imagen "no decora", argumenta.
DECORATIVE_PATTERNS = (
    "computadora antigua",
    "código verde",
    "codigo verde",
    "terminal retro",
    "decorativo",
    "foto de stock",
)


def make_candidate(angle: str = "problem-story") -> dict:
    """Candidato mínimo (dict, como lo consumiría el workflow desde DB)."""
    return {"angle": angle, "hook": "Hook", "body": "Body", "cta": "CTA"}


def _quoted_fragments(text: str) -> list[str]:
    """Fragmentos citados entre comillas dobles dentro del rationale."""
    return re.findall(r'"([^"]+)"', text)


# ── Mapa keyword→concepto versionado ────────────────────────────────────────


def test_contract_version_is_versioned():
    assert CONTRACT_VERSION == "1.0.0"


def test_concept_rules_non_empty_and_stable():
    assert CONCEPT_RULES_V1, "el mapa keyword→concepto no puede estar vacío"
    for rule in CONCEPT_RULES_V1:
        assert rule["keywords"], "cada regla exige al menos un keyword"
        assert rule["concept"].strip(), "cada regla exige concepto no vacío"
        assert rule["metaphor"].strip(), "cada regla exige metáfora no vacía"
        assert rule["layers"], "cada regla exige al menos una capa estructural"


# ── VIS-01: contrato completo para tesis demo, concepto NO decorativo ───────


def test_demo_thesis_produces_two_layer_concept():
    contract = build_visual_contract(THESIS_DEMO_1, make_candidate())
    assert contract["concept"].strip()
    # Concepto esperado por VIS-01: "diagrama de dos capas: código vs
    # conocimiento operativo oculto" (SOLUTION.md §8).
    assert "dos capas" in contract["concept"]
    assert "conocimiento operativo" in contract["concept"]


@pytest.mark.parametrize("thesis", [THESIS_DEMO_1, THESIS_DEMO_2, THESIS_DEMO_3])
def test_concept_is_never_decorative(thesis):
    contract = build_visual_contract(thesis, make_candidate())
    concept = contract["concept"].lower()
    for pattern in DECORATIVE_PATTERNS:
        assert pattern not in concept, f"concepto decorativo detectado: {pattern}"
    assert concept != contract["thesis"].lower(), "concepto no puede repetir la tesis"


# ── VIS-03: todo elemento con rationale que cita la tesis ───────────────────


def test_every_element_has_non_empty_rationale():
    contract = build_visual_contract(THESIS_DEMO_1, make_candidate())
    assert contract["elements"], "el contrato debe definir elementos"
    for element in contract["elements"]:
        assert element["rationale"].strip(), f"{element['element_id']}: rationale vacío"


def test_every_rationale_cites_literal_thesis_phrase():
    contract = build_visual_contract(THESIS_DEMO_1, make_candidate())
    for element in contract["elements"]:
        fragments = _quoted_fragments(element["rationale"])
        assert fragments, f"{element['element_id']}: rationale sin cita a la tesis"
        for fragment in fragments:
            assert (
                fragment in THESIS_DEMO_1
            ), f"{element['element_id']}: {fragment!r} no es literal de la tesis"


def test_elements_cover_metaphor_structure_domain_and_text():
    contract = build_visual_contract(THESIS_DEMO_1, make_candidate())
    kinds = {element["kind"] for element in contract["elements"]}
    assert {"metaphor", "structure", "domain", "text"} <= kinds


def test_alt_text_is_specific_and_related():
    contract = build_visual_contract(THESIS_DEMO_1, make_candidate())
    assert contract["alt_text"].strip()
    assert THESIS_DEMO_1 in contract["alt_text"], "alt_text debe citar la tesis"


# ── Determinismo (VIS-02, HARN-03 aplicado al visual) ───────────────────────


def test_same_thesis_and_candidate_produces_identical_contract():
    first = build_visual_contract(THESIS_DEMO_1, make_candidate("practical-framework"))
    second = build_visual_contract(THESIS_DEMO_1, make_candidate("practical-framework"))
    assert first == second


def test_different_thesis_produces_different_concept():
    concept_1 = build_visual_contract(THESIS_DEMO_1, make_candidate())["concept"]
    concept_2 = build_visual_contract(THESIS_DEMO_2, make_candidate())["concept"]
    assert concept_1 != concept_2


# ── El ángulo del candidato moldea el elemento de dominio ───────────────────


def test_candidate_angle_drives_domain_element():
    domain_problem = [
        e
        for e in build_visual_contract(THESIS_DEMO_1, make_candidate("problem-story"))[
            "elements"
        ]
        if e["kind"] == "domain"
    ][0]
    domain_argument = [
        e
        for e in build_visual_contract(
            THESIS_DEMO_1, make_candidate("argued-position")
        )["elements"]
        if e["kind"] == "domain"
    ][0]
    assert domain_problem != domain_argument
    assert "riesgo" in domain_problem["description"]
    assert domain_argument["description"].strip()


def test_angle_metadata_covers_all_three_angles():
    assert set(ANGLE_META_V1) == {
        "problem-story",
        "practical-framework",
        "argued-position",
    }
    for meta in ANGLE_META_V1.values():
        assert meta["label"].strip()
        assert meta["domain_description"].strip()


# ── Fallback determinístico sin keywords conocidos ───────────────────────────


def test_fallback_concept_for_unknown_thesis():
    unknown = "La documentación técnica debe mantenerse cerca del código fuente"
    contract = build_visual_contract(unknown, make_candidate())
    assert contract["concept"] == FALLBACK_CONCEPT
    for element in contract["elements"]:
        for fragment in _quoted_fragments(element["rationale"]):
            assert fragment in unknown, "fallback: la cita debe seguir siendo literal"


# ── Forma del contrato (compatible con VisualContract pydantic) ─────────────


def test_contract_shape_matches_visual_contract_schema():
    contract = build_visual_contract(THESIS_DEMO_1, make_candidate())
    assert set(contract) == {"thesis", "concept", "elements", "alt_text", "status"}
    assert contract["status"] == "VISUAL_DRAFT"
    for element in contract["elements"]:
        assert set(element) == {"element_id", "kind", "description", "rationale"}
