"""`DemoProvider` determinístico (design §6.3, HARN-03).

SIN random ni red: deriva los tres candidatos del brief (tesis, audiencia,
objetivo y evidencia reales) y evalúa con las MISMAS reglas determinísticas del
dominio (penalizaciones y blockers), de modo que atraviesa los mismos schemas,
guardrails, validaciones y trazas que un provider remoto. Solo sustituye la
llamada externa (§12.7).

`DEMO_FORCE_INVALID=1` fuerza una salida JSON inválida para recorrer el camino
`repair → validation_failed → GENERATION_FAILED` (segundo caso de la demo).
"""
from __future__ import annotations

import json
from typing import Any, Sequence

from api.schemas import BriefIn

from domain.blockers import activate_blockers
from domain.score import (
    base_score,
    penalizacion_genericidad,
    penalizacion_riesgo,
    score_final,
)
from domain.validation import (
    contains_personal_experience,
    load_cliche_catalog,
    normalize_text,
)

# Términos de nicho COBOL/mainframe para la dimensión de relevancia (VOI-05).
_NICHE_TERMS = (
    "cobol",
    "mainframe",
    "jcl",
    "cics",
    "ims",
    "batch",
    "jobs",
    "migracion",
    "reglas de negocio",
    "conocimiento operativo",
)

# JSON inválido por diseño (misma forma que `regression_invalid_json.json`):
# coma final + candidato incompleto → repair no alcanza → GENERATION_FAILED.
INVALID_RAW_OUTPUT = '{"candidates": [{"angle": "problem-story",}],}'

_RUBRIC_RULES = {
    "hook": "EVAL-02 ancla: hook excepcional para el brief con evidencia textual.",
    "niche_relevance": "EVAL-02 ancla: relevancia demostrable para el nicho mainframe.",
    "specificity_evidence": "EVAL-02 ancla: especificidad y evidencia textual concreta.",
    "clarity": "EVAL-02 ancla: claridad y legibilidad sin relleno.",
    "conversation_potential": "EVAL-02 ancla: cierre con pregunta especifica, sin bait.",
    "voice_fit": "VOI-02: voz tecnica, sobria y didactica, sin cliches.",
}

# Diferenciación mínima y determinística por ángulo (design §6.3): el ángulo,
# NO el brief ni el azar, define un sesgo pequeño y estable entre candidatos.
# Sin esto, los tres candidatos del demo empatan en score y la regla de
# decisión (§7.3) nunca alcanza un `RECOMMENDED` con brecha >= 4 en el caso
# base. Cada +1/-1 se traduce en ±4 pts (dimensión 0.20) o ±2 pts (0.10).
_ANGLE_DELTAS = {
    "problem-story": {"voice_fit": 1},  # ancla narrativa: voz sobria/didáctica
    "practical-framework": {"hook": -1},  # marco: hook más funcional que narrativo
    "argued-position": {"hook": -1},  # postura: hook menos anclado al problema
}


