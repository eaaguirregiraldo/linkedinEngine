from domain.blockers import (
    MIN_TOP_GAP,
    THRESHOLD_RECOMMEND,
    THRESHOLD_REVISION_LOW,
    activate_blockers,
    decide,
)


def scores(*values):
    return [{"candidate_id": index, "score_final": value} for index, value in enumerate(values, 1)]


def test_thresholds_are_the_versioned_initial_values():
    assert (THRESHOLD_RECOMMEND, MIN_TOP_GAP, THRESHOLD_REVISION_LOW) == (72, 4, 60)


def test_high_score_with_blocker_is_not_recommended():
    decision = decide(scores(88, 71, 64), {1: [{"code": "UNSUPPORTED_CLAIM"}]}, 17)
    assert decision.outcome == "REVISION_REQUIRED"
    assert decision.best_candidate_id == 1


def test_78_71_64_is_recommended():
    decision = decide(scores(78, 71, 64), {}, 7)
    assert decision.outcome == "RECOMMENDED"
    assert decision.best_candidate_id == 1


def test_gap_below_four_requires_revision():
    decision = decide(scores(74, 72), {}, 2)
    assert decision.outcome == "REVISION_REQUIRED"
    assert "dos mejoras" in decision.reason.lower()


def test_revision_band_requires_two_improvements():
    decision = decide(scores(68, 62, 55), {}, 6)
    assert decision.outcome == "REVISION_REQUIRED"
    assert "dos mejoras" in decision.reason.lower()
    assert not decision.brief_needs_revision


def test_all_below_60_requires_brief_revision():
    decision = decide(scores(58, 54, 50), {}, 4)
    assert decision.outcome == "REVISION_REQUIRED"
    assert decision.brief_needs_revision
    assert "brief" in decision.reason.lower()


def test_decision_is_reproducible():
    args = (scores(78, 71, 64), {}, 7)
    assert decide(*args) == decide(*args)


def test_blocker_activation_covers_all_assigned_categories():
    candidate = {
        "body": "Lideré una migración con 30% de ahorro. Te garantizo el resultado.",
        "claims": [{"text": "30% de ahorro", "support": "needs_review"}],
    }
    codes = {blocker.code for blocker in activate_blockers(candidate, evidence=[])}
    assert "UNSUPPORTED_CLAIM" in codes
    assert "INVENTED_EXPERIENCE" in codes
    assert "PROHIBITED_CONTENT" in codes
    assert "NEEDS_REVIEW" in codes


def test_number_in_body_without_claim_or_evidence_is_blocked():
    candidate = {"body": "La migración reduce 37% los incidentes.", "claims": []}
    codes = {blocker.code for blocker in activate_blockers(candidate, evidence=[])}
    assert "UNSUPPORTED_ASSERTION" in codes
