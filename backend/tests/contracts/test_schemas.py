# backend/tests/contracts/test_schemas.py
"""Tests del contrato canónico pydantic — Batch C, tarea C.1.

Cubre los criterios de C.1: cardinalidad de ``GenerationOutput`` (2 o 4
candidatos rechazados), unicidad de ángulos, ``rating`` fuera de 0..5,
dimensión sin quote/rubric_rule, ``ReceiptOut`` con ``remote_id`` no None,
tesis vacía, rationale obligatorio y formas básicas del resto del contrato.
"""

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import pytest  # noqa: E402  (sys.path bootstrap por encima)
from pydantic import ValidationError  # noqa: E402

from api.schemas import (  # noqa: E402
    Blocker,
    BriefIn,
    CandidateEdit,
    CandidateOut,
    CandidateOutput,
    CandidateScore,
    ClaimOut,
    DecisionOut,
    DimensionRatings,
    DimensionScore,
    ErrorBody,
    ErrorDetail,
    EvaluationOutput,
    EvidenceItem,
    GenerationOutput,
    HealthOut,
    Penalties,
    ProjectCreate,
    ReasonIn,
    ReceiptOut,
    VisualContract,
    VisualElement,
    VisualOut,
)


# ── Helpers ────────────────────────────────────────────────────────────────


def make_candidate(angle: str = "problem-story", **overrides) -> CandidateOutput:
    data = dict(
        angle=angle,
        hook="Hook del candidato",
        body="Body del candidato",
        cta="¿Qué opinás?",
        claims=[ClaimOut(text="Claim", support="ev-1")],
    )
    data.update(overrides)
    return CandidateOutput(**data)


def make_generation(*angles: str) -> GenerationOutput:
    return GenerationOutput(candidates=[make_candidate(a) for a in angles])


def _dimension() -> DimensionScore:
    return DimensionScore(rating=4, quote="Frase del candidato", rubric_rule="Rúbrica v1")


def make_candidate_score(candidate_id: int = 1, **overrides) -> CandidateScore:
    data = dict(
        candidate_id=candidate_id,
        dimensions=DimensionRatings(
            hook=_dimension(),
            niche_relevance=_dimension(),
            specificity_evidence=_dimension(),
            clarity=_dimension(),
            conversation_potential=_dimension(),
            voice_fit=_dimension(),
        ),
        penalties=Penalties(risk=0, generic=5),
        score_final=74,
        blockers=[],
    )
    data.update(overrides)
    return CandidateScore(**data)


def valid_brief() -> BriefIn:
    return BriefIn(
        thesis="Migrar COBOL no es traducir sintaxis",
        audience="Líderes de modernización",
        objective="Generar conversación",
        evidence=[
            EvidenceItem(id="ev-1", text="hecho aportado", type="known_facts"),
            EvidenceItem(id="ev-2", text="opinión del autor", type="author_opinions"),
        ],
        constraints=["No usar cifras de empresas"],
    )


# ── ErrorDetail: mapa abierto preservado en JSON Schema (ADR-003) ───────────


def test_error_detail_schema_allows_arbitrary_non_empty_details():
    details_schema = ErrorDetail.model_json_schema()["properties"]["details"]

    assert details_schema["additionalProperties"] is True

    error = ErrorBody.model_validate(
        {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "el request no cumple el contrato",
                "details": {
                    "fields": [{"loc": ["body", "thesis"], "msg": "Field required"}],
                    "code": "MISSING_FIELD",
                },
            }
        }
    )
    assert error.error.details["fields"]
    assert error.error.details["code"] == "MISSING_FIELD"


# ── GenerationOutput: cardinalidad y unicidad (GEN-01/02) ──────────────────


def test_generation_with_two_candidates_rejected():
    with pytest.raises(ValidationError):
        make_generation("problem-story", "practical-framework")


def test_generation_with_four_candidates_rejected():
    with pytest.raises(ValidationError):
        make_generation("problem-story", "practical-framework", "argued-position", "problem-story")


def test_generation_with_duplicate_angles_rejected():
    with pytest.raises(ValidationError):
        make_generation("problem-story", "practical-framework", "problem-story")


def test_generation_valid_with_three_unique_angles():
    gen = make_generation("problem-story", "practical-framework", "argued-position")
    assert len(gen.candidates) == 3
    assert {c.angle for c in gen.candidates} == {
        "problem-story",
        "practical-framework",
        "argued-position",
    }


def test_angle_outside_enum_rejected():
    with pytest.raises(ValidationError):
        make_candidate("clickbait")


def test_candidate_empty_hook_rejected():
    with pytest.raises(ValidationError):
        make_candidate(hook="")


def test_claim_without_support_rejected():
    with pytest.raises(ValidationError):
        ClaimOut(text="claim sin soporte")


# ── DimensionScore: rating 0..5 + quote + rubric_rule (EVAL-02/03) ──────────


def test_rating_out_of_range_rejected():
    with pytest.raises(ValidationError):
        DimensionScore(rating=7, quote="q", rubric_rule="r")


def test_rating_negative_rejected():
    with pytest.raises(ValidationError):
        DimensionScore(rating=-1, quote="q", rubric_rule="r")


def test_dimension_without_quote_rejected():
    with pytest.raises(ValidationError):
        DimensionScore(rating=4, quote="", rubric_rule="r")


def test_dimension_without_rubric_rule_rejected():
    with pytest.raises(ValidationError):
        DimensionScore(rating=4, quote="q", rubric_rule="")


def test_dimension_missing_field_rejected():
    with pytest.raises(ValidationError):
        DimensionScore(rating=4, quote="q")  # falta rubric_rule


# ── CandidateScore ──────────────────────────────────────────────────────────