class DemoProvider:
    """Provider determinístico etiquetado ``DEMO_PROVIDER`` (HARN-03, §12.7)."""

    name = "DEMO_PROVIDER"
    model: str | None = None
    params: dict[str, Any] = {}

    def __init__(self, force_invalid: bool | None = None) -> None:
        self._force_invalid = bool(force_invalid)

    # ── Generación ──────────────────────────────────────────────────────────

    def generate_candidates(self, brief: BriefIn) -> str:
        """Devuelve JSON crudo con 3 candidatos derivados del brief (determinístico)."""
        if self._force_invalid:
            return INVALID_RAW_OUTPUT
        candidates = [self._build_candidate(angle, brief) for angle in _ANGLES]
        return json.dumps({"candidates": candidates}, ensure_ascii=False)

    def _build_candidate(self, angle: str, brief: BriefIn) -> dict[str, Any]:
        thesis = brief.thesis.strip()
        audience = brief.audience.strip() or "equipos de mainframe"
        claims = [
            {"text": item.text.strip(), "support": item.id}
            for item in brief.evidence
            if item.text.strip() and item.id
        ]
        hook, body, cta = _TEMPLATES[angle](thesis, audience)
        return {
            "angle": angle,
            "hook": hook,
            "body": body,
            "cta": cta,
            "claims": claims,
        }

    # ── Evaluación ──────────────────────────────────────────────────────────

    def evaluate_candidates(
        self,
        candidates: Sequence[Any],
        brief: BriefIn,
        catalog_version: str,
    ) -> str:
        """Devuelve JSON crudo de evaluación (heurística determinística).

        Aplica las MISMAS penalizaciones y blockers del dominio: una cifra sin
        fuente o una experiencia inventada reciben `penalizacion_riesgo` y
        blocker, igual que con un provider remoto (HARN-03).
        """
        catalog = load_cliche_catalog()
        evidence = tuple(brief.evidence)
        bodies = [self._field(candidate, "body") for candidate in candidates]
        scores = [
            self._score_candidate(candidate, evidence, bodies, catalog, index)
            for index, candidate in enumerate(candidates)
        ]
        return json.dumps({"candidate_scores": scores}, ensure_ascii=False)

    def _score_candidate(
        self,
        candidate: Any,
        evidence: Sequence[Any],
        bodies: Sequence[str],
        catalog: Any,
        candidate_id: int,
    ) -> dict[str, Any]:
        hook = self._field(candidate, "hook")
        body = self._field(candidate, "body")
        cta = self._field(candidate, "cta")
        claims = self._field(candidate, "claims") or ()
        angle = str(self._field(candidate, "angle", ""))
        dimensions = self._dimensions(hook, body, cta, claims, evidence, catalog, angle)
        # base_score (dominio) espera {dimension: {"rating": int}}; el evaluador
        # demo entrega {dimension: {"rating", "quote", "rubric_rule"}} (HARN-03).
        ratings = {
            name: {"rating": rating, "quote": quote, "rubric_rule": _RUBRIC_RULES[name]}
            for name, (rating, quote) in dimensions.items()
        }
        risk = penalizacion_riesgo(claims, evidence)
        generic = penalizacion_genericidad(
            body,
            catalog,
            # "other_candidates": excluye el propio body, o toda comparación
            # consigo mismo sumaría 5 de genericidad (falso positivo).
            [other for index, other in enumerate(bodies) if index != candidate_id],
        )
        base = base_score(ratings)
        final = score_final(base, risk, generic)
        blockers = [
            {
                "code": blocker.code,
                "message": blocker.message,
                "detail": blocker.detail,
            }
            for blocker in activate_blockers(candidate, evidence)
        ]
        return {
            "candidate_id": candidate_id,
            "dimensions": ratings,
            "penalties": {"risk": int(risk), "generic": int(generic)},
            "score_final": final,
            "blockers": blockers,
        }

    def _dimensions(
        self,
        hook: str,
        body: str,
        cta: str,
        claims: Sequence[Any],
        evidence: Sequence[Any],
        catalog: Any,
        angle: str = "",
    ) -> dict[str, tuple[int, str]]:
        """Heurísticas determinísticas 0-5 con cita textual (EVAL-02/03)."""
        body_lower = body.casefold()
        niche_hits = sum(1 for term in _NICHE_TERMS if term in body_lower)
        cliches = [
            phrase
            for phrase in catalog.phrases
            if normalize_text(phrase) in normalize_text(body)
        ]
        evidence_ids = {str(item.id) for item in evidence}
        supported = sum(
            1
            for claim in claims
            if str(self._field(claim, "support", "")) in evidence_ids
            or self._field(claim, "support", "") == "author_opinion"
        )

        hook_rating = 4
        if len(hook) >= 30 and niche_hits >= 1:
            hook_rating = 5
        elif len(hook) < 15:
            hook_rating = 3
        quote_hook = hook[:90] or body[:90]

        niche_rating = 1 if niche_hits == 0 else min(5, 2 + niche_hits)

        if not claims:
            specificity = 1
        elif supported == len(claims):
            specificity = 5
        elif supported > 0:
            specificity = 3
        else:
            specificity = 1
        quote_spec = (self._field(claims[0], "text", "") if claims else body)[:90]

        clarity = 4 if 60 <= len(body) <= 1_500 else 3
        if cliches:
            clarity = min(clarity, 3)
        quote_clarity = body[:90]

        cta_lower = cta.casefold()
        if cta.endswith("?") and "que opinas" not in cta_lower:
            conversation = 5
        elif "que opinas" in cta_lower:
            conversation = 1
        else:
            conversation = 3
        quote_conv = cta[:60]

        voice = 4
        if cliches:
            voice = max(0, 4 - 2 * len(cliches))
        if contains_personal_experience(body):
            voice = max(0, voice - 2)
        quote_voice = body[:90]

        raw = {
            "hook": (hook_rating, quote_hook),
            "niche_relevance": (niche_rating, body[:90]),
            "specificity_evidence": (specificity, quote_spec),
            "clarity": (clarity, quote_clarity),
            "conversation_potential": (conversation, quote_conv),
            "voice_fit": (voice, quote_voice),
        }
        deltas = _ANGLE_DELTAS.get(angle, {})
        return {
            name: (min(5, max(0, rating + deltas.get(name, 0))), quote)
            for name, (rating, quote) in raw.items()
        }

    @staticmethod
    def _field(obj: Any, name: str, default: Any = None) -> Any:
        if isinstance(obj, dict):
            return obj.get(name, default)
        return getattr(obj, name, default)


