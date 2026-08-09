"""Tests de `DemoProvider` (HARN-03, design §6.3).

Cubre: determinismo byte a byte, derivación de los 3 ángulos desde el brief,
claims→evidence ids, salida forzada inválida y reuso de los MISMOS guards del
dominio (penalizaciones y blockers) en el evaluador demo.
"""
import json

import pytest

from ai.demo_provider import DemoProvider, INVALID_RAW_OUTPUT
from api.schemas import BriefIn, EvidenceItem
from domain.blockers import activate_blockers
from domain.score import penalizacion_genericidad, penalizacion_riesgo
from domain.validation import load_cliche_catalog


def _brief() -> BriefIn:
    return BriefIn(
        thesis="Migrar COBOL no es traducir sintaxis: es traducir reglas de negocio",
        audience="equipos de mainframe",
        objective="generar contenido para operaciones y arquitectura",
        evidence=[
            EvidenceItem(
                id="ev-1",
                text="El inventario actual incluye jobs JCL y excepciones operativas",
                type="known_facts",
            ),
            EvidenceItem(
                id="ev-2",
                text="Las reglas de negocio que corren hoy no están documentadas",
                type="open_questions",
            ),
        ],
    )


def _parse(raw: str) -> dict:
    return json.loads(raw)


# ── HARN-03: determinismo y derivación del brief ────────────────────────────


def test_same_brief_same_output_byte_to_byte():
    provider = DemoProvider()
    first = provider.generate_candidates(_brief())
    second = provider.generate_candidates(_brief())
    assert first == second


def test_generation_returns_exactly_three_candidates_with_unique_angles():
    output = _parse(DemoProvider().generate_candidates(_brief()))
    candidates = output["candidates"]
    assert len(candidates) == 3
    angles = [candidate["angle"] for candidate in candidates]
    assert sorted(angles) == ["argued-position", "practical-framework", "problem-story"]
    assert len(set(angles)) == 3


def test_candidates_derive_thesis_and_audience_from_brief():
    brief = _brief()
    output = _parse(DemoProvider().generate_candidates(brief))
    for candidate in output["candidates"]:
        text = " ".join((candidate["hook"], candidate["body"], candidate["cta"]))
        # La tesis viaja a los tres borradores (HARN-03: sin random ni red).
        assert brief.thesis in candidate["body"]
        assert brief.audience in candidate["body"]
        assert text.strip()


def test_claims_map_to_evidence_ids_from_brief():
    brief = _brief()
    output = _parse(DemoProvider().generate_candidates(brief))
    evidence_ids = {item.id for item in brief.evidence}
    for candidate in output["candidates"]:
        for claim in candidate["claims"]:
            assert claim["support"] in evidence_ids
            assert claim["text"].strip()


def test_no_evidence_means_no_claims():
    brief = BriefIn(thesis="Tesis sin evidencia")
    output = _parse(DemoProvider().generate_candidates(brief))
    assert len(brief.evidence) == 0
    for candidate in output["candidates"]:
        assert candidate["claims"] == []


def test_force_invalid_returns_invalid_raw_output():
    output = DemoProvider(force_invalid=True).generate_candidates(_brief())
    assert output == INVALID_RAW_OUTPUT


# ── HARN-03: el evaluador demo reusa los guards del dominio ─────────────────


def test_evaluator_reuses_domain_risk_penalty():
    """Cifra sin fuente en un claim → misma penalización que el dominio.

    `penalizacion_riesgo` inspecciona SOLO los claims (no el body): un número
    sin fuente suma 10; una experiencia personal inventada en un claim vale 25.
    """
    provider = DemoProvider()
    brief = _brief()
    unsourced = {
        "angle": "problem-story",
        "hook": "Reducimos 40% el costo de una migración",
        "body": "El proceso completo tomó seis meses de trabajo.",
        "cta": "¿Cómo medís el riesgo de tu migración?",
        "claims": [{"text": "Reducimos 40% el costo", "support": "needs_review"}],
    }
    invented = {
        "angle": "problem-story",
        "hook": "Lideré una migración en 2024",
        "body": "El proceso completo tomó seis meses de trabajo.",
        "cta": "¿Cómo medís el riesgo de tu migración?",
        "claims": [{"text": "Lideré una migración en 2024", "support": "needs_review"}],
    }
    evidence = []  # sin evidencia aprobada → claim sin soporte
    scores = _parse(provider.evaluate_candidates([unsourced, invented], brief, "1"))
    domain_risk_unsourced = penalizacion_riesgo(unsourced["claims"], evidence)
    domain_risk_invented = penalizacion_riesgo(invented["claims"], evidence)
    demo_risks = [score["penalties"]["risk"] for score in scores["candidate_scores"]]
    assert demo_risks == [
        int(domain_risk_unsourced),
        int(domain_risk_invented),
    ]
    assert demo_risks == [10, 25]  # PENALTY_RISK_PER_UNSUPPORTED_CLAIM / _INVENTED_EXPERIENCE


def test_evaluator_reuses_domain_genericity_penalty():
    """Cliché del catálogo (fixture regression_generic) → misma penalización."""
    provider = DemoProvider()
    brief = _brief()
    candidate = {
        "angle": "argued-position",
        "hook": "El futuro ya llegó",
        "body": "En un mundo en constante evolución, COBOL está más vivo que nunca.",
        "cta": "¿Qué opinas?",
        "claims": [],
    }
    output = _parse(provider.evaluate_candidates([candidate], brief, "1"))
    catalog = load_cliche_catalog()
    domain_generic = penalizacion_genericidad(
        candidate["body"], catalog.phrases, []
    )
    demo_generic = output["candidate_scores"][0]["penalties"]["generic"]
    assert demo_generic == int(domain_generic)
    assert demo_generic >= 5


def test_evaluator_activates_same_blockers_as_domain():
    provider = DemoProvider()
    brief = _brief()
    candidate = {
        "angle": "problem-story",
        "hook": "Reducimos 40% el costo de una migración",
        "body": "Lideré esa migración y obtuvimos el resultado en seis meses.",
        "cta": "¿Cómo medís el riesgo de tu migración?",
        "claims": [{"text": "Reducimos 40% el costo", "support": "needs_review"}],
    }
    evidence = []
    output = _parse(provider.evaluate_candidates([candidate], brief, "1"))
    domain_codes = {blocker.code for blocker in activate_blockers(candidate, evidence)}
    demo_codes = {blocker["code"] for blocker in output["candidate_scores"][0]["blockers"]}
    assert demo_codes == domain_codes
    assert "UNSUPPORTED_CLAIM" in demo_codes


def test_evaluator_output_is_contract_complete():
    """Cada score trae las 6 dimensiones con rating/quote/rubric_rule."""
    provider = DemoProvider()
    brief = _brief()
    output = _parse(provider.evaluate_candidates([{"angle": "problem-story", "hook": "H", "body": "B", "cta": "C", "claims": []}], brief, "1"))
    dimensions = output["candidate_scores"][0]["dimensions"]
    assert set(dimensions) == {
        "hook",
        "niche_relevance",
        "specificity_evidence",
        "clarity",
        "conversation_potential",
        "voice_fit",
    }
    for score in dimensions.values():
        assert 0 <= score["rating"] <= 5
        assert score["quote"]
        assert score["rubric_rule"]


@pytest.mark.parametrize("force_invalid", [False, True])
def test_provider_label_is_demo(force_invalid):
    provider = DemoProvider(force_invalid=force_invalid)
    assert provider.name == "DEMO_PROVIDER"
    assert provider.model is None
    assert provider.params == {}
