"""Tests de trazabilidad (HARN-07, TRC-01/02, design §6.6/§13.2).

`build_trace_event` tipa eventos con ts UTC ISO-8601; `redact_secrets`
redacta recursivamente valores bajo claves sensibles sin tocar el resto.
"""
import datetime as dt

import pytest

from core.trace import REDACTED, build_trace_event, redact_secrets


# ── build_trace_event (TRC-01) ──────────────────────────────────────────────


def test_build_trace_event_has_ts_and_type():
    event = build_trace_event("prompt_resolved", prompt_hash="sha256:abc", version="1.0.0")
    assert set(event) >= {"ts", "type", "prompt_hash", "version"}
    assert event["type"] == "prompt_resolved"
    assert event["prompt_hash"] == "sha256:abc"
    assert event["version"] == "1.0.0"


def test_build_trace_event_ts_is_utc_iso8601():
    event = build_trace_event("provider_invoked")
    parsed = dt.datetime.fromisoformat(event["ts"])
    # fromisoformat conserva el offset; debe estar en UTC (sufijo +00:00 o Z).
    assert event["ts"].endswith("+00:00") or event["ts"].endswith("Z")
    assert parsed.tzinfo is not None


def test_build_trace_event_preserves_event_order():
    first = build_trace_event("prompt_resolved")
    second = build_trace_event("provider_invoked")
    assert first["type"] == "prompt_resolved"
    assert second["type"] == "provider_invoked"


# ── redact_secrets (TRC-02, RNF-04) ─────────────────────────────────────────


@pytest.mark.parametrize(
    "key",
    [
        "api_key",
        "apikey",
        "api-key",
        "API_KEY",
        "Authorization",
        "x-api-key",
        "token",
        "access_token",
        "secret",
        "password",
        "passwd",
        "credential",
        "private_key",
    ],
)
def test_redact_secrets_redacts_sensitive_keys(key):
    assert redact_secrets({key: "valor-secreto"}) == {key: REDACTED}


def test_redact_secrets_does_not_touch_legit_domain_keys():
    data = {
        "author_opinions": "no se redacta",
        "support": "author_opinion",
        "blocker": "UNSUPPORTED_CLAIM",
        "candidate_id": 1,
        "score_final": 90,
    }
    assert redact_secrets(data) == data


def test_redact_secrets_recurses_into_lists_and_dicts():
    data = {
        "candidates": [
            {"angle": "problem-story", "claims": [{"text": "ok"}]},
            {"angle": "argued-position", "api_key": "sk-secret"},
        ]
    }
    redacted = redact_secrets(data)
    assert redacted["candidates"][0] == {"angle": "problem-story", "claims": [{"text": "ok"}]}
    assert redacted["candidates"][1]["api_key"] == REDACTED


def test_redact_secrets_recurses_into_tuples():
    data = {"events": ({"authorization": "Bearer tok"}, {"type": "ok"})}
    redacted = redact_secrets(data)
    assert redacted["events"][0]["authorization"] == REDACTED
    assert redacted["events"][1] == {"type": "ok"}


def test_redact_secrets_leaves_plain_values_untouched():
    assert redact_secrets("no soy secreto") == "no soy secreto"
    assert redact_secrets(42) == 42
    assert redact_secrets(None) is None
    assert redact_secrets(["a", {"b": 1}]) == ["a", {"b": 1}]


def test_redact_secrets_is_idempotent():
    data = {"api_key": "sk-secret", "nested": {"token": "t-1", "ok": True}}
    once = redact_secrets(data)
    assert redact_secrets(once) == once


def test_redact_secrets_on_trace_events():
    events = [
        build_trace_event("provider_invoked", provider="DEMO_PROVIDER"),
        build_trace_event("provider_error", message="boom"),
        build_trace_event("output_validated", checks=[{"name": "schema", "ok": True}]),
    ]
    redacted = redact_secrets(events)
    # La estructura y el orden de la traza se conservan; el contenido no
    # sensible queda intacto (TRC-01: traza append-only, no destructiva).
    assert [event["type"] for event in redacted] == [
        "provider_invoked",
        "provider_error",
        "output_validated",
    ]
    assert redacted[0]["provider"] == "DEMO_PROVIDER"
    assert redacted[1]["message"] == "boom"
    assert redacted[2]["checks"] == [{"name": "schema", "ok": True}]
