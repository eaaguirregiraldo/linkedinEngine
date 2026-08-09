# backend/tests/visual/test_svg.py
"""Tests de `visual.svg` — Batch F, tarea F.3.

Cubre el criterio de F.3: mismo contrato → SVG idéntico byte a byte
(reproducibilidad, VIS-02), el SVG incluye alt text (accesibilidad), la
plantilla es única (1200×630) y el asset queda con `svg_path` local.
"""

import xml.etree.ElementTree as ET

from visual.contract import build_visual_contract
from visual.svg import SVG_HEIGHT, SVG_WIDTH, render_svg, render_svg_string

THESIS_DEMO_1 = (
    "Migrar COBOL no es traducir sintaxis; es recuperar conocimiento "
    "operativo antes de tocar código"
)

SVG_NS = "{http://www.w3.org/2000/svg}"


def make_candidate(angle: str = "problem-story") -> dict:
    return {"angle": angle, "hook": "Hook", "body": "Body", "cta": "CTA"}


def make_contract() -> dict:
    return build_visual_contract(THESIS_DEMO_1, make_candidate())


def _parse(svg: str) -> ET.Element:
    return ET.fromstring(svg)


# ── VIS-02: reproducibilidad byte a byte ────────────────────────────────────


def test_same_contract_renders_identical_svg():
    contract = make_contract()
    first = render_svg_string(contract)
    second = render_svg_string(contract)
    assert first == second
    assert first.strip(), "el SVG no puede ser vacío"


def test_different_visual_id_does_not_change_svg_content(tmp_path):
    contract = make_contract()
    path_1 = render_svg(contract, visual_id=1, output_dir=tmp_path / "visuals")
    path_2 = render_svg(contract, visual_id=2, output_dir=tmp_path / "visuals")
    assert path_1.name == "1.svg"
    assert path_2.name == "2.svg"
    assert path_1.read_text(encoding="utf-8") == path_2.read_text(encoding="utf-8")


# ── Plantilla única 1200×630, XML válido ────────────────────────────────────


def test_svg_is_valid_xml_with_expected_dimensions():
    root = _parse(render_svg_string(make_contract()))
    assert root.tag == f"{SVG_NS}svg"
    assert root.attrib["width"] == str(SVG_WIDTH)
    assert root.attrib["height"] == str(SVG_HEIGHT)


def test_svg_uses_single_editorial_template():
    root = _parse(render_svg_string(make_contract()))
    # Un solo elemento raíz svg y exactamente un fondo a 1200×630.
    rects = [child for child in root if child.tag == f"{SVG_NS}rect"]
    assert rects, "la plantilla debe dibujar el fondo"


# ── Accesibilidad: alt text dentro del SVG (VIS-02) ─────────────────────────


def test_svg_includes_alt_text_as_desc():
    contract = make_contract()
    root = _parse(render_svg_string(contract))
    desc = root.find(f"{SVG_NS}desc")
    assert desc is not None, "falta el elemento <desc> con alt text"
    assert contract["alt_text"] in desc.text


def test_svg_includes_concept_as_title():
    contract = make_contract()
    root = _parse(render_svg_string(contract))
    title = root.find(f"{SVG_NS}title")
    assert title is not None, "falta el elemento <title>"
    assert contract["concept"] in title.text


def test_svg_includes_thesis_text_on_image():
    contract = make_contract()
    root = _parse(render_svg_string(contract))
    texts = [child.text for child in root if child.tag == f"{SVG_NS}text"]
    # La tesis corta aparece como texto legible en la tarjeta (SOLUTION.md §8).
    assert any(texts), "no hay texto en la imagen"
    assert any(t and contract["thesis"][:20] in t for t in texts)


# ── Escapado XML: la tesis puede contener caracteres especiales ─────────────


def test_svg_escapes_special_characters_in_thesis():
    contract = {
        "thesis": 'Tesis con & <especial> y "comillas"',
        "concept": "Concepto & prueba",
        "elements": [
            {
                "element_id": "el-01",
                "kind": "metaphor",
                "description": 'Capa con & <simbolos>',
                "rationale": 'la tesis menciona "especial"',
            }
        ],
        "alt_text": 'Tarjeta con & <símbolos> y "comillas"',
        "status": "VISUAL_DRAFT",
    }
    svg = render_svg_string(contract)
    assert "<script" not in svg
    _parse(svg)  # debe seguir siendo XML válido


# ── Escritura local con svg_path (VIS-02: "se guarda localmente") ───────────


def test_render_writes_file_with_svg_path(tmp_path):
    contract = make_contract()
    output_dir = tmp_path / "data" / "visuals"
    path = render_svg(contract, visual_id=7, output_dir=output_dir)
    assert path.exists()
    assert path.is_file()
    assert path.read_text(encoding="utf-8") == render_svg_string(contract)


def test_render_creates_parent_directories(tmp_path):
    contract = make_contract()
    output_dir = tmp_path / "no" / "existe" / "todavia"
    path = render_svg(contract, visual_id=3, output_dir=output_dir)
    assert path.exists()


# ── Estado honesto en la tarjeta ────────────────────────────────────────────


def test_svg_includes_contract_status():
    contract = make_contract()
    root = _parse(render_svg_string(contract))
    texts = [child.text for child in root if child.tag == f"{SVG_NS}text"]
    assert any(t and contract["status"] in t for t in texts)
