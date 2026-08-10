# Apply Progress — `linkedin-content-engine` (Waves 1-6 consolidadas)

> Fase: `sdd-apply` | Cambio: `linkedin-content-engine` | Fecha: 2026-08-09 | Modo: **hybrid** (openspec + Engram)
> Alcance: **Wave 1** — Batch A1 (scaffold), B (dominio puro), C (contratos pydantic), D (persistencia). **Wave 2** — Batch E (GenAI harness/DemoProvider), F (visual SVG determinístico). **Wave 3** — Batch G (API FastAPI + workflow + contrato OpenAPI vivo). **Wave 4** — H1 (base FE) + H2 (wizard 10 pasos). **Wave 5** — I (suite contract anti-drift) ✅ COMPLETA. **Wave 6** — J (cierre P0) ✅ J.1-J.5 verificadas; J.6 pendiente por no-commit.
> Espejo de lote: Engram topics `sdd/linkedin-content-engine/apply-progress/{a1,b,c,d,e,f}` → consolidado en este archivo + Engram topic `sdd/linkedin-content-engine/apply-progress`.
> ⚠️ Nota de reconciliación: el lote E persistió su reporte con el topic CONSOLIDADO (`sdd/linkedin-content-engine/apply-progress`, skill sdd-apply Step 5) en lugar del topic de lote `.../apply-progress/e` (instrucción del orquestador), pisando el consolidado de Wave 1 en Engram. Restaurado en esta consolidación; el reporte E vive también en `.../apply-progress/e` (Engram) y en #901/#900/#897 (session summaries).

---

## 1. Estado consolidado

| Batch | Tareas | Estado | Evidencia (ejecutada en esta consolidación, sin build) |
|---|---|---|---|
| A1 — Scaffold workspace | 8/8 implementadas, **6/8 criterio completo** | ⚠️ PARCIAL (2 criterios pendientes) | Ver §3 |
| B — Dominio puro (FSM, score, blockers, validación, clichés, fixtures) | 7/7 | ✅ COMPLETO | `pytest -q backend/tests/domain backend/tests/fixtures` → **49 passed** |
| C — Contratos canónicos pydantic | 3/3 | ✅ COMPLETO | `pytest -q backend/tests/contracts` → **43 passed** |
| D — Persistencia SQLModel/SQLite + traza + seed | 5/5 | ✅ COMPLETO | `pytest -q backend/tests/db` → **21 passed** |
| E — GenAI harness: prompts versionados, DemoProvider, retry/repair, traza | 6/6 | ✅ COMPLETO | `pytest -q backend/tests/harness` → **58 passed** |
| F — Visual: contrato SVG determinístico + ImageProvider opcional | 5/5 | ✅ COMPLETO | `pytest -q backend/tests/visual` → **54 passed** |
| G — API FastAPI: errors, dependencies, workflow, routers, main, contrato OpenAPI vivo | 7/7 | ✅ COMPLETO | `pytest -q backend/tests/api` → **54 passed** (G.1/G.2 errors+deps 19 + G.3 workflow 16 + G.4 endpoints 10 + G.5 main 9) |
| H1 — Base FE: client tipado, useAsync, primitivas UI, estilos | 5/5 | ✅ COMPLETO | `npm --prefix frontend run test` → **24 passed**; `tsc --noEmit` limpio |
| H2 — Wizard 10 pasos + App | 12/12 | ✅ COMPLETO | Vitest **34 passed**; `tsc --noEmit` limpio; schema sin drift; smoke Vite 200/200 |
| I — Contrato FE/BE anti-drift | 4/4 | ✅ COMPLETO | `npm run test:contract` → **4 passed**; drift byte a byte, round-trip real, cobertura y CORS |
| **Backend completo (Wave 1 + Wave 2 + Wave 3)** | — | ✅ | `pytest -q backend/tests` → **279 passed** (225 Wave 1+2 + 54 api G) |
| Ruff | — | ✅ | `ruff check backend/` → **All checks passed** (ruff 0.8.4, backend/.venv) |
| J — Cierre P0 | 5/6 criterios verificables | ✅ PARCIAL POR RESTRICCIÓN | README/decisiones/roadmap auditados; smoke normal e inválido; pytest/Vitest/contrato/tsc/schema/Ruff verdes; J.6 requiere commit y queda sin marcar |

**Checkboxes en `tasks.md`:** 65 marcadas `[x]` (A1.3–A1.8, B.1–B.7, C.1–C.3, D.1–D.5, E.1–E.6, F.1–F.5, G.1–G.7, H1.1–H1.5, H2.1–H2.12, I.1–I.4, J.1–J.5). A1.1/A1.2, J.6 y K permanecen sin marcar.

---

## 2. Detalle por lote (reportes Engram: A1 #887, B #893, C #886, D #890, E #896/`apply-progress/e`, F #898/`apply-progress/f`)

