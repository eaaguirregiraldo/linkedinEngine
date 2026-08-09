"""FastAPI app (G.5, design §11.2/§13, ADR-008).

- **Lifespan**: ``create_all`` idempotente + seed demo (ADR-008) — la DB se
  crea al arrancar; el seed solo inserta si ``ContentProject`` está vacío.
- **CORS**: allowlist ``CORS_ORIGINS`` (separada por comas) con
  ``allow_credentials=False`` (API-03, design §13.3): sin cookies ni
  credenciales en el MVP local.
- **Docs**: ``/docs`` y ``/redoc`` SOLO en ``APP_ENV=dev`` (design §13);
  ``/openapi.json`` queda disponible (el FE genera ``schema.d.ts`` desde él,
  ADR-003/§5.2).
- **Errores**: handlers globales de ``api.errors`` (design §12).
- **Bind local**: ``uvicorn.run`` en ``127.0.0.1`` (RUN-01, design §13.3).
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

from api import errors
from api.dependencies import get_settings
from api.routers import candidates, meta, projects, runs, visuals
from core.config import Settings
from db.engine import create_all_tables, create_db_engine
from db.seed import seed_demo_data


def create_app(settings: Settings | None = None) -> FastAPI:
    """Construye la app FastAPI (factory: los tests la usan con settings propios).

    El lifespan corre ``create_all`` + seed sobre ``DATABASE_PATH``; la
    dependencia ``get_session`` abre sus sesiones sobre el mismo fichero
    (misma ruta de settings), así la DB seedeada es la que sirven los
    endpoints.
    """
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        del app  # el engine del lifespan es transitorio: solo create_all + seed
        engine = create_db_engine(settings.database_path)
        create_all_tables(engine)
        with Session(engine) as session:
            seed_demo_data(session)
        yield

    app = FastAPI(
        title="LinkedIn Content Engine",
        version="0.1.0",
        description=(
            "Motor editorial asistido por GenAI para LinkedIn (MVP local, demo)."
        ),
        lifespan=lifespan,
        docs_url="/docs" if settings.app_env == "dev" else None,
        redoc_url="/redoc" if settings.app_env == "dev" else None,
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    errors.register_exception_handlers(app)
    app.include_router(meta.router)
    app.include_router(projects.router)
    app.include_router(runs.router)
    app.include_router(candidates.router)
    app.include_router(visuals.router)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="127.0.0.1", port=get_settings().api_port)
