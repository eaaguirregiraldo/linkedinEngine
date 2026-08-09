"""Trazabilidad (design §6.6/§13, fsm-trace TRC-02, invariante 4).

`build_trace_event` crea eventos tipados con marca de tiempo (ts UTC ISO-8601).
`redact_secrets` redacta recursivamente cualquier valor bajo claves sensibles
(api_key, authorization, tokens, etc.) antes de persistir o responder,
garantizando que la traza nunca exponga secretos (RNF-04).
"""
from __future__ import annotations

import datetime as _datetime
import re
from typing import Any

# Patrón de claves sensibles. Se evita "auth" a secas para no redactar
# campos legítimos del dominio (p. ej. "author_opinions" de la evidencia).
_SECRET_KEY_RE = re.compile(
    r"(api[_-]?key|authorization|x-api-key|token|secret|passwd|password|credential|private[_-]?key)",
    re.IGNORECASE,
)

REDACTED = "[REDACTED]"


def _utc_now_iso() -> str:
    return _datetime.datetime.now(_datetime.timezone.utc).isoformat()


def build_trace_event(event_type: str, **data: Any) -> dict[str, Any]:
    """Construye un evento de traza tipado: `{ts, type, **data}`."""
    return {"ts": _utc_now_iso(), "type": event_type, **data}


def _is_secret_key(key: Any) -> bool:
    return isinstance(key, str) and _SECRET_KEY_RE.search(key) is not None


def redact_secrets(obj: Any) -> Any:
    """Redacta recursivamente valores bajo claves sensibles (TRC-02)."""
    if isinstance(obj, dict):
        return {
            key: (REDACTED if _is_secret_key(key) else redact_secrets(value))
            for key, value in obj.items()
        }
    if isinstance(obj, list):
        return [redact_secrets(item) for item in obj]
    if isinstance(obj, tuple):
        return tuple(redact_secrets(item) for item in obj)
    return obj
