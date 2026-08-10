"""OpenAI-compatible provider.

The adapter only transports prompts and returns raw JSON. Validation, repair,
guardrails and trace events remain exclusively in ``ai.harness``.
"""
from __future__ import annotations

import json
from typing import Any, Sequence

import httpx

from api.schemas import BriefIn
from core.config import Settings

from .providers import INVALID_OUTPUT, TRANSIENT, UNAVAILABLE, ProviderError


class OpenAICompatProvider:
    name = "OPENAI_PROVIDER"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self.model = settings.openai_model
        self.params = {"temperature": 0.4, "timeout": settings.openai_timeout}

    def generate_candidates(self, brief: BriefIn) -> str:
        payload = {
            "thesis": brief.thesis,
            "audience": brief.audience,
            "objective": brief.objective,
            "evidence": [item.model_dump() for item in brief.evidence],
            "constraints": brief.constraints,
        }
        return self._complete(
            "Generate exactly three LinkedIn candidates as JSON matching the canonical GenerationOutput schema. "
            "Use only the supplied brief evidence; unsupported claims must not be presented as facts.\n"
            + json.dumps(payload, ensure_ascii=False)
        )

    def evaluate_candidates(
        self, candidates: Sequence[Any], brief: BriefIn, catalog_version: str
    ) -> str:
        payload = {
            "brief": brief.model_dump(),
            "candidates": list(candidates),
            "catalog_version": catalog_version,
        }
        return self._complete(
            "Evaluate the anonymous candidates and return JSON matching the canonical EvaluationOutput schema. "
            "Return one score per candidate position, with six dimensions, quote, rubric_rule and blockers.\n"
            + json.dumps(payload, ensure_ascii=False, default=str)
        )

    def _complete(self, user_prompt: str) -> str:
        url = f"{self._settings.openai_base_url.rstrip('/')}/chat/completions"
        headers = {"Authorization": f"Bearer {self._settings.openai_api_key}"}
        body = {
            "model": self.model,
            "temperature": self.params["temperature"],
            "messages": [
                {
                    "role": "system",
                    "content": "You are a structured editorial service. Return JSON only, never markdown.",
                },
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
        }
        try:
            response = httpx.post(
                url,
                headers=headers,
                json=body,
                timeout=self._settings.openai_timeout,
            )
        except httpx.TimeoutException as exc:
            raise ProviderError(TRANSIENT, "OpenAI agotó el timeout configurado") from exc
        except httpx.RequestError as exc:
            raise ProviderError(TRANSIENT, "No se pudo conectar con OpenAI") from exc

        if response.status_code in {408, 409, 429} or response.status_code >= 500:
            raise ProviderError(TRANSIENT, f"OpenAI respondió temporalmente ({response.status_code})")
        if response.status_code in {401, 403}:
            raise ProviderError(UNAVAILABLE, "OpenAI rechazó la API key configurada en el backend")
        if response.status_code >= 400:
            raise ProviderError(UNAVAILABLE, f"OpenAI rechazó la solicitud ({response.status_code})")

        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise ProviderError(INVALID_OUTPUT, "OpenAI devolvió una respuesta sin contenido estructurado") from exc
        if not isinstance(content, str) or not content.strip():
            raise ProviderError(INVALID_OUTPUT, "OpenAI devolvió contenido vacío")
        return content


__all__ = ["OpenAICompatProvider"]