### Batch A1 — Scaffold (Engram #887)
- **A1.1** `git init` + `.gitignore` **HECHOS** (verificado con `git check-ignore`: `data/`, `node_modules/`, `.env`, `.venv/`, `__pycache__/`, `*.db` ignorados; `SOLUTION.md`, `openspec/`, `.env.example` NO ignorados).
  ⚠️ **Criterio incompleto: NO existe commit inicial** (`git log` → "branch 'master' does not have any commits yet"; todo el árbol está untracked). Bloqueado por la regla del orquestador (no commit). **Pendiente para el cierre de Wave 1 / decisión del orquestador.**
- **A1.2** `package.json` raíz con 9 scripts (`dev`, `dev:api`, `dev:web`, `schema:generate`, `schema:check`, `test`, `test:contract`, `demo` + `test` lifecycle) + `concurrently@^9.1.0`. `npm run` lista los scripts; `npm install` resuelve.
  ⚠️ **Criterio incompleto: `npm run dev` NO levanta ambos procesos.** Verificado en vivo: vite sirve **HTTP 200 en :5173**, pero uvicorn falla con `Could not import module "api.main"` → **puerto 8000 sin respuesta (000)**. El stub mínimo exigido por el criterio no existe: `backend/api/main.py` es del Batch G (Wave 3). **Pendiente hasta G.5.**
