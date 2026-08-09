"""Meta endpoints (G.4, design §5.4): ``GET /api/health``.

Responde el estado del servicio con el proveedor activo (demo por default,
HARN-09): el frontend usa el provider para mostrar los banners honestos
(RUN-03/06) — sin adivinar el proveedor desde el cliente.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from api import schemas
from api.routers import ERROR_RESPONSES
from api.dependencies import get_settings
from core.config import Settings

router = APIRouter(prefix="/api", tags=["meta"], responses=ERROR_RESPONSES)


@router.get("/health", response_model=schemas.HealthOut)
def health(settings: Settings = Depends(get_settings)) -> schemas.HealthOut:
    """Estado del servicio y proveedor GenAI activo (API-01)."""
    return schemas.HealthOut(status="ok", provider=settings.genai_provider)