def test_candidate_score_valid():
    score = make_candidate_score()
    assert score.score_final == 74
    assert score.dimensions.hook.rating == 4
    assert score.penalties.generic == 5
    assert score.blockers == []


def test_candidate_score_with_blocker():
    score = make_candidate_score(
        blockers=[Blocker(code="UNSUPPORTED_CLAIM", message="cifra sin evidencia", detail="10%")],
        score_final=88,
    )
    assert score.blockers[0].code == "UNSUPPORTED_CLAIM"
    assert score.score_final == 88


def test_candidate_score_score_final_out_of_range_rejected():
    with pytest.raises(ValidationError):
        make_candidate_score(score_final=150)


def test_evaluation_output_valid():
    out = EvaluationOutput(candidate_scores=[make_candidate_score(1), make_candidate_score(2), make_candidate_score(3)])
    assert len(out.candidate_scores) == 3


# ── ReceiptOut: recibo simulado sin ID remoto (SIM-01/02) ───────────────────


def test_receipt_out_remote_id_non_none_rejected():
    with pytest.raises(ValidationError):
        ReceiptOut(
            id=1,
            candidate_id=1,
            visual_id=1,
            created_at="2026-08-09T00:00:00Z",
            remote_id="li:post:abc123",
        )


def test_receipt_out_valid_with_remote_id_none():
    receipt = ReceiptOut(id=1, candidate_id=1, visual_id=1, created_at="2026-08-09T00:00:00Z")
    assert receipt.mode == "simulated"
    assert receipt.status == "SIMULATED_PUBLISHED"
    assert receipt.notice == "no se envió contenido a LinkedIn"
    assert receipt.remote_id is None


def test_receipt_out_status_cannot_be_real():
    with pytest.raises(ValidationError):
        ReceiptOut(id=1, candidate_id=1, visual_id=1, created_at="x", status="PUBLISHED_REAL")


def test_receipt_out_mode_cannot_be_real():
    with pytest.raises(ValidationError):
        ReceiptOut(id=1, candidate_id=1, visual_id=1, created_at="x", mode="real")


# ── BriefIn (CAP-02/03/05) ──────────────────────────────────────────────────


def test_brief_thesis_empty_rejected():
    with pytest.raises(ValidationError):
        BriefIn(thesis="   ", evidence=[EvidenceItem(id="ev-1", text="f", type="known_facts")])


def test_brief_valid():
    brief = valid_brief()
    assert brief.thesis == "Migrar COBOL no es traducir sintaxis"
    assert len(brief.evidence) == 2
    assert brief.evidence[1].type == "author_opinions"
    assert brief.constraints == ["No usar cifras de empresas"]


def test_evidence_type_outside_enum_rejected():
    with pytest.raises(ValidationError):
        EvidenceItem(id="ev-1", text="x", type="rumor")


# ── Visual (VIS-03/04) ──────────────────────────────────────────────────────


def test_visual_element_rationale_required():
    with pytest.raises(ValidationError):
        VisualElement(element_id="el-1", kind="shape", description="d", rationale="")


def test_visual_contract_valid():
    contract = VisualContract(
        thesis="tesis",
        concept="concepto",
        elements=[
            VisualElement(element_id="el-1", kind="shape", description="d", rationale="frase de la tesis")
        ],
        alt_text="alt text específico",
    )
    assert contract.status == "VISUAL_DRAFT"
    assert contract.elements[0].rationale


def test_visual_contract_alt_text_required():
    with pytest.raises(ValidationError):
        VisualContract(thesis="t", concept="c", elements=[], alt_text="")


def test_visual_out_requires_id_and_candidate():
    with pytest.raises(ValidationError):
        VisualOut(thesis="t", concept="c", elements=[], alt_text="a")  # falta id/candidate_id


# ── DecisionOut (EVAL-06) ───────────────────────────────────────────────────


def test_decision_out_valid():
    d = DecisionOut(outcome="RECOMMENDED", best_candidate_id=3, reason="mejor candidato")
    assert d.outcome == "RECOMMENDED"
    assert d.brief_needs_revision is False


def test_decision_out_outcome_literal_closed():
    with pytest.raises(ValidationError):
        DecisionOut(outcome="APPROVED", reason="x")


# ── Errores, reasons, edición, proyecto (API-04, APPR-01/02, CAP-01) ────────


def test_error_body_shape():
    body = ErrorBody(
        error=ErrorDetail(
            code="STATE_TRANSITION_REJECTED",
            message="Falta evaluación previa",
            details={"state": "GENERATED"},
        )
    )
    assert body.error.code == "STATE_TRANSITION_REJECTED"
    assert body.error.details["state"] == "GENERATED"


def test_reason_in_empty_rejected():
    with pytest.raises(ValidationError):
        ReasonIn(reason="")


def test_candidate_edit_requires_full_content():
    with pytest.raises(ValidationError):
        CandidateEdit(content={"hook": "h"})  # faltan body/cta


def test_project_create_blank_idea_rejected():
    with pytest.raises(ValidationError):
        ProjectCreate(raw_idea="   ")


def test_health_out_defaults():
    assert HealthOut().status == "ok"
    assert HealthOut(provider="DEMO_PROVIDER").provider == "DEMO_PROVIDER"


# ── CandidateOut (design §5.5) ──────────────────────────────────────────────


def test_candidate_out_defaults_and_serialization():
    cand = CandidateOut(id=7, angle="argued-position", hook="h", body="b", cta="c", claims=[])
    assert cand.content_version == 1
    assert cand.evaluation is None
    assert cand.decision is None
    data = cand.model_dump(mode="json")
    assert data["angle"] == "argued-position"
    assert data["content_version"] == 1
    assert data["evaluation"] is None
