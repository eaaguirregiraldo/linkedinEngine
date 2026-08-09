# backend/tests/contracts/test_contracts_identity.py
"""Tests de identidad de clases entre ``ai.contracts`` y ``api.schemas`` — Batch C, tarea C.2.

Criterio de C.2: ``ai/contracts.py`` reexporta los MISMOS modelos pydantic de
C.1 (sin redefinición); importar desde ambos módulos referencia el mismo
objeto (design §5.1, ADR-003, HARN-04).
"""

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import pytest  # noqa: E402  (sys.path bootstrap por encima)
from pydantic import ValidationError  # noqa: E402

import ai.contracts as contracts  # noqa: E402
import api.schemas as schemas  # noqa: E402


def test_generation_output_is_same_class():
    assert contracts.GenerationOutput is schemas.GenerationOutput


def test_evaluation_output_is_same_class():
    assert contracts.EvaluationOutput is schemas.EvaluationOutput


def test_candidate_output_is_same_class():
    assert contracts.CandidateOutput is schemas.CandidateOutput


def test_candidate_score_is_same_class():
    assert contracts.CandidateScore is schemas.CandidateScore


def test_dimension_score_is_same_class():
    assert contracts.DimensionScore is schemas.DimensionScore


def test_no_redefinition_of_llm_contracts():
    """La identidad de clase es la prueba de no redefinición: si alguien
    reescribe los modelos en ``ai/contracts.py``, estos asserts fallan."""
    for name in contracts.__all__:
        assert getattr(contracts, name) is getattr(schemas, name), f"{name} fue redefinido"


def test_validation_applies_through_contracts():
    """La misma validación (2 candidatos → rechazo) corre desde ``ai.contracts``."""
    with pytest.raises(ValidationError):
        contracts.GenerationOutput(
            candidates=[
                schemas.CandidateOutput(angle="problem-story", hook="h", body="b", cta="c", claims=[]),
                schemas.CandidateOutput(angle="practical-framework", hook="h2", body="b2", cta="c2", claims=[]),
            ]
        )


def test_rating_validation_applies_through_contracts():
    """Rating fuera de rango rechazado también desde ``ai.contracts`` (EVAL-02)."""
    with pytest.raises(ValidationError):
        contracts.CandidateScore(
            candidate_id=1,
            dimensions=schemas.DimensionRatings(
                hook=schemas.DimensionScore(rating=7, quote="q", rubric_rule="r"),
                niche_relevance=schemas.DimensionScore(rating=3, quote="q", rubric_rule="r"),
                specificity_evidence=schemas.DimensionScore(rating=3, quote="q", rubric_rule="r"),
                clarity=schemas.DimensionScore(rating=3, quote="q", rubric_rule="r"),
                conversation_potential=schemas.DimensionScore(rating=3, quote="q", rubric_rule="r"),
                voice_fit=schemas.DimensionScore(rating=3, quote="q", rubric_rule="r"),
            ),
            score_final=70,
        )
