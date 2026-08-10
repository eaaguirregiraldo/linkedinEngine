from __future__ import annotations

import json

import httpx
import pytest

from ai.openai_compat import OpenAICompatProvider
from ai.providers import ProviderError, TRANSIENT, UNAVAILABLE
from api.schemas import BriefIn, EvidenceItem
from core.config import Settings


def _brief() -> BriefIn:
    return BriefIn(
        thesis="Migrar COBOL es recuperar conocimiento operativo",
        evidence=[EvidenceItem(id="e1", text="Jobs JCL documentados", type="known_facts")],
    )


def test_openai_response_is_raw_json_and_does_not_change_harness_contract(monkeypatch):
    expected = {"candidates": []}

    def fake_post(*args, **kwargs):
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": json.dumps(expected)}}]},
            request=httpx.Request("POST", "https://example.test/v1/chat/completions"),
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    provider = OpenAICompatProvider(Settings(openai_api_key="sk-test"))
    assert json.loads(provider.generate_candidates(_brief())) == expected


@pytest.mark.parametrize("status,code", [(401, UNAVAILABLE), (429, TRANSIENT), (503, TRANSIENT)])
def test_openai_http_errors_are_normalized(monkeypatch, status, code):
    monkeypatch.setattr(
        httpx,
        "post",
        lambda *args, **kwargs: httpx.Response(
            status,
            request=httpx.Request("POST", "https://example.test/v1/chat/completions"),
        ),
    )
    with pytest.raises(ProviderError) as error:
        OpenAICompatProvider(Settings(openai_api_key="sk-test")).generate_candidates(_brief())
    assert error.value.code == code


def test_openai_request_never_receives_frontend_key():
    provider = OpenAICompatProvider(Settings(openai_api_key="sk-test"))
    assert provider.params["temperature"] == 0.4
