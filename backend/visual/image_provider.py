"""Interfaz `ImageProvider` opcional (F.4, [P1], ADR-006).

Design §7.4: el visual P0 es SIEMPRE la tarjeta SVG determinística. El
provider de imágenes generativas vive detrás de ``VISUAL_PROVIDER=image`` y
está DESACTIVADO por defecto: con ``svg`` no se instancia ni se invoca, y
sin credenciales configuradas tampoco. Fallo → fallback a SVG con aviso y
traza, NUNCA conmutación silenciosa.

La implementación real (P1-04, tarea K.4) se conecta en
``resolve_image_provider``; en F.4 solo existe la interfaz, el asset y la
resolución desactivada, para que el contrato visual observable P0 no cambie.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

__all__ = [
    "ImageAsset",
    "ImageProvider",
    "IMAGE_PROVIDER_DISABLED_NOTICE",
    "image_provider_enabled",
    "resolve_image_provider",
    "fallback_notice",
]

# Aviso para UI/traza cuando se usa SVG en vez de un proveedor de imagen
# (fallback con aviso explícito, nunca silencioso — ADR-006).
IMAGE_PROVIDER_DISABLED_NOTICE = (
    "proveedor de imágenes desactivado; se usa la tarjeta SVG determinística (P0)"
)


@dataclass
class ImageAsset:
    """Asset de imagen producido por un provider (P1).

    ``path`` es local (P0 guarda el SVG); un provider remoto devolvería el
    asset descargado o su referencia, siempre con el ``notice`` de fallback.
    """

    path: str | None
    provider: str
    notice: str


class ImageProvider(Protocol):
    """Contrato del proveedor de imágenes opcional (design §7.4, P1-04)."""

    name: str

    def generate(self, contract: Any) -> ImageAsset:
        """Genera el asset desde el contrato visual; falla → el llamador cae a SVG."""
        ...


def image_provider_enabled(settings: Any) -> bool:
    """¿Está habilitado el provider de imágenes?

    Requiere ``VISUAL_PROVIDER=image`` Y credenciales/endpoint de imagen.
    El default (``svg``) y la ausencia de credenciales lo desactivan
    (sin red y sin keys en P0 — RNF-01).
    """
    if getattr(settings, "visual_provider", "svg") != "image":
        return False
    return bool(
        getattr(settings, "image_api_url", "") or getattr(settings, "image_api_key", "")
    )


def resolve_image_provider(settings: Any) -> ImageProvider | None:
    """Devuelve el provider de imágenes invocable, o ``None`` (desactivado).

    F.4 es el stub de interfaz: sin implementación real (K.4) siempre devuelve
    ``None``, de modo que el workflow (G) usa el SVG determinístico con el
    ``fallback_notice`` — nunca hay conmutación silenciosa (ADR-006).
    """
    if not image_provider_enabled(settings):
        return None
    # P1-04 (K.4): instanciar aquí el ImageProvider real cuando exista.
    return None


def fallback_notice() -> str:
    """Aviso para UI/traza al usar SVG en lugar del provider de imagen."""
    return IMAGE_PROVIDER_DISABLED_NOTICE
