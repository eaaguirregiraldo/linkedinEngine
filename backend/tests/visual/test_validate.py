# backend/tests/visual/test_validate.py
"""Tests de `visual.validate` — Batch F, tarea F.2.

Cubre el criterio de F.2: contrato con elemento sin rationale → rechazo
(apto para `VISUAL_REVISION_REQUIRED`), sin alt_text → rechazo, elemento
prohibido (marcas no autorizadas, texto ilegible, estereotipos retro sin
relación argumental) → rechazo (VIS-03/04/05/07).
"""

import pytest

from visual.contract import build_visual_contract
from visual.validate import is_valid, validate_visual_contract

THESIS_DEMO_1 = (
    "Migrar COBOL no es traducir sintaxis; es recuperar conocimiento "
    "operativo antes de tocar código"
)


def make_candidate(angle: str = "problem-story") -> dict:
    return {"angle": angle, "hook": "Hook", "body": "Body", "cta": "CTA"}


def make_contract() -> dict:
    """Contrato válido generado por F.1 (punto de partida de las mutaciones)."""
    return build_visual_contract(THESIS_DEMO_1, make_candidate())


def _errors(contract: dict) -> list[str]:
    return validate_visual_contract(contract).errors


# ── Contrato válido ─────────────────────────────────────────────────────────


def test_valid_contract_passes():
    result = validate_visual_contract(make_contract())
    assert result.valid is True
    assert result.errors == []


def test_is_valid_convenience():
    assert is_valid(make_contract()) is True
    broken = make_contract()
    broken["elements"][0]["rationale"] = ""
    assert is_valid(broken) is False


# ── VIS-03: elemento sin rationale o con rationale en blanco → rechazo ──────


def test_element_without_rationale_is_rejected():
    contract = make_contract()
    contract["elements"][0]["rationale"] = ""
    errors = _errors(contract)
    assert errors, "debe rechazar el contrato"
    assert any("rationale" in error for error in errors)


def test_element_with_blank_rationale_is_rejected():
    contract = make_contract()
    contract["elements"][1]["rationale"] = "   "
    assert not is_valid(contract)


def test_element_without_description_is_rejected():
    contract = make_contract()
    contract["elements"][0]["description"] = ""
    assert not is_valid(contract)


# ── VIS-04: alt_text obligatorio y específico → rechazo si falta/genérico ───


def test_missing_alt_text_is_rejected():
    contract = make_contract()
    contract["alt_text"] = ""
    errors = _errors(contract)
    assert errors
    assert any("alt_text" in error for error in errors)


def test_blank_alt_text_is_rejected():
    contract = make_contract()
    contract["alt_text"] = "   "
    assert not is_valid(contract)


@pytest.mark.parametrize(
    "generic_alt",
    ["imagen", "visual", "tarjeta", "gráfico", "svg", "ilustración", "foto"],
)
def test_generic_alt_text_is_rejected(generic_alt):
    contract = make_contract()
    contract["alt_text"] = generic_alt
    assert not is_valid(contract), f"alt_text genérico no rechazado: {generic_alt!r}"


def test_unrelated_alt_text_is_rejected():
    contract = make_contract()
    contract["alt_text"] = "colores y formas aleatorias"
    assert not is_valid(contract)


# ── VIS-05/07: elementos prohibidos → rechazo ───────────────────────────────


def test_brand_mark_is_rejected():
    contract = make_contract()
    contract["elements"][0]["description"] = "logo de una empresa ficticia"
    errors = _errors(contract)
    assert errors
    assert any("marca" in error for error in errors)


def test_illegible_text_is_rejected():
    contract = make_contract()
    contract["elements"][0]["kind"] = "text"
    contract["elements"][0]["description"] = "x" * 150
    errors = _errors(contract)
    assert errors
    assert any("ilegible" in error for error in errors)


def test_retro_stereotype_without_argumental_relation_is_rejected():
    contract = make_contract()
    contract["elements"][0]["kind"] = "metaphor"
    contract["elements"][0]["description"] = "cinta magnética decorativa"
    contract["elements"][0]["rationale"] = "decoración"
    errors = _errors(contract)
    assert errors
    assert any("estereotipo" in error for error in errors)


# ── Sin elementos → rechazo ─────────────────────────────────────────────────


def test_contract_without_elements_is_rejected():
    contract = make_contract()
    contract["elements"] = []
    assert not is_valid(contract)


# ── Forma de entrada: dict o pydantic VisualContract (VIS-03 shape-agnostic) ─


def test_validate_accepts_pydantic_visual_contract():
    from api.schemas import VisualContract, VisualElement

    contract = make_contract()
    model = VisualContract(
        thesis=contract["thesis"],
        concept=contract["concept"],
        elements=[VisualElement(**element) for element in contract["elements"]],
        alt_text=contract["alt_text"],
        status=contract["status"],
    )
    result = validate_visual_contract(model)
    assert result.valid is True
    assert result.errors == []
