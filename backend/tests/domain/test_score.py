import pytest

from domain.score import (
    DIMENSION_WEIGHTS,
    base_score,
    dimension_100,
    penalizacion_genericidad,
    penalizacion_riesgo,
    score_final,
    validate_dimension_scores,
)
from domain.validation import load_cliche_catalog


def test_dimension_weights_sum_to_one():
    assert sum(DIMENSION_WEIGHTS.values()) == pytest.approx(1.0)


@pytest.mark.parametrize(("rating", "expected"), [(0, 0), (3, 60), (5, 100)])
def test_dimension_100(rating, expected):
    assert dimension_100(rating) == expected


@pytest.mark.parametrize("rating", [-1, 6, 3.5])
def test_dimension_100_rejects_invalid_rating(rating):
    with pytest.raises(ValueError):
        dimension_100(rating)


def test_base_score_uses_all_six_dimensions():
    ratings = {name: 5 for name in DIMENSION_WEIGHTS}
    assert base_score(ratings) == pytest.approx(100)


@pytest.mark.parametrize(
    ("base", "risk", "generic", "expected"),
    [(130, 0, 0, 100), (20, 25, 15, 0), (74.6, 10, 5, 60)],
)
def test_score_final_rounds_and_clamps(base, risk, generic, expected):
    assert score_final(base, risk, generic) == expected


def test_risk_penalty_caps_three_unsupported_numbers_at_25():
    claims = [
        {"text": "10% de ahorro", "support": "missing-1"},
        {"text": "20 equipos", "support": "missing-2"},
        {"text": "30 días", "support": "missing-3"},
    ]
    assert penalizacion_riesgo(claims, evidence=[]) == 25


def test_invented_personal_experience_costs_25():
    claims = [{"text": "Lideré una migración durante cinco años", "support": "needs_review"}]
    assert penalizacion_riesgo(claims, evidence=[]) == 25


def test_supported_claim_has_no_risk_penalty():
    claims = [{"text": "El inventario tiene 20 jobs", "support": "ev-1"}]
    evidence = [{"id": "ev-1", "text": "El inventario tiene 20 jobs"}]
    assert penalizacion_riesgo(claims, evidence) == 0


def test_genericity_caps_four_cliches_at_15():
    catalog = ["frase uno", "frase dos", "frase tres", "frase cuatro"]
    text = ". ".join(catalog)
    assert penalizacion_genericidad(text, catalog, []) == 15


def test_genericity_accepts_loaded_catalog_object():
    assert penalizacion_genericidad("El futuro ya llegó", load_cliche_catalog(), []) == 5


def test_dimension_score_requires_quote_and_rubric_rule():
    valid = {name: {"rating": 4, "quote": "frase", "rubric_rule": "regla-v1"} for name in DIMENSION_WEIGHTS}
    assert validate_dimension_scores(valid)
    invalid = {name: dict(value) for name, value in valid.items()}
    invalid["clarity"]["quote"] = ""
    assert not validate_dimension_scores(invalid)
