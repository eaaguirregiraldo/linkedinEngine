"""Tests del harness GenAI (E.5: retry/repair/traza, HARN-01/05/07/08).

Provider fakes: devuelven JSON crudo y fallan a pedido, nunca implementan
retry/repair (ADR-005: eso vive en el harness).
"""
import json

import pytest

from ai import harness
from ai.demo_provider import DemoProvider
from ai.harness import (
    DEFAULT_BACKOFF,
    EVALUATION_PROMPT_ID,
    GENERATION_PROMPT_ID,
    MAX_ATTEMPTS,
    ManifestError,
    repair_once,
    resolve_prompt,
    run_evaluation,
    run_generation,
)
from ai.providers import ProviderError, TRANSIENT, UNAVAILABLE
from api.schemas import BriefIn, EvidenceItem


def _brief() -> BriefIn:
    return BriefIn(
        thesis="Migrar COBOL no es traducir sintaxis: es traducir reglas de negocio",
        audience="equipos de mainframe",
        evidence=[
            EvidenceItem(
                id="ev-1",
                text="El inventario actual incluye jobs JCL y excepciones operativas",
                type="known_facts",
            )
        ],
    )


# Provider fakes ──────────────────────────────────────────────────────────────


class _DemoLike:
    """Genera con `DemoProvider` (válido) pero etiqueta distinta."""

    name = "FAKE"
    model = "fake-model"
    params = {"temperature": 0.4}

    def generate_candidates(self, brief):
        return DemoProvider().generate_candidates(brief)

    def evaluate_candidates(self, candidates, brief, catalog_version):
        return DemoProvider().evaluate_candidates(candidates, brief, catalog_version)


class _Flaky:
    """Falla `failures` veces con `code` y después genera válido."""

    name = "FLAKY"
    model = None
    params = {}

    def __init__(self, failures=2, code=TRANSIENT, failures_eval=0):
        self.failures = failures
        self.code = code
        self.failures_eval = failures_eval
        self.calls = 0
        self.eval_calls = 0

    def generate_candidates(self, brief):
        self.calls += 1
        if self.calls <= self.failures:
            raise ProviderError(self.code, "provider temporalmente no disponible")
        return DemoProvider().generate_candidates(brief)

    def evaluate_candidates(self, candidates, brief, catalog_version):
        self.eval_calls += 1
        if self.eval_calls <= self.failures_eval:
            raise ProviderError(self.code, "evaluador temporalmente no disponible")
        return DemoProvider().evaluate_candidates(candidates, brief, catalog_version)


class _Broken:
    """Siempre devuelve la misma salida inválida (reparable o no)."""

    name = "BROKEN"
    model = None
    params = {}

    def __init__(self, raw):
        self.raw = raw

    def generate_candidates(self, brief):
        return self.raw

    def evaluate_candidates(self, candidates, brief, catalog_version):
        return self.raw


def _trailing_comma_invalid(brief) -> str:
    """Salida con coma final: reparable por `repair_once` (HARN-05)."""
    raw = DemoProvider().generate_candidates(brief)
    assert raw.endswith("}")
    # "…]}" → "…],}" : coma final ilegal en el objeto raíz.
    return raw[:-1] + ",}"


# ── Manifiesto (E.2, HARN-01) ───────────────────────────────────────────────


def test_resolve_prompt_returns_prompt_and_stable_hash():
    resolved = resolve_prompt(GENERATION_PROMPT_ID)
    assert resolved.prompt_id == GENERATION_PROMPT_ID
    assert resolved.version == "1.0.0"
    assert resolved.schema_version == "1.0.0"
    assert resolved.path.is_file()
    assert resolved.text.strip()
    assert resolved.sha256.startswith("sha256:")
    # Hash estable entre resoluciones del mismo prompt.
    assert resolve_prompt(GENERATION_PROMPT_ID).sha256 == resolved.sha256
    # El manifiesto referencia el contrato {file, version, schema_version, sha256}.
    manifest = json.loads(
        (harness.PROMPTS_DIR / harness.MANIFEST_FILE).read_text(encoding="utf-8")
    )
    entry = manifest["prompts"]["linkedin-candidate-generator"]
    assert entry["file"] == "linkedin-candidate-generator@1.0.0.md"
    assert set(entry) == {"file", "version", "schema_version", "sha256"}


