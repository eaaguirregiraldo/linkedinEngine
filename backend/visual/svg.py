"""Plantilla SVG editorial determinística (F.3, VIS-02).

``render_svg`` escribe la tarjeta en ``data/visuals/{visual_id}.svg`` usando
UNA única plantilla parametrizada 1200×630: tesis corta, metáfora visual
(capas estructurales) y elementos de dominio. La salida es una función pura
del contrato (sin timestamps ni random): mismo contrato → mismo SVG byte a
byte (VIS-02). Accesibilidad: el SVG incluye ``<title>`` (concepto) y
``<desc>`` (alt_text) y texto legible en imagen.

Sin LLM, sin red, sin dependencias del contrato pydantic (alcance F = B+A1).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from visual.contract import get_field

__all__ = [
    "SVG_WIDTH",
    "SVG_HEIGHT",
    "FONT_STACK",
    "render_svg",
    "render_svg_string",
]

SVG_WIDTH = 1200
SVG_HEIGHT = 630
FONT_STACK = "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"

# Paleta fija (determinística): la plantilla es única, sin color por ángulo.
_BG = "#0B1220"
_PANEL = "#1E293B"
_ACCENT = "#F59E0B"
_TEXT = "#F8FAFC"
_MUTED = "#94A3B8"

_MAX_THESIS_CHARS = 96
_THESIS_LINE_CHARS = 34
_MAX_THESIS_LINES = 3
_MAX_LABEL_CHARS = 32
_MAX_CONCEPT_CHARS = 64

# Kinds que se dibujan como capas/figuras (el resto, p. ej. "text", alimenta
# el bloque de tesis). Se dibujan como máximo 4 para mantener legibilidad.
_SHAPE_KINDS = frozenset({"metaphor", "structure", "domain"})
_MAX_SHAPES = 4

_WHITESPACE_RE = re.compile(r"\s+")


def _short(text: str, max_chars: int) -> str:
    """Colapsa espacios y trunca con elipsis si hace falta (legible en imagen)."""
    collapsed = _WHITESPACE_RE.sub(" ", text or "").strip()
    if len(collapsed) <= max_chars:
        return collapsed
    return collapsed[:max_chars].rstrip() + "…"


def _wrap(text: str, width: int) -> list[str]:
    """Word-wrap determinístico por cantidad de caracteres por línea."""
    words = (text or "").split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _shape_elements(contract: Any) -> list[dict[str, Any]]:
    elements = get_field(contract, "elements") or []
    return [
        element
        for element in elements
        if (get_field(element, "kind") or "").strip().lower() in _SHAPE_KINDS
    ][:_MAX_SHAPES]


def render_svg_string(contract: Any) -> str:
    """Renderiza el SVG como string — función pura del contrato (VIS-02)."""
    thesis = _short(get_field(contract, "thesis") or "", _MAX_THESIS_CHARS)
    concept_full = (get_field(contract, "concept") or "").strip()
    concept = _short(concept_full, _MAX_CONCEPT_CHARS)
    alt_text = get_field(contract, "alt_text") or ""
    status = get_field(contract, "status") or "VISUAL_DRAFT"

    thesis_lines = _wrap(thesis, _THESIS_LINE_CHARS)[:_MAX_THESIS_LINES]
    if len(_wrap(thesis, _THESIS_LINE_CHARS)) > _MAX_THESIS_LINES:
        thesis_lines[-1] = thesis_lines[-1].rstrip() + "…"

    shapes = _shape_elements(contract)
    shape_rects: list[str] = []
    shape_y = 176
    for index, element in enumerate(shapes):
        label = _short(get_field(element, "description") or "", _MAX_LABEL_CHARS)
        fill = _ACCENT if index == 0 else _PANEL
        label_fill = _BG if index == 0 else _TEXT
        shape_rects.append(
            f'<rect x="64" y="{shape_y}" width="520" height="62" rx="12" fill="{fill}"/>'
        )
        shape_rects.append(
            '<text x="84" y="{}" font-family="{}" font-size="18" fill="{}">'
            "{}</text>".format(
                shape_y + 39, FONT_STACK, label_fill, escape(label)
            )
        )
        shape_y += 62 + 18

    thesis_lines_svg = "\n".join(
        '<text x="660" y="{}" font-family="{}" font-size="26" font-weight="600" '
        'fill="{}">{}</text>'.format(214 + index * 38, FONT_STACK, _TEXT, escape(line))
        for index, line in enumerate(thesis_lines)
    )

    footer_x = 64
    footer_right_x = SVG_WIDTH - 64

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" '
        f'height="{SVG_HEIGHT}" viewBox="0 0 {SVG_WIDTH} {SVG_HEIGHT}" '
        'role="img" aria-labelledby="vis-title vis-desc">\n'
        f"  <title id=\"vis-title\">{escape(concept_full)}</title>\n"
        f"  <desc id=\"vis-desc\">{escape(alt_text)}</desc>\n"
        f'  <rect x="0" y="0" width="{SVG_WIDTH}" height="{SVG_HEIGHT}" fill="{_BG}"/>\n'
        f'  <rect x="0" y="0" width="{SVG_WIDTH}" height="8" fill="{_ACCENT}"/>\n'
        '<text x="64" y="64" font-family="{}" font-size="15" letter-spacing="2" '
        'fill="{}">MOTOR EDITORIAL · VISUAL SEMÁNTICO</text>\n'.format(
            FONT_STACK, _MUTED
        )
        + '<text x="64" y="98" font-family="{}" font-size="20" font-weight="600" '
        'fill="{}">{}</text>\n'.format(FONT_STACK, _TEXT, escape(concept))
        + "\n".join(shape_rects)
        + (("\n" + thesis_lines_svg) if thesis_lines_svg else "")
        + (
            '\n<text x="{}" y="600" font-family="{}" font-size="14" fill="{}">'
            "estado: {}</text>\n".format(footer_x, FONT_STACK, _MUTED, escape(status))
        )
        + '<text x="{}" y="600" font-family="{}" font-size="14" text-anchor="end" '
        'fill="{}">tarjeta determinística · generada localmente</text>\n'.format(
            footer_right_x, FONT_STACK, _MUTED
        )
        + "</svg>\n"
    )


def render_svg(
    contract: Any, visual_id: int, output_dir: str | Path = "data/visuals"
) -> Path:
    """Escribe ``{visual_id}.svg`` bajo ``output_dir`` y devuelve su path.

    El path local queda disponible para el workflow (G), que lo persiste en
    ``VisualAsset.svg_path`` (VIS-02: "el asset se guarda localmente").
    """
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    path = output / f"{visual_id}.svg"
    path.write_text(render_svg_string(contract), encoding="utf-8")
    return path
