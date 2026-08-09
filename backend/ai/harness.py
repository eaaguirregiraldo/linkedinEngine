"""GenAI harness: retry/repair/traza (design §6.5/§6.6, HARN-01/05/07/08).

El retry/repair VIVE acá, no en el provider (ADR-005). El harness resuelve el
prompt versionado y su hash (HARN-01), valida la salida contra el schema
canónico pydantic (HARN-04), repara UNA sola vez el JSON inválido (HARN-05) y
registra la traza por ejecución con `redact_secrets` siempre aplicado (HARN-07).
Si el evaluador semántico falla tras las políticas, degrada a solo-determinístico
(`semantic_available=False`) sin fabricar un score completo (HARN-08).
"""
from __future__ import annotations

import hashlib
import json
import random
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

from pydantic import ValidationError

from api.schemas import (
    BriefIn,
    CandidateOutput,
    CandidateScore,
    EvaluationOutput,
    GenerationOutput,
)

from core.config import Settings, get_settings
from core.trace import build_trace_event, redact_secrets
from domain.validation import CLICHE_CATALOG_VERSION, parse_json_only

from .providers import (
    INVALID_OUTPUT,
    TRANSIENT,
    GenAIProvider,
    ProviderError,
)

GENERATION_PROMPT_ID = "linkedin-candidate-generator@1.0.0"
EVALUATION_PROMPT_ID = "editorial-evaluator@1.0.0"

# Degradación del evaluador semántico (HARN-08, design §12 → 503
# SEMANTIC_EVALUATION_UNAVAILABLE / estado EVALUATION_PARTIAL).
SEMANTIC_EVALUATION_UNAVAILABLE = "SEMANTIC_EVALUATION_UNAVAILABLE"

PROMPTS_DIR = Path(__file__).with_name("prompts")
MANIFEST_FILE = "manifest.json"

MAX_ATTEMPTS = 3
DEFAULT_BACKOFF: tuple[float, ...] = (0.5, 1.5)
DEMO_SEED = 0

_TRAILING_COMMA_RE = re.compile(r",\s*([}\]])")


# ── Manifiesto de prompts (HARN-01, design §6.1) ────────────────────────────


class ManifestError(RuntimeError):
    """El manifiesto no resuelve el prompt o el hash no coincide (HARN-01)."""


@dataclass(frozen=True)
class ResolvedPrompt:
    """Prompt resuelto: ruta, texto, versión, schema_version y hash real."""

    prompt_id: str
    path: Path
    text: str
    version: str
    schema_version: str
    sha256: str


