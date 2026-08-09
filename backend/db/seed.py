"""Seed demo idempotente (D.4, design §9.3, ADR-008; capture CAP-01/CAP-03).

Inserta 3 ideas demo (design §9.3) con brief prefijado y voz v0 provisional
(dada por el default del modelo) SOLO si ``ContentProject`` está vacío.
Regenerar el estado demo = borrar ``data/engine.db`` y arrancar de nuevo
(rollback plan; PST-01 escenario "seed reproducible").

La forma del brief sigue el contrato canónico (C.1): ``evidence`` usa
``{id, text, type}`` con ``type ∈ known_facts|author_opinions|open_questions``
y ``audience``/``objective`` por defecto por idea (CAP-03), que la API expone
como ``DemoIdeaOut{id, raw_idea, default_audience, default_objective}``.
"""
from __future__ import annotations

from typing import Any

from sqlmodel import Session, select

from db.models import ContentProject

__all__ = ["DEMO_IDEAS", "seed_demo_data", "list_demo_ideas"]


DEMO_IDEAS: list[dict[str, Any]] = [
    {
        "id": "demo-cobol-knowledge",
        "title": "Migrar COBOL es recuperar conocimiento",
        "raw_idea": (
            "Migrar COBOL no es traducir sintaxis; es recuperar conocimiento "
            "operativo antes de tocar código"
        ),
        "audience": "líderes de modernización",
        "objective": (
            "plantear la migración como recuperación de conocimiento operativo, "
            "no como reescritura de sintaxis"
        ),
        "thesis": (
            "Migrar COBOL no es traducir sintaxis; es recuperar conocimiento "
            "operativo antes de tocar código."
        ),
        "evidence": [
            {
                "id": "e1",
                "text": (
                    "El conocimiento operativo vive en reglas de negocio y "
                    "excepciones que rara vez están documentadas."
                ),
                "type": "known_facts",
            },
            {
                "id": "e2",
                "text": (
                    "La sintaxis COBOL es la parte más simple del sistema; el "
                    "riesgo está en lo que el código hace, no en cómo se escribe."
                ),
                "type": "known_facts",
            },
            {
                "id": "e3",
                "text": (
                    "Un proyecto de modernización que empieza traduciendo código "
                    "sin mapear conocimiento previo transfiere bugs y deuda."
                ),
                "type": "author_opinions",
            },
            {
                "id": "e4",
                "text": (
                    "¿Cuánto del conocimiento operativo de un mainframe queda "
                    "registrado antes de apagarlo?"
                ),
                "type": "open_questions",
            },
        ],
        "constraints": [
            "No inventar cifras de empresas.",
            "No presentar la migración como trivial.",
        ],
    },
    {
        "id": "demo-mainframe-reason",
        "title": "El mainframe sigue en producción por una razón",
        "raw_idea": (
            "El mainframe sigue en producción por una razón: décadas de reglas "
            "de negocio que nadie se atreve a tocar"
        ),
        "audience": "arquitectos",
        "objective": (
            "explicar por qué el mainframe persiste: reglas de negocio "
            "acumuladas y riesgo percibido"
        ),
        "thesis": (
            "El mainframe sigue en producción por una razón: décadas de reglas "
            "de negocio que nadie se atreve a tocar."
        ),
        "evidence": [
            {
                "id": "e1",
                "text": (
                    "Los mainframes procesan una proporción mayoritaria de las "
                    "transacciones críticas de la industria."
                ),
                "type": "known_facts",
            },
            {
                "id": "e2",
                "text": (
                    "El miedo no es al hardware, sino a romper reglas de negocio "
                    "que nadie documentó a tiempo."
                ),
                "type": "author_opinions",
            },
            {
                "id": "e3",
                "text": "¿Qué regla de negocio se perdió en la última migración que conocés?",
                "type": "open_questions",
            },
        ],
        "constraints": [
            "Sin cifras absolutas sin fuente.",
            "No tratar el mainframe como reliquia.",
        ],
    },
    {
        "id": "demo-risk-model",
        "title": "Modernizar es cambiar el modelo de riesgo",
        "raw_idea": (
            "Modernizar no es cambiar de lenguaje; es cambiar el modelo de riesgo"
        ),
        "audience": "CTOs",
        "objective": (
            "reencuadrar la modernización como gestión de riesgo, no como "
            "cambio de tecnología"
        ),
        "thesis": "Modernizar no es cambiar de lenguaje; es cambiar el modelo de riesgo.",
        "evidence": [
            {
                "id": "e1",
                "text": (
                    "La tecnología envejece, pero el riesgo que gestiona una "
                    "plataforma madura es el que realmente decide el timing."
                ),
                "type": "known_facts",
            },
            {
                "id": "e2",
                "text": (
                    "Decidir modernizar por moda tecnológica es un riesgo de "
                    "negocio, no una mejora de stack."
                ),
                "type": "author_opinions",
            },
            {
                "id": "e3",
                "text": "¿Qué riesgo estás comprando cuando decidís no modernizar?",
                "type": "open_questions",
            },
        ],
        "constraints": [
            "Sin prometer ROI numérico.",
            "Enfocar en decisiones de negocio.",
        ],
    },
]


def seed_demo_data(session: Session, *, force: bool = False) -> int:
    """Inserta las ideas demo SOLO si ``ContentProject`` está vacío.

    Idempotente (PST-01 / ADR-008): la segunda llamada no inserta nada.
    Devuelve la cantidad de proyectos insertados.
    """
    existing = session.exec(select(ContentProject.id).limit(1)).first()
    if existing is not None and not force:
        return 0
    for idea in DEMO_IDEAS:
        session.add(
            ContentProject(
                title=idea["title"],
                raw_idea=idea["raw_idea"],
                status="IDEA",
                brief={
                    "thesis": idea["thesis"],
                    "audience": idea["audience"],
                    "objective": idea["objective"],
                    "evidence": idea["evidence"],
                    "constraints": idea["constraints"],
                },
            )
        )
    session.commit()
    return len(DEMO_IDEAS)


def list_demo_ideas(session: Session) -> list[ContentProject]:
    """Ideas demo persistidas (GET /api/ideas/demo las expone; P1-ready)."""
    statement = select(ContentProject).order_by(ContentProject.id)
    return list(session.exec(statement))
