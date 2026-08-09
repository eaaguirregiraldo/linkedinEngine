import json
from pathlib import Path

import pytest

from domain.blockers import activate_blockers
from domain.score import base_score, penalizacion_genericidad, score_final
from domain.validation import load_cliche_catalog, parse_json_only


FIXTURES = Path(__file__).parents[1] / "fixtures"


@pytest.mark.parametrize(
    "name", ["regression_solid", "regression_generic", "regression_invented_claim", "regression_invalid_json"]
)
def test_regression_fixture_expectations(name):
    data = json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))
    expectation = data["expectation"]
    if name == "regression_invalid_json":
        with pytest.raises(ValueError):
            parse_json_only(data["raw_output"])
        assert expectation["terminal_state"] == "GENERATION_FAILED"
        return

    candidate = data["candidate"]
    evidence = data["evidence"]
    blockers = activate_blockers(candidate, evidence)
    generic = penalizacion_genericidad(
        " ".join((candidate["hook"], candidate["body"], candidate["cta"])),
        load_cliche_catalog().phrases,
        [],
    )
    final = score_final(base_score(data["ratings"]), 0, generic)
    if expectation.get("no_blockers"):
        assert not blockers
        assert expectation["score_min"] <= final <= expectation["score_max"]
    if expectation.get("genericity_min"):
        assert generic >= expectation["genericity_min"]
    if expectation.get("blocker_code"):
        assert expectation["blocker_code"] in {blocker.code for blocker in blockers}
