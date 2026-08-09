from itertools import product

from domain.fsm import EVENTS, STATES, TRANSITIONS, FsmContext, apply


VALID_BRIEF = {"thesis": "Migrar COBOL exige recuperar conocimiento", "evidence": [{"id": "ev-1"}]}
VALID_CANDIDATES = [
    {
        "angle": "problem-story",
        "hook": "Problema real",
        "body": "Historia operativa",
        "cta": "¿Qué excepción encontraste?",
    },
    {
        "angle": "practical-framework",
        "hook": "Marco concreto",
        "body": "Pasos de migración",
        "cta": "¿Qué paso priorizarías?",
    },
    {
        "angle": "argued-position",
        "hook": "Tesis incómoda",
        "body": "Argumento de negocio",
        "cta": "¿Qué riesgo discutirías?",
    },
]


def context_for(event: str, target: str) -> FsmContext:
    data = {
        "brief": VALID_BRIEF,
        "candidates": VALID_CANDIDATES,
        "evaluation": {"outcome": "RECOMMENDED" if target == "RECOMMENDED" else "REVISION_REQUIRED"},
        "blockers": (),
        "visual": {
            "status": "VISUAL_READY",
            "alt_text": "Diagrama de conocimiento operativo",
            "elements": [{"rationale": "recuperar conocimiento"}],
        },
        "approved_candidate_id": 1,
        "candidate_id": 1,
        "reason": "Decisión editorial explícita",
        "candidate_changed": True,
        "remote_id": "urn:li:post:1",
    }
    return FsmContext(**data)


def test_transition_table_has_exactly_25_rows_and_known_symbols():
    assert len(TRANSITIONS) == 25
    assert all(t.source in STATES and t.event in EVENTS for t in TRANSITIONS)


def test_every_declared_transition_accepts_a_valid_context():
    for transition in TRANSITIONS:
        result = apply(
            transition.source,
            transition.event,
            context_for(transition.event, transition.target),
        )
        if transition.target in {"PUBLISHING_REAL", "PUBLISHED_REAL", "REAL_PUBLISH_FAILED"}:
            assert not result.ok
            assert result.state == transition.source
        else:
            assert result.ok, (transition, result.reason)


def test_all_undeclared_state_event_combinations_are_rejected_without_mutation():
    declared = {(t.source, t.event) for t in TRANSITIONS}
    for state, event in product(STATES, EVENTS):
        if (state, event) in declared:
            continue
        result = apply(state, event, context_for(event, "REVISION_REQUIRED"))
        assert not result.ok
        assert result.state == state


def test_candidate_edited_returns_to_generated_from_assigned_states():
    for state in ("GENERATED", "RECOMMENDED", "REVISION_REQUIRED", "VISUAL_DRAFT", "VISUAL_READY"):
        result = apply(state, "CANDIDATE_EDITED", context_for("CANDIDATE_EDITED", "GENERATED"))
        assert result.ok and result.state == "GENERATED"


def test_design_edit_candidate_alias_is_accepted():
    result = apply("RECOMMENDED", "edit_candidate", context_for("CANDIDATE_EDITED", "GENERATED"))
    assert result.ok and result.state == "GENERATED"


def test_invalid_brief_guard_is_actionable():
    result = apply("IDEA", "SUBMIT_BRIEF", FsmContext(brief={"thesis": "", "evidence": []}))
    assert not result.ok and result.state == "IDEA"
    assert "tesis" in result.reason.lower() and "evidencia" in result.reason.lower()


def test_approval_requires_reason_and_no_blockers():
    result = apply(
        "RECOMMENDED",
        "APPROVE",
        FsmContext(candidate_id=1, reason="", blockers=({"code": "UNSUPPORTED_CLAIM"},)),
    )
    assert not result.ok and result.state == "RECOMMENDED"
    assert "blocker" in result.reason.lower() or "raz" in result.reason.lower()


def test_real_publication_states_are_unreachable_in_p0():
    for state in STATES:
        for event in ("START_REAL_PUBLISH", "PUBLISH_SUCCEEDED", "PUBLISH_FAILED"):
            result = apply(state, event, context_for(event, "PUBLISHING_REAL"))
            assert not result.ok
            assert result.state == state


def test_unknown_state_and_event_are_rejected():
    assert not apply("UNKNOWN", "START_GENERATION", FsmContext()).ok
    assert not apply("IDEA", "UNKNOWN", FsmContext()).ok
