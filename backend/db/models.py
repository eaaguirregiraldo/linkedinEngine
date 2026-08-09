"""Modelos SQLModel: los 5 agregados de design §9.1 / SOLUTION.md §11.1 (D.2).

Evaluación, decisiones y traza se persisten como JSON embebido en
``GenerationRun``/``Candidate`` (proposal y §11.1 lo autorizan).

Invariantes de design §9.2 aplicadas a nivel de modelo/repos:
- ``angle`` único por run: ``UniqueConstraint(run_id, angle)`` (invariante 6).
- ``remote_id`` SIEMPRE ``None`` en modo simulado (invariante 5, ADR-007):
  validado en el modelo y forzado por el repo de publicación.
- SIN columnas de credenciales (PST-02): ninguna tabla persiste keys/tokens.
- ``trace_events`` append-only (TRC-03): la capa de repos solo expone append.

Nota de timestamps: se guardan UTC sin tzinfo (SQLite no soporta zonas
horarias); evita comparaciones entre aware/naive aguas abajo.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import JSON, Column, UniqueConstraint
from sqlmodel import Field, SQLModel

__all__ = [
    "VOICE_V0",
    "utcnow",
    "ContentProject",
    "GenerationRun",
    "Candidate",
    "VisualAsset",
    "PublicationAttempt",
]


def utcnow() -> datetime:
    """Timestamp UTC naive (SQLite no conserva tzinfo)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# Perfil de voz v0 PROVISIONAL (SOLUTION.md §4.2): hipótesis no validada,
# etiquetada como provisional en UI y traza. No es un corpus validado.
VOICE_V0: dict[str, Any] = {
    "version": "v0",
    "label": "perfil de voz provisional v0",
    "rules": [
        "Técnica y sobria, con autoridad basada en experiencia, no en grandilocuencia.",
        "Didáctica para personas no especialistas, sin tratar a COBOL como una curiosidad arqueológica.",
        "Directa y levemente contraria a lugares comunes, pero no provocadora por defecto.",
        "Usa ejemplos concretos, consecuencias operativas y decisiones de negocio.",
        "Evita frases vacías como 'el futuro ya llegó', 'en un mundo en constante evolución' o "
        "'COBOL está más vivo que nunca' sin evidencia.",
        "No inventa experiencias en primera persona; solo usa 'vi', 'lideré' o 'aprendí' "
        "cuando el autor haya aportado esa evidencia.",
        "Cierra con una pregunta específica o invitación a compartir experiencia, no con engagement bait.",
    ],
}


class ContentProject(SQLModel, table=True):
    """Agregado raíz: idea → brief → estado FSM del proyecto (design §9.1)."""

    __tablename__ = "contentproject"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: Optional[str] = Field(default=None, max_length=200)
    raw_idea: str = Field(max_length=2000)
    brief: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    status: str = Field(default="IDEA", max_length=40)
    voice_profile: dict[str, Any] = Field(
        default_factory=lambda: dict(VOICE_V0), sa_column=Column(JSON)
    )
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class GenerationRun(SQLModel, table=True):
    """Una ejecución de generación con su traza (design §9.1, §6.6)."""

    __tablename__ = "generationrun"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="contentproject.id", index=True)
    # status ∈ GENERATING | GENERATED | GENERATION_FAILED
    status: str = Field(default="GENERATING", max_length=40)
    provider: str = Field(max_length=80)
    model: Optional[str] = Field(default=None, max_length=120)
    prompt_version: str = Field(default="", max_length=40)
    schema_version: str = Field(default="", max_length=40)
    prompt_hash: str = Field(default="", max_length=128)
    started_at: datetime = Field(default_factory=utcnow)
    completed_at: Optional[datetime] = Field(default=None)
    error_code: Optional[str] = Field(default=None, max_length=60)
    # Solo se persiste salida cruda si TRACE_STORE_RAW_OUTPUT=true (decide el
    # harness; §12.6). Por defecto el contenido queda descartado.
    raw_output: Optional[str] = Field(default=None)
    # Append-only (TRC-03): los repos solo agregan eventos, nunca mutan/borran.
    trace_events: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))


class Candidate(SQLModel, table=True):
    """Candidato producido por un run (design §9.1; invariante 6: angle único)."""

    __tablename__ = "candidate"
    __table_args__ = (UniqueConstraint("run_id", "angle", name="uq_candidate_run_angle"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="generationrun.id", index=True)
    # angle ∈ problem-story | practical-framework | argued-position (contrato C)
    angle: str = Field(max_length=40)
    hook: str = Field(max_length=600)
    body: str = Field(max_length=4000)
    cta: str = Field(max_length=600)
    claims: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    content_version: int = Field(default=1)
    # Evaluación ACTUAL (dimensiones + penalizaciones + score). Al editar se
    # invalida (None); la evaluación previa queda en trace_events (TRC-03).
    evaluation: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    # Historial de decisiones append-only [{decision, by, reason, at}].
    decision_history: Optional[list[dict[str, Any]]] = Field(default=None, sa_column=Column(JSON))
    selected: bool = Field(default=False)
    selection_reason: Optional[str] = Field(default=None, max_length=500)


class VisualAsset(SQLModel, table=True):
    """Contrato visual + ruta SVG local (design §7, §9.1)."""

    __tablename__ = "visualasset"

    id: Optional[int] = Field(default=None, primary_key=True)
    candidate_id: int = Field(foreign_key="candidate.id", index=True)
    thesis: str = Field(max_length=1000)
    concept: str = Field(max_length=500)
    # [{element_id, kind, description, rationale}] — rationale obligatorio (VIS-03)
    elements: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    alt_text: str = Field(max_length=500)
    svg_path: Optional[str] = Field(default=None, max_length=500)
    # status ∈ VISUAL_DRAFT | VISUAL_READY | VISUAL_REVISION_REQUIRED
    status: str = Field(default="VISUAL_DRAFT", max_length=40)


class PublicationAttempt(SQLModel, table=True):
    """Intento de publicación (modo simulado en P0; ADR-007).

    Invariante 5 (§9.2): en modo ``simulated`` ``remote_id`` es SIEMPRE
    ``None`` — jamás un ID remoto inventado (SIM-02, RNF-02). El repo
    ``save_publication_attempt`` lo fuerza al crear; no hay camino para
    persistir un intento simulado con ``remote_id`` no nulo. Nota: SQLModel
    ``table=True`` (0.0.22) no ejecuta field validators de pydantic en
    ``__init__``, por eso la garantía vive en la capa de repos.
    """

    __tablename__ = "publicationattempt"

    id: Optional[int] = Field(default=None, primary_key=True)
    candidate_id: int = Field(foreign_key="candidate.id", index=True)
    mode: str = Field(default="simulated", max_length=20)
    status: str = Field(max_length=40)  # SIMULATED_PUBLISHED
    remote_id: Optional[str] = Field(default=None)
    receipt: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utcnow)
