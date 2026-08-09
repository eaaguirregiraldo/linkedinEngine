# backend/api/schemas.py
"""Contrato canónico FE/BE (pydantic) — única fuente de verdad del contrato.

ADR-003: todos los modelos de request/response viven acá como pydantic; FastAPI
genera ``/openapi.json`` a partir de ellos y el frontend genera ``schema.d.ts``
con ``openapi-typescript``. Los contratos del harness GenAI
(``backend/ai/contracts.py``) reutilizan los MISMOS modelos: el schema que
valida la salida del provider es el del contrato API (design §5.1, §5.5).
"""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# ── Enumeraciones canónicas ────────────────────────────────────────────────

Angle = Literal["problem-story", "practical-framework", "argued-position"]
"""Enumeración cerrada de ángulos narrativos (GEN-02)."""

EvidenceKind = Literal["known_facts", "author_opinions", "open_questions"]
"""Clasificación de afirmaciones del brief (CAP-05)."""

Outcome = Literal["RECOMMENDED", "REVISION_REQUIRED"]
"""Resultado de la regla de decisión (EVAL-06)."""

Notice = Literal["no se envió contenido a LinkedIn"]
"""Aviso inequívoco de publicación simulada (SIM-01, SIM-02)."""


# ── Captura del brief (RF-01, specs capture) ───────────────────────────────


class EvidenceItem(BaseModel):
    """Afirmación del brief clasificada por tipo (CAP-05, design §5.5)."""

    id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    type: EvidenceKind


class BriefIn(BaseModel):
    """Brief editorial canónico (design §5.5; capture CAP-02/03/05).

    La tesis MUST ser única y no vacía; la obligación de al menos una
    evidencia la gobierna el guard de la FSM (design §4.2 transición 1),
    no este schema.
    """

    thesis: str
    audience: str = ""
    objective: str = ""
    evidence: list[EvidenceItem] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)

    @field_validator("thesis")
    @classmethod
    def _thesis_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("thesis must not be empty")
        return v


# ── Salida de generación (RF-02; generation GEN-01/02/04) ──────────────────


class ClaimOut(BaseModel):
    """Claim del candidato con soporte declarado (GEN-04).

    ``support`` referencia una evidencia del brief, ``author_opinion`` o
    ``needs_review``; la existencia real del soporte la valida el dominio
    (design §5.5).
    """

    text: str = Field(min_length=1)
    support: str = Field(min_length=1)


class CandidateOutput(BaseModel):
    """Candidato tal como lo produce el provider (sin id/versión/estado).

    Es la pieza que valida el harness GenAI (HARN-04): campos no vacíos,
    enumeración cerrada de ángulos, claims con soporte (GEN-04).
    """

    angle: Angle
    hook: str = Field(min_length=1)
    body: str = Field(min_length=1)
    cta: str = Field(min_length=1)
    claims: list[ClaimOut] = Field(default_factory=list)


class GenerationOutput(BaseModel):
    """Salida validada del harness de generación (GEN-01/02).

    Reglas del contrato: exactamente 3 candidatos y ``angle`` únicos; ambas
    violaciones rechazan la salida (model_validator, design §5.5).
    """

    candidates: list[CandidateOutput]

    @model_validator(mode="after")
    def _check_cardinality_and_uniqueness(self) -> "GenerationOutput":
        if len(self.candidates) != 3:
            raise ValueError(
                f"generation must contain exactly 3 candidates, got {len(self.candidates)}"
            )
        angles = [c.angle for c in self.candidates]
        if len(set(angles)) != len(angles):
            raise ValueError(f"candidate angles must be unique, got {sorted(angles)}")
        return self


class CandidateOut(CandidateOutput):
    """Candidato del contrato API: suma id, versión y evaluación (design §5.5)."""

    id: int
    content_version: int = 1
    evaluation: "EvaluationSummary | None" = None
    decision: str | None = None


# ── Evaluación (RF-03; evaluation EVAL-01/02/03/04) ─────────────────────────


class DimensionScore(BaseModel):
    """Nota ordinal 0-5 con cita y regla de rúbrica (EVAL-02/03).

    Una nota sin ``quote`` y ``rubric_rule`` es inválida (design §4.4).
    """

    rating: int = Field(ge=0, le=5)
    quote: str = Field(min_length=1)
    rubric_rule: str = Field(min_length=1)


