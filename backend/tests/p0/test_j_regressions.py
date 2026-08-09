"""Regresiones consolidadas del cierre P0 (Wave 6, lote J)."""
from __future__ import annotations

import json
from itertools import product
from pathlib import Path

import pytest

from api import errors
from api.schemas import ErrorBody, ErrorDetail
from domain.fsm import EVENTS, STATES, FsmContext, TRANSITIONS, apply
from domain.blockers import activate_blockers
from domain.score import base_score, penalizacion_genericidad, score_final
from domain.validation import load_cliche_catalog, parse_json_only


FIXTURES = Path(__file__).parents[1] / "fixtures"


@pytest.mark.parametrize("name", ["solid", "generic", "invented_claim", "invalid_json"])
def test_four_versioned_fixtures_preserve_p0_expectations(name: str) -> None:
    data = json.loads((FIXTURES / f"regression_{name}.json").read_text())
    expectation = data["expectation"]
    if name == "invalid_json":
        with pytest.raises(ValueError):
            parse_json_only(data["raw_output"])
        assert expectation["terminal_state"] == "GENERATION_FAILED"
        return
    candidate = data["candidate"]
    blockers = activate_blockers(candidate, data["evidence"])
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


def test_fsm_rejects_illegal_events_without_state_mutation() -> None:
    declared = {(transition.source, transition.event) for transition in TRANSITIONS}
    for state, event in product(STATES, EVENTS):
        if (state, event) in declared:
            continue
        result = apply(state, event, FsmContext())
        assert not result.ok
        assert result.state == state


def test_real_publish_is_unreachable_and_approval_errors_are_actionable() -> None:
    for state in STATES:
        result = apply(state, "START_REAL_PUBLISH", FsmContext())
        assert not result.ok and result.state == state
    rejected = errors.StateTransitionRejected("se requiere una razón humana")
    body = ErrorBody(
        error=ErrorDetail(
            code=rejected.code,
            message=rejected.message,
            details=rejected.details,
        )
    )
    assert body.error.code == "STATE_TRANSITION_REJECTED"
    assert "razón" in body.error.message