def test_resolve_evaluation_prompt():
    resolved = resolve_prompt(EVALUATION_PROMPT_ID)
    assert resolved.prompt_id == EVALUATION_PROMPT_ID
    assert resolved.version == "1.0.0"
    assert resolved.sha256.startswith("sha256:")


def test_resolve_prompt_rejects_edited_file_without_version_bump(tmp_path):
    """HARN-01: editar un prompt SIN subir versión rompe la resolución."""
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    file_name = "linkedin-candidate-generator@1.0.0.md"
    (prompts / file_name).write_text("# Rol\ncontenido ORIGINAL\n", encoding="utf-8")
    manifest = {
        "prompts": {
            "linkedin-candidate-generator": {
                "file": file_name,
                "version": "1.0.0",
                "schema_version": "1.0.0",
                # hash calculado sobre el contenido ORIGINAL
                "sha256": "sha256:"
                + __import__("hashlib").sha256(
                    "# Rol\ncontenido ORIGINAL\n".encode("utf-8")
                ).hexdigest(),
            }
        }
    }
    (prompts / harness.MANIFEST_FILE).write_text(json.dumps(manifest), encoding="utf-8")
    resolve_prompt(GENERATION_PROMPT_ID, prompts_dir=prompts)  # OK con hash correcto
    # Se edita el archivo sin tocar el manifiesto → mismatch.
    (prompts / file_name).write_text("# Rol\ncontenido MODIFICADO\n", encoding="utf-8")
    with pytest.raises(ManifestError, match="subir la version"):
        resolve_prompt(GENERATION_PROMPT_ID, prompts_dir=prompts)


@pytest.mark.parametrize(
    "prompt_id",
    [
        "capacidad-desconocida@1.0.0",  # capacidad no existe
        "linkedin-candidate-generator@9.9.9",  # versión no existe
        "sin-version",  # sin @capacidad@versión
    ],
)
def test_resolve_prompt_rejects_unknown_capacity_or_version(prompt_id):
    with pytest.raises(ManifestError):
        resolve_prompt(prompt_id)


# ── repair_once (HARN-05) ────────────────────────────────────────────────────


def test_repair_once_fixes_trailing_commas_only():
    raw = '{"candidates": [{"angle": "problem-story"},]}'
    fixed = repair_once(raw, "unused")
    assert fixed == '{"candidates": [{"angle": "problem-story"}]}'


def test_repair_once_returns_none_when_nothing_to_repair():
    assert repair_once('{"ok": true}', "unused") is None
    # JSON con otro defecto sintáctico (llave sin cerrar) NO es reparable.
    assert repair_once('{"candidates": [', "unused") is None


def test_repair_once_never_rewrites_content():
    """Cardinalidad o campos faltantes NO son reparable (sintaxis únicamente)."""
    raw = '{"candidates": [{"angle": "problem-story"}]}'  # 1 candidato, JSON válido
    assert repair_once(raw, "schema inválido") is None


# ── run_generation: éxito, repair, retry, fallo ─────────────────────────────


def test_generation_success_trace_has_prompt_and_validation_events():
    result = run_generation(_brief(), _DemoLike())
    assert result.ok
    assert result.candidates is not None
    assert len(result.candidates) == 3
    event_types = [event["type"] for event in result.trace_events]
    assert event_types[0] == "prompt_resolved"
    assert "provider_invoked" in event_types
    assert "output_validated" in event_types
    resolved = resolve_prompt(GENERATION_PROMPT_ID)
    assert result.prompt_version == resolved.version
    assert result.schema_version == resolved.schema_version
    assert result.prompt_hash == resolved.sha256
    assert result.provider == "FAKE"
    # raw_output off por defecto (HARN-07).
    assert result.raw_output is None


def test_generation_repairs_trailing_comma_once():
    brief = _brief()
    result = run_generation(brief, _Broken(_trailing_comma_invalid(brief)))
    assert result.ok
    assert len(result.candidates) == 3
    types = [event["type"] for event in result.trace_events]
    assert "repair_ok" in types
    assert "output_validated" in types
    # repair_ok y repair_failed NUNCA conviven en el mismo intento.
    for event in result.trace_events:
        if event["type"] == "repair_failed":
            assert event["attempt"] != 1 or "repair_ok" not in types