def resolve_prompt(prompt_id: str, prompts_dir: Path | None = None) -> ResolvedPrompt:
    """Resuelve un prompt por id (`capacidad@versión`), calculando su hash real.

    El manifiesto declara `{file, version, schema_version, sha256}` por
    capacidad. Si el hash calculado del archivo NO coincide con el declarado, el
    prompt fue editado sin subir versión (HARN-01): se lanza `ManifestError`.
    """
    directory = prompts_dir or PROMPTS_DIR
    manifest_path = directory / MANIFEST_FILE
    if not manifest_path.is_file():
        raise ManifestError(f"manifiesto no encontrado: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    prompts = manifest.get("prompts", {})
    if "@" not in prompt_id:
        raise ManifestError(f"prompt_id debe ser 'capacidad@version': {prompt_id}")
    capacity, version = prompt_id.rsplit("@", 1)
    entry = prompts.get(capacity)
    if entry is None:
        raise ManifestError(f"capacidad desconocida en manifiesto: {capacity}")
    expected_file = f"{capacity}@{version}.md"
    if entry.get("file") != expected_file:
        raise ManifestError(
            f"version {version} no existe para {capacity}: "
            f"esperaba {expected_file}, manifiesto tiene {entry.get('file')}"
        )
    path = directory / expected_file
    if not path.is_file():
        raise ManifestError(f"archivo de prompt no encontrado: {path}")
    text = path.read_text(encoding="utf-8")
    computed = f"sha256:{hashlib.sha256(text.encode('utf-8')).hexdigest()}"
    declared = entry.get("sha256")
    if declared != computed:
        raise ManifestError(
            f"hash de {prompt_id} no coincide con el manifiesto: "
            f"edita el prompt exige subir la version (HARN-01) "
            f"[declarado {declared}, calculado {computed}]"
        )
    return ResolvedPrompt(
        prompt_id=prompt_id,
        path=path,
        text=text,
        version=entry.get("version", version),
        schema_version=entry.get("schema_version", "1.0.0"),
        sha256=computed,
    )


# ── Resultados ──────────────────────────────────────────────────────────────


@dataclass
class RunResult:
    """Resultado de una ejecución de generación (design §6.5)."""

    ok: bool
    candidates: tuple[CandidateOutput, ...] | None = None
    trace_events: list[dict[str, Any]] = field(default_factory=list)
    error_code: str | None = None
    provider: str = ""
    model: str | None = None
    params: dict[str, Any] = field(default_factory=dict)
    prompt_version: str = ""
    schema_version: str = ""
    prompt_hash: str = ""
    raw_output: str | None = None


@dataclass
class EvaluationRunResult:
    """Resultado de una ejecución de evaluación (EVAL-07, HARN-08)."""

    ok: bool
    semantic_available: bool
    candidate_scores: tuple[CandidateScore, ...] | None = None
    trace_events: list[dict[str, Any]] = field(default_factory=list)
    error_code: str | None = None
    provider: str = ""
    model: str | None = None
    params: dict[str, Any] = field(default_factory=dict)
    prompt_version: str = ""
    schema_version: str = ""
    prompt_hash: str = ""


# ── Helpers de validación (HARN-04) ─────────────────────────────────────────


def _validate_generation(raw: str) -> GenerationOutput | None:
    """Valida el JSON crudo contra el schema canónico (HARN-04)."""
    try:
        parsed = parse_json_only(raw)
    except ValueError:
        return None
    try:
        return GenerationOutput.model_validate(parsed)
    except ValidationError:
        return None


def _generation_error(raw: str) -> str:
    try:
        parsed = parse_json_only(raw)
    except ValueError as exc:
        return f"JSON inválido: {exc}"
    try:
        GenerationOutput.model_validate(parsed)
        return "salida inválida"
    except ValidationError as exc:
        return f"schema inválido: {exc.errors()[0]['msg']}"


def repair_once(raw: str, error: str) -> str | None:
    """UNA reparación determinística de sintaxis (HARN-05).

    Solo corrige lo que el error permite corregir sin inventar contenido: elimina
    comas finales del JSON. Nunca reescribe contenido. Devuelve None si no hay
    reparación sintáctica posible (p. ej. cardinalidad o campos faltantes).
    """
    fixed = _TRAILING_COMMA_RE.sub(r"\1", raw)
    if fixed == raw:
        return None
    try:
        parse_json_only(fixed)
    except ValueError:
        return None
    return fixed


def _redact_raw_output(raw: str) -> str:
    """Redacta la salida cruda JSON sin romper su forma (HARN-07, §13.2).

    ``redact_secrets`` opera sobre estructuras, no sobre texto plano: la salida
    cruda se guarda solo en caminos de éxito (JSON válido), así que se parsea,
    se redacta y se vuelve a serializar. Si por cualquier motivo no parsea, se
    devuelve tal cual (nunca se pierde la traza por un fallo de redacción).
    """
    try:
        parsed = parse_json_only(raw)
    except ValueError:
        return raw
    return json.dumps(redact_secrets(parsed), ensure_ascii=False)


# ── Generación ──────────────────────────────────────────────────────────────


def run_generation(
    brief: BriefIn,
    provider: GenAIProvider,
    *,
    settings: Settings | None = None,
    backoff: Sequence[float] = DEFAULT_BACKOFF,
) -> RunResult:
    """Ejecuta una generación: prompt+hash → provider → validar → repair/retry.

    Hasta `MAX_ATTEMPTS` intentos (inicial + 2 reintentos) con backoff ante
    errores transitorios; UNA reparación de JSON inválido en el intento 1;
    agotado → `RunResult.failed("INVALID_OUTPUT" | "PROVIDER_TRANSIENT_ERROR")`
    conservando la traza (HARN-05, GEN-06). `raw_output` solo si
    `TRACE_STORE_RAW_OUTPUT=true`; `redact_secrets` siempre (HARN-07).
    """
    settings = settings or get_settings()
    events: list[dict[str, Any]] = []

    try:
        resolved = resolve_prompt(GENERATION_PROMPT_ID)
    except ManifestError as exc:
        events.append(
            build_trace_event(
                "generation_failed", error_code="PROMPT_MANIFEST_ERROR", error=str(exc)
            )
        )
        return RunResult(
            ok=False,
            trace_events=redact_secrets(events),
            error_code="PROMPT_MANIFEST_ERROR",
            provider=provider.name,
            model=provider.model,
            params=provider.params,
        )

    events.append(
        build_trace_event(
            "prompt_resolved",
            prompt_id=resolved.prompt_id,
            prompt_hash=resolved.sha256,
            schema_version=resolved.schema_version,
        )
    )

    for attempt in range(1, MAX_ATTEMPTS + 1):
        events.append(
            build_trace_event(
                "provider_invoked",
                provider=provider.name,
                model=provider.model,
                params=provider.params,
                attempt=attempt,
            )
        )
        try:
            raw = provider.generate_candidates(brief)
        except ProviderError as exc:
            events.append(
                build_trace_event(
                    "provider_error", attempt=attempt, code=exc.code, message=exc.message
                )
            )
            if exc.code == TRANSIENT and attempt < MAX_ATTEMPTS:
                delay = backoff[attempt - 1] if attempt - 1 < len(backoff) else 0.0
                events.append(
                    build_trace_event("retry_scheduled", attempt=attempt, backoff=delay)
                )
                time.sleep(delay)
                continue
            error_code = (
                "PROVIDER_TRANSIENT_ERROR" if exc.code == TRANSIENT else exc.code
            )
            events.append(
                build_trace_event("generation_failed", error_code=error_code, attempt=attempt)
            )
            return RunResult(
                ok=False,
                trace_events=redact_secrets(events),
                error_code=error_code,
                provider=provider.name,
                model=provider.model,
                params=provider.params,
                prompt_version=resolved.version,
                schema_version=resolved.schema_version,
                prompt_hash=resolved.sha256,
            )

        validated = _validate_generation(raw)
        if validated is not None:
            events.append(
                build_trace_event(
                    "output_validated",
                    checks=[{"name": "schema", "ok": True}],
                    attempt=attempt,
                )
            )
            return RunResult(
                ok=True,
                candidates=tuple(validated.candidates),
                trace_events=redact_secrets(events),
                provider=provider.name,
                model=provider.model,
                params=provider.params,
                prompt_version=resolved.version,
                schema_version=resolved.schema_version,
                prompt_hash=resolved.sha256,
                raw_output=(
                    _redact_raw_output(raw)
                    if settings.trace_store_raw_output
                    else None
                ),
            )

        error = _generation_error(raw)
        events.append(
            build_trace_event("validation_failed", attempt=attempt, error=error)
        )
        if attempt == 1:
            repaired = repair_once(raw, error)
            if repaired is None:
                # Sin reparación sintáctica posible (HARN-05): la traza no
                # mezcla repair_ok con repair_failed en el mismo intento.
                events.append(
                    build_trace_event("repair_failed", attempt=attempt, error=error)
                )
            else:
                events.append(build_trace_event("repair_ok", attempt=attempt))
                validated = _validate_generation(repaired)
                if validated is not None:
                    events.append(
                        build_trace_event(
                            "output_validated",
                            checks=[{"name": "schema", "ok": True}],
                            attempt=attempt,
                            repaired=True,
                        )
                    )
                    return RunResult(
                        ok=True,
                        candidates=tuple(validated.candidates),
                        trace_events=redact_secrets(events),
                        provider=provider.name,
                        model=provider.model,
                        params=provider.params,
                        prompt_version=resolved.version,
                        schema_version=resolved.schema_version,
                        prompt_hash=resolved.sha256,
                        raw_output=(
                            _redact_raw_output(repaired)
                            if settings.trace_store_raw_output
                            else None
                        ),
                    )

    events.append(build_trace_event("generation_failed", error_code=INVALID_OUTPUT))
    return RunResult(
        ok=False,
        trace_events=redact_secrets(events),
        error_code=INVALID_OUTPUT,
        provider=provider.name,
        model=provider.model,
        params=provider.params,
        prompt_version=resolved.version,
        schema_version=resolved.schema_version,
        prompt_hash=resolved.sha256,
    )


# ── Evaluación ──────────────────────────────────────────────────────────────


def _anonymize(candidate: Any) -> dict[str, Any]:
    """Anonimiza un candidato: solo contenido, sin metadatos (EVAL-07)."""
    claims = _field(candidate, "claims", ()) or ()
    return {
        "angle": _field(candidate, "angle"),
        "hook": _field(candidate, "hook"),
        "body": _field(candidate, "body"),
        "cta": _field(candidate, "cta"),
        "claims": [
            {
                "text": _field(claim, "text", ""),
                "support": _field(claim, "support", ""),
            }
            for claim in claims
        ],
    }


def run_evaluation(
    candidates: Sequence[Any],
    brief: BriefIn,
    provider: GenAIProvider,
    *,
    catalog_version: str | None = None,
    seed: int | None = None,
    settings: Settings | None = None,
    backoff: Sequence[float] = DEFAULT_BACKOFF,
) -> EvaluationRunResult:
    """Evalúa candidatos anonimizados y en orden aleatorio (EVAL-07).

    En modo demo el orden aleatorio es determinístico (seed fija); en remoto,
    aleatorio real. Si el evaluador semántico falla tras las políticas, degrada a
    `semantic_available=False` SIN fabricar un score completo (HARN-08 → el
    workflow mapea a `EVALUATION_PARTIAL`).
    """
    settings = settings or get_settings()
    version = catalog_version or CLICHE_CATALOG_VERSION
    events: list[dict[str, Any]] = []

    try:
        resolved = resolve_prompt(EVALUATION_PROMPT_ID)
    except ManifestError as exc:
        events.append(
            build_trace_event(
                "evaluation_failed", error_code="PROMPT_MANIFEST_ERROR", error=str(exc)
            )
        )
        return EvaluationRunResult(
            ok=False,
            semantic_available=False,
            trace_events=redact_secrets(events),
            error_code="PROMPT_MANIFEST_ERROR",
            provider=provider.name,
            model=provider.model,
            params=provider.params,
        )

    events.append(
        build_trace_event(
            "prompt_resolved",
            prompt_id=resolved.prompt_id,
            prompt_hash=resolved.sha256,
            schema_version=resolved.schema_version,
        )
    )

    order = list(range(len(candidates)))
    rng = random.Random(DEMO_SEED if provider.name == "DEMO_PROVIDER" else None)
    if seed is not None:
        rng = random.Random(seed)
    rng.shuffle(order)
    anonymous = [_anonymize(candidates[i]) for i in order]
    events.append(
        build_trace_event(
            "evaluation_anonymized", order=list(order), catalog_version=version
        )
    )

    for attempt in range(1, MAX_ATTEMPTS + 1):
        events.append(
            build_trace_event(
                "provider_invoked",
                provider=provider.name,
                model=provider.model,
                params=provider.params,
                attempt=attempt,
            )
        )
        try:
            raw = provider.evaluate_candidates(anonymous, brief, version)
        except ProviderError as exc:
            events.append(
                build_trace_event(
                    "provider_error", attempt=attempt, code=exc.code, message=exc.message
                )
            )
            if exc.code == TRANSIENT and attempt < MAX_ATTEMPTS:
                delay = backoff[attempt - 1] if attempt - 1 < len(backoff) else 0.0
                events.append(
                    build_trace_event("retry_scheduled", attempt=attempt, backoff=delay)
                )
                time.sleep(delay)
                continue
            # HARN-08: cualquier fallo terminal del evaluador semántico degrada a
            # solo-determinístico (design §12, 503). El código original del
            # provider queda en el evento de traza, no en el error_code del run.
            events.append(
                build_trace_event(
                    "evaluation_failed",
                    error_code=SEMANTIC_EVALUATION_UNAVAILABLE,
                    provider_code=exc.code,
                    semantic="unavailable",
                    attempt=attempt,
                )
            )
            return EvaluationRunResult(
                ok=False,
                semantic_available=False,
                trace_events=redact_secrets(events),
                error_code=SEMANTIC_EVALUATION_UNAVAILABLE,
                provider=provider.name,
                model=provider.model,
                params=provider.params,
                prompt_version=resolved.version,
                schema_version=resolved.schema_version,
                prompt_hash=resolved.sha256,
            )

        try:
            parsed = parse_json_only(raw)
            output = EvaluationOutput.model_validate(parsed)
        except (ValueError, ValidationError) as exc:
            events.append(
                build_trace_event("validation_failed", attempt=attempt, error=str(exc))
            )
            if attempt == 1:
                repaired = repair_once(raw, str(exc))
                if repaired is None:
                    events.append(
                        build_trace_event("repair_failed", attempt=attempt, error=str(exc))
                    )
                else:
                    # repair_ok y repair_failed son mutuamente excluyentes por
                    # intento: si la reparación sintáctica no alcanza, el loop
                    # reintenta con el provider (HARN-05).
                    events.append(build_trace_event("repair_ok", attempt=attempt))
                    try:
                        output = EvaluationOutput.model_validate(parse_json_only(repaired))
                    except (ValueError, ValidationError):
                        pass
                    else:
                        events.append(
                            build_trace_event(
                                "output_validated",
                                checks=[{"name": "schema", "ok": True}],
                                attempt=attempt,
                                repaired=True,
                            )
                        )
                        scores = _remap_scores(output.candidate_scores, order)
                        for score in scores:
                            events.append(
                                build_trace_event(
                                    "evaluation_scored",
                                    candidate_id=score.candidate_id,
                                    score_final=score.score_final,
                                    dimensions={
                                        name: _field(dimension, "rating")
                                        for name, dimension in score.dimensions.model_dump().items()
                                    },
                                    penalties={"risk": score.penalties.risk, "generic": score.penalties.generic},
                                    blockers=[blocker.code for blocker in score.blockers],
                                )
                            )
                        return EvaluationRunResult(
                            ok=True,
                            semantic_available=True,
                            candidate_scores=tuple(scores),
                            trace_events=redact_secrets(events),
                            provider=provider.name,
                            model=provider.model,
                            params=provider.params,
                            prompt_version=resolved.version,
                            schema_version=resolved.schema_version,
                            prompt_hash=resolved.sha256,
                        )
            continue

        events.append(
            build_trace_event(
                "output_validated",
                checks=[{"name": "schema", "ok": True}],
                attempt=attempt,
            )
        )
        scores = _remap_scores(output.candidate_scores, order)
        for score in scores:
            events.append(
                build_trace_event(
                    "evaluation_scored",
                    candidate_id=score.candidate_id,
                    score_final=score.score_final,
                    dimensions={
                        name: _field(dimension, "rating")
                        for name, dimension in score.dimensions.model_dump().items()
                    },
                    penalties={"risk": score.penalties.risk, "generic": score.penalties.generic},
                    blockers=[blocker.code for blocker in score.blockers],
                )
            )
        return EvaluationRunResult(
            ok=True,
            semantic_available=True,
            candidate_scores=tuple(scores),
            trace_events=redact_secrets(events),
            provider=provider.name,
            model=provider.model,
            params=provider.params,
            prompt_version=resolved.version,
            schema_version=resolved.schema_version,
            prompt_hash=resolved.sha256,
        )

    events.append(
        build_trace_event(
            "evaluation_failed",
            error_code=SEMANTIC_EVALUATION_UNAVAILABLE,
            semantic="unavailable",
        )
    )
    return EvaluationRunResult(
        ok=False,
        semantic_available=False,
        trace_events=redact_secrets(events),
        error_code=SEMANTIC_EVALUATION_UNAVAILABLE,
        provider=provider.name,
        model=provider.model,
        params=provider.params,
        prompt_version=resolved.version,
        schema_version=resolved.schema_version,
        prompt_hash=resolved.sha256,
    )


def _remap_scores(
    scores: Sequence[CandidateScore], order: Sequence[int]
) -> tuple[CandidateScore, ...]:
    """Re-mapea `candidate_id` de posición barajada a posición original (EVAL-07)."""
    inverse = {position: original for original, position in enumerate(order)}
    remapped: list[CandidateScore] = []
    for score in scores:
        remapped.append(score.model_copy(update={"candidate_id": inverse[score.candidate_id]}))
    return tuple(remapped)


def _field(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


__all__ = [
    "DEFAULT_BACKOFF",
    "DEMO_SEED",
    "EVALUATION_PROMPT_ID",
    "GENERATION_PROMPT_ID",
    "EvaluationRunResult",
    "ManifestError",
    "ResolvedPrompt",
    "RunResult",
    "repair_once",
    "resolve_prompt",
    "run_evaluation",
    "run_generation",
]