_ANGLES = ("problem-story", "practical-framework", "argued-position")


def _template_problem_story(thesis: str, audience: str) -> tuple[str, str, str]:
    hook = f"El problema que nadie documenta: {thesis}"
    body = (
        f"{thesis} Cuando el conocimiento operativo vive en una sola persona, cada "
        f"silencio se paga en el siguiente corte de batch. Para {audience}, el primer "
        f"paso no es traducir sintaxis: es mapear jobs JCL, excepciones operativas y "
        f"responsables antes de tocar una línea."
    )
    cta = "¿Qué excepción operativa no está documentada en tu entorno?"
    return hook, body, cta


def _template_practical_framework(thesis: str, audience: str) -> tuple[str, str, str]:
    hook = f"Un marco práctico para {thesis}"
    body = (
        f"{thesis} Un plan accionable para {audience} tiene tres pasos: inventariar las "
        f"reglas de negocio que corren hoy, priorizar por frecuencia y riesgo, y validar "
        f"cada excepción con quien la opera. Ese inventario convierte conocimiento tácito "
        f"en decisiones verificables de negocio."
    )
    cta = "¿Cuál de los tres pasos es el más difícil de sostener en tu equipo?"
    return hook, body, cta


def _template_argued_position(thesis: str, audience: str) -> tuple[str, str, str]:
    hook = f"Mi postura: {thesis}"
    body = (
        f"{thesis} Para {audience}, modernizar no es cambiar de lenguaje; es preservar el "
        f"comportamiento que nadie documentó. Traducir sintaxis sin traducir reglas de "
        f"negocio transfiere el riesgo en vez de eliminarlo. La decisión correcta empieza "
        f"por el inventario, no por el compilador."
    )
    cta = "¿Tu organización mide el riesgo de migración por sintaxis o por reglas?"
    return hook, body, cta


_TEMPLATES = {
    "problem-story": _template_problem_story,
    "practical-framework": _template_practical_framework,
    "argued-position": _template_argued_position,
}


__all__ = ["DemoProvider", "INVALID_RAW_OUTPUT"]