def test_generation_force_invalid_fails_after_repair():
    result = run_generation(_brief(), DemoProvider(force_invalid=True))
    assert not result.ok
    assert result.error_code == "INVALID_OUTPUT"
    assert result.candidates is None
    types = [event["type"] for event in result.trace_events]
    assert "validation_failed" in types
    assert "repair_ok" in types  # la coma final se reparó en el intento 1
    assert "generation_failed" in types


def test_generation_two_candidates_is_terminal_invalid_output():
    brief = _brief()
    raw = '{"candidates": [{"angle": "problem-story", "hook": "h", "body": "b", "cta": "c"}, {"angle": "argued-position", "hook": "h2", "body": "b2", "cta": "c2"}]}'
    result = run_generation(brief, _Broken(raw))
    assert not result.ok
    assert result.error_code == "INVALID_OUTPUT"
    # Cardinalidad no reparable: 3 intentos, ninguno reparó.
    types = [event["type"] for event in result.trace_events]
    assert types.count("validation_failed") == MAX_ATTEMPTS
    assert "repair_ok" not in types


def test_generation_retries_transient_with_backoff(monkeypatch):
    sleeps = []
    monkeypatch.setattr(harness.time, "sleep", sleeps.append)
    provider = _Flaky(failures=2, code=TRANSIENT)
    result = run_generation(_brief(), provider)
    assert result.ok
    assert provider.calls == 3  # 2 fallos + 1 éxito
    types = [event["type"] for event in result.trace_events]
    assert types.count("retry_scheduled") == 2
    assert sleeps == [0.5, 1.5]  # DEFAULT_BACKOFF


def test_generation_exhausts_transient_attempts(monkeypatch):
    monkeypatch.setattr(harness.time, "sleep", lambda _: None)
    provider = _Flaky(failures=10, code=TRANSIENT)
    result = run_generation(_brief(), provider)
    assert not result.ok
    assert result.error_code == "PROVIDER_TRANSIENT_ERROR"
    assert provider.calls == MAX_ATTEMPTS
    assert result.candidates is None


def test_generation_failure_keeps_brief_intact(monkeypatch):
    """RNF-03: un fallo nunca destruye el brief ni se representa como éxito."""
    monkeypatch.setattr(harness.time, "sleep", lambda _: None)
    brief = _brief()
    result = run_generation(brief, _Flaky(failures=10, code=TRANSIENT))
    assert not result.ok
    # El brief (objeto inmutable pydantic) sigue igual tras el fallo.
    assert brief.thesis == "Migrar COBOL no es traducir sintaxis: es traducir reglas de negocio"


# ── run_evaluation: anonimización, orden, remapeo, degrade (EVAL-07, HARN-08) ─


class _RecordingEval:
    """Captura lo que recibe el evaluador para inspeccionar anonimización/orden."""

    name = "DEMO_PROVIDER"  # el seed fijo (EVAL-07) aplica al proveedor demo
    model = None
    params = {}

    def __init__(self):
        self.received = None

    def generate_candidates(self, brief):
        return DemoProvider().generate_candidates(brief)

    def evaluate_candidates(self, candidates, brief, catalog_version):
        self.received = list(candidates)
        return DemoProvider().evaluate_candidates(candidates, brief, catalog_version)


def test_evaluation_anonymizes_candidates():
    provider = _RecordingEval()
    result = run_generation(_brief(), provider)
    scores_result = run_evaluation(result.candidates, _brief(), provider)
    assert scores_result.ok
    assert scores_result.semantic_available
    for candidate in provider.received:
        assert set(candidate) == {"angle", "hook", "body", "cta", "claims"}
        for claim in candidate["claims"]:
            assert set(claim) == {"text", "support"}


def test_evaluation_orders_candidates_deterministically_with_demo_seed():
    provider = _RecordingEval()
    brief = _brief()
    result = run_generation(brief, provider)
    first = run_evaluation(result.candidates, brief, _RecordingEval())
    second = run_evaluation(result.candidates, brief, _RecordingEval())
    order_first = next(
        event["order"] for event in first.trace_events if event["type"] == "evaluation_anonymized"
    )
    order_second = next(
        event["order"] for event in second.trace_events if event["type"] == "evaluation_anonymized"
    )
    assert order_first == order_second  # seed fija DEMO_SEED en demo
    assert sorted(order_first) == [0, 1, 2]


