# backend/tests/visual/test_image_provider.py
"""Tests de `visual.image_provider` — Batch F, tarea F.4 [P1].

Cubre el criterio de F.4: con el default (`VISUAL_PROVIDER=svg`) el
provider de imágenes NO se instancia ni se invoca; el contrato visual
observable P0 no cambia. Fallo → fallback a SVG con aviso (nunca
conmutación silenciosa, ADR-006).
"""

from core.config import Settings

from visual.contract import build_visual_contract
from visual.image_provider import (
    IMAGE_PROVIDER_DISABLED_NOTICE,
    fallback_notice,
    image_provider_enabled,
    resolve_image_provider,
)
from visual.validate import is_valid
from visual.svg import render_svg_string

THESIS_DEMO_1 = (
    "Migrar COBOL no es traducir sintaxis; es recuperar conocimiento "
    "operativo antes de tocar código"
)


def make_candidate(angle: str = "problem-story") -> dict:
    return {"angle": angle, "hook": "Hook", "body": "Body", "cta": "CTA"}


def make_contract() -> dict:
    return build_visual_contract(THESIS_DEMO_1, make_candidate())


# ── Default: VISUAL_PROVIDER=svg → desactivado, nunca invocado ──────────────


def test_default_settings_disable_image_provider():
    settings = Settings()
    assert settings.visual_provider == "svg"
    assert image_provider_enabled(settings) is False
    assert resolve_image_provider(settings) is None


def test_image_provider_requires_visual_provider_image():
    settings = Settings(visual_provider="svg", image_api_url="http://image.local")
    assert image_provider_enabled(settings) is False


# ── VISUAL_PROVIDER=image sin credenciales → sigue desactivado (sin red) ────


def test_image_provider_disabled_without_credentials():
    settings = Settings(visual_provider="image")
    assert image_provider_enabled(settings) is False
    assert resolve_image_provider(settings) is None


# ── Con credenciales: el stub P1 no expone provider real (K.4 lo agrega) ────


def test_image_provider_enabled_flag_with_credentials():
    settings = Settings(visual_provider="image", image_api_url="http://image.local")
    assert image_provider_enabled(settings) is True
    # F.4 es el stub de interfaz: sin implementación real no hay provider
    # invocable → resolve devuelve None (la conmutación la decide el workflow
    # con aviso y traza; ADR-006).
    assert resolve_image_provider(settings) is None


# ── Fallback con aviso, nunca conmutación silenciosa ────────────────────────


def test_fallback_notice_is_explicit():
    notice = fallback_notice()
    assert notice.strip()
    assert "SVG" in notice
    assert "desactivado" in notice


def test_disabled_notice_constant_matches_fallback():
    assert fallback_notice() == IMAGE_PROVIDER_DISABLED_NOTICE


# ── P0 observable sin cambios (ADR-006) ─────────────────────────────────────


def test_p0_visual_contract_unchanged_by_image_provider_config():
    settings = Settings()
    assert resolve_image_provider(settings) is None
    contract = make_contract()
    assert is_valid(contract)
    svg = render_svg_string(contract)
    assert svg.strip()
    # El default del visual sigue siendo el SVG determinístico de F.3.
    assert settings.visual_provider == "svg"