class DimensionRatings(BaseModel):
    """Las 6 dimensiones de la fórmula §7.2 (design §4.4)."""

    hook: DimensionScore
    niche_relevance: DimensionScore
    specificity_evidence: DimensionScore
    clarity: DimensionScore
    conversation_potential: DimensionScore
    voice_fit: DimensionScore


class Penalties(BaseModel):
    """Penalizaciones de la fórmula (EVAL-04)."""

    risk: int = Field(default=0, ge=0)
    generic: int = Field(default=0, ge=0)


class Blocker(BaseModel):
    """Blocker de evidencia/seguridad (EVAL-05, design §4.5)."""

    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    detail: str | None = None


class CandidateScore(BaseModel):
    """Score desglosado de un candidato (design §5.5, EVAL-01/02/03)."""

    candidate_id: int
    dimensions: DimensionRatings
    penalties: Penalties = Field(default_factory=Penalties)
    score_final: int = Field(ge=0, le=100)
    blockers: list[Blocker] = Field(default_factory=list)


class DecisionOut(BaseModel):
    """Decisión de la regla reproducible (design §4.5, EVAL-06)."""

    outcome: Outcome
    best_candidate_id: int | None = None
    reason: str = Field(min_length=1)
    brief_needs_revision: bool = False


class EvaluationSummary(BaseModel):
    """Resumen de evaluación incrustado en ``CandidateOut`` (design §5.5)."""

    score_final: int = Field(ge=0, le=100)
    decision: str | None = None


class EvaluationOutput(BaseModel):
    """Salida validada del evaluador (LLM) — el mismo schema del contrato API.

    Reexportada por ``ai.contracts`` (HARN-04, C.2): una sola definición.
    """

    candidate_scores: list[CandidateScore]


class EvaluationOut(BaseModel):
    """Respuesta de ``POST /api/runs/{run_id}/evaluate`` (design §5.4)."""

    candidate_scores: list[CandidateScore]
    decision: DecisionOut


# ── Visual (RF-05; visual VIS-01/03/04) ─────────────────────────────────────


class VisualElement(BaseModel):
    """Elemento visual con vínculo obligatorio a la tesis (VIS-03)."""

    element_id: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    description: str = Field(min_length=1)
    rationale: str = Field(min_length=1)


class VisualContract(BaseModel):
    """Contrato visual derivado de la tesis (design §7, VIS-01)."""

    thesis: str = Field(min_length=1)
    concept: str = Field(min_length=1)
    elements: list[VisualElement] = Field(default_factory=list)
    alt_text: str = Field(min_length=1)
    status: str = "VISUAL_DRAFT"


class VisualOut(VisualContract):
    """Respuesta del flujo visual: contrato + metadatos del asset (§5.4)."""

    id: int
    candidate_id: int
    svg_path: str | None = None


# ── Publicación simulada (RF-06; simulation SIM-01/02) ──────────────────────


class ReceiptOut(BaseModel):
    """Recibo local de publicación simulada (design §5.5, SIM-02).

    ``remote_id`` es ``None`` SIEMPRE en modo simulado: jamás un ID remoto
    inventado. ``mode``/``status``/``notice`` son literales cerrados.
    """

    id: int
    mode: Literal["simulated"] = "simulated"
    status: Literal["SIMULATED_PUBLISHED"] = "SIMULATED_PUBLISHED"
    candidate_id: int
    visual_id: int
    created_at: str
    notice: Notice = "no se envió contenido a LinkedIn"
    remote_id: None = None


class PublicationOut(BaseModel):
    """Respuesta de ``POST /api/candidates/{id}/publish-simulated`` (§5.4)."""

    receipt: ReceiptOut
    candidate_id: int
    visual_id: int
    mode: Literal["simulated"] = "simulated"
    status: Literal["SIMULATED_PUBLISHED"] = "SIMULATED_PUBLISHED"


# ── Errores estructurados (design §12, api API-04) ──────────────────────────


class ErrorDetail(BaseModel):
    """Detalle de error único: código + mensaje accionable + detalles."""

    code: str
    message: str
    details: dict[str, Any] = Field(
        default_factory=dict,
        json_schema_extra={"additionalProperties": True},
    )


class ErrorBody(BaseModel):
    """Envelope de error: ``{"error": {"code", "message", "details"}}``."""

    error: ErrorDetail


# ── Ideas demo y proyectos (capture CAP-01, design §9.3) ────────────────────