def test_evaluation_remaps_candidate_ids_back_to_original_positions():
    provider = _RecordingEval()
    brief = _brief()
    result = run_generation(brief, provider)
    scores_result = run_evaluation(result.candidates, brief, provider)
    order = next(
        event["order"] for event in scores_result.trace_events if event["type"] == "evaluation_anonymized"
    )
    original_ids = {candidate_id for candidate_id in range(len(result.candidates))}
    assert {score.candidate_id for score in scores_result.candidate_scores} == original_ids
    # El orden recibido por el provider es una permutación de los índices originales.
    assert set(order) == original_ids


def test_evaluation_degrades_when_semantic_evaluator_unavailable(monkeypatch):
    monkeypatch.setattr(harness.time, "sleep", lambda _: None)
    # failures=0 → generación OK en el 1er intento; evaluador cae SIEMPRE.
    provider = _Flaky(failures=0, failures_eval=10, code=UNAVAILABLE)
    result = run_generation(_brief(), provider)
    scores_result = run_evaluation(result.candidates, _brief(), provider)
    assert not scores_result.ok
    assert scores_result.semantic_available is False
    assert scores_result.error_code == "SEMANTIC_EVALUATION_UNAVAILABLE"
    assert scores_result.candidate_scores is None
    # Sin score fabricado (HARN-08).
    assert "evaluation_scored" not in [e["type"] for e in scores_result.trace_events]


def test_evaluation_retries_transient_then_succeeds(monkeypatch):
    monkeypatch.setattr(harness.time, "sleep", lambda _: None)
    provider = _Flaky(failures_eval=1, code=TRANSIENT)
    result = run_generation(_brief(), provider)
    scores_result = run_evaluation(result.candidates, _brief(), provider)
    assert scores_result.ok
    assert scores_result.semantic_available
    assert provider.eval_calls == 2  # 1 fallo + 1 éxito
    types = [e["type"] for e in scores_result.trace_events]
    assert types.count("retry_scheduled") == 1


# ── Traza: redacción y raw_output (HARN-07) ─────────────────────────────────


def test_trace_never_contains_secrets(monkeypatch, tmp_path):
    """Un provider que devuelve secretos en la salida no los filtra a la traza."""
    monkeypatch.setattr(harness.time, "sleep", lambda _: None)

    class _Leaky(_DemoLike):
        name = "LEAKY"

        def generate_candidates(self, brief):
            payload = json.loads(super().generate_candidates(brief))
            payload["api_key"] = "sk-super-secret-123"
            payload["authorization"] = "Bearer tok-456"
            return json.dumps(payload)

    result = run_generation(_brief(), _Leaky())
    assert result.ok  # la salida validada ignora los campos extra
    serialized = json.dumps(result.trace_events)
    assert "sk-super-secret-123" not in serialized
    assert "tok-456" not in serialized
    assert "api_key" not in serialized


def test_raw_output_redacted_when_trace_store_raw_output_enabled(monkeypatch, tmp_path):
    """HARN-07: raw_output con TRACE_STORE_RAW_OUTPUT=true, ya redactado."""
    monkeypatch.setattr(harness.time, "sleep", lambda _: None)
    from core.config import Settings

    class _Leaky(_DemoLike):
        name = "LEAKY2"

        def generate_candidates(self, brief):
            payload = json.loads(super().generate_candidates(brief))
            payload["api_key"] = "sk-super-secret-123"
            return json.dumps(payload)

    settings = Settings(trace_store_raw_output=True)
    result = run_generation(_brief(), _Leaky(), settings=settings)
    assert result.ok
    assert result.raw_output is not None
    assert "sk-super-secret-123" not in result.raw_output
    assert "[REDACTED]" in result.raw_output
    # Sigue siendo JSON válido.
    parsed = json.loads(result.raw_output)
    assert len(parsed["candidates"]) == 3


def test_default_backoff_matches_design():
    assert DEFAULT_BACKOFF == (0.5, 1.5)