- **A1.3** `backend/requirements.txt` (pines: fastapi==0.115.6, uvicorn==0.34.0, sqlmodel==0.0.22, pydantic==2.9.2, pydantic-settings==2.6.1, python-dotenv==1.0.1, httpx==0.28.1), `requirements-dev.txt` (pytest==8.3.4, ruff==0.8.4), `pyproject.toml` (testpaths, ruff line-length 100), `backend/package.json` (wrappers `dev`/`test`). Instalación limpia en `backend/.venv` (Python 3.12.7). `npm --prefix backend run test` ejecuta pytest → **225 passed** (con `backend/.venv/bin` en PATH).
  ⚠️ **Gotcha documentado (#887):** sin venv activado, npm resuelve el pytest del sistema (anaconda 9.0.3) que NO tiene deps del proyecto (falla de colección en tests/db). No es defecto del wrapper: es activación de entorno estándar de Python.
- **A1.4** `backend/core/config.py` — `Settings` pydantic-settings con TODAS las vars de design §11.3 y defaults correctos. Verificado en esta consolidación: `APP_ENV=dev`, `API_PORT=8000`, `GENAI_PROVIDER=demo` sin env, `cors_origins_list` parsea la allowlist. `.env` de la raíz se carga desde CWD `backend/` (`_discover_env_file` sube por padres).
  📝 Nota: el criterio pide "test unit" y **no hay test persistente** para core/config (verificación funcional del lote). Comportamiento demostrado; recomendado agregar test en una wave posterior.
- **A1.5** `backend/core/trace.py` — `build_trace_event(type, **data)` → `{ts UTC ISO, type, ...}`; `redact_secrets` recursivo redacta `api_key`/`authorization`/`token`/`secret`/`password`/`credential` → `[REDACTED]`, sin tocar `author` (protege `author_opinions`).
  📝 Nota: misma observación que A1.4 — sin test unit persistente.
- **A1.6** `backend/tests/conftest.py` — inserta `backend/` al `sys.path` (path absoluto), fixtures `db_file`/`sqlite_db_url`. **Criterio demostrado:** `pytest -q backend/tests` descubre y corre las subcarpetas de B/C/D/E/F sin conflictos → 225 passed.
- **A1.7** Scaffold `frontend/` — `package.json` (react 18.3.1, typescript ~5.6.3, vite ^5.4.11, vitest, @testing-library/react, openapi-typescript), `tsconfig.json` strict, `vite.config.ts` (port 5173, proxy `/api → :8000`, bloque `test` delegado a H1.4), `index.html`. `npm install` resuelto; vite verificado sirviendo 200 en :5173 durante el smoke test de `npm run dev`.
- **A1.8** `.env.example` — 14 vars de design §11.3 documentadas, `OPENAI_API_KEY=` y `IMAGE_API_KEY=` vacías. Verificado: sin credenciales reales.

### Batch B — Dominio puro (Engram #893)
- **B.1** `backend/domain/fsm.py` — FSM pura de 25 filas con guards y estados reales inalcanzables (`PUBLISHED_REAL`/`PUBLISHING_REAL` con guard muerto `real_publish_enabled()==False`).
- **B.2** `backend/domain/score.py` — `DIMENSION_WEIGHTS` (suma 1.0), `dimension_100`, `clamp`, penalizaciones (riesgo 25, genéricos 15), `score_final`.
- **B.3** `backend/domain/blockers.py` — activación de blockers + `decide()` con umbrales versionados (72/4/60), reproducible.
- **B.4** `backend/domain/validation.py` — normalización, duplicados, paráfrasis, claims sin soporte, prohibidos, instrucciones maliciosas tratadas como DATO.
- **B.5** `backend/domain/cliches_v1.txt` — catálogo versionado con carga estable (versión/hash).
- **B.6** `backend/tests/fixtures/regression_{solid,generic,invented_claim,invalid_json}.json` — 4 fixtures versionados con expectativas.
- **B.7** Cierre: **49 passed** en domain+fixtures.
- ⚠️ **Desviación documentada (#893):** tasks.md exige `CANDIDATE_EDITED` desde GENERATED/RECOMMENDED/REVISION_REQUIRED/VISUAL_DRAFT/VISUAL_READY y omite EVALUATION_PARTIAL; design.md §4.2 incluía EVALUATION_PARTIAL y omitía GENERATED. Se siguió el criterio verificable de tasks.md (B.1). Reconciliar en verify si aplica.

### Batch C — Contratos canónicos (Engram #886)
- **C.1** `backend/api/schemas.py` — contrato completo design §5.5 (BriefIn, CandidateOut, GenerationOutput con model_validator 3-ángulos-únicos, EvaluationOutput/DimensionScore 0..5+quote+rubric_rule, Penalties, DecisionOut, VisualContract/VisualElement, ReceiptOut `mode="simulated"` + `remote_id=None` fijo + notice, ErrorBody, DemoIdeaOut, ProjectOut/RunOut/HealthOut, etc.).
- **C.2** `backend/ai/contracts.py` — reexporta los MISMOS objetos (identidad verificada por test: `contracts.X is schemas.X`).
- **C.3** Cierre: **43 passed** (36 schemas + 7 identidad).
- ⚠️ **Desviación documentada (#886):** `min_length=1` de pydantic NO rechaza strings de solo espacios; la semántica (blancos) queda en la capa de validación de dominio (B.4/F.2), con validators strip SOLO donde specs lo exigen (`thesis`, `raw_idea`). Split estructura/semántica según design.

### Batch D — Persistencia (Engram #890)
- **D.1** `backend/db/engine.py` — `create_db_engine` (crea dir padre, PRAGMA foreign_keys=ON), `create_all_tables` idempotente (ADR-008), `session_factory`.
- **D.2** `backend/db/models.py` — 5 tablas SQLModel §9.1 + `VOICE_V0` provisional; invariantes: `UniqueConstraint(run_id, angle)`, `remote_id=None` simulado (garantía en repo, NO pydantic validator — SQLModel 0.0.22 table=True no ejecuta validators; verificado empíricamente, #890), sin columnas de credenciales (PST-02 testeado).
- **D.3** `backend/db/repos.py` — repos finos por agregado; traza append-only (TRC-03, sin API de mutación); `bump_candidate_version` (content_version++ + evaluación/selection invalidada).
- **D.4** `backend/db/seed.py` — 3 ideas demo §9.3 con brief prefijado + voz v0; idempotente.
- **D.5** Cierre: **21 passed**.
- ⚠️ **Desviación documentada (#890):** con `Session.exec` hay que usar `from sqlmodel import select` (`sqlalchemy.select` devuelve Row); timestamps UTC naive (SQLite sin tz).

### Batch E — GenAI harness (Engram `apply-progress/e`, #896/#901)
- **E.1** `backend/ai/prompts/linkedin-candidate-generator@1.0.0.md` + `backend/ai/prompts/editorial-evaluator@1.0.0.md` — propósito, contexto permitido, 7 reglas de voz v0 PROVISIONAL (VOI-02) literales, delimitadores `<BRIEF_DATOS>..</BRIEF_DATOS>` (el brief viaja como DATOS — HARN-06 anti-inyección), formato JSON de salida (contrato), ejemplo mínimo, prohibiciones VOI-03 (clichés del catálogo como prohibidos, no como prosa).
- **E.2** `backend/ai/prompts/manifest.json` — `{file, version, schema_version, sha256}` por capacidad; `resolve_prompt(id)` calcula el hash al cargar y valida contra el manifest (editar sin subir versión → `ManifestError`). **Hashes verificados en esta consolidación:** generator `sha256:94440177...823d`, evaluator `sha256:90edc7d3...e93202` (coinciden con `shasum` de los `.md`).
- **E.3** `backend/ai/providers.py` — `GenAIProvider` (Protocol runtime_checkable: `name`, `generate_candidates`, `evaluate_candidates`) + `ProviderError` con `code ∈ TRANSIENT|INVALID_OUTPUT|UNAVAILABLE`. Retry/repair NO viven en el provider (ADR-005).
- **E.4** `backend/ai/demo_provider.py` — `DemoProvider` DETERMINÍSTICO derivado del brief (tesis/audiencia/evidencia reales; claims mapean evidence ids), `name="DEMO_PROVIDER"`, `model=None`; `DEMO_FORCE_INVALID=1` → JSON inválido (camino repair→`GENERATION_FAILED`). Reusa `penalizacion_riesgo`/`penalizacion_genericidad`/`activate_blockers`/catálogo de clichés (HARN-03: mismos guards). **Bugs corregidos en el lote:** (1) `base_score` recibía tuplas y el dominio espera dict → TypeError en `run_evaluation`; (2) auto-similitud en `penalizacion_genericidad` (excluye el propio body).
- **E.5** `backend/ai/harness.py` — `run_generation` (resolver prompt+hash → traza `prompt_resolved`; loop 1..3 con backoff 0.5s/1.5s ante `TRANSIENT` → `retry_scheduled`; validación pydantic → `output_validated`; `repair_once` ÚNICA con el error del schema → `repair_ok`/`repair_failed` mutuamente excluyentes; agotado → `RunResult.failed("INVALID_OUTPUT"|"PROVIDER_TRANSIENT_ERROR")` → `generation_failed`); `run_evaluation` (anonimiza + orden aleatorio con seed fija en demo, EVAL-07; degrada a solo-determinístico con `EVALUATION_PARTIAL`/error_code `SEMANTIC_EVALUATION_UNAVAILABLE` si el evaluador semántico falla, HARN-08, conservando `provider_code` en traza — design §12 503; sin fabricar score); `raw_output` SOLO si `TRACE_STORE_RAW_OUTPUT=true` y redactado (parse→`redact_secrets`→re-dump, HARN-07); `redact_secrets` siempre.
- **E.6** Cierre: **58 passed** (12 demo_provider + 24 harness + 22 trace). Suite backend completa **225 passed**; ruff limpio.
- 🔲 (resuelto en esta consolidación) El reporte E fue guardado en el topic consolidado en lugar de `apply-progress/e` — restaurado (ver nota de cabecera).

### Batch F — Visual (Engram #898 / `apply-progress/f`)
- **F.1** `backend/visual/contract.py` — `build_visual_contract(thesis, candidate)` SIN LLM: `CONTRACT_VERSION="1.0.0"`, `CONCEPT_RULES_V1` (3 reglas keyword→concepto: conocimiento operativo/tácito → dos capas; mainframe/décadas/reglas → caja de reglas; modernizar/modelo de riesgo → lenguaje vs riesgo), `ANGLE_META_V1` (3 ángulos); `elements[]` con rationale citando frases LITERALES de la tesis; `alt_text` específico; status `VISUAL_DRAFT` (VIS-01/03).
- **F.2** `backend/visual/validate.py` — `validate_visual_contract` → `ValidationResult{valid, errors}`; shape-agnostic (dict o `VisualContract` pydantic); rechaza rationale/description vacíos, `elements=[]`, alt_text vacío/genérico ("imagen", "visual", "tarjeta", "gráfico", "svg", "ilustración", "foto") o no relacionado, marcas ("logo", "®", "™"), texto >140 chars, estereotipos retro sin relación argumental (VIS-03/04/05/07).
- **F.3** `backend/visual/svg.py` — `render_svg` UNA plantilla editorial parametrizada 1200×630: `<title>`=concepto COMPLETO, `<desc>`=alt_text, `<text>` tesis corta (34 chars/línea, máx 3) + status, escape XML (`saxutils.escape`); `render_svg(contract, visual_id, output_dir)` escribe `data/visuals/{id}.svg` con parents. Determinismo byte a byte (mismo contrato → mismo SVG; VIS-02).
- **F.4** `backend/visual/image_provider.py` — interfaz `ImageProvider.generate(contract) -> ImageAsset` detrás de `VISUAL_PROVIDER=image`, **desactivada por defecto** (`image_provider_enabled` exige `visual_provider=="image"` Y credenciales; `resolve_image_provider` → None, stub P1/K.4); `fallback_notice()` = "proveedor de imágenes desactivado; se usa la tarjeta SVG determinística (P0)" — fallback con aviso, nunca conmutación silenciosa (ADR-006).
- **F.5** Cierre: **54 passed** (test_contract, test_validate, test_svg, test_image_provider). Smoke end-to-end: tesis demo → contrato válido (2 capas) → SVG 1200×630 determinístico → provider desactivado.
- 📝 Nota (post-consolidación): **F.5 no requirió código nuevo** — `save_visual`/`update_visual_status`/`VisualAsset.svg_path` ya existían del lote D (`apply-progress/e` lo confirmó); F.5 es solo el criterio de cierre (suite visual en verde).

### Batch G — API FastAPI (Engram `apply-progress/g`, #910)
- **G.1** `backend/api/errors.py` — envelope único `ErrorBody{error:{code,message,details}}` + handlers: `VALIDATION_ERROR` 400, `NOT_FOUND` 404, `STATE_TRANSITION_REJECTED` 409, `CONTRACT_INVALID` 422, `PROVIDER_UNAVAILABLE` 502, `SEMANTIC_EVALUATION_UNAVAILABLE` 503 (semana anterior, testeado).
- **G.2** `backend/api/dependencies.py` — `get_session` (engine cacheado por módulo, SQLite `DATABASE_PATH`), `get_settings`, `get_provider` (demo default; openai SOLO con `GENAI_PROVIDER=openai` + key; sin conmutación automática — HARN-09), `get_harness` (semana anterior, testeado).
- **G.3** `backend/api/workflow.py` — orquesta FSM+harness+visual+repos; transiciones aplicadas ANTES de persistir (ilegal → 409 sin corrupción, FSM-01); traza append-only + `decision_history` + receipt; `CANDIDATE_EDITED` → `content_version++` + invalidación; `approve` exige razón sin blockers; `simulate_publish` con guards candidato APPROVED + visual VISUAL_READY; `redact_secrets` antes de responder. **16/16 verde** en `test_workflow.py`.
  - 🔑 **Bug de posición→ID resuelto:** el harness evalúa por POSICIÓN (EVAL-07 anonimiza+baraja; `_remap_scores` devuelve `candidate_id` = índice ORIGINAL en la lista). El workflow mapea `by_position` → ID real de DB ANTES de decidir/persistir. El loop de persistencia itera los scores RE-MAPEADOS por `score.candidate_id` (un zip posicional previo dejaba al candidato 3 sin evaluación → re-evaluación full-path desde RECOMMENDED → 409 espurio). Fix: 16/16.
  - 🔑 **Idempotencia honesta (TRC-03/APPR-03):** `_stored_evaluation` devuelve la decisión vigente SIN re-correr el harness si TODOS los candidatos tienen evaluación con `content_version` vigente (no-op sin eventos); solo la edición invalida.
  - 🔑 **DemoProvider diferenciado:** `_ANGLE_DELTAS` por ángulo (problem-story voice_fit+1 → 97; practical-framework/argued-position hook−1 → 91; gap 6 ≥ 4) → decisión RECOMMENDED reproducible con mejor candidato problem-story. `test_demo_provider.py` no pinea scores → sin break.
  - `_candidate_out.decision` = última entrada de `decision_history` (REVISION_REQUIRED/APPROVED), fallback a la evaluación.
- **G.4** Routers (10/10 en `test_endpoints.py`, TestClient + SQLite temp): `meta.py` (`GET /api/health`), `projects.py` (`GET /api/ideas/demo` desde `seed.DEMO_IDEAS`, `POST /projects` 201 → IDEA, `POST /projects/{id}/brief`, `GET /projects/{id}`, `GET /projects`), `runs.py` (`GET /runs/{id}` traza redactada, `POST /runs/{id}/evaluate`), `candidates.py` (generate, retry-generate, edit, request-revision, approve, visual, publish-simulated), `visuals.py` (approve, reject, `GET /visuals/{id}/svg` — path desde la DB, sin path traversal §13.5; si `svg_path` es None renderiza del contrato vía `render_svg_string`).
  - `ERROR_RESPONSES` compartido en `api/routers/__init__.py` → `ErrorBody`/`ErrorDetail` entran a `/openapi.json` (el FE los tipea desde `schema.d.ts`, ADR-003/H1.1).
  - 🔑 **FSM mensaje accionable (API-04, design §12):** `_REQUIREMENT_BY_EVENT` en `domain/fsm.py` — transición ilegal ahora dice el requisito faltante ("se requiere: un brief aprobado (BRIEF_READY)", "…una evaluacion previa del candidato…"). Tests de dominio no acoplaban el mensaje → sin break (49 siguen verdes).
- **G.5** `backend/api/main.py` — `create_app(settings=None)` factory + `app` a nivel de módulo; lifespan `create_all` idempotente + `seed_demo_data` (ADR-008); CORS allowlist `CORS_ORIGINS` con `allow_credentials=False` (API-03); `/docs`+`/redoc` solo en `APP_ENV=dev` (openapi.json siempre, ADR-003); uvicorn `127.0.0.1`. **9/9 en `test_main.py`**.
  - 🔑 **Gotcha de aislamiento:** `get_settings` es singleton `lru_cache` — los tests de main lo limpian con env parcheado y el cache quedaba polucionado para otros tests (rompía `db/test_engine.py` en suite completa). Fix: `get_settings.cache_clear()` en el teardown del fixture.
- **G.6** `frontend/src/api/schema.d.ts` (1920 líneas, openapi-typescript 7.13 contra backend vivo :8000) + `frontend/src/api/openapi.json` cacheado (§19-1: sí). Contiene `components["schemas"]["CandidateOut"]`, `ErrorBody`, `PublicationOut`, `RunDetailOut`, etc. **`npm run schema:check` → diff vacío OK.** ⚠️ La parte "COMMITEAR" del criterio queda PENDIENTE por regla del orquestador (no commit; el repo entero sigue untracked — A1.1 sigue pendiente).
- **G.7** Cierre: **`pytest -q backend/tests` → 279 passed** + `ruff check backend/` → All checks passed. G.5 además CIERRA A1.2 (el puerto 8000 ahora responde; `npm run dev` levanta ambos procesos).

### Batch H1 — Base frontend (Engram `apply-progress/h1`)
- **H1.1** `frontend/src/api/client.ts` importa exclusivamente tipos de `schema.d.ts`, expone helpers para todos los endpoints P0 y normaliza respuestas no-2xx/red a `ApiError` con `ErrorBody` canónico. Fetch mock 409 verificado.
- **H1.2** `frontend/src/hooks/useAsync.ts` usa un lock síncrono en `useRef` para ignorar un segundo `run()` antes del rerender; mantiene `{data,error,busy,run}` y libera `busy` en success/error.
- **H1.3** primitivas UI completas: Banner, ScoreBreakdown, CandidateCard, AngleTag, ErrorBanner, BlockersList, ReceiptCard y VoiceBadge; fórmula 72/4/60 y pesos visibles como calibrables; recibo sin IDs/URLs remotos.
- **H1.4** Vitest+jsdom configurado en `vite.config.ts`, suite contract excluida del run unitario; `tokens.css` + `base.css` responsive con estados simulation/demo/error visualmente distintos.
- **H1.5** cierre verde: **24/24 tests** y `tsc --noEmit` sin errores. Se corrigió el test del error conforme al tipo generado `details?: Record<string, never>` sin `any`, casts ni DTO manual; el mensaje conserva el detalle accionable exigido por API-04.
- **Schema check:** no ejecutado en H1 porque no es criterio de H1.1-H1.5 y no se modificaron `openapi.json`/`schema.d.ts` ni backend; sigue siendo criterio de I.4.

### Bugfix contractual previo a H2 — `ErrorDetail.details`
- **Causa:** `ErrorDetail.details: dict[str, Any]` aceptaba payloads runtime no vacíos, pero el OpenAPI cacheado no materializaba `additionalProperties`; `openapi-typescript` generaba `Record<string, never>` e impedía representar `details.fields`/`details.code`.
- **Corrección canónica:** `backend/api/schemas.py` declara explícitamente `json_schema_extra={"additionalProperties": True}` sobre el field. Se regeneraron `frontend/src/api/openapi.json` y `frontend/src/api/schema.d.ts` desde FastAPI vivo.
- **Regresión:** pytest exige `additionalProperties: true` y valida un envelope no vacío; Vitest construye `ErrorBody` con `fields` y `code` directamente desde el tipo generado, sin `any`, casts ni DTO manual.
- **Tipo TS final:** `details?: { [key: string]: unknown }`.
- **Evidencia:** pytest relevante **55 passed**; Vitest **24 passed**; `tsc --noEmit` limpio; `npm run schema:check` diff vacío.
- **Estado SDD:** bugfix transversal documentado; no se marca ninguna tarea H2/I porque sus criterios exactos no fueron ejecutados completamente.

### Batch H2 — Wizard 10 pasos + App (Engram `apply-progress/h2`)
- **H2.1-H2.3:** App/layout y wizard con provider/voz v0, tres ideas demo + manual normalizada, brief editable con tesis, defaults, evidencia clasificada y restricciones; validaciones accesibles bloquean idea/tesis/evidencia vacías.
- **H2.4-H2.6:** generación real por client H1 con lock anti doble envío, `GENERATION_FAILED` + retry, exactamente tres cards/ángulos, evaluación completa con fórmula/blockers y `EVALUATION_PARTIAL` sin score fabricado.
- **H2.7-H2.8:** selección/edición real; edición invalida evaluación y fuerza reevaluación; alternativa, revisión y aprobación humana exigen razón; blockers bloquean aprobación; override explícito.
- **H2.9:** SVG/alt text/rationale visibles, sin autoaprobación; aprobar/rechazar exige razón y regenerar desde `VISUAL_REVISION_REQUIRED` usa endpoint tipado nuevo.
- **H2.10-H2.11:** preview inequívocamente simulada, recibo local sin URL/URN/remote ID, traza por tipo con prompt/schema/hash/provider/score/versiones/decisiones/recibo y redacción defensiva de secretos.
- **Corrección backend mínima por bloqueo real:** `approve visual` recibe `ReasonIn`, nuevo endpoint `regenerate`, razones/eventos humanos y recibo simulado enriquecido en traza; OpenAPI cacheado y tipos TS regenerados.
- **Verificación:** frontend **34/34**, backend **281/281**, `tsc --noEmit` limpio, `schema:check` diff vacío, Vite `/` y `/src/main.tsx` HTTP **200**, sin build ni commit.

---

## 3. Criterios A1 pendientes (sin marcar, con explicación)

1. **A1.1** — Falta el **commit inicial** (`git init` + `.gitignore` están hechos y verificados). El criterio completo exige "commit inicial con SOLUTION.md y openspec/ intactos". No se commiteó por regla del orquestador (no commit). **Acción:** commitear cuando el orquestador levante la regla (conventional commit, sin atribución IA).
2. **A1.2** — ✅ **RESUELTO por G.5** (verificado en esta consolidación): `uvicorn api.main:app` arranca y responde en :8000; `npm run dev` levanta ambos procesos. Pendiente SOLO de marcar `[x]` en tasks.md cuando el orquestador lo autorice (junto con A1.1).

> Nota adicional (no bloqueante): A1.4 y A1.5 no tienen test unit persistente (el criterio los pedía); el comportamiento está demostrado funcionalmente. Recomendado: agregar `backend/tests/core/test_config.py` y `test_trace.py` en una wave posterior o como gap de verify.

---

## 4. Pruebas ejecutadas (esta consolidación, sin build, backend/.venv)

| Comando | Resultado |
|---|---|
| `backend/.venv/bin/pytest -q backend/tests` | **279 passed** (225 Wave 1+2 + 54 api G) |
| `backend/.venv/bin/pytest -q backend/tests/api` (criterio G.7) | **54 passed** (errors+deps 19, workflow 16, endpoints 10, main 9) |
| `backend/.venv/bin/pytest -q backend/tests/domain backend/tests/fixtures` (criterio B.7) | **49 passed** |
| `backend/.venv/bin/pytest -q backend/tests/contracts` (criterio C.3) | **43 passed** |
| `backend/.venv/bin/pytest -q backend/tests/db` (criterio D.5) | **21 passed** |
| `backend/.venv/bin/pytest -q backend/tests/harness` (criterio E.6) | **58 passed** |
| `backend/.venv/bin/pytest -q backend/tests/visual` (criterio F.5) | **54 passed** |
| `backend/.venv/bin/ruff check backend/` | **All checks passed** |
| `PATH=backend/.venv/bin:$PATH npm --prefix backend run test` (criterio A1.3) | **279 passed** |
| `npm run dev` (smoke, criterio A1.2) | vite 200 :5173 / uvicorn 200 :8000 (`/api/health` + `/openapi.json`) — ✅ **A1.2 RESUELTO** |
| `GET /openapi.json` + `npm run schema:generate` (criterio G.6) | `frontend/src/api/schema.d.ts` 1920 líneas; `npm run schema:check` → **diff vacío OK** |
| `npm --prefix frontend run test` (criterio H1.4/H1.5) | **24 passed** (4 archivos: client, useAsync, UI, styles) |
| `frontend/node_modules/.bin/tsc --noEmit` (criterio H1.1/H1.5) | **sin errores** |
| `.venv/bin/pytest tests/contracts/test_schemas.py tests/api/test_errors.py tests/api/test_main.py -q` (bugfix contractual) | **55 passed** |
| `npm run schema:check` (bugfix contractual, backend vivo) | **diff vacío OK** |
| `git check-ignore` (criterio A1.1) | paths sensibles ignorados; SOLUTION.md/openspec/.env.example NO |
| `git log` | **sin commits** → A1.1 pendiente |
| Hashes de prompts (E.2, esta consolidación) | generator `sha256:94440177...823d`, evaluator `sha256:90edc7d3...e93202` — coinciden con manifest.json |
| `.env.example` grep credenciales | sin credenciales reales |

Sin build (regla global), sin commit (regla orquestador). El bugfix no modifica `tasks.md` ni marca H2/I.

---

## 5. Interfaz para Wave 3 (G)

- **G** (API) depende de A1+B+C+D+E+F — **todas DONE**. Consumirá: `db.engine` (`create_all_tables`, `seed_demo_data` en lifespan), `db.repos.get_run_detail` para ensamblar traza (§14), `settings.cors_origins_list` (NO `cors_origins` directo — gotcha A1.4), `ai.harness` (`run_generation`/`run_evaluation`), `visual.svg.render_svg` + `visual.validate.validate_visual_contract` + `visual.image_provider.resolve_image_provider`/`fallback_notice` (F.4, stub P1 → G usa SVG determinístico), y `domain.fsm` para autorizar transiciones antes de persistir (design §1).

## 6. Next steps

1. ✅ **Wave 3 (G) COMPLETA** — backend API integrado y verde (279 passed). Backend P0 completo: dominio + harness + visual + persistencia + API.
2. ✅ **Wave 4 H1 + H2 COMPLETA** — base frontend y wizard 10 pasos end-to-end verdes. **Próxima fase: I** (contrato FE/BE).
3. **Commit inicial (A1.1)** — pendiente de decisión del orquestador (regla no-commit; todo el árbol sigue untracked). La parte "COMMITEAR" de G.6 corre con él.
4. Recomendado para sdd-verify: confirmar reconciliación FSM tasks.md vs design.md (B.1), los gaps de tests unit de core (A1.4/A1.5), y el `_REQUIREMENT_BY_EVENT` nuevo del FSM (G.4).

## 7. Batch I — Contrato FE/BE anti-drift

- **I.1** `frontend/src/tests/contract/openapi-drift.test.ts` ejecuta `openapi-typescript` contra `/openapi.json` vivo y compara el resultado byte a byte con `schema.d.ts`; ante diferencia exige regenerar el schema.
- **I.2** `frontend/src/tests/contract/roundtrip-smoke.test.ts` usa el `api/client.ts` real y tipos generados para recorrer HTTP completo: ideas demo, proyecto, brief, generación con `DEMO_PROVIDER`, evaluación, aprobación humana, visual, aprobación humana y `SIMULATED_PUBLISHED`. Las respuestas `CandidateOut`, `EvaluationOut` y `PublicationOut` se validan contra los schemas del OpenAPI vivo mediante un validador genérico de JSON Schema, sin DTOs manuales. Incluye CORS permitido para `http://localhost:5173` y rechazado para origen desconocido.
- **I.3** `frontend/src/tests/contract/schema-coverage.test.ts` inspecciona las referencias `components['schemas']` del código fuente y verifica que cada componente exista en el archivo generado.
- **I.4** Verificación completa con backend vivo: `pytest -q` → **281 passed**; `npm --prefix frontend run test` → **34 passed**; `npm run test:contract` → **4 passed**; `frontend/node_modules/.bin/tsc --noEmit` desde `frontend/` → **limpio**; `npm run schema:check` → **sin drift**.

### Resultado

Batch I queda **COMPLETO / GREEN**. No se detectaron defectos en las fuentes canónicas; solo se corrigieron guards de optionalidad en la prueba nueva según `schema.d.ts`. No se ejecutó build ni se creó commit. Próximo lote: **J**.

## 8. Batch J — Cierre P0 (J.1-J.5 verificados)

- **J.1:** `README.md` ya contiene Node `24.14.0`, Python `3.12.7`, instalación, arranque de ambos procesos, demo sin credenciales/red, limitaciones, guion, regla de corte y referencia a `SOLUTION.md`.
- **J.2:** `docs/decisions.md` cubre ADR-001..009 y los supuestos de voz v0 provisional, umbrales `72/4/60`, heurística sin promesa de viralidad, SQLite descartable y DemoProvider sin keys.
- **J.3:** README §Semana adicional documenta OAuth/LinkedIn real, Alembic, validación de voz, adaptadores P1, historial/E2E y calibración con datos.
- **J.4:** `backend/tests/p0/test_j_regressions.py` → **6 passed**; `python scripts/demo_smoke.py` → `SIMULATED_PUBLISHED`; con backend del venv y `DEMO_FORCE_INVALID=1`, `python scripts/demo_smoke.py --failure` → `GENERATION_FAILED`, conservando el brief. El contrato FE/BE repitió round-trip real hasta publicación simulada.
- **J.5:** `PATH=backend/.venv/bin:$PATH npm test` → **287 pytest + 34 Vitest**; `vitest.contract.config.ts` → **4 passed**; `tsc --noEmit` limpio; schema sin drift; `ruff check backend/` limpio.
- **J.6:** permanece `[ ]`: el criterio exige commit inicial, slices y working tree limpio; la instrucción del usuario prohíbe commit.

**Resultado P0:** `65/68` tareas marcadas, **95.6%**. A1.1/A1.2 siguen pendientes en `tasks.md` por estado heredado; J.6 queda pendiente explícitamente. No se implementó P1/K, no hubo build ni commit, y no se modificaron documentos de evidencia ya cumplidos.
# Enhancement: provider explícito DemoProvider/OpenAI

- Implementado `backend/ai/openai_compat.py` con HTTP Chat Completions mediante `httpx`; no usa SDK ni expone credenciales.
- `get_provider` acepta solo la selección `demo|openai` y conserva el fallback explícito, nunca automático.
- La UI ofrece el selector antes de generar y etiqueta cada salida con el provider real; errores de key/proveedor incluyen acción sobre `.env`.
- Tests mockados cubren respuestas HTTP, errores normalizados y selección DemoProvider sin key.