class DemoIdeaOut(BaseModel):
    """Idea demo ofrecida por ``GET /api/ideas/demo`` (design §9.3)."""

    id: str = Field(min_length=1)
    raw_idea: str = Field(min_length=1)
    default_audience: str = ""
    default_objective: str = ""


class ProjectCreate(BaseModel):
    """Request de ``POST /api/projects`` (design §5.4; CAP-01)."""

    raw_idea: str
    title: str | None = None

    @field_validator("raw_idea")
    @classmethod
    def _raw_idea_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("raw_idea must not be empty")
        return v


class ProjectOut(BaseModel):
    """Proyecto (vista de lista, P1-ready — design §5.4/§9.1)."""

    id: int
    raw_idea: str
    title: str | None = None
    status: str = "IDEA"
    created_at: str
    updated_at: str


class VoiceProfileOut(BaseModel):
    """Perfil de voz v0 PROVISIONAL (VOI-01): explícitamente no validado."""

    version: str = "v0"
    label: str = "perfil de voz provisional v0"
    provisional: bool = True
    rules: list[str] = Field(default_factory=list)


class ProjectDetailOut(ProjectOut):
    """Proyecto con brief y voz aplicada (design §5.4)."""

    brief: BriefIn | None = None
    voice_profile: VoiceProfileOut | None = None


# ── Runs y traza (RF-07; fsm-trace TRC-01/02) ───────────────────────────────


class RunOut(BaseModel):
    """Respuesta de generate/retry-generate: run + candidatos (design §5.4)."""

    id: int
    project_id: int
    status: str
    provider: str
    model: str | None = None
    prompt_version: str
    schema_version: str
    prompt_hash: str
    candidates: list[CandidateOut] = Field(default_factory=list)
    error_code: str | None = None
    started_at: str
    completed_at: str | None = None


class TraceEventOut(BaseModel):
    """Evento de traza tipado (design §6.6); el resto de campos son datos.

    ``extra="allow"``: cada evento lleva sus propios campos (provider, prompt_id,
    score_final, …) manteniendo ``ts``/``type`` como base del contrato.
    """

    model_config = ConfigDict(extra="allow")

    ts: str
    type: str


class RunDetailOut(BaseModel):
    """Traza completa de una ejecución, ya redactada (TRC-01/02)."""

    run: RunOut
    trace_events: list[TraceEventOut] = Field(default_factory=list)
    brief: BriefIn | None = None
    voice_profile: VoiceProfileOut | None = None


# ── Health y edición (api API-01; approval APPR-02) ─────────────────────────


class HealthOut(BaseModel):
    """Respuesta de ``GET /api/health``."""

    status: Literal["ok"] = "ok"
    provider: str | None = None


class ReasonIn(BaseModel):
    """Razón editorial obligatoria (APPR-01/04, VIS-06)."""

    reason: str = Field(min_length=1)

    @field_validator("reason")
    @classmethod
    def _reason_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("reason must not be empty")
        return v


class CandidateContent(BaseModel):
    """Contenido editable de un candidato (APPR-02)."""

    hook: str = Field(min_length=1)
    body: str = Field(min_length=1)
    cta: str = Field(min_length=1)


class CandidateEdit(BaseModel):
    """Request de ``POST /api/candidates/{id}/edit`` (design §5.4)."""

    content: CandidateContent


__all__ = [
    # Enumeraciones
    "Angle",
    "EvidenceKind",
    "Outcome",
    "Notice",
    # Captura
    "EvidenceItem",
    "BriefIn",
    # Generación
    "ClaimOut",
    "CandidateOutput",
    "GenerationOutput",
    "CandidateOut",
    # Evaluación
    "DimensionScore",
    "DimensionRatings",
    "Penalties",
    "Blocker",
    "CandidateScore",
    "EvaluationOutput",
    "EvaluationOut",
    "DecisionOut",
    "EvaluationSummary",
    # Visual
    "VisualElement",
    "VisualContract",
    "VisualOut",
    # Publicación
    "ReceiptOut",
    "PublicationOut",
    # Errores
    "ErrorDetail",
    "ErrorBody",
    # Ideas demo / proyectos
    "DemoIdeaOut",
    "ProjectCreate",
    "ProjectOut",
    "VoiceProfileOut",
    "ProjectDetailOut",
    # Runs y traza
    "RunOut",
    "TraceEventOut",
    "RunDetailOut",
    # Health y edición
    "HealthOut",
    "ReasonIn",
    "CandidateContent",
    "CandidateEdit",
]
